from __future__ import annotations

import pythonnet

pythonnet.load("coreclr")

import clr
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "notebooks"))
from helper_functions import resolve_bestfit_dll, resolve_numerics_dll

clr.AddReference(str(resolve_numerics_dll()))
clr.AddReference(str(resolve_bestfit_dll()))

from RMC.BestFit import ExactData
from RMC.BestFit.Analyses import FittingAnalysis
from RMC.BestFit.Models import DataFrame
from Numerics.Distributions import Normal


def build_site_records() -> pd.DataFrame:
    site_names = [f"S{i:02d}" for i in range(1, 9)]
    records = []
    for site_index, site in enumerate(site_names, start=1):
        index_flood = 7000.0 + 650.0 * site_index
        noise = list(Normal(0.0, 0.18).GenerateRandomValues(35, 250 + site_index))
        for offset, z in enumerate(noise):
            year = 1990 + offset
            trend = 1.0 + 0.003 * offset
            peak = max(500.0, index_flood * trend * (1.0 + float(z)))
            records.append((site, year, peak, index_flood))
    return pd.DataFrame(records, columns=["site", "year", "peak", "index_flood"])


def bestfit_dataframe(values: pd.Series) -> DataFrame:
    df = DataFrame()
    for i, value in enumerate(values, start=1):
        df.ExactSeries.Add(ExactData(i, float(value)))
    df.PlottingParameter = 0.0
    df.CalculatePlottingPositions()
    return df


regional = build_site_records()
regional["scaled_peak"] = regional["peak"] / regional["index_flood"]

scaled_df = bestfit_dataframe(regional["scaled_peak"])
analysis = FittingAnalysis(scaled_df)
analysis.RunAsync().Wait()

regional_fit = sorted(analysis.FittedDistributions, key=lambda fd: fd.AIC)[0]
regional_distribution = regional_fit.Distribution

return_periods = [10, 25, 50, 100]
scaled_q = {}
for t in return_periods:
    f = 1.0 - 1.0 / t
    scaled_q[t] = float(regional_distribution.InverseCDF(float(f)))

at_site = regional.groupby("site", as_index=False)["index_flood"].mean()
for t in return_periods:
    at_site[f"q{t}"] = at_site["index_flood"] * scaled_q[t]

site_summary = regional.groupby("site", as_index=False).agg(
    mean_peak=("peak", "mean"),
    std_peak=("peak", "std"),
    mean_scaled=("scaled_peak", "mean"),
    std_scaled=("scaled_peak", "std"),
)
site_summary["cv_scaled"] = site_summary["std_scaled"] / site_summary["mean_scaled"]
final = at_site.merge(site_summary, on="site", how="left")

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
regional.to_csv(results_dir / "regional_analysis_site_records.csv", index=False)
final.to_csv(results_dir / "regional_analysis_site_quantiles.csv", index=False)

print("Regional Analysis Demo")
print("BestFit regional scaled distribution")
print(f"- type={regional_distribution.Type}")
print(f"- AIC={float(regional_fit.AIC):.2f}")
for t in return_periods:
    print(f"- scaled q{t}={scaled_q[t]:.4f}")

print("\nSite quantiles")
print(final.round(2).to_string(index=False))
print("\nWrote:", results_dir / "regional_analysis_site_records.csv")
print("Wrote:", results_dir / "regional_analysis_site_quantiles.csv")
