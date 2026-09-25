"""Contract tests for frozen BestFit SQLite projects."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import sqlite3
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from bestfit_examples.project_data import export_project, load_project


def _deflate(text: str) -> bytes:
    compressor = zlib.compressobj(wbits=-15)
    return compressor.compress(text.encode("utf-8")) + compressor.flush()


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    path = tmp_path / "sample.bestfit"
    connection = sqlite3.connect(path)
    connection.execute('CREATE TABLE "Project" (Name TEXT, SoftwareVersion TEXT)')
    connection.execute('INSERT INTO "Project" VALUES (?, ?)', ("Fixture", "2.0.1"))
    connection.execute(
        'CREATE TABLE "Time Series Data" '
        '(Name TEXT, TimeSeries TEXT, TimeSeriesCompressed BLOB, '
        'USGSRawText TEXT, USGSRawTextCompressed BLOB, UnitLabel TEXT)'
    )
    legacy = '<TimeSeries TimeInterval="OneYear"><SeriesOrdinate Index="1900-01-01" Value="1.25" /></TimeSeries>'
    compressed = '<TimeSeries TimeInterval="Irregular"><SeriesOrdinate Index="2017-02-08T16:05:08Z" Value="15.279999999999999" /></TimeSeries>'
    connection.execute(
        'INSERT INTO "Time Series Data" VALUES (?, ?, ?, ?, ?, ?)',
        ("Legacy", legacy, None, "original\nresponse", None, "cfs"),
    )
    connection.execute(
        'INSERT INTO "Time Series Data" VALUES (?, ?, ?, ?, ?, ?)',
        ("Compressed", "", _deflate(compressed), "", _deflate('{"source":"USGS"}'), "ft"),
    )
    connection.execute('CREATE TABLE "Input Data" (Name TEXT, DataFrame TEXT, UnitLabel TEXT)')
    connection.execute(
        'INSERT INTO "Input Data" VALUES (?, ?, ?)',
        (
            "Historical",
            '<DataFrame NumberOfLowOutliers="30" LowOutlierThreshold="782">'
            '<ExactSeries><ExactData Index="1932" Value="4260" IsLowOutlier="False" />'
            '</ExactSeries><PerceptionThresholdSeries><PerceptionThresholdData Index="1900" '
            'LowerBound="0" UpperBound="782" /></PerceptionThresholdSeries></DataFrame>',
            "cfs",
        ),
    )
    connection.execute('CREATE TABLE "<Bulletin 17C>" (Name TEXT, AnalysisXml TEXT, MCMCResults BLOB)')
    connection.execute(
        'INSERT INTO "<Bulletin 17C>" VALUES (?, ?, ?)',
        ("Saved fit", '<Result Estimate="1.5" />', b"\x00\xff\x01"),
    )
    connection.commit()
    connection.close()
    return path


def test_legacy_and_compressed_sources_keep_original_cells_and_decode_records(sample_project: Path) -> None:
    project = export_project(sample_project)
    rows = project["tables"]["Time Series Data"]["rows"]
    assert rows[0]["TimeSeries"].startswith('<TimeSeries TimeInterval="OneYear">')
    assert rows[1]["TimeSeries"] == ""
    assert rows[1]["TimeSeriesCompressed"] == {
        "encoding": "base64",
        "data": base64.b64encode(_deflate('<TimeSeries TimeInterval="Irregular"><SeriesOrdinate Index="2017-02-08T16:05:08Z" Value="15.279999999999999" /></TimeSeries>')).decode("ascii"),
    }
    decoded = project["decoded"]["Time Series Data"]
    assert decoded[0]["TimeSeries"]["records"] == [{"Index": "1900-01-01", "Value": "1.25"}]
    assert decoded[1]["TimeSeries"]["records"] == [
        {"Index": "2017-02-08T16:05:08Z", "Value": "15.279999999999999"}
    ]
    assert decoded[1]["TimeSeries"]["source_column"] == "TimeSeriesCompressed"
    assert decoded[1]["USGSRawText"] == '{"source":"USGS"}'
    assert project["decoded"]["Input Data"][0]["DataFrame"]["attributes"] == {
        "NumberOfLowOutliers": "30", "LowOutlierThreshold": "782"
    }
    assert project["decoded"]["Input Data"][0]["DataFrame"]["series"]["PerceptionThresholdSeries"] == [
        {"Index": "1900", "LowerBound": "0", "UpperBound": "782"}
    ]


def test_saved_results_and_binary_cells_roundtrip_without_writing_source(sample_project: Path) -> None:
    before = hashlib.sha256(sample_project.read_bytes()).hexdigest()
    project = export_project(sample_project)
    after = hashlib.sha256(sample_project.read_bytes()).hexdigest()
    assert before == after == project["source"]["sha256"]
    row = project["tables"]["<Bulletin 17C>"]["rows"][0]
    assert row["AnalysisXml"] == '<Result Estimate="1.5" />'
    assert base64.b64decode(row["MCMCResults"]["data"]) == b"\x00\xff\x01"
    assert not list(sample_project.parent.glob("*.bestfit-*"))


def test_tracked_app_source_records_repo_relative_path_and_commit() -> None:
    source_root = Path(__file__).resolve().parents[2] / "RMC-BestFit" / "examples"
    matches = list(source_root.rglob("manual-entry-example.bestfit")) if source_root.exists() else []
    if not matches:
        pytest.skip("Sibling BestFit examples checkout unavailable")
    project = export_project(matches[0])
    assert project["source"]["relative_path"].startswith("examples/1-time-series-data/")
    assert len(project["source"]["repository_commit"]) == 40


def test_corrupt_compressed_payload_raises_with_row_context(sample_project: Path) -> None:
    connection = sqlite3.connect(sample_project)
    connection.execute('UPDATE "Time Series Data" SET TimeSeriesCompressed=? WHERE Name=?', (b"bad", "Compressed"))
    connection.commit()
    connection.close()
    with pytest.raises(ValueError, match="Time Series Data.*Compressed.*TimeSeriesCompressed"):
        export_project(sample_project)


def test_cli_gzip_is_deterministic_and_loader_verifies_hash(sample_project: Path, tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    command = [
        sys.executable,
        "scripts/export_app_examples.py",
        "--data-root", str(data_root),
        "--project", str(sample_project),
    ]
    subprocess.run(command, check=True)
    exported = data_root / "projects" / "sample.json.gz"
    first = exported.read_bytes()
    subprocess.run(command, check=True)
    assert exported.read_bytes() == first
    # The frozen cache carries raw cells once; loading builds the derived view.
    assert "decoded" not in json.loads(gzip.decompress(first))
    loaded = load_project("sample", data_root)
    assert loaded["decoded"]["Time Series Data"][1]["TimeSeries"]["records"][0]["Value"] == "15.279999999999999"
    manifest = json.loads((data_root / "source-manifest.json").read_text(encoding="utf-8"))
    assert manifest["projects"]["sample"]["source_sha256"] == hashlib.sha256(sample_project.read_bytes()).hexdigest()
    exported.write_bytes(first[:-4] + b"XXXX")
    with pytest.raises(ValueError, match="SHA256"):
        load_project("sample", data_root)


def test_sinnemahoning_full_project_preserves_uncertain_input_source() -> None:
    project = load_project("sinnemahoning-move3-bayesian")
    assert project["source"]["relative_path"] == (
        "examples/4-univariate-distribution-analysis/1-univariate-analysis/"
        "4-measurement-errors/sinnemahoning-move3-bayesian.bestfit"
    )
    assert len(project["tables"]["<Univariate Distribution>"]["rows"]) == 3
    inputs = project["tables"]["Input Data"]["rows"]
    index = next(i for i, row in enumerate(inputs) if row["Name"] == "Sinnemahoning - MOVE.3 - With Errors")
    decoded = project["decoded"]["Input Data"][index]["DataFrame"]["series"]
    assert len(decoded["ExactSeries"]) == 79
    assert len(decoded["UncertainSeries"]) == 25
