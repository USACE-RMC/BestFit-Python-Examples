# BestFit Python Examples

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

Use Python 3.10+ in a virtual environment. Work from a checkout: large fixture/result files are not installed into the examples wheel. Keep a compatible RMC-BestFit checkout beside it, or substitute its path below. [runtime-lock.json](runtime-lock.json) records the required revision. Before it is published, use the supplied local development checkout.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[notebooks,test]"
.venv/Scripts/python.exe -m pip install ../RMC-BestFit/skills/bestfit-frequency
.venv/Scripts/python.exe -m pip install jupyterlab
.venv/Scripts/python.exe -m jupyterlab
```

On Linux/macOS the interpreter is `.venv/bin/python`. Open a notebook and select that environment's Python kernel. `RUN_ANALYSES = False` is the default. Saved walkthroughs need no .NET host, live download, API server or new MCMC run. They verify source and cache checksums before using saved coordinates.

## Repeat an analysis

Install the .NET **10 SDK** and build the locked portable BestFit source with **RMC.Numerics 2.2.0**. Both assemblies are verified as one runtime; the loader never chooses arbitrary DLLs from a machine cache.

```powershell
.venv/Scripts/python.exe scripts/bootstrap_runtime.py --bestfit-source ../RMC-BestFit --install-plots
```

Without `--bestfit-source`, bootstrap clones the exact locked revision into `.runtime/source` once it is available upstream. Restart the kernel, set `RUN_ANALYSES = True`, and execute the desired notebook. Priors, seeds, iterations, thinning, transformations and probability ordinates are retained. Linked analyses rerun in dependency order; coincident frequency receives fresh marginal uncertainty samples. Full runs can take substantially longer. Execution success and sampler convergence are separate checks.

Reruns write receipts and compressed results under `output/reruns/`. Checked-in `results/` caches describe the original saved app projects, making desktop comparisons reproducible. See `python scripts/run_curriculum_analyses.py --help` for selective batch execution and verified receipt reuse.

## Shared app plots

The notebooks use the canonical `bestfit_plots` package in the BestFit skill. The same package serves API snapshots. The [plot gallery](docs/plot-gallery/index.html) and [app-to-Python map](docs/app-plot-map.md) trace 45 desktop slots to source methods, adapters and independent geometry checks. Read each recorded status before claiming parity.

```python
from bestfit_examples.results import saved_case
case = saved_case("bulletin-17c-examples", "Example #2")
display(case.settings)
case.show("frequency")
```

The BestFit skill's `scripts/plot_source.py` lists and renders saved case, PlotSpec and API-source artifacts, writing PNG/SVG/JSON. The target is app geometry and semantics with Matplotlib fonts; custom desktop styles and exact pixels are outside the comparison.

## Sources and validation

[data/source-manifest.json](data/source-manifest.json) records hashes and original paths for 22 full-fidelity project exports (about 145 MiB). The additional Sinnemahoning fixture supplies uncertain observations for notebook 01 and the plot gallery. Historical bounds, uncertain observations, compressed payloads, configurations and saved ensembles are preserved. Notebook 05 cites official [Bulletin 17C Appendix 10](https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf); notebook 10 documents the Nile date discrepancy and explicit display correction while preserving original bytes.

```powershell
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe scripts/validate_notebooks.py --write
```

Validation uses a separate kernel for every notebook. [validation/](validation/) records execution, full-settings runs, retained superseded attempts and source checks. These are engineering evidence and numerical diagnostics, not scientific acceptance of every fitted model. Rebuild caches after reviewed adapter changes with `python scripts/build_saved_results.py`.

The earlier seven notebooks and loose scripts are superseded. Their history remains in Git; [migration.md](docs/migration.md) maps former entry points. Read the [source review](docs/source-review.md) for the scientific context and corrections; the five-package plan is retained under [docs/superpowers](docs/superpowers/).

Released under the [Zero-Clause BSD license](LICENSE).
