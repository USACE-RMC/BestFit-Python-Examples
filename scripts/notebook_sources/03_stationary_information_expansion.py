# %% [markdown]
# # 03 · Stationary univariate analysis and information expansion
#
# The Kamp at Zwettl project is a nine-case Bayesian GEV study. The 1951–2005
# record includes the 2002 flood; temporal expansion adds historical intervals and
# a perception window. Causal information is an external quantile prior, not a flood.
# Restart Kernel and Run All constructs every model from raw observations and runs MCMC.
# The parallel API example in BestFit Verification is ViglioneEtAlTests.cs; its
# Jeffreys and point-estimator settings differ from this saved app example.

# %%
from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / "runtime-lock.json").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
from time import perf_counter
from math import log, expm1, isclose
import pandas as pd
from IPython.display import display
from bestfit_examples.runtime import load_bestfit
from bestfit_examples.raw import load_raw
from bestfit_examples.fresh import plot_context, plots, show, record_run
runtime = load_bestfit()
print(runtime)
from System import Array, Double, DateTime
from System.Collections.Generic import List
from Numerics.Data import ProbabilityOrdinates
from Numerics.Distributions import Normal, UnivariateDistributionType
from RMC.BestFit.Models import (DataFrame, ExactData, ExactSeries, IntervalData,
                                ThresholdData, QuantilePrior, UnivariateDistribution)
from RMC.BestFit.Analyses import UnivariateAnalysis
from RMC.BestFit.Estimation import BayesianAnalysis

# %% [markdown]
# ## Original observations and nine alternatives
#
# Each temporal alternative uses its own input series with interval floods and
# threshold evidence. The causal alternatives retain the systematic series and add
# a prior to the 0.2% annual-exceedance quantile.

# %%
raw = load_raw("viglione-et-al-2013")
input_names = ["Systematic (1951-2001)", "Systematic (1951-2005)",
               "Systematic (1951-2001) + Temporal Expansion",
               "Systematic (1951-2005) + Temporal Expansion"]
case_specs = [
    ("MCMC - Systematic (1951-2001)", input_names[0], "none", "PosteriorMean"),
    ("MCMC - Systematic (1951-2005)", input_names[1], "none", "PosteriorMode"),
    ("MCMC - Systematic (1951-2001) + Temporal", input_names[2], "none", "PosteriorMean"),
    ("MCMC - Systematic (1951-2005) + Temporal", input_names[3], "none", "PosteriorMean"),
    ("MCMC - Systematic (1951-2001) + Causal", input_names[0], "causal", "PosteriorMean"),
    ("MCMC - Systematic (1951-2005) + Causal", input_names[1], "causal", "PosteriorMean"),
    ("MCMC - Systematic (1951-2001) + Temporal + Causal", input_names[2], "causal", "PosteriorMean"),
    ("MCMC - Systematic (1951-2005) + Temporal + Causal", input_names[3], "causal", "PosteriorMean"),
    ("MCMC - Systematic (1951-2001) + 3 Quantile Priors", input_names[0], "three", "PosteriorMean"),
]
display(pd.DataFrame(raw["inputs"][input_names[0]]["series"]["ExactSeries"]).head())
print(raw["source"])

# %% [markdown]
# ## Construct the four evidence frames
#
# A threshold's NumberAbove counts additional recorded exceedances. It does not
# duplicate the explicitly entered interval events.

# %%
frames = {}
for input_name in input_names:
    observed = raw["inputs"][input_name]
    frame = DataFrame()
    frame.ExactSeries = ExactSeries()
    for row in observed["series"]["ExactSeries"]:
        point = ExactData(DateTime.Parse(row["DateTime"]), float(row["Value"]))
        point.Index = int(row["Index"])
        point.IsLowOutlier = row.get("IsLowOutlier", "False") == "True"
        frame.ExactSeries.Add(point)
    for row in observed["series"]["IntervalSeries"]:
        frame.IntervalSeries.Add(IntervalData(int(row["Index"]), float(row["LowerValue"]),
                                             float(row["Value"]), float(row["UpperValue"])))
    for row in observed["series"]["ThresholdSeries"]:
        threshold = ThresholdData(int(row["StartIndex"]), int(row["EndIndex"]), float(row["Value"]))
        threshold.NumberAbove = int(row["NumberAbove"])
        frame.ThresholdSeries.Add(threshold)
    frame.PlottingParameter = float(observed["attributes"]["PlottingParameter"])
    assert frame.Lambda == 1.0
    frame.CalculatePlottingPositions()
    frames[input_name] = frame
display(pd.DataFrame([{"Input": name, "Exact": f.ExactSeries.Count,
                       "Intervals": f.IntervalSeries.Count, "Thresholds": f.ThresholdSeries.Count}
                      for name, f in frames.items()]))
assert [frames[name].ExactSeries.Count for name in input_names] == [51, 55, 51, 55]
assert [frames[name].IntervalSeries.Count for name in input_names] == [0, 0, 3, 3]
assert [frames[name].ThresholdSeries.Count for name in input_names] == [0, 0, 1, 1]

# %% [markdown]
# ## Configure the GEV models and run the saved MCMC design
#
# All nine saved app models use Jeffreys' scale prior. The published-result
# Verification tests turn it off, so their parameter tolerances are not direct
# acceptance tolerances for these reruns. Fitted parameters below come from MCMC.

# %%
aep = [1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, .0001, .0002, .0005,
       .001, .002, .005, .01, .02, .05, .1, .2, .3, .5, .7, .8, .9, .95, .98, .99]
