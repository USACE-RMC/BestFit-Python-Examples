# Migration from the original examples

The app projects now define the curriculum. Each walkthrough begins with an
analysis question; controlled synthetic cases are identified explicitly.

| Previous entry point | Replacement |
|---|---|
| `00_getting_started.ipynb` | README, locked runtime bootstrap, notebook 00 |
| `01_distribution_fitting.ipynb`, `02_model_estimation.ipynb` | Notebooks 01–06 |
| `03_time_series_forecasting.ipynb` | Notebooks 10–11 |
| `04_rating_curve_analysis.ipynb` | Notebook 09 |
| `05_spatial_extremes.ipynb`, `regional_analysis.py` | Outside this app-example curriculum; no replacement claim for regional pooling |
| `06_batch_workflow_and_reporting.ipynb`, batch YAML | `scripts/run_curriculum_analyses.py` and persisted receipts |
| `flood_frequency_simple.py` | Notebooks 02, 03 and 05 |
| `rating_curve_example.py` | Notebook 09 |
| `helper_functions.py`, DLL cache discovery | `bestfit_examples.runtime` and `runtime-lock.json` |

The 12 notebook files are the teaching surface. Shared infrastructure lives in
`bestfit_examples/`; numerical methods remain in BestFit/Numerics. Plot code lives
in the BestFit skill and is installed as `bestfit-plots`, not copied into notebooks.
Frozen fixtures/results and fresh rerun artifacts have separate provenance.

Prior files remain recoverable at baseline commit
`e0cba2ef1c884ddf0e3a06d0d2fb47f291d8d4f8`. Contributor history is retained.
