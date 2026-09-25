# Source review and implementation decisions

The saved BestFit example projects define this curriculum. A useful walkthrough
must explain the hydrologic question, preserve the information supplied to the
likelihood, show the model actually configured in the app, and distinguish saved
results from a fresh analysis. The former seven notebooks and separate scripts
have been superseded by twelve app-based walkthroughs; their baseline and entry
point mapping remain in [migration.md](migration.md).

| Source finding | Consequence and implemented treatment |
|---|---|
| The projects mix legacy XML and compressed time-series/result fields. | Empty legacy text does not mean missing observations. The loader preserves both forms and original source payloads. Mississippi has 96 timestamp-matched stage/discharge observations. |
| Input information includes exact, uncertain, interval and perception-threshold records. | These remain separate types. Notebook 01 includes 79 exact and 25 uncertain Sinnemahoning records, plus the Viglione historical-information cases; intervals are not replaced by midpoint observations. |
| The Viglione project uses GEV, despite the accompanying tutorial's LP-III wording. | Notebooks 02–03 follow the saved GEV analyses. Nine Bayesian alternatives show changes in record period, temporal information, causal information and quantile priors. |
| Brays Bayou contains seven LP-III trend structures and a DIC-weighted composite. | Notebook 04 shows trend ownership, evaluation year and saved weights. Composite fit-metric placeholders display as unavailable rather than perfect zero scores. |
| Bulletin 17C's official examples use EMA/MGBT; the saved app cases use its GMM implementation and MVN/BCB uncertainty. | Notebook 05 describes Orestimba and Pueblo from official Appendix 10, retains the app's saved observations and screening, and compares published and saved numbers without claiming method equivalence or calling frequentist ensembles MCMC. |
| Point-process, AMS, mixture and composite cases have different sampling/model interpretations. | Notebook 06 uses short separate vignettes. A model-score table across POT and AMS inputs is explicitly descriptive; it cannot select a winner across different likelihood contributions. |
| The copula examples and segmented rating examples use distinct synthetic datasets. | They teach behavior and model structure, not a cross-dataset AIC/BIC contest. Synthetic inputs are labeled and the field rating remains a separate vignette. |
| Sum-of-Normals filenames contain nominal correlations; the saved copulas have fitted correlations and finite integration grids. | Notebook 08 uses fitted parameters in the analytic check and reports finite-grid error. Waimea shows its conditional copula, 50 bins, 10×5 response grid and absence of an attached observed response input. |
| The Nile project's 100 values match the bundled CSV, but its dates are shifted by 26 years. | Notebook 10 explicitly displays CSV dates 1871–1970 while preserving the saved 1897–1996 project. The main series and residual date coordinates shift together; values and fitted model remain unchanged. |
| Airline's retained fit has R-hat/ESS concerns and misses seasonal held-out behavior. | The notebook reports the limitation. Completing a run or rendering its plots does not accept convergence; no settings were shortened or tuned to obtain a pass. |
| Regression examples are ARIMAX configurations with AR=MA=0 and a saved future-covariate rule. | Notebook 11 shows the actual simple/multiple regressions, 30-step forecast and BlockBootstrap covariate extension. |

The existing plotting skill covered default stationary univariate and B17C
frequency curves. It now provides one installable package for all 45 app plot
slots. [The plot map](app-plot-map.md) connects each slot and variant to its app
factory, population method, adapter and independent source evidence. The API/MCP
addition exports detached, completed-run coordinates; rendering does not estimate.

Independent implementation review also caught and corrected missing coincident
marginal chains, parameter reset during regression covariate restoration, stale
receipt reuse, fresh plots retaining saved-run identity, missing AMS markers,
silently truncated residual arrays, and lost influence labels/orientation. These
were implementation defects corrected during this work, not changes to BestFit's
scientific methods.

[Validation records](../validation/README.md) separate source fidelity, numerical
diagnostics, plot parity, notebook execution and package contracts. Original
projects, algorithms, priors, seeds, tolerances and sampler lengths are retained.
