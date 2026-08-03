"""This script demonstrates a complete rating curve (stage-discharge) analysis workflow:
1. Generate synthetic stage-discharge measurement data
2. Estimate rating curve parameters using Maximum Likelihood Estimation (MLE)
3. Generate a rating table for a range of stage values
4. Create diagnostic plots:
   - Observed vs. fitted rating curve
   - Scatter plot with 1:1 line to assess fit quality
   - Residuals vs. stage to check for systematic bias
   - Percent error distribution histogram
5. Export results to CSV files for report generation

A rating curve is a mathematical relationship between stream stage (water level) and 
discharge (flow rate). This is essential for converting stage measurements into flow 
estimates at ungaged sites or for extending discharge records.

Outputs:
- rating_curve_observed_vs_fit.csv: Point-by-point comparison of observations and fits
- rating_curve_table.csv: Discharge estimates for a range of stage values
- matplotlib plots: Diagnostic visualizations of model performance
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

from RMC.BestFit.Estimation import MaximumLikelihood, OptimizationMethod
from RMC.BestFit.Models import RatingCurve


true_params = convert_to_dotnet_array([
        0.30,  # zero-flow stage: the stage at which discharge is zero (y-intercept)
        1.25,  # log10(alpha): log-scale discharge coefficient parameter
        1.70,  # exponent: power law exponent determining rating curve shape
        0.08,  # log-space error: standard deviation of measurement error in log space
    ])

# Use the rating curve class to generate synthetic data
# The RatingCurve model implements the standard power law form: Q = alpha * (H - H0)^n
# where Q is discharge, H is stage, H0 is the zero-flow stage, alpha is a coefficient,
# and n is the exponent. Measurement error is added in log-space to be realistic.
generator = RatingCurve()
generator.SetParameterValues(true_params)
synthetic = generator.GenerateSyntheticData(sampleSize=70, minStage=0.6, maxStage=5.0, seed=5)
stage_ts = synthetic.Item1
discharge_ts = synthetic.Item2

# Estimating parameters using MLE
# Maximum Likelihood Estimation (MLE) finds parameter values that maximize the probability
# of observing the data given the model. We use MultilevelSingleLinkage optimization to
# handle the non-convex parameter space and avoid local minima.
model = RatingCurve(stage_ts, discharge_ts, numberOfSegments=1)
mle = MaximumLikelihood(model, OptimizationMethod.MultilevelSingleLinkage)
mle.Estimate()

if not mle.IsEstimated:
    raise RuntimeError("BestFit MaximumLikelihood did not converge for the rating curve.")

fit_params = mle.BestParameterSet.Values
model.SetParameterValues(fit_params)

# Pull values out of model
stage = [float(point.Value) for point in stage_ts]
discharge_obs = [float(point.Value) for point in discharge_ts]
discharge_fit = [float(model.Predict(fit_params, h)) for h in stage]
residual = [obs - fit for obs, fit in zip(discharge_obs, discharge_fit)]
pct_error = [100.0 * err / max(obs, 1e-9) for err, obs in zip(residual, discharge_obs)]
residual_stats = list(model.Residuals(fit_params))

df = pd.DataFrame({
        "stage": stage,
        "discharge_obs": discharge_obs,
        "discharge_fit": discharge_fit,
        "residual": residual,
        "pct_error": pct_error,
    })

rmse = float((sum(float(r) * float(r) for r in residual_stats) / len(residual_stats)) ** 0.5)
mae = float(sum(abs(r) for r in residual) / len(residual))

# Creating rating table
table = model.GenerateRatingTable(parameters=fit_params, minStage=0.6, maxStage=5.0, numPoints=45)
rating_table = pd.DataFrame({
        "stage": [float(table[i, 0]) for i in range(table.GetLength(0))],
        "discharge_fit": [float(table[i, 1]) for i in range(table.GetLength(0))],
    })

# Print results to a csv file
df.to_csv("examples/output_tables/rating_curve_observed_vs_fit.csv", index=False)
rating_table.to_csv("examples/output_tables/rating_curve_table.csv", index=False)

print("Rating Curve Demo")
print("BestFit MLE parameters")
for parameter in model.Parameters:
    print(f"- {parameter.Name}: {parameter.Value:.4f}")
print(f"Log-likelihood: {mle.BestParameterSet.Fitness:.3f}")
print(f"RMSE: {rmse:.3f}")
print(f"MAE: {mae:.3f}")
print("\nFirst 10 observed rows")
print(df.head(10).round(3).to_string(index=False))
print("\nRating table preview")
print(rating_table.head(10).round(3).to_string(index=False))

stage_arr = np.asarray(stage, dtype=float)
discharge_obs_arr = np.asarray(discharge_obs, dtype=float)
discharge_fit_arr = np.asarray(discharge_fit, dtype=float)
residual_arr = np.asarray(residual, dtype=float)
pct_error_arr = np.asarray(pct_error, dtype=float)

# Smooth fitted curve from rating table
stage_curve = rating_table["stage"].to_numpy(dtype=float)
discharge_curve = rating_table["discharge_fit"].to_numpy(dtype=float)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1) Observed vs fitted rating curve
# Compare observed stage-discharge measurements to the fitted rating curve.
sort_idx = np.argsort(stage_arr)
axes[0, 0].scatter(
    stage_arr,
    discharge_obs_arr,
    s=35,
    alpha=0.75,
    color="black",
    label="Observed",
)
axes[0, 0].plot(
    stage_curve,
    discharge_curve,
    color="steelblue",
    linewidth=2.5,
    label="Fitted rating curve",
)
axes[0, 0].set_title("Observed Data and Fitted Rating Curve")
axes[0, 0].set_xlabel("Stage")
axes[0, 0].set_ylabel("Discharge")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# 2) Observed vs fitted scatter with 1:1 line
# This comparison shows whether the fitted discharge values are close to the
# observed values across the data range. Points on the 1:1 line indicate perfect fit.
xy_min = min(discharge_obs_arr.min(), discharge_fit_arr.min())
xy_max = max(discharge_obs_arr.max(), discharge_fit_arr.max())
axes[0, 1].scatter(
    discharge_obs_arr,
    discharge_fit_arr,
    s=35,
    alpha=0.75,
    color="darkorange",
    edgecolor="black",
    label="Points",
)
axes[0, 1].plot(
    [xy_min, xy_max],
    [xy_min, xy_max],
    linestyle="--",
    color="black",
    linewidth=1.5,
    label="1:1 line",
)
axes[0, 1].set_title("Observed vs Fitted Discharge")
axes[0, 1].set_xlabel("Observed Discharge")
axes[0, 1].set_ylabel("Fitted Discharge")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# 3) Residuals vs stage
# Plot the model residuals against stage to look for systematic bias or heteroscedasticity.
axes[1, 0].axhline(0.0, color="black", linestyle="--", linewidth=1.2)
axes[1, 0].scatter(
    stage_arr,
    residual_arr,
    s=35,
    alpha=0.75,
    color="seagreen",
    edgecolor="black",
)
axes[1, 0].set_title("Residuals vs Stage")
axes[1, 0].set_xlabel("Stage")
axes[1, 0].set_ylabel("Residual (Observed - Fitted)")
axes[1, 0].grid(True, alpha=0.3)

# 4) Percent error histogram
# Summarize the distribution of relative errors between observed and fitted
# discharge values.
axes[1, 1].hist(
    pct_error_arr,
    bins=14,
    color="mediumpurple",
    edgecolor="black",
    alpha=0.75,
)
axes[1, 1].axvline(0.0, color="black", linestyle="--", linewidth=1.2)
axes[1, 1].set_title("Percent Error Distribution")
axes[1, 1].set_xlabel("Percent Error (%)")
axes[1, 1].set_ylabel("Count")
axes[1, 1].grid(True, alpha=0.3, axis="y")

fig.suptitle(
    f"Rating Curve Fit Diagnostics  |  RMSE = {rmse:.3f}, MAE = {mae:.3f}",
    fontsize=14,
)
plt.tight_layout()
plt.show()