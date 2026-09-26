"""Authoring tool: extract observation-only fixtures from audited app archives.

Not called by notebooks or their generator. No model, analysis configuration,
fitted parameters, chains, results, or plot coordinates enter the raw fixtures.
"""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bestfit_examples.project_data import load_project
from bestfit_examples.data import series_xml


def record(element):
    # Plotting positions and threshold counts are derived anew by BestFit.
    attrs = {k: v for k, v in element.attrib.items()
             if k not in {"PlottingPosition", "NumberBelow"}}
    if len(element):
        attrs["children"] = [{"tag": c.tag, **record(c)} for c in element]
    return attrs


def main():
    source = json.loads((ROOT / "data/source-manifest.json").read_text(encoding="utf-8"))
    entries = source["projects"]
    destination = ROOT / "data/raw"
    destination.mkdir(exist_ok=True)
    manifest = {"schemaVersion": 1, "description": "Observations and input metadata only; no fitted objects or results.", "projects": {}}
    for slug in entries:
        project = load_project(slug)
        raw = {"source": project["source"], "series": {}, "inputs": {}}
        for row in project["tables"].get("Time Series Data", {}).get("rows", []):
            element = ET.fromstring(series_xml(row))
            metadata = {k: row.get(k) for k in ("Name", "UnitLabel", "SeriesType", "EntryMethod", "USGSSiteNumber")}
            raw["series"][row["Name"]] = {"metadata": metadata, "attributes": dict(element.attrib),
                                            "records": [record(x) for x in element]}
        for row in project["tables"].get("Input Data", {}).get("rows", []):
            element = ET.fromstring(row["DataFrame"])
            metadata = {k: v for k, v in row.items() if k not in {"DataFrame", "Description"}
                        and not k.endswith("PlotSettings") and not isinstance(v, dict)
                        and not (isinstance(v, str) and v.lstrip().startswith("<"))}
            raw["inputs"][row["Name"]] = {
                "metadata": metadata, "attributes": dict(element.attrib),
                "series": {s.tag: [record(r) for r in s] for s in element}}
        payload = gzip.compress(json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), mtime=0)
        path = destination / (slug + ".json.gz")
        path.write_bytes(payload)
        manifest["projects"][slug] = {"path": path.name, "sha256": hashlib.sha256(payload).hexdigest(),
                                      "source": project["source"]}
        print(slug, len(payload))
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
