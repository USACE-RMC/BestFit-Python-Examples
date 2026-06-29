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

from RMC.BestFit.Estimation import MaximumLikelihood, OptimizationMethod
from RMC.BestFit.Models import RatingCurve


true_params = convert_to_dotnet_array(
    [
        0.30,  # zero-flow stage
        1.25,  # log10(alpha)
        1.70,  # exponent
        0.08,  # log-space error
    ]
)

generator = RatingCurve()
generator.SetParameterValues(true_params)
synthetic = generator.GenerateSyntheticData(sampleSize=70, minStage=0.6, maxStage=5.0, seed=5)
stage_ts = synthetic.Item1
discharge_ts = synthetic.Item2

model = RatingCurve(stage_ts, discharge_ts, numberOfSegments=1)
mle = MaximumLikelihood(model, OptimizationMethod.MultilevelSingleLinkage)
mle.Estimate()

if not mle.IsEstimated:
    raise RuntimeError("BestFit MaximumLikelihood did not converge for the rating curve.")

fit_params = mle.BestParameterSet.Values
model.SetParameterValues(fit_params)

stage = [float(point.Value) for point in stage_ts]
discharge_obs = [float(point.Value) for point in discharge_ts]
discharge_fit = [float(model.Predict(fit_params, h)) for h in stage]
residual = [obs - fit for obs, fit in zip(discharge_obs, discharge_fit)]
pct_error = [100.0 * err / max(obs, 1e-9) for err, obs in zip(residual, discharge_obs)]
residual_stats = list(model.Residuals(fit_params))

df = pd.DataFrame(
    {
        "stage": stage,
        "discharge_obs": discharge_obs,
        "discharge_fit": discharge_fit,
        "residual": residual,
        "pct_error": pct_error,
    }
)

rmse = float((sum(float(r) * float(r) for r in residual_stats) / len(residual_stats)) ** 0.5)
mae = float(sum(abs(r) for r in residual) / len(residual))

table = model.GenerateRatingTable(parameters=fit_params, minStage=0.6, maxStage=5.0, numPoints=45)
rating_table = pd.DataFrame(
    {
        "stage": [float(table[i, 0]) for i in range(table.GetLength(0))],
        "discharge_fit": [float(table[i, 1]) for i in range(table.GetLength(0))],
    }
)

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(results_dir / "rating_curve_observed_vs_fit.csv", index=False)
rating_table.to_csv(results_dir / "rating_curve_table.csv", index=False)

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
print("\nWrote:", results_dir / "rating_curve_observed_vs_fit.csv")
print("Wrote:", results_dir / "rating_curve_table.csv")
