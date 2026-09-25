"""Independent source checks on frozen original BestFit cells and references."""

from __future__ import annotations

import math

from scripts.audit_sources import audit_b17c, audit_nile, audit_run_quality, audit_sum_two_normals


def test_nile_frozen_csv_values_match_saved_series_with_uniform_date_shift(tmp_path) -> None:
    result = audit_nile()
    assert result == audit_nile(app_root=tmp_path / "app-not-checked-out")
    assert result["source_record_count"] == result["saved_record_count"] == 100
    assert result["value_mismatch_count"] == 0
    assert result["year_offset_values"] == [26]
    assert result["source_year_range"] == [1871, 1970]
    assert result["saved_year_range"] == [1897, 1996]
    assert result["frozen_csv_sha256"] == result["provenance"]["source_sha256"]


def test_b17c_reports_published_and_saved_one_percent_quantiles_without_method_equivalence() -> None:
    results = audit_b17c()
    orestimba = results["orestimba"]
    assert orestimba["published_ema_cfs"] == 13820
    assert math.isclose(orestimba["saved_gmm_cfs"], 13823.814991100618, rel_tol=1e-14)
    assert orestimba["saved_rounded_to_10_cfs"] == 13820
    assert orestimba["difference_cfs"] == orestimba["saved_gmm_cfs"] - 13820
    assert "EMA" in orestimba["published_method"]
    assert "GMM" in orestimba["saved_method"]
    assert "1932" in orestimba["published_context"]
    pueblo = results["pueblo"]
    assert pueblo["published_ema_cfs"] == 39800
    assert pueblo["saved_rounded_to_10_cfs"] == 39780
    assert "paleoflood" in pueblo["published_context"]
    assert pueblo["saved_input_record_counts"]["IntervalSeries"] == 4


def test_sum_of_normals_checks_actual_response_grid_and_fitted_parameters() -> None:
    results = audit_sum_two_normals()
    assert len(results) == 3
    for case in results:
        assert case["response_is_x_plus_y"] is True
        assert case["response_cell_count"] == 49
        assert case["z_comparison_count"] == case["configured_number_of_bins"]
        assert case["max_absolute_aep_error"] == max(
            point["absolute_error"] for point in case["aep_comparison"]
        )
        assert case["max_absolute_aep_error"] > 0
    nominal_zero = next(case for case in results if case["name"] == "CFA - Rho = 0.0")
    assert nominal_zero["z_comparison_count"] == 20
    assert sorted(case["z_comparison_count"] for case in results) == [20, 50, 50]
    assert nominal_zero["fitted_rho"] == 0.088550743996887
    first = nominal_zero["aep_comparison"][0]
    mu = nominal_zero["analytic_sum_mu"]
    sigma = nominal_zero["analytic_sum_sigma"]
    expected_survival = 0.5 * math.erfc((first["z"] - mu) / (sigma * math.sqrt(2)))
    assert first["analytic_aep"] == expected_survival


def test_fresh_run_quality_separates_completion_from_chain_diagnostics(tmp_path) -> None:
    # A clean checkout contains receipts, but deliberately excludes large rerun
    # snapshots. Exercise the audit with independent, portable diagnostic inputs.
    import base64
    import gzip
    import hashlib
    import json

    receipts = tmp_path / "receipts"
    outputs = tmp_path / "outputs"
    receipts.mkdir()
    outputs.mkdir()
    for number, (name, chains, statistics) in enumerate([
        ("Bayesian control", 4, [{"Rhat": 1.2, "ESS": 50},
                                  {"Rhat": 1.0, "ESS": 1000},
                                  {"Rhat": None, "ESS": None}]),
        ("GMM control", 0, [{"Rhat": 0.0, "ESS": 0}]),
    ], 1):
        results = {"ParameterResults": [{"SummaryStatistics": item} for item in statistics]}
        binary = base64.b64encode(json.dumps(results).encode()).decode()
        raw = gzip.compress(json.dumps({"mcmc": {"bytes_base64": binary}}).encode())
        output = f"case-{number}.json.gz"
        (outputs / output).write_bytes(raw)
        receipt = {"status": "completed", "analysis_name": name, "project_slug": "control",
                   "output_snapshot": output, "output_snapshot_bytes": len(raw),
                   "output_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                   "diagnostics": {"mcmc": {"chain_count": chains}}}
        (receipts / f"case-{number:03d}.json").write_text(json.dumps(receipt))
    (receipts / "case-003.json").write_text(json.dumps({"status": "failed"}))
    summary = audit_run_quality(receipts, outputs)
    assert summary["completion_status_counts"] == {"completed": 2, "failed": 1}
    assert summary["convergence_status"] == "not_established_by_completion"
    diagnostics = summary["parameter_diagnostics"]
    assert diagnostics["finite_rhat_count"] == 2
    assert diagnostics["rhat_over_1_01_count"] == 1
    assert diagnostics["ess_below_400_count"] == 1
    assert diagnostics["rhat_ess_inapplicable_count"] == 1
    assert diagnostics["rhat_ess_unavailable_count"] == 1
    assert {warning["analysis_name"] for warning in summary["screening_warnings"]} == {"Bayesian control"}

    import pytest
    (outputs / "case-1.json.gz").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash/size mismatch"):
        audit_run_quality(receipts, outputs)
