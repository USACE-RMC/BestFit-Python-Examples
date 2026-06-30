"""Simple flood frequency demo. One this file runs you will have a popup window of graphs
and tables will be outputed to the terminal and written to csv files under outputs/tables/"""

from __future__ import annotations
import pythonnet

pythonnet.load("coreclr")

import clr
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "notebooks"))
from helper_functions import convert_to_dotnet_array, resolve_bestfit_dll, resolve_numerics_dll

clr.AddReference(str(resolve_numerics_dll()))
clr.AddReference(str(resolve_bestfit_dll()))

from RMC.BestFit import ExactData
from RMC.BestFit.Analyses import FittingAnalysis
from RMC.BestFit.Models import DataFrame
from Numerics.Distributions import Normal

# Generate synthetic data
years = list(range(1980, 1980 + 50))
noise = list(Normal(0.0, 850.0).GenerateRandomValues(50, 123))
peaks = [max(500.0, 9200.0 + 35.0 * (year - years[0]) + float(err)) for year, err in zip(years, noise)]
peaks = pd.DataFrame({"year": years, "peak_cfs": peaks})

# Build BestFit dataframe
df = DataFrame()
for row in peaks.itertuples(index=False):
    df.ExactSeries.Add(ExactData(int(row.year), float(row.peak_cfs)))
df.PlottingParameter = 0.0
df.CalculatePlottingPositions()

# Fitting analysis
analysis = FittingAnalysis(df)
analysis.RunAsync().Wait()

# Pull out GEV and Gumbel distributions
lookup = {}
for fitted in analysis.FittedDistributions:
    key = str(fitted.Distribution.Type).lower()
    if "generalizedextremevalue" in key or "generalized extreme value" in key:
            lookup["gev"] = fitted.Distribution
    if "gumbel" in key:
            lookup["gumbel"] = fitted.Distribution
best = sorted(analysis.FittedDistributions, key=lambda fd: fd.AIC)[0]
lookup.setdefault("best_aic", best.Distribution)

# Find empirical return period
values = [float(v) for v in peaks["peak_cfs"].tolist()]
ranked = sorted(((float(value), i) for i, value in enumerate(values)), reverse=True)
n = len(ranked)

# Organize into a table
rows = []
for rank, (value, original_index) in enumerate(ranked, start=1):
    p_exceed = rank / (n + 1.0)
    rows.append( {
                "original_index": original_index,
                "value": value,
                "rank": rank,
                "p_exceed": p_exceed,
                "return_period": 1.0 / p_exceed,
            })
ret = pd.DataFrame(rows).sort_values("return_period")


ret["F"] = 1.0 - 1.0 / ret["return_period"]
for name, dist in lookup.items():
    ret[name] = [float(dist.InverseCDF(float(min(max(p, 1e-6), 1 - 1e-6)))) for p in ret["F"]]

return_periods = [2, 5, 10, 25, 50, 100, 200]
rows = []
for t in return_periods:
    f = min(max(1.0 - 1.0 / t, 1e-6), 1.0 - 1e-6)
    row = {"return_period": t}
    for name, model in lookup.items():
        row[name] = float(model.InverseCDF(float(f)))
    rows.append(row)
qt = pd.DataFrame(rows)

# Save tables to .csv file
results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
ret.to_csv(results_dir / "flood_frequency_empirical_vs_model.csv", index=False)
qt.to_csv(results_dir / "flood_frequency_return_period_table.csv", index=False)

# Sort by best AIC
best = sorted(analysis.FittedDistributions, key=lambda fd: fd.AIC)[0]
print("Flood Frequency Demo")
print("- Sample size:", len(values))
print("- BestFit best distribution:", best.Distribution.Type)
print("- BestFit best AIC:", round(float(best.AIC), 2))
print("\nTop empirical return periods")
cols = ["return_period", "value"] + list(lookup.keys())
print(ret[cols].tail(10).round(2).to_string(index=False))
print("\nReturn-period quantile table")
print(qt.round(2).to_string(index=False))
print("\nWrote:", results_dir / "flood_frequency_empirical_vs_model.csv")
print("Wrote:", results_dir / "flood_frequency_return_period_table.csv")

