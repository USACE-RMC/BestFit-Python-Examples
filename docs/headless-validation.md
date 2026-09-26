# Headless Python curriculum validation

Validation date: 2026-09-25. The rewrite retains the twelve notebook names and the
51 primary cases in `curriculum-cases.json`, including the original observations,
model choices, priors and analysis settings. Additional marginal and component
fits are executed where the primary cases depend on them. The notebooks themselves
perform construction and execution; neither a saved analysis nor a hidden batch
runner supplies their results.

The teaching reference was `C:\GIT\numerics-python-examples` at
`725a1cd6996fba801b7d47221074a5be5ca1df93`, particularly its distribution fitting,
Bayesian inference, time-series and linear-model examples. C# references below are
relative to `src/RMC.BestFit.Verification` in RMC-BestFit at
`db5807d6e3a85606797cda79542f2d51a80a57a6`. Those files were read to understand APIs;
no Verification test method or blanket suite was invoked. Their synthetic test
scenarios were not substituted for the existing app examples.

## Execution boundary and evidence

Python 3.12.14, .NET 10, RMC.Numerics 2.2.0 and the locked BestFit revision were used.
The managed assembly hashes are recorded in every receipt. The runtime lock was
not changed. Raw fixture provenance retains original app-example commit
`3fa55a0f75bbd583e2fb7fce42180faa376f007c`.

`scripts/validate_notebooks.py --write` creates a new workspace containing only
Python support code, checksummed raw fixtures, response grids and the verified
runtime. It clears notebook outputs and runs each notebook in an independent
kernel. Saved project archives, result caches and earlier rerun outputs are not
copied; an audit hook additionally rejects their Python file access and legacy
restoration imports. This is an accidental-cache guard, not an OS sandbox for
arbitrary CLR code. Source review confirms no such alternative file access.

Each analysis receipt records its fresh run identity, elapsed time, source,
configuration and available diagnostics. Each displayed figure's identity matches
an analysis computed by that notebook; data-preparation figures identify their raw
source instead. Validation checks the complete original case roster and matches
PNG/specification pairs. The identical PNG bytes are embedded in the delivered
notebook, including under the headless Agg backend. Receipt `artifactAudit` and
`notebookOutputAudit` fields retain figure lineage, image hashes, executed-cell
counts and a digest of every cell output. CFA receipts also identify both fresh
marginal chains and their draw counts. `--audit-only` compares the original
complete inventories, hashes and run files, including raw inputs, runtime,
helpers and canonical plotting source, without modifying receipts or running
estimators again. A cleared notebook, replaced table, removed plot pair or changed
helper fails the audit. Historical saved settings are used
only by separate, offline fidelity review, never by execution cells.

Git delivery preserves the exact bytes of checksummed inputs and helpers through
`.gitattributes`, extending the existing notebook/receipt rules. Before commit,
64 input, helper, notebook and receipt files were checked against the staged
blobs and exported with both `core.autocrlf=true` and `false`; all hashes matched.
The runtime lock and other configuration values were unchanged. See the
[Git round-trip evidence](../validation/headless-git-roundtrip.json).

See [machine-readable receipts](../validation/headless/) and the maintained
[copyable Python sources](../scripts/notebook_sources/). Timings include kernel
startup, tables and rendering and vary with machine load; analysis-only timings
also appear in each notebook. Full sampling settings were retained.

| Notebook | Execution | Seconds | Primary cases | Analyses including dependencies | Embedded figures |
|---|---|---:|---:|---:|---:|
| 00 | Passed | 15.250 | 0 | 0 | 4 |
| 01 | Passed | 11.235 | 0 | 0 | 6 |
| 02 | Passed | 9.687 | 4 | 4 | 6 |
| 03 | Passed | 29.546 | 9 | 9 | 10 |
| 04 | Passed | 116.797 | 8 | 8 | 15 |
| 05 | Passed | 23.407 | 4 | 4 | 4 |
| 06 | Passed | 56.297 | 7 | 11 | 7 |
| 07 | Passed | 36.531 | 6 | 18 | 3 |
| 08 | Passed | 51.407 | 4 | 16 | 4 |
| 09 | Passed | 77.031 | 4 | 4 | 6 |
| 10 | Passed | 29.031 | 3 | 3 | 6 |
| 11 | Passed | 17.922 | 2 | 2 | 4 |
| **Total** | **12 passed** | **474.141** | **51** | **79** | **75** |

