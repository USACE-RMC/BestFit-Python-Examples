> [!IMPORTANT]
> **Under active review and development.** This repository's examples, code, plots, documentation, and results are subject to change as review progresses.

# BestFit Python Examples

[![License: 0BSD](https://img.shields.io/badge/License-0BSD-blue.svg)](LICENSE)

Twelve notebooks teach how to construct, configure, run, inspect and plot headless
[RMC.BestFit](https://github.com/USACE-RMC/RMC-BestFit) analyses directly from Python through pythonnet.
Each notebook starts with the original example's raw observations, creates actual .NET objects,
executes the library's calculation or estimation methods, and plots the results it just computed.
No GUI, API server or saved analysis project is required.

| Notebook | Examples and purpose |
|---|---|
| [00 · Time-series data](notebooks/00_time_series_data.ipynb) | USGS daily, instantaneous, peak and measured series; other import routes |
| [01 · Input data](notebooks/01_input_data.ipynb) | Calendar/water-year maxima, Big Bear POT, historical and uncertain information |
| [02 · Distribution fitting](notebooks/02_distribution_fitting.ipynb) | Fifteen candidates for four Kamp/Zwettl inputs |
| [03 · Stationary and information expansion](notebooks/03_stationary_information_expansion.ipynb) | Nine Viglione GEV alternatives |
| [04 · Nonstationary univariate](notebooks/04_nonstationary_univariate.ipynb) | Brays Bayou LP-III links and DIC model averaging |
| [05 · Bulletin 17C](notebooks/05_bulletin_17c.ipynb) | Original examples 2 (Orestimba) and 4 (Pueblo), GMM with MVN/BCB uncertainty |
| [06 · Advanced univariate](notebooks/06_advanced_univariate.ipynb) | Point process, mixtures/zero inflation, competing flood types |
| [07 · Bivariate analysis](notebooks/07_bivariate_analysis.ipynb) | Six copulas, value/CDF scatter and contours |
| [08 · Coincident frequency](notebooks/08_coincident_frequency.ipynb) | Sum of Normals and Waimea stage response |
| [09 · Rating curves](notebooks/09_rating_curves.ipynb) | Mississippi field measurements and segmented ratings |
| [10 · Classic time series](notebooks/10_classic_time_series.ipynb) | Airline, Nile and Mauna Loa |
| [11 · Regression](notebooks/11_regression.ipynb) | Simple/multiple consumption regression |

## Setup

Use **Python 3.12**, Git and the **.NET 10 SDK** for the validated Windows setup.
The package declares Python 3.10 or later; other Python versions and Linux/macOS are not covered
by this validation. Work from a checkout: observations and notebooks are not bundled in the wheel.

```powershell
git clone https://github.com/USACE-RMC/BestFit-Python-Examples.git
cd BestFit-Python-Examples
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[notebooks,test]"
.venv/Scripts/python.exe scripts/bootstrap_runtime.py --install-plots
.venv/Scripts/python.exe -m pip install jupyterlab
.venv/Scripts/python.exe -m ipykernel install --prefix .venv --name bestfit-examples --display-name "BestFit examples"
.venv/Scripts/python.exe -m jupyterlab
```

Bootstrap builds the exact public BestFit revision in [runtime-lock.json](runtime-lock.json)
with RMC.Numerics 2.2.0 and installs its canonical `bestfit_plots` package.
The loader checks assembly hashes, versions and the .NET host before using them.
An optional `--bestfit-source PATH` must identify a clean checkout at the locked commit.
The installer enables long paths for its Git subprocesses without changing global Git settings.

## Run and adapt an example

Select the **BestFit examples** kernel and use **Restart Kernel and Run All**.
That action performs the analyses at their original settings, including MCMC and bootstrap work.
The execution cells report measured runtime. There is no cached-replay switch.
The longer notebooks run multiple fits and dependencies; review the visible configuration before starting.

Follow the substantive cells in order: load raw rows, create `DataFrame` or `TimeSeries`,
construct the model, configure priors and analysis settings, call `RunAsync`, and read the
result properties. For example, notebook 02 constructs its `ExactData`/`IntervalData`/`ThresholdData`
records and candidate distributions before calling `FittingAnalysis.RunAsync` and reading
`FittedDistributions`. Bayesian notebooks expose the model, sampler, seeds, chain lengths,
probability ordinates and prediction settings in the same way.

Replace raw observations with your own timestamp/value or historical-data rows, preserving units
and the meaning of uncertain observations. Copy the substantive cells into a Python script:
the maintained [Python notebook sources](scripts/notebook_sources/) also run as ordinary scripts
from the repository root. Runtime and plotting helpers do not construct or execute analyses.

## Data, interpretation and figures

[data/raw/manifest.json](data/raw/manifest.json) binds observation-only fixtures to the original app
projects and checksums. Separate raw CFA response grids retain the original response surfaces.
The existing datasets, case roster, models and settings remain the teaching examples; C# Verification
fixtures provide API references rather than replacement scenarios. The [workflow map](docs/headless-workflow-map.md)
records those references and the Python construction steps.

Every displayed analysis figure receives newly computed in-memory objects through the canonical
BestFit plotting utilities. Tables and diagnostic cells read those same objects.
The [desktop plot gallery](docs/plot-gallery/index.html), [app plot map](docs/app-plot-map.md),
original `data/projects/` archives and `results/` caches are retained as separate historical
comparison evidence. Notebooks do not load them. `scripts/compare_saved_analyses.py` is a legacy
comparison utility and is not the curriculum execution path.

Upstream BestFit narratives include AI-generated material that has not yet been reviewed.
Existing scientific context is retained where appropriate, with procedural explanations rewritten
to teach the Python workflow. Successful execution does not establish convergence or scientific acceptance.
Keep the Airline diagnostic concerns, the Nile source-date discrepancy and explicit display correction,
and the distinction between BestFit's B17C GMM uncertainty and official EMA/MGBT results in view.
Notebook 05 refers to [Bulletin 17C Appendix 10](https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf).

## Development and validation

```powershell
.venv/Scripts/python.exe scripts/create_notebooks.py
.venv/Scripts/python.exe scripts/validate_notebooks.py --write
.venv/Scripts/python.exe -m pytest --basetemp=.runtime/pytest
```

The generator reads only the explicit Python sources and recreates unexecuted notebooks.
Validation starts each notebook in a fresh independent kernel in a workspace containing code,
raw inputs and the verified runtime. Saved projects, result caches and prior rerun outputs are absent;
an access guard rejects attempts to read them. No fitted object is restored during this validation.
Receipts in [validation/headless/](validation/headless/) record code/input/runtime identities,
actual executions, elapsed time, complete case counts and figure lineage. Per-notebook references,
settings, checks and limitations are described in the [validation report](docs/headless-validation.md). Select notebooks with
`--notebooks 02_distribution_fitting`, for example; full source settings remain in force.
`scripts/run_curriculum_analyses.py` invokes this same notebook workflow.
Use `scripts/validate_notebooks.py --audit-only` to compare retained execution evidence
with its original hashes without repeating estimation or rewriting receipts. It checks
the current source, helpers, raw inputs, runtime, run records, tables and embedded PNGs.
Regenerating notebooks clears their outputs, so run validation with `--write` afterward.

Tests protect raw-data provenance, runtime identity, explicit teaching code, generator consistency,
plot presentation and legacy comparison infrastructure. Reading C# Verification source does not run
its tests; no blanket Verification run is part of notebook validation.
Earlier validation receipts and review material remain historical evidence of the superseded workflow.

## Authors, review and citation

Authors: **[Sadie Niblett](https://orcid.org/0009-0008-8588-4816)** and **[C. Haden Smith](https://orcid.org/0000-0002-4651-9890)**, U.S. Army Corps of Engineers, Risk Management Center.

Reviewer: **[Julian “Tiki” Gonzalez](https://orcid.org/0009-0009-9058-7653)**, U.S. Army Corps of Engineers, Risk Management Center. Reviewer credit does not imply completion of the ongoing review.

Use [CITATION.cff](CITATION.cff) to cite the repository, and identify the commit used for reproducibility.
This development version is **0.2.0 (unreleased)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for corrections and reproducibility reports.

## License

This project uses the [Zero-Clause BSD (0BSD) license](LICENSE), consistent with
[Numerics-Python-Examples](https://github.com/USACE-RMC/Numerics-Python-Examples).
Dependency licenses remain with their respective projects.
