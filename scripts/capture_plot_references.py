"""Capture current desktop geometry from the exact frozen teaching projects.

Uses the pinned BestFit exporter on disposable inputs. The dependency checkout
and original projects are not modified. Only absolute capture paths are redacted
in published JSON; untouched raw exports remain under output/.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path, required=True)
    parser.add_argument("--only", help="Plot ID prefix")
    args = parser.parse_args()
    app = args.bestfit_source.resolve()
    git = ["git", "-c", f"safe.directory={app.as_posix()}", "-C", str(app)]
    lock = json.loads((ROOT / "runtime-lock.json").read_text())
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if revision != lock["bestFitCommit"]:
        raise ValueError("Desktop exporter source must match runtime-lock.json")
    manifest = json.loads((ROOT / "data/source-manifest.json").read_text())
    inputs = ROOT / ".runtime/reference-sources"
    for entry in manifest["projects"].values():
        relative = entry["source_relative_path"]
        content = subprocess.check_output([*git, "show", f"{lock['exampleSourceCommit']}:{relative}"])
        if hashlib.sha256(content).hexdigest() != entry["source_sha256"]:
            raise ValueError(f"Frozen source mismatch: {relative}")
        target = inputs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    path = app / "tools/PlotReferenceExporter/export_references.py"
    module_spec = importlib.util.spec_from_file_location("desktop_reference_export", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    module.ROOT = inputs
    module.REFERENCE = ROOT / "validation/plot-parity/app-reference"
    module.GALLERY = ROOT / "output/plot-reference-gallery"
    # EXE and MANIFEST retain their paths in the pinned dependency checkout.
    sys.argv = [str(path)] + (["--only", args.only] if args.only else [])
    module.main()
    rows = json.loads((module.REFERENCE / "index.json").read_text())
    failures = []
    for row in rows:
        if row["status"] not in {"exported", "app_conditional_empty"}:
            failures.append(row)
        if row["status"] != "exported":
            continue
        path = module.REFERENCE / (row["plotId"] + "--" + row["variant"] + ".json")
        raw = path.read_bytes()
        data = json.loads(raw)
        # Keep existing redacted records untouched during a targeted refresh.
        if not Path(data["project"]).is_absolute():
            continue
        data["project"] = row["source"].replace("\\", "/")
        data["captureProvenance"] = {
            "runtimeSourceCommit": revision,
            "exampleSourceCommit": lock["exampleSourceCommit"],
            "rawExportSha256": hashlib.sha256(raw).hexdigest(),
            "pathRedacted": True,
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{len(rows)} desktop variants; {len(failures)} unexpected failures")
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
