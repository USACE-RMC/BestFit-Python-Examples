> [!IMPORTANT]
> **Under active review and development.** This repository's examples, code, plots, documentation, and results are subject to change as review progresses.

# BestFit Python Examples

[![License: 0BSD](https://img.shields.io/badge/License-0BSD-blue.svg)](LICENSE)

Twelve concise walkthroughs follow the projects in [RMC-BestFit](https://github.com/USACE-RMC/RMC-BestFit), with frozen inputs, visible model choices, saved results and an explicit full-settings rerun path. They cover flood frequency, dependence, rating curves and time series. Controlled synthetic cases are identified as such.

| Notebook | App examples and purpose |
|---|---|
| [00 · Time-series data](notebooks/00_time_series_data.ipynb) | USGS daily, instantaneous, peak and measured series; other import routes |
| [01 · Input data](notebooks/01_input_data.ipynb) | Calendar/water-year maxima, Big Bear POT, historical information |
| [02 · Distribution fitting](notebooks/02_distribution_fitting.ipynb) | Fifteen candidates for four Kamp/Zwettl inputs |
| [03 · Stationary and information expansion](notebooks/03_stationary_information_expansion.ipynb) | Nine Viglione GEV alternatives |
| [04 · Nonstationary univariate](notebooks/04_nonstationary_univariate.ipynb) | Brays Bayou LP-III links and DIC model averaging |
| [05 · Bulletin 17C](notebooks/05_bulletin_17c.ipynb) | Official examples 2 (Orestimba) and 4 (Pueblo), MVN and BCB |
| [06 · Advanced univariate](notebooks/06_advanced_univariate.ipynb) | Point process, mixtures/zero inflation, competing flood types |
| [07 · Bivariate analysis](notebooks/07_bivariate_analysis.ipynb) | Six copulas, value/CDF scatter and contours |
| [08 · Coincident frequency](notebooks/08_coincident_frequency.ipynb) | Sum of Normals and Waimea stage response |
| [09 · Rating curves](notebooks/09_rating_curves.ipynb) | Mississippi field measurements and segmented ratings |
| [10 · Classic time series](notebooks/10_classic_time_series.ipynb) | Airline, Nile and Mauna Loa |
| [11 · Regression](notebooks/11_regression.ipynb) | Simple/multiple consumption regression |

## Run the saved walkthroughs

Use **Python 3.12** for the validated Windows setup below, with Git available on PATH. The package declares Python 3.10 or later; this publication check covers Python 3.12 on Windows. Work from a checkout: large fixture/result files are not installed into the examples wheel. [runtime-lock.json](runtime-lock.json) records the exact BestFit revision used for the runtime and shared plotting package.

```powershell
git clone https://github.com/USACE-RMC/BestFit-Python-Examples.git
cd BestFit-Python-Examples
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[notebooks,test]"
.venv/Scripts/python.exe scripts/install_plots.py
.venv/Scripts/python.exe -m pip install jupyterlab
.venv/Scripts/python.exe -m ipykernel install --prefix .venv --name bestfit-examples --display-name "BestFit examples"
.venv/Scripts/python.exe -m jupyterlab
```

The plotting installer reads the exact public revision from `runtime-lock.json` and enables long paths for its Git subprocesses on Windows without changing global Git settings. On Linux/macOS the interpreter is `.venv/bin/python`; those platforms were not part of this validation. Open a notebook and select **BestFit examples**. `RUN_ANALYSES = False` is the default. After installing Python dependencies, saved walkthroughs need no .NET host, data download, API server or new MCMC run. They verify source and cache checksums before using saved coordinates.

## Repeat an analysis

Install the .NET **10 SDK** and build the locked portable BestFit source with **RMC.Numerics 2.2.0**. Both assemblies are verified as one runtime; the loader never chooses arbitrary DLLs from a machine cache.

```powershell
.venv/Scripts/python.exe scripts/bootstrap_runtime.py --install-plots
```

Bootstrap clones the publicly available locked revision into `.runtime/source`. Alternatively, pass `--bestfit-source PATH` for a clean checkout at that exact commit; a different revision is rejected. Restart the kernel, set `RUN_ANALYSES = True`, and execute the desired notebook. Priors, seeds, iterations, thinning, transformations and probability ordinates are retained. Linked analyses rerun in dependency order; coincident frequency receives fresh marginal uncertainty samples. Full runs can take substantially longer. Execution success and sampler convergence are separate checks.

Reruns write receipts and compressed results under `output/reruns/`. Checked-in `results/` caches describe the original saved app projects, making desktop comparisons reproducible. See `python scripts/run_curriculum_analyses.py --help` for selective batch execution and verified receipt reuse.

## Shared app plots

The notebooks use the canonical `bestfit_plots` package in the BestFit skill. The same package serves API snapshots. The [plot gallery](docs/plot-gallery/index.html) and [app-to-Python map](docs/app-plot-map.md) trace 45 desktop slots to source methods, adapters and independent geometry checks. Read each recorded status before claiming parity.

```python
from bestfit_examples.results import saved_case
case = saved_case("bulletin-17c-examples", "Example #2")
display(case.settings)
case.show("frequency")
```

The BestFit skill's `scripts/plot_source.py` lists and renders saved case, PlotSpec and API-source artifacts, writing PNG/SVG/JSON. The target is app geometry and semantics with Matplotlib fonts; custom desktop styles and exact pixels are outside the comparison. The examples add spacing for dense CDF contour labels and retain the saved desktop log range for the zero-inflated mixture; both are display adjustments with source coordinates preserved.

## Sources and validation

Narration in the upstream BestFit examples includes AI-generated material that has not yet been reviewed. Treat it as provisional. Existing notebook narratives are retained, with narrowly justified technical corrections; executable checks and source records do not establish that every explanation or model has received scientific review. The documented Airline convergence concerns and B17C GMM/EMA distinction remain relevant.

The frozen project revision is recorded separately from the runtime. Only description cells differ from the current BestFit examples; the frozen descriptions remain unchanged.

[data/source-manifest.json](data/source-manifest.json) records hashes and original paths for 22 full-fidelity project exports (about 145 MiB). The included Sinnemahoning fixture supplies uncertain observations for notebook 01 and the plot gallery. Historical bounds, uncertain observations, compressed payloads, configurations and saved ensembles are preserved. Notebook 05 cites official [Bulletin 17C Appendix 10](https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf); notebook 10 documents the Nile date discrepancy and explicit display correction while preserving original bytes.

```powershell
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/validate_notebooks.py --write
```

The full Python test suite includes managed restoration checks and requires the runtime bootstrap above. Notebook validation uses a separate kernel for every notebook and can use saved results without .NET. [validation/](validation/) records execution, full-settings runs, retained superseded attempts and source checks. These are engineering evidence and numerical diagnostics, not scientific acceptance of every fitted model. Rebuild caches after reviewed adapter changes with `python scripts/build_saved_results.py`.

The earlier seven notebooks and loose scripts are superseded. Their history remains in Git; [migration.md](docs/migration.md) maps former entry points. Read the [source review](docs/source-review.md) for the scientific context and corrections; the five-package plan is retained under [docs/superpowers](docs/superpowers/).

## Authors, review and citation

Authors: **[Sadie Niblett](https://orcid.org/0009-0008-8588-4816)** and **[C. Haden Smith](https://orcid.org/0000-0002-4651-9890)**, U.S. Army Corps of Engineers, Risk Management Center.

Reviewer: **[Julian “Tiki” Gonzalez](https://orcid.org/0009-0009-9058-7653)**, U.S. Army Corps of Engineers, Risk Management Center. Reviewer credit does not imply completion of the ongoing review.

Use [CITATION.cff](CITATION.cff) to cite the repository, and identify the commit used for reproducibility. This development version is **0.2.0 (unreleased)**. See [CONTRIBUTING.md](CONTRIBUTING.md) for corrections and reproducibility reports.

## License

This project uses the [Zero-Clause BSD (0BSD) license](LICENSE), consistent with [Numerics-Python-Examples](https://github.com/USACE-RMC/Numerics-Python-Examples). Dependency licenses remain with their respective projects.
