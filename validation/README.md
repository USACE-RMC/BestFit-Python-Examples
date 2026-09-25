# Validation evidence

The current [2026-09-25 publication check](publication-2026-09-25/README.md)
uses public BestFit commit `db5807d6e3a85606797cda79542f2d51a80a57a6`,
.NET 10, and RMC.Numerics 2.2.0. Frozen project sources remain at
`3fa55a0f75bbd583e2fb7fce42180faa376f007c`. All 22 projects have identical
non-description cells at those revisions; the 239 changed descriptions were
not imported because the upstream narration is still under review.

| Check | Current result |
|---|---|
| Notebook execution | 12 independent kernels, 41 figures, zero errors; clean-copy replay also passed with managed imports blocked |
| Original-settings analyses | 51 completed; all 51 receipts and output checksums verified |
| Examples Python suite | 71 passed |
| Shared plots, comparator, exporter contracts | 131 passed and 15 subtests passed |
| BestFit fast suites | Core 3434, UI 645, App 444, API 532: 5055 passed |
| Saved plots | All 560 views from 71 cases rendered |
| Desktop parity | 45 slots, 85 populated variants passed, one expected empty stationary chronology |
| Visual review | All 41 notebook figures and all 85 populated gallery variants inspected |
| Installation and metadata | Public pinned plotting install verified by installed commit identity; wheels built; CFF schema and dependency checks passed |
| Runtime | Exact assembly identities and hashes checked; zero build warnings/errors |

The map has one more acceptance variant than the earlier review:
`input_data.chronology--saved_index`. The independent desktop references are
stored in [plot-parity/app-reference](plot-parity/app-reference/); original
coordinates are retained even when documented Python display labels differ.

The [follow-up review](../docs/reviews/2026-09-25-publication-refresh.md) documents
the disposition of the eight findings in the earlier
[2026-09-22 review](../docs/reviews/2026-09-22-python-public-readiness.md).
That historical report and its evidence remain available. Superseded successful
notebook/run receipts and the old diagnostic summary are preserved under
[archive/2026-09-22](archive/2026-09-22/).

`source-checks.json` records the published B17C comparisons, Nile CSV/project
date check, and fitted sum-of-Normals analytic controls. `run-quality-summary.json`
records current rerun diagnostics. The Airline Passengers case retains its
R-hat/ESS warnings. Completion does not certify convergence or model suitability;
the B17C GMM results are not official EMA/MGBT results.

`reruns/` contains current receipts and named prior attempts. Large rerun snapshots
remain under ignored `output/reruns/`; hashes and byte counts are in receipts.
After runtime bootstrap, `python scripts/run_curriculum_analyses.py` verifies
existing local output or reports it as missing/stale. Use `--rerun-existing` to
explicitly repeat the original settings. The full Python test suite requires the
managed runtime; saved notebook replay does not.

No blanket Verification suite was run. Numerical algorithms, priors, seeds,
tolerances, iteration lengths, source payloads, and estimation contracts were
preserved. Human scientific review and development remain ongoing.