## Add graphs here
import numpy as np
import matplotlib.pyplot as plt

peak_flows = peaks["peak_cfs"].to_numpy(dtype=float)
models = {name: dist for name, dist in lookup.items()}

fit_rows = []
for fitted in analysis.FittedDistributions:
    fit_rows.append(
        {
            "Model": str(fitted.Distribution.Type),
            "AIC": float(fitted.AIC),
            #"KS Statistic": float(fitted.KolmogorovSmirnov.Statistic),
        }
    )
fit_df = pd.DataFrame(fit_rows).sort_values("AIC")

quantile_rows = []
for _, row in qt.iterrows():
    for name in models.keys():
        if name in row.index:
            quantile_rows.append(
                {
                    "Model": name.upper(),
                    "ReturnPeriod": float(row["return_period"]),
                    "DesignFlow": float(row[name]),
                }
            )
quantile_df = pd.DataFrame(quantile_rows)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1) Histogram + fitted PDFs
x_pdf = np.linspace(peak_flows.min() * 0.8, peak_flows.max() * 1.1, 500)
axes[0, 0].hist(
    peak_flows,
    bins=16,
    density=True,
    alpha=0.5,
    color="gray",
    edgecolor="black",
    label="Observed",
)
for name, dist in models.items():
    axes[0, 0].plot(
        x_pdf,
        [float(dist.PDF(float(xi))) for xi in x_pdf],
        linewidth=2,
        label=name.upper(),
    )
axes[0, 0].set_title("Observed Data and Fitted PDFs")
axes[0, 0].set_xlabel("Peak Flow (cfs)")
axes[0, 0].set_ylabel("Density")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# 2) Empirical CDF + fitted CDFs
sorted_flows = np.sort(peak_flows)
ecdf = np.arange(1, len(sorted_flows) + 1) / len(sorted_flows)
axes[0, 1].step(sorted_flows, ecdf, where="post", color="black", linewidth=2, label="ECDF")
for name, dist in models.items():
    axes[0, 1].plot(
        sorted_flows,
        [float(dist.CDF(float(xi))) for xi in sorted_flows],
        linewidth=2,
        label=name.upper(),
    )
axes[0, 1].set_title("Empirical vs Fitted CDFs")
axes[0, 1].set_xlabel("Peak Flow (cfs)")
axes[0, 1].set_ylabel("CDF")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# 3) Flood frequency curves
axes[1, 0].scatter(
    ret["return_period"],
    ret["value"],
    color="black",
    s=30,
    label="Empirical",
    zorder=3,
)
for name, grp in quantile_df.groupby("Model"):
    axes[1, 0].plot(
        grp["ReturnPeriod"].values,
        grp["DesignFlow"].values,
        marker="o",
        linewidth=2,
        label=name,
    )
axes[1, 0].set_xscale("log")
axes[1, 0].set_title("Flood Frequency Curves")
axes[1, 0].set_xlabel("Return Period (years)")
axes[1, 0].set_ylabel("Design Flow (cfs)")
axes[1, 0].grid(True, alpha=0.3, which="both")
axes[1, 0].legend()

# 4) KS statistic bar chart
# top_fit_df = fit_df.head(3).copy()
# axes[1, 1].bar(top_fit_df["Model"], top_fit_df["KS Statistic"], color=["steelblue", "coral", "seagreen"][:len(top_fit_df)])
# axes[1, 1].set_title("Goodness of Fit (KS Statistic)")
# axes[1, 1].set_ylabel("KS Statistic")
# axes[1, 1].grid(True, alpha=0.3, axis="y")
# axes[1, 1].tick_params(axis="x", rotation=15)

plt.tight_layout()
plt.show()