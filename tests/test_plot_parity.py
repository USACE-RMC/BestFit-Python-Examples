"""Documented display corrections must never hide changed plot coordinates."""
from copy import deepcopy
import importlib.util
from pathlib import Path


def checker():
    path = Path(__file__).resolve().parents[1] / "scripts/check_plot_parity.py"
    spec = importlib.util.spec_from_file_location("check_plot_parity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference(plot_id, title="90% Credible Interval"):
    return {"plotId": plot_id, "analysisKind": "ARIMAXAnalysis",
            "axes": [{"position": "Bottom", "type": "LinearAxis", "Title": "% Change"},
                     {"position": "Left", "type": "LinearAxis", "Title": "Residual"}],
            "series": [{"name": "interval", "Title": title, "points": [[27000, 2.5]]}],
            "annotations": []}


def test_residual_date_correction_retains_original_geometry_and_source():
    original = reference("time_series_analysis.residuals")
    saved = deepcopy(original)
    actual = checker().reference_for_comparison(original)
    assert actual["axes"][0]["type"] == "DateTimeAxis"
    assert actual["axes"][0]["Title"] == "Date"
    assert actual["series"][0]["points"] == [[27000, 2.5]]
    assert original == saved


def test_qq_correction_identifies_observed_x_and_model_y():
    actual = checker().reference_for_comparison(reference("fitting.qq"))
    assert [axis["Title"] for axis in actual["axes"]] == ["Quantile (Data)", "Quantile (Model)"]


def test_prediction_and_b17c_labels_remain_distinct():
    module = checker()
    predictive = module.reference_for_comparison(reference("rating.curve"))
    assert predictive["series"][0]["Title"] == "90% Prediction Interval"
    frequentist = reference("shared_diagnostics.histogram", "Posterior Histogram")
    frequentist["analysisKind"] = "Bulletin17CAnalysis"
    actual = module.reference_for_comparison(frequentist)
    assert actual["series"][0]["Title"] == "Uncertainty Histogram"
    bayesian = module.reference_for_comparison(reference("univariate.frequency"))
    assert bayesian["series"][0]["Title"] == "90% Credible Interval"


def test_unrecognized_view_is_not_normalized():
    original = reference("custom.residuals")
    assert checker().reference_for_comparison(original) == original
