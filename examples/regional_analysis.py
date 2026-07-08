"""Regional analysis using site dependent AIC values. This file produces a pop up window of graphs
while tables are outputted via the terminal and written to csv files found in outputs/tables/"""

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

# Build synthetic site data
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
regional = pd.DataFrame(records, columns=["site", "year", "peak", "index_flood"])

regional["scaled_peak"] = regional["peak"] / regional["index_flood"]

# Create BestFit DataFrame
df = DataFrame()
for i, value in enumerate(regional["scaled_peak"], start=1):
     df.ExactSeries.Add(ExactData(i, float(value)))
df.PlottingParameter = 0.0
df.CalculatePlottingPositions()

# Run fitting analysis
analysis = FittingAnalysis(df)
analysis.RunAsync().Wait()

# Sort by best AIC
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
    std_scaled=("scaled_peak", "std"),)

site_summary["cv_scaled"] = site_summary["std_scaled"] / site_summary["mean_scaled"]
final = at_site.merge(site_summary, on="site", how="left")

# Write results to .csv file
regional.to_csv("examples/output_tables/regional_analysis_site_records.csv", index=False)
final.to_csv("examples/output_tables/regional_analysis_site_quantiles.csv", index=False)

print("Regional Analysis Demo")
print("BestFit regional scaled distribution")
print(f"- type={regional_distribution.Type}")
print(f"- AIC={float(regional_fit.AIC):.2f}")
for t in return_periods:
    print(f"- scaled q{t}={scaled_q[t]:.4f}")

print("\nSite quantiles")
print(final.round(2).to_string(index=False))

# Add graphs here
import numpy as np
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
site_order = sorted(site_names)
colors = plt.cm.tab10(np.linspace(0, 1, len(site_order)))

# 1) Scaled peak empirical CDFs by site with the regional fitted CDF
# Compare each site-specific scaled empirical CDF to the pooled regional CDF fit.
for site, color in zip(site_order, colors):
    site_data = np.sort(
        regional.loc[regional["site"] == site, "scaled_peak"].to_numpy(dtype=float)
    )
    ecdf = np.arange(1, len(site_data) + 1) / (len(site_data) + 1)
    axes[0, 0].step(
        site_data,
        ecdf,
        where="post",
        color=color,
        alpha=0.75,
        linewidth=1.5,
        label=site,
    )

pooled_data = np.sort(regional["scaled_peak"].to_numpy(dtype=float))
pooled_ecdf = np.arange(1, len(pooled_data) + 1) / (len(pooled_data) + 1)
axes[0, 0].step(
    pooled_data,
    pooled_ecdf,
    where="post",
    color="black",
    linewidth=2,
    label="Pooled ECDF",
)

x_cdf = np.linspace(pooled_data.min(), pooled_data.max(), 300)
cdf_fit = np.array([float(regional_distribution.CDF(float(x))) for x in x_cdf])
axes[0, 0].plot(
    x_cdf,
    cdf_fit,
    color="red",
    linewidth=2,
    label="Regional fitted CDF",
)

axes[0, 0].set_title("Scaled Peak Empirical CDFs by Site with Regional Fit")
axes[0, 0].set_xlabel("Scaled Peak")
axes[0, 0].set_ylabel("Cumulative Probability")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend(fontsize=8, ncol=2)

# 2) Boxplots of scaled peaks with regional quantile lines
# Show the spread of scaled peak values at each site and overlay the regional
# quantile estimates for reference.
scaled_data = [
    regional.loc[regional["site"] == site, "scaled_peak"].to_numpy(dtype=float)
    for site in site_order
]
axes[0, 1].boxplot(scaled_data, showmeans=True)
axes[0, 1].set_xticklabels(site_order)
axes[0, 1].set_title("Site Scaled Peak Distributions")
axes[0, 1].set_xlabel("Site")
axes[0, 1].set_ylabel("Scaled Peak")
axes[0, 1].grid(True, alpha=0.3, axis="y")

regional_quantiles = {
    t: float(regional_distribution.InverseCDF(float(min(max(1.0 - 1.0 / t, 1e-6), 1.0 - 1e-6))))
    for t in return_periods
}
for t, q in regional_quantiles.items():
    axes[0, 1].axhline(q, linestyle="--", linewidth=1.2, label=f"Regional q{t}")
axes[0, 1].legend(fontsize=8, ncol=2)

# 3) Site return-period quantile curves
# Plot design flow estimates for each site at the selected return periods.
for _, row in final.sort_values("site").iterrows():
    x = np.array(return_periods, dtype=float)
    y = np.array([row[f"q{t}"] for t in return_periods], dtype=float)
    axes[1, 0].plot(
        x,
        y,
        marker="o",
        linewidth=2,
        label=row["site"],
    )
axes[1, 0].set_xscale("log")
axes[1, 0].set_title("Site Return-Period Quantile Curves")
axes[1, 0].set_xlabel("Return Period (years)")
axes[1, 0].set_ylabel("Estimated Peak Flow")
axes[1, 0].grid(True, alpha=0.3, which="both")
axes[1, 0].legend(ncol=2, fontsize=8)

# 4) Site mean scaled peak vs. CV
# Visualize site-level variability by comparing the mean scaled peak to the
# coefficient of variation for each site.
axes[1, 1].scatter(
    final["mean_scaled"].to_numpy(dtype=float),
    final["cv_scaled"].to_numpy(dtype=float),
    s=80,
    color="tab:blue",
    edgecolor="black",
)
for _, row in final.sort_values("site").iterrows():
    axes[1, 1].text(
        row["mean_scaled"] + 0.002,
        row["cv_scaled"] + 0.002,
        row["site"],
        fontsize=8,
    )
axes[1, 1].set_title("Site Mean Scaled Peak vs. CV")
axes[1, 1].set_xlabel("Mean Scaled Peak")
axes[1, 1].set_ylabel("Coefficient of Variation")
axes[1, 1].grid(True, alpha=0.3)

fig.suptitle(
    f"Regional Flood Analysis  |  Best Distribution: {regional_distribution.Type}  |  AIC = {float(regional_fit.AIC):.2f}",
    fontsize=14,
)
plt.tight_layout()
plt.show()