The final passes took 7.90 minutes of summed notebook runtime. All
75 PNGs are retained inside the notebooks and match the exported fresh artifacts.
The final read-only audit passed for all twelve without changing receipt hashes;
see [audit evidence](../validation/headless-audit.json) and
[visual checks](../validation/headless-visual-review.json). All three offline
settings audits passed for the 79 analyses. The full Python suite passed 87 tests
in 41.237 seconds ([JUnit evidence](../validation/headless-tests.xml)); three
teaching/source checks passed again after the final CFA label change
([source checks](../validation/headless-source-tests.xml)).

## Notebook-by-notebook checks and limitations

### 00 — Time-series data

Reference: `TestData.cs` and `TimeSeriesAnalysis/ARIMAXAnalysisTests.cs` demonstrate
time-series inputs; production Numerics `TimeSeries.MovingAverage` and
`MonthlySeries` resolve calculation semantics. Python constructs `TimeSeries` and
`SeriesOrdinate[DateTime, Double]` from the original USGS dates and values. It
exposes the daily/peak intervals, 365-day averaging window, monthly maximum
operator, missing values, units and explicit stage/discharge timestamp join.
`MovingAverage(365)` and `MonthlySeries(Maximum)` create fresh calculated series
for the table and plots; canonical seasonality uses the freshly constructed
observations. Every rolling mean is checked against independent raw-data rolling
arithmetic (relative 1e-12, absolute 1e-9), and every monthly maximum matches
exactly. The inventory retains the large instantaneous datasets and other original
import routes; it does not claim that mismatched stage/discharge counts are pairs.
Seasonality describes observed spread, not a fitted uncertainty interval.

### 01 — Input data

Reference: `Univariate/VerificationReportTests/ViglioneEtAlTests.cs`, particularly
`Test3_ExactData_1951_2001_TemporalExpansion`, and
`Datasets/UnivariateData/Bulletin17CData.cs` for evidence types; production
`DataFrame.CreateBlockSeries`, `CreatePeaksOverThresholdSeries` and
`CalculatePlottingPositions` for preparation. Python constructs `TimeSeries`,
`DataFrame`, `ExactData`, `IntervalData`, `ThresholdData`, `UncertainData` and
`LogNormal` measurement distributions. Calendar/water-year boundaries, no smoothing,
1-inch POT threshold, five-step separation, period 2, historical bounds and
measurement-error coordinates are visible. Actual block/POT extraction and
`ThresholdDiagnostics.ComputeMeanResidualLife`/`ComputeParameterStability` feed
the displayed tables and six plots. Both 80-value annual series match the raw
source's observed annual values; 233 events/67 exposure years and the event-rate
identity are asserted. Historical and uncertain records remain distinct likelihood
information. Threshold diagnostics do not establish independence or select a
defensible threshold automatically.

### 02 — Distribution fitting

Reference: `DistributionFitting/FittingAnalysisTests.cs`,
`CreateTestDataFrame`, `CreateTestFittingAnalysis`, and
`Test_FittingAnalysis_WabashRiverData`. This was the representative notebook
implemented, executed and inspected before applying its pattern to the rest.
Python constructs the four original Kamp `DataFrame` evidence sets and a
`FittingAnalysis` with fifteen visibly instantiated distribution candidates.
It exposes the original 25 AEP ordinates and calls
`RunAsync(None).GetAwaiter().GetResult()` for each new analysis. Candidate tables
read `FittedDistributions`, including fit failures; frequency, PDF and Q–Q plots
read these same new fits. Normal MLE mean and population standard deviation on
the two exact-only samples agree with direct sample arithmetic within relative
1e-3/absolute 1e-8. This tests that family's point fitting, not all fifteen rare
tails or historical likelihoods. AIC/BIC comparisons are scoped to one input.

### 03 — Stationary information expansion

