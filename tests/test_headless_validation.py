"""The acceptance runner must reject partial runs and stale figure identities."""
import importlib.util
import base64
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("headless_validator", ROOT / "scripts/validate_notebooks.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def fixture(root):
    (root / "data/raw").mkdir(parents=True)
    (root / "data/raw/manifest.json").write_text(json.dumps({"projects": {"sample": {"source": {"sha256": "raw-hash"}}}}))
    (root / "curriculum-cases.json").write_text(json.dumps([
        {"notebook": "02", "slug": "sample", "names": ["case A", "case B"]}]))
    figures = root / "artifacts/figures"
    figures.mkdir(parents=True)
    (figures / "000-frequency.png").write_bytes(b"image bytes for identity check")
    (figures / "000-frequency.json").write_text(json.dumps({"plotId": "frequency", "source": {
        "kind": "rerun", "id": "case A", "runId": "fresh-A"}}))
    runs = [{"name": name, "status": "completed", "source": {"sha256": "raw-hash"}, "runId": run_id}
            for name, run_id in (("case A", "fresh-A"), ("case B", "fresh-B"))]
    return root / "artifacts", runs


def test_requires_every_original_case_even_when_one_run_succeeded(tmp_path):
    artifacts, runs = fixture(tmp_path)
    with pytest.raises(ValueError, match="Missing completed curriculum cases"):
        validator.audit_artifacts("02_test", artifacts, runs[:1], root=tmp_path)


def test_rejects_figure_from_another_kernel_run(tmp_path):
    artifacts, runs = fixture(tmp_path)
    runs[0]["runId"] = "different-run"
    with pytest.raises(ValueError, match="Figure does not identify"):
        validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)


def test_retains_verifiable_figure_hashes_and_case_counts(tmp_path):
    artifacts, runs = fixture(tmp_path)
    result = validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)
    assert result["expectedPrimaryCases"] == 2
    assert result["completedAnalysesIncludingDependencies"] == 2
    assert result["figureLineage"][0]["source"]["runId"] == "fresh-A"
    assert len(result["figureLineage"][0]["pngSha256"]) == 64


def test_requires_both_displayed_image_and_plot_spec(tmp_path):
    artifacts, runs = fixture(tmp_path)
    (artifacts / "figures/001-untracked.png").write_bytes(b"missing spec")
    with pytest.raises(ValueError, match="both a PNG"):
        validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)


def test_show_embeds_the_same_png_it_exports_with_agg(tmp_path, monkeypatch):
    import matplotlib
    matplotlib.use("Agg")
    from IPython.core.formatters import DisplayFormatter
    import IPython.display
    from bestfit_examples.fresh import show
    shown = []
    monkeypatch.setattr(IPython.display, "display", lambda obj, **kwargs: shown.append(
        (DisplayFormatter().format(obj)[0], kwargs.get("metadata", {}))))
    monkeypatch.setenv("BESTFIT_FIGURE_DIR", str(tmp_path))
    show({"version": 1, "plotId": "test.line", "variant": "default", "title": "Fresh result",
          "source": {"kind": "rerun", "id": "case A", "runId": "fresh-A"},
          "axes": {"x": {"label": "x", "scale": "linear", "unit": "", "value": "value"},
                   "y": {"label": "y", "scale": "linear", "unit": "", "value": "value"}},
          "series": [{"name": "Result", "kind": "line", "x": [0, 1], "y": [1, 2], "style": {}}]})
    data, metadata = shown[0]
    assert "image/png" in data
    png = data["image/png"]
    if isinstance(png, str):
        png = base64.b64decode(png)
    assert png == next(tmp_path.glob("*.png")).read_bytes()
    assert metadata["bestfit"]["source"]["runId"] == "fresh-A"


def output_book():
    import nbformat
    image = b"fresh image"
    source = {"kind": "rerun", "id": "case A", "runId": "fresh-A"}
    book = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell("show(spec)", execution_count=2,
        outputs=[nbformat.v4.new_output("display_data", data={"image/png": base64.b64encode(image).decode()},
                                      metadata={"bestfit": {"plotId": "frequency", "source": source}})])])
    audit = {"figureLineage": [{"pngSha256": hashlib.sha256(image).hexdigest(),
                                "plotId": "frequency", "source": source}]}
    return book, audit


def test_output_audit_rejects_cleared_notebooks_and_text_only_plots():
    book, audit = output_book()
    expected = validator.audit_notebook_outputs(book, audit)
    assert expected["embeddedPngs"] == 1
    book.cells[0].outputs[0].data = {"text/plain": "<Figure with 1 Axes>"}
    with pytest.raises(ValueError, match="Embedded notebook figures"):
        validator.audit_notebook_outputs(book, audit)
    book.cells[0].outputs = []
    book.cells[0].execution_count = None
    with pytest.raises(ValueError, match="unexecuted"):
        validator.audit_notebook_outputs(book, audit)


