# %% [markdown]
# # 09 · Rating curves
#
# Fit a stage–discharge relationship to paired field measurements and compare
# one-, two-, and three-segment synthetic examples. Restart Kernel and Run All
# constructs each time series and estimates each curve from raw observations.
# API reference: `RatingCurveExampleFixtures.cs` creates the model from paired
# time series; `RatingCurveExampleRecoveryTests.cs` runs the Bayesian analysis.

# %%
from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / "runtime-lock.json").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
from time import perf_counter
import numpy as np
import pandas as pd
from IPython.display import display
from bestfit_examples.runtime import load_bestfit
from bestfit_examples.raw import load_raw
from bestfit_examples.fresh import plot_context, plots, show, record_run
runtime = load_bestfit()
print(runtime)
from System import Array, Double, DateTime
from Numerics.Data import TimeSeries, TimeInterval, SeriesOrdinate
from Numerics.Distributions import Uniform
from RMC.BestFit.Models import RatingCurve
from RMC.BestFit.Analyses import RatingCurveAnalysis
from RMC.BestFit.Estimation import BayesianAnalysis

# Independent SciPy discharge-space log-likelihoods from the pinned Verification
# fixture, evaluated at known generating parameters (not saved BestFit estimates).
synthetic_oracle = {
    1: ([1., .24389656534469958, 2.6666666666666665, .05], -1577.7594156516989),
    2: ([1., .24389656534469958, 2.6666666666666665, 10., 2.9462998885606555, 1.67, .05],
        -1850.3134085800252),
    3: ([1., .24389656534469958, 2.6666666666666665, 10., 2.9462998885606555, 1.67,
         15., 3.6095332363473847, 1.67, .05], -1888.5687896304166),
}

# %% [markdown]
# ## Field and synthetic paired observations
#
# The USGS 07024175 series holds 96 irregular-date stage/discharge pairs. The
# synthetic project holds 300 daily stages and a separate discharge series per
# segment design. Dates, units and measured values come from the raw fixtures;
# saved fitted curves and posterior draws are never inputs to this notebook.

# %%
field_raw = load_raw("usgs-07024175-mississippi-rating-curve")
synthetic_raw = load_raw("synthetic-rating-curve-examples")
case_specs = [
    ("USGS 07024175 Rating Curve", field_raw, "USGS 07024175 Measured Stage",
     "USGS 07024175 Measured Discharge", 1, "PosteriorMode", 8, 40),
    ("1 Segment Rating Curve", synthetic_raw, "Stage Data",
     "1 Segment - Flow Data", 1, "PosteriorMean", 8, 40),
    ("2 Segment Rating Curve", synthetic_raw, "Stage Data",
     "2 Segment - Flow Data", 2, "PosteriorMean", 14, 70),
    ("3 Segment Rating Curve", synthetic_raw, "Stage Data",
     "3 Segment - Flow Data", 3, "PosteriorMean", 20, 100),
]
display(pd.DataFrame([{"Case": name, "Stage records": len(raw["series"][stage]["records"]),
                       "Discharge records": len(raw["series"][flow]["records"]),
                       "Time interval": raw["series"][stage]["attributes"]["TimeInterval"]}
                      for name, raw, stage, flow, *_ in case_specs]))
print(field_raw["source"])
print(synthetic_raw["source"])

# %% [markdown]
# ## Construct time series and rating models
#
# For the irregular field data, add each timestamp explicitly. For the synthetic
# daily data, the public constructor builds the regular dates from the first date
# and values. Both series in each case must align on date; do not pair by sorted
# values. BestFit uses Gaussian residuals in log10 discharge and a Jeffreys
# prior on the residual scale. The default flat coefficient priors are preserved.

