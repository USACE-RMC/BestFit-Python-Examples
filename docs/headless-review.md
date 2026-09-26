# Headless curriculum review

Review date: 2026-09-25. Scope: all twelve maintained Python notebook sources,
generated notebooks, shared raw/execution/plot helpers, generator, validator,
README, fresh execution receipts and figures. The comparison baseline was
`f94c84c55db73caf69addc39b17907757c488ef6` on `headless-python-teaching`.

An additional independent reviewer found three material defects after the initial
review: omitted CFA marginal uncertainty, missing embedded notebook figures, and
an audit that could accept modified evidence. The corrections and final checks
are recorded below. The review concerns the construction/execution/presentation
contract described in [the validation report](headless-validation.md), not
scientific acceptance of every fitted example. The independent reviewer inspected
recorded evidence and ran read-only setting comparisons; the implementation agent
performed the fresh estimator runs and regression tests. Neither ran C# Verification
tests.

## Evidence examined

Every notebook visibly loads original observations, constructs .NET inputs and
models, sets the relevant priors/options, performs calculations or `RunAsync`,
reads fresh results and supplies those objects to canonical plot adapters.
There is no default saved-result replay, restoration call, hidden analysis
builder, or replacement Verification scenario in this execution path. Original
case coverage is 51 primary cases and 79 executed analyses including dependencies.
Final acceptance also requires executed cells and matching embedded outputs;
cell-source hashes alone did not reveal the delivery defects.

Raw loaders verify fixture checksums. Fresh validation workspaces omit saved
projects, result caches and previous reruns; the Python access guard rejects
those paths and legacy restoration modules. The validator checks original named
primary cases and source hashes, paired PNG/specification files, figure run
identities and both fresh CFA marginal-chain identities. The retained-evidence
audit compares immutable original inventories and hashes for all execution inputs,
run artifacts and delivered notebook outputs. This is an accidental-cache safeguard, not an operating-system
sandbox for arbitrary CLR file access. Source inspection found no such bypass.

Offline comparisons checked authored samplers, models, prior distributions,
bounds/flags, trends, composite membership and probability grids against original
project evidence. Both univariate and multivariate setting audits passed.
The independent reviewer repeated all three offline audits, covering 32
univariate/composite, 38 multivariate/rating and nine fitting/ARIMAX runs. Direct
source comparison also confirmed 22 raw fixtures with 39 time series (2,582,010
records), 61 frames (15,926 records), and four response grids. Fitted values,
elapsed time and inactive stale stationary trend-prior copies were
distinguished from active configuration. Final 10/11 model XML matches the
original ARIMAX models after fresh estimation, even after unnecessary saved
fitted-value assignments were removed from setup. Their sampler initialization
uses the explicitly configured priors.

The independent numerical checks are useful at their stated scope: raw rolling
means/monthly maxima, original annual maxima and event-rate identities, Normal
MLE coordinates, GEV quantiles, DIC weight normalization, B17C worked-example
parameters, mixture/composite CDF identities, the Gaussian copula orthant
identity, analytic Normal-sum CFA, independently authored rating likelihoods,
and raw-data time-series/regression residual and Gaussian-likelihood arithmetic.
They do not amount to independent verification of every posterior or interval.

## Findings resolved during review

| Finding | Final correction and evidence |
|---|---|
| P1: CFA used fixed marginal point values for uncertainty despite fitting both marginals | Notebook 08 assigns each fresh `BayesianAnalysis.Results` to `MarginalXChain`/`MarginalYChain` before execution, matching the production desktop workflow; CLR identity/draw-count assertions and receipt dependency checks protect the wiring. |
| P2: All notebooks lacked embedded PNGs; 03–06 had cleared outputs despite successful receipts | Explicit PNG display works under Agg and exports the same bytes. Validation requires executed cells and exact correspondence between embedded images and fresh artifacts; all twelve are re-executed with outputs retained. The cause of the earlier cleared outputs was not established. |
| P2: Audit overwrote hashes and could miss changed helpers, run files or removed plot pairs | The audit is read-only and compares original complete inventories and hashes. Regression checks reject replacement images, paired deletions, modified run records, helpers and table outputs without rewriting receipts. |
| Incomplete execution could pass with only one analysis receipt | Validator now requires the original named primary roster and binds figure identities to fresh runs. |
| Notebook 00 checked counts but not new transformations | Independent raw-data rolling means and monthly maxima now check the displayed calculations. |
| Notebook 11 did not distinguish observed holdout from future dates | Both regression charts mark the end of training and the end of observations. |
| Notebooks 08/09 hid sampler diagnostics in receipts | Direct fresh-result R-hat/ESS tables now cover CFA dependencies and every rating case. |
| Conditional Makaweli mean positivity flag differed from the original case | Explicit `IsPositive=True` restores the authored flag; offline setting audit passes. |
| Notebook 07's negative contour labels lacked scale explanation | Prose identifies natural-log joint density evaluated on CDF coordinates. |
| Notebook 05 did not expose fit/bootstrap status | A fresh GMM/BootstrapResults table distinguishes valid/substituted refits, retained draws and optimizer candidate statuses. |
| Several notebook 03 discharge figures lacked units | All nine frequency figures now label discharge in m³/s. |

