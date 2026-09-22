"""Write the twelve concise app-example walkthroughs; results are generated separately."""
from pathlib import Path
from textwrap import dedent
import hashlib
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]
SETUP='''
from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / "runtime-lock.json").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
import json
import pandas as pd
from IPython.display import display
from bestfit_examples.project_data import load_project
from bestfit_examples.data import input_inventory, series_inventory
from bestfit_examples.results import saved_case
from bestfit_examples.presentation import (case_metrics, case_provenance, compare_frequency,
    composite_weights, trend_ownership, uncertain_observations)
%matplotlib inline
RUN_ANALYSES = False  # True: rerun the saved analysis and its dependencies at full original settings.
'''


def markdown(text): return nb.v4.new_markdown_cell(dedent(text).strip())
def code(text): return nb.v4.new_code_cell(dedent(text).strip())


def write(filename,title,intro,cells):
    book=nb.v4.new_notebook(cells=[markdown(f"# {title}\n\n{intro}"),markdown('''
        **Execution:** the default walkthrough reads checked saved app results, so it needs no live download or MCMC run.
        Install this repository and the shared `bestfit-plots` package as described in the [README](../README.md).
        To repeat an analysis, first build the pinned .NET runtime, set `RUN_ANALYSES = True`, and run the notebook in a fresh kernel.
        The rerun retains the source priors, seeds, sampling settings and probability ordinates; receipts are saved under `output/reruns/`.
        '''),code(SETUP),*cells],metadata={"kernelspec":{"display_name":"BestFit examples","language":"python","name":"bestfit-examples"},
                                                         "language_info":{"name":"python","version":"3.12"}})
    for index, cell in enumerate(book.cells):
        identity = f"{filename}\0{index}\0{cell.cell_type}\0{cell.source}".encode("utf-8")
        cell["id"] = hashlib.sha256(identity).hexdigest()[:12]
    destination=ROOT/"notebooks"/filename
    destination.parent.mkdir(exist_ok=True)
    nb.write(book,destination)
    print(f"{filename}: {len(book.cells)} cells")