# %%
analyses, models, timings, pair_counts = {}, {}, {}, {}
for name, raw, stage_name, flow_name, segments, estimator, chains, thinning in case_specs:
    stage_rows = raw["series"][stage_name]["records"]
    flow_rows = raw["series"][flow_name]["records"]
    assert len(stage_rows) == len(flow_rows)
    assert all(s["Index"] == q["Index"] for s, q in zip(stage_rows, flow_rows))
    assert all(float(q["Value"]) > 0 for q in flow_rows)
    interval = raw["series"][stage_name]["attributes"]["TimeInterval"]
    assert interval == raw["series"][flow_name]["attributes"]["TimeInterval"]
    if interval == "Irregular":
        stage = TimeSeries(TimeInterval.Irregular)
        discharge = TimeSeries(TimeInterval.Irregular)
        for s, q in zip(stage_rows, flow_rows):
            stage.Add(SeriesOrdinate[DateTime, Double](DateTime.Parse(s["Index"]), float(s["Value"])))
            discharge.Add(SeriesOrdinate[DateTime, Double](DateTime.Parse(q["Index"]), float(q["Value"])))
    else:
        assert interval == "OneDay"
        start = DateTime.Parse(stage_rows[0]["Index"])
        stage = TimeSeries(TimeInterval.OneDay, start,
                           Array[Double]([float(row["Value"]) for row in stage_rows]))
        discharge = TimeSeries(TimeInterval.OneDay, start,
                               Array[Double]([float(row["Value"]) for row in flow_rows]))
    model = RatingCurve(stage, discharge, segments)
    model.UseDefaultFlatPriors = True
    model.UseJeffreysRuleForScale = True
    assert model.NumberOfSegments == segments
    if raw is synthetic_raw and segments in (1, 3):
        # The source examples admit exponent zero; the current constructor
        # starts at 0.1 for these coordinates. Preserve authored support.
        for parameter_index in ([2] if segments == 1 else [2, 5, 8]):
            model.Parameters[parameter_index].LowerBound = 0.0
            model.Parameters[parameter_index].UpperBound = 5.0
            model.Parameters[parameter_index].PriorDistribution = Uniform(0.0, 5.0)
    if raw is synthetic_raw:
        generating_parameters, oracle_log_likelihood = synthetic_oracle[segments]
        likelihood = float(model.DataLogLikelihood(Array[Double](generating_parameters)))
        assert abs(likelihood - oracle_log_likelihood) < 1e-4
    analysis = RatingCurveAnalysis(model)
    analysis.Name = name
    analysis.UseDefaultStageBins = True
    analysis.StageBins = 100
    # These are the saved app's display/processing ranges, not estimated parameters.
    if raw is field_raw:
        analysis.MinStage, analysis.MaxStage = -10.32, 45.96
    else:
        analysis.MinStage, analysis.MaxStage = -.7326817927, 21.7691008757
    bayes = analysis.BayesianAnalysis
    bayes.UseSimulationDefaults = True
    bayes.Type = BayesianAnalysis.SamplerType.DEMCzs
    bayes.NumberOfChains = chains
    bayes.ThinningInterval = thinning
    bayes.WarmupIterations = 1750
    bayes.Iterations = 3500
    bayes.PRNGSeed = 12345
    bayes.UseAdvancedSimulationDefaults = True
    bayes.InitialIterations = {1: 400, 2: 700, 3: 1000}[segments]
    bayes.Jump = {1: .8414570696119914, 2: .63608175575157, 3: .53218417864494993}[segments]
    bayes.CredibleIntervalWidth = .9
    bayes.OutputLength = 10000
    bayes.PointEstimator = getattr(BayesianAnalysis.PointEstimateType, estimator)
    started = perf_counter()
    analysis.RunAsync(None).GetAwaiter().GetResult()
    timings[name] = perf_counter() - started
    analyses[name], models[name] = analysis, model
    pair_counts[name] = model.GetDataAlignmentCounts().Item3
    record_run(name, analysis, timings[name], raw=raw, model=model)

