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


def synthetic_annual_peaks(seed: int = 101, n: int = 50) -> pd.DataFrame:
    years = list(range(1980, 1980 + n))
    noise = list(Normal(0.0, 850.0).GenerateRandomValues(n, seed))
    peaks = [max(500.0, 9200.0 + 35.0 * (year - years[0]) + float(err)) for year, err in zip(years, noise)]
    return pd.DataFrame({"year": years, "peak_cfs": peaks})


def build_bestfit_dataframe(records: pd.DataFrame) -> DataFrame:
    df = DataFrame()
    for row in records.itertuples(index=False):
        df.ExactSeries.Add(ExactData(int(row.year), float(row.peak_cfs)))
    df.PlottingParameter = 0.0
    df.CalculatePlottingPositions()
    return df


def empirical_return_period(values: list[float]) -> pd.DataFrame:
    ranked = sorted(((float(value), i) for i, value in enumerate(values)), reverse=True)
    n = len(ranked)
    rows = []
    for rank, (value, original_index) in enumerate(ranked, start=1):
        p_exceed = rank / (n + 1.0)
        rows.append(
            {
                "original_index": original_index,
                "value": value,
                "rank": rank,
                "p_exceed": p_exceed,
                "return_period": 1.0 / p_exceed,
            }
        )
    return pd.DataFrame(rows).sort_values("return_period")


def fitted_distribution_lookup(analysis: FittingAnalysis) -> dict[str, object]:
    lookup = {}
    for fitted in analysis.FittedDistributions:
        key = str(fitted.Distribution.Type).lower()
        if "generalizedextremevalue" in key or "generalized extreme value" in key:
            lookup["gev"] = fitted.Distribution
        if "gumbel" in key:
            lookup["gumbel"] = fitted.Distribution
    best = sorted(analysis.FittedDistributions, key=lambda fd: fd.AIC)[0]
    lookup.setdefault("best_aic", best.Distribution)
    return lookup


def quantile_table(models: dict[str, object], return_periods: list[float]) -> pd.DataFrame:
    rows = []
    for t in return_periods:
        f = min(max(1.0 - 1.0 / t, 1e-6), 1.0 - 1e-6)
        row = {"return_period": t}
        for name, model in models.items():
            row[name] = float(model.InverseCDF(float(f)))
        rows.append(row)
    return pd.DataFrame(rows)


peaks = synthetic_annual_peaks(seed=101, n=50)
bestfit_df = build_bestfit_dataframe(peaks)

analysis = FittingAnalysis(bestfit_df)
analysis.RunAsync().Wait()
models = fitted_distribution_lookup(analysis)

values = [float(v) for v in peaks["peak_cfs"].tolist()]
ret = empirical_return_period(values)
ret["F"] = 1.0 - 1.0 / ret["return_period"]
for name, dist in models.items():
    ret[name] = [float(dist.InverseCDF(float(min(max(p, 1e-6), 1 - 1e-6)))) for p in ret["F"]]

return_periods = [2, 5, 10, 25, 50, 100, 200]
qt = quantile_table(models, return_periods)

results_dir = Path(__file__).resolve().parents[1] / "outputs" / "tables"
results_dir.mkdir(parents=True, exist_ok=True)
ret.to_csv(results_dir / "flood_frequency_empirical_vs_model.csv", index=False)
qt.to_csv(results_dir / "flood_frequency_return_period_table.csv", index=False)

best = sorted(analysis.FittedDistributions, key=lambda fd: fd.AIC)[0]
print("Flood Frequency Demo")
print("- Sample size:", len(values))
print("- BestFit best distribution:", best.Distribution.Type)
print("- BestFit best AIC:", round(float(best.AIC), 2))
print("\nTop empirical return periods")
cols = ["return_period", "value"] + list(models.keys())
print(ret[cols].tail(10).round(2).to_string(index=False))
print("\nReturn-period quantile table")
print(qt.round(2).to_string(index=False))
print("\nWrote:", results_dir / "flood_frequency_empirical_vs_model.csv")
print("Wrote:", results_dir / "flood_frequency_return_period_table.csv")
