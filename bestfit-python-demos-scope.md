# BestFit Python Examples - Project Scope

## Overview

This document defines the scope for a PythonNet demo repository that showcases the RMC-BestFit library for Python users. The goal is to provide practical, reproducible examples for flood frequency analysis, Bayesian statistical modeling, rating curve fitting, time series forecasting, and spatial extremes — all called directly from Python.

---

## Repository

**Name:** `bestfit-python-examples`

**Rationale:** Clear, searchable name that communicates these are reproducible examples for Python-based practitioners rather than a full wrapper.

**Location:** Separate from the core BestFit repo to:
- Keep demos independent from core library release cycles
- Make it easier for Python/hydrology communities to discover and clone
- Allow contributions from domain practitioners
- Support both Windows and cross-platform .NET runtimes

---

## Target Audience

- **Hydrologists & flood-risk analysts:** Automating flood frequency workflows
- **Engineers:** Validating model assumptions, uncertainty quantification, dam/levee safety
- **Water resources researchers:** Comparing estimation methods (MLE vs Bayesian vs GMM)
- **USACE practitioners:** Transitioning from desktop BestFit to Python-based pipelines

## Repository Structure

```
bestfit-python-examples/
|-- README.md                      # Overview, installation, getting started
|-- LICENSE                        # Same as BestFit (BSD-style, USACE-RMC)
|-- notebook-requirements.txt      # Necessary Python packages to install
|-- CONTRIBUTING.md                # How to contribute
|-- CODE_OF_CONDUCT.md             # Community guidelines
|
|-- notebooks/
|   |-- 00_getting_started.ipynb
|   |-- 01_distribution_fitting.ipynb
|   |-- 02_model_selection_and_comparison.ipynb
|   |-- 03_bayesian_flood_frequency.ipynb
|   |-- 04_distribution_analysis.ipynb
|   |-- 05_rating_curve_analysis.ipynb
|   |-- 06_time_series_forecasting.ipynb
|   |-- 07_spatial_extremes.ipynb
|   |-- 08_batch_workflow_and_reporting.ipynb
|   `-- helper_functions.py        # Shared helpers for plotting, I/O, etc.
|
|-- examples/
|   |-- flood_frequency_simple.py       # Bulletin 17C-style workflow
|   |-- rating_curve_example.py         # Two-segment rating curve
|   `-- regional_analysis.py            # Spatial GEV demonstration
|
|-- data/
|   |-- raw/                       # Sample datasets (CSV)
|   `-- processed/                 # Cleaned/cached outputs
|
`-- outputs/
    |-- figures/                   # Publication-ready plots
    `-- tables/                    # Model summaries, comparison tables
```

---

## Jupyter Notebooks

### 00. Getting Started
**Purpose:** Environment setup and hello-world invocation.

**Content:**
- Installing .NET runtime (Windows/Linux/macOS guidance)
- Installing PythonNet via pip
- Loading BestFit DLLs (Numerics.dll, RMC.BestFit.dll)
- First example: Create a Normal distribution, check PDF/CDF
- Reflection helpers to inspect available classes and methods
- Troubleshooting guide for common pythonnet/runtime issues

**Code Preview:**
```python
import clr
clr.AddReference("RMC.BestFit")
from RMC.BestFit.Models import UnivariateDistribution, UnivariateDistributionType

# Create a GEV distribution
gev = UnivariateDistribution(min_value=0, mode=50, quantile_90=100)
print(f"GEV Mean: {gev.Mean:.2f}, Std: {gev.StandardDeviation:.2f}")
print(f"P(X < 120) = {gev.CDF(120):.4f}")
```

**Outputs:**
- Runtime diagnostics table
- Pass/fail integration check

---

### 01. Distribution Fitting
**Purpose:** Parameter estimation from observed data using multiple methods.

**Content:**
- Data input types
- Probability distributions for flood frequency analysis
- `FittingAnalyses` method from BestFit
- Comparing goodness of fit metrics (AIC, BIC, RMSE)

**Real-world context:** Flood frequency analysis — fitting annual peak flows from a gauge station.

**Code Preview:**
```python
from RMC.BestFit.Analyses import FittingAnalysis

# Fit all 15 distributions to annual maximum flows
analysis = FittingAnalysis(data_frame)
analysis.RunAsync()

