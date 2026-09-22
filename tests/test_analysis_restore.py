"""Source-grounded restoration tests; no fitting or sampling is invoked."""

from __future__ import annotations

import pytest

from bestfit_examples.analysis import prepare_rerun, rerun_analysis, restore_analysis
from bestfit_examples.project_data import load_project


def test_viglione_canonical_roster_restores_original_gev_and_saved_results() -> None:
    project = load_project("viglione-et-al-2013")
    restored = restore_analysis(
        project, "Univariate Distribution Analysis", "MCMC - Systematic (1951-2001)"
    )
    assert restored["input"].ExactSeries.Count == 51
    assert restored["model"].Distribution.GetType().Name == "GeneralizedExtremeValue"
    assert restored["analysis"].BayesianAnalysis.NumberOfChains == 6
    assert restored["analysis"].BayesianAnalysis.Iterations == 3500
    assert restored["analysis"].BayesianAnalysis.PRNGSeed == 12345
    assert restored["analysis"].BayesianAnalysis.Results is not None
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].IsEstimated
    assert restored["source"]["sha256"] == project["source"]["sha256"]
    assert restored["row"]["AnalysisXml"].startswith("<UnivariateAnalysis")


def test_saved_result_snapshot_includes_rehydratable_chain_bytes() -> None:
    import base64
    from bestfit_examples.analysis import _snapshot_node

    project = load_project("viglione-et-al-2013")
    restored = restore_analysis(
        project, "Univariate Distribution Analysis", "MCMC - Systematic (1951-2001)"
    )
    snapshot = _snapshot_node(restored)
    from System import Array, Byte
    from Numerics.Sampling.MCMC import MCMCResults

    encoded = snapshot["mcmc"]["bytes_base64"]
    rehydrated = MCMCResults.FromByteArray(Array[Byte](base64.b64decode(encoded)))
    assert rehydrated.MarkovChains.Length == 6


def test_b17c_snapshot_preserves_ensemble_without_markov_chains() -> None:
    import base64
    from bestfit_examples.analysis import _snapshot_node
    from bestfit_examples.runtime import load_bestfit

    load_bestfit()
    from System import Array, Byte
    from Numerics.Sampling.MCMC import MCMCResults

    restored = restore_analysis(
        load_project("bulletin-17c-examples"), "Univariate Distribution Analysis", "Example #2"
    )
    snapshot = _snapshot_node(restored)
    assert snapshot["mcmc"]["chain_count"] == 0
    assert snapshot["mcmc"]["ensemble_size"] == 10000
    rehydrated = MCMCResults.FromByteArray(Array[Byte](base64.b64decode(snapshot["mcmc"]["bytes_base64"])))
    assert rehydrated.Output.Count == 10000


def test_restore_requires_canonical_analysis_name_and_valid_dependency() -> None:
    project = load_project("viglione-et-al-2013")
    with pytest.raises(KeyError, match="No analysis"):
        restore_analysis(project, "Univariate Distribution Analysis", "unknown")
    altered = dict(project)
    altered["tables"] = dict(project["tables"])
    payload = dict(project["tables"]["<Univariate Distribution>"])
    payload["rows"] = [dict(row) for row in payload["rows"]]
    payload["rows"][0]["InputData"] = "missing input"
    altered["tables"]["<Univariate Distribution>"] = payload
    with pytest.raises(KeyError, match="missing input"):
        restore_analysis(altered, "Univariate Distribution Analysis", "MCMC - Systematic (1951-2001)")


def test_viglione_fitting_restores_all_saved_candidate_results() -> None:
    project = load_project("viglione-et-al-2013")
    restored = restore_analysis(project, "Distribution Fitting Analysis", "Fit - Systematic (1951-2001)")
    assert restored["input"].ExactSeries.Count == 51
    assert restored["analysis"].IsEstimated
    assert restored["analysis"].FittedDistributions.Count == 15
    assert restored["row"]["FittedDistributions"]


