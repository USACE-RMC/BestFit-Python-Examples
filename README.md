# BestFit Python Examples

Practical Python demos for **RMC-BestFit** using `pythonnet`, with notebook-first workflows and script examples for flood frequency, rating curves, forecasting, and regional analysis.

## What This Repo Contains

- `notebooks/00_getting_started.ipynb` to `08_batch_workflow_and_reporting.ipynb`
- `examples/` runnable Python scripts
- `notebooks/helper_functions.py` shared DLL path helpers
- `bestfit-python-demos-scope.md` project scope and roadmap

## Requirements

- Windows + Python 3.10+
- .NET runtime compatible with your BestFit build
- RMC DLLs:
  - `RMC.BestFit.dll`
  - `Numerics.dll`

Python packages (see `notebook-requirements.txt`):

- `pythonnet`
- `numpy`
- `pandas`
- `matplotlib`
- `scipy`
- `statsmodels`
- `jupyter`

## Setup

1. Install dependencies:

```powershell
pip install -r notebook-requirements.txt
```

2. Set DLL environment variables only if you want to override the local defaults:

```powershell
$env:RMC_BESTFIT_DLL="C:\GIT\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\RMC.BestFit.dll"
$env:RMC_NUMERICS_DLL="C:\GIT\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\Numerics.dll"
```

3. Start Jupyter:

```powershell
jupyter lab
```

Open notebooks in numeric order starting with `00_getting_started.ipynb`.

## Notebooks Guide

- `00_getting_started.ipynb`: runtime setup, DLL loading, first distribution calls, troubleshooting
- `01_distributions.ipynb`: distribution tour and shape comparison
- `02_distribution_fitting.ipynb`: empirical return periods and fitted quantile curves
- `03_bayesian_flood_frequency.ipynb`: uncertainty workflow (bootstrap posterior proxy)
- `04_model_selection_and_comparison.ipynb`: AIC/BIC comparison patterns
- `05_rating_curve_analysis.ipynb`: segmented stage-discharge fitting
- `06_time_serie_forecasting.ipynb`: ARIMAX-style forecasting demo
- `07_spatial_extremes.ipynb`: index-flood regional pooling
- `08_batch_workflow_and_reporting.ipynb`: config-driven multi-site batch flow and exports

Each notebook includes:

- Intro context
- Step-by-step code
- End summary with recommended exercises

## Example Scripts

Run from repo root:

```powershell
py examples\flood_frequency_simple.py
py examples\rating_curve_example.py
py examples\regional_analysis.py
```

Current script outputs:

- `outputs/tables/flood_frequency_empirical_vs_model.csv`
- `outputs/tables/flood_frequency_return_period_table.csv`
- `outputs/tables/rating_curve_observed_vs_fit.csv`
- `outputs/tables/rating_curve_table.csv`
- `outputs/tables/regional_analysis_site_records.csv`
- `outputs/tables/regional_analysis_site_quantiles.csv`

## DLL Resolution Behavior

`notebooks/helper_functions.py` uses this order:

1. `RMC_BESTFIT_DLL` / `RMC_NUMERICS_DLL` env vars
2. Known local default paths in this dev environment

If DLL load fails, verify paths first.

## Troubleshooting

- `pythonnet` runtime error at import:
  - use `pythonnet.load("coreclr")` for the current .NET build
  - use `pythonnet.load("netfx")` only for legacy .NET Framework builds
- `FileNotFoundError` for DLLs:
  - set env vars explicitly
- `AddReference` load conflicts:
  - restart kernel/session and re-run top cells only once

## Notes

- Some notebooks use synthetic data for deterministic demos.
- Scope and planned enhancements are tracked in `bestfit-python-demos-scope.md`.
- `Numerics-Python-Examples` in sibling folder was used as style/structure reference.
