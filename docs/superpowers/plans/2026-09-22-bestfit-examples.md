# BestFit Python examples implementation plan

**Goal:** Deliver the approved twelve-notebook curriculum and all 45 app plot slots within five staged work packages.

**Architecture:** Portable BestFit/Numerics calculations, Python adapters and one shared Matplotlib package; additive read-only API/MCP exports; unchanged desktop and numerical behavior.

**Tech stack:** Python 3.10+, pythonnet, .NET 10, RMC.Numerics 2.2.0, Matplotlib, NumPy, SciPy, Jupyter.

**Spec:** `../specs/2026-09-22-bestfit-examples-design.md` is authoritative.

## Review focus

- Typed historical information or compressed project data silently lost during export.
- Cached data/configuration/software identity differs from the displayed analysis.
- Shared plotting accidentally substitutes statistical calculations or labels the wrong estimator/interval.
- Missing/inconsistent API result state or a read-only export triggers a fit.
- Source project settings, chronological alignment, or original input provenance is replaced by plausible invented data.

### Task 1: Reproducible foundation and data notebooks

Create isolated worktrees, persisted spec/plan/ledger, pinned runtime, typed source fixtures and loader. Build the shared package and 15 raw-series/input-data plots. Produce notebooks 00-01. Establish independent app export tooling outside desktop production code. Test compressed/legacy inputs, runtime rejection and source fidelity, plus plot geometry and cached notebook execution. Expected: reproducible frozen input and plotting evidence; no online download needed for cached walkthrough.

### Task 2: Fitting and univariate notebooks

Build notebooks 02-04, five fitting/two univariate plot slots and five shared diagnostics (trace, histogram, KDE, ACF, mean log likelihood). Add same-run read-only export data and adapters. Retain all source settings and run original-setting cases with receipts. Test failed-fit filtering, estimator sign/results ownership, nonstationary conditions and source/app parity. Expected: fresh results and diagnostics with no mixed analysis identities.

### Task 3: B17C and advanced univariate

Build notebooks 05-06; B17C, point process, mixture, composite plot slots and influence variants. Add official citations, observations/screening/window preservation and published comparisons. Test B17C method/interval labels and supported Bayesian/GMM diagnostics. Expected: both B17C cases and three advanced vignettes operate from frozen sources.

### Task 4: Bivariate, coincident and rating

Build notebooks 07-09; bivariate variants, coincident response frequency, four rating plots and parameter-pair heat map. Add dependency/marginal exports and adapters. Check sum-of-Normals analytic control, Waimea response construction and 96 paired Mississippi measurements. Expected: seven slots and their variants have evidence.

### Task 5: Time-series, regression and integration

Build notebooks 10-11 and six analysis plot slots. Complete skill docs, install/package workflows, source/reference gallery, migration/README, independent whole-branch review and validation. Supersede old synthetic-only material. Expected: 12 source-backed notebooks, 45 supported plot slots, all required tests/evidence, scoped local commits, no publication.

## Per-package gate and handoff

Use test-first implementation for meaningful code, independent task review and fresh verification. Run complete appropriate Python suites, independent fresh-kernel notebook validation and four required BestFit fast suites for its changes. Do not run blanket Verification. Record commands, exit codes, counts, artifacts, timing and deficiencies. A package is complete only when its scope and evidence are complete. Handoffs name both exact branches, HEADs, worktrees, completed notebook/plot IDs and outstanding findings.