# Rank by AIC
ranked = sorted(analysis.Results, key=lambda x: x.AIC)
for result in ranked[:3]:
    print(f"{result.Distribution.Type}: AIC={result.AIC:.2f}")
```

---

### 02. Model Estimation
**Purpose:** Compare different BestFit Estimation methods

**Content:**

**Real-world context:** 

---

### 03. Bayesian Flood Frequency
**Purpose:** Practical Bayesian estimation for flood frequency studies.

**Content:**
- Understanding Bayesian workflow vs MLE
- Setting prior distributions (Jeffreys, quantile-based)
- Running DEMCzs sampler (differential evolution MCMC with snooker update)
- Interpreting posterior summaries (mean, median, credible intervals)
- Return-period quantile extraction with full uncertainty
- Sensitivity analysis: with/without historical or paleofloods
- Model diagnostics (effective sample size, trace plots, autocorrelation)

**Real-world context:** Incorporating historical/paleo information into a 100-year flood estimate with honest uncertainty bounds.

**Code Preview:**
```python
from RMC.BestFit.Models import UnivariateDistribution, UnivariateDistributionType
from RMC.BestFit.Analyses import UnivariateAnalysis

# Create GEV model
model = UnivariateDistribution(data_frame, UnivariateDistributionType.GeneralizedExtremeValue)

# Run Bayesian analysis
analysis = UnivariateAnalysis(model)
analysis.BayesianAnalysis.Iterations = 10000
analysis.BayesianAnalysis.WarmupIterations = 5000
analysis.RunAsync()

