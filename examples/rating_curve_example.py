from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(5)
stage = np.linspace(0.6, 5.0, 70)
q_true = np.where(stage < 2.2, 18 * (stage - 0.3) ** 1.7, 65 * (stage - 0.3) ** 1.15)
q_obs = np.maximum(0.1, q_true * (1 + rng.normal(0, 0.08, size=stage.size)))

break_stage = 2.2
mask = stage < break_stage

# Segment fits in log-log space
c1 = np.polyfit(np.log(stage[mask] - 0.3), np.log(q_obs[mask]), 1)
c2 = np.polyfit(np.log(stage[~mask] - 0.3), np.log(q_obs[~mask]), 1)

b1, a1 = c1[0], np.exp(c1[1])
b2, a2 = c2[0], np.exp(c2[1])

df = pd.DataFrame({"stage": stage, "discharge_obs": q_obs})
df["discharge_fit"] = np.where(stage < break_stage, a1 * (stage - 0.3) ** b1, a2 * (stage - 0.3) ** b2)
df["residual"] = df["discharge_obs"] - df["discharge_fit"]
df["pct_error"] = 100.0 * df["residual"] / np.maximum(df["discharge_obs"], 1e-9)

rmse = float(np.sqrt(np.mean(df["residual"] ** 2)))
mae = float(np.mean(np.abs(df["residual"])))

# Build a rating table at fixed stage increments
stage_table = np.arange(0.6, 5.01, 0.1)
rating_table = pd.DataFrame({"stage": stage_table})
rating_table["discharge_fit"] = np.where(
    rating_table["stage"] < break_stage,
    a1 * (rating_table["stage"] - 0.3) ** b1,
    a2 * (rating_table["stage"] - 0.3) ** b2,
)

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
df.to_csv(results_dir / "rating_curve_observed_vs_fit.csv", index=False)
rating_table.to_csv(results_dir / "rating_curve_table.csv", index=False)

print("Rating Curve Demo")
print(f"Segment 1: Q={a1:.3f}(h-0.3)^{b1:.3f}")
print(f"Segment 2: Q={a2:.3f}(h-0.3)^{b2:.3f}")
print(f"Break stage: {break_stage:.2f}")
print(f"RMSE: {rmse:.3f}")
print(f"MAE: {mae:.3f}")
print("\nFirst 10 observed rows")
print(df.head(10).round(3).to_string(index=False))
print("\nRating table preview")
print(rating_table.head(10).round(3).to_string(index=False))
print("\nWrote:", results_dir / "rating_curve_observed_vs_fit.csv")
print("Wrote:", results_dir / "rating_curve_table.csv")