def test_output_audit_rejects_stale_embedded_figures():
    book, audit = output_book()
    book.cells[0].outputs[0].data["image/png"] = base64.b64encode(b"older figure").decode()
    with pytest.raises(ValueError, match="Embedded notebook figures"):
        validator.audit_notebook_outputs(book, audit)


def retained_evidence(root, monkeypatch):
    """Small on-disk acceptance bundle, without running any scientific estimator."""
    import nbformat
    import shutil
    source, runs = fixture(root)
    stem = "02_test"
    artifacts = root / "new-output" / stem
    shutil.copytree(source, artifacts)
    second_spec = json.loads((artifacts / "figures/000-frequency.json").read_text())
    second_spec["plotId"] = "density"
    (artifacts / "figures/001-density.json").write_text(json.dumps(second_spec))
    (artifacts / "figures/001-density.png").write_bytes(b"second fresh figure")
    (artifacts / "runs").mkdir()
    for i, run in enumerate(runs):
        (artifacts / "runs" / f"{i}.json").write_text(json.dumps(run))
    audit = validator.audit_artifacts(stem, artifacts, runs, root=root)
    outputs = []
    for item in audit["figureLineage"]:
        png = (artifacts / "figures" / item["file"]).read_bytes()
        outputs.append(nbformat.v4.new_output("display_data",
            data={"image/png": base64.b64encode(png).decode()},
            metadata={"bestfit": {"plotId": item["plotId"], "source": item["source"]}}))
    book = nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(
        "show(fresh_results)", execution_count=2, outputs=outputs)])
    (root / "notebooks").mkdir()
    nbformat.write(book, root / "notebooks" / (stem + ".ipynb"))
    inputs = {"helper.py": "original-helper-hash"}
    monkeypatch.setattr(validator, "execution_inputs", lambda _: inputs)
    monkeypatch.setattr(validator, "ROOT", root)
    receipt = {"status": "passed", "notebookWritten": True, "executionInputs": dict(inputs),
               "workspace": str(root), "analyses": runs, "artifactAudit": audit,
               "sourceSha256": hashlib.sha256(book.cells[0].source.encode()).hexdigest(),
               "notebookOutputAudit": validator.audit_notebook_outputs(book, audit)}
    directory = root / "validation/headless"
    directory.mkdir(parents=True)
    receipt_path = directory / (stem + ".json")
    receipt_path.write_text(json.dumps(receipt))
    return stem, artifacts, receipt_path, inputs


@pytest.mark.parametrize("change, message", [
    ("replace_figure", "figure artifacts changed"),
    ("remove_pair", "figure artifacts changed"),
    ("run_receipt", "run artifacts changed"),
    ("helper", "helper, fixture"),
    ("table", "notebook outputs changed"),
])
def test_audit_only_rejects_changed_evidence_without_rewriting_receipts(tmp_path, monkeypatch, change, message):
    import nbformat
    stem, artifacts, path, inputs = retained_evidence(tmp_path, monkeypatch)
    original = path.read_bytes()
    validator.audit_existing([stem])
    assert path.read_bytes() == original
    if change == "replace_figure":
        (artifacts / "figures/001-density.png").write_bytes(b"replaced figure")
    elif change == "remove_pair":
        (artifacts / "figures/001-density.png").unlink()
        (artifacts / "figures/001-density.json").unlink()
    elif change == "run_receipt":
        run_path = artifacts / "runs/0.json"
        run = json.loads(run_path.read_text())
        run["seconds"] = 123.0
        run_path.write_text(json.dumps(run))
    elif change == "helper":
        inputs["helper.py"] = "changed-helper-hash"
    else:
        book_path = tmp_path / "notebooks" / (stem + ".ipynb")
        book = nbformat.read(book_path, as_version=4)
        book.cells[0].outputs.append(nbformat.v4.new_output("stream", name="stdout", text="stale table"))
        nbformat.write(book, book_path)
    with pytest.raises(ValueError, match=message):
        validator.audit_existing([stem])
    assert path.read_bytes() == original


def test_cfa_requires_both_recorded_fresh_marginal_chains(tmp_path):
    artifacts, runs = fixture(tmp_path)
    for run in runs:
        run["class"] = "UnivariateAnalysis"
    cfa = {"name": "CFA", "class": "CoincidentFrequencyAnalysis", "status": "completed",
           "runId": "fresh-CFA", "source": {"sha256": "raw-hash"}}
    runs.append(cfa)
    with pytest.raises(ValueError, match="both fresh marginal chains"):
        validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)
    cfa["marginalChains"] = {axis: {"runId": run["runId"], "name": run["name"], "outputDraws": 10000}
                             for axis, run in zip(("X", "Y"), runs)}
    validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)
    cfa["marginalChains"]["Y"]["runId"] = "old-kernel-run"
    with pytest.raises(ValueError, match="both fresh marginal chains"):
        validator.audit_artifacts("02_test", artifacts, runs, root=tmp_path)
