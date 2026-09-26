# %% [markdown]
# # 11 · Regression through the time-series model
#
# These are the app's simple and multiple Consumption regressions. Restart Kernel and Run All
# constructs five frozen quarterly series, both ARIMAX models, and runs the saved Bayesian settings.
# API reference: BestFit Verification `TimeSeriesAnalysis/ARIMAXAnalysisTests.cs` and
# `Datasets/TimeSeriesData/RealTimeSeriesData.cs`. The actual observations are from this project's
# frozen source; the Verification scenarios are not used as data or model settings.

# %%
from pathlib import Path
import sys
from time import perf_counter
ROOT = Path.cwd() if (Path.cwd() / "runtime-lock.json").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import pandas as pd
import numpy as np
from IPython.display import display
from bestfit_examples.runtime import load_bestfit
from bestfit_examples.raw import load_raw
from bestfit_examples.fresh import plot_context, plots, show, record_run
print(load_bestfit())
from System import Array, DateTime, Double
from System.Collections.Generic import List
from Numerics.Data import TimeInterval, TimeSeries, SeriesOrdinate
from Numerics.Distributions import Uniform
from RMC.BestFit.Models import ARIMAX, Transform
from RMC.BestFit.Analyses import ARIMAXAnalysis
from RMC.BestFit.Estimation import BayesianAnalysis

# %% [markdown]
# ## Construct aligned quarterly observations
#
# `Consumption` is the response. Income, Production, Savings and Unemployment are the only
# available saved predictors. All 187 records run from 1970 Q1 to 2016 Q3. The dates are
# retained exactly, so `SetCovariates` can align predictors by timestamp.

# %%
raw = load_raw("time-series-regression-example")
series = {}
for name in ("Consumption", "Income", "Production", "Savings", "Unemployment"):
    source = raw["series"][name]
    ts = TimeSeries(getattr(TimeInterval, source["attributes"]["TimeInterval"]))
    for row in source["records"]:
        ts.Add(SeriesOrdinate[DateTime, Double](DateTime.Parse(row["Index"]), float(row["Value"])))
    series[name] = ts
response_dates = [str(p.Index.ToString("o")) for p in series["Consumption"]]
assert all([str(p.Index.ToString("o")) for p in ts] == response_dates for ts in series.values())
display(pd.DataFrame([{"Series": name, "Observations": ts.Count,
                       "First": str(ts[0].Index.ToString("yyyy-MM-dd")),
                       "Last": str(ts[ts.Count-1].Index.ToString("yyyy-MM-dd"))}
                      for name, ts in series.items()]))
print(raw["source"])

# %% [markdown]
# ## Configure the saved regression designs
#
# These are ARIMAX(0,0,0) models with current-quarter predictors (`XOrderB=0`), intercept,
# no transform, no seasonal or trend component, and the saved flat parameter priors plus
# Jeffreys' scale rule. Both retain automatic training selection: 149 of 187 observations.
# The tuples give the original parameter bounds and uniform prior limits. DEMCzs initializes
# from these priors; the fitted coefficients will come from the newly computed chains.

# %%
cases = {
    "Simple Linear Regression": {
        "covariates": ["Income"], "chains": 6, "thin": 30, "initial": 300,
        "jump": .97163093130399403,
        "parameters": [(.01, 10), (-10, 10), (1.11022302462516e-16, 10)]},
    "Multiple Linear Regression": {
        "covariates": ["Income", "Production", "Savings", "Unemployment"],
        "chains": 12, "thin": 60, "initial": 600, "jump": .68704682033565467,
        "parameters": [(.01, 10), (-10, 10), (-10, 10), (-10, 10), (-10, 10),
                       (1.11022302462516e-16, 10)]},
}
models = {}
for name, settings in cases.items():
    model = ARIMAX(series["Consumption"])
    model.TransformType = getattr(Transform, "None")
    model.IncludeIntercept = True
    model.IncludeSeasonality = False
    model.TrendType = getattr(ARIMAX.Trend, "None")
    model.AROrderP = 0
    model.DiffOrderD = 0
    model.MAOrderQ = 0
    model.XOrderB = 0
    model.CovariateExtension = ARIMAX.CovariateExtensionMethod.BlockBootstrap
    covariates = List[TimeSeries]()
    for covariate_name in settings["covariates"]:
        covariates.Add(series[covariate_name])
    model.SetCovariates(covariates)
    model.UseDefaultFlatPriors = True
    model.UseJeffreysRuleForScale = True
    model.UseDefaultTrainingSteps = True
    assert model.TrainingTimeSteps == 149
    assert model.Parameters.Count == len(settings["parameters"])
    for parameter, (lower, upper) in zip(model.Parameters, settings["parameters"]):
        parameter.LowerBound = lower
        parameter.UpperBound = upper
        parameter.PriorDistribution = Uniform(lower, upper)
        parameter.IsPositive = parameter.Name.startswith("Scale")
        parameter.IsFixed = False
    models[name] = model
display(pd.DataFrame([{"Analysis": name, "Predictors": ", ".join(c["covariates"]),
                       "Training": models[name].TrainingTimeSteps,
                       "Observed holdout": models[name].TimeSeries.Count - models[name].TrainingTimeSteps,
                       "Future steps": 30}
                      for name, c in cases.items()]))

# %% [markdown]
# ## Run each saved Bayesian analysis
#
# `analysis.ForecastingTimeSteps=30` extends beyond the observed response; the 38 observed
# holdout quarters remain a separate assessment window. `BlockBootstrap` extends each predictor
# independently, retaining within-series blocks but not their joint dependence. Deterministic
# predictions extend predictors with their means; predictive uncertainty includes bootstrap draws.

