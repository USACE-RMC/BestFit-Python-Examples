"""Plot conversion and execution receipts for objects constructed in notebook cells.

No data loading, model construction, configuration, or estimation occurs here.
"""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import math
import os
import uuid

ROOT = Path(__file__).resolve().parents[1]
_RUN_IDENTITIES = {}


def plot_context(analysis, model=None, *, name, raw, frame=None, metadata=None,
                 dependencies=None, **extra):
    """Attach provenance/labels to a completed in-memory analysis for canonical adapters."""
    if not analysis.IsEstimated:
        raise ValueError("Compute the analysis before creating its plot context")
    run_id = _RUN_IDENTITIES.get(id(analysis), (None, str(uuid.uuid4())))[1]
    return {"analysis": analysis, "model": model, "input": frame,
            "name": name, "source": raw["source"], "input_row": metadata or {},
            "row": {"Name": name}, "dependencies": dependencies or {},
            "plotSourceIdentity": {"kind": "rerun", "id": name, "runId": run_id},
            **extra}


def plots(context, diagnostics=False):
    """Convert fresh object results using the pinned canonical plotting utilities."""
    from bestfit_plots.adapters.frequency import fitting_plots, frequency_plots
    from bestfit_plots.adapters.response_models import bivariate_plots, coincident_plots, rating_plots, time_series_analysis_plots
    kind = str(context["analysis"].GetType().Name)
    adapters = {"FittingAnalysis": fitting_plots, "BivariateAnalysis": bivariate_plots,
                "CoincidentFrequencyAnalysis": coincident_plots, "RatingCurveAnalysis": rating_plots,
                "ARIMAXAnalysis": time_series_analysis_plots}
    result = adapters.get(kind, frequency_plots)(context)
    if diagnostics:
        from bestfit_plots.adapters.diagnostics import diagnostic_plots
        result.update({"diagnostic_" + key: value for key, value in diagnostic_plots(context).items()})
    if bool(getattr(context.get("model"), "IsZeroInflated", False)):
        result["frequency"]["axes"]["y"].update(minimum=0.1, maximum=1000.0)
        result["frequency"]["displayTransform"] = {
            "kind": "desktop-view-limits", "reason": "Show the positive component on the original 0.1–1000 log range; the zero mass remains in the computed distribution."}
    return result


def show(spec):
    """Display a canonical figure and retain its fresh-source identity for validation."""
    from .plotting import render_plot
    from IPython.display import Image, display
    import matplotlib.pyplot as plt
    figure = render_plot(spec)
    try:
        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=140, facecolor="white")
        png = buffer.getvalue()
        # Explicit PNG display works in fresh kernels even with the headless Agg
        # backend, where display(figure) otherwise produces only a text repr.
        display(Image(data=png, format="png"),
                metadata={"bestfit": {"plotId": spec["plotId"], "source": spec["source"]}})
        directory = os.environ.get("BESTFIT_FIGURE_DIR")
        if directory:
            target = Path(directory)
            target.mkdir(parents=True, exist_ok=True)
            index = len(list(target.glob("*.png")))
            prefix = target / f"{index:03d}-{spec['plotId']}"
            Path(str(prefix) + ".png").write_bytes(png)
            Path(str(prefix) + ".json").write_text(json.dumps(spec, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    finally:
        plt.close(figure)


def record_run(name, analysis, seconds, *, raw, model=None):
    """Record measured runtime and current settings after the notebook's execution call."""
    from .runtime import load_bestfit
    if not analysis.IsEstimated:
        raise RuntimeError(f"{name}: execution returned without an estimated result")
    def finite(value):
        number = float(value)
        return number if math.isfinite(number) else None
    result = getattr(analysis, "AnalysisResults", None)
    run_id = str(uuid.uuid4())
    _RUN_IDENTITIES[id(analysis)] = (analysis, run_id)
    receipt = {"name": name, "class": str(analysis.GetType().Name), "status": "completed", "runId": run_id,
               "seconds": round(seconds, 3), "source": raw["source"], "runtime": load_bestfit(),
               "analysisSettings": str(analysis.ToXElement()),
               "modelSettings": str(model.ToXElement()) if model is not None else None,
               "metrics": {key: finite(getattr(result, key)) for key in ("AIC", "BIC", "DIC", "RMSE")
                           if result is not None and hasattr(result, key)}}
    bayes = getattr(analysis, "BayesianAnalysis", None)
    chain = getattr(bayes, "Results", None) if bayes is not None else None
    if chain is not None and chain.ParameterResults is not None:
        receipt["diagnostics"] = [{"parameter": i, "Rhat": finite(p.SummaryStatistics.Rhat),
                                   "ESS": finite(p.SummaryStatistics.ESS)}
                                  for i, p in enumerate(chain.ParameterResults)]
    if hasattr(analysis, "MarginalXChain"):
        from System import Object
        receipt["marginalChains"] = {}
        for axis in ("X", "Y"):
            marginal_chain = getattr(analysis, f"Marginal{axis}Chain")
            identity = None
            if marginal_chain is not None:
                for dependency, dependency_id in _RUN_IDENTITIES.values():
                    dependency_bayes = getattr(dependency, "BayesianAnalysis", None)
                    dependency_chain = getattr(dependency_bayes, "Results", None)
                    if dependency_chain is not None and Object.ReferenceEquals(marginal_chain, dependency_chain):
                        identity = {"runId": dependency_id, "name": str(dependency.Name),
                                    "outputDraws": int(marginal_chain.Output.Count)}
                        break
                if identity is None:
                    raise ValueError(f"{name}: marginal {axis} does not identify a recorded fresh analysis")
            receipt["marginalChains"][axis] = identity
    if model is not None and hasattr(model, "Parameters"):
        receipt["parameters"] = [{"name": str(p.Name), "value": finite(p.Value),
                                  "lower": finite(p.LowerBound), "upper": finite(p.UpperBound),
                                  "prior": str(p.PriorDistribution), "fixed": bool(p.IsFixed)}
                                 for p in model.Parameters]
    directory = os.environ.get("BESTFIT_RUN_DIR")
    if directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(name.encode()).hexdigest()[:12]
        (path / (key + ".json")).write_text(json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{name}: completed in {seconds:.2f} s. Execution alone does not establish convergence or scientific acceptance.")
    return receipt
