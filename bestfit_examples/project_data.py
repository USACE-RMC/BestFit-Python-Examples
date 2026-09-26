"""Read-only, lossless SQLite snapshots of saved BestFit example projects.

``tables`` retains every SQLite cell without XML interpretation. ``decoded`` is
an additional, convenient view of time-series ordinates and historical input
records; its attribute strings intentionally preserve the source precision.
Neither export nor load instantiates a .NET object or executes serialized data.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import sqlite3
import subprocess
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_identity(path: Path) -> tuple[str, str | None]:
    root = next((parent for parent in path.parents if (parent / ".git").exists()), None)
    if root is None:
        return path.name, None
    try:
        commit = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return path.relative_to(root).as_posix(), commit
    except (OSError, ValueError, subprocess.CalledProcessError):
        return path.name, None


def _xml_view(xml: str, kind: str, context: str) -> dict[str, Any]:
    if "<!DOCTYPE" in xml.upper() or "<!ENTITY" in xml.upper():
        raise ValueError(f"{context}: XML entity declarations are unsupported")
    try:
        element = ET.fromstring(xml)
    except ET.ParseError as error:
        raise ValueError(f"{context}: malformed {kind} XML: {error}") from error
    if element.tag != kind:
        raise ValueError(f"{context}: expected {kind} XML, found {element.tag}")
    if kind == "TimeSeries":
        return {
            "attributes": dict(element.attrib),
            "records": [dict(child.attrib) for child in element if child.tag == "SeriesOrdinate"],
        }
    return {
        "attributes": dict(element.attrib),
        "series": {
            series.tag: [dict(record.attrib) for record in series]
            for series in element
        },
    }


def _compressed_text(value: Any, context: str) -> str | None:
    if not value:
        return None
    if not isinstance(value, (bytes, bytearray)):
        raise ValueError(f"{context}: compressed value is not binary")
    try:
        return zlib.decompress(value, wbits=-15).decode("utf-8")
    except (zlib.error, UnicodeDecodeError) as error:
        raise ValueError(f"{context}: corrupt raw-DEFLATE UTF-8 payload: {error}") from error


def _decoded_row(table: str, row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    name = str(row.get("Name", ""))
    if table == "Time Series Data":
        for field in ("TimeSeries", "USGSRawText"):
            compressed_field = field + "Compressed"
            text = _compressed_text(row.get(compressed_field), f"{table} {name} {compressed_field}")
            source_column = compressed_field if text is not None else field
            if text is None:
                text = row.get(field)
            if text:
                if field == "TimeSeries":
                    result[field] = {
                        "source_column": source_column,
                        **_xml_view(text, "TimeSeries", f"{table} {name} {source_column}"),
                    }
                else:
                    result[field] = text
    if table == "Input Data" and row.get("DataFrame"):
        result["DataFrame"] = _xml_view(
            row["DataFrame"], "DataFrame", f"{table} {name} DataFrame"
        )
    return result


def _json_cell(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}
    if value is None or isinstance(value, (str, int, float)):
        return value
    raise TypeError(f"Unsupported SQLite cell type: {type(value).__name__}")


def _sqlite_cell(value: Any) -> Any:
    if isinstance(value, dict) and value.get("encoding") == "base64":
        return base64.b64decode(value["data"], validate=True)
    return value


def _derived_views(tables: dict[str, Any]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for table, contents in tables.items():
        if table not in {"Time Series Data", "Input Data"}:
            continue
        views = [
            _decoded_row(table, {key: _sqlite_cell(value) for key, value in row.items()})
            for row in contents["rows"]
        ]
        if any(views):
            decoded[table] = views
    return decoded


def export_project(path: str | Path) -> dict[str, Any]:
    """Export all user tables from a project without opening it for writes."""
    source = Path(path).resolve(strict=True)
    relative_path, commit = _source_identity(source)
    before = _sha256(source)
    tables: dict[str, Any] = {}
    decoded: dict[str, Any] = {}
    with sqlite3.connect(f"{source.as_uri()}?mode=ro&immutable=1", uri=True) as connection:
        names = [
            value for (value,) in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        if not names:
            raise ValueError(f"{source}: no project tables found")
        for table in names:
            quoted = '"' + table.replace('"', '""') + '"'
            columns = [record[1] for record in connection.execute(f"PRAGMA table_info({quoted})")]
            rows: list[dict[str, Any]] = []
            views: list[dict[str, Any]] = []
            for values in connection.execute(f"SELECT * FROM {quoted}"):
                raw = dict(zip(columns, values))
                views.append(_decoded_row(table, raw))
                rows.append({key: _json_cell(value) for key, value in raw.items()})
            tables[table] = {"columns": columns, "rows": rows}
            if any(views):
                decoded[table] = views
    after = _sha256(source)
    if after != before:
        raise ValueError(f"{source}: source changed during read-only export")
    return {
        "format_version": 1,
        "source": {
            "relative_path": relative_path,
            "repository_commit": commit,
            "sha256": before,
            "bytes": source.stat().st_size,
        },
        "tables": tables,
        "decoded": decoded,
    }


def load_project(slug: str, data_root: str | Path | None = None) -> dict[str, Any]:
    """Load a checked frozen snapshot by slug; reject missing or altered bytes."""
    if not slug or slug in {".", ".."} or not all(c.isalnum() or c in "-_" for c in slug):
        raise ValueError(f"Invalid project slug: {slug!r}")
    root = Path(data_root) if data_root is not None else Path(__file__).resolve().parent.parent / "data"
    manifest = json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))
    try:
        entry = manifest["projects"][slug]
    except KeyError as error:
        raise KeyError(f"Unknown project slug: {slug}") from error
    snapshot = root / "projects" / f"{slug}.json.gz"
    if _sha256(snapshot) != entry["export_sha256"]:
        raise ValueError(f"SHA256 mismatch for {slug} project export")
    with gzip.open(snapshot, "rt", encoding="utf-8") as stream:
        project = json.load(stream)
    if project["source"]["sha256"] != entry["source_sha256"]:
        raise ValueError(f"SHA256 mismatch for {slug} project source metadata")
    project["decoded"] = _derived_views(project["tables"])
    return project