def test_b17c_example_two_restores_screening_settings_and_saved_uncertainty() -> None:
    project = load_project("bulletin-17c-examples")
    restored = restore_analysis(project, "Univariate Distribution Analysis", "Example #2")
    assert restored["input"].ExactSeries.Count == 82
    assert restored["input"].NumberOfLowOutliers == 30
    assert restored["input"].LowOutlierThreshold == 782
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].BayesianAnalysis.Results is not None
    assert restored["analysis"].IsEstimated


def test_point_process_restores_original_pot_model_and_results() -> None:
    project = load_project("point-process-examples")
    restored = restore_analysis(project, "Univariate Distribution Analysis", "USC00040741 - Point Process")
    assert restored["model"].GetType().Name == "PointProcessModel"
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].BayesianAnalysis.Results is not None


def test_mixture_restores_original_components_and_results() -> None:
    project = load_project("mixture-distribution-examples")
    restored = restore_analysis(project, "Univariate Distribution Analysis", "Mixture Distribution - 2 Normals")
    assert restored["model"].GetType().Name == "MixtureModel"
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].BayesianAnalysis.Results is not None


def test_bivariate_restores_named_marginals_and_copula_results() -> None:
    project = load_project("bivariate-distribution-examples")
    restored = restore_analysis(project, "Bivariate Distribution Analysis", "AMH Copula")
    from System import Object

    assert restored["row"]["MarginalX"] == "AMH - Marginal X"
    assert restored["row"]["MarginalY"] == "AMH - Marginal Y"
    assert Object.ReferenceEquals(restored["model"].MarginalX, restored["dependencies"]["MarginalX"]["model"])
    assert Object.ReferenceEquals(restored["model"].MarginalY, restored["dependencies"]["MarginalY"]["model"])
    assert restored["analysis"].AnalysisResults is not None


def test_mississippi_rating_uses_original_aligned_series_and_saved_results() -> None:
    project = load_project("usgs-07024175-mississippi-rating-curve")
    restored = restore_analysis(project, "Rating Curve Analysis", "USGS 07024175 Rating Curve")
    assert restored["stage"].Count == 96
    assert restored["discharge"].Count == 96
    assert restored["model"].GetType().Name == "RatingCurve"
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].BayesianAnalysis.Results is not None


def test_synthetic_rating_fixture_keeps_two_and_three_segment_models() -> None:
    project = load_project("synthetic-rating-curve-examples")
    two = restore_analysis(project, "Rating Curve Analysis", "2 Segment Rating Curve")
    three = restore_analysis(project, "Rating Curve Analysis", "3 Segment Rating Curve")
    assert two["model"].NumberOfSegments == 2
    assert three["model"].NumberOfSegments == 3
    assert two["analysis"].AnalysisResults is not None
    assert three["analysis"].AnalysisResults is not None


def test_regression_restores_covariates_forecast_and_original_saved_results() -> None:
    project = load_project("time-series-regression-example")
    restored = restore_analysis(project, "Time Series Analysis", "Multiple Linear Regression")
    assert [name for name in restored["dependencies"]] == [
        "Income", "Production", "Savings", "Unemployment"
    ]
    assert restored["analysis"].ForecastingTimeSteps == 30
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].BayesianAnalysis.Results is not None


@pytest.mark.parametrize("name", ["Simple Linear Regression", "Multiple Linear Regression"])
def test_regression_covariates_preserve_every_saved_parameter_field(name: str) -> None:
    from xml.etree import ElementTree as ET

    restored = restore_analysis(load_project("time-series-regression-example"), "Time Series Analysis", name)
    original = ET.fromstring(restored["row"]["ARIMAX"]).find("Parameters")
    assert original is not None
    actual = [ET.fromstring(str(parameter.ToXElement())) for parameter in restored["model"].Parameters]
    assert len(actual) == len(original)
    for saved, current in zip(original, actual):
        assert ET.canonicalize(ET.tostring(current, encoding="unicode"), strip_text=True) == ET.canonicalize(
            ET.tostring(saved, encoding="unicode"), strip_text=True
        )


def test_composite_restores_named_component_analyses_and_saved_curve() -> None:
    project = load_project("mixed-population-examples")
    restored = restore_analysis(project, "Univariate Distribution Analysis", "Competing Flood Types")
    assert list(restored["dependencies"]) == ["Full POR Snow Driven", "Full POR Rainfall Driven"]
    assert restored["analysis"].Analyses.Count == 2
    assert str(restored["analysis"].CompositeDistributionType) == "CompetingRisks"
    assert restored["analysis"].AnalysisResults is not None


def test_coincident_restores_response_surface_and_saved_frequency_curve() -> None:
    project = load_project("sum-two-normals")
    restored = restore_analysis(project, "Bivariate Distribution Analysis", "CFA - Rho = 0.0")
    assert restored["row"]["BivariateAnalysis"] == "Normal Copula - Rho = 0.0"
    assert restored["analysis"].NumberOfBins == 20
    assert restored["analysis"].XValues.Length == 7
    assert restored["analysis"].YValues.Length == 7
    assert restored["analysis"].ZOutputValues.Length == 20
    assert restored["analysis"].AnalysisResults is not None
    assert restored["analysis"].IsEstimated
    from System import Object

    bivariate = restored["dependencies"]["BivariateAnalysis"]
    for axis in ("X", "Y"):
        marginal = bivariate["dependencies"][f"Marginal{axis}"]["analysis"]
        assert Object.ReferenceEquals(
            getattr(restored["analysis"], f"Marginal{axis}Chain"), marginal.BayesianAnalysis.Results
        )


def test_coincident_rerun_syncs_fresh_marginal_chains_after_dependencies() -> None:
    from bestfit_examples.analysis import _run_graph
    from System import Object

    restored = prepare_rerun("sum-two-normals", "Bivariate Distribution Analysis", "CFA - Rho = 0.0")["restored"]
    assert restored["analysis"].MarginalXChain is None
    assert restored["analysis"].MarginalYChain is None
    _run_graph(restored, [], set())
    bivariate = restored["dependencies"]["BivariateAnalysis"]
    for axis in ("X", "Y"):
        marginal = bivariate["dependencies"][f"Marginal{axis}"]["analysis"]
        assert Object.ReferenceEquals(
            getattr(restored["analysis"], f"Marginal{axis}Chain"), marginal.BayesianAnalysis.Results
        )


def test_coincident_optional_overlay_can_be_blank_in_saved_waimea_case() -> None:
    project = load_project("waimea-river-stage-frequency")
    restored = restore_analysis(
        project, "Bivariate Distribution Analysis", "CFA - Normal - Conditional",
        restore_results=False,
    )
    assert restored["input"] is None
    assert restored["dependencies"]["BivariateAnalysis"]["analysis"] is not None


def test_prepare_rerun_uses_frozen_settings_without_saved_chain() -> None:
    prepared = prepare_rerun(
        "viglione-et-al-2013", "Univariate Distribution Analysis", "MCMC - Systematic (1951-2001)"
    )
    restored = prepared["restored"]
    assert restored["analysis"].BayesianAnalysis.Iterations == 3500
    assert restored["analysis"].BayesianAnalysis.PRNGSeed == 12345
    assert restored["analysis"].BayesianAnalysis.Results is None
    assert prepared["receipt"]["source_sha256"] == restored["source"]["sha256"]
    assert len(prepared["receipt"]["settings_sha256"]) == 64
    assert prepared["receipt"]["status"] == "prepared"


