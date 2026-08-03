# BestFit Python Examples

[![License: 0BSD](https://img.shields.io/badge/License-0BSD-blue.svg)](https://opensource.org/licenses/0BSD)
[![DOI](https://zenodo.org/badge/1135095276.svg)](https://doi.org/10.5281/zenodo.19715583)

This repository contains Python notebooks that demonstrate the USACE-RMC BestFit .NET library through pythonnet. The notebooks provide practical, reproducible examples of BestFit applications for flood frequency, rating curves, forecasting, and regional analysis.

## What This Repo Contains
- `notebooks/` contains 7 Jupyter notebooks organized by topic
- `examples/` contains runnable Python example scripts
- `notebooks/helper_functions.py` contains shared helper functions
- `notebooks/` also includes YAML workflow configuration examples for batch analysis

## Notebooks Guide
- `00_getting_started.ipynb`: runtime setup, DLL loading, first distribution calls, and troubleshooting
- `01_distribution_fitting.ipynb`: a distribution tour and shape comparisons
- `02_model_estimation.ipynb`: empirical return periods and fitted quantile curves
- `03_time_series_forecasting.ipynb`: forecasting workflows and time-series examples
- `04_rating_curve_analysis.ipynb`: segmented stage-discharge fitting and diagnostics
- `05_spatial_extremes.ipynb`: index-flood regional pooling examples
- `06_batch_workflow_and_reporting.ipynb`: config-driven multi-site batch workflows and exports

## Project Structure

```
BestFit-Python-Examples/
├── examples/                             # Standalone Python example scripts
│   ├── flood_frequency_simple.py               # Simple flood frequency analysis example
│   ├── rating_curve_example.py                 # Rating curve (stage-discharge) fitting example
│   ├── regional_analysis.py                    # Index-flood regional analysis example
│   └── output_tables/                          # CSV output directory for examples
├── notebooks/                            # Jupyter notebooks and helper code
│   ├── 00_getting_started.ipynb                # Setup and configuration guide
│   ├── 01_distribution_fitting.ipynb           # Distribution fitting and comparison
│   ├── 02_model_estimation.ipynb               # Parameter estimation workflows
│   ├── 03_time_series_forecasting.ipynb        # Time series forecasting with ARIMA
│   ├── 04_rating_curve_analysis.ipynb          # Stage-discharge relationship modeling
│   ├── 05_spatial_extremes.ipynb               # Regional flood frequency analysis
│   ├── 06_batch_workflow_and_reporting.ipynb   # Batch processing and reporting
│   ├── helper_functions.py                     # Shared utility functions (DLL resolution, conversions)
│   ├── batch_workflow_config_1.yaml            # Example batch configuration (simple)
│   ├── batch_workflow_config_2.yaml            # Example batch configuration (advanced)
│   └── outputs/                                # Output directory for notebook results
├── CONTRIBUTING.md                       # Contribution guidelines
├── CODE_OF_CONDUCT.md                    # Code of conduct
├── CITATION.cff                          # Citation metadata
├── LICENSE                               # BSD-3-Clause license
├── README.md                             # This file
└── notebook-requirements.txt             # Python dependencies
```

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
**NOTE:** The commands below assume Windows. See notebook `00_getting_started.ipynb` for macOS/Linux equivalents.
**NOTE:** This demo uses both `RMC.BestFit.dll` and `Numerics.dll`. When you download RMC BestFit, Numerics is typically included as a dependency, so you generally only need BestFit to access both. You can also download Numerics separately if you prefer.

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

   The notebooks auto-discover the DLL in either location via `resolve_bestfit_dll()` in [notebooks/helper_functions.py](notebooks/helper_functions.py).

4. Load BestFit and Numerics in a notebook or script

   ```python
   import pythonnet
   pythonnet.load("coreclr")

   import clr
   from helper_functions import resolve_bestfit_dll, resolve_numerics_dll

   clr.AddReference(str(resolve_bestfit_dll()))
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

- `examples/output_tables/flood_frequency_empirical_vs_model.csv`
- `examples/output_tables/flood_frequency_return_period_table.csv`
- `examples/output_tables/rating_curve_observed_vs_fit.csv`
- `examples/output_tables/rating_curve_table.csv`
- `examples/output_tables/regional_analysis_site_records.csv`
- `examples/output_tables/regional_analysis_site_quantiles.csv`

## Troubleshooting
- `pythonnet` runtime error at import:
  - use `pythonnet.load("coreclr")` for the current .NET build
  - use `pythonnet.load("netfx")` only for legacy .NET Framework builds
- `FileNotFoundError` for DLLs:
  - set env vars explicitly
- `AddReference` load conflicts:
  - restart kernel/session and re-run top cells only once

## Best Practices

- **Always load the .NET runtime first** — Call `pythonnet.load("coreclr")` before importing `clr`. This is the most common setup mistake.
- **Use virtual environments** — Create a `.venv` for this project to avoid dependency conflicts.
- **Check data quality** — Review raw data for outliers, gaps, and stationarity before fitting distributions.
- **Use multiple distributions** — BestFit can fit many distributions simultaneously; compare AIC/BIC to select the best.
- **Validate results** — Always inspect diagnostic plots and compare fitted models to empirical data visually.
- **Document your workflow** — Keep notes on data sources, preprocessing steps, and modeling decisions for reproducibility.

## Resources

- [RMC-BestFit GitHub Repository](https://github.com/USACE-RMC/RMC-BestFit) — Main BestFit project
- [Numerics-Python-Examples](https://github.com/USACE-RMC/Numerics-Python-Examples) — Numerics library demonstrations
- [USACE-RMC Website](https://www.rmc.usace.army.mil/Software/RMC-BestFit/) — Official software page
- [pythonnet Documentation](https://pythonnet.github.io/) — Python/.NET bridge documentation
- [Jupyter Notebook Documentation](https://jupyter-notebook.readthedocs.io/) — Notebook platform documentation

## References
<a id="1">[1]</a>
Haan, C. T., Barfield, B. J., & Hayes, J. C. (1994). *Design hydrology and sedimentology for small catchments*. Academic Press.

For more details on flood frequency analysis theory, see documentation within the BestFit notebooks.

## License
This project is released under the [Zero-Clause BSD (0BSD) license](LICENSE).
