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
regional.to_csv("examples/regional_analysis_site_records.csv", index=False)
final.to_csv("examples/regional_analysis_site_quantiles.csv", index=False)

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

# 1) Peak flow time series by site
for site, grp in regional.groupby("site"):
    grp = grp.sort_values("year")
    axes[0, 0].plot(
        grp["year"].to_numpy(dtype=float),
        grp["peak"].to_numpy(dtype=float),
        marker="o",
        linewidth=1.6,
        markersize=3.5,
        label=site,
    )
axes[0, 0].set_title("Annual Peak Flow by Site")
axes[0, 0].set_xlabel("Year")
axes[0, 0].set_ylabel("Peak Flow")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend(ncol=2, fontsize=8)

# 2) Scaled peak distributions by site
scaled_data = [
    regional.loc[regional["site"] == site, "scaled_peak"].to_numpy(dtype=float)
    for site in site_names
]
axes[0, 1].boxplot(scaled_data, tick_labels=site_names)
axes[0, 1].set_title("Scaled Peak Distribution by Site")
axes[0, 1].set_xlabel("Site")
axes[0, 1].set_ylabel("Scaled Peak")
axes[0, 1].grid(True, alpha=0.3, axis="y")

# 3) Site quantile curves
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
axes[1, 0].set_title("Regional Quantile Curves by Site")
axes[1, 0].set_xlabel("Return Period (years)")
axes[1, 0].set_ylabel("Estimated Peak Flow")
axes[1, 0].grid(True, alpha=0.3, which="both")
axes[1, 0].legend(ncol=2, fontsize=8)

# 4) Heatmap of site quantiles
heatmap_data = final.sort_values("site")[[f"q{t}" for t in return_periods]].to_numpy(dtype=float)
im = axes[1, 1].imshow(heatmap_data, aspect="auto", cmap="YlGnBu")
axes[1, 1].set_title("Site Quantile Heatmap")
axes[1, 1].set_xlabel("Return Period")
axes[1, 1].set_ylabel("Site")
axes[1, 1].set_xticks(np.arange(len(return_periods)))
axes[1, 1].set_xticklabels([str(t) for t in return_periods])
axes[1, 1].set_yticks(np.arange(len(site_names)))
axes[1, 1].set_yticklabels(final.sort_values("site")["site"].tolist())

for i in range(heatmap_data.shape[0]):
    for j in range(heatmap_data.shape[1]):
        axes[1, 1].text(
            j,
            i,
            f"{heatmap_data[i, j]:.0f}",
            ha="center",
            va="center",
            color="black",
            fontsize=8,
        )

fig.colorbar(im, ax=axes[1, 1], shrink=0.85, label="Estimated Peak Flow")

fig.suptitle(
    f"Regional Flood Analysis  |  Best Distribution: {regional_distribution.Type}  |  AIC = {float(regional_fit.AIC):.2f}",
    fontsize=14,
)
plt.tight_layout()
plt.show()