def test_explicit_rerun_writes_success_receipt_after_task_completion(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import json
    import bestfit_examples.analysis as module

    class CompletedTask:
        def GetAwaiter(self):
            return self

        def GetResult(self):
            return None

    class FastAnalysis:
        IsEstimated = True

        def RunAsync(self, progress=None):
            return CompletedTask()

        def ToXElement(self):
            return "<OriginalSettingsRun />"

    monkeypatch.setattr(module, "prepare_rerun", lambda *args: {
        "restored": {"analysis": FastAnalysis(), "table": "Univariate Distribution Analysis", "name": "Example"},
        "receipt": {"status": "prepared", "settings_sha256": "abc"},
    })
    path = tmp_path / "run.json"
    receipt = rerun_analysis(
        "sample", "Univariate Distribution Analysis", "Example", path,
        output_dir=tmp_path / "output",
    )
    assert receipt["status"] == "completed"
    assert json.loads(path.read_text(encoding="utf-8"))["settings_sha256"] == "abc"
    assert receipt["finished_utc"] >= receipt["started_utc"]
    assert receipt["wall_seconds"] >= 0
    snapshot = tmp_path / "output" / receipt["output_snapshot"]
    import gzip

    assert json.loads(gzip.decompress(snapshot.read_bytes()))["analysis_xml"] == "<OriginalSettingsRun />"


def test_rerun_executes_analysis_dependencies_before_target(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import bestfit_examples.analysis as module

    calls = []

    class CompletedTask:
        def GetAwaiter(self):
            return self

        def GetResult(self):
            return None

    class Analysis:
        IsEstimated = True

        def __init__(self, label):
            self.label = label

        def RunAsync(self, progress=None):
            calls.append(self.label)
            return CompletedTask()

        def ToXElement(self):
            return f"<{self.label} />"

    dependency = {"analysis": Analysis("upstream"), "dependencies": {}, "name": "upstream", "table": "Univariate Distribution Analysis"}
    restored = {"analysis": Analysis("target"), "dependencies": {"MarginalX": dependency}, "name": "target", "table": "Bivariate Distribution Analysis"}
    monkeypatch.setattr(module, "prepare_rerun", lambda *args: {
        "restored": restored,
        "receipt": {"status": "prepared", "settings_sha256": "abc"},
    })
    result = rerun_analysis(
        "sample", "Bivariate Distribution Analysis", "target", tmp_path / "receipt.json",
        output_dir=tmp_path / "output", return_restored=True,
    )
    assert calls == ["upstream", "target"]
    assert result["restored"] is restored
    assert result["receipt"]["dependencies"][0]["name"] == "upstream"
    assert restored["plotSourceIdentity"]["kind"] == "rerun"
    assert dependency["plotSourceIdentity"]["runId"] == restored["plotSourceIdentity"]["runId"]


def test_rerun_receipt_omits_full_mcmc_bytes(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import bestfit_examples.analysis as module

    class Task:
        def GetAwaiter(self):
            return self

        def GetResult(self):
            return None

    class Analysis:
        IsEstimated = True

        def RunAsync(self, progress=None):
            return Task()

    monkeypatch.setattr(module, "prepare_rerun", lambda *args: {
        "restored": {"analysis": Analysis(), "dependencies": {}, "name": "example", "table": "Univariate Distribution Analysis"},
        "receipt": {"status": "prepared", "settings_sha256": "abc"},
    })
    monkeypatch.setattr(module, "_snapshot_node", lambda _: {
        "is_estimated": True,
        "mcmc": {"chain_count": 1, "bytes_base64": "Zm9v"},
    })
    receipt = rerun_analysis(
        "sample", "Univariate Distribution Analysis", "example", tmp_path / "receipt.json",
        output_dir=tmp_path / "output",
    )
    assert receipt["diagnostics"]["mcmc"] == {"chain_count": 1}
    assert "bytes_base64" not in (tmp_path / "receipt.json").read_text(encoding="utf-8")


def test_failed_target_keeps_completed_dependency_and_failure_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import json
    import bestfit_examples.analysis as module

    class Task:
        def __init__(self, fail=False):
            self.fail = fail

        def GetAwaiter(self):
            return self

        def GetResult(self):
            if self.fail:
                raise RuntimeError("model failed")

    class Analysis:
        IsEstimated = True

        def __init__(self, fail=False):
            self.fail = fail

        def RunAsync(self, progress=None):
            return Task(self.fail)

    dependency = {"analysis": Analysis(), "dependencies": {}, "name": "upstream"}
    target = {"analysis": Analysis(True), "dependencies": {"MarginalX": dependency}, "name": "target"}
    monkeypatch.setattr(module, "prepare_rerun", lambda *args: {
        "restored": target,
        "receipt": {"status": "prepared", "settings_sha256": "abc"},
    })
    path = tmp_path / "failed.json"
    with pytest.raises(RuntimeError, match="model failed"):
        rerun_analysis("sample", "Bivariate Distribution Analysis", "target", path, output_dir=tmp_path / "output")
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["status"] == "failed"
    assert receipt["dependencies"][0]["name"] == "upstream"


def test_curriculum_runner_lists_exact_cases_without_starting_analysis() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/run_curriculum_analyses.py", "--list"],
        check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "51 selected cases" in result.stdout
    assert "CFA - Normal - Conditional" in result.stdout
    assert "3 Segment Rating Curve" in result.stdout


def test_curriculum_runner_rejects_stale_receipt_and_missing_or_changed_output(tmp_path) -> None:
    import hashlib
    import json
    from scripts.run_curriculum_analyses import _existing_receipt_issue

    expected = {
        "status": "prepared", "project_slug": "fixture", "table": "Time Series Analysis",
        "analysis_name": "case", "settings_sha256": "settings", "source_sha256": "source",
        "source_relative_path": "examples/fixture.bestfit", "example_source_commit": "source-commit",
        "runtime_source_commit": "runtime-commit", "runtime_bestfit_sha256": "bestfit",
        "runtime_numerics_sha256": "numerics",
    }
    output = tmp_path / "outputs"
    path = output / "fixture" / "fresh.json.gz"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"fresh output")
    receipt = dict(expected, status="completed", output_snapshot="fixture/fresh.json.gz")
    receipt["output_snapshot_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt["output_snapshot_bytes"] = path.stat().st_size
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert _existing_receipt_issue(receipt_path, expected, output) is None

    for field in ("settings_sha256", "source_sha256", "runtime_source_commit", "runtime_bestfit_sha256", "runtime_numerics_sha256"):
        changed = dict(receipt, **{field: "other"})
        receipt_path.write_text(json.dumps(changed), encoding="utf-8")
        assert field in _existing_receipt_issue(receipt_path, expected, output)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    path.write_bytes(b"stale output")
    assert "checksum" in _existing_receipt_issue(receipt_path, expected, output)
    path.unlink()
    assert "missing" in _existing_receipt_issue(receipt_path, expected, output)


def test_curriculum_runner_does_not_replace_stale_receipt(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    import json
    import scripts.run_curriculum_analyses as runner

    monkeypatch.setattr(runner, "_cases", lambda: [("fixture", "Time Series Analysis", "case")])
    monkeypatch.setattr(runner, "load_project", lambda slug: {
        "tables": {"Time Series Analysis": {"rows": [{"Name": "case"}]}}
    })
    monkeypatch.setattr(runner, "prepare_rerun", lambda *args: {
        "receipt": {"status": "prepared", "project_slug": "fixture", "table": "Time Series Analysis",
                    "analysis_name": "case", "settings_sha256": "new"}
    })
    monkeypatch.setattr(runner, "rerun_analysis", lambda *args, **kwargs: pytest.fail("stale case was rerun"))
    receipt_dir = tmp_path / "receipts"
    receipt_dir.mkdir()
    path = runner._receipt_path(1, "fixture", "case", receipt_dir)
    path.write_text(json.dumps({"status": "completed", "settings_sha256": "old"}), encoding="utf-8")
    before = path.read_bytes()
    assert runner.main(["--receipt-dir", str(receipt_dir), "--output-dir", str(tmp_path / "outputs")]) == 1
    assert path.read_bytes() == before
    assert "STALE" in capsys.readouterr().out
