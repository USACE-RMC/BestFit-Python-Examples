"""Small, explicit bridges from frozen source records to portable data objects."""
from __future__ import annotations
import base64
import zlib
from .project_data import load_project


def row_named(project, table, name):
    rows = [r for r in project["tables"][table]["rows"] if r.get("Name") == name]
    if len(rows) != 1:
        raise KeyError(f"Expected one {table} row named {name!r}, found {len(rows)}")
    return rows[0]


def series_xml(row):
    compressed = row.get("TimeSeriesCompressed")
    if compressed and compressed.get("data"):
        return zlib.decompress(base64.b64decode(compressed["data"], validate=True), wbits=-15).decode("utf-8")
    if row.get("TimeSeries"):
        return row["TimeSeries"]
    raise ValueError(f"No time-series data for {row['Name']}")


def time_series(project, name):
    from .runtime import load_bestfit
    load_bestfit()
    from Numerics.Data import TimeSeries
    from System.Xml.Linq import XElement
    return TimeSeries(XElement.Parse(series_xml(row_named(project, "Time Series Data", name))))


def input_frame(project, name):
    from .runtime import load_bestfit
    load_bestfit()
    from RMC.BestFit.Models import DataFrame
    from System.Xml.Linq import XElement
    return DataFrame(XElement.Parse(row_named(project, "Input Data", name)["DataFrame"]))


def source_identity(project, name, table="Input Data"):
    from bestfit_plots.adapters.common import source_identity as identity
    return identity({"source": project["source"], "name": name, "table": table,
                     "row": row_named(project, table, name)})


def series_inventory(project):
    """A pandas view of source choices, dates and missing data, without loading .NET."""
    import pandas as pd
    output = []
    for row, decoded in zip(project["tables"].get("Time Series Data", {}).get("rows", []),
                            project["decoded"].get("Time Series Data", [])):
        records = decoded.get("TimeSeries", {}).get("records", [])
        output.append({"Series": row["Name"], "Route": row.get("EntryMethod"), "Type": row.get("SeriesType"),
                       "Unit": row.get("UnitLabel"), "Records": len(records),
                       "Start": records[0]["Index"] if records else None,
                       "End": records[-1]["Index"] if records else None,
                       "Missing": sum(r.get("Value") in {"NaN", ""} for r in records)})
    return pd.DataFrame(output)


def input_inventory(project):
    import pandas as pd
    output = []
    for row, decoded in zip(project["tables"].get("Input Data", {}).get("rows", []),
                            project["decoded"].get("Input Data", [])):
        frame = decoded["DataFrame"]
        output.append({"Input": row["Name"], "Unit": row.get("UnitLabel"),
                       "Method": row.get("ExactDataMethod"),
                       **{kind.replace("Series", ""): len(frame["series"].get(kind, []))
                          for kind in ("ExactSeries", "UncertainSeries", "IntervalSeries", "ThresholdSeries")},
                       "Flagged low floods": int(frame["attributes"].get("NumberOfLowOutliers", 0))})
    return pd.DataFrame(output)
