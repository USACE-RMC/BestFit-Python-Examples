"""Legacy archive/comparison support, never imported by teaching notebooks.

Restore frozen model analyses through the app's public XML constructors.

This module only deserializes original project cells. It never calls RunAsync,
Estimate, or a sampler during restoration.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
import os
import re
import time
import xml.etree.ElementTree as ET
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _row(project: dict[str, Any], table: str, name: str) -> dict[str, Any]:
    try:
        rows = project["tables"][table]["rows"]
    except KeyError as error:
        raise KeyError(f"No analysis table {table!r}") from error
    matches = [row for row in rows if row.get("Name") == name]
    if len(matches) != 1:
        raise KeyError(f"No analysis {name!r} in {table!r}" if not matches else f"Duplicate analysis {name!r} in {table!r}")
    return matches[0]


def _xml(row: dict[str, Any], field: str, *, required: bool = False) -> Any:
    from System.Xml.Linq import XElement

    content = row.get(field)
    if not content:
        if required:
            raise ValueError(f"Missing {field} for {row.get('Name')}")
        return None
    try:
        return XElement.Parse(content)
    except Exception as error:
        raise ValueError(f"Invalid {field} XML for {row.get('Name')}: {error}") from error


def _saved_mcmc(row: dict[str, Any]) -> Any:
    from System import Array, Byte
    from Numerics.Sampling.MCMC import MCMCResults

    cell = row.get("MCMCResults")
    if not cell:
        return None
    if cell.get("encoding") != "base64":
        raise ValueError(f"Unknown MCMCResults encoding for {row.get('Name')}")
    try:
        compressed = base64.b64decode(cell["data"], validate=True)
        if not compressed:
            return None
        return MCMCResults.FromByteArray(Array[Byte](zlib.decompress(compressed, wbits=-15)))
    except Exception as error:
        raise ValueError(f"Invalid MCMCResults for {row.get('Name')}: {error}") from error


def _saved_uncertainty(row: dict[str, Any], field: str) -> Any:
    from Numerics.Distributions import UncertaintyAnalysisResults

    element = _xml(row, field)
    return None if element is None else UncertaintyAnalysisResults.FromXElement(element)


def _time_series(project: dict[str, Any], name: str) -> tuple[Any, dict[str, Any]]:
    from Numerics.Data import TimeSeries
    from System.Xml.Linq import XElement

    row = _row(project, "Time Series Data", name)
    cell = row.get("TimeSeriesCompressed")
    if cell and cell.get("data"):
        if cell.get("encoding") != "base64":
            raise ValueError(f"Unknown TimeSeriesCompressed encoding for {name}")
        try:
            content = zlib.decompress(base64.b64decode(cell["data"], validate=True), wbits=-15).decode("utf-8")
        except Exception as error:
            raise ValueError(f"Invalid compressed TimeSeries for {name}: {error}") from error
    else:
        content = row.get("TimeSeries")
    if not content:
        raise ValueError(f"No TimeSeries payload for {name}")
    return TimeSeries(XElement.Parse(content)), row


def _sync_coincident_marginal_chains(restored: dict[str, Any]) -> None:
    """Mirror the app wrapper's marginal-chain wiring for a CFA graph."""
    bivariate = restored.get("dependencies", {}).get("BivariateAnalysis")
    if bivariate is None:
        return
    from RMC.BestFit.Analyses import UnivariateAnalysis

    for axis in ("X", "Y"):
        marginal = bivariate["dependencies"][f"Marginal{axis}"]["analysis"]
        bayesian = marginal.BayesianAnalysis if isinstance(marginal, UnivariateAnalysis) else None
        chain = bayesian.Results if bayesian is not None and bayesian.IsEstimated else None
        setattr(restored["analysis"], f"Marginal{axis}Chain", chain)