Reference: `Univariate/VerificationReportTests/ViglioneEtAlTests.cs`, methods
`Test1_ExactData_1951_2001` through
`Test9_ExactData_1951_2001_CausalExpansion_TheePriors`. Python constructs four
evidence frames, nine GEV `UnivariateDistribution` models, `QuantilePrior`
objects and nine `UnivariateAnalysis` objects. Historical intervals, perception
windows, Normal quantile priors, Jeffreys' scale rule, point estimator, AEP grid
and every sampler control are visible. The three-prior case retains its
1200/2400 warmup/iteration setting and 95% interval; other cases use 1750/3500
and 90%. Each `RunAsync` supplies fresh point curves, posterior summaries,
R-hat/ESS and canonical frequency/diagnostic plots. The Hosking GEV inverse-CDF
formula independently checks fresh point-curve ordinates at AEP .5/.01/.001
(relative 1e-10, absolute 1e-8). The published Verification scenarios disable
Jeffreys and use different point estimators, so their recovery tolerances are not
claimed for these preserved examples. Tail interpretation still requires mixing
and prior-sensitivity review.

### 04 — Nonstationary Brays Bayou

Reference: `Univariate/ValidationTests/NonstationaryValidationTests.cs`, production
`UnivariateDistribution.SetTrendModel`, and
`Univariate/CompositeTests/CompositePredictiveRecoveryTests.cs` (`CreateComposite`).
Python constructs the original LP-III input, seven `UnivariateDistribution` and
`UnivariateAnalysis` pairs, then three `WeightedUnivariateAnalysis` children and
a `CompositeAnalysis`. Constant, linear, logistic and step links retain their
ownership of mean/scale/skew, start year 1929, evaluation year 2024 and prior
bounds. Chain counts/thinning/initial iterations vary with each original case;
Logistic–Logistic retains 20000 posterior outputs. The seven `RunAsync` calls
produce DIC, conditional curves, chronology and chain diagnostics.
`EstimateModelWeights` and composite `RunAsync` use only the original three
selected children. DIC weights agree with independently normalized
`exp(-0.5 * (DIC - min(DIC)))` to 1e-12. The composite has no independent chain
and its zero-valued fit-metric placeholders are not scientific scores. These
checks do not establish causality or adequacy of extrapolated trends.

### 05 — Bulletin 17C

Reference: `Univariate/Bulletin17CTests/B17CExampleTests.cs`, `Test_Example2` and
`Test_Example4`; `Datasets/UnivariateData/Bulletin17CData.cs`, `GetExample2` and
`GetExample4`; production `Bulletin17CAnalysis.RunAsync` for uncertainty.
Python constructs exact/interval/threshold evidence, four
`Bulletin17CDistribution` models and `Bulletin17CAnalysis` objects. Original
zeros, low-flood flags/threshold, historical windows, AEPs, seed, 90% width and
10000 MVN versus 1000 BCB outputs are visible. Orestimba uses MVN, Pueblo linked
MVN, with a BCB alternative for each. `RunAsync` performs GMM and uncertainty
propagation. Tables read `GMM.BestParameterSet.Values` and new point curves;
plots read new confidence intervals. The three log-parameter coordinates meet
the Verification worked-example targets at absolute 1e-3. This does not validate
interval coverage. BestFit GMM with preserved low-flood interpretation is distinct
from the official EMA/MGBT workflow; the uncertainty ensemble is not an MCMC
posterior even though its controls reside on `BayesianAnalysis`.

### 06 — Advanced univariate

