"""Build Python views from frozen sources matched to independent desktop exports."""
from __future__ import annotations
import argparse
from copy import deepcopy
from functools import lru_cache
import gzip
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@lru_cache(maxsize=2)
def project(slug):
    from bestfit_examples.project_data import load_project
    return load_project(slug)


@lru_cache(maxsize=3)
def restored(slug, element):
    from bestfit_examples.analysis import restore_analysis
    p = project(slug)
    matches = [table for table in ("Distribution Fitting Analysis", "Univariate Distribution Analysis",
               "Bivariate Distribution Analysis", "Rating Curve Analysis", "Time Series Analysis")
               if any(row["Name"] == element for row in p["tables"].get(table, {}).get("rows", []))]
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical analysis for {slug}/{element}, got {matches}")
    return restore_analysis(p, matches[0], element)


@lru_cache(maxsize=3)
def base_plots(slug, element, family):
    if family in {"input_data", "time_series_data"}:
        from build_saved_results import input_snapshots
        table = "Input Data" if family == "input_data" else "Time Series Data"
        return next(input_snapshots(slug, table, [element]))["plots"]
    from bestfit_examples.snapshot import analysis_snapshot
    return analysis_snapshot(slug, restored(slug, element))["plots"]


def prepare_spec(slug, reference):
    plot_id, variant, element = (reference[k] for k in ("plotId", "variant", "element"))
    family, name = plot_id.split(".")
    if family == "shared_diagnostics":
        from bestfit_plots.adapters.diagnostics import diagnostic_plots
        import inspect
        options = {}
        parameters = inspect.signature(diagnostic_plots).parameters
        if variant == "warmup":
            if "include_warmup" not in parameters:
                raise NotImplementedError("Trace warmup adapter option is pending")
            options["include_warmup"] = True
        if variant == "prior":
            if "show_prior" not in parameters:
                raise NotImplementedError("Prior histogram overlay adapter is pending")
            options["show_prior"] = True
        if name == "influence" and variant != "bayesian_leverage":
            if "influence_view" not in parameters:
                raise NotImplementedError("Influence view adapter options are pending")
            options["influence_view"] = variant
        spec = diagnostic_plots(restored(slug, element), **options)[name]
    else:
        candidates = base_plots(slug, element, family)
        key = variant if family == "bivariate" else "qq_log10" if name == "qq" and variant == "log10" else "qq_real" if name == "qq" and variant == "real" else name
        if family == "point_process" and variant == "ams":
            key = "frequency_ams"
        spec = candidates[key]
    spec = deepcopy(spec)
    spec["variant"] = variant
    if variant == "comparison" and family in {"univariate", "coincident", "point_process"}:
        selection = reference["variantSelection"]
        prefix = "AlternativeSelector checked "
        if prefix not in selection:
            raise ValueError("Comparison needs an explicit selected source alternative")
        alternative = selection.split(prefix, 1)[1]
        other = base_plots(slug, alternative, family)["frequency"]
        if slug == "viglione-et-al-2013" and other["axes"]["y"]["label"] == "Value":
            # This alternative's saved label is generic. Both records are the
            # Kamp/Zwettl discharge series in cms, established by the project
            # context and tutorial, so make that display context explicit.
            other = deepcopy(other)
            other["axes"] = deepcopy(spec["axes"])
            spec["comparisonUnitContext"] = "Kamp at Zwettl discharge in cms; alternative saved label is generic Value."
        from bestfit_plots.source import add_frequency_comparison
        spec = add_frequency_comparison(spec, other, alternative)
    spec["appReference"] = {"file": plot_id + "--" + variant + ".json",
                            "sourceSha256": reference["sourceSha256"]}
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path, default=ROOT.parent/"RMC-BestFit")
    parser.add_argument("--reference-dir", type=Path, default=ROOT/"validation/plot-parity/app-reference")
    parser.add_argument("--reference-images", type=Path, default=ROOT/"output/plot-reference-gallery")
    parser.add_argument("--only", help="Plot ID prefix, for a targeted refresh")
    parser.add_argument("--images", action="store_true", help="Render PNG/SVG pairs for every populated variant")
    args = parser.parse_args()
    from bestfit_examples.runtime import load_bestfit
    from bestfit_plots import validate_spec
    from bestfit_examples.plotting import export_plot
    load_bestfit()
    reference_dir = args.reference_dir
    references = json.loads((reference_dir/"index.json").read_text(encoding="utf-8"))
    source_manifest = json.loads((ROOT/"data/source-manifest.json").read_text(encoding="utf-8"))["projects"]
    slugs = {entry["source_relative_path"].replace("\\", "/").lower(): slug for slug,entry in source_manifest.items()}
    output = ROOT/"docs/plot-gallery"
    (output/"specs").mkdir(parents=True, exist_ok=True)
    manifest_path = output/"index.json"
    records = json.loads(manifest_path.read_text(encoding="utf-8")) if args.only and manifest_path.exists() else []
    for item in references:
        if args.only and not item["plotId"].startswith(args.only):
            continue
        key = item["plotId"]+"--"+item["variant"]
        record = dict(item, key=key, pythonStatus="pending")
        records = [r for r in records if r["key"] != key]
        try:
            if item["status"] != "exported":
                record["pythonStatus"] = "app_conditional_empty" if item["status"] == "app_conditional_empty" else "reference_unavailable"
                continue
            path = reference_dir/(key+".json")
            reference = json.loads(path.read_text(encoding="utf-8"))
            slug = slugs[item["source"].replace("\\", "/").lower()]
            if reference["sourceSha256"] != source_manifest[slug]["source_sha256"]:
                raise ValueError("Desktop export and Python fixture describe different project bytes")
            spec = prepare_spec(slug, reference)
            validate_spec(spec)
            data = gzip.compress(json.dumps(spec, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode(), mtime=0)
            (output/"specs"/(key+".json.gz")).write_bytes(data)
            record.update(pythonStatus="prepared", slug=slug, sourceSha256=reference["sourceSha256"],
                          specSha256=hashlib.sha256(data).hexdigest(), referenceSha256=hashlib.sha256(path.read_bytes()).hexdigest())
            if args.images:
                export_plot(spec, output/key)
                # Matplotlib path data ends some lines with spaces; keep generated
                # vector files clean in Git without changing their coordinates.
                svg_path = output/(key+".svg")
                svg_path.write_text("\n".join(line.rstrip() for line in
                    svg_path.read_text(encoding="utf-8").splitlines())+"\n",
                    encoding="utf-8", newline="\n")
                source_png = args.reference_images/(key+".png")
                if source_png.exists():
                    shutil.copyfile(source_png, output/(key+"--app.png"))
                record["image"] = key+".png"
        except Exception as error:
            record.update(pythonStatus="failed", error=f"{type(error).__name__}: {error}")
        finally:
            records.append(record)
            print(f"{record['pythonStatus']}: {key}" + (" "+record["error"] if record.get("error") else ""), flush=True)
            manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    cards = []
    for row in records:
        key = row["key"]
        image_path = output/(key+".png")
        images = (f'<div class="pair"><figure><img src="{key}.png"><figcaption>Python</figcaption></figure>'
                  f'<figure><img src="{key}--app.png"><figcaption>Desktop reference</figcaption></figure></div>' if image_path.exists() else "")
        spec_link = (f'<a href="specs/{key}.json.gz">Source-bound PlotSpec</a>'
                     if (output/"specs"/(key+".json.gz")).exists() else
                     '<p>No plot is produced for this saved selection.</p>')
        cards.append(f'<article id="{key}"><h2>{html.escape(row["plotId"])} · {html.escape(row["variant"])}</h2>'
                     f'<p>{html.escape(row["element"])} · {html.escape(row["pythonStatus"])}</p>{images}'
                     f'<p>{html.escape(row.get("error", ""))}</p>{spec_link}</article>')
    (output/"index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>BestFit app plot gallery</title>'
        '<style>body{max-width:1500px;margin:40px auto;padding:0 24px;font:16px system-ui;color:#203040;background:#fafafa}'
        'h1{font-size:36px}article{background:white;padding:24px;margin:24px 0;border:1px solid #dce2e8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}'
        'figure{margin:0}img{width:100%}figcaption{font-size:14px;color:#556}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>'
        '<h1>BestFit app plot gallery</h1><p>Python and independently exported desktop views of the same frozen source. '
        'Prepared means the adapter ran; only the separate parity report establishes geometry agreement. '
        'Fonts and interactive/custom styles are outside the comparison.</p>'+"".join(cards)+'</html>', encoding="utf-8")


if __name__ == "__main__":
    main()
