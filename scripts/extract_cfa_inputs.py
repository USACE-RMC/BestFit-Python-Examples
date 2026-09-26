"""Extract only authored CFA response grids from the pinned source project dictionaries."""
from pathlib import Path
import hashlib
import json
from bestfit_examples.project_data import load_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw-responses"
manifest = {"schemaVersion": 1, "description": "Authored CFA response grids only; no fitted objects or results.",
            "projects": {}}

for slug in ("sum-two-normals", "waimea-river-stage-frequency"):
    source_path = ROOT / "data/projects" / (slug + ".json.gz")
    payload = source_path.read_bytes()
    source = load_project(slug)
    cases = {}
    for row in source["tables"]["<Coincident Frequency>"]["rows"]:
        x = [float(v) for v in row["XValues"].split(",")]
        y = [float(v) for v in row["YValues"].split(",")]
        values = [float(v) for v in row["BivariateResponse"].split(",")]
        assert len(values) == len(x) * len(y)
        cases[row["Name"]] = {
            "bivariate_analysis": row["BivariateAnalysis"],
            "x": x, "y": y,
            "response": [values[i * len(y):(i + 1) * len(y)] for i in range(len(x))],
            "bins": int(row["NumberOfBins"]),
        }
    output = {"source": source["source"], "source_project_sha256": hashlib.sha256(payload).hexdigest(),
              "cases": cases}
    OUT.mkdir(exist_ok=True)
    path = OUT / (slug + ".json")
    path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["projects"][slug] = {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                   "source": source["source"],
                                   "source_project_sha256": hashlib.sha256(payload).hexdigest()}
    print(slug, len(cases))
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