# %%
analyses, timings = {}, {}
for name, settings in cases.items():
    analysis = ARIMAXAnalysis(models[name])
    analysis.ForecastingTimeSteps = 30
    bayes = analysis.BayesianAnalysis
    bayes.Type = BayesianAnalysis.SamplerType.DEMCzs
    bayes.UseSimulationDefaults = True
    bayes.UseAdvancedSimulationDefaults = True
    bayes.NumberOfChains = settings["chains"]
    bayes.ThinningInterval = settings["thin"]
    bayes.WarmupIterations = 1750
    bayes.Iterations = 3500
    bayes.PRNGSeed = 12345
    bayes.InitialIterations = settings["initial"]
    bayes.Jump = settings["jump"]
    bayes.JumpThreshold = .1
    bayes.SnookerThreshold = .1
    bayes.Noise = 1e-12
    bayes.Scale = 5.6644
    bayes.Beta = .05
    bayes.MaxTreeDepth = 10
    bayes.CredibleIntervalWidth = .9
    bayes.OutputLength = 10000
    bayes.PointEstimator = BayesianAnalysis.PointEstimateType.PosteriorMean
    started = perf_counter()
    analysis.RunAsync(None).GetAwaiter().GetResult()
    timings[name] = perf_counter() - started
    analyses[name] = analysis
    record_run(name, analysis, timings[name], raw=raw, model=models[name])

# %% [markdown]
# ## Independently check the fitted regression arithmetic
#
# With AR=MA=d=0 and no transformation, the training mean is X beta and errors are Gaussian.
# Compute both from the raw rows and the coefficients just estimated, then compare with BestFit's
# residuals and data likelihood. The absolute 1e-9 tolerance allows floating-point summation error;
# it is not a tolerance on statistical accuracy, MCMC convergence or future forecasts.

# %%
arithmetic_checks = []
for name, model in models.items():
    n = model.TrainingTimeSteps
    y = np.array([float(row["Value"]) for row in raw["series"]["Consumption"]["records"][:n]])
    design = np.column_stack([np.ones(n)] + [
        [float(row["Value"]) for row in raw["series"][predictor]["records"][:n]]
        for predictor in cases[name]["covariates"]])
    parameters = np.array([float(p.Value) for p in model.Parameters])
    expected_residuals = y - design @ parameters[:-1]
    sigma = parameters[-1]
    expected_log_likelihood = float(np.sum(-np.log(sigma * np.sqrt(2 * np.pi))
                                           - .5 * (expected_residuals / sigma)**2))
    managed_parameters = Array[Double](parameters.tolist())
    np.testing.assert_allclose(list(model.Residuals(managed_parameters)), expected_residuals,
                               rtol=1e-12, atol=1e-9)
    np.testing.assert_allclose(model.DataLogLikelihood(managed_parameters), expected_log_likelihood,
                               rtol=1e-12, atol=1e-9)
    arithmetic_checks.append({"Case": name, "Independent Gaussian data log-likelihood": expected_log_likelihood,
                              "Checked training rows": n})
display(pd.DataFrame(arithmetic_checks))

# %% [markdown]
# ## Compare fits for the same response and inspect mixing
#
# The two cases share Consumption observations and ARIMAX likelihood, so their DIC values can
# be compared. Lower fit criteria do not establish causal effects or guarantee future accuracy.
# R-hat and ESS below come from these new chains. A completed chain is not convergence acceptance.

# %%
fit_rows, parameter_rows = [], []
for name, analysis in analyses.items():
    result = analysis.AnalysisResults
    fit_rows.append({"Analysis": name, "AIC": float(result.AIC), "BIC": float(result.BIC),
                     "DIC": float(result.DIC), "RMSE": float(result.RMSE),
                     "Seconds": timings[name]})
    for parameter, estimate in zip(models[name].Parameters, analysis.BayesianAnalysis.Results.ParameterResults):
        stats = estimate.SummaryStatistics
        parameter_rows.append({"Analysis": name, "Parameter": str(parameter.Name),
                               "Posterior mean": float(stats.Mean),
                               "R-hat": float(stats.Rhat), "ESS": float(stats.ESS)})
display(pd.DataFrame(fit_rows))
display(pd.DataFrame(parameter_rows))

# %% [markdown]
# ## Fresh prediction and residual views
#
# The prediction plot labels the training, observed holdout and future parts on a date axis.
# Residual structure motivates a separate model question; these examples retain their zero
# AR, differencing and MA orders. Compare predictive bands and residual dependence together.

# %%
from bestfit_plots.adapters.common import line
figures = {}
for name, analysis in analyses.items():
    context = plot_context(analysis, models[name], name=name, raw=raw,
                           metadata=raw["series"]["Consumption"]["metadata"])
    figures[name] = plots(context)
    # Mark where the observed holdout ends and the 30 future quarters begin.
    prediction = figures[name]["series"]
    training_marker = next(s for s in prediction["series"] if s["name"] == "End of Training Period")
    observation_end = str(series["Consumption"][series["Consumption"].Count - 1].Index.ToString("yyyy-MM-ddTHH:mm:ss"))
    prediction["series"].append(line("End of Observations (future begins)",
                                      [observation_end, observation_end], training_marker["y"],
                                      color="#555555", linestyle=":"))
    print(name)
    show(figures[name]["series"])
show(figures["Multiple Linear Regression"]["residuals"])
show(figures["Multiple Linear Regression"]["residual_pacf"])

# %% [markdown]
# **Adapt this example:** use your own aligned response and predictor series, choose the model
# and forecast horizon, and inspect mixing and held-out behavior before interpreting coefficients.
