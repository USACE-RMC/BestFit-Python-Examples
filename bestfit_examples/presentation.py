"""Compact comparisons for the notebooks, using existing PlotSpec coordinates."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
import xml.etree.ElementTree as ET


def compare_frequency(cases, title="Frequency alternatives"):
    """Overlay the configured point-estimate curves and retain all source IDs."""
    from bestfit_plots import render_plot
    from IPython.display import display
    import matplotlib.pyplot as plt
    specs = [c.data["plots"]["frequency"] for c in cases]
    spec = deepcopy(specs[0])
    spec["title"] = title
    spec["source"] = {"kind":"comparison", "id":title,
                      "runId":"sha256:"+hashlib.sha256(json.dumps([s["source"] for s in specs],sort_keys=True).encode()).hexdigest()}
    spec["comparedSources"] = [s["source"] for s in specs]
    spec["series"] = []
    colors = ["black","#1f77b4","#d95f02","#238b45","#9467bd","#a63603","#e377c2","#636363","#17becf"]
    for case, original, color in zip(cases,specs,colors):
        candidates = [s for s in original["series"] if s["kind"]=="line" and s["name"] in
                      {"Posterior Mode","Posterior Mean","Computed","Computed Curve","Mean Parameters"}]
        if len(candidates)!=1:
            raise ValueError(f"No unambiguous configured estimate curve for {case.data['name']}")
        curve = deepcopy(candidates[0])
        curve["name"] = case.data["name"]
        curve["style"] = {"color":color,"linewidth":1.5}
        spec["series"].append(curve)
    figure=render_plot(spec)
    display(figure)
    plt.close(figure)


def corrected_nile_dates(case):
    """Apply the documented 26-year display correction, retaining source provenance."""
    from datetime import datetime, timedelta
    from .results import Case
    data=deepcopy(case.data)
    for spec in data["plots"].values():
        is_date_axis = spec["axes"]["x"]["scale"] == "date"
        is_residual_oa_date = (
            spec.get("plotId") == "time_series_analysis.residuals" and not is_date_axis
        )
        if not is_date_axis and not is_residual_oa_date:
            continue
        for series in spec["series"]:
            for key in ("x","xLower","xUpper"):
                if key not in series:
                    continue
                if is_residual_oa_date:
                    epoch = datetime(1899, 12, 30)
                    series[key] = [
                        (lambda shifted: (shifted - epoch).total_seconds() / 86400)(
                            (epoch + timedelta(days=float(value))).replace(
                                year=(epoch + timedelta(days=float(value))).year - 26
                            )
                        ) if value is not None else None
                        for value in series[key]
                    ]
                else:
                    series[key]=[datetime.fromisoformat(v).replace(year=datetime.fromisoformat(v).year-26).isoformat()
                                 if v is not None else None for v in series[key]]
        spec["displayTransform"]={"kind":"date-correction","years":-26,"reason":"Nile source CSV 1871-1970; saved app project 1897-1996"}
        if is_residual_oa_date:
            spec["displayTransform"]["sourceEncoding"] = "OADate"
    data["dateCorrection"]="Nile source CSV dates, -26 years; values and fitted model retained"
    return Case(data)


def case_metrics(cases, *, comparison_scope=None):
    """Show fit metrics with their response/likelihood scope made explicit.

    The table deliberately does not rank rows. A caller may state that rows are
    comparable only after establishing the same response, observations, and
    likelihood. Composite persistence placeholders are shown as unavailable.
    """
    import pandas as pd
    scope = comparison_scope or "Descriptive only — rows may use different responses or likelihoods."
    rows = []
    for case in cases:
        settings = case.data.get("settings", {})
        metrics = dict(case.data.get("metrics", {}))
        composite = settings.get("Analysis") == "CompositeAnalysis"
        metric_note = ""
        if composite and metrics and all(value in (0, 0.0, None) for value in metrics.values()):
            metrics = {key: pd.NA for key in metrics}
            metric_note = "N/A: composite result does not define these fit metrics"
        rows.append({
            "Analysis": case.data["name"],
            "Input / response": settings.get("InputData", "see saved dependencies"),
            "Analysis type": settings.get("Analysis", case.data.get("table", "unknown")),
            **metrics,
            "Metric note": metric_note,
            "Comparison scope": scope,
        })
    return pd.DataFrame(rows)


def _short_sha(value):
    return "sha256:" + value[:12] if value else "unavailable"


def case_provenance(cases):
    """Return compact saved/fresh, source, runtime, and receipt identities."""
    import pandas as pd
    rows = []
    for case in cases:
        receipt = case.data.get("receipt") or {}
        fresh_sha = receipt.get("output_snapshot_sha256")
        rows.append({
            "Analysis": case.data["name"],
            "Origin": case.data.get("origin", "unknown"),
            "Source": _short_sha(case.data.get("sourceSha256") or receipt.get("source_sha256")),
            "Runtime": (case.data.get("runtimeCommit") or receipt.get("runtime_source_commit") or "unavailable")[:12],
            "Settings": _short_sha(receipt.get("settings_sha256")) if receipt else "saved in project snapshot",
            "Receipt / result": _short_sha(fresh_sha) if receipt else "saved snapshot; no rerun receipt",
        })
    return pd.DataFrame(rows)


def trend_ownership(project, names):
    """Read the saved nonstationary trend type owned by each LP-III parameter."""
    import pandas as pd
    rows = project["tables"]["<Univariate Distribution>"]["rows"]
    output = []
    owner_columns = {
        "Mean (of log)": "Mean (of log)",
        "Std Dev (of log)": "Std Dev (of log)",
        "Skew (of log)": "Skew (of log)",
    }
    for name in names:
        matches = [row for row in rows if row["Name"] == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one saved univariate row for {name}")
        root = ET.fromstring(matches[0]["UnivariateDistribution"])
        record = {"Alternative": name}
        trends = root.find("TrendModels")
        for trend in trends if trends is not None else []:
            owner = trend.attrib.get("OwnerName", "")
            column = next((label for prefix, label in owner_columns.items() if owner.startswith(prefix)), None)
            if column:
                record[column] = trend.attrib["Type"]
        output.append(record)
    return pd.DataFrame(output, columns=["Alternative", *owner_columns.values()])


def composite_weights(project, name):
    """Read persisted component weights from one composite analysis."""
    import pandas as pd
    rows = project["tables"]["<Composite Distribution>"]["rows"]
    matches = [row for row in rows if row["Name"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one saved composite row for {name}")
    row = matches[0]
    analyses = ET.fromstring(row["Analyses"])
    return pd.DataFrame([{
        "Alternative": element.attrib["UnivariateAnalysis"],
        "Weight": float(element.attrib["Weight"]),
        "Method": row["ModelAverageMethod"],
    } for element in analyses])


def uncertain_observations(project, name):
    """Expose original uncertain-observation distribution children without CLR use."""
    import pandas as pd
    rows = project["tables"]["Input Data"]["rows"]
    matches = [row for row in rows if row["Name"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one saved input row for {name}")
    root = ET.fromstring(matches[0]["DataFrame"])
    uncertain = root.find("UncertainSeries")
    records = []
    for element in uncertain if uncertain is not None else []:
        distribution = element.find("Distribution")
        if distribution is None:
            raise ValueError(f"Uncertain observation {element.attrib.get('Index')} has no distribution")
        records.append({
            "Index": element.attrib["Index"],
            "Distribution": distribution.attrib["Type"],
            "Mu": float(distribution.attrib["Mu"]),
            "Sigma": float(distribution.attrib["Sigma"]),
            "Plotting position": float(element.attrib["PlottingPosition"]),
        })
    return pd.DataFrame(records, columns=["Index", "Distribution", "Mu", "Sigma", "Plotting position"])
