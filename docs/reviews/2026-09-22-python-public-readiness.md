# BestFit Python public-readiness peer review

Reviewed on 2026-09-22. **Verdict: focused corrections are required before final public sharing.** The implementation has a sound reproducibility foundation and the saved walkthroughs run successfully, but seven P2 findings affect API behavior or scientific interpretation. One P3 presentation issue remains. No P0/P1 finding was established within this review's scope.

The reviewed app range is `3fa55a0f75bbd583e2fb7fce42180faa376f007c..5b4883c41ba46c43678d59cd42fd8180918f64dc`, including `190b088f1a354d696440b6f3a94a008cb031bc9c`. The examples range is `e0cba2ef1c884ddf0e3a06d0d2fb47f291d8d4f8..0120e23b44e4da73e24fa1f91506efaca383fa93`. At the end of the read-only review, both worktrees were clean on `python-example-retooling` at those exact commits. The review made no implementation edits, commits, pushes, merges, user-profile installations, or numerical-analysis reruns. This documentation archive records that review; the findings remain open.

Three independent reviewers covered the API/export contract, notebooks 00–06, and notebooks 07–11. The coordinating review checked setup, packaging declarations, source/cache integrity, notebook structure, actual figures, and the reported findings. The approved design and implementation plan were the requirements baseline. Findings below distinguish newly introduced problems from inherited desktop behavior.

