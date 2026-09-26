# Headless notebook implementation and validation map

The September 25 correction preserves the existing curriculum and case roster in
`curriculum-cases.json`. Verification code supplies API examples, not replacement
datasets. The runtime remains BestFit `db5807d6e3a85606797cda79542f2d51a80a57a6`,
.NET 10, and RMC.Numerics 2.2.0.

| Notebook | Existing examples | C# API references under RMC.BestFit.Verification | Visible Python workflow |
|---|---|---|---|
| 00 | USGS series; GHCN, CHMN, DSS, manual routes | TestData.cs; TimeSeriesAnalysis/ARIMAXAnalysisTests.cs; Numerics time-series notebook | Raw timestamp/value records → TimeSeries/SeriesOrdinate → transformations and summaries → plots |
| 01 | Moose River calendar/water-year maxima, Big Bear POT, Viglione history, Sinnemahoning uncertainty | Univariate/VerificationReportTests/ViglioneEtAlTests.cs; Bulletin17CTests; production DataFrame | Construct/extract exact data, IntervalData, ThresholdData, UncertainData → plotting positions → input diagnostics |
| 02 | Four Kamp/Zwettl inputs, 15 families | DistributionFitting/FittingAnalysisTests.cs | DataFrame/ExactSeries plus historical records → FittingAnalysis and candidate distributions → RunAsync → fitted distributions, metrics, fresh plots |
| 03 | Nine Viglione GEV alternatives | Univariate/VerificationReportTests/ViglioneEtAlTests.cs | Construct each input/model → explicit parameter and quantile priors and sampler settings → UnivariateAnalysis.RunAsync → curves/chains/diagnostics |
| 04 | Seven Brays Bayou LP-III models and DIC average | Univariate recovery fixtures; Univariate/CompositeTests; production parameter links | Raw peaks → location/scale links → seven UnivariateAnalysis runs → WeightedUnivariateAnalysis/CompositeAnalysis → conditional curves |
| 05 | Original B17C examples 2 and 4; MVN/BCB | Univariate/Bulletin17CTests | DataFrame with original low-flood flags and historical bounds → Bulletin17CDistribution/Analysis → GMM uncertainty runs → confidence intervals |
| 06 | Big Bear point processes/GEV; two Normal mixtures; competing/mixture flood types | Univariate/PointProcessTests; MixtureTests; CompositeTests | Explicit component models, seasons/weights/zero inflation → primary and dependency runs → fresh component and combined results |
| 07 | Six original copulas | Bivariate/BivariateAnalysisParameterRecoveryTests.cs | Raw paired marginals → marginal runs → BivariateDistribution/copula → BivariateAnalysis.RunAsync → scatter/contours/diagnostics |
| 08 | Three sums of Normals and Waimea | Bivariate/CoincidentFrequencyAnalysisTests.cs | Marginal models and dependence → response grid → CoincidentFrequencyAnalysis with fresh marginal chains → RunAsync → response frequency |
| 09 | Mississippi measurements and 1/2/3 segment synthetic ratings | RatingCurve/RatingCurveExampleFixtures.cs; RatingCurveExampleRecoveryTests.cs | Timestamped observations → RatingCurve segments/error model/priors → RatingCurveAnalysis.RunAsync → curves and residuals |
| 10 | Airline, Nile, Mauna Loa | TimeSeriesAnalysis/ARIMAXAnalysisTests.cs; TestData.cs/Datasets | Raw TimeSeries → ARIMAX orders/transforms/priors → ARIMAXAnalysis.RunAsync → predictions and residual diagnostics |
| 11 | Simple/multiple consumption regression | TimeSeriesAnalysis/ARIMAXAnalysisTests.cs; Numerics linear-model notebook | Raw response/covariate series → SetCovariates → explicit parameters and sampler → RunAsync → fitted results and diagnostics |

## Implementation sequence

- [x] Verify Git/runtime baseline and create dedicated local branch.
- [x] Extract observation-only fixtures with source hashes; retain original archives separately.
- [x] Complete and execute notebook 02 first; inspect teaching code and regenerated plots.
- [x] Apply the explicit pattern to all remaining cases, preserving settings.
- [x] Replace generator and primary runner; add guards against restoration/cached replay.
- [x] Execute all 12 in independent kernels with project/result archives unavailable.
- [x] Review numerical expectations, diagnostics, figures, and teaching quality; record per-notebook evidence.

No blanket Verification run is part of this work. Successful execution, convergence,
and scientific acceptance are reported separately. No merge or push is authorized.
