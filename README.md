# BestFit Python Examples

[![License: 0BSD](https://img.shields.io/badge/License-0BSD-blue.svg)](https://opensource.org/licenses/0BSD)
[![DOI](https://zenodo.org/badge/1135095276.svg)](https://doi.org/10.5281/zenodo.19715583)

This repository contains Python notebooks that demonstrate the USACE-RMC BestFit .NET library through pythonnet. The notebooks provide practical, reproducible examples of BestFit applications including flood frequency, rating curves, forecasting, and regional analysis.

## What This Repo Contains
- `notebooks/` 7 Juptyer notebooks organized by topic
- `examples/` runnable Python example scripts
- `notebooks/helper_functions.py` shared helper functions
- `bestfit-python-demos-scope.md` project scope and roadmap

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


## Requirements
- Windows + Python 3.10+
- .NET runtime compatible with your BestFit build (.NET 6+)
   - Install the [.NET SDK](https://dotnet.microsoft.com/download) if you don't already have it
- The [RMC.Numerics](https://www.nuget.org/packages/RMC.Numerics) NuGet package (see Quick Start)
- RMC DLLs (see Quick Start)
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

## Quick Start
The quick start will walk you through creating a virtual Python environment, installing the notebook requirements, and pulling in the `RMC.BestFit` NuGet package. For a more in-depth walkthrough see notebook [`00_getting_started.ipynb`](notebooks/00_getting_started.ipynb).  
**NOTE:** The commands below assume Windows. See notebook `00` for macOS/Linux equivalents.
**NOTE:** This demo use both the `RMC.BestFit.dll`and `Numerics.dll`. When you download RMC BestFit, Numerics comes automatically built in (!!!CHECK IF THIS IS TRUE WITH NUGET PACKAGE!!!). Thus we only need BestFit to access both. You can download Numerics separately as the stand alone library if you wish.

1. Create and activate a virtual Python environment

   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install ipykernel
   python -m ipykernel install --user --name=.venv --display-name "Python (.venv)"
   ```

2. Install the Python requirements

   ```bash
   pip install -r notebook-requirements.txt
   ```

3. Install the `RMC.BestFit` NuGet package

   ```bash
   # Option A — global NuGet cache (recommended; requires the .NET SDK):
   dotnet add package RMC.BestFit

   # Option B — local packages/ folder (requires nuget.exe on PATH):
   nuget install RMC.BestFit -OutputDirectory packages
   ```

   Both commands pull the **latest** published version by default.

   The notebooks auto-discover the DLL in either location via `resolve_bestfit_dll()` in [`notebooks/helper_functions.py`](notebooks/helper_functions.py).

4. Load BestFit and Numerics in a notebook or script

   ```python
   import pythonnet
   pythonnet.load("coreclr")

   import clr
   from helper_functions import resolve_bestfit_dll, resolve_numerics_dll

   clr.AddReference(str(resolve_besfit_dll()))
   clr.AddReference(str(resolve_numerics_dll()))
   ```

5. Run a `FittingAnalysis` on data to quickly fit the 15 distributions most commonly used for flood frequency.

  ```python
  from RMC.BestFit import ExactData, ExactSeries
  from RMC.BestFit.Models import DataFrame
  from RMC.BestFit.Analyses import FittingAnalysis

  annual_peaks = [
    45000, 52000, 38000, 61000, 49000, 55000, 42000, 67000, 39000, 48000,
    51000, 36000, 58000, 44000, 53000, 47000, 62000, 41000, 50000, 37000,
    54000, 46000, 59000, 43000, 56000, 40000, 63000, 35000, 57000, 45000]
  df = DataFrame()
  df.ExactSeries = ExactSeries(convert_to_dotnet_array(annual_peaks))

  analysis = FittingAnalysis(df)  
  analysis.RunAsync().Wait()
  ```

## Using a local BestFit (+ Numerics) build instead of NuGet
If you prefer to build BestFit or Numerics from source — for example, to develop against the latest `main` branch — clone the [BestFit](https://github.com/USACE-RMC/BestFit) and [Numerics](https://github.com/USACE-RMC/Numerics) repos and build them:

```bash
git clone https://github.com/USACE-RMC/BestFit.git
cd BestFit
dotnet build BestFit.sln --configuration Release

git clone https://github.com/USACE-RMC/Numerics.git
cd Numerics
dotnet build Numerics.sln --configuration Release
```

Then point the notebooks at your build by setting the `BESTFIT_DLL` `NUMERICS_DLL` environment variables before launching Jupyter:

```powershell
# PowerShell
$env:BESTFIT_DLL = "C:\path\to\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\RMC.BestFit.dll"
$env:NUMERICS_DLL = "C:\path\to\Numerics\Numerics\bin\Release\net8.0\Numerics.dll"

# bash / zsh
export BESTFIT_DLL=/path/to/RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\RMC.BestFit.dll
export NUMERICS_DLL=/path/to/Numerics/Numerics/bin/Release/net8.0/Numerics.dll

```

`resolve_bestfit_dll` and `resolve_numerics_dll()` use these variable first, then fall back to the NuGet cache and finally a local `packages/` folder.

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

## Troubleshooting
- `pythonnet` runtime error at import:
  - use `pythonnet.load("coreclr")` for the current .NET build
  - use `pythonnet.load("netfx")` only for legacy .NET Framework builds
- `FileNotFoundError` for DLLs:
  - set env vars explicitly
- `AddReference` load conflicts:
  - restart kernel/session and re-run top cells only once


## License
This project is released under the [Zero-Clause BSD (0BSD) license](LICENSE).
