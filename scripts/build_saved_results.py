"""Rebuild saved-result geometry from frozen app cases; this does not rerun analyses."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bestfit_examples.data import input_frame, row_named, source_identity, time_series
from bestfit_examples.project_data import load_project
from bestfit_examples.runtime import load_bestfit


def write_snapshot(snapshot, manifest):
    from bestfit_plots import validate_spec
    for spec in snapshot["plots"].values():
        validate_spec(spec)
    key = [snapshot[k] for k in ("slug","table","name")]
    filename = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:20]+".json.gz"
    content = gzip.compress(json.dumps(snapshot,ensure_ascii=False,allow_nan=False,separators=(",", ":")).encode(),mtime=0)
    path = ROOT/"results"/filename
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(content)
    entry = dict(zip(("slug","table","name"),key),file=filename,sha256=hashlib.sha256(content).hexdigest())
    manifest["cases"] = [c for c in manifest["cases"] if [c[k] for k in ("slug","table","name")]!=key]+[entry]
    manifest["cases"].sort(key=lambda c:(c["slug"],c["table"],c["name"]))
    (ROOT/"results"/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Saved {snapshot['slug']}: {snapshot['name']} ({len(snapshot['plots'])} views)",flush=True)


def input_snapshots(slug, table, names=None):
    from bestfit_plots.adapters.input_data import input_data_plots, time_series_plots, threshold_plots
    from System import Enum
    from Numerics.Data import SmoothingFunctionType
    project = load_project(slug)
    runtime = load_bestfit()
    for row in project["tables"][table]["rows"]:
        name = row["Name"]
        if names is not None and name not in names:
            continue
        source = source_identity(project,name,table)
        if table=="Time Series Data":
            plots = time_series_plots(time_series(project,name),source,row["UnitLabel"],peak=row.get("SeriesType") in {"PeakDischarge","PeakStage"})
        else:
            plots = input_data_plots(input_frame(project,name),source,row["UnitLabel"],row.get("IndexLabel", "Index"))
            if row.get("ExactDataMethod")=="PeaksOverThresholdSeries":
                plots.update(threshold_plots(time_series(project,row["TimeSeriesElement"]),source,
                    Enum.Parse(SmoothingFunctionType,row["SmoothingFunction"]),int(row["Period"]),float(row["Threshold"])))
        yield {"schemaVersion":1,"slug":slug,"table":table,"name":name,"origin":"saved-app-input",
               "sourceSha256":project["source"]["sha256"],"sourceCommit":project["source"]["repository_commit"],
               "runtimeCommit":runtime["sourceCommit"],"runtimeHashes":runtime["fileHashes"],"metrics":{},
               "settings":{k:row[k] for k in ("UnitLabel","EntryMethod","SeriesType","ExactDataMethod","TimeBlock","Threshold","Period","SmoothingFunction") if k in row},
               "plots":plots}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only",choices=["inputs","analyses","all"],default="all")
    parser.add_argument("--slug")
    args=parser.parse_args()
    load_bestfit()
    path=ROOT/"results"/"manifest.json"
    manifest=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schemaVersion":1,"cases":[]}
    if args.only in {"inputs","all"}:
        routes=[("usgs-download-example","Time Series Data",None),
                ("usgs-block-max-example","Input Data",None),
                ("usgs-peak-download-example","Input Data",None),
                ("ghcn-peaks-over-threshold-example","Input Data",None),
                ("viglione-et-al-2013","Input Data",None),
                ("sinnemahoning-move3-bayesian","Input Data",["Sinnemahoning - MOVE.3 - With Errors"]),
                ("bulletin-17c-examples","Input Data",["Example #2 - Data","Example #4 - Data"])]
        for slug,table,names in routes:
            if args.slug and args.slug!=slug:
                continue
            for snapshot in input_snapshots(slug,table,names):
                write_snapshot(snapshot,manifest)
    if args.only in {"analyses","all"}:
        from bestfit_examples.analysis import restore_analysis
        from bestfit_examples.snapshot import analysis_snapshot
        cases=json.loads((ROOT/"curriculum-cases.json").read_text(encoding="utf-8"))
        for group in cases:
            slug=group["slug"]
            if args.slug and args.slug!=slug:
                continue
            project=load_project(slug)
            for name in group["names"]:
                snapshot=analysis_snapshot(slug,restore_analysis(project,group["table"],name))
                write_snapshot(snapshot,manifest)


if __name__=="__main__":
    main()
