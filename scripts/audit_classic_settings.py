"""Offline fidelity review of fitting and ARIMAX settings, never a notebook input."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bestfit_examples.project_data import load_project

CASES = {
    "02_distribution_fitting": ("viglione-et-al-2013", "Distribution Fitting Analysis"),
    "10_classic_time_series": ("classic-time-series-examples", "Time Series Analysis"),
    "11_regression": ("time-series-regression-example", "Time Series Analysis"),
}
OUTPUT_ATTRIBUTES = {"DIC", "WAIC", "WAIC_pD", "LOOIC", "LOO_pD", "LOOIC_SE", "IsEstimated", "ElapsedTime"}


def configuration(element):
    """Compare model structure, priors and flags; fitted parameter values are outputs."""
    attributes = {k: v for k, v in element.attrib.items()
                  if not (element.tag == "ModelParameter" and k == "Value")}
    return element.tag, attributes, (element.text or "").strip(), [configuration(c) for c in element]


def main():
    count = 0
    for stem, (slug, table) in CASES.items():
        receipt = json.loads((ROOT / "validation/headless" / (stem + ".json")).read_text(encoding="utf-8"))
        assert receipt["status"] == "passed", stem
        book = json.loads((ROOT / "notebooks" / (stem + ".ipynb")).read_text(encoding="utf-8"))
        digest = hashlib.sha256("\n".join("".join(c["source"]) for c in book["cells"]).encode()).hexdigest()
        assert digest == receipt["sourceSha256"], stem + " changed since execution"
        project = load_project(slug)
        rows = {row["Name"]: row for row in project["tables"][table]["rows"]}
        assert {r["name"] for r in receipt["analyses"]} == set(rows), stem
        for run in receipt["analyses"]:
            row = rows[run["name"]]
            old, new = ET.fromstring(row["AnalysisXml"]), ET.fromstring(run["analysisSettings"])
            assert old.attrib == new.attrib, run["name"]
            if stem.startswith("02"):
                families = lambda tree: [e.get("Type") for e in tree.findall("FittedDistributions/FittedDistribution/Distribution")]
                assert families(old) == families(new) and len(families(new)) == 15, run["name"]
                assert old.findtext("ProbabilityOrdinates") == new.findtext("ProbabilityOrdinates"), run["name"]
            else:
                assert configuration(ET.fromstring(row["ARIMAX"])) == configuration(ET.fromstring(run["modelSettings"])), run["name"]
                before = ET.fromstring(row["BayesianAnalysis"])
                after = new.find("BayesianAnalysis")
                assert {k: v for k, v in before.attrib.items() if k not in OUTPUT_ATTRIBUTES} == {
                    k: v for k, v in after.attrib.items() if k not in OUTPUT_ATTRIBUTES}, run["name"]
            count += 1
        print(stem + ": original model and analysis configuration preserved")
    print(f"PASS: {count} fresh fitting/ARIMAX configurations; fitted outputs excluded")


if __name__ == "__main__":
    main()
