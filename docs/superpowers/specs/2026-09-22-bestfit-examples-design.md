# BestFit Python examples design

Approved in the task conversation on 2026-09-22. The implementation instruction authorizes the complete five-package plan and scoped local commits, not publication.

## Goal and constraints

Build twelve concise, source-backed teaching notebooks following the saved BestFit application examples. Reuse one importable Python plotting implementation in RMC-BestFit's existing `skills/bestfit-frequency` bundle. Cover all 45 distinct app plot slots and their supported variants with data and close app-style parity. Do not alter desktop plotting or statistical algorithms. Add read-only REST/MCP exports where plot source data is missing. Default notebook execution displays validated saved results; an explicit `RUN_ANALYSES=True` reruns the original model, sampler, bootstrap, prior, seed, and probability settings. Do not shorten computations or change methods to make checks pass.

Baseline repositories: RMC-BestFit `3fa55a0f75bbd583e2fb7fce42180faa376f007c`; BestFit-Python-Examples `e0cba2ef1c884ddf0e3a06d0d2fb47f291d8d4f8`. Use .NET 10 and RMC.Numerics 2.2.0, with exact source identity for BestFit rather than trusting assembly version alone. Original dirty checkouts remain untouched. No pushes, PRs, releases, skill-profile installations, or blanket Verification runs are authorized by this implementation.

## Curriculum

| ID | Notebook | Saved examples and teaching intent |
|---|---|---|
| 00 | Time-series data and setup | USGS daily/instantaneous/annual-peak/measured stage-discharge distinctions; frozen imports, dates and units; brief GHCN/CHMN/ABOM/DSS/manual routes. |
| 01 | Input data | Moose calendar/water-year maxima, direct annual peaks, GHCN POT; exact/uncertain/interval/perception-threshold data using app fixtures. |
| 02 | Distribution fitting | Four Viglione `Fit - ...` alternatives, fifteen candidate distributions, failed-fit filtering, information criteria and frequency/PDF/CDF/PP/QQ diagnostics. |
| 03 | Stationary univariate and information expansion | Nine Kamp at Zwettl GEV alternatives: 1951-2001 versus 1951-2005; temporal, causal, combined and three-quantile-prior cases. |
| 04 | Nonstationary univariate | Seven Brays Bayou LP-III alternatives, constant/linear/logistic/step trends, location/scale combinations and DIC model average. |
| 05 | Bulletin 17C examples 2 and 4 | Orestimba low floods/zeros and Pueblo historical intervals/nonexceedance windows; paired MVN/BCB alternatives, official context and method distinctions. |
| 06 | Advanced univariate | Big Bear POT point process versus AMS GEV and seasonal case; mixture/zero-inflated cases; mixed-population mixture versus competing-risk composite. |
| 07 | Bivariate | App copula examples, saved marginal models, scatter/density/joint-exceedance in value and marginal-CDF coordinates. Clearly label synthetic teaching cases. |
| 08 | Coincident frequency | Sum of two Normals at negative/zero/positive correlation, followed by Waimea/Makaweli response-frequency case. |
| 09 | Rating curves | Mississippi 07024175, 96 paired observations and one-segment model; brief app synthetic two/three-segment contrasts. |
| 10 | Classic time-series models | Airline ARIMA(1,1,1), Nile ARIMA(1,1,0), Mauna Loa quadratic trend plus seasonality, training/forecast and residual diagnostics. |
| 11 | Regression | Consumption~Income and multiple regression with Income/Production/Savings/Unemployment; preserve saved training/forecast settings and AR=MA=0. |

Each notebook has two or three compact vignettes, visible model choices, provenance, selected figures, useful tables and interpretation. IO/interop/plot helpers must not obscure those choices. All variants belong in a separate plot gallery rather than flooding notebooks with plots. Existing synthetic-only notebooks and redundant scripts are superseded; retain intentional verified outputs, remove incidental outputs and tracked bytecode.

## Scientific and source boundaries

