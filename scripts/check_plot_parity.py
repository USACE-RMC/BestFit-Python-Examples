"""Compare prepared Python views with independently exported desktop geometry."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reference_for_comparison(reference):
    """Correct known desktop presentation defects without changing coordinates.

    Independent exported geometry remains the numerical oracle. These explicit
    rules match the documented public display semantics, not the actual values
    supplied by the Python plot under test.
    """
    result = deepcopy(reference)
    plot_id = result["plotId"]
    if plot_id == "fitting.qq":
        for axis in result["axes"]:
            if axis["position"] in {"Bottom", "Left"}:
                axis["Title"] = "Quantile (Data)" if axis["position"] == "Bottom" else "Quantile (Model)"
    if plot_id == "time_series_analysis.residuals":
        for axis in result["axes"]:
            if axis["position"] == "Bottom":
                axis.update(type="DateTimeAxis", Title="Date")
    b17c = plot_id.startswith("b17c.") or any(
        name in result.get("analysisKind", "").lower() for name in ("b17c", "bulletin17c"))
    predictive = plot_id in {"rating.curve", "time_series_analysis.series"}
    seasonal = plot_id == "time_series_data.seasonality"

    def label(value):
        if not isinstance(value, str):
            return value
        if predictive:
            value = value.replace("Credible Interval", "Prediction Interval").replace("Confidence Interval", "Prediction Interval")
        if seasonal:
            value = value.replace("Confidence Interval", "Observed Range")
        if b17c:
            value = value.replace("Posterior", "Uncertainty").replace("Credible", "Confidence").replace("Quantile Prior", "Quantile Penalty")
        return value

    if "title" in result:
        result["title"] = label(result["title"])
    for item in result.get("series", []) + result.get("annotations", []):
        for key in ("name", "Title", "text"):
            if key in item:
                item[key] = label(item[key])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path, default=ROOT.parent/"RMC-BestFit")
    parser.add_argument("--reference-dir", type=Path, default=ROOT/"validation/plot-parity/app-reference")
    args = parser.parse_args()
    app = args.bestfit_source.resolve()
    module_spec = importlib.util.spec_from_file_location("app_geometry_compare", app/"validation/plot-parity/compare.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    gallery = ROOT/"docs/plot-gallery"
    rows = json.loads((gallery/"index.json").read_text(encoding="utf-8"))
    output = ROOT/"validation/plot-parity"
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for row in rows:
        key = row["key"]
        result = dict(plotId=row["plotId"], variant=row["variant"], source=row["source"], element=row["element"])
        if row["pythonStatus"] != "prepared":
            result.update(status=row["pythonStatus"], error=row.get("error", row.get("detail")))
            results.append(result)
            continue
        app_file = args.reference_dir/(key+".json")
        python_file = gallery/"specs"/(key+".json.gz")
        try:
            reference = json.loads(app_file.read_text(encoding="utf-8"))
            spec = json.loads(gzip.decompress(python_file.read_bytes()))
            if reference["sourceSha256"] != spec["appReference"]["sourceSha256"]:
                raise ValueError("App and Python artifacts identify different source bytes")
            corrected_reference = reference_for_comparison(reference)
            report = module.compare_geometry(corrected_reference, spec)
            report["displayCorrectionsApplied"] = corrected_reference != reference
            differences = report["differences"]
            report["differenceCount"] = len(differences)
            report["differenceTypes"] = dict(Counter(d["message"] for d in differences))
            report["differences"] = differences[:50]
            report["differencesTruncated"] = len(differences)>50
            result.update(status="verified" if report["ok"] else "differences", **report,
                          referenceSha256=hashlib.sha256(app_file.read_bytes()).hexdigest(),
                          specSha256=hashlib.sha256(python_file.read_bytes()).hexdigest())
            row.update(parityStatus=result["status"], referenceSha256=result["referenceSha256"],
                       specSha256=result["specSha256"])
        except Exception as error:
            result.update(status="comparison_failed", error=f"{type(error).__name__}: {error}")
        results.append(result)
        print(key+": "+result["status"]+" "+str(result.get("differenceTypes", result.get("error", ""))), flush=True)
    summary = {"schemaVersion":1,"absoluteTolerance":1e-10,"relativeTolerance":1e-8,
               "counts":dict(Counter(row["status"] for row in results)),"comparisons":results}
    (output/"report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    (gallery/"index.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(summary["counts"])
    return 1 if any(row["status"] not in {"verified", "app_conditional_empty"} for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
