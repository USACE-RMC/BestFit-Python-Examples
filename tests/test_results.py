"""Saved walkthroughs cannot silently read altered data or another software revision."""
import gzip
import hashlib
import json
import pytest


def fixture(tmp_path):
    root=tmp_path
    (root/"results").mkdir()
    (root/"data").mkdir()
    snapshot={"schemaVersion":1,"slug":"project","name":"analysis","table":"analysis",
              "sourceSha256":"source","runtimeCommit":"abc","plots":{},"settings":{},"metrics":{}}
    content=gzip.compress(json.dumps(snapshot).encode(),mtime=0)
    (root/"results"/"case.json.gz").write_bytes(content)
    (root/"results"/"manifest.json").write_text(json.dumps({"schemaVersion":1,"cases":[{
        "slug":"project","name":"analysis","table":"analysis","file":"case.json.gz",
        "sha256":hashlib.sha256(content).hexdigest()}]}))
    (root/"runtime-lock.json").write_text('{"bestFitCommit":"abc"}')
    (root/"data"/"source-manifest.json").write_text('{"projects":{"project":{"source_sha256":"source"}}}')
    return root


def test_changed_saved_plot_bytes_rejected(tmp_path):
    from bestfit_examples.results import saved_case
    root=fixture(tmp_path)
    (root/"results"/"case.json.gz").write_bytes(b"changed")
    with pytest.raises(ValueError,match="checksum"):
        saved_case("project","analysis",root=root)


def test_different_runtime_revision_is_not_a_validated_cache(tmp_path):
    from bestfit_examples.results import saved_case
    root=fixture(tmp_path)
    (root/"runtime-lock.json").write_text('{"bestFitCommit":"other"}')
    with pytest.raises(ValueError,match="revision"):
        saved_case("project","analysis",root=root)


def test_read_saved_case_does_not_require_clr(tmp_path):
    from bestfit_examples.results import saved_case
    case=saved_case("project","analysis",root=fixture(tmp_path))
    assert case.data["sourceSha256"] == "source"


def test_fresh_plot_identity_tracks_run_and_dependencies():
    from bestfit_examples.analysis import _bind_run_identity
    child = {"name": "Marginal", "table": "Univariate", "analysis": object(), "dependencies": {}}
    root = {"name": "Response", "table": "Coincident", "analysis": object(), "dependencies": {"X": child}}
    receipt = {"started_utc": "2026-09-22T12:00:00Z", "output_snapshot_sha256": "fresh-output", "runtime": {"sourceCommit": "abc"}}
    _bind_run_identity(root, receipt)
    identity = dict(root["plotSourceIdentity"])
    assert identity["kind"] == "rerun"
    assert identity["runId"] == child["plotSourceIdentity"]["runId"]
    assert identity["id"] != child["plotSourceIdentity"]["id"]
    _bind_run_identity(root, {**receipt, "started_utc": "2026-09-22T13:00:00Z"})
    assert root["plotSourceIdentity"]["runId"] != identity["runId"]
