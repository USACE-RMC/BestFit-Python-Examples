"""Compare prepared Python views with independently exported desktop geometry."""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path, default=ROOT.parent/"RMC-BestFit")
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
        app_file = app/"validation/plot-parity/app-reference"/(key+".json")
        python_file = gallery/"specs"/(key+".json.gz")
        try:
            reference = json.loads(app_file.read_text(encoding="utf-8"))
            spec = json.loads(gzip.decompress(python_file.read_bytes()))
            if reference["sourceSha256"] != spec["appReference"]["sourceSha256"]:
                raise ValueError("App and Python artifacts identify different source bytes")
            report = module.compare_geometry(reference, spec)
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
