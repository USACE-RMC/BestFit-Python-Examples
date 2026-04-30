from __future__ import annotations

import pythonnet
pythonnet.load("netfx")

import clr
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "notebooks"))
from helper_functions import resolve_bestfit_dll, resolve_numerics_dll

clr.AddReference(str(resolve_numerics_dll()))
clr.AddReference(str(resolve_bestfit_dll()))

from Numerics.Distributions import GeneralizedExtremeValue

rng = np.random.default_rng(25)
sites = [f"S{i:02d}" for i in range(1, 9)]
records = []
for s in sites:
    idx_flood = rng.uniform(7000, 13000)
    annual = idx_flood * rng.lognormal(mean=0.0, sigma=0.18, size=35)
    for y, q in zip(range(1990, 1990 + 35), annual):
        records.append((s, y, q, idx_flood))

regional = pd.DataFrame(records, columns=["site", "year", "peak", "index_flood"])
regional["scaled_peak"] = regional["peak"] / regional["index_flood"]

# Regional scaled distribution
scaled_mean = float(regional["scaled_peak"].mean())
scaled_std = float(regional["scaled_peak"].std(ddof=1))
d = GeneralizedExtremeValue(scaled_mean, max(1e-6, 0.8 * scaled_std), 0.08)

# Regional quantiles in scaled space
return_periods = [10, 25, 50, 100]
scaled_q = {}
for t in return_periods:
    f = 1.0 - 1.0 / t
    scaled_q[t] = float(d.InverseCDF(float(f)))

# Project back to each site
at_site = regional.groupby("site", as_index=False)["index_flood"].mean()
for t in return_periods:
    at_site[f"q{t}"] = at_site["index_flood"] * scaled_q[t]

site_summary = regional.groupby("site", as_index=False).agg(
    mean_peak=("peak", "mean"),
    std_peak=("peak", "std"),
    cv_scaled=("scaled_peak", lambda s: float(np.std(s, ddof=1) / np.mean(s))),
)
final = at_site.merge(site_summary, on="site", how="left")

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
regional.to_csv(results_dir / "regional_analysis_site_records.csv", index=False)
final.to_csv(results_dir / "regional_analysis_site_quantiles.csv", index=False)

print("Regional Analysis Demo")
print("Scaled-space summary")
print(f"- mean={scaled_mean:.4f}, std={scaled_std:.4f}")
for t in return_periods:
    print(f"- scaled q{t}={scaled_q[t]:.4f}")

print("\nSite quantiles")
print(final.round(2).to_string(index=False))
print("\nWrote:", results_dir / "regional_analysis_site_records.csv")
print("Wrote:", results_dir / "regional_analysis_site_quantiles.csv")
