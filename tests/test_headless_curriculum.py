"""The teaching contract: notebook code must construct and execute, not restore."""
import ast
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_twelve_sources_have_visible_construction_and_execution():
    sources = sorted((ROOT / "scripts/notebook_sources").glob("*.py"))
    assert len(sources) == 12
    prohibited = {"saved_case", "restore_analysis", "prepare_rerun", "rerun_analysis", "load_project",
                  "run_example", "FromXElement", "RestoreAnalysisResults", "FromByteArray", "Parse"}
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        names = [n.func.id if isinstance(n.func, ast.Name) else n.func.attr if isinstance(n.func, ast.Attribute) else "" for n in calls]
        # DateTime.Parse is a straightforward date conversion, not XML restoration.
        for node in calls:
            if isinstance(node.func, ast.Attribute) and node.func.attr == "Parse":
                assert isinstance(node.func.value, ast.Name) and node.func.value.id == "DateTime", path
        assert not (set(names) & (prohibited - {"Parse"})), path
        assert "load_bestfit" in names and "load_raw" in names, path
        assert "TimeSeries" in names or "DataFrame" in names, path
        if int(path.name[:2]) >= 2:
            assert "RunAsync" in names, path
            assert "record_run" in names, path
        assert not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and
                       any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "RunAsync"
                           for c in ast.walk(n)) for n in ast.walk(tree)), path


def test_generator_reproduces_notebook_sources_without_saved_results():
    spec = importlib.util.spec_from_file_location("create_notebooks", ROOT / "scripts/create_notebooks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path in (ROOT / "scripts/notebook_sources").glob("*.py"):
        expected = module.build(path)
        current = json.loads((ROOT / "notebooks" / (path.stem + ".ipynb")).read_text(encoding="utf-8"))
        assert [c.source for c in expected.cells] == ["".join(c["source"]) for c in current["cells"]]


def test_raw_fixtures_have_no_fitted_objects_or_result_payloads():
    from bestfit_examples.raw import load_raw
    manifest = json.loads((ROOT / "data/raw/manifest.json").read_text(encoding="utf-8"))
    forbidden = {"AnalysisXml", "MCMCResults", "AnalysisResults", "FittedDistributions", "ChronologyAnalysisResults"}
    def check(value):
        if isinstance(value, dict):
            assert not (value.keys() & forbidden)
            for item in value.values():
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)
    for slug in manifest["projects"]:
        raw = load_raw(slug)
        assert set(raw) == {"source", "inputs", "series"}
        check(raw)
