"""Load one explicitly pinned BestFit/Numerics runtime in a fresh kernel."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def file_hash(path: Path) -> str:
    """Return a file's SHA256 without loading an assembly."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_runtime(root: Path | None = None, environ: dict | None = None) -> dict:
    """Verify the complete local pair; never search global package caches."""
    root = Path(root or ROOT).resolve()
    environ = os.environ if environ is None else environ
    directory = Path(environ.get("BESTFIT_RUNTIME_DIR", root / ".runtime")).resolve()
    receipt = directory / "provenance.json"
    if not receipt.is_file():
        raise FileNotFoundError(
            f"No verified BestFit runtime at {directory}. Run python scripts/bootstrap_runtime.py."
        )
    provenance = json.loads(receipt.read_text(encoding="utf-8"))
    lock = json.loads((root / "runtime-lock.json").read_text(encoding="utf-8"))
    if provenance.get("schemaVersion") != 1:
        raise RuntimeError("Unsupported runtime provenance schema")
    if provenance.get("sourceCommit") != lock["bestFitCommit"]:
        raise RuntimeError("BestFit source revision differs from runtime-lock.json; rebuild the runtime")
    for actual, expected in (("bestFitVersion", "bestFitAssemblyVersion"),
                             ("numericsVersion", "numericsAssemblyVersion"),
                             ("targetFramework", "targetFramework")):
        if expected in lock and provenance.get(actual) != lock[expected]:
            raise RuntimeError(f"Runtime {actual} differs from runtime-lock.json")
    paths = {"bestfit": directory / "lib" / "RMC.BestFit.dll",
             "numerics": directory / "lib" / "Numerics.dll"}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(f"Missing {path.name}; run python scripts/bootstrap_runtime.py")
        if file_hash(path) != provenance.get("fileHashes", {}).get(path.name):
            raise RuntimeError(f"Assembly hash mismatch for {path.name}; rebuild the runtime")
    return {**paths, "provenance": provenance, "directory": directory}


def assembly_identity(library: Path, runtime_config: Path | None = None) -> dict:
    """Load and inspect the pair, rejecting an already-loaded different runtime."""
    from pythonnet import get_runtime_info, load

    if get_runtime_info() is None:
        load("coreclr", runtime_config=str(runtime_config or ROOT / "dotnet" / "bestfit.runtimeconfig.json"))
    import clr
    from System import AppDomain, Environment
    from System.Reflection import AssemblyName

    if int(Environment.Version.Major) != 10:
        raise RuntimeError("These examples require .NET 10. Restart with a fresh kernel and the pinned runtime.")
    library = Path(library).resolve()
    for assembly in AppDomain.CurrentDomain.GetAssemblies():
        name = str(assembly.GetName().Name)
        if name in {"Numerics", "RMC.BestFit"}:
            if Path(str(assembly.Location)).resolve() != library / f"{name}.dll":
                raise RuntimeError(f"{name} is already loaded from another path. Restart the kernel.")
    versions = {}
    for name, key in (("Numerics", "numericsVersion"), ("RMC.BestFit", "bestFitVersion")):
        path = library / f"{name}.dll"
        versions[key] = str(AssemblyName.GetAssemblyName(str(path)).Version)
        assembly = clr.AddReference(str(path))
        if name == "RMC.BestFit":
            attributes = [a for a in assembly.GetCustomAttributesData()
                          if str(a.AttributeType.FullName) == "System.Runtime.Versioning.TargetFrameworkAttribute"]
            versions["targetFramework"] = str(attributes[0].ConstructorArguments[0].Value)
    return versions


def load_bestfit() -> dict:
    """Verify bytes and metadata before returning the loaded runtime receipt."""
    resolved = resolve_runtime()
    observed = assembly_identity(resolved["directory"] / "lib")
    for key, value in observed.items():
        if value != resolved["provenance"][key]:
            raise RuntimeError(f"Loaded {key} differs from the runtime receipt; restart and rebuild")
    return resolved["provenance"]
