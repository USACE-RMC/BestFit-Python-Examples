# App-to-Python plot map

Each row maps one desktop plot slot to its canonical adapter. The gallery contains all accepted variants;
the separate report checks source-bound geometry, axes, labels, series presence, and styles.

[Side-by-side gallery](plot-gallery/index.html) · [Detailed parity report](../validation/plot-parity/report.json)

| App plot ID | Python adapter | Variants | Evidence |
|---|---|---|---|
| `time_series_data.series` | `input_data.py::time_series_plots` | default | {'verified': 1} |
| `time_series_data.seasonality` | `input_data.py::time_series_plots` | default | {'verified': 1} |
| `time_series_data.acf` | `input_data.py::time_series_plots` | default | {'verified': 1} |
| `time_series_data.pacf` | `input_data.py::time_series_plots` | default | {'verified': 1} |
| `input_data.chronology` | `input_data.py::input_data_plots` | calendar_year, water_year, saved_index | {'verified': 3} |
| `input_data.frequency` | `input_data.py::input_data_plots` | default, exact, interval, uncertain, low_outlier | {'verified': 5} |
| `input_data.seasonality` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.density` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.histogram` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.qq` | `input_data.py::input_data_plots` | default, real, log10 | {'verified': 3} |
| `input_data.acf` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.pacf` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.mean_residual_life` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.modified_scale` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `input_data.shape` | `input_data.py::input_data_plots` | default | {'verified': 1} |
| `fitting.frequency` | `frequency.py::frequency_plots` | default, comparison | {'verified': 2} |
| `fitting.pdf` | `frequency.py::frequency_plots` | default, comparison | {'verified': 2} |
| `fitting.cdf` | `frequency.py::frequency_plots` | default, comparison | {'verified': 2} |
| `fitting.pp` | `frequency.py::frequency_plots` | default, comparison | {'verified': 2} |
| `fitting.qq` | `frequency.py::frequency_plots` | default, comparison | {'verified': 2} |
| `univariate.frequency` | `frequency.py::frequency_plots` | stationary, nonstationary, comparison, quantile_prior | {'verified': 4} |
| `univariate.chronology` | `frequency.py::frequency_plots` | stationary, nonstationary | {'app_conditional_empty': 1, 'verified': 1} |
| `b17c.frequency` | `frequency.py::frequency_plots` | mv_normal, bcb, historical_interval, low_outlier | {'verified': 4} |
| `point_process.frequency` | `frequency.py::frequency_plots` | pot, ams, seasonal, comparison | {'verified': 4} |
| `mixture.frequency` | `frequency.py::frequency_plots` | mixture, zero_inflated | {'verified': 2} |
| `composite.frequency` | `frequency.py::frequency_plots` | competing_risk, component | {'verified': 2} |
| `bivariate.distribution` | `response_models.py::bivariate_plots` | scatter_values, scatter_cdf, density_values, density_cdf, joint_exceedance_values, joint_exceedance_cdf | {'verified': 6} |
| `coincident.frequency` | `response_models.py::coincident_plots` | default, comparison, linear_response | {'verified': 3} |
| `rating.curve` | `response_models.py::rating_plots` | default, segmented | {'verified': 2} |
| `rating.residuals` | `response_models.py::rating_plots` | default | {'verified': 1} |
| `rating.residual_histogram` | `response_models.py::rating_plots` | default | {'verified': 1} |
| `rating.residual_qq` | `response_models.py::rating_plots` | default | {'verified': 1} |
| `time_series_analysis.series` | `response_models.py::time_series_analysis_plots` | training, forecast | {'verified': 2} |
| `time_series_analysis.residuals` | `response_models.py::time_series_analysis_plots` | default | {'verified': 1} |
| `time_series_analysis.residual_histogram` | `response_models.py::time_series_analysis_plots` | default | {'verified': 1} |
| `time_series_analysis.residual_qq` | `response_models.py::time_series_analysis_plots` | default | {'verified': 1} |
| `time_series_analysis.residual_acf` | `response_models.py::time_series_analysis_plots` | default | {'verified': 1} |
| `time_series_analysis.residual_pacf` | `response_models.py::time_series_analysis_plots` | default | {'verified': 1} |
| `shared_diagnostics.trace` | `diagnostics.py::diagnostic_plots` | chain, warmup | {'verified': 2} |
| `shared_diagnostics.histogram` | `diagnostics.py::diagnostic_plots` | posterior, prior | {'verified': 2} |
| `shared_diagnostics.kde` | `diagnostics.py::diagnostic_plots` | posterior | {'verified': 1} |
| `shared_diagnostics.acf` | `diagnostics.py::diagnostic_plots` | parameter | {'verified': 1} |
| `shared_diagnostics.mean_log_likelihood` | `diagnostics.py::diagnostic_plots` | default | {'verified': 1} |
| `shared_diagnostics.pair_heatmap` | `diagnostics.py::diagnostic_plots` | parameter_pair | {'verified': 1} |
| `shared_diagnostics.influence` | `diagnostics.py::diagnostic_plots` | bayesian_leverage, bayesian_fit, bayesian_variance, gmm_fit, gmm_variance, leave_one_out | {'verified': 6} |

## Interpretation and deliberate boundaries

The stationary univariate chronology tab is conditionally absent. Its empty record is expected; the nonstationary case supplies this slot's populated evidence.

Python displays time-series residuals on a Date axis, corrects fitting Q-Q labels, and distinguishes frequentist uncertainty, prediction intervals, and observed seasonal ranges. The comparison applies these explicit presentation corrections to a copy of the independent reference, keeping its coordinates and the original export intact. Contours carry numeric levels and seasonal dates display month names. These corrections do not alter estimation or stored results.

The examples renderer spaces CDF contour labels with a small blank margin. The zero-inflated mixture retains the independently exported desktop log range (0.1 to 1000); near-zero positive coordinates remain stored outside that view. These layout choices are checked separately from geometry parity.

Factory-default presentation is compared; saved custom colors/titles, WPF interaction, and pixel-identical font rasterization are excluded. Simulation, contour grids, priors, intervals, and diagnostics come from the unchanged BestFit/Numerics methods or completed API export. No renderer refits data.

Use `bestfit_plots.source.add_frequency_comparison(base, alternative, name)` or the skill CLI's `--compare-source` and `--compare-name` for source-identified overlays. Both source identities are retained; matching axes and units are required. A plotted comparison is not automatically a valid information-criterion ranking.
