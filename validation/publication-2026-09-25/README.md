# Publication check — 2026-09-25

This refresh checks execution, source fidelity, plotting, installation, and public
documentation. It does not complete the ongoing human scientific review. The
README explicitly marks the repository as under active review and development.

The examples baseline was `1121ade3049d61be057cf8d9b32f401bbcdeaac0`.
The runtime and public plotting package are pinned to BestFit
`db5807d6e3a85606797cda79542f2d51a80a57a6`; frozen projects remain at
`3fa55a0f75bbd583e2fb7fce42180faa376f007c`.

| Evidence | Meaning |
|---|---|
| [summary.json](summary.json) | Test counts, runtime assembly hashes, 51-run completion, and exact notebook prose-change inventory |
| [environment.json](environment.json) | Python 3.12.14 / Windows 11 and dependency versions used |
| [source-drift.json](source-drift.json) | Cell-level comparison of all 22 current and frozen projects; only 239 description cells differ |
| [all-views.json](all-views.json) | All 560 saved views rendered; 13 affected views refreshed after final layout fixes |
| [visual-review.json](visual-review.json) | Inspected gallery/notebook figures, final PNG hashes, and resolved review findings |
| [clean-replay.json](clean-replay.json) | All 12 notebooks / 41 figures from a clean candidate copy, with managed imports and original-example reads blocked |
| [../notebooks](../notebooks/) | Independent execution receipts and current notebook hashes |
| [../reruns](../reruns/) | 51 original-settings run receipts; all output hashes and byte counts verified |
| [../plot-parity/report.json](../plot-parity/report.json) | 85 populated variants pass at absolute tolerance 1e-10 and relative tolerance 1e-8; one expected empty variant |

The four fast .NET suites passed 5,055 tests. The shared plotting/comparator/exporter
Python checks passed 131 tests and 15 subtests. The examples passed 71 tests.
The portable runtime and pinned desktop/exporter builds completed with zero
warnings and errors. The 51 analyses took 905.327 seconds of summed analysis wall
time while other validation was running; this is not a performance benchmark.

Every notebook figure and all 85 populated gallery variants were visually
inspected. Geometry comparisons alone do not establish readable label placement
or useful display ranges. That visual review found and resolved dense CDF contour
label clipping and the zero-inflated mixture's excessively expanded log scale.
The examples renderer still delegates to the canonical package: its CDF labels
are positioned on existing contour paths with a small blank margin. The mixture
retains the independently exported desktop range of 0.1 to 1000. Original
coordinates, contour levels, and near-zero stored ordinates remain intact.

Two measured USGS time-series views emit NumPy's timezone-representation warning.
All 1,351 affected timestamp coordinates were compared with explicit aware
Python datetime conversion and matched exactly; both figures rendered. The
warning is recorded rather than hidden or treated as missing data.

Fresh-environment installation included an actual public Git checkout with
process-local long-path support. The plotting installer forces replacement of
an existing same-version package and its installed PEP 610 commit identity was
checked against the lock. Both wheels built, dependency checks passed, and the
citation validated against the CFF 1.2 schema. The license remains 0BSD, matching
Numerics-Python-Examples; Sadie Niblett and C. Haden Smith are the authors, and
Julian “Tiki” Gonzalez is credited as reviewer without implying review completion.

The runtime-free notebook replay initially preceded the final layout correction
and was then repeated on the final notebook/code copy. An attempted full pytest
run without the managed runtime produced the expected restoration failures; the
README now states this prerequisite. Full managed tests passed. The installation
check also exposed and resolved Windows long-path checkout errors and the
same-version package replacement issue.

Reproduction from a prepared checkout:

```powershell
.venv/Scripts/python.exe scripts/install_plots.py
.venv/Scripts/python.exe scripts/bootstrap_runtime.py --bestfit-source PATH_TO_PINNED_BESTFIT
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/validate_notebooks.py --write
.venv/Scripts/python.exe scripts/run_curriculum_analyses.py --rerun-existing
.venv/Scripts/python.exe scripts/audit_sources.py --app-root PATH_TO_PINNED_BESTFIT
```

To refresh independent desktop evidence, build the pinned BestFit Debug solution
and `tools/PlotReferenceExporter` first. Desktop validation on this Windows host
used the existing HEC-DSS checkout through `-p:HecDssRoot=PATH_TO_HEC_DSS_DOTNET`;
the portable notebook runtime does not need that desktop dependency. Then run:

```powershell
.venv/Scripts/python.exe scripts/capture_plot_references.py --bestfit-source PATH_TO_PINNED_BESTFIT
.venv/Scripts/python.exe scripts/build_plot_gallery.py --bestfit-source PATH_TO_PINNED_BESTFIT --images
.venv/Scripts/python.exe scripts/check_plot_parity.py --bestfit-source PATH_TO_PINNED_BESTFIT
.venv/Scripts/python.exe scripts/update_plot_map.py --bestfit-source PATH_TO_PINNED_BESTFIT
```

The capture script uses verified frozen project bytes in disposable local files;
it does not save changes to original projects. Published reference JSON differs
from raw exporter output only by redacting an absolute path and adding capture
provenance. Raw exports, complete logs/TRX, disposable checkouts, and contact sheets
remain local scratch; their relevant hashes and compact results are recorded here.

Linux/macOS, every supported Python version, fresh external data services, and
every model family over live HTTP were not revalidated. No numerical algorithms,
priors, seeds, tolerances, iteration lengths, release tags, or repository visibility
were changed. Airline convergence concerns and B17C GMM/EMA distinctions remain
explicit. Earlier successful receipts are retained in the dated archive.
