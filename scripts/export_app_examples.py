"""Freeze selected, tracked BestFit SQLite examples without modifying them.

The default selection spans all twelve notebooks and one gallery-only source.
The 32 tracked projects total about 315 MB; this selects 22 source projects
and retains every table, cell, setting and saved result within each one.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bestfit_examples.project_data import export_project  # noqa: E402


CURRICULUM_STEMS = (
    "usgs-download-example",
    "ghcn-download-example",
    "chmn-download-example",
    "hec-dss-import-example",
    "manual-entry-example",
    "usgs-block-max-example",
    "usgs-peak-download-example",
    "ghcn-peaks-over-threshold-example",
    "viglione-et-al-2013",
    "nsffa-brays-bayou-texas",
    "bulletin-17c-examples",
    "sinnemahoning-move3-bayesian",
    "point-process-examples",
    "mixture-distribution-examples",
    "mixed-population-examples",
    "bivariate-distribution-examples",
    "sum-two-normals",
    "waimea-river-stage-frequency",
    "usgs-07024175-mississippi-rating-curve",
    "synthetic-rating-curve-examples",
    "classic-time-series-examples",
    "time-series-regression-example",
)


def _selected_sources(source_root: Path) -> list[Path]:
    available: dict[str, Path] = {}
    for path in source_root.rglob("*.bestfit"):
        if path.stem in available:
            raise ValueError(f"Duplicate BestFit project slug: {path.stem}")
        available[path.stem] = path
    missing = set(CURRICULUM_STEMS) - set(available)
    if missing:
        raise FileNotFoundError(f"Missing curriculum project(s): {sorted(missing)}")
    return [available[stem] for stem in CURRICULUM_STEMS]


def _gzip_bytes(payload: bytes) -> bytes:
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0, compresslevel=9) as zipped:
        zipped.write(payload)
    return stream.getvalue()


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path,
        default=Path(__file__).resolve().parents[2] / "RMC-BestFit" / "examples",
    )
    parser.add_argument(
        "--data-root", type=Path,
        default=Path(__file__).resolve().parent.parent / "data",
    )
    parser.add_argument("--project", action="append", type=Path, default=[], help="Explicit .bestfit path; repeatable")
    args = parser.parse_args(argv)
    sources = args.project or _selected_sources(args.source_root)
    slugs = [path.stem for path in sources]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Project slugs must be unique")
    projects: dict[str, dict[str, object]] = {}
    for path in sources:
        project = export_project(path)
        # Derived XML records can be huge for long daily series. Frozen raw
        # cells carry their exact compressed bytes and load_project recreates
        # this view after hash verification.
        project.pop("decoded")
        payload = json.dumps(
            project, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        compressed = _gzip_bytes(payload)
        output = args.data_root / "projects" / f"{path.stem}.json.gz"
        _write_bytes(output, compressed)
        source = project["source"]
        projects[path.stem] = {
            "source_relative_path": source["relative_path"],
            "source_repository_commit": source["repository_commit"],
            "source_sha256": source["sha256"],
            "source_bytes": source["bytes"],
            "export_relative_path": f"projects/{path.stem}.json.gz",
            "export_sha256": hashlib.sha256(compressed).hexdigest(),
            "export_bytes": len(compressed),
        }
        print(f"{path.stem}: source {source['bytes']} bytes, export {len(compressed)} bytes", flush=True)
    manifest = {
        "format_version": 1,
        "selection": "explicit paths" if args.project else (
            "22 full projects from 32 tracked app projects: 21 curriculum projects and one "
            "Sinnemahoning measurement-error gallery source. The ABOM route and redundant or "
            "alternate saved examples remain linked to their unchanged app sources."
        ),
        "projects": projects,
    }
    _write_bytes(
        args.data_root / "source-manifest.json",
        (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
    )
    print(f"Exported {len(projects)} project(s); {sum(item['export_bytes'] for item in projects.values())} compressed bytes", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