References: `Univariate/PointProcessTests/PointProcessRecoveryTests.cs`
(`Test_NonSeasonalProductionGenerator_RecoversParent`,
`Test_SeasonalProductionGenerator_RecoversParentAndBothChangePoints`);
`Univariate/MixtureTests/MixtureRecoveryTests.cs`
(`NormalMixture2D_BayesianRecovery`, `ZeroInflatedNormalMixture2D_BayesianRecovery`);
`Univariate/CompositeTests/CompositePredictiveRecoveryTests.cs` and
`CompositeOracleVerificationTests.cs` (`MixtureCdf_MatchesExactWeightedNormalSum`,
`MaximumComposite_MatchesIndependentAndComonotonicClosedForms`). Python constructs
`PointProcessModel`, GEV `UnivariateDistribution`, two-Normal `MixtureModel`,
four LogNormal child models, their analysis objects and two `CompositeAnalysis`
objects. Threshold/exposure, August versus October year start, seasonality,
zero inflation, .75/.25 mixture weights, independent maximum rule and full
case-specific samplers are explicit. Eleven `RunAsync` calls produce the seven
primary curves and all dependency results. Rate 253/67 and zero mass .1 are
checked from observations; independent Normal CDF and product/weighted-sum
identities check the new mixture/composite distributions at relative/absolute
1e-10. Fresh R-hat/ESS are displayed. These identities do not establish posterior
recovery, point-process model adequacy or resolve mixture label switching. The
positive-component log display preserves the zero atom in the computed model.

### 07 — Bivariate distributions

Reference: `Bivariate/BivariateAnalysisParameterRecoveryTests.cs`, methods
`RecoverNormalCopulaParameters`, `RecoverJoeCopulaParameters`,
`RecoverGumbelCopulaParameters`, `RecoverFrankCopulaParameters`,
`RecoverClaytonCopulaParameters` and `RecoverAMHCopulaParameters`, for constructing
and fitting marginal/copula models. Python constructs twelve Normal
`UnivariateDistribution`/`UnivariateAnalysis` marginals, six
`BivariateDistribution` copulas and six `BivariateAnalysis` objects. Original
paired indices, six copula families, priors (including the AMH X exception),
inference-from-margins method and individual sampler settings are visible.
Eighteen `RunAsync` calls feed the six-case parameter/diagnostic table and the
original Normal-copula scatter/CDF/density views. The fresh Normal copula's
`CDF(.5,.5)` agrees with `1/4 + asin(rho)/(2*pi)` to absolute 1e-8.
This is an analytic copula arithmetic check, not six-family posterior recovery.
Negative density contour labels are natural-log joint density evaluated on CDF
coordinates, not probabilities or copula density alone.

### 08 — Coincident frequency

Reference: `Bivariate/CoincidentFrequencyAnalysisTests.cs`, methods
`SumOfNormals_RhoZero_MatchesClosedForm`, `SumOfNormals_RhoPositive_MatchesClosedForm`
and `SumOfNormals_RhoNegative_MatchesClosedForm`, for dependency construction,
response grids and the independent Normal-sum calculation. Those tests deliberately
omit marginal chains to isolate their point-curve check. The app-example uncertainty
workflow instead follows production
`RMC.BestFit.UI/Elements/BivariateAnalysis/CoincidentFrequencyAnalysis.cs`,
`SyncMarginalChainsToInnerAnalysis`: Python explicitly assigns the fresh
`BayesianAnalysis.Results` to `MarginalXChain` and `MarginalYChain`. It asserts CLR
object identities and 10000 draws per marginal before running CFA. Python
constructs and runs all eight marginal models, four copulas and four
`CoincidentFrequencyAnalysis` objects, supplying fresh marginal chains. The
original Normal-sum 7×7 grids and Waimea 10×5 stage surface are checksummed plain
input fixtures. Historical/low-flood information, Waimea regional-skew/quantile
priors, conditional Makaweli data, bin counts, seed, estimator and interval width
remain explicit. The zero-correlation case retains 20 bins/95%; the other cases
retain 50 bins/90%. Fresh `ZOutputValues` and `AnalysisResults` feed response
tables/curves; marginal and copula R-hat/ESS are shown separately. Normal-sum
AEPs are monotone and meet maximum/mean absolute discrepancy bounds .05/.01
against the analytical sum using freshly fitted means/scales/rho, matching the
Verification integration-check scale. This does not validate Waimea's engineered
stage surface or establish uncertainty coverage. Copula estimation conditions on
fitted marginal point values; CFA independently resamples the marginal and copula
chains, rather than constructing a joint posterior. Waimea's stationary likelihood
uses top-level parameter priors; inactive stale nested trend priors in the old
serialization are not installed as competing settings.

### 09 — Rating curves