# %% [markdown]
# ## Read fitted results and inspect residuals
#
# A smooth curve can conceal systematic residual structure. The residual views
# show deviations in log10 discharge, the same scale used by the likelihood.
# These four likelihoods describe distinct datasets and should not be ranked
# against one another to select the number of controls for the field site.

# %%
rows = []
for name, raw, stage_name, flow_name, segments, estimator, chains, thinning in case_specs:
    analysis, model = analyses[name], models[name]
    result = analysis.BayesianAnalysis.Results
    assert analysis.IsEstimated and result is not None
    rows.append({"Case": name, "Segments": segments, "Paired measurements": pair_counts[name],
                 "Parameters": model.NumberOfParameters, "Estimator": estimator,
                 "Scale posterior mean": float(result.PosteriorMean.Values[model.NumberOfParameters-1]),
                 "AIC": float(analysis.AnalysisResults.AIC),
                 "BIC": float(analysis.AnalysisResults.BIC),
                 "RMSE": float(analysis.AnalysisResults.RMSE)})
display(pd.DataFrame(rows))
field_name = "USGS 07024175 Rating Curve"
field_result = analyses[field_name].BayesianAnalysis.Results
display(pd.DataFrame({"Parameter": [str(p.DisplayName) for p in models[field_name].Parameters],
                      "Posterior mean": [float(v) for v in field_result.PosteriorMean.Values]}))
field_figures = plots(plot_context(analyses[field_name], models[field_name],
                                  name=field_name, raw=field_raw,
                                  metadata=field_raw["series"]["USGS 07024175 Measured Stage"]["metadata"],
                                  discharge_row=field_raw["series"]["USGS 07024175 Measured Discharge"]["metadata"]))
show(field_figures["curve"])
show(field_figures["residuals"])
show(field_figures["residual_qq"])

# %% [markdown]
# ## Controlled segment examples
#
# These are separately generated discharges on the same 300 daily stages.
# Their curves demonstrate where added hydraulic controls become active; they
# are not evidence that the USGS site requires additional segments.

# %%
for name in ("1 Segment Rating Curve", "2 Segment Rating Curve", "3 Segment Rating Curve"):
    result = analyses[name].BayesianAnalysis.Results
    display(pd.DataFrame({"Parameter": [str(p.DisplayName) for p in models[name].Parameters],
                          "Posterior mean": [float(v) for v in result.PosteriorMean.Values]}))
    show(plots(plot_context(analyses[name], models[name],
                            name=name, raw=synthetic_raw,
                            metadata=synthetic_raw["series"]["Stage Data"]["metadata"],
                            discharge_row=synthetic_raw["series"][name[0] + " Segment - Flow Data"]["metadata"]))["curve"])

# %% [markdown]
# ## Inspect parameter-level MCMC diagnostics
#
# The R-hat and effective sample size are computed by BestFit for each fresh
# posterior coordinate, including the residual scale. Inspect them before using
# uncertainty bands. Good chain mixing cannot establish hydraulic suitability,
# correct segment count, or independence of the field measurements.

# %%
diagnostic_rows = []
for name, *_ in case_specs:
    result = analyses[name].BayesianAnalysis.Results
    assert analyses[name].IsEstimated and result is not None
    for index, parameter in enumerate(result.ParameterResults):
        summary = parameter.SummaryStatistics
        diagnostic_rows.append({"Case": name,
                                "Parameter": str(models[name].Parameters[index].DisplayName),
                                "R-hat": float(summary.Rhat), "ESS": float(summary.ESS),
                                "Lower 90%": float(summary.LowerCI),
                                "Upper 90%": float(summary.UpperCI)})
display(pd.DataFrame(diagnostic_rows))

# %% [markdown]
# **Adapt this example:** enter paired stage/discharge observations with matching
# timestamps, choose a justified number of segments and stage range, fit the curve,
# and inspect residuals, posterior diagnostics and physical plausibility together.
