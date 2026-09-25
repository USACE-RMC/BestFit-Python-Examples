"""Audit frozen example sources against independent published and analytic controls.

The audit reads original frozen cells and a byte-identical CSV copy. It never
fits a model, downloads observations, or changes a scientific setting.
"""

from __future__ import annotations

import argparse
import base64
import collections
import csv
import gzip
import hashlib
import io
import json
import math
import statistics
import sys
import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bestfit_examples.project_data import load_project  # noqa: E402


USGS_B17C_URL = "https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _row(project: dict[str, Any], table: str, name: str) -> dict[str, Any]:
    matches = [row for row in project["tables"][table]["rows"] if row["Name"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one {table} / {name} row, found {len(matches)}")
    return matches[0]


def _series(project: dict[str, Any], table: str, name: str, field: str) -> dict[str, Any]:
    rows = project["tables"][table]["rows"]
    index = next((i for i, row in enumerate(rows) if row["Name"] == name), None)
    if index is None:
        raise ValueError(f"Missing {table} / {name}")
    return project["decoded"][table][index][field]


def audit_nile(data_root: Path | None = None, app_root: Path | None = None) -> dict[str, Any]:
    """Compare every published CSV ordinate to the saved project series."""
    root = data_root or ROOT / "data"
    provenance = json.loads((root / "references" / "nile-river-flow.provenance.json").read_text(encoding="utf-8"))
    frozen = root / provenance["frozen_relative_path"]
    csv_bytes = frozen.read_bytes()
    if len(csv_bytes) != provenance["source_bytes"] or _sha256(csv_bytes) != provenance["frozen_sha256"]:
        raise ValueError("Frozen Nile CSV bytes differ from provenance")
    if provenance["frozen_sha256"] != provenance["source_sha256"]:
        raise ValueError("Frozen Nile CSV SHA256 differs from app source SHA256")
    app = app_root if app_root is not None else ROOT.parent / "RMC-BestFit"
    app_source = app / provenance["source_relative_path"]
    if app_source.exists():
        if app_source.read_bytes() != csv_bytes:
            raise ValueError("App Nile CSV bytes differ from frozen copy")

    csv_rows = list(csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig"))))
    if not csv_rows or set(csv_rows[0]) != {"Date", "Flow"}:
        raise ValueError("Unexpected Nile CSV columns")
    project = load_project("classic-time-series-examples", root)
    if provenance["source_repository_commit"] != project["source"]["repository_commit"]:
        raise ValueError("Nile CSV and project source commits differ")
    saved = _series(project, "Time Series Data", "Nile River Flows", "TimeSeries")["records"]
    if len(csv_rows) != 100 or len(saved) != 100:
        raise ValueError("Nile reference or saved project no longer contains 100 records")
    source_dates = [date.fromisoformat(row["Date"]) for row in csv_rows]
    saved_dates = [date.fromisoformat(row["Index"][:10]) for row in saved]
    mismatches = [i for i, (source, project_row) in enumerate(zip(csv_rows, saved))
                  if Decimal(source["Flow"]) != Decimal(project_row["Value"])]
    offsets = sorted({saved_day.year - source_day.year for source_day, saved_day in zip(source_dates, saved_dates)})
    same_month_day = all((a.month, a.day) == (b.month, b.day) for a, b in zip(source_dates, saved_dates))
    if mismatches or offsets != [26] or not same_month_day:
        raise ValueError(f"Nile values or date offset changed: mismatches={mismatches}, offsets={offsets}")
    return {
        "source_csv_relative_path": provenance["source_relative_path"],
        "frozen_csv_sha256": _sha256(csv_bytes),
        "project_source_sha256": project["source"]["sha256"],
        "source_record_count": len(csv_rows),
        "saved_record_count": len(saved),
        "value_mismatch_count": len(mismatches),
        "year_offset_values": offsets,
        "month_day_match": same_month_day,
        "source_year_range": [source_dates[0].year, source_dates[-1].year],
        "saved_year_range": [saved_dates[0].year, saved_dates[-1].year],
        "finding": "All 100 flow values match; saved project dates are uniformly 26 years later than the source CSV.",
        "provenance": provenance,
    }


def audit_b17c(data_root: Path | None = None) -> dict[str, Any]:
    """Report measured differences from published EMA/MGBT point estimates."""
    project = load_project("bulletin-17c-examples", data_root)
    definitions = {
        "orestimba": ("Example #2", "10-9", 13820),
        "pueblo": ("Example #4", "10-17", 39800),
    }
    results = {}
    for key, (name, table, published) in definitions.items():
        row = _row(project, "<Bulletin 17C>", name)
        settings = ET.fromstring(row["AnalysisXml"])
        output = ET.fromstring(row["AnalysisResults"])
        probabilities = [float(value) for value in settings.findtext("ProbabilityOrdinates", "").split("|")]
        estimated = [float(value) for value in output.attrib["ModeCurve"].split("|")]
        if len(probabilities) != len(estimated):
            raise ValueError(f"B17C probability/result length mismatch for {name}")
        try:
            index = probabilities.index(0.01)
        except ValueError as error:
            raise ValueError(f"Saved B17C {name} has no 1% AEP ordinate") from error
        saved = estimated[index]
        input_view = _series(project, "Input Data", row["InputData"], "DataFrame")
        results[key] = {
            "analysis_name": name,
            "station": "Orestimba Creek near Newman, California" if key == "orestimba" else "Arkansas River at Pueblo, Colorado",
            "aep": 0.01,
            "units": "cubic feet per second",
            "published_table": table,
            "published_source_url": USGS_B17C_URL,
            "published_method": "Bulletin 17C Expected Moments Algorithm (EMA) with Multiple Grubbs-Beck Test",
            "published_context": (
                "USGS 11274500 continuous systematic record, water years 1932–2013; "
                "table 10-9 EMA/MGBT quantiles."
                if key == "orestimba" else
                "USGS 07099500 and companion Arkansas River records with historical intervals, "
                "perception thresholds, discontinued-record bounds, and paleoflood context; "
                "table 10-17 EMA/MGBT quantiles."
            ),
            "published_ema_cfs": published,
            "saved_method": "RMC-BestFit Bulletin 17C generalized method of moments (GMM) point estimate",
            "saved_gmm_cfs": saved,
            "difference_cfs": saved - published,
            "difference_percent_of_published": (saved - published) / published * 100,
            "saved_rounded_to_10_cfs": round(saved / 10) * 10,
            "saved_input_record_counts": {kind: len(records) for kind, records in input_view["series"].items()},
            "source_project_sha256": project["source"]["sha256"],
            "interpretation": "Different estimation methods and saved input/context; numeric proximity is not proof of method equivalence.",
        }
    return results


def audit_sum_two_normals(data_root: Path | None = None) -> list[dict[str, Any]]:
    """Use the closed form sum of correlated Normals as an independent AEP control."""
    project = load_project("sum-two-normals", data_root)
    cases = []
    for row in sorted(project["tables"]["<Coincident Frequency>"]["rows"], key=lambda item: item["Name"]):
        x = [float(value) for value in row["XValues"].split(",")]
        y = [float(value) for value in row["YValues"].split(",")]
        response = [float(value) for value in row["BivariateResponse"].split(",")]
        expected_response = [xi + yi for xi in x for yi in y]
        if len(response) != len(expected_response) or response != expected_response:
            raise ValueError(f"Saved response grid is not exactly X+Y for {row['Name']}")
        bivariate = _row(project, "<Bivariate Distribution>", row["BivariateAnalysis"])
        parameters = ET.fromstring(bivariate["BivariateDistribution"]).find("Parameters")
        if parameters is None or len(parameters) != 1:
            raise ValueError(f"Expected one fitted Normal copula parameter for {row['Name']}")
        rho = float(parameters[0].attrib["Value"])
        if not -1 < rho < 1:
            raise ValueError(f"Invalid fitted Normal copula rho for {row['Name']}")
        marginal_names = [bivariate[axis] for axis in ("MarginalX", "MarginalY")]
        margins = []
        for name in marginal_names:
            marginal = _row(project, "<Univariate Distribution>", name)
            distribution = ET.fromstring(marginal["UnivariateDistribution"]).find("Distribution")
            if distribution is None or distribution.attrib.get("Type") != "Normal":
                raise ValueError(f"Expected saved Normal margin for {name}")
            margins.append({"analysis_name": name, "mu": float(distribution.attrib["Mu"]),
                            "sigma": float(distribution.attrib["Sigma"])})
        mu = margins[0]["mu"] + margins[1]["mu"]
        sigma = math.sqrt(margins[0]["sigma"] ** 2 + margins[1]["sigma"] ** 2 +
                          2 * rho * margins[0]["sigma"] * margins[1]["sigma"])
        if not math.isfinite(sigma) or sigma <= 0:
            raise ValueError(f"Invalid analytic sum variance for {row['Name']}")
        z_values = [float(value) for value in row["ZOutputValues"].split(",")]
        saved_aep = [float(value) for value in ET.fromstring(row["AnalysisResults"]).attrib["ModeCurve"].split("|")]
        if len(z_values) != len(saved_aep):
            raise ValueError(f"CFA output grid/result mismatch for {row['Name']}")
        comparison = []
        for z, saved in zip(z_values, saved_aep):
            oracle = 0.5 * math.erfc((z - mu) / (sigma * math.sqrt(2)))
            comparison.append({"z": z, "saved_aep": saved, "analytic_aep": oracle,
                               "signed_error": saved - oracle, "absolute_error": abs(saved - oracle)})
        errors = [point["absolute_error"] for point in comparison]
        cases.append({
            "name": row["Name"],
            "source_project_sha256": project["source"]["sha256"],
            "response_is_x_plus_y": True,
            "response_cell_count": len(response),
            "response_x_count": len(x),
            "response_y_count": len(y),
            "configured_number_of_bins": int(row["NumberOfBins"]),
            "marginal_x": margins[0],
            "marginal_y": margins[1],
            "fitted_rho": rho,
            "analytic_sum_mu": mu,
            "analytic_sum_sigma": sigma,
            "z_comparison_count": len(comparison),
            "max_absolute_aep_error": max(errors),
            "mean_absolute_aep_error": statistics.mean(errors),
            "root_mean_squared_aep_error": math.sqrt(statistics.mean(error * error for error in errors)),
            "aep_comparison": comparison,
            "interpretation": "Closed-form Gaussian survival versus saved app CFA point-estimate AEP on its finite response grid; errors are reported, not thresholded.",
        })
    return cases


def audit_run_quality(
    receipt_root: Path | None = None, output_root: Path | None = None,
) -> dict[str, Any]:
    """Summarize fresh-run receipts and serialized diagnostics without acceptance claims."""
    receipts = receipt_root or ROOT / "validation" / "reruns"
    outputs = output_root or ROOT / "output" / "reruns"
    paths = sorted(receipts.glob("case-*.json"))
    if not paths:
        raise ValueError("No fresh curriculum rerun receipts found")
    statuses: collections.Counter[str] = collections.Counter()
    finite_rhats: list[float] = []
    finite_esses: list[float] = []
    inapplicable = 0
    unavailable = 0
    high_rhat = 0
    low_ess = 0
    case_warnings = []
    with_results = 0
    for path in paths:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        statuses[receipt["status"]] += 1
        if receipt["status"] != "completed":
            continue
        snapshot_path = outputs / receipt["output_snapshot"]
        raw = snapshot_path.read_bytes()
        if len(raw) != receipt["output_snapshot_bytes"] or _sha256(raw) != receipt["output_snapshot_sha256"]:
            raise ValueError(f"Fresh snapshot hash/size mismatch for {path.name}")
        node = json.loads(gzip.decompress(raw))
        metadata = receipt.get("diagnostics", {}).get("mcmc")
        if metadata is None:
            continue
        with_results += 1
        binary = node.get("mcmc", {}).get("bytes_base64")
        if not binary:
            raise ValueError(f"Missing fresh MCMC/ensemble bytes for {path.name}")
        results = json.loads(base64.b64decode(binary, validate=True))
        parameters = results.get("ParameterResults") or []
        case_high = []
        case_low = []
        for index, parameter in enumerate(parameters):
            summary = parameter.get("SummaryStatistics") or {}
            rhat, ess = summary.get("Rhat"), summary.get("ESS")
            if metadata["chain_count"] == 0:
                inapplicable += 1
                continue
            if not isinstance(rhat, (int, float)) or not math.isfinite(rhat) or \
                    not isinstance(ess, (int, float)) or not math.isfinite(ess):
                unavailable += 1
                continue
            finite_rhats.append(rhat)
            finite_esses.append(ess)
            if rhat > 1.01:
                high_rhat += 1
                case_high.append({"parameter_index": index, "rhat": rhat})
            if ess < 400:
                low_ess += 1
                case_low.append({"parameter_index": index, "ess": ess})
        if case_high or case_low:
            case_warnings.append({"project_slug": receipt["project_slug"],
                                  "analysis_name": receipt["analysis_name"],
                                  "rhat_over_1_01": case_high, "ess_below_400": case_low})
    return {
        "receipt_count": len(paths),
        "completion_status_counts": dict(sorted(statuses.items())),
        "convergence_status": "not_established_by_completion",
        "screening_thresholds": {"rhat_over": 1.01, "ess_below": 400,
                                 "role": "descriptive warnings only; not scientific acceptance"},
        "mcmc_or_ensemble_result_count": with_results,
        "parameter_diagnostics": {
            "finite_rhat_count": len(finite_rhats),
            "finite_ess_count": len(finite_esses),
            "rhat_range": [min(finite_rhats), max(finite_rhats)] if finite_rhats else None,
            "ess_range": [min(finite_esses), max(finite_esses)] if finite_esses else None,
            "rhat_over_1_01_count": high_rhat,
            "ess_below_400_count": low_ess,
            "rhat_ess_inapplicable_count": inapplicable,
            "rhat_ess_unavailable_count": unavailable,
            "inapplicable_reason": "Frequentist B17C ensembles have no Markov chains; their R-hat and ESS are not MCMC convergence diagnostics.",
        },
        "screening_warnings": case_warnings,
    }


def _write_json(path: Path, value: Any, *, check: bool) -> None:
    payload = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if check:
        if not path.is_file() or path.read_bytes() != payload:
            raise ValueError(f"Audit artifact is stale: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    parser.add_argument("--app-root", type=Path, default=ROOT.parent / "RMC-BestFit")
    parser.add_argument("--receipt-root", type=Path, default=ROOT / "validation" / "reruns")
    parser.add_argument("--output-root", type=Path, default=ROOT / "output" / "reruns")
    parser.add_argument("--source-report", type=Path, default=ROOT / "validation" / "source-checks.json")
    parser.add_argument("--quality-report", type=Path, default=ROOT / "validation" / "run-quality-summary.json")
    parser.add_argument("--check", action="store_true", help="Verify committed reports without rewriting them")
    args = parser.parse_args(argv)
    source = {
        "schema_version": 1,
        "nile": audit_nile(args.data_root, args.app_root),
        "bulletin_17c": audit_b17c(args.data_root),
        "sum_two_normals": audit_sum_two_normals(args.data_root),
    }
    quality = audit_run_quality(args.receipt_root, args.output_root)
    _write_json(args.source_report, source, check=args.check)
    _write_json(args.quality_report, quality, check=args.check)
    print(f"Nile {source['nile']['value_mismatch_count']} value mismatches, "
          f"{len(source['sum_two_normals'])} analytic CFA comparisons; "
          f"{quality['receipt_count']} rerun receipts, "
          f"{len(quality['screening_warnings'])} diagnostic warning case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
