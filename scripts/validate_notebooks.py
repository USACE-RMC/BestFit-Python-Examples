"""Execute the real teaching notebooks in fresh kernels without saved projects/results."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ("00_time_series_data", "01_input_data", "02_distribution_fitting",
             "03_stationary_information_expansion", "04_nonstationary_univariate", "05_bulletin_17c",
             "06_advanced_univariate", "07_bivariate_analysis", "08_coincident_frequency",
             "09_rating_curves", "10_classic_time_series", "11_regression")


def stage_workspace(root, destination):
    """Whitelist the inputs of execution; never copy any prior result directory."""
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("runtime-lock.json", "curriculum-cases.json"):
        shutil.copy2(root / name, destination / name)
    shutil.copytree(root / "bestfit_examples", destination / "bestfit_examples",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("raw", "raw-responses"):
        if (root / "data" / name).exists():
            shutil.copytree(root / "data" / name, destination / "data" / name)
    for name in ("dotnet/bestfit.runtimeconfig.json", ".runtime/provenance.json",
                 ".runtime/lib/RMC.BestFit.dll", ".runtime/lib/Numerics.dll"):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / name, target)
    return destination


GUARD = '''
import os, sys
from pathlib import Path
_validation_root = Path.cwd().resolve()
assert not (_validation_root / "data/projects").exists()
assert not (_validation_root / "results").exists()
assert not (_validation_root / "output/reruns").exists()
sys.path.insert(0, str(_validation_root))
def _raw_only_audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0]))
        parts = tuple(p.lower() for p in path.parts)
        forbidden = path.suffix.lower() == ".bestfit" or "results" in parts or "reruns" in parts
        forbidden = forbidden or any(parts[i:i+2] == ("data", "projects") for i in range(len(parts)-1))
        if forbidden:
            raise RuntimeError("Saved project/result access forbidden during headless validation: " + str(path))
    if event == "import" and args[0] in {"bestfit_examples.analysis", "bestfit_examples.results", "bestfit_examples.project_data"}:
        raise RuntimeError("Legacy restoration modules are unavailable in headless validation")
sys.addaudithook(_raw_only_audit)
import bestfit_examples.raw, bestfit_examples.runtime
assert Path(bestfit_examples.raw.__file__).resolve().is_relative_to(_validation_root)
assert Path(bestfit_examples.runtime.__file__).resolve().is_relative_to(_validation_root)
print("Validation: raw inputs and verified runtime only; saved project/result access is forbidden.")
'''


def audit_artifacts(stem, artifacts, run_receipts, root=ROOT):
    """Check the original case roster and bind every figure to this kernel's work."""
    manifest = json.loads((root / "data/raw/manifest.json").read_text(encoding="utf-8"))
    curriculum = json.loads((root / "curriculum-cases.json").read_text(encoding="utf-8"))
    expected = {(name, manifest["projects"][entry["slug"]]["source"]["sha256"])
                for entry in curriculum if entry["notebook"] == stem[:2] for name in entry["names"]}
    actual = {(r["name"], r["source"]["sha256"]) for r in run_receipts if r["status"] == "completed"}
    if expected - actual:
        raise ValueError("Missing completed curriculum cases: " + repr(sorted(expected - actual)))
    by_id = {r["runId"]: r for r in run_receipts}
    if len(by_id) != len(run_receipts) or len(actual) != len(run_receipts):
        raise ValueError("Execution receipts must have unique run identities and case/source pairs")
    for run in run_receipts:
        if run.get("class") == "CoincidentFrequencyAnalysis":
            for axis in ("X", "Y"):
                chain = run.get("marginalChains", {}).get(axis)
                dependency = by_id.get(chain.get("runId")) if chain else None
                if (not dependency or dependency.get("class") != "UnivariateAnalysis"
                        or chain.get("name") != dependency["name"] or chain.get("outputDraws", 0) <= 0
                        or dependency["source"] != run["source"]):
                    raise ValueError("CFA must propagate both fresh marginal chains: " + run["name"])
    pngs = {p.stem for p in (artifacts / "figures").glob("*.png")}
    specs = {p.stem for p in (artifacts / "figures").glob("*.json")}
    if not specs or pngs != specs:
        raise ValueError("Every displayed figure must have both a PNG and a provenance specification")
    raw_ids = {"raw:" + item["source"]["sha256"] for item in manifest["projects"].values()}
    figures = []
    for filename in sorted(specs):
        path = artifacts / "figures" / (filename + ".json")
        spec = json.loads(path.read_text(encoding="utf-8"))
        source = spec["source"]
        if int(stem[:2]) >= 2:
            run = by_id.get(source.get("runId"))
            if source.get("kind") != "rerun" or run is None or source.get("id") != run["name"]:
                raise ValueError("Figure does not identify a completed analysis from this kernel: " + filename)
        elif source.get("kind") != "rerun" or source.get("runId") not in raw_ids:
            raise ValueError("Data figure does not identify a verified raw input: " + filename)
        figures.append({"file": filename + ".png", "plotId": spec["plotId"], "source": source,
                        "specSha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "pngSha256": hashlib.sha256(path.with_suffix(".png").read_bytes()).hexdigest()})
    return {"status": "passed", "expectedPrimaryCases": len(expected),
            "completedAnalysesIncludingDependencies": len(actual), "figureLineage": figures}


def execution_inputs(root):
    """Bind receipts to the actual helper, fixture and managed runtime bytes."""
    paths = [root / name for name in ("runtime-lock.json", "curriculum-cases.json",
             "dotnet/bestfit.runtimeconfig.json", ".runtime/provenance.json",
             ".runtime/lib/RMC.BestFit.dll", ".runtime/lib/Numerics.dll")]
    paths += list((root / "bestfit_examples").rglob("*.py"))
    paths += [p for name in ("raw", "raw-responses") for p in (root / "data" / name).glob("*") if p.is_file()]
    hashes = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    import bestfit_plots
    package = Path(bestfit_plots.__file__).parent
    hashes.update({"canonical_plots/" + p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted(package.rglob("*.py"))})
    return hashes


def audit_notebook_outputs(book, artifact_audit):
    """Require executed cells and the same PNG bytes/identities as the fresh plots."""
    code = [c for c in book["cells"] if c["cell_type"] == "code" and "".join(c["source"]).strip()]
    counts = [c.get("execution_count") for c in code]
    if not counts or any(not isinstance(n, int) or n < 1 for n in counts) or counts != sorted(set(counts)):
        raise ValueError("Notebook contains unexecuted or out-of-order code cells")
    embedded = []
    for cell in code:
        for output in cell.get("outputs", []):
            if output["output_type"] == "error":
                raise ValueError("Notebook contains an execution error")
            data = output.get("data", {})
            if "image/png" in data:
                png = base64.b64decode("".join("".join(data["image/png"]).split()), validate=True)
                metadata = output.get("metadata", {}).get("bestfit", {})
                embedded.append({"pngSha256": hashlib.sha256(png).hexdigest(),
                                 "plotId": metadata.get("plotId"), "source": metadata.get("source")})
    expected = [{key: item[key] for key in ("pngSha256", "plotId", "source")}
                for item in artifact_audit["figureLineage"]]
    if embedded != expected:
        raise ValueError("Embedded notebook figures do not match fresh rendered artifacts and identities")
    payload = [{"execution_count": c["execution_count"], "outputs": c.get("outputs", [])} for c in code]
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"status": "passed", "executedCodeCells": len(code), "embeddedPngs": len(embedded),
            "outputsSha256": digest}


def audit_existing(stems):
    """Check retained evidence against original hashes without modifying receipts."""
    import nbformat
    inputs = execution_inputs(ROOT)
    for stem in stems:
        path = ROOT / "validation/headless" / (stem + ".json")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt["status"] != "passed":
            raise ValueError(stem + ": no successful execution to audit")
        if not receipt.get("notebookWritten"):
            raise ValueError(stem + ": no retained output validation; execute with --write")
        if receipt.get("executionInputs") != inputs:
            raise ValueError(stem + ": helper, fixture, plotting package or runtime changed after execution")
        book = nbformat.read(ROOT / "notebooks" / (stem + ".ipynb"), as_version=4)
        source_hash = hashlib.sha256("\n".join("".join(c["source"]) for c in book["cells"]).encode()).hexdigest()
        if receipt["sourceSha256"] != source_hash:
            raise ValueError(stem + ": notebook changed after execution")
        artifacts = Path(receipt["workspace"]) / "new-output" / stem
        runs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((artifacts / "runs").glob("*.json"))]
        if runs != receipt["analyses"]:
            raise ValueError(stem + ": run artifacts changed after execution")
        artifact_audit = audit_artifacts(stem, artifacts, runs, root=ROOT)
        if artifact_audit != receipt["artifactAudit"]:
            raise ValueError(stem + ": figure artifacts changed after execution")
        if audit_notebook_outputs(book, artifact_audit) != receipt.get("notebookOutputAudit"):
            raise ValueError(stem + ": notebook outputs changed after execution")
        print(stem + ": original inputs, runs, tables and embedded figures verified", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebooks", nargs="*", default=list(NOTEBOOKS))
    parser.add_argument("--write", action="store_true", help="Retain fresh tables and figures in the notebooks")
    parser.add_argument("--audit-only", action="store_true", help="Check current source, case roster and figure lineage against existing successful runs")
    parser.add_argument("--timeout", type=int, default=14400, help="Per-cell seconds; full source settings are never shortened")
    args = parser.parse_args(argv)
    unknown = set(args.notebooks) - set(NOTEBOOKS)
    if unknown:
        parser.error("Unknown notebooks: " + ", ".join(sorted(unknown)))
    if args.audit_only:
        audit_existing(args.notebooks)
        return 0
    run_id = uuid.uuid4().hex[:12]
    stage = stage_workspace(ROOT, ROOT / ".runtime/headless-validation" / run_id)
    input_hashes = execution_inputs(stage)
    kernel_root = stage / ".runtime/jupyter"
    kernel = kernel_root / "kernels/bestfit-examples"
    kernel.mkdir(parents=True)
    (kernel / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-X", "utf8", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                                                   "display_name": "BestFit examples", "language": "python"}))
    os.environ.update(JUPYTER_PATH=str(kernel_root), JUPYTER_RUNTIME_DIR=str(stage / ".runtime/jupyter-runtime"),
                      IPYTHONDIR=str(stage / ".runtime/ipython"), PYTHONUTF8="1", MPLBACKEND="Agg")
    # Never inherit an override pointing at a different checkout's runtime.
    os.environ["BESTFIT_RUNTIME_DIR"] = str(stage / ".runtime")
    import nbformat
    from nbclient import NotebookClient
    destination = ROOT / "validation/headless"
    destination.mkdir(parents=True, exist_ok=True)
    for stem in args.notebooks:
        path = ROOT / "notebooks" / (stem + ".ipynb")
        book = nbformat.read(path, as_version=4)
        nbformat.validate(book)
        source_hash = hashlib.sha256("\n".join(c.source for c in book.cells).encode()).hexdigest()
        for cell in book.cells:
            if cell.cell_type == "code":
                cell.outputs, cell.execution_count = [], None
        book.cells.insert(0, nbformat.v4.new_code_cell(GUARD))
        artifacts = stage / "new-output" / stem
        os.environ["BESTFIT_RUN_DIR"] = str(artifacts / "runs")
        os.environ["BESTFIT_FIGURE_DIR"] = str(artifacts / "figures")
        started = time.monotonic()
        receipt = {"notebook": path.name, "status": "running", "python": sys.version.split()[0],
                   "independentKernel": True, "savedCachesUnavailable": True, "runId": run_id,
                   "sourceSha256": source_hash, "rawManifestSha256": hashlib.sha256((stage / "data/raw/manifest.json").read_bytes()).hexdigest(),
                   "runtime": json.loads((stage / ".runtime/provenance.json").read_text()),
                   "executionInputs": input_hashes, "notebookWritten": bool(args.write),
                   "workspace": str(stage)}
        print(f"Executing {path.name} (raw-only workspace {run_id})", flush=True)
        try:
            NotebookClient(book, kernel_name="bestfit-examples", timeout=args.timeout,
                           resources={"metadata": {"path": str(stage)}}).execute()
            book.cells.pop(0)
            for cell in book.cells:
                cell.metadata.pop("execution", None)
                if cell.cell_type == "code":
                    assert not any(o.output_type == "error" for o in cell.outputs)
            run_receipts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((artifacts / "runs").glob("*.json"))]
            artifact_audit = audit_artifacts(stem, artifacts, run_receipts, root=stage)
            output_audit = audit_notebook_outputs(book, artifact_audit)
            nbformat.write(book, artifacts / "executed.ipynb")
            if args.write:
                nbformat.write(book, path)
            receipt.update(status="passed", codeCells=sum(c.cell_type == "code" for c in book.cells),
                           errorOutputs=0, analyses=run_receipts, artifactAudit=artifact_audit,
                           notebookOutputAudit=output_audit,
                           figures=len(list((artifacts / "figures").glob("*.png"))))
        except Exception as error:
            receipt.update(status="failed", error=str(error))
            raise
        finally:
            receipt["elapsedSeconds"] = round(time.monotonic() - started, 3)
            (destination / (stem + ".json")).write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{receipt['status']}: {path.name} ({receipt['elapsedSeconds']} s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
