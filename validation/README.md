# Validation evidence

The examples use BestFit commit `5b4883c41ba46c43678d59cd42fd8180918f64dc`,
.NET 10, and RMC.Numerics 2.2.0. Frozen project sources remain at app commit
`3fa55a0f75bbd583e2fb7fce42180faa376f007c`. This distinction preserves the original
example records while pinning the compatible plotting/API implementation.

| Check | Evidence |
|---|---|
| Notebook execution | 12 independent kernels passed; per-file hashes and timing in `notebooks/` |
| Full-settings reruns | 51 completed at the locked runtime; all 51 receipts and output checksums verified; 310.876 s summed analysis time |
| Examples Python suite | 52 passed |
| Plot package, comparator, exporter contracts | 95 passed and 6 subtests passed |
| BestFit fast suites | Core 3434, UI 645, App 444, API 526: 5049 passed |
| Desktop plot parity | 45 slots; 84 populated variants passed, one expected empty stationary chronology |
| Packaging | Both wheels built; canonical plotting wheel rendered PNG/SVG with managed imports blocked; skill ZIP built |
| Runtime bootstrap | Exact paired assembly identities and hashes checked; zero build warnings/errors |
| Source audits | Nile values/dates, published B17C comparisons and three fitted sum-of-Normals controls checked |

The 71 saved cases contain 560 named views, prepared from 22 complete project
snapshots. These cached views are readable without CLR, a server, or a download.
The plot gallery is separate from the concise notebook selections.

`source-checks.json` records the official B17C comparisons, the Nile CSV/project
date audit, and the fitted sum-of-Normals analytic control. `run-quality-summary.json`
reports diagnostics for full-settings reruns. Completed execution does not certify
sampler convergence. The Airline Passengers case retains its observed R-hat/ESS
concerns in notebook 10; no sampler setting or acceptance criterion was changed.

The B17C numbers compare saved app GMM results with published EMA values. Numerical
proximity does not establish method equivalence. Information criteria are compared
only when the response observations and likelihood treatment permit it; other
metric tables are explicitly descriptive. Composite placeholder zeros display as
unavailable. The Nile display correction shifts dates by 26 years, with original
source bytes retained.

`reruns/` keeps completed-run receipts and named prior attempts, including recorder
failures and superseded restoration/runtime evidence. Large rerun snapshots live
under ignored `output/reruns/`; their byte counts and hashes remain in receipts.
Use `python scripts/run_curriculum_analyses.py` to repeat or verify current receipts.
It rejects stale or altered evidence rather than silently treating it as completed.

No blanket Verification suite was run. No desktop or numerical algorithms, priors,
seeds, tolerances, default iteration lengths, or public estimation contracts changed.
These are engineering and source-parity checks, not a blanket scientific endorsement.
