# %% [markdown]
# # 02 · Distribution fitting
#
# Use the Kamp at Zwettl inputs to compare candidate distributions before a focused Bayesian analysis.
# Restart Kernel and Run All constructs and runs every fit from raw observations through pythonnet.
# API reference: `DistributionFitting/FittingAnalysisTests.cs`, `CreateTestDataFrame`,
# `CreateTestFittingAnalysis`, and `Test_FittingAnalysis_WabashRiverData` in BestFit Verification.
# Those methods supply the construction pattern; the data remain the original Kamp examples.

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
from Numerics.Data import ProbabilityOrdinates
from Numerics.Distributions import (Exponential, GammaDistribution, GeneralizedExtremeValue,
    GeneralizedLogistic, GeneralizedNormal, GeneralizedPareto, Gumbel, KappaFour,
    LnNormal, Logistic, LogNormal, LogPearsonTypeIII, Normal, PearsonTypeIII, Weibull)
from RMC.BestFit.Models import DataFrame, ExactData, ExactSeries, IntervalData, ThresholdData
from RMC.BestFit.Analyses import FittingAnalysis

# %% [markdown]
# ## Load the four original inputs
#
# The four alternatives compare 1951–2001 and 1951–2005, each with and without temporal expansion.
# The raw fixture contains values, years, historical bounds and provenance; it contains no fitted objects.
# A perception threshold describes what would have been noticed during a period, not fabricated annual floods.

# %%
raw = load_raw("viglione-et-al-2013")
input_names = ["Systematic (1951-2001)", "Systematic (1951-2005)",
               "Systematic (1951-2001) + Temporal Expansion", "Systematic (1951-2005) + Temporal Expansion"]
display(pd.DataFrame(raw["inputs"][input_names[0]]["series"]["ExactSeries"]).head())
print(raw["source"])

# %% [markdown]
# ## Construct BestFit inputs explicitly
#
# `ExactData` retains the annual index. `IntervalData` carries the lower, central and upper flood estimates.
# `ThresholdData.NumberAbove` counts additional exceedances not already entered explicitly.
# BestFit computes nonexceedance counts and plotting positions after the observations are attached.
# Replace these rows with your own observations while retaining their units and meaning.

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
    frame.PlottingParameter = 0.0
    assert frame.Lambda == 1.0  # Annual observations; no POT-to-annual conversion.
    frame.CalculatePlottingPositions()
    frames[input_name] = frame
display(pd.DataFrame([{"Input": name, "Exact": f.ExactSeries.Count,
                       "Intervals": f.IntervalSeries.Count, "Thresholds": f.ThresholdSeries.Count}
                      for name, f in frames.items()]))

# %% [markdown]
# ## Configure fifteen candidate distributions and execute MLE
#
# The instances below define candidate families; their parameters will be fitted by BestFit.
# `FittingAnalysis.RunAsync` uses the library's MLE and optimizer policy.
# Probability ordinates retain the original example's upper-tail grid. Each iteration constructs
# a distinct analysis. The execution call blocks until that fit has finished.

# %%
aep = [1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5, .0001, .0002, .0005,
       .001, .002, .005, .01, .02, .05, .1, .2, .3, .5, .7, .8, .9, .95, .98, .99]
analyses, timings = {}, {}
for input_name, frame in frames.items():
    analysis = FittingAnalysis(frame)
    analysis.DistributionList.Clear()
    for distribution in (Exponential(), GammaDistribution(), GeneralizedExtremeValue(),
                         GeneralizedLogistic(), GeneralizedNormal(), GeneralizedPareto(),
                         Gumbel(), KappaFour(), LnNormal(), Logistic(), LogNormal(),
                         LogPearsonTypeIII(), Normal(), PearsonTypeIII(), Weibull()):
        analysis.DistributionList.Add(distribution)
    analysis.ProbabilityOrdinates = ProbabilityOrdinates(Array[Double](aep))
    assert not analysis.IsEstimated
    started = perf_counter()
    analysis.RunAsync(None).GetAwaiter().GetResult()
    timings[input_name] = perf_counter() - started
    analyses[input_name] = analysis
    record_run("Fit - " + input_name, analysis, timings[input_name], raw=raw)

# %% [markdown]
# ## Read the results just computed
#
# Keep unsuccessful fits and their messages visible. AIC/BIC rank candidates only within one fitting
# alternative, where observations and likelihood treatment are the same. Scores are not ranked across inputs.
# A favorable within-input score alone does not establish a plausible rare tail.

# %%
candidate_rows = []
for input_name, analysis in analyses.items():
    for fit in analysis.FittedDistributions:
        candidate_rows.append({"Input": input_name, "Distribution": str(fit.Distribution.DisplayName),
                               "Succeeded": fit.FitSucceeded, "AIC": float(fit.AIC),
                               "BIC": float(fit.BIC), "RMSE": float(fit.RMSE),
                               "Failure": str(fit.ErrorMessage)})
candidates = pd.DataFrame(candidate_rows)
display(candidates[candidates.Input == input_names[0]].sort_values("AIC", na_position="last"))
display(candidates.sort_values(["Input", "AIC"]).groupby("Input", sort=False).head(3))
failed_candidates = candidates.loc[~candidates["Succeeded"], ["Input", "Distribution", "Failure"]]
print(f"Unsuccessful candidates across all four inputs: {len(failed_candidates)}")
display(failed_candidates)

# %% [markdown]
# ## Check an independent numerical expectation
#
# For exact-only samples, Normal MLE equals the sample mean and population standard deviation.
# A 0.1% relative tolerance is a conservative optimizer check on these fixed data, not a claim about
# rare quantiles or historical-data likelihoods. It does not test the other families.

# %%
normal_checks = []
for input_name in input_names[:2]:
    values = np.array([float(point.Value) for point in frames[input_name].ExactSeries])
    fit = next(f for f in analyses[input_name].FittedDistributions if isinstance(f.Distribution, Normal))
    assert fit.FitSucceeded
    expected = np.array([values.mean(), values.std(ddof=0)])
    computed = np.array([float(fit.Distribution.Mu), float(fit.Distribution.Sigma)])
    np.testing.assert_allclose(computed, expected, rtol=1e-3, atol=1e-8)
    normal_checks.append({"Input": input_name, "Mean": computed[0], "Expected mean": expected[0],
                          "Sigma": computed[1], "Expected sigma": expected[1]})
display(pd.DataFrame(normal_checks))

# %% [markdown]
# ## Plot fresh in-memory results
#
# The canonical BestFit adapters receive the same `analysis` and `frame` objects above.
# The density view emphasizes the body; the frequency view emphasizes the upper tail.
# Q–Q axes are Data versus Model. Historical observations keep BestFit's plotting positions.

# %%
figure_specs = {}
for input_name in input_names:
    context = plot_context(analyses[input_name], name="Fit - " + input_name, raw=raw,
                           frame=frames[input_name], metadata=raw["inputs"][input_name]["metadata"],
                           unitLabel="Peak discharge (m³/s)")
    figure_specs[input_name] = plots(context)
    print(input_name)
    show(figure_specs[input_name]["frequency"])
show(figure_specs[input_names[0]]["pdf"])
show(figure_specs[input_names[0]]["qq"])

# %% [markdown]
# **Adapt this example:** replace the raw records; choose candidate families and probability ordinates;
# construct a new `FittingAnalysis`, call `RunAsync`, and inspect `FittedDistributions` before plotting.
# Changing periods or historical bounds changes the evidence. Notebook 03 holds the GEV family fixed
# to examine those sources directly. Upstream scientific narratives remain provisional.
