"""Create deterministic, source-bound PlotSpec artifacts outside notebook prose."""
from __future__ import annotations
import math
import xml.etree.ElementTree as ET


def finite(value):
    value = float(value)
    return value if math.isfinite(value) else None


def analysis_snapshot(slug, restored):
    """Copy saved model/result geometry through the canonical plotting package."""
    from .runtime import load_bestfit
    from bestfit_plots import validate_spec
    from bestfit_plots.adapters.response_models import bivariate_plots, coincident_plots, rating_plots, time_series_analysis_plots
    from bestfit_plots.adapters.frequency import fitting_plots, frequency_plots
    from bestfit_plots.adapters.diagnostics import diagnostic_plots
    analysis, model, row = restored["analysis"], restored["model"], restored["row"]
    kind = str(analysis.GetType().Name)
    if kind=="FittingAnalysis":
        plots = fitting_plots(restored)
    elif kind=="BivariateAnalysis":
        plots = bivariate_plots(restored)
    elif kind=="CoincidentFrequencyAnalysis":
        plots = coincident_plots(restored)
    elif kind=="RatingCurveAnalysis":
        plots = rating_plots(restored)
    elif kind=="ARIMAXAnalysis":
        plots = time_series_analysis_plots(restored)
    else:
        plots = frequency_plots(restored)
    if kind!="FittingAnalysis":
        plots.update({"diagnostic_"+k:v for k,v in diagnostic_plots(restored).items()})
    if slug == "mixture-distribution-examples" and bool(getattr(model, "IsZeroInflated", False)):
        # Independent desktop export: mixture.frequency--zero_inflated.json.
        # A near-zero positive ordinate otherwise expands Matplotlib to 1e-16,
        # making the nonzero distribution unreadable. Coordinates remain intact.
        plots["frequency"]["axes"]["y"].update(minimum=0.1, maximum=1000.0)
        plots["frequency"]["displayTransform"] = {
            "kind": "desktop-view-limits",
            "reference": "validation/plot-parity/app-reference/mixture.frequency--zero_inflated.json",
            "reason": "Match the saved desktop log range; values below 0.1 remain stored but outside the view.",
        }
    for spec in plots.values():
        validate_spec(spec)
    runtime = load_bestfit()
    settings = {"Analysis":kind, "Saved project":restored["source"]["relative_path"]}
    for key in ("InputData", "MarginalX", "MarginalY", "TimeSeriesData", "StageData", "DischargeData", "Covariates"):
        if row.get(key):
            settings[key] = row[key]
    if row.get("AnalysisXml"):
        xml = ET.fromstring(row["AnalysisXml"])
        settings.update(xml.attrib)
        for child in xml:
            if child.tag in {"BayesianAnalysis", "GMM", "GMMOptions", "ProbabilityOrdinates", "Ordinates"}:
                settings.update({child.tag+"."+k:v for k,v in child.attrib.items()})
    parameters = []
    if model is not None and hasattr(model, "ToXElement"):
        model_xml = ET.fromstring(str(model.ToXElement()))
        settings.update({"Model."+k:v for k,v in model_xml.attrib.items()})
        distribution = model_xml.find("Distribution")
        if distribution is not None:
            settings["Model.Distribution"] = distribution.get("Type", "")
    if restored.get("dependencies"):
        settings["Dependencies"] = "; ".join(restored["dependencies"])
    if model is not None and hasattr(model, "Parameters"):
        parameters = [{"Parameter":str(p.DisplayName), "Estimate":finite(p.Value), "Fixed":bool(p.IsFixed),
                       "Lower":finite(p.LowerBound), "Upper":finite(p.UpperBound),
                       "Prior":str(p.PriorDistribution)} for p in model.Parameters]
    metrics = {}
    result = getattr(analysis, "AnalysisResults", None)
    for key in ("AIC", "BIC", "DIC", "WAIC", "RMSE"):
        if result is not None and hasattr(result,key):
            metrics[key] = finite(getattr(result,key))
    candidates = []
    if kind=="FittingAnalysis":
        candidates = [{"Distribution":str(f.Distribution.DisplayName) if f.Distribution is not None else "Unavailable",
                       "Succeeded":bool(f.FitSucceeded), "Shown":bool(f.ShowResults),
                       "AIC":finite(f.AIC), "BIC":finite(f.BIC), "RMSE":finite(f.RMSE),
                       "Failure":str(f.ErrorMessage)} for f in analysis.FittedDistributions]
    return {"schemaVersion":1,"slug":slug,"table":restored["table"],"name":restored["name"],
            "origin":"saved-app", "sourceSha256":restored["source"]["sha256"],
            "sourceCommit":restored["source"]["repository_commit"],
            "runtimeCommit":runtime["sourceCommit"], "runtimeHashes":runtime["fileHashes"],
            "settings":settings, "parameters":parameters, "metrics":metrics, "candidates":candidates, "plots":plots}