# Extract return period quantile
results = analysis.BayesianAnalysis.Results
q100 = model.InverseCDF(1 - 1/100, results.MAP.Values)
print(f"100-year flood: {q100:.1f} ± {uncertainty:.1f} m³/s")
```

---

### 04.Distribution Analysis
**Purpose:**

**Content:**

---


### 05. Rating Curve Analysis
**Purpose:** Stage-discharge relationship fitting and prediction.

**Content:**
- Two-/three-segment power-law rating curves
- Data quality handling (measurement uncertainty)
- Bayesian parameter estimation with DEMCzs
- Generating rating tables across stage ranges
- Forecast uncertainty propagation
- Extrapolation guidance and pitfalls
- Real vs synthetic examples

**Real-world context:** Deriving streamflow from stage recorders without direct discharge measurements.

---

### 06. Time Series Forecasting
**Purpose:** Streamflow prediction using AR, MA, ARIMA, and ARIMAX models.

**Content:**
- Autoregressive (AR) models
- Moving Average (MA) processes
- Integrated ARMA (ARIMA) for non-stationary flow
- Exogenous covariates (ARIMAX) — e.g., precipitation forcing
- Stationarity testing and differencing
- Model selection (AIC for lag order)
- Forecast intervals and diagnostics
- Multi-step ahead predictions

**Real-world context:** 12-month streamflow forecasting for water supply planning.

---

### 07. Spatial Extremes (Regional Analysis)
**Purpose:** Combining information across multiple sites using spatial dependence.

**Content:**
- Spatial GEV for regional frequency analysis
- Index flood approach and regional L-moments
- Spatial correlation structures
- Pooling information to improve at-site estimates
- Ungauged site prediction
- Handling heterogeneous record lengths

**Real-world context:** Robust 100-year flood estimate for an ungauged tributary.

---

### 08. Batch Workflow and Reporting
**Purpose:** Operationalize the notebooks into a config-driven batch runner.

**Content:**
- YAML/JSON configuration for parameterized runs
- Loop over multiple sites, scenarios, or models
- Consolidate outputs: tables, figures, HTML report
- Version control artifacts and results
- Export to common formats (Excel, PDF, CSV)
- Integration with automated reporting pipelines

**Real-world context:** Running 50 sites through a standardized flood frequency study in one run.

## Key Features of BestFit

### Bayesian-First Philosophy
RMC-BestFit is designed around Bayesian estimation as the primary inference method:

- **DEMCzs Sampler**: Differential Evolution MCMC with snooker update — self-tuning, robust to multimodal posteriors
- **Quantile Priors**: Incorporate engineering judgment through prior distributions specified via quantiles
- **Jeffreys Priors**: Non-informative defaults for scale parameters
- **Full Uncertainty Quantification**: Posterior distributions for all parameters and derived quantities (return periods, forecasts, etc.)
- **Model Comparison**: DIC, WAIC, LOO-CV with Pareto-smoothed importance sampling

### Advanced Data Handling
The DataFrame API supports multiple observation types:

| Data Type | Class | Use Case |
|-----------|-------|----------|
| Exact | `ExactData` | Systematic gauge records (most common) |
| Uncertain | `UncertainData` | Historical floods with measurement error |
| Interval | `IntervalData` | Paleoflood deposits with bounded magnitude |
| Threshold | `ThresholdData` | Perception thresholds (exceedance/non-exceedance; triggers) |

### 15 Univariate Distributions
All optimized for hydrologic extremes:

| Distribution | Class Name | Typical Application |
|--------------|------------|---------------------|
| Generalized Extreme Value | `GeneralizedExtremeValue` | Annual maximum flood frequency |
| Log-Pearson Type III | `LogPearsonTypeIII` | Bulletin 17C standard |
| Generalized Pareto | `GeneralizedPareto` | Peaks-over-threshold (POT) analysis |
| Normal | `Normal` | General continuous data |
| Log-Normal | `LogNormal` | Positively skewed data |
| Gumbel | `Gumbel` | Type I extreme value (simplified GEV) |
| Gamma | `GammaDistribution` | Duration, waiting times |
| Weibull | `Weibull` | Minimum extremes, reliability |
| *And 7 more...* | | Pearson III, Student-t, Exponential, Uniform, Triangular, Pert, Beta |

---

## Code Style & Dependencies

### Python Packages
```txt
pythonnet>=3.0.0
pandas>=1.2.0
numpy>=1.20.0
scipy>=1.6.0
matplotlib>=3.3.0
jupyter>=1.0.0
pyyaml>=5.3.0
```

### .NET Requirements
- .NET 6.0+ for the current local `RMC-BestFit` build
- .NET Framework 4.7.2+ only when intentionally using a legacy BestFit build
- Numerics.dll (math/MCMC engine)
- RMC.BestFit.dll (models and analyses)

### DLL Resolution Policy
The helper functions should keep BestFit and Numerics paired whenever possible.

Preferred order:
1. User-pinned environment variables: `RMC_BESTFIT_DLL` and `RMC_NUMERICS_DLL`.
2. `C:\GIT\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\...`.
3. `C:\GIT\RMC-BestFit Version 2.0 (Beta-3)\Release\Libraries\...`.
4. `C:\GIT\RMC-BestFit-Dev\...`, then standalone `C:\GIT\Numerics\...` only as a fallback for Numerics.

The `RMC-BestFit` source build is preferred over the standalone `Numerics` build because BestFit is compiled against a specific Numerics API surface. Loading both DLLs from the same BestFit output folder reduces version skew and avoids namespace/import failures. Environment variables remain first because they are an explicit user override.

### Code Quality
- Notebooks use markdown cells for narrative
- Each notebook runs top-to-bottom without manual intervention
- Comments explain the "why" behind choices, not just the "what"
- Plots follow consistent styling (color palettes, fonts, grid)
- Helper functions in `helper_functions.py` to keep notebooks readable

### Reference Repository Alignment
Use the local `C:\GIT\Numerics-Python-Examples` repository as the style and structure reference:

- Keep notebooks practical and executable top-to-bottom.
- Start with environment/runtime setup, then DLL loading, then namespace imports.
- Include enough markdown to explain the modeling decision before the code that implements it.
- Prefer concise comments inside code cells for conversion, API-boundary, and statistical assumptions.
- End notebooks with a short summary and IEEE-style references.
- Keep script examples runnable from the repository root and write deterministic CSV outputs under `outputs/tables`.

---

## Open Questions / Refinements

- **DLL pathing:** Keep manual reference loading for demos; document environment-variable overrides as the recommended user customization point.
- **Licensing:** Confirm licensing obligations for batch/automated execution
- **Cross-platform:** Test and document Linux/macOS workarounds (WSL, Docker, etc.)
- **Threading:** Document any thread-safety constraints for parallel site processing
- **Export formats:** Which output formats most valuable for practitioners? (Excel, Parquet, NetCDF, etc.)
- **Notebook depth:** Expand notebooks 03 and 04 from placeholders into runnable Bayesian and distribution-analysis workflows once the current BestFit Bayesian API is stable.
