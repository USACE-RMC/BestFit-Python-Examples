from __future__ import annotations

import pythonnet
pythonnet.load("coreclr")

import clr
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "notebooks"))
from helper_functions import resolve_bestfit_dll, resolve_numerics_dll

# Load the paired Numerics and BestFit assemblies from the same preferred build.
clr.AddReference(str(resolve_numerics_dll()))
clr.AddReference(str(resolve_bestfit_dll()))

from Numerics.Distributions import GeneralizedExtremeValue, Gumbel


def synthetic_annual_peaks(seed: int = 101, n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    years = np.arange(1980, 1980 + n)
    baseline = 9200 + 35 * (years - years.min())
    noise = rng.normal(0, 850, size=n)
    peaks = np.maximum(500, baseline + noise)
    return pd.DataFrame({"year": years, "peak_cfs": peaks})


def empirical_return_period(values: np.ndarray) -> pd.DataFrame:
    x = np.asarray(values, dtype=float)
    ranks = np.argsort(np.argsort(-x)) + 1
    n = len(x)
    p_exceed = ranks / (n + 1.0)
    rp = 1.0 / p_exceed
    return pd.DataFrame({"value": x, "rank": ranks, "p_exceed": p_exceed, "return_period": rp})


def quantile_table(models: dict[str, object], return_periods: list[float]) -> pd.DataFrame:
    rows = []
    for t in return_periods:
        f = np.clip(1.0 - 1.0 / t, 1e-6, 1.0 - 1e-6)
        row = {"return_period": t}
        for name, model in models.items():
            row[name] = float(model.InverseCDF(float(f)))
        rows.append(row)
    return pd.DataFrame(rows)


peaks = synthetic_annual_peaks(seed=101, n=50)
x = peaks["peak_cfs"].to_numpy()
mu = float(np.mean(x))
sd = float(np.std(x, ddof=1))

models = {
    "gev": GeneralizedExtremeValue(mu, max(1e-6, 0.8 * sd), 0.08),
    "gumbel": Gumbel(mu, max(1e-6, 0.8 * sd)),
}

ret = empirical_return_period(x).sort_values("return_period")
ret["F"] = 1.0 - 1.0 / ret["return_period"]
for name, dist in models.items():
    ret[name] = [float(dist.InverseCDF(float(np.clip(p, 1e-6, 1 - 1e-6)))) for p in ret["F"]]

return_periods = [2, 5, 10, 25, 50, 100, 200]
qt = quantile_table(models, return_periods)

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
ret.to_csv(results_dir / "flood_frequency_empirical_vs_model.csv", index=False)
qt.to_csv(results_dir / "flood_frequency_return_period_table.csv", index=False)

print("Flood Frequency Demo")
print("- Sample size:", len(x))
print("- Mean peak:", round(mu, 2))
print("- Std peak:", round(sd, 2))
print("\nTop empirical return periods")
print(ret[["return_period", "value", "gev", "gumbel"]].tail(10).round(2).to_string(index=False))
print("\nReturn-period quantile table")
print(qt.round(2).to_string(index=False))
print("\nWrote:", results_dir / "flood_frequency_empirical_vs_model.csv")
print("Wrote:", results_dir / "flood_frequency_return_period_table.csv")