def main():
    write("00_time_series_data.ipynb","00 · Time-series data and reproducible setup",
          "Start with what was observed: daily values, instantaneous measurements, annual peaks, and paired field measurements represent different sampling processes.",[
        markdown('''
        ## Frozen USGS imports
        The app's `usgs-download-example.bestfit` contains eight series. Daily discharge is a daily summary;
        instantaneous discharge describes conditions at a timestamp; an annual peak is the largest observed event in a year.
        Measured stage and discharge are separate field series used to develop a rating curve after an explicit timestamp join.
        This source stores 939 stage records and 412 discharge records; calling every stored row a pair would be incorrect.
        These distinctions determine which later analysis is appropriate.
        '''),
        code('''
        PROJECT = "usgs-download-example"
        project = load_project(PROJECT)
        display(series_inventory(project))
        print("Source:", project["source"]["relative_path"])
        print("SHA256:", project["source"]["sha256"])
        '''),
        markdown('''
        ## Daily discharge and seasonality
        The Moose River daily record shows the observations available for block-maxima extraction.
        The seasonality view uses the app's monthly summaries. Its bands describe the spread of monthly observations;
        the app labels these bands “Confidence Interval.” They are not uncertainty bounds for a fitted flood-frequency curve.
        '''),
        code('''
        daily = saved_case(PROJECT, "USGS - 01134500 - Daily Discharge")
        display(daily.settings)
        daily.show("series")
        daily.show("seasonality")
        '''),
        markdown('''
        ## Annual peaks and other import routes
        Peak seasonality is a monthly event-frequency histogram. ACF/PACF views keep the app's missing-data guard;
        a gap is not treated as a zero or silently interpolated.
        The app also supplies GHCN precipitation, CHMN, HEC-DSS and manual-entry projects in this repository's frozen source inventory.
        The ABOM example remains linked from the app's `examples/1-time-series-data` folder; online imports are optional updates, not prerequisites for this walkthrough.
        '''),
        code('''
        peaks = saved_case(PROJECT, "USGS - 01614000 - Peak Discharge")
        peaks.show("seasonality")
        routes = ["ghcn-download-example", "chmn-download-example", "hec-dss-import-example", "manual-entry-example"]
        display(pd.concat([series_inventory(load_project(slug)).assign(Project=slug) for slug in routes], ignore_index=True))
        '''),
        markdown("**Next:** notebook 01 turns the observed records into analysis inputs while retaining dates, units and historical information.")])

    write("01_input_data.ipynb","01 · Input data for frequency analysis",
          "Construct a sample that matches the question: annual maxima, peaks over a threshold, or a record expanded with historical bounds.",[
        markdown('''
        ## Calendar-year versus water-year maxima
        Both Moose River alternatives contain 80 maxima. Their year boundaries can assign an event to different blocks;
        the event timestamp remains attached to the annual index. Select the block definition before fitting a distribution.
        '''),
        code('''
        PROJECT = "usgs-block-max-example"
        project = load_project(PROJECT)
        display(input_inventory(project))
        calendar_year = saved_case(PROJECT, "USGS - 01134500 - Block Max - Calendar Year")
        water_year = saved_case(PROJECT, "USGS - 01134500 - Block Max - Water Year")
        display(pd.concat([calendar_year.settings.assign(Alternative="Calendar year"), water_year.settings.assign(Alternative="Water year")]))
        water_year.show("chronology")
        water_year.show("frequency")
        '''),
        markdown('''
        ## Peaks over threshold
        The Big Bear GHCN example uses a 1-inch threshold and retains 233 peaks over 67 observation years.
        The threshold diagnostics use the same saved smoothing function and period as extraction.
        Mean residual life and GPD parameter stability help examine a threshold; they do not automatically select it or establish independence.
        '''),
        code('''
        pot_project = load_project("ghcn-peaks-over-threshold-example")
        display(input_inventory(pot_project))
        pot = saved_case("ghcn-peaks-over-threshold-example", "GHCN-USC00040741-POT")
        display(pot.settings)
        pot.show("mean_residual_life")
        pot.show("shape")
        '''),
        markdown('''
        ## Exact, uncertain, interval and threshold information
        Exact observations, uncertain measurements, event intervals, and perception thresholds make different likelihood contributions.
        A threshold window encodes what would have been noticed over a period; its duration is information, not a fabricated series of annual floods.
        Viglione's temporal-expansion input illustrates historical information. Notebook 05 uses the original Bulletin 17C records;
        the newer USGS annual-peak download is a different observation period and must not replace them.
        '''),
        code('''
        historical = load_project("viglione-et-al-2013")
        display(input_inventory(historical))
        expanded = saved_case("viglione-et-al-2013", "Systematic (1951-2001) + Temporal Expansion")
        expanded.show("chronology")
        display(input_inventory(load_project("usgs-peak-download-example")))
        '''),
        markdown('''
        ## Authentic uncertain observations: Sinnemahoning MOVE.3
        The frozen `With Errors` input contains 79 exact observations and 25 uncertain observations.
        Each uncertain year carries its saved LogNormal measurement distribution; it is not converted to an exact point before analysis.
        The compact table below shows original distribution parameters directly from the project XML.
        '''),
        code('''
        measurement_project = load_project("sinnemahoning-move3-bayesian")
        display(input_inventory(measurement_project))
        uncertain = uncertain_observations(measurement_project, "Sinnemahoning - MOVE.3 - With Errors")
        display(uncertain.head())
        print(f"Saved uncertain observations: {len(uncertain)}")
        uncertain_case = saved_case("sinnemahoning-move3-bayesian", "Sinnemahoning - MOVE.3 - With Errors", table="Input Data")
        uncertain_case.show("chronology")
        display(case_provenance([uncertain_case]))
        ''')])

    write("02_distribution_fitting.ipynb","02 · Distribution fitting",
          "Use the Kamp at Zwettl inputs to compare candidate distributions before a focused Bayesian analysis.",[
        markdown('''
        ## Fifteen candidate distributions
        The four saved `Fit - ...` alternatives compare 1951–2001 and 1951–2005, each with and without temporal expansion.
        The candidate table keeps unsuccessful fits and their messages visible; plotted curves include only successful candidates whose app `ShowResults` setting is selected.
        AIC/BIC rank candidates only **within one saved fitting alternative**, where observations and likelihood treatment are the same.
        The four fitting alternatives use different periods or historical-information treatments, so their scores are not ranked across inputs.
        A favorable within-input score alone does not establish a plausible rare tail.
        '''),
        code('''
        PROJECT = "viglione-et-al-2013"
        names = ["Fit - Systematic (1951-2001)", "Fit - Systematic (1951-2005)",
                 "Fit - Systematic (1951-2001) + Temporal Expansion", "Fit - Systematic (1951-2005) + Temporal Expansion"]
        fits = [saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names]
        display(fits[0].settings)
        display(fits[0].candidates.sort_values("AIC", na_position="last"))
        fits[0].show("frequency")
        display(case_provenance(fits))
        '''),
        markdown('''
        ## Inspect fit in more than one view
        The density view emphasizes the body of the sample; the frequency view emphasizes the upper tail.
        P–P and Q–Q plots use the app's nonparametric plotting positions, preserving the historical input treatment.
        CDF, P–P, Q–Q and every candidate overlay are also available in the separate plot gallery.
        '''),
        code('''
        fits[0].show("pdf")
        fits[0].show("qq")
        display(pd.concat([fit.candidates.assign(Input=fit.data["name"]) for fit in fits], ignore_index=True)
                .sort_values(["Input", "AIC"]).groupby("Input", sort=False).head(3))
        '''),
        markdown("**Interpretation:** changing the observation period or adding historical bounds changes the evidence. Notebook 03 holds the GEV model family fixed to examine those information sources directly.")])

    write("03_stationary_information_expansion.ipynb","03 · Stationary univariate analysis and information expansion",
          "The app's Viglione project is a GEV case study for the Kamp at Zwettl, not an LP-III tutorial.",[
        markdown('''
        ## Systematic and temporal information
        Compare the record ending in 2001 with the record including the 2002 flood and ending in 2005.
        Temporal expansion adds three interval floods and one perception-threshold record to the 51 exact observations in the shorter input.
        Each curve below comes from its own saved analysis, with its own priors and sampler configuration.
        '''),
        code('''
        PROJECT = "viglione-et-al-2013"
        groups = json.loads((ROOT / "curriculum-cases.json").read_text(encoding="utf-8"))
        names = next(g["names"] for g in groups if g["notebook"] == "03")
        cases = {name: saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names}
        base = cases["MCMC - Systematic (1951-2001)"]
        display(base.settings)
        display(base.parameters)
        compare_frequency([cases[names[i]] for i in (0, 1, 2, 3)], "Systematic and temporal information")
        '''),
        markdown('''
        ## Causal information and combined expansion
        The causal alternatives add a Normal quantile prior at AEP 0.002 with mean 480 and standard deviation 80 m³/s.
        This is external information about a quantile, not an additional observed flood. Compare it with temporal expansion and their combination.
        The three-prior alternative instead uses AEPs 0.1, 0.01 and 0.001 with Normal means 100, 250 and 500, and standard deviations 20, 40 and 60 m³/s.
        '''),
        code('''
        compare_frequency([cases[names[i]] for i in (0, 2, 4, 6)], "Temporal, causal and combined expansion")
        combined = cases["MCMC - Systematic (1951-2001) + Temporal + Causal"]
        combined.show("frequency")
        display(cases[names[8]].frequency_table())
        '''),
        markdown('''
        ## Uncertainty and diagnostics
        Read credible intervals alongside the configured point estimate and posterior predictive curve.
        The separate gallery contains trace, posterior density, histogram, autocorrelation, mean log-likelihood, pair-density and influence views.
        Fresh-run receipts record numerical diagnostics; successful rendering is not evidence of sampler convergence.

        Fit metrics below are retained per case for provenance. They are not ranked across rows because the observation periods,
        historical-information treatments, or priors differ.

        Source context: [Viglione et al. (2013), *Flood frequency hydrology: 3. A Bayesian analysis*](https://doi.org/10.1029/2011WR010782).
        '''),
        code('''
        combined.show("diagnostic_trace")
        display(case_metrics(list(cases.values())))
        display(case_provenance(list(cases.values())))
        ''')])

    write("04_nonstationary_univariate.ipynb","04 · Nonstationary univariate analysis",
          "Follow the saved Brays Bayou LP-III alternatives to compare how location and scale change through time.",[
        markdown('''
        ## Seven structural alternatives
        Begin with the constant model, then compare linear, logistic and step changes. The three two-part names represent the saved combinations
        of location and scale links. These are alternative explanations of a changing flood record; adding flexibility does not establish the cause of a trend.
        '''),
        code('''
        PROJECT = "nsffa-brays-bayou-texas"
        names = next(g["names"] for g in json.loads((ROOT / "curriculum-cases.json").read_text()) if g["notebook"] == "04")
        cases = [saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names]
        project = load_project(PROJECT)
        display(input_inventory(project))
        display(cases[1].settings)
        display(trend_ownership(project, names[:-1]))
        display(case_metrics(cases[:-1], comparison_scope="Comparable fitted alternatives: same Brays Bayou response, observations, and likelihood."))
        display(case_metrics([cases[-1]]))
        display(case_provenance(cases))
        '''),
        markdown('''
        ## Chronology and conditional frequency
        The chronology view follows the app's configured nonstationary conditions and probability outputs.
        A frequency curve under changing parameters must be interpreted at its specified condition; it is not one timeless return-period curve for the whole record.
        '''),
        code('''
        cases[1].show("chronology")
        compare_frequency(cases[:4], "Constant, linear, logistic and step alternatives")
        '''),
        markdown('''
        ## Model averaging
        `Bayesian Model Average` is the app's DIC-weighted composite of the saved alternatives.
        Its uncertainty reflects those chosen models and weights; it does not include every possible future change in the watershed.
        The saved component curves are evaluated at parameter time index 2024. Zero-valued persisted composite fit metrics are placeholders and display as N/A.
        '''),
        code('''
        cases[-1].show("frequency")
        display(cases[-1].settings)
        display(composite_weights(project, "Bayesian Model Average"))
        display(pd.DataFrame({"Evaluation year": [int(cases[0].data["settings"]["Model.ParameterTimeIndex"])],
                              "Weight method": ["DIC"]}))
        ''')])

    write("05_bulletin_17c.ipynb","05 · Bulletin 17C examples 2 and 4",
          "Use the original Orestimba Creek and Arkansas River at Pueblo inputs to understand low floods, historical intervals and nonexceedance information.",[
        markdown('''
        ## Example 2: Orestimba Creek, California
        USGS station 11274500 has 82 annual peaks for 1932–2013 in this reference example, including 12 zeros.
        The saved app input flags 30 low floods at a 782 cfs threshold. Keep the original observations and flags together.
        The newer download in notebook 01 contains a longer record and is a different analysis.

        The official Bulletin 17C workflow uses EMA and MGBT. These notebooks show BestFit's GMM implementation and its saved MVN/BCB uncertainty alternatives.
        A GMM uncertainty ensemble is not a Bayesian posterior chain, and its intervals are confidence intervals.
        '''),
        code('''
        PROJECT = "bulletin-17c-examples"
        project = load_project(PROJECT)
        display(input_inventory(project).query("Input in ['Example #2 - Data', 'Example #4 - Data']"))
        names = ["Example #2", "Example #2 - BCB", "Example #4", "Example #4 - BCB"]
        cases = {name:saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names}
        display(pd.DataFrame([{
            "Alternative": name,
            "Uncertainty method": case.data["settings"]["UncertaintyMethod"],
            "Ensemble output length": int(case.data["settings"]["BayesianAnalysis.OutputLength"]),
            "Interval width": float(case.data["settings"]["BayesianAnalysis.CredibleIntervalWidth"]),
            "PRNG seed": int(case.data["settings"]["BayesianAnalysis.PRNGSeed"]),
            "Compatibility container": case.data["settings"]["BayesianAnalysis.Type"] + " (inactive sampler for B17C)",
        } for name, case in cases.items()]))
        display(case_provenance(list(cases.values())))
        cases["Example #2"].show("frequency")
        display(cases["Example #2"].parameters)
        display(cases["Example #2"].frequency_table())
        '''),
        markdown('''
        ## Example 4: Arkansas River at Pueblo, Colorado
        USGS station 07099500 combines 81 exact peaks, four event intervals and four perception-threshold records.
        The long nonexceedance information reaches back to 1165. It is represented by explicit windows, not invented annual values.
        The MVN alternative uses the saved linked-multivariate-normal setting; the BCB alternative retains its original bootstrap configuration.
        '''),
        code('''
        historical = saved_case(PROJECT, "Example #4 - Data", table="Input Data")
        historical.show("chronology")
        cases["Example #4"].show("frequency")
        display(cases["Example #4"].settings)
        '''),
        markdown('''
        ## Reference comparison and interpretation
        Appendix 10 describes Orestimba starting on printed page 111 and Pueblo on page 123.
        Tables 10-9 and 10-17 report 13,820 cfs for Orestimba and 39,800 cfs for Pueblo at 1% AEP. Compare the computed curve and the method-specific intervals separately;
        agreement after published rounding is a different check from uncertainty-interval agreement. The official examples use station skew.

        Reference: [England et al., Bulletin 17C, version 1.1 (May 2019), Appendix 10](https://pubs.usgs.gov/tm/04/b05/tm4b5.pdf).
        '''),
        code('''
        checks = json.loads((ROOT / "validation/source-checks.json").read_text(encoding="utf-8"))
        display(pd.DataFrame([{ "Station": entry["station"], "Table": entry["published_table"],
                               "Published EMA (cfs)": entry["published_ema_cfs"], "Saved GMM (cfs)": entry["saved_gmm_cfs"],
                               "Difference (%)": entry["difference_percent_of_published"] }
                              for entry in checks["bulletin_17c"].values()]))
        display(pd.concat([case.frequency_table((.01,)).assign(Alternative=name) for name,case in cases.items()], ignore_index=True))
        cases["Example #2"].show("diagnostic_influence")
        ''')])

    write("06_advanced_univariate.ipynb","06 · Advanced univariate vignettes",
          "Three distinct questions: threshold exceedances, latent populations, and combinations of flood-generating processes.",[
        markdown('''
        ## Point process: Big Bear precipitation
        The saved USC00040741 alternatives compare the peaks-over-threshold point process with an annual-maxima GEV and a seasonal point process.
        Retain the 1-inch threshold and 67-year exposure. POT exceedance probability and annual exceedance probability have different meanings;
        the app's frequency view includes its Langbein-converted annual plotting positions.
        Their fit metrics remain visible as per-case provenance but are not ranked across the POT and annual-maxima responses or likelihoods.
        '''),
        code('''
        pp_names = ["USC00040741 - Point Process", "USC00040741 - GEV", "USC00040741 - Seasonal Point Process"]
        pp = [saved_case("point-process-examples", name, run=RUN_ANALYSES) for name in pp_names]
        display(pp[0].settings)
        pp[0].show("frequency")
        display(case_metrics(pp))
        display(case_provenance(pp))
        '''),
        markdown('''
        ## Mixture: two populations and a point mass at zero
        The app uses controlled synthetic Normal mixtures to make component separation visible.
        The zero-inflated case adds a probability mass at zero; it is not created by replacing zeros with a small positive number.
        A mixture describes an observation arising from one latent population and its mixing probability.
        '''),
        code('''
        mixture = saved_case("mixture-distribution-examples", "Mixture Distribution - 2 Normals", run=RUN_ANALYSES)
        zero_inflated = saved_case("mixture-distribution-examples", "Mixture Distribution - 2 Normals - Zero-Inflated", run=RUN_ANALYSES)
        mixture.show("frequency")
        display(zero_inflated.parameters)
        display(case_provenance([mixture, zero_inflated]))
        '''),
        markdown('''
        ## Composite: competing flood types versus a mixture
        The mixed-population project uses synthetic snow-driven and rainfall-driven components with **LogNormal** margins.
        Competing risks combines processes whose annual maximum can win in the same year. A mixture combines selected populations with weights.
        Preserve each saved component's own input period: the full-period and sub-sample alternatives are intentional contrasts.
        '''),
        code('''
        competing = saved_case("mixed-population-examples", "Competing Flood Types", run=RUN_ANALYSES)
        composite_mixture = saved_case("mixed-population-examples", "Mixture of Flood Types", run=RUN_ANALYSES)
        competing.show("frequency")
        display(case_metrics([competing, composite_mixture]))
        display(case_provenance([competing, composite_mixture]))
        ''')])

    write("07_bivariate_analysis.ipynb","07 · Bivariate analysis",
          "Follow the app's six synthetic copula examples while keeping marginal behavior separate from dependence.",[
        markdown('''
        ## Margins and dependence
        Each example links two saved Normal marginal analyses with one of AMH, Clayton, Frank, Gumbel, Joe or Normal copulas.
        These are controlled teaching datasets, not observed river-gage case studies. Observed pairs are matched by index and exclude flagged low outliers.
        Each named copula case has its own simulated paired sample, so the metric rows are descriptive and are not a cross-case model ranking.
        '''),
        code('''
        PROJECT = "bivariate-distribution-examples"
        names = ["AMH Copula", "Clayton Copula", "Frank Copula", "Gumbel Copula", "Joe Copula", "Normal Copula"]
        cases = [saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names]
        display(cases[-1].settings)
        display(case_metrics(cases))
        display(case_provenance(cases))
        cases[-1].show("scatter_values")
        '''),
        markdown('''
        ## Value and marginal-probability coordinates
        In probability coordinates, observed values use their empirical plotting-position complements;
        simulated values use their fitted marginal CDFs. The simulation retains the app's original seed and output-length cap.
        Density contours use the app's log joint density grid; joint-exceedance contours instead show P(X>x, Y>y).
        '''),
        code('''
        cases[-1].show("density_cdf")
        cases[-1].show("joint_exceedance_values")
        '''),
        markdown("**Interpretation:** similar marginal fits can still imply different joint tails. Notebook 08 carries the joint model through a specified response function; a copula contour alone is not a response-frequency curve.")])

    write("08_coincident_frequency.ipynb","08 · Coincident frequency",
          "Start with a tractable sum, then follow the Waimea/Makaweli conditional stage-frequency example.",[
        markdown('''
        ## Sum of two correlated Normals
        For Z=X+Y, the analytic mean is μX+μY and the variance is σX²+σY²+2ρσXσY.
        The app provides synthetic cases at ρ=-0.5, 0 and +0.5. This control makes the effect of dependence visible before using a nonlinear response surface.
        The chart places response on a **linear** vertical axis and AEP on the horizontal probability axis; its uncertainty bounds are horizontal at fixed response.
        These are **Simulated Proof** cases. Their named univariate marginals and bivariate copula are upstream dependencies of each CFA result.
        '''),
        code('''
        PROJECT = "sum-two-normals"
        names = ["CFA - Rho = -0.5", "CFA - Rho = 0.0", "CFA - Rho = +0.5"]
        cases = [saved_case(PROJECT, name, run=RUN_ANALYSES) for name in names]
        compare_frequency(cases, "Sum of two Normals: dependence alternatives")
        display(cases[1].settings)
        cfa_project = load_project(PROJECT)
        cfa_rows = {row["Name"]: row for row in cfa_project["tables"]["<Coincident Frequency>"]["rows"]}
        display(pd.DataFrame([{
            "Analysis": name,
            "Response": row["InputData"],
            "Bivariate dependency": row["BivariateAnalysis"],
            "X ordinates": len(row["XValues"].split(",")),
            "Y ordinates": len(row["YValues"].split(",")),
            "Response cells": len(row["BivariateResponse"].split(",")),
            "Output bins": int(row["NumberOfBins"]),
        } for name in names for row in [cfa_rows[name]]]))
        checks = json.loads((ROOT / "validation/source-checks.json").read_text(encoding="utf-8"))
        display(pd.DataFrame(checks["sum_two_normals"])[["name", "fitted_rho", "response_is_x_plus_y",
                                                        "configured_number_of_bins", "max_absolute_aep_error"]])
        display(case_provenance(cases))
        '''),
        markdown('''
        ## Waimea and Makaweli
        Use `CFA - Normal - Conditional`, its saved conditional Normal copula, and its named marginal dependencies.
        The conditional Makaweli input represents values associated with Waimea events. Pairing two independently extracted annual maxima would define a different event population.
        The saved response surface and ordinates produce the stage-frequency result; they are retained rather than replaced by an invented sum-of-flows calculation.
        The selected CFA has no observed response input attached: its frozen `InputData` field is blank.
        '''),
        code('''
        waimea = saved_case("waimea-river-stage-frequency", "CFA - Normal - Conditional", run=RUN_ANALYSES)
        display(waimea.settings)
        waimea_project = load_project("waimea-river-stage-frequency")
        waimea_rows = waimea_project["tables"]["<Coincident Frequency>"]["rows"]
        waimea_row = next(row for row in waimea_rows if row["Name"] == "CFA - Normal - Conditional")
        waimea_x = [float(value) for value in waimea_row["XValues"].split(",")]
        waimea_y = [float(value) for value in waimea_row["YValues"].split(",")]
        waimea_response = [float(value) for value in waimea_row["BivariateResponse"].split(",")]
        assert len(waimea_response) == len(waimea_x) * len(waimea_y)
        display(pd.DataFrame([{
            "Bivariate analysis": waimea_row["BivariateAnalysis"],
            "Number of bins": int(waimea_row["NumberOfBins"]),
            "X ordinates": len(waimea_x),
            "Y ordinates": len(waimea_y),
            "Response cells": len(waimea_response),
            "Response range (ft)": f"{min(waimea_response):.2f}\u2013{max(waimea_response):.2f}",
            "Observed response input": waimea_row["InputData"] or "None attached",
        }]))
        waimea.show("frequency")
        display(input_inventory(waimea_project))
        display(case_provenance([waimea]))
        '''),
        markdown("**Interpretation:** the case names give nominal generating correlations; the table uses fitted correlations. The analytic check verifies every saved response cell is X+Y and compares the closed-form Gaussian survival with the saved app curve on its finite grid, reporting errors without changing grid settings. Distinguish marginal/dependence uncertainty from the specified response model; Waimea answers its conditional stage-response question.")])

    write("09_rating_curves.ipynb","09 · Rating curves",
          "Fit a stage-discharge relationship to paired field measurements, then inspect residuals and segment choices.",[
        markdown('''
        ## Mississippi River at New Madrid, Missouri
        The USGS 07024175 project stores 96 stage and 96 discharge observations in compressed fields.
        Every timestamp pairs exactly, from February 2017 through March 2026. The original USGS responses are retained in the frozen source.
        The app plots discharge horizontally and stage vertically; credible intervals are horizontal at a fixed stage.
        '''),
        code('''
        PROJECT = "usgs-07024175-mississippi-rating-curve"
        project = load_project(PROJECT)
        inventory = series_inventory(project)
        display(inventory)
        assert list(inventory["Records"]) == [96, 96]
        rating = saved_case(PROJECT, "USGS 07024175 Rating Curve", run=RUN_ANALYSES)
        display(rating.settings)
        display(rating.parameters)
        rating.show("curve")
        display(case_provenance([rating]))
        '''),
        markdown('''
        ## Residual behavior
        The residual scatter uses the fitted log10 discharge values and the app's residual definition.
        The histogram's Normal overlay uses the saved error-scale parameter; its Q–Q reference uses the residual sample mean and standard deviation.
        These views can reveal structure that an apparently smooth rating curve conceals.
        '''),
        code('''
        rating.show("residuals")
        rating.show("residual_qq")
        '''),
        markdown('''
        ## One, two and three segments
        The separate synthetic rating project contains 300 paired measurements for each segment configuration.
        These controlled examples illustrate piecewise behavior. They are not evidence that a more complex model is required at New Madrid.
        Their metrics describe separate simulated responses and are not ranked against one another or against the New Madrid fit.
        '''),
        code('''
        synthetic = [saved_case("synthetic-rating-curve-examples", f"{n} Segment Rating Curve", run=RUN_ANALYSES) for n in (1,2,3)]
        display(case_metrics(synthetic))
        display(synthetic[1].parameters)
        display(case_provenance(synthetic))
        ''')])

    write("10_classic_time_series.ipynb","10 · Classic time-series analyses",
          "Use Airline Passengers, Nile flow and Mauna Loa CO₂ to distinguish serial dependence, trend and seasonality.",[
        markdown('''
        ## Airline Passengers
        The source has 144 monthly observations for 1949–1960 and a saved ARIMA(1,1,1) configuration.
        Keep the original training, transformation, seasonal and prediction settings visible. The app shades training and held-out prediction regions separately, meeting at the last training observation.
        Airline trains on 120 of 144 values. `ForecastingTimeSteps=0`, so the final 24 values are a held-out prediction region rather than a future forecast.
        The full-settings rerun audit flagged Airline sampler convergence: the largest R-hat is about 1.26 and the smallest ESS about 52.
        Read this example as a model and diagnostic walkthrough; completion does not establish a reliable forecast. The [run-quality report](../validation/run-quality-summary.json) retains the parameter-level findings.
        '''),
        code('''
        PROJECT = "classic-time-series-examples"
        display(series_inventory(load_project(PROJECT)))
        airline = saved_case(PROJECT, "Airline Passengers - TSA", run=RUN_ANALYSES)
        display(airline.settings)
        airline.show("series")
        airline.show("residual_acf")
        '''),
        markdown('''
        ## Nile River flow
        The saved model is ARIMA(1,1,0). A source discrepancy matters here: the `.bestfit` project dates the 100 values to 1897–1996,
        while the source CSV dates the same values to 1871–1970. This walkthrough applies the documented 26-year **display-date correction** below.
        It keeps the original project, values, model and saved results unchanged and records the correction in each date plot's metadata.
        Nile uses saved ARIMA(1,1,0), trains on 80 of 100 values, and has `ForecastingTimeSteps=0`; its final 20 values are also held out, not future forecasts.
        The app-compatible residual plot stores dates as numeric OLE Automation dates on a linear axis despite its response-unit label; the display correction shifts those encoded dates consistently without changing source timestamps or the model.
        '''),
        code('''
        from bestfit_examples.presentation import corrected_nile_dates
        nile = corrected_nile_dates(saved_case(PROJECT, "Nile River Flows - TSA", run=RUN_ANALYSES))
        print(nile.data["dateCorrection"])
        display(pd.DataFrame([{
            "Analysis": case.data["name"],
            "ARIMA": label,
            "Training values": int(case.data["settings"]["Model.TrainingTimeSteps"]),
            "Total values": total,
            "Held-out prediction values": total - int(case.data["settings"]["Model.TrainingTimeSteps"]),
            "Future forecast steps": int(case.data["settings"]["ForecastingTimeSteps"]),
        } for case, label, total in [(airline, "(1,1,1)", 144), (nile, "(1,1,0)", 100)]]))
        nile.show("series")
        '''),
        markdown('''
        ## Mauna Loa CO₂
        This example uses a quadratic trend plus seasonality with no ARMA terms, rather than silently adding an autoregressive model.
        Examine the remaining residual dependence and the distinction between extrapolating the saved trend and establishing a physical forecast model.
        Airline passengers, Nile flow and atmospheric CO₂ are different responses with different likelihood scales; their fit metrics are retained per case and are not compared across rows.
        '''),
        code('''
        co2 = saved_case(PROJECT, "Mauna Loa - CO2", run=RUN_ANALYSES)
        display(co2.settings)
        co2.show("series")
        display(case_metrics([airline, nile, co2]))
        display(case_provenance([airline, nile, co2]))
        ''')])

    write("11_regression.ipynb","11 · Regression through the time-series model",
          "Follow the app's simple and multiple consumption regressions while preserving their training and forecast design.",[
        markdown('''
        ## Consumption and income
        The frozen project contains 187 quarterly observations from 1970 through mid-2016.
        `Simple Linear Regression` models Consumption using Income. It is stored as ARIMAX with AR, differencing and MA orders all zero.
        The saved training length is 149 steps, the default-training flag remains enabled, and the forecast horizon is 30 steps.
        '''),
        code('''
        PROJECT = "time-series-regression-example"
        display(series_inventory(load_project(PROJECT)))
        simple = saved_case(PROJECT, "Simple Linear Regression", run=RUN_ANALYSES)
        multiple = saved_case(PROJECT, "Multiple Linear Regression", run=RUN_ANALYSES)
        display(simple.settings)
        display(simple.parameters)
        simple.show("series")
        '''),
        markdown('''
        ## Multiple regression
        The second saved model adds Production, Savings and Unemployment to Income.
        Use the aligned covariates and saved transformations. Coefficients are conditional associations under this model;
        additional predictors do not by themselves establish causal effects or improve out-of-sample performance.
        Both analyses use the saved `BlockBootstrap` covariate-extension method for their 30-step future horizon; this preserves cross-covariate blocks instead of inventing known future covariates.
        '''),
        code('''
        display(multiple.settings)
        display(multiple.parameters)
        display(case_metrics([simple, multiple], comparison_scope="Comparable: same Consumption response, aligned observations, and ARIMAX likelihood."))
        display(case_provenance([simple, multiple]))
        multiple.show("residuals")
        multiple.show("residual_pacf")
        '''),
        markdown('''
        ## Read the fit and forecast together
        The app's training/prediction bands, residual distribution and serial-correlation diagnostics complement one another.
        A persistent residual pattern motivates a separate model question; this walkthrough preserves the original zero-AR/MA regression examples.
        All six time-series plots and shared sampler diagnostics are available through each saved case and the plot gallery.
        ''')])


if __name__=="__main__": main()