Additional final checks confirmed the original 27-ordinate zero-inflated grid in
06, visibility of unsuccessful candidates across all four fitting inputs in 02,
and the Waimea stage-axis unit in 08. The 10/11 raw-data arithmetic checks remain
in place after removing saved fitted-value assignments from their setup.

The additional reviewer independently ran the 13 focused validation regressions
(all passed), audited the corrected fitting/CFA notebooks, and checked that the
audit left receipt hashes unchanged. Direct inspection confirmed six fitting
and four CFA embedded PNGs with valid signatures and exact source/hash matches.
All four CFA receipts identify their eight corresponding fresh marginal fits
with 10000 draws each. The retained full-suite JUnit report records 87 tests,
zero failures/errors/skips in 41.237 seconds. These tests include legacy
comparison support; estimator acceptance comes from the separate notebook runs
and their explicitly scoped checks, not the test count.

Final closure: the independent reviewer audited all twelve completed notebooks
and directly inspected their JSON outputs. All 76 code cells were executed,
51 primary cases and 79 total analyses completed, and 75 embedded PNGs matched
the retained artifact bytes and source identities. No error outputs remained.
The reviewer closed all three additional findings with no remaining actionable
defect. See the [immutable audit receipt](../validation/headless-audit.json),
[test evidence](../validation/headless-tests.xml), and per-notebook timings in
the validation report. This closure does not certify convergence or scientific
acceptance.

## Visual review

All 75 final figures were inspected, including changed renders after corrections.
Where a correction changed only tables or code, final PNG hashes were compared
with the already inspected renders. Of the final 75 PNGs, 71 are byte-identical
to previously reviewed images and the four corrected CFA figures were inspected
again by both implementation and independent review agents. The
[visual inventory](../validation/headless-visual-review.json) retains these
comparisons. The figure counts are:

| Notebook | 00 | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Figures | 4 | 6 | 6 | 10 | 15 | 4 | 7 | 3 | 4 | 6 | 6 | 4 |

The four CFA figures were inspected again after attaching the marginal chains.
Their changed bands now include marginal uncertainty. A visible Matplotlib
context reduces only their probability tick-label size to avoid colliding
rare-tail labels; it does not change coordinates, ranges or numerical results.

No blank panels, clipped legends, broken date/probability axes or blocking
readability defects remain. Historical/uncertain observations, confidence versus
credible/predictive interval terminology, Nile's disclosed display-only date
correction, log-density contours and the zero-inflated log view were reviewed.
Dense fitting legends are readable. Broad tails, strong residual dependence,
occasionally negative predictive support and the zero-atom discontinuity remain
visible rather than being cosmetically removed.

## Scientific limits retained

Execution does not establish MCMC convergence, uncertainty coverage, model
adequacy or causal validity. Airline retains poor mixing and residual concerns.
Nonstationary frequency curves are conditional on the stated evaluation year;
historical observations are not all draws from that year's distribution.
B17C GMM and its uncertainty methods are distinct from official EMA/MGBT.
Bootstrap optimizer candidate-status totals must not be mistaken for counts of
accepted refits. CFA propagates both marginal chains and the copula chain through
independent posterior index resampling; this is not a jointly fitted posterior.
Conditional event definitions and engineered response surfaces need separate validation. Rating
likelihood checks do not establish hydraulic suitability or extrapolation safety.
Mixture identities do not resolve label switching or identify physical flood
mechanisms. These limitations remain part of the teaching context.
