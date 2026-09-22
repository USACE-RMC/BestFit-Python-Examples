from __future__ import annotations

import pandas as pd

from bestfit_examples.presentation import (
    case_metrics,
    case_provenance,
    composite_weights,
    corrected_nile_dates,
    trend_ownership,
    uncertain_observations,
)
from bestfit_examples.project_data import load_project
from bestfit_examples.results import Case


def _case(name="case", *, analysis="UnivariateAnalysis", input_name="sample", metrics=None, receipt=None):
    return Case({
        "name": name,
        "origin": "fresh-run" if receipt else "saved-app",
        "sourceSha256": "a" * 64,
        "runtimeCommit": "b" * 40,
        "settings": {"Analysis": analysis, "InputData": input_name},
        "metrics": metrics or {"AIC": 10.0, "BIC": 11.0, "DIC": 12.0, "RMSE": 1.0},
        **({"receipt": receipt} if receipt else {}),
    })


def test_case_metrics_labels_scope_and_composite_zero_metrics_as_unavailable() -> None:
    fitted = _case("fit")
    composite = _case(
        "average", analysis="CompositeAnalysis",
        metrics={"AIC": 0.0, "BIC": 0.0, "DIC": 0.0, "RMSE": 0.0},
    )
    table = case_metrics([fitted, composite])
    assert table.loc[0, "Input / response"] == "sample"
    assert table.loc[0, "Analysis type"] == "UnivariateAnalysis"
    assert table.loc[0, "Comparison scope"].startswith("Descriptive only")
    assert table.loc[0, "AIC"] == 10.0
    assert pd.isna(table.loc[1, "AIC"])
    assert pd.isna(table.loc[1, "RMSE"])
    assert table.loc[1, "Metric note"] == "N/A: composite result does not define these fit metrics"


def test_case_metrics_accepts_explicit_same_response_likelihood_scope() -> None:
    table = case_metrics(
        [_case("one"), _case("two")],
        comparison_scope="Comparable: same response, observations, and likelihood.",
    )
    assert set(table["Comparison scope"]) == {"Comparable: same response, observations, and likelihood."}


def test_case_provenance_distinguishes_saved_and_fresh_receipt_identity() -> None:
    receipt = {"output_snapshot_sha256": "c" * 64, "settings_sha256": "d" * 64}
    table = case_provenance([_case("saved"), _case("fresh", receipt=receipt)])
    assert table.loc[0, "Origin"] == "saved-app"
    assert table.loc[0, "Receipt / result"] == "saved snapshot; no rerun receipt"
    assert table.loc[1, "Origin"] == "fresh-run"
    assert table.loc[1, "Receipt / result"] == "sha256:" + "c" * 12
    assert table.loc[1, "Settings"] == "sha256:" + "d" * 12
    assert table.loc[1, "Source"] == "sha256:" + "a" * 12


def test_nonstationary_trend_ownership_and_saved_bma_weights_are_explicit() -> None:
    project = load_project("nsffa-brays-bayou-texas")
    ownership = trend_ownership(project, ["NSFFA - Linear - Logistic", "NSFFA - Step"])
    assert list(ownership.columns) == ["Alternative", "Mean (of log)", "Std Dev (of log)", "Skew (of log)"]
    assert list(ownership.iloc[0, 1:]) == ["Linear", "Logistic", "Constant"]
    assert list(ownership.iloc[1, 1:]) == ["StepFunction", "Constant", "Constant"]
    weights = composite_weights(project, "Bayesian Model Average")
    assert weights["Weight"].sum() == 1.0
    assert weights.iloc[-1]["Alternative"] == "NSFFA - Step - Logistic"
    assert weights.iloc[-1]["Weight"] > 0.97
    assert set(weights["Method"]) == {"DIC"}


def test_uncertain_vignette_uses_saved_distribution_children() -> None:
    project = load_project("sinnemahoning-move3-bayesian")
    observations = uncertain_observations(project, "Sinnemahoning - MOVE.3 - With Errors")
    assert len(observations) == 25
    assert list(observations.columns) == ["Index", "Distribution", "Mu", "Sigma", "Plotting position"]
    assert observations.iloc[0].to_dict() == {
        "Index": "1914", "Distribution": "LogNormal", "Mu": 4.147,
        "Sigma": 0.074, "Plotting position": 0.45714285714285713,
    }


def test_nile_date_correction_shifts_date_axes_and_residual_oa_dates() -> None:
    from datetime import datetime, timedelta

    epoch = datetime(1899, 12, 30)
    oa = (datetime(1897, 1, 1) - epoch).total_seconds() / 86400
    case = Case({
        "plots": {
            "series": {"plotId": "time_series_analysis.series", "axes": {"x": {"scale": "date"}},
                       "series": [{"x": ["1897-01-01T00:00:00"]}]},
            "residuals": {"plotId": "time_series_analysis.residuals", "axes": {"x": {"scale": "linear"}},
                          "series": [{"x": [oa]}]},
        }
    })
    corrected = corrected_nile_dates(case)
    assert corrected.data["plots"]["series"]["series"][0]["x"] == ["1871-01-01T00:00:00"]
    shifted_oa = corrected.data["plots"]["residuals"]["series"][0]["x"][0]
    shifted = epoch + timedelta(days=shifted_oa)
    assert shifted == datetime(1871, 1, 1)
    assert corrected.data["plots"]["residuals"]["displayTransform"]["sourceEncoding"] == "OADate"


def test_generated_notebooks_keep_reviewed_presentation_contract() -> None:
    import nbformat
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    books = {path.stem: nbformat.read(path, 4) for path in (root / "notebooks").glob("*.ipynb")}
    assert len(books) == 12
    # The approved curriculum retains verified figures and tables. Execution
    # timestamps and error outputs are incidental, not teaching content.
    for book in books.values():
        for cell in book.cells:
            assert "execution" not in cell.metadata
            if cell.cell_type == "code":
                assert all(output.output_type != "error" for output in cell.get("outputs", []))
    for number in range(2, 12):
        book = next(book for name, book in books.items() if name.startswith(f"{number:02d}_"))
        assert any("case_provenance" in cell.source and "import" not in cell.source for cell in book.cells)
    assert any("Sinnemahoning - MOVE.3 - With Errors" in cell.source for cell in books["01_input_data"].cells)
    assert any("inactive sampler for B17C" in cell.source for cell in books["05_bulletin_17c"].cells)
    assert any("OLE Automation" in cell.source for cell in books["10_classic_time_series"].cells)
