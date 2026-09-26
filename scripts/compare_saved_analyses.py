"""Legacy comparison utility for archived app projects, not the notebook workflow.

Runs serially, records each attempt, and never changes priors, models, seeds,
sampler lengths, probabilities or tolerances. No case is silently retried.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bestfit_examples.analysis import prepare_rerun, rerun_analysis  # noqa: E402
from bestfit_examples.project_data import load_project  # noqa: E402


def _cases() -> list[tuple[str, str, str]]:
    cases: list[tuple[str, str, str]] = []

    def add(slug: str, table: str, names: list[str]) -> None:
        cases.extend((slug, table, name) for name in names)

    univariate = "Univariate Distribution Analysis"
    bivariate = "Bivariate Distribution Analysis"
    fitting = "Distribution Fitting Analysis"
    add("viglione-et-al-2013", fitting, [
        "Fit - Systematic (1951-2001)",
        "Fit - Systematic (1951-2005)",
        "Fit - Systematic (1951-2001) + Temporal Expansion",
        "Fit - Systematic (1951-2005) + Temporal Expansion",
    ])
    add("viglione-et-al-2013", univariate, [
        "MCMC - Systematic (1951-2001)",
        "MCMC - Systematic (1951-2005)",
        "MCMC - Systematic (1951-2001) + Temporal",
        "MCMC - Systematic (1951-2005) + Temporal",
        "MCMC - Systematic (1951-2001) + Causal",
        "MCMC - Systematic (1951-2005) + Causal",
        "MCMC - Systematic (1951-2001) + Temporal + Causal",
        "MCMC - Systematic (1951-2005) + Temporal + Causal",
        "MCMC - Systematic (1951-2001) + 3 Quantile Priors",
    ])
    add("nsffa-brays-bayou-texas", univariate, [
        "NSFFA - Constant", "NSFFA - Linear", "NSFFA - Logistic", "NSFFA - Step",
        "NSFFA - Linear - Logistic", "NSFFA - Logistic - Logistic",
        "NSFFA - Step - Logistic", "Bayesian Model Average",
    ])
    add("bulletin-17c-examples", univariate, [
        "Example #2", "Example #2 - BCB", "Example #4", "Example #4 - BCB",
    ])
    add("point-process-examples", univariate, [
        "USC00040741 - Point Process", "USC00040741 - GEV",
        "USC00040741 - Seasonal Point Process",
    ])
    add("mixture-distribution-examples", univariate, [
        "Mixture Distribution - 2 Normals",
        "Mixture Distribution - 2 Normals - Zero-Inflated",
    ])
    add("mixed-population-examples", univariate, [
        "Competing Flood Types", "Mixture of Flood Types",
    ])
    add("bivariate-distribution-examples", bivariate, [
        "AMH Copula", "Clayton Copula", "Frank Copula", "Gumbel Copula",
        "Joe Copula", "Normal Copula",
    ])
    add("sum-two-normals", bivariate, [
        "CFA - Rho = -0.5", "CFA - Rho = 0.0", "CFA - Rho = +0.5",
    ])
    add("waimea-river-stage-frequency", bivariate, ["CFA - Normal - Conditional"])
    add("usgs-07024175-mississippi-rating-curve", "Rating Curve Analysis", [
        "USGS 07024175 Rating Curve",
    ])
    add("synthetic-rating-curve-examples", "Rating Curve Analysis", [
        "1 Segment Rating Curve", "2 Segment Rating Curve", "3 Segment Rating Curve",
    ])
    add("classic-time-series-examples", "Time Series Analysis", [
        "Airline Passengers - TSA", "Nile River Flows - TSA", "Mauna Loa - CO2",
    ])
    add("time-series-regression-example", "Time Series Analysis", [
        "Simple Linear Regression", "Multiple Linear Regression",
    ])
    return cases


def _receipt_path(index: int, slug: str, name: str, directory: Path) -> Path:
    if index == 1:
        return directory / "case-001-viglione-fit-1951-2001.json"
    label = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return directory / f"case-{index:03d}-{slug}-{label}.json"


def _existing_receipt_issue(receipt_path: Path, expected: dict, output_dir: Path) -> str | None:
    """Return why an old receipt cannot stand in for this exact rerun."""
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return f"unreadable receipt: {error}"
    if receipt.get("status") != "completed":
        return f"status is {receipt.get('status', 'missing')}"
    for key, value in expected.items():
        if key != "status" and receipt.get(key) != value:
            return f"{key} differs from current source/runtime/settings"
    relative = receipt.get("output_snapshot")
    if not isinstance(relative, str) or not relative:
        return "output snapshot path missing"
    root = output_dir.resolve()
    output = (root / relative).resolve()
    if not output.is_relative_to(root):
        return "output snapshot path escapes output directory"
    if not output.is_file():
        return "output snapshot missing"
    if output.stat().st_size != receipt.get("output_snapshot_bytes"):
        return "output snapshot byte count differs"
    if hashlib.sha256(output.read_bytes()).hexdigest() != receipt.get("output_snapshot_sha256"):
        return "output snapshot checksum differs"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="Validate and show selected cases without running")
    parser.add_argument("--start", type=int, default=1, help="First one-based case number")
    parser.add_argument("--stop", type=int, default=None, help="Last one-based case number, inclusive")
    parser.add_argument("--rerun-existing", action="store_true", help="Explicitly repeat cases with receipts")
    parser.add_argument("--receipt-dir", type=Path, default=ROOT / "validation" / "reruns")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "output" / "reruns")
    args = parser.parse_args(argv)
    cases = _cases()
    if args.start < 1 or args.start > len(cases) or (args.stop is not None and args.stop < args.start):
        parser.error("Invalid case range")
    project_names: dict[str, dict[str, list[str]]] = {}
    for slug, table, name in cases:
        if slug not in project_names:
            project = load_project(slug)
            project_names[slug] = {
                key: [row["Name"] for row in value["rows"]]
                for key, value in project["tables"].items()
            }
        if project_names[slug].get(table, []).count(name) != 1:
            raise ValueError(f"Selection is absent or ambiguous: {slug} / {table} / {name}")
    if args.list:
        for index, (slug, table, name) in enumerate(cases, 1):
            print(f"{index:03d} {slug} | {table} | {name}")
        print(f"{len(cases)} selected cases")
        return 0
    stop = args.stop or len(cases)
    failures = 0
    for index in range(args.start, stop + 1):
        slug, table, name = cases[index - 1]
        receipt_path = _receipt_path(index, slug, name, args.receipt_dir)
        if receipt_path.exists() and not args.rerun_existing:
            expected = prepare_rerun(slug, table, name)["receipt"]
            issue = _existing_receipt_issue(receipt_path, expected, args.output_dir)
            if issue is not None:
                print(f"{index:03d} STALE {issue}: {name}", flush=True)
                failures += 1
            else:
                print(f"{index:03d} EXISTING completed and verified: {name}", flush=True)
            continue
        print(f"{index:03d} RUN {slug}: {name}", flush=True)
        try:
            receipt = rerun_analysis(
                slug, table, name, receipt_path, output_dir=args.output_dir,
            )
        except Exception as error:
            failures += 1
            print(f"{index:03d} FAILED {type(error).__name__}: {error}", flush=True)
        else:
            print(f"{index:03d} {receipt['status']} {receipt['wall_seconds']}s", flush=True)
    print(f"Selected range {args.start}-{stop}; failures {failures}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
