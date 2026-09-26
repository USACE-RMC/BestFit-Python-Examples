"""Checksum-verified raw observations; this module does not construct analyses."""
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def load_raw(slug, root=None):
    """Return plain Python observations/metadata, with no configured or fitted objects."""
    directory = Path(root) if root is not None else ROOT / "data/raw"
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["projects"][slug]
    payload = (directory / entry["path"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
        raise ValueError(f"Raw input checksum mismatch: {slug}")
    return json.loads(gzip.decompress(payload))


def net_matrix(values):
    """Convert rectangular Python rows into System.Double[,]."""
    from System import Array, Double
    rows = [list(row) for row in values]
    columns = len(rows[0]) if rows else 0
    if any(len(row) != columns for row in rows):
        raise ValueError("Matrix rows must have equal lengths")
    matrix = Array.CreateInstance(Double, len(rows), columns)
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            matrix[i, j] = float(value)
    return matrix