Saved projects contain both legacy XML text and compressed payloads: support both, do not treat an empty legacy column as missing data. Export typed records with dates/indices, units, bounds, perception windows/counts, low-outlier flags, quantile priors, model/analysis configuration, revision and checksums. Preserve source projects.

Viglione uses GEV, not the LP-III stated in its tutorial. Cite Viglione et al. (2013), *Flood frequency hydrology: 3. A Bayesian analysis*, DOI 10.1029/2011WR010782. Mixed-population margins are LogNormal. Regression cases are ARIMAX configurations with AR=MA=0.

Bulletin 17C source: England et al., version 1.1 (May 2019), Appendix 10, https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf. Example 2: Orestimba 11274500, 82 observations (1932-2013), including 12 zeros; saved app screening has 30 flagged observations and threshold 782 cfs. Do not replace this with the newer 94-record download. Example 4: Pueblo 07099500, 81 exact, four interval and four threshold records including long nonexceedance information. Describe official EMA/MGBT separately from app GMM and its MVN/BCB uncertainty. Neither sampled B17C ensemble nor confidence limits are Bayesian MCMC. Existing published log-parameter comparisons use absolute 1e-3 rounding tolerance.

Nile has the same 100 values in the project and CSV but saved project dates are 1897-1996. Notebook uses the documented CSV dates 1871-1970 and records this provenance deviation; no silent app-project edit. Mississippi data are in compressed fields: 96 exactly timestamp-aligned stage/discharge observations, with original USGS response text.

## Plot coverage and interfaces

One canonical `bestfit_plots` package under the RMC-BestFit skill directory, included in the skill ZIP and installed by the notebooks. Preserve existing `plot_frequency.py` behavior through a thin wrapper. Pythonnet and API adapters normalize source data into a common versioned `PlotSpec`; renderers do no estimation. A spec carries plot ID, variant, source/run identity, axis semantics, units, named series and display defaults. APIs supply missing same-run data without estimation or inconsistent snapshots.

| Owner | Plot IDs / slots |
|---|---|
| Time-series data (4) | series, seasonality, acf, pacf |
| Input data (11) | chronology, frequency, seasonality, density, histogram, qq, acf, pacf, mean_residual_life, modified_scale, shape |
| Fitting (5) | frequency, pdf, cdf, pp, qq |
| Univariate (2) | frequency, chronology |
| B17C (1) | frequency |
| Point process (1) | frequency |
| Mixture (1) | frequency |
| Composite (1) | frequency |
| Bivariate (1) | distribution: scatter/density/joint-exceedance times values/CDF coordinates |
| Coincident (1) | frequency with linear response axis |
| Rating (4) | curve, residuals, residual_histogram, residual_qq |
| Time-series analysis (6) | series, residuals, residual_histogram, residual_qq, residual_acf, residual_pacf |
| Shared diagnostics (7) | trace, histogram, kde, acf, mean_log_likelihood, pair_heatmap, influence |

Manifest entries include app factory/population methods, adapter, source fixture, supported variants and evidence status. Preserve probability-axis orientation, marker styles, interval labels, configured point estimator and original omissions. Cover quantile priors/penalties, comparison/component overlays, nonstationary conditions, POT/AMS and seasonal variants, supported Bayesian/GMM influence views. Plot parity is data and close style, not pixel identity or WPF interaction/customization.

## Validation and completion

Validate source round trips; notebook schema and independent fresh kernels; cache invalidation; paired runtime identity; failed-fit and mixed-result handling; missing/misaligned/nonfinite plotting arrays and log-axis omissions. Compare fixed app result geometry and independently exported app plots, not merely the two Python adapters against each other. Full original-setting reruns require receipts and visible diagnostics. Use appropriate fast Python and four BestFit .NET suites; do not run blanket Verification or alter scientific methods/tolerances. Each package ends in independent review, passing checks, scoped local commits and an exact cross-repository handoff. Engineering parity is not a scientific endorsement.