def restore_analysis(
    project: dict[str, Any], table: str, name: str, *, restore_results: bool = True
) -> dict[str, Any]:
    """Restore a canonical analysis roster entry and its exact saved payload."""
    roster = _row(project, table, name)
    kind = roster.get("Type") if table in {
        "Univariate Distribution Analysis", "Bivariate Distribution Analysis"
    } else table
    payloads = {
        "RMC.BestFit.UI.UnivariateAnalysis": "<Univariate Distribution>",
        "RMC.BestFit.UI.B17CAnalysis": "<Bulletin 17C>",
        "RMC.BestFit.UI.PointProcessAnalysis": "<Point Process>",
        "RMC.BestFit.UI.MixtureAnalysis": "<Mixture Distribution>",
        "RMC.BestFit.UI.BivariateAnalysis": "<Bivariate Distribution>",
        "RMC.BestFit.UI.CoincidentFrequencyAnalysis": "<Coincident Frequency>",
        "RMC.BestFit.UI.CompositeAnalysis": "<Composite Distribution>",
        "Distribution Fitting Analysis": "Distribution Fitting Analysis",
        "Rating Curve Analysis": "Rating Curve Analysis",
        "Time Series Analysis": "Time Series Analysis",
    }
    if kind not in payloads:
        raise NotImplementedError(f"Restoration for {kind!r} is not implemented")
    row = _row(project, payloads[kind], name)
    input_row = None
    if kind not in {"RMC.BestFit.UI.BivariateAnalysis", "Rating Curve Analysis", "Time Series Analysis"}:
        input_name = row.get("InputData")
        if input_name or kind != "RMC.BestFit.UI.CoincidentFrequencyAnalysis":
            input_row = _row(project, "Input Data", input_name)
            if not input_row.get("DataFrame"):
                raise ValueError(f"Missing DataFrame for input {input_name}")

    from bestfit_examples.runtime import load_bestfit

    load_bestfit()
    lock = json.loads((Path(__file__).resolve().parent.parent / "runtime-lock.json").read_text(encoding="utf-8"))
    source_commit = lock.get("exampleSourceCommit", lock["bestFitCommit"])
    if project.get("source", {}).get("repository_commit") != source_commit:
        raise RuntimeError("Frozen example source commit differs from runtime-lock.json")
    from RMC.BestFit.Analyses import (
        ARIMAXAnalysis, BivariateAnalysis, Bulletin17CAnalysis,
        CoincidentFrequencyAnalysis, CompositeAnalysis,
        FittingAnalysis, MixtureAnalysis, PointProcessAnalysis, RatingCurveAnalysis,
        UnivariateAnalysis, WeightedUnivariateAnalysis,
    )
    from RMC.BestFit.Models import (
        ARIMAX, BivariateDistribution, Bulletin17CDistribution, DataFrame,
        MixtureModel, PointProcessModel, RatingCurve, UnivariateDistribution,
    )

    data_frame = DataFrame(_xml(input_row, "DataFrame", required=True)) if input_row else None
    dependencies: dict[str, Any] = {}
    extra: dict[str, Any] = {}
    if kind == "RMC.BestFit.UI.CoincidentFrequencyAnalysis":
        dependency = restore_analysis(
            project, "Bivariate Distribution Analysis", row["BivariateAnalysis"],
            restore_results=restore_results,
        )
        dependencies["BivariateAnalysis"] = dependency
        xml = ET.Element("CoincidentFrequencyAnalysis", {"NumberOfBins": str(row["NumberOfBins"])})
        for field in ("XValues", "YValues", "BivariateResponse"):
            ET.SubElement(xml, field).text = row[field]
        from System import Array, Double, Enum
        from System.Xml.Linq import XElement

        analysis = CoincidentFrequencyAnalysis(
            dependency["analysis"], XElement.Parse(ET.tostring(xml, encoding="unicode"))
        )
        _sync_coincident_marginal_chains({"analysis": analysis, "dependencies": dependencies})
        if row.get("BayesianAnalysis"):
            settings = ET.fromstring(row["BayesianAnalysis"]).attrib
            bayesian = analysis.BayesianAnalysis
            for field in ("CredibleIntervalWidth", "OutputLength", "PRNGSeed"):
                if field in settings:
                    setattr(bayesian, field, float(settings[field]) if field == "CredibleIntervalWidth" else int(settings[field]))
            if "PointEstimator" in settings:
                bayesian.PointEstimator = Enum.Parse(bayesian.PointEstimator.GetType(), settings["PointEstimator"])
        if row.get("ZOutputValues"):
            analysis.SetZOutputValues(Array[Double]([float(value) for value in row["ZOutputValues"].split(",")]))
        if restore_results and row.get("AnalysisResults"):
            analysis.RestoreAnalysisResults(_saved_uncertainty(row, "AnalysisResults"))
        model = dependency["model"]
    elif kind == "Rating Curve Analysis":
        stage, stage_row = _time_series(project, row["StageData"])
        discharge, discharge_row = _time_series(project, row["DischargeData"])
        model = RatingCurve(stage, discharge, _xml(row, "RatingCurve", required=True))
        analysis = RatingCurveAnalysis(
            model, _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
        data_frame, input_row = stage, stage_row
        extra = {"stage": stage, "discharge": discharge, "discharge_row": discharge_row}
    elif kind == "Time Series Analysis":
        series, input_row = _time_series(project, row["TimeSeriesData"])
        model = ARIMAX(series, _xml(row, "ARIMAX", required=True))
        covariates = [part for part in (row.get("Covariates") or "").split("|") if part]
        if covariates:
            from System.Collections.Generic import List
            from Numerics.Data import TimeSeries
            from RMC.BestFit.Models import ModelParameter

            saved_parameters = List[ModelParameter]()
            for parameter in model.Parameters:
                saved_parameters.Add(ModelParameter(parameter.ToXElement()))
            series_list = List[TimeSeries]()
            for covariate in covariates:
                covariate_series, covariate_row = _time_series(project, covariate)
                series_list.Add(covariate_series)
                dependencies[covariate] = {"series": covariate_series, "row": covariate_row}
            model.SetCovariates(series_list)
            # SetCovariates rebuilds default parameters. Restore every frozen
            # value, bound, prior, and fixed flag after alignment is attached.
            model.Parameters = saved_parameters
        analysis = ARIMAXAnalysis(
            model, _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
        data_frame = series
    elif kind == "RMC.BestFit.UI.BivariateAnalysis":
        for axis in ("MarginalX", "MarginalY"):
            dependency_name = row.get(axis)
            if not dependency_name:
                raise ValueError(f"Missing {axis} for {name}")
            dependencies[axis] = restore_analysis(
                project, "Univariate Distribution Analysis", dependency_name,
                restore_results=restore_results,
            )
        model = BivariateDistribution(
            dependencies["MarginalX"]["model"], dependencies["MarginalY"]["model"],
            _xml(row, "BivariateDistribution", required=True),
        )
        analysis = BivariateAnalysis(
            model, _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
    elif kind == "RMC.BestFit.UI.CompositeAnalysis":
        model = None
        root = ET.Element("CompositeAnalysis", {
            "IsEstimated": "false",
            "CompositeDistributionType": row["CompositeDistributionType"],
            "ModelAverageMethod": row["ModelAverageMethod"],
            "Dependency": row["Dependency"],
            "IsMaximum": str(bool(row["IsMaximum"])).lower(),
        })
        ET.SubElement(root, "ProbabilityOrdinates").text = row["ProbabilityOrdinates"]
        for field in ("CorrelationMatrix", "BayesianAnalysis"):
            if row.get(field):
                root.append(ET.fromstring(row[field]))
        from System.Xml.Linq import XElement

        analysis = CompositeAnalysis(XElement.Parse(ET.tostring(root, encoding="unicode")))
        _xml(row, "Analyses", required=True)
        for link in ET.fromstring(row["Analyses"]):
            dependency_name = link.attrib["UnivariateAnalysis"]
            dependency = restore_analysis(
                project, "Univariate Distribution Analysis", dependency_name,
                restore_results=restore_results,
            )
            dependencies[dependency_name] = dependency
            analysis.Analyses.Add(WeightedUnivariateAnalysis(
                dependency["analysis"], float(link.attrib["Weight"])
            ))
        if restore_results and row.get("AnalysisResults"):
            analysis.RestoreAnalysisResults(_saved_uncertainty(row, "AnalysisResults"))
    elif kind == "Distribution Fitting Analysis":
        model = None
        analysis = FittingAnalysis(data_frame, _xml(row, "AnalysisXml", required=True))
    elif kind == "RMC.BestFit.UI.UnivariateAnalysis":
        model = UnivariateDistribution(data_frame, _xml(row, "UnivariateDistribution", required=True))
        analysis = UnivariateAnalysis(
            model,
            _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
            _saved_uncertainty(row, "ChronologyAnalysisResults") if restore_results else None,
        )
    elif kind == "RMC.BestFit.UI.B17CAnalysis":
        model = Bulletin17CDistribution(data_frame, _xml(row, "Bulletin17CDistribution", required=True))
        analysis = Bulletin17CAnalysis(
            model,
            _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
    elif kind == "RMC.BestFit.UI.PointProcessAnalysis":
        model = PointProcessModel(data_frame, _xml(row, "PointProcess", required=True))
        analysis = PointProcessAnalysis(
            model, _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
    else:
        model = MixtureModel(data_frame, _xml(row, "MixtureDistribution", required=True))
        analysis = MixtureAnalysis(
            model, _xml(row, "AnalysisXml", required=True),
            _saved_mcmc(row) if restore_results else None,
            _saved_uncertainty(row, "AnalysisResults") if restore_results else None,
        )
    restored = {
        "model": model,
        "analysis": analysis,
        "input": data_frame,
        "source": project["source"],
        "table": table,
        "name": name,
        "row": row,
        "input_row": input_row,
        "dependencies": dependencies,
        **extra,
    }
    return restored


def prepare_rerun(
    slug: str, table: str, name: str, *, data_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a fresh analysis from a verified snapshot, without starting it."""
    from bestfit_examples.project_data import load_project
    from bestfit_examples.runtime import load_bestfit

    project = load_project(slug, data_root)
    restored = restore_analysis(project, table, name, restore_results=False)
    ignored = {"MCMCResults", "AnalysisResults", "ChronologyAnalysisResults", "UncertaintyAnalysisResults"}
    settings = {
        key: value for key, value in restored["row"].items()
        if key not in ignored and not key.endswith("PlotSettings")
    }
    settings_sha256 = hashlib.sha256(json.dumps(
        settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()
    runtime = load_bestfit()
    receipt = {
        "schema_version": 1,
        "status": "prepared",
        "project_slug": slug,
        "table": table,
        "analysis_name": name,
        "source_sha256": restored["source"]["sha256"],
        "source_relative_path": restored["source"]["relative_path"],
        "example_source_commit": restored["source"]["repository_commit"],
        "runtime_source_commit": runtime["sourceCommit"],
        "runtime_bestfit_sha256": runtime["fileHashes"]["RMC.BestFit.dll"],
        "runtime_numerics_sha256": runtime["fileHashes"]["Numerics.dll"],
        "settings_sha256": settings_sha256,
    }
    return {"restored": restored, "receipt": receipt}


def _run_graph(restored: dict[str, Any], log: list[dict[str, Any]], seen: set[int]) -> None:
    analysis = restored["analysis"]
    identity = id(analysis)
    if identity in seen:
        return
    for dependency in restored.get("dependencies", {}).values():
        if isinstance(dependency, dict) and "analysis" in dependency:
            _run_graph(dependency, log, seen)
    _sync_coincident_marginal_chains(restored)
    started = time.monotonic()
    analysis.RunAsync(None).GetAwaiter().GetResult()
    duration = time.monotonic() - started
    if hasattr(analysis, "IsEstimated") and not analysis.IsEstimated:
        raise RuntimeError(f"RunAsync returned without estimation for {restored.get('name')}")
    log.append({
        "name": restored.get("name"),
        "table": restored.get("table"),
        "wall_seconds": round(duration, 3),
        "status": "completed",
    })
    seen.add(identity)


def _finite_metric(value: Any) -> float | None:
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def _snapshot_node(restored: dict[str, Any]) -> dict[str, Any]:
    analysis = restored["analysis"]
    model = restored.get("model")
    result = getattr(analysis, "AnalysisResults", None)
    bayesian = getattr(analysis, "BayesianAnalysis", None)
    chain = getattr(bayesian, "Results", None) if bayesian is not None else None
    node = {
        "name": restored.get("name"),
        "table": restored.get("table"),
        "analysis_xml": str(analysis.ToXElement()) if hasattr(analysis, "ToXElement") else None,
        "model_xml": str(model.ToXElement()) if model is not None and hasattr(model, "ToXElement") else None,
        "analysis_results_xml": str(result.ToXElement()) if result is not None else None,
        "is_estimated": bool(analysis.IsEstimated) if hasattr(analysis, "IsEstimated") else None,
        "dependencies": {},
    }
    if result is not None:
        node["fit_metrics"] = {
            key: _finite_metric(getattr(result, key))
            for key in ("AIC", "BIC", "DIC", "RMSE")
        }
    if chain is not None:
        from Numerics.Sampling.MCMC import MCMCResults

        markov_chains = chain.MarkovChains
        acceptance_rates = chain.AcceptanceRates
        node["mcmc"] = {
            "chain_count": int(markov_chains.Length) if markov_chains is not None else 0,
            "ensemble_size": int(chain.Output.Count) if chain.Output is not None else 0,
            "saved_samples_per_chain": [int(part.Count) for part in markov_chains] if markov_chains is not None else [],
            "acceptance_rates": [_finite_metric(value) for value in acceptance_rates] if acceptance_rates is not None else [],
            "bytes_base64": base64.b64encode(bytes(MCMCResults.ToByteArray(chain))).decode("ascii"),
        }
    for key, dependency in restored.get("dependencies", {}).items():
        if isinstance(dependency, dict) and "analysis" in dependency:
            node["dependencies"][key] = _snapshot_node(dependency)
    return node


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def _bind_run_identity(restored: dict[str, Any], receipt: dict[str, Any]) -> None:
    """Bind a completed run and its dependencies to one immutable receipt identity."""
    run_id = "sha256:" + hashlib.sha256(json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")).hexdigest()

    def bind(node: dict[str, Any]) -> None:
        node["plotSourceIdentity"] = {
            "kind": "rerun", "id": f"{node['table']}/{node['name']}", "runId": run_id,
        }
        for dependency in node.get("dependencies", {}).values():
            if isinstance(dependency, dict) and "analysis" in dependency:
                bind(dependency)

    bind(restored)


def rerun_analysis(
    slug: str, table: str, name: str, receipt_path: str | Path,
    *, output_dir: str | Path | None = None, return_restored: bool = False,
) -> dict[str, Any]:
    """Explicitly run a fresh frozen analysis, recording success or failure.

    This can be expensive: original MCMC, bootstrap, seed and probability
    settings are kept. Call only from an explicit RUN_ANALYSES branch.
    """
    prepared = prepare_rerun(slug, table, name)
    receipt = prepared["receipt"]
    started = time.monotonic()
    receipt["started_utc"] = datetime.now(timezone.utc).isoformat()
    output = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parent.parent / "output" / "reruns"
    safe_name = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    relative = Path(slug) / f"{safe_name}-{receipt['settings_sha256'][:12]}.json.gz"
    dependency_log: list[dict[str, Any]] = []
    try:
        _run_graph(prepared["restored"], dependency_log, set())
        snapshot = _snapshot_node(prepared["restored"])
        payload = gzip.compress(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8"),
            mtime=0,
        )
        _write_atomic(output / relative, payload)
        receipt["output_snapshot"] = relative.as_posix()
        receipt["output_snapshot_sha256"] = hashlib.sha256(payload).hexdigest()
        receipt["output_snapshot_bytes"] = len(payload)
        receipt["diagnostics"] = {
            key: snapshot[key] for key in ("is_estimated", "fit_metrics") if key in snapshot
        }
        if "mcmc" in snapshot:
            receipt["diagnostics"]["mcmc"] = {
                key: value for key, value in snapshot["mcmc"].items() if key != "bytes_base64"
            }
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(error).__name__}: {error}"
        raise
    else:
        receipt["status"] = "completed"
    finally:
        receipt["dependencies"] = [
            entry for entry in dependency_log
            if (entry["name"], entry["table"]) != (name, table)
        ]
        receipt["wall_seconds"] = round(time.monotonic() - started, 3)
        receipt["finished_utc"] = datetime.now(timezone.utc).isoformat()
        _write_atomic(
            Path(receipt_path),
            (json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"),
        )
    _bind_run_identity(prepared["restored"], receipt)
    return {"restored": prepared["restored"], "receipt": receipt} if return_restored else receipt
