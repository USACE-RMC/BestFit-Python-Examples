"""Runtime provenance must reject mixed or changed assemblies before use."""
import hashlib
import json
from pathlib import Path

import pytest


def runtime_fixture(tmp_path):
    library = tmp_path / ".runtime" / "lib"
    library.mkdir(parents=True)
    hashes = {}
    for name in ("RMC.BestFit.dll", "Numerics.dll"):
        path = library / name
        path.write_bytes(name.encode())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    identity = {"schemaVersion": 1, "sourceCommit": "abc123", "fileHashes": hashes,
                "bestFitVersion": "2.0.0.0", "numericsVersion": "2.2.0.0",
                "targetFramework": ".NETCoreApp,Version=v10.0"}
    (tmp_path / ".runtime" / "provenance.json").write_text(json.dumps(identity))
    (tmp_path / "runtime-lock.json").write_text(json.dumps({"bestFitCommit": "abc123"}))
    return library


def test_changed_assembly_rejected_before_loading(tmp_path):
    from bestfit_examples.runtime import resolve_runtime
    library = runtime_fixture(tmp_path)
    (library / "Numerics.dll").write_bytes(b"changed assembly")
    with pytest.raises(RuntimeError, match="hash"):
        resolve_runtime(tmp_path, environ={})


def test_verified_pair_resolves_as_one_runtime(tmp_path):
    from bestfit_examples.runtime import resolve_runtime
    library = runtime_fixture(tmp_path)
    resolved = resolve_runtime(tmp_path, environ={})
    assert resolved["bestfit"] == library / "RMC.BestFit.dll"
    assert resolved["numerics"] == library / "Numerics.dll"


def test_wrong_source_revision_rejected(tmp_path):
    from bestfit_examples.runtime import resolve_runtime
    runtime_fixture(tmp_path)
    (tmp_path / "runtime-lock.json").write_text('{"bestFitCommit":"different"}')
    with pytest.raises(RuntimeError, match="revision"):
        resolve_runtime(tmp_path, environ={})


def test_missing_runtime_does_not_search_global_cache(tmp_path):
    from bestfit_examples.runtime import resolve_runtime
    with pytest.raises(FileNotFoundError, match="bootstrap_runtime"):
        resolve_runtime(tmp_path, environ={})


def test_explicit_runtime_directory_is_also_verified(tmp_path):
    from bestfit_examples.runtime import resolve_runtime
    runtime_fixture(tmp_path)
    resolved = resolve_runtime(tmp_path, environ={"BESTFIT_RUNTIME_DIR": str(tmp_path / ".runtime")})
    assert resolved["provenance"]["sourceCommit"] == "abc123"
