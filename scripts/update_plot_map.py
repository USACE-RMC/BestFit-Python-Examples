"""Publish plot coverage only from current independently compared artifacts."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path, default=ROOT.parent/"RMC-BestFit")
    parser.add_argument("--reference-dir", type=Path, default=ROOT/"validation/plot-parity/app-reference")
    args = parser.parse_args()
    mapping_path = args.bestfit_source / "skills/bestfit-frequency/references/app-plot-map.json"
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    report_path = ROOT / "validation/plot-parity/report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    rows = {(row["plotId"], row["variant"]): row for row in report["comparisons"]}
    adapters = {
        "time_series_data": "input_data.py::time_series_plots",
        "input_data": "input_data.py::input_data_plots",
        "fitting": "frequency.py::frequency_plots",
        "univariate": "frequency.py::frequency_plots",
        "b17c": "frequency.py::frequency_plots",
        "point_process": "frequency.py::frequency_plots",
        "mixture": "frequency.py::frequency_plots",
        "composite": "frequency.py::frequency_plots",
        "bivariate": "response_models.py::bivariate_plots",
        "coincident": "response_models.py::coincident_plots",
        "rating": "response_models.py::rating_plots",
        "time_series_analysis": "response_models.py::time_series_analysis_plots",
        "shared_diagnostics": "diagnostics.py::diagnostic_plots",
    }
    lines = ["# App-to-Python plot map", "",
             "Each row maps one desktop plot slot to its canonical adapter. The gallery contains all accepted variants;",
             "the separate report checks source-bound geometry, axes, labels, series presence, and styles.", "",
             "[Side-by-side gallery](plot-gallery/index.html) · [Detailed parity report](../validation/plot-parity/report.json)", "",
             "| App plot ID | Python adapter | Variants | Evidence |", "|---|---|---|---|"]
    for slot in mapping["slots"]:
        family = slot["plotId"].split(".")[0]
        slot["adapter"] = "bestfit_plots/adapters/" + adapters[family]
        evidence = []
        for variant in slot["variants"]:
            row = rows[(slot["plotId"], variant)]
            key = slot["plotId"] + "--" + variant
            if row["status"] == "verified":
                for path, field in ((args.reference_dir / (key + ".json"), "referenceSha256"),
                                    (ROOT / "docs/plot-gallery/specs" / (key + ".json.gz"), "specSha256")):
                    if hashlib.sha256(path.read_bytes()).hexdigest() != row[field]:
                        raise ValueError(f"Parity evidence is stale: {path}")
            evidence.append({"variant": variant, "status": row["status"], "source": row["source"],
                             "element": row["element"],
                             **{k: row[k] for k in ("referenceSha256", "specSha256") if k in row}})
        slot["sourceFixture"] = sorted({row["source"] for row in evidence})
        slot["evidence"] = evidence
        slot["status"] = "implemented" if all(row["status"] in {"verified", "app_conditional_empty"} for row in evidence) else "incomplete"
        counts = Counter(row["status"] for row in evidence)
        lines.append(f"| `{slot['plotId']}` | `{adapters[family]}` | {', '.join(slot['variants'])} | {dict(counts)} |")
    mapping["evidenceReport"] = "BestFit-Python-Examples/validation/plot-parity/report.json"
    mapping["evidenceReportSha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
    mapping["evidenceCounts"] = report["counts"]
    lines += ["", "## Interpretation and deliberate boundaries", "",
              "The stationary univariate chronology tab is conditionally absent. Its empty record is expected; the nonstationary case supplies this slot's populated evidence.", "",
              "Python displays time-series residuals on a Date axis, corrects fitting Q-Q labels, and distinguishes frequentist uncertainty, prediction intervals, and observed seasonal ranges. The comparison applies these explicit presentation corrections to a copy of the independent reference, keeping its coordinates and the original export intact. Contours carry numeric levels and seasonal dates display month names. These corrections do not alter estimation or stored results.", "",
              "The examples renderer spaces CDF contour labels with a small blank margin. The zero-inflated mixture retains the independently exported desktop log range (0.1 to 1000); near-zero positive coordinates remain stored outside that view. These layout choices are checked separately from geometry parity.", "",
              "Factory-default presentation is compared; saved custom colors/titles, WPF interaction, and pixel-identical font rasterization are excluded. Simulation, contour grids, priors, intervals, and diagnostics come from the unchanged BestFit/Numerics methods or completed API export. No renderer refits data.", "",
              "Use `bestfit_plots.source.add_frequency_comparison(base, alternative, name)` or the skill CLI's `--compare-source` and `--compare-name` for source-identified overlays. Both source identities are retained; matching axes and units are required. A plotted comparison is not automatically a valid information-criterion ranking.", ""]
    (ROOT / "docs/app-plot-map.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/app-plot-map.md").write_text("\n".join(lines), encoding="utf-8")
    print(dict(Counter(slot["status"] for slot in mapping["slots"])))
    return 0 if all(slot["status"] == "implemented" for slot in mapping["slots"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
