"""Windows Git options must remain local to the plotting installer process."""
import importlib.util
from pathlib import Path


def installer():
    path = Path(__file__).resolve().parents[1] / "scripts/install_plots.py"
    spec = importlib.util.spec_from_file_location("install_plots", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_long_paths_do_not_change_parent_environment():
    parent = {"PATH": "preserved"}
    child = installer().git_environment(parent)
    assert parent == {"PATH": "preserved"}
    assert child["PATH"] == parent["PATH"]
    assert child["GIT_CONFIG_COUNT"] == "1"
    assert child["GIT_CONFIG_KEY_0"] == "core.longpaths"
    assert child["GIT_CONFIG_VALUE_0"] == "true"


def test_existing_git_options_are_preserved():
    parent = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.sslVerify",
              "GIT_CONFIG_VALUE_0": "true"}
    child = installer().git_environment(parent)
    assert child["GIT_CONFIG_COUNT"] == "2"
    assert child["GIT_CONFIG_KEY_0"] == "http.sslVerify"
    assert child["GIT_CONFIG_VALUE_0"] == "true"
    assert child["GIT_CONFIG_KEY_1"] == "core.longpaths"
    assert child["GIT_CONFIG_VALUE_1"] == "true"
