# %% [markdown]
# # 00 · Time-series data and reproducible setup
#
# Start with what was observed: daily values, instantaneous measurements, annual peaks,
# and paired field measurements represent different sampling processes.
# This notebook loads the verified managed runtime and constructs Numerics time-series objects
# used by headless BestFit models. It follows the explicit construction pattern in
# Numerics-Python-Examples `10_time_series.ipynb` and BestFit Verification `TestData.cs`.

# %%
from pathlib import Path
import sys
ROOT = Path.cwd() if (Path.cwd() / "runtime-lock.json").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))
from time import perf_counter
import numpy as np
import pandas as pd
from IPython.display import display
from bestfit_examples.runtime import load_bestfit
from bestfit_examples.raw import load_raw
from bestfit_examples.fresh import show
runtime = load_bestfit()
print(runtime)
from System import DateTime, Double
from Numerics.Data import TimeSeries, TimeInterval, SeriesOrdinate, BlockFunctionType
from bestfit_plots.adapters.input_data import time_series_plots

# %% [markdown]
# ## Frozen USGS observations
#
# The original USGS example contains eight series. Daily discharge is a daily summary;
# instantaneous discharge describes conditions at a timestamp; an annual peak is the largest event in a year.
# Raw observations and metadata have been extracted without fitted objects or saved plot coordinates.
# The inventory includes the large instantaneous records; the following construction cells use the same
# daily and annual-peak records displayed in this example.

# %%
started = perf_counter()
raw = load_raw("usgs-download-example")
inventory = []
for name, item in raw["series"].items():
    records = item["records"]
    inventory.append({"Series": name, "Type": item["metadata"]["SeriesType"],
                      "Unit": item["metadata"]["UnitLabel"], "Records": len(records),
                      "Start": records[0]["Index"], "End": records[-1]["Index"],
                      "Missing": sum(not np.isfinite(float(r["Value"])) for r in records)})
display(pd.DataFrame(inventory))
print(raw["source"])

# %% [markdown]
# ## Construct daily discharge and calculate a transformation
#
# Adding timestamped ordinates preserves actual dates and missing values. A missing measurement
# remains NaN, never zero or silently interpolated. The 365-day moving average is calculated
# by Numerics from the newly constructed series. Change `period` to examine another averaging interval.

# %%
daily_name = "USGS - 01134500 - Daily Discharge"
daily_records = raw["series"][daily_name]["records"]
daily = TimeSeries(TimeInterval.OneDay)
for row in daily_records:
    daily.Add(SeriesOrdinate[DateTime, Double](DateTime.Parse(row["Index"]), float(row["Value"])))
moving_average = daily.MovingAverage(365)
monthly_maximum = daily.MonthlySeries(BlockFunctionType.Maximum)
assert daily.Count == len(daily_records)
# Check the transformations against independent arithmetic on the raw observations.
raw_values = np.array([float(row["Value"]) for row in daily_records])
expected_average = pd.Series(raw_values).rolling(365, min_periods=365).mean().iloc[364:]
np.testing.assert_allclose([float(p.Value) for p in moving_average], expected_average,
                           rtol=1e-12, atol=1e-9, equal_nan=True)
assert str(moving_average[0].Index.ToString("yyyy-MM-dd")) == daily_records[364]["Index"][:10]
raw_months = pd.DataFrame({"Date": pd.to_datetime([r["Index"] for r in daily_records]),
                          "Value": raw_values})
expected_maxima = raw_months.groupby(raw_months["Date"].dt.to_period("M"))["Value"].max()
np.testing.assert_allclose([float(p.Value) for p in monthly_maximum], expected_maxima,
                           rtol=0, atol=0, equal_nan=True)
print("Verified all 365-day means and calendar-month maxima against raw-observation arithmetic.")
display(pd.DataFrame([{"Date": str(p.Index.ToString("yyyy-MM-dd")), "Monthly maximum": float(p.Value)}
                      for p in monthly_maximum]).head(12))
source = {"kind": "rerun", "id": daily_name, "runId": "raw:" + raw["source"]["sha256"]}
daily_plots = time_series_plots(daily, source, raw["series"][daily_name]["metadata"]["UnitLabel"])
show(daily_plots["series"])
show(daily_plots["seasonality"])
show(time_series_plots(moving_average, source, "365-day mean discharge (cfs)")["series"])

# %% [markdown]
# ## Annual peaks and monthly event frequency
#
# Seasonality bands above describe the spread of monthly observations. They are not uncertainty
# bounds for a fitted flood-frequency curve. Peak seasonality below is a monthly event-frequency histogram.
# The source labels this sparse peak series `OneDay`; retain that metadata and its actual event dates.
# ACF/PACF calculations in the canonical utilities keep the app's missing-data guard.

# %%
peak_name = "USGS - 01614000 - Peak Discharge"
peaks = TimeSeries(TimeInterval.OneDay)
for row in raw["series"][peak_name]["records"]:
    peaks.Add(SeriesOrdinate[DateTime, Double](DateTime.Parse(row["Index"]), float(row["Value"])))
peak_source = {"kind": "rerun", "id": peak_name, "runId": source["runId"]}
show(time_series_plots(peaks, peak_source, raw["series"][peak_name]["metadata"]["UnitLabel"], peak=True)["seasonality"])
assert peaks.Count == 69

# %% [markdown]
# ## Field measurements and other import routes
#
# Measured stage and discharge are separate field series. The source stores 939 stage records and
# 412 discharge records; calling every row a pair would be incorrect. Join timestamps explicitly
# before using paired measurements for a rating curve, and inspect unmatched observations.
# GHCN precipitation, CHMN, HEC-DSS and manual-entry inputs retain their original route and units.
# The upstream ABOM example remains an optional online import, not a prerequisite.

# %%
stage_records = pd.DataFrame(raw["series"]["USGS - 01570500 - Measured Stage"]["records"])
flow_records = pd.DataFrame(raw["series"]["USGS - 01570500 - Measured Discharge"]["records"])
paired = stage_records.merge(flow_records, on="Index", how="inner", suffixes=("_stage", "_discharge"))
print(f"{len(stage_records)} stage records, {len(flow_records)} discharge records, {len(paired)} joined rows")
display(paired.head())
routes = ["ghcn-download-example", "chmn-download-example", "hec-dss-import-example", "manual-entry-example"]
route_inventory = []
for slug in routes:
    imported = load_raw(slug)
    for name, item in imported["series"].items():
        route_inventory.append({"Project": slug, "Series": name, "Route": item["metadata"]["EntryMethod"],
                                "Unit": item["metadata"]["UnitLabel"], "Records": len(item["records"])})
display(pd.DataFrame(route_inventory))
print(f"Data preparation and plots: {perf_counter() - started:.2f} s")

# %% [markdown]
# **Adapt this example:** provide timestamp/value rows from your own CSV or measurement source,
# select the appropriate `TimeInterval`, construct `TimeSeries`, and call its calculation methods.
# Keep units, observation timing and missing values explicit. Notebook 01 prepares these observations
# for frequency analysis; subsequent notebooks construct models and execute estimation.
