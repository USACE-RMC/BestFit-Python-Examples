# Clean tracked-distribution walkthrough check

12/12 passed; 0 failed; 40.717 seconds.

Source HEAD: `0120e23b44e4da73e24fa1f91506efaca383fa93`.

Tracked git archive, independent cached-only kernels, original examples filesystem reads and managed imports blocked.

Existing outputs were cleared before execution. Each notebook used a separate kernel. All writes were confined to review scratch.

| Notebook | Status | Seconds | PNG figures |
|---|---|---:|---:|
| 00_time_series_data.ipynb | passed | 10.625 | 3 |
| 01_input_data.ipynb | passed | 3.265 | 6 |
| 02_distribution_fitting.ipynb | passed | 2.781 | 3 |
| 03_stationary_information_expansion.ipynb | passed | 3.062 | 4 |
| 04_nonstationary_univariate.ipynb | passed | 2.828 | 3 |
| 05_bulletin_17c.ipynb | passed | 2.844 | 4 |
| 06_advanced_univariate.ipynb | passed | 2.656 | 3 |
| 07_bivariate_analysis.ipynb | passed | 2.609 | 3 |
| 08_coincident_frequency.ipynb | passed | 2.641 | 2 |
| 09_rating_curves.ipynb | passed | 2.359 | 3 |
| 10_classic_time_series.ipynb | passed | 2.672 | 4 |
| 11_regression.ipynb | passed | 2.375 | 3 |

No `.runtime` or `output` directory was present before or after replay: True.

Detailed import origins, interpreter, hashes and failures are in `clean-walkthrough-check.json`.

Limitations:
- Reused existing dependency environment and canonical plotting source, not a fresh dependency install.
- No numerical estimation, online imports, REST/MCP, or RUN_ANALYSES=True paths executed.
- Audit hook blocks Python open calls under original examples checkout; it is not an OS-level file-access trace.
