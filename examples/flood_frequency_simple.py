"""This script demonstrates a complete flood frequency analysis workflow using BestFit:
1. Generate synthetic annual peak flow data with a trend component
2. Detrend the data to create a stationary series for distribution fitting
3. Fit multiple probability distributions to the residuals
4. Compute return period quantiles using the fitted distributions
5. Generate diagnostic plots comparing empirical and fitted distributions
6. Export results to CSV files for further analysis

Outputs:
- flood_frequency_empirical_vs_model.csv: Empirical return periods vs. model predictions
- flood_frequency_return_period_table.csv: Return period quantile estimates
- matplotlib plots: Visual comparison of fits, CDFs, and flood frequency curves
"""

from __future__ import annotations
import pythonnet

pythonnet.load("coreclr")

import clr
import pandas as pd
from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt

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
# Use stationary synthetic data 
peaks = [max(500.0, 9200.0 + float(err)) for year, err in zip(years, noise)]
peaks = pd.DataFrame({"year": years, "peak_cfs": peaks})

# Build BestFit dataframe
df = DataFrame()
# Detrend the synthetic series before fitting stationary distributions.
# This is a critical preprocessing step: we remove any temporal trend (linear increase/decrease
# in mean) from the data before fitting, because BestFit's distributions assume stationarity.
# We fit a linear trend and use residuals for distribution fitting. When we
# compute quantiles and PDFs we will add the trend back at a reference year
# (most recent year) so returned design flows are on the original scale.
# This approach separates non-stationary behavior (trend) from stationary variability (residuals).
fit = np.polyfit(peaks["year"].to_numpy(dtype=float), peaks["peak_cfs"].to_numpy(dtype=float), 1)
peaks["trend"] = np.polyval(fit, peaks["year"].to_numpy(dtype=float))
peaks["residual"] = peaks["peak_cfs"] - peaks["trend"]

for row in peaks.itertuples(index=False):
    # Use residuals for the stationary distribution fit
    df.ExactSeries.Add(ExactData(int(row.year), float(row.residual)))
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

# Reference trend (add back to residual quantiles/PDFs). Use the most recent year.
trend_ref = float(np.polyval(fit, np.array([years[-1]], dtype=float))[0])

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
# Distances returned by the fitted distributions are residuals; add the
# reference trend to shift quantiles/PDFs back to original flow scale.
# The models were trained on residuals (detrended data), so we must transform
# their predictions back to the original scale by adding the trend value.
for name, dist in lookup.items():
    ret[name] = [float(dist.InverseCDF(float(min(max(p, 1e-6), 1 - 1e-6)))) + trend_ref for p in ret["F"]]

return_periods = [2, 5, 10, 25, 50, 100, 200]
rows = []
for t in return_periods:
    f = min(max(1.0 - 1.0 / t, 1e-6), 1.0 - 1e-6)
    row = {"return_period": t}
    for name, model in lookup.items():
        row[name] = float(model.InverseCDF(float(f))) + trend_ref
    rows.append(row)
qt = pd.DataFrame(rows)

# Save tables to .csv file
ret.to_csv("examples/output_tables/flood_frequency_empirical_vs_model.csv", index=False)
qt.to_csv("examples/output_tables/flood_frequency_return_period_table.csv", index=False)

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

# Use a centered trend (mean across sample years) for plotting overlays so the
# model PDF/CDF represents the average data scale when comparing to the pooled histogram.
trend_ref_plot = float(peaks["trend"].mean())

# 1) Histogram + fitted PDFs (evaluate PDFs on residual space, then shift)
# This plot compares the observed peak flow histogram to the fitted stationary
# model PDFs after shifting them back to the original flow scale.
residuals = peaks["residual"].to_numpy(dtype=float)
axes[0, 0].hist(
    peak_flows,
    bins=16,
    density=True,
    alpha=0.5,
    color="gray",
    edgecolor="black",
    label="Observed",
)

# For each fitted model, compute a safe residual grid (use distribution quantiles when possible),
# compute PDF on residual grid, then shift x by trend_ref to overlay on observed histogram.
for name, dist in models.items():
    try:
        qlow = float(dist.InverseCDF(0.001))
        qhigh = float(dist.InverseCDF(0.999))
        if not np.isfinite(qlow) or not np.isfinite(qhigh) or qlow == qhigh:
            raise ValueError
    except Exception:
        qlow = residuals.min() * 1.1
        qhigh = residuals.max() * 1.1

    x_res_grid = np.linspace(qlow, qhigh, 500)
    try:
        pdf_res = np.array([float(dist.PDF(float(xi))) for xi in x_res_grid])
    except Exception:
        pdf_res = np.zeros_like(x_res_grid)

    x_grid = x_res_grid + trend_ref_plot
    axes[0, 0].plot(x_grid, pdf_res, linewidth=2, label=name.upper())

axes[0, 0].set_title("Observed Data and Fitted PDFs (models shifted by trend)")
axes[0, 0].set_xlabel("Peak Flow (cfs)")
axes[0, 0].set_ylabel("Density")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# 2) Empirical CDF + fitted CDFs (evaluate CDFs on residuals then shift x)
# This plot shows the empirical CDF of the observed flows and the fitted model
# CDFs using the same shift applied to the PDFs, so the distribution fit can be
# assessed visually on the original flow scale.
sorted_flows = np.sort(peak_flows)
ecdf = np.arange(1, len(sorted_flows) + 1) / len(sorted_flows)
axes[0, 1].step(sorted_flows, ecdf, where="post", color="black", linewidth=2, label="ECDF")
for name, dist in models.items():
    # evaluate model CDF at (observed - centered trend), because models were fit to residuals
    res_points = sorted_flows - trend_ref_plot
    try:
        cdf_vals = np.array([float(dist.CDF(float(xi))) for xi in res_points])
    except Exception:
        cdf_vals = np.zeros_like(res_points)
    axes[0, 1].plot(sorted_flows, cdf_vals, linewidth=2, label=name.upper())

axes[0, 1].set_title("Empirical vs Fitted CDFs (models shifted by trend)")
axes[0, 1].set_xlabel("Peak Flow (cfs)")
axes[0, 1].set_ylabel("CDF")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# 3) Flood frequency curves
# This plot compares empirical exceedance-based return levels to the model-derived
# return-period quantiles for each fitted distribution.
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

plt.tight_layout()
plt.show()