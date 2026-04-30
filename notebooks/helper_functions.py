from __future__ import annotations

from pathlib import Path
import os


def resolve_bestfit_dll() -> Path:
    candidates = [
        os.environ.get("RMC_BESTFIT_DLL", ""),
        r"C:\GIT\RMC-BestFit Version 2.0 (Beta-3)\Release\Libraries\RMC.BestFit.dll",
        r"C:\GIT\RMC-BestFit-Dev\RMC.BestFit\bin\Release\RMC.BestFit.dll",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("RMC.BestFit.dll not found. Set RMC_BESTFIT_DLL environment variable.")


def resolve_numerics_dll() -> Path:
    candidates = [
        os.environ.get("RMC_NUMERICS_DLL", ""),
        r"C:\GIT\RMC-BestFit Version 2.0 (Beta-3)\Release\Libraries\Numerics.dll",
        r"C:\GIT\Numerics\Numerics\bin\Release\Numerics.dll",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("Numerics.dll not found. Set RMC_NUMERICS_DLL environment variable.")


def convert_to_donet_array(values):
    """Convert a Python iterable of numeric values to System.Double[] for .NET APIs."""
    import System

    arr = list(float(v) for v in values)
    return System.Array[System.Double](arr)
