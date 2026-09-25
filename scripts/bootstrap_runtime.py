"""Build the exact source revision and record the two assemblies as one runtime.

Use --bestfit-source for an existing compatible checkout, or allow a local clone
of the locked revision. This script does not search machine-wide DLL caches.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bestfit_examples.runtime import assembly_identity, file_hash


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, **kwargs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bestfit-source", type=Path)
    parser.add_argument("--install-plots", action="store_true", help="Install the canonical plotting package from this same checkout")
    args = parser.parse_args()
    lock = json.loads((ROOT / "runtime-lock.json").read_text(encoding="utf-8"))
    source = (args.bestfit_source or ROOT / ".runtime" / "source").resolve()
    git = ["git", "-c", "core.longpaths=true", "-c", f"safe.directory={source.as_posix()}", "-C", str(source)]
    if not source.exists() and args.bestfit_source is None:
        run(["git", "clone", "--no-checkout", lock["bestFitRepository"], str(source)])
        run([*git, "checkout", "--detach", lock["bestFitCommit"]])
    revision = run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if revision != lock["bestFitCommit"]:
        raise RuntimeError(f"Source revision {revision} differs from locked {lock['bestFitCommit']}")
    # Do not silently build modified numerical sources. Additive API/plot files
    # do not affect this portable project; a committed revision is pinned later.
    core_changes = run([*git, "status", "--porcelain", "--", "src/RMC.BestFit", "Directory.Build.props",
                        "Directory.Packages.props"], capture_output=True, text=True).stdout.strip()
    if core_changes:
        raise RuntimeError("Portable BestFit source has uncommitted changes; use the locked clean source")
    library = ROOT / ".runtime" / "lib"
    library.mkdir(parents=True, exist_ok=True)
    run(["dotnet", "build", str(ROOT / "dotnet" / "BestFitRuntime.csproj"), "-c", "Release",
         f"-p:BestFitSourceRoot={source.as_posix()}", "-p:UseLocalRmcNumerics=false", "-o", str(library), "-v:minimal"])
    identity = assembly_identity(library)
    for actual, expected in (("bestFitVersion", "bestFitAssemblyVersion"),
                             ("numericsVersion", "numericsAssemblyVersion"),
                             ("targetFramework", "targetFramework")):
        if identity[actual] != lock[expected]:
            raise RuntimeError(f"Built {actual} {identity[actual]} differs from lock {lock[expected]}")
    receipt = {"schemaVersion": 1, "sourceCommit": revision, **identity,
               "fileHashes": {name: file_hash(library / name) for name in ("RMC.BestFit.dll", "Numerics.dll")}}
    (ROOT / ".runtime" / "provenance.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if args.install_plots:
        run([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps",
             str(source / "skills" / "bestfit-frequency")])
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