analyses, models, timings = {}, {}, {}
for name, input_name, prior_kind, estimator in case_specs:
    model = UnivariateDistribution(frames[input_name], UnivariateDistributionType.GeneralizedExtremeValue)
    model.UseDefaultFlatPriors = True
    model.UseJeffreysRuleForScale = True
    if prior_kind == "causal":
        model.EnableQuantilePriors = True
        model.UseSingleQuantile = True
        priors = List[QuantilePrior]()
        priors.Add(QuantilePrior(.002, Normal(480., 80.)))
        model.QuantilePriors = priors
    elif prior_kind == "three":
        model.EnableQuantilePriors = True
        model.UseSingleQuantile = False
        priors = List[QuantilePrior]()
        priors.Add(QuantilePrior(.1, Normal(100., 20.)))
        priors.Add(QuantilePrior(.01, Normal(250., 40.)))
        priors.Add(QuantilePrior(.001, Normal(500., 60.)))
        model.QuantilePriors = priors
    analysis = UnivariateAnalysis(model)
    analysis.ProbabilityOrdinates = ProbabilityOrdinates(Array[Double](aep))
    bayes = analysis.BayesianAnalysis
    bayes.UseSimulationDefaults = True
    bayes.Type = BayesianAnalysis.SamplerType.DEMCzs
    bayes.NumberOfChains = 6
    bayes.ThinningInterval = 30
    bayes.WarmupIterations = 1200 if prior_kind == "three" else 1750
    bayes.Iterations = 2400 if prior_kind == "three" else 3500
    bayes.PRNGSeed = 12345
    bayes.UseAdvancedSimulationDefaults = True
    bayes.InitialIterations = 300
    bayes.Jump = .971630931303994
    bayes.JumpThreshold = .1
    bayes.SnookerThreshold = .1
    bayes.Noise = 1e-12
    bayes.Scale = 5.6644
    bayes.Beta = .05
    bayes.MaxTreeDepth = 10
    bayes.CredibleIntervalWidth = .95 if prior_kind == "three" else .9
    bayes.OutputLength = 10000
    bayes.PointEstimator = getattr(BayesianAnalysis.PointEstimateType, estimator)
    started = perf_counter()
    analysis.RunAsync(None).GetAwaiter().GetResult()
    timings[name] = perf_counter() - started
    analyses[name], models[name] = analysis, model
    record_run(name, analysis, timings[name], raw=raw, model=model)

# %% [markdown]
# ## Compare fresh estimates and intervals
#
# Read the selected point estimate and credible interval with each case's data
# period and prior. Fit scores across changed evidence or priors are not a ranking.

# %%
rows = []
for name, input_name, prior_kind, estimator in case_specs:
    analysis = analyses[name]
    result = analysis.BayesianAnalysis.Results
    assert analysis.IsEstimated and result is not None
    rows.append({"Case": name, "Input": input_name, "Prior": prior_kind,
                 "Estimator": estimator, "MAP parameters": list(result.MAP.Values),
                 "1% AEP parameter point estimate": float(analysis.AnalysisResults.ModeCurve[aep.index(.01)])})
display(pd.DataFrame(rows))
# Independent Hosking-parameterized GEV inverse CDF for the freshly selected
# parameter point estimate. This checks curve ordinates at common and rare AEPs.
for name, _, _, _ in case_specs:
    distribution = analyses[name].GetPointEstimateDistribution()
    xi, alpha, kappa = (float(distribution.Xi), float(distribution.Alpha),
                         float(distribution.Kappa))
    for probability in (.5, .01, .001):
        t = -log(1.0 - probability)
        expected = xi - alpha * log(t) if abs(kappa) < 1e-12 else (
            xi - alpha * expm1(kappa * log(t)) / kappa)
        actual = float(analyses[name].AnalysisResults.ModeCurve[aep.index(probability)])
        assert isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-8)
diagnostics = []
for name, _, _, _ in case_specs:
    result = analyses[name].BayesianAnalysis.Results
    for i, parameter in enumerate(result.ParameterResults):
        stats = parameter.SummaryStatistics
        diagnostics.append({"Case": name, "Parameter": str(models[name].Parameters[i].DisplayName),
                            "R-hat": float(stats.Rhat), "ESS": float(stats.ESS)})
display(pd.DataFrame(diagnostics))

# %% [markdown]
# ## View the computed frequency and posterior diagnostics
#
# Plot adapters read the analyses above. A completed chain is not itself
# convergence or scientific acceptance; examine the diagnostic views before
# interpreting tail differences.

# %%
specs = {}
for name, input_name, _, _ in case_specs:
    context = plot_context(analyses[name], models[name], name=name, raw=raw,
                           frame=frames[input_name], metadata=raw["inputs"][input_name]["metadata"],
                           unitLabel="Peak discharge (m³/s)")
    specs[name] = plots(context, diagnostics=True)
    show(specs[name]["frequency"])
diagnostic_keys = [key for key in specs[case_specs[0][0]] if key.startswith("diagnostic_")]
print("Diagnostic views:", diagnostic_keys)
if diagnostic_keys:
    show(specs[case_specs[0][0]][diagnostic_keys[0]])

# %% [markdown]
# **Adapt this example:** enter your exact, interval and threshold evidence;
# state quantile-prior sources independently; then fit a newly constructed GEV.
# Source: Viglione et al. (2013), DOI 10.1029/2011WR010782.