1. **P2 — Plot-source error responses cannot serialize.**

   [PlotSourceResponse.cs:109](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/src/RMC.BestFit.Api/DTOs/Analyses/PlotSourceResponse.cs#L109) declares `Results` as nonnullable `JsonElement`. The REST controller's failure path constructs this DTO with `Results` left at `Undefined`. Serialization then throws `InvalidOperationException` in `JsonElementConverter.Write`, preventing the documented JSON error response for unknown, never-run, or busy analyses. Existing controller tests inspect `ObjectResult.StatusCode` before serialization and miss this failure. This is new in the app implementation.

   Make the unset result safely nullable/omittable and test the serialized response body for the actual error paths. The actual built API serializer reproduction is retained in [app-contract-repros.py](../../validation/peer-review/2026-09-22/app-contract-repros.py) and [its output](../../validation/peer-review/2026-09-22/app-contract-repros.txt); the coordinating reviewer independently reproduced it.

2. **P2 — API missing observations cannot be rendered by the Python adapter.**

   [common.py:20](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/common.py#L20) preserves all strings. The API encodes missing floating-point observations as the JSON string `"NaN"`, and [api_response_models.py:145](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/api_response_models.py#L145) forwards these values into a numeric plot axis. A completed time-series snapshot with such an observation fails validation with `y must contain finite numbers or JSON null gaps`; the equivalent null gap succeeds. This is a new API-to-plot contract defect, separate from the valid saved notebook caches.

   Normalize numeric missing-value encodings at the API boundary while preserving date strings and array alignment. Add a wire-format test with a legitimate missing holdout observation. The reproduction and output are in the same API evidence files above.

3. **P2 — B17C ensemble diagnostics are incorrectly called posterior distributions.**

   [diagnostics.py:125](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/diagnostics.py#L125) checks for the substring `b17c`, which does not match `Bulletin17CAnalysis`, rather than using the existing B17C predicate. The pair plot consequently receives the title “Joint Posterior Density.” Lines 257 and 268 also use unconditional “Posterior Histogram” and “Posterior Density” legend labels. These labels are present in the actual saved Example #2 diagnostic PlotSpecs and are accessible through the saved-case plotting API.

   Use consistent frequentist ensemble/sampling-distribution terminology in B17C titles and legends, with a representative B17C diagnostic test. Notebook 05's main prose and displayed frequency/influence plots already make the correct GMM/EMA and confidence/credible distinctions. This is a new plotting-package labeling defect; no estimation change is required.

4. **P2 — The fitting Q–Q plot reverses the meaning of its axis labels.**

   [frequency.py:284](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/frequency.py#L284) puts ordered observations on x and fitted inverse-CDF quantiles on y, then labels x “Quantile (Model)” and y “Quantile (Data).” The figure displayed in [notebook 02:695](../../notebooks/02_distribution_fitting.ipynb#L695), cell 6, visibly repeats the mismatch. This affects the reader's interpretation of deviations from the diagonal.

   The desktop already has this label/coordinate inconsistency, so it is **not a newly introduced numerical regression**. Correct or explicitly annotate the teaching display. If using a display-only correction, document it and preserve the original desktop-parity references rather than silently changing their meaning.

5. **P2 — The regression notebook incorrectly claims preservation of cross-covariate bootstrap blocks.**

   [notebook 11:497](../../notebooks/11_regression.ipynb#L497), cell 5, and its generator [create_notebooks.py:592](../../scripts/create_notebooks.py#L592) say `BlockBootstrap` preserves cross-covariate blocks. The actual [ARIMAX.cs:1874](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/src/RMC.BestFit/Models/TimeSeries/ARIMAX.cs#L1874) implementation resamples each covariate separately with `resampleSeed + i`; deterministic prediction appends each covariate's mean. The simulation path also uses separate per-covariate seeds.

   Explain within-series block resampling and the lack of synchronized multivariate blocks. This is new incorrect prose describing a pre-existing algorithm. Correct the notebook and generator together; do not change the algorithm to match the prose.

6. **P2 — Bivariate contour levels are not identified in the displayed figures.**

   [render.py:122](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/render.py#L122) discards the contour set without adding numeric labels or a colorbar. Notebook 07 cell 6 displays all levels in the same black color, so readers cannot identify particular exceedance probabilities or density values. The desktop explicitly supplies contour labels in `BivariateAnalysisControl.xaml.cs:648,701`; this is a new presentation/parity omission.

   Label the supplied levels without changing the grid or probabilities. Test rendered labels, not only that a contour collection exists. [Stored notebook figure](../../validation/peer-review/2026-09-22/notebook-images/07_bivariate_analysis-cell-06-02.png).

7. **P2 — The regression residual plot labels encoded dates as consumption changes.**

   [notebook 11:1033](../../notebooks/11_regression.ipynb#L1033), cell 6, displays residual x coordinates around 26,000–39,000 under “% Change in Consumption.” The coordinates are OLE Automation dates, as supplied by [response_models.py:223](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/response_models.py#L223). The adapter intentionally preserves the desktop convention; the repository's global parity notes explain it, and notebook 10 has a local explanation for Nile. Notebook 11 provides no such explanation.

   Add a notebook-local explanation/annotation or a documented display-only conversion to dates. This is inherited desktop presentation with a new teaching-context omission, not a new estimation defect. [Stored residual figure](../../validation/peer-review/2026-09-22/notebook-images/11_regression-cell-06-01.png).

8. **P3 — Seasonality figures show an artificial 2020 year.**

   [input_data.py:83](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/adapters/input_data.py#L83) anchors monthly summaries to 2020 dates, and the generic date formatter in [render.py:66](https://github.com/USACE-RMC/RMC-BestFit/blob/5b4883c41ba46c43678d59cd42fd8180918f64dc/skills/bestfit-frequency/bestfit_plots/render.py#L66) exposes that year in notebook 00. These are all-record seasonal summaries, not observations restricted to 2020. The desktop uses month-name formatting. Use month-only labels without changing any data. [Stored seasonality figure](../../validation/peer-review/2026-09-22/notebook-images/00_time_series_data-cell-06-01.png).

**Fresh verification and evidence**

| Check performed in this review | Result |
|---|---|
| Cached notebooks from a tracked-files archive, independent kernels | 12/12 passed; 45 original code cells, 41 PNG figures, zero errors |
| Access to original examples files and managed imports during that replay | Blocked by Python guards; scratch import origins verified; no `.runtime` or `output` before/after |
| Examples Python suite | 52 passed |
| Plotting and comparator suite, committed files copied to writable scratch | 92 passed, 6 subtests passed |
| Desktop reference exporter smoke tests | 3 passed |
| Existing compiled API exporter test methods, invoked directly | 9 passed; this was not a fresh full .NET suite run |
| Source/cache/execution evidence integrity | 22 fixtures, 71 cases/560 views, 12 notebook hashes, 51 completed-run outputs and 45 slots/85 variants verified |
| Skill ZIP checksum | Matches `6cba6f900d173a6dddc39b03b4f8b7e1601ba811f813529f1257709d7cc07564` |
| Notebook schema/output hygiene | All schema-valid; no stored error output or detected user-home paths in notebook text/code/outputs |
| Tracked Python repository hygiene | No tracked bytecode, virtual environments or managed binaries; no broken curriculum links identified |
| Git checks | Both reviewed worktrees still clean at reviewed commits; both range whitespace checks passed |

The initial test attempts encountered sandbox temp/source-directory write restrictions. Examples tests passed after using a review-local temporary directory; plotting tests passed from an archive of the exact committed sources, and exporter tests passed with review-local temp paths. These were environment restrictions, not repository failures. The initial stalled plotting process was terminated before the successful isolated retry.

Execution details: [clean walkthrough report](../../validation/peer-review/2026-09-22/clean-walkthrough-check.md), [machine-readable walkthrough evidence](../../validation/peer-review/2026-09-22/clean-walkthrough-check.json), [examples test log](../../validation/peer-review/2026-09-22/examples-tests.log), [plot test log](../../validation/peer-review/2026-09-22/plot-tests.log), [exporter test log](../../validation/peer-review/2026-09-22/exporter-tests.log), [static audit](../../validation/peer-review/2026-09-22/static-audit.json). The [evidence README](../../validation/peer-review/2026-09-22/README.md) explains path normalization and the retained artifacts. Full test XML, duplicate image exports, copied repositories and temporary harnesses remain local review scratch.

**Notebook coverage**

| Notebook | Review outcome |
|---|---|
| 00 | Clear source/sampling distinctions and inventories; artificial-year seasonality labels need polish. |
| 01 | Historical, threshold and uncertain observations preserved; provenance and limits clearly explained. |
| 02 | Candidate failures and within-input score scope handled; Q–Q labels need correction/disclosure. |
| 03 | GEV identity, temporal/causal information, quantile priors and curve meanings are explicit. |
| 04 | Trend ownership and DIC scope are explicit; retained BMA rerun confirms displayed weights. A suspected stale-weight defect was not substantiated. |
| 05 | Main GMM/EMA explanation is careful; optional B17C diagnostic titles/legends need correction. |
| 06 | POT/AMS, mixture, zero mass and competing-risk distinctions are explained without overstated score comparisons. |
| 07 | Synthetic sources and marginal-coordinate meanings are explicit; contours need their numeric levels. |
| 08 | Correlated-Normal control and Waimea conditional response context are appropriately qualified. |
| 09 | All 96 Mississippi stage/discharge timestamps independently matched; synthetic segment alternatives are identified. |
| 10 | Nile date correction and Airline diagnostics are disclosed; completed execution is not represented as convergence acceptance. |
| 11 | AR/MA and forecast settings are visible; bootstrap explanation and residual-axis context need correction. |

**Readiness limits and correction boundaries**

This review reused the existing Python dependency environment. It establishes independence of the cached walkthroughs from ignored analysis output and the original examples directory, not clean dependency installation on every supported Python version. Linux/macOS execution, fresh live imports, and every model family over a live HTTP server were not retested. The browser request for the official B17C PDF returned HTTP 403, so exact published table/page values were not independently reverified in this pass. Prior source audits remain evidence, not a newly repeated primary-source check.

Model suitability, hydrologic decisions, sampler convergence, and statistical/physics acceptance are outside an engineering peer-review verdict. The disclosed Airline warning remains relevant. No scientific algorithms, priors, seeds, tolerances, iteration lengths, historical sources, or previous validation receipts should be changed to resolve these findings.

After the focused corrections, refresh only affected notebook/plot outputs and relevant checks, preserving prior receipts and explaining any intentional departure from inherited desktop labels. Do not automatically repeat unchanged numerical runs. The handoff's separate publication condition also remains: the examples pin a local app revision, so external users need that compatible revision to be made available through an authorized paired publication/integration step. This review did not push, merge, or verify a new upstream publication.

Cross-repository source links identify the reviewed app commit and will resolve publicly once that revision is published. They do not imply publication was performed.
