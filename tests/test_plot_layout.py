"""Check rendered readability as well as source-coordinate parity."""
from copy import deepcopy
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("variant", ["density_cdf", "joint_exceedance_cdf"])
@pytest.mark.parametrize("name", ["AMH Copula", "Clayton Copula", "Frank Copula",
                                 "Gumbel Copula", "Joe Copula", "Normal Copula"])
def test_cdf_contour_labels_fit_without_overlap_or_source_changes(variant, name):
    from bestfit_examples.plotting import render_plot
    from bestfit_examples.results import saved_case
    spec = saved_case("bivariate-distribution-examples", name).data["plots"][variant]
    original = deepcopy(spec)
    figure = render_plot(spec)
    try:
        figure.canvas.draw()
        axes = figure.axes[0]
        renderer = figure.canvas.get_renderer()
        bounds = [text.get_window_extent(renderer) for text in axes.texts]
        assert len(bounds) >= 9
        assert all(axes.bbox.contains(*box.min) and axes.bbox.contains(*box.max) for box in bounds)
        assert not any(a.overlaps(b) for i, a in enumerate(bounds) for b in bounds[i+1:])
        assert spec == original
    finally:
        plt.close(figure)


def test_zero_inflated_log_range_matches_desktop_without_dropping_small_values():
    from bestfit_examples.results import saved_case
    case = saved_case("mixture-distribution-examples", "Mixture Distribution - 2 Normals - Zero-Inflated")
    spec = case.data["plots"]["frequency"]
    assert any(0 < y < 1e-10 for series in spec["series"] for y in series["y"] if y is not None)
    reference = json.loads((ROOT / "validation/plot-parity/app-reference/mixture.frequency--zero_inflated.json").read_text())
    expected = next(axis for axis in reference["axes"] if axis["position"] == "Left")
    figure = case.plot()
    try:
        assert figure.axes[0].get_ylim() == pytest.approx((expected["ActualMinimum"], expected["ActualMaximum"]))
    finally:
        plt.close(figure)
