# Publication refresh follow-up — 2026-09-25

The engineering findings from the [2026-09-22 review](2026-09-22-python-public-readiness.md)
are addressed by the public BestFit `db5807d` plotting/API implementation and the
focused examples corrections below. Human scientific review remains ongoing;
reviewer credit and successful execution do not establish scientific acceptance.

| Earlier finding | Current disposition |
|---|---|
| Plot-source error response serialization | Pinned API uses a safely nullable result; current API suite and exporter contracts pass |
| API string NaN observations | Pinned adapters normalize missing numeric wire values; plotting/API contract tests pass |
| B17C posterior terminology | Frequentist uncertainty labels retained in refreshed diagnostic PlotSpecs; Bayesian labels remain distinct |
| Fitting Q–Q axes | Observed x / fitted model y labels corrected; original desktop exports retained with explicit display-normalization rules |
| Regression bootstrap claim | Notebook 11 and generator explain separate within-series block resampling, without claiming synchronized multivariate blocks |
| Missing contour levels | Numeric levels displayed; final layout correction makes dense CDF contour labels readable |
| Regression residual axis | Dates displayed and explained locally, preserving the source date coordinates |
| Artificial seasonality year | Month names displayed without the arbitrary anchor year |

Only two notebook Markdown cells changed: the Nile date-axis explanation in
notebook 10 and the bootstrap/date explanation in notebook 11. No notebook code
cell or frozen description changed. A complete cell-level source comparison
showed that the current BestFit projects differ only in 239 description cells;
that AI-generated, unreviewed narration was not imported.

An independent read-only review checked the implementation, source/cache/receipt
integrity, all 85 gallery variants, and the installation path. It identified
additional issues with contour label clipping, zero-inflated log autoscaling,
Windows Git path lengths, and replacement of an installed same-version plotting
package. These were corrected without changing scientific algorithms or source
coordinates. Dedicated rendering tests check label bounds/overlap and the desktop
log range; the public installer is verified against its installed commit identity.

See the [publication evidence](../../validation/publication-2026-09-25/README.md)
for execution counts, runtime hashes, clean replay, parity results, and limits.
The earlier review and its evidence are preserved as a historical record.