References: `RatingCurve/RatingCurveExampleFixtures.cs` and
`RatingCurve/RatingCurveExampleRecoveryTests.cs`, especially
`Bayesian_OneSegment_RecoversExampleCurve`, `Bayesian_TwoSegment_RecoversExampleCurve`
and `Bayesian_ThreeSegment_RecoversExampleCurve`, for construction, likelihood and
headless recovery workflows. Python constructs paired `TimeSeries`, four
`RatingCurve` and `RatingCurveAnalysis` objects. It retains Mississippi's 96
irregular pairs and the three original 300-point synthetic datasets, one/two/three
segments, uniform bounds, Jeffreys rule, log10-discharge error, stage grids,
full samplers and the USGS posterior-mode exception. Four `RunAsync` calls feed
fresh parameter estimates, RMSE, R-hat/ESS, rating curves and USGS residual/Q–Q
views. Before fitting, fresh model likelihoods at generating parameters agree
with independent SciPy-authored Verification oracle constants to absolute 1e-4
(observed differences below 7e-7 on rounded source data). Only the oracle
constants are used; SciPy does not estimate any notebook model. This validates
likelihood arithmetic, not sampler convergence, segment identifiability or
extrapolation beyond measurements.

### 10 — Classic time series

Reference: `TimeSeriesAnalysis/ARIMAXAnalysisTests.cs`,
`Test_EstimateParameters_ARIMA110`, `Test_EstimateParameters_ARIMA111`,
`Test_EstimateParameters_LinearTrend_Only` and
`Test_EstimateParameters_AR1_Seasonal`; `Datasets/TimeSeriesData/RealTimeSeriesData.cs`
for context. Python constructs three `TimeSeries`, `ARIMAX` and `ARIMAXAnalysis`
objects. Airline (1,1,1), Nile (1,1,0), and Mauna Loa quadratic/Fourier structure,
training counts 120/80/632, no transformation, priors, full sampler settings and
zero future horizon are visible. Three `RunAsync` calls supply fresh prediction
curves, fit metrics, residuals and chain diagnostics. Independent raw-data AR/MA
recurrences or explicit trend/Fourier means agree with residuals and Gaussian
data likelihood at relative 1e-12/absolute 1e-8. The source Nile dates remain
1897–1996 in the model; an explicit display-only shift labels 1871–1970. Airline
retains the documented poor mixing (maximum R-hat about 1.262, minimum ESS about
51.6) and residual concerns; execution is not acceptance of its forecasts.

### 11 — Regression

Reference: `TimeSeriesAnalysis/ARIMAXAnalysisTests.cs`,
`Test_EstimateParameters_SimpleRegression_RValidation` and
`Test_EstimateParameters_MultipleRegression_RValidation`. Python constructs five
aligned quarterly `TimeSeries`, two `ARIMAX(0,0,0)` models,
`List[TimeSeries]` covariates through `SetCovariates`, and `ARIMAXAnalysis`.
Original predictors, uniform bounds, intercept, no transformation, Jeffreys rule,
149/187 training split, full samplers, BlockBootstrap and 30 future quarters are
visible. Two `RunAsync` calls feed fresh coefficient/fit/R-hat/ESS tables,
prediction and residual plots. Explicit raw-data `X @ beta` residuals and Gaussian
data likelihood match at relative 1e-12/absolute 1e-9. Prediction figures mark both
the end of training and end of observations. Independent predictor bootstraps do
not preserve cross-predictor dependence; coefficients are conditional associations
and these checks do not establish causal or forecasting validity.

## Review scope

The initial representative example and the completed curriculum were reviewed for
visible construction/configuration/execution/result access, retained case coverage,
settings fidelity and plot lineage. Visual review covers every regenerated figure,
including labels, units, dates, contour readability, uncertainty terminology and
zero-inflated log display. Numerical checks are deliberately scoped above;
successful execution, convergence and scientific acceptance remain separate.

Validation occurred on local branch `headless-python-teaching`, based on
`f94c84c55db73caf69addc39b17907757c488ef6`, before commit, merge or push. Existing
`.vs/` content, license, citation metadata, authors and reviewer credit were
preserved. Earlier validation documents describe the superseded saved-viewer
workflow and are retained only as historical evidence.
