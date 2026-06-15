from __future__ import annotations

from pathlib import Path
import os


def resolve_bestfit_dll() -> Path:
    """Return the preferred RMC.BestFit.dll path.

    Preference order:
    1. RMC_BESTFIT_DLL, when the user pins a specific build.
    2. The local RMC-BestFit source build, which keeps BestFit and Numerics paired.
    3. The Beta-3 release bundle, useful for stable demo runs.
    4. The local dev clone, useful only when intentionally testing development builds.
    """
    candidates = [
        os.environ.get("RMC_BESTFIT_DLL", ""),
        r"C:\GIT\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\RMC.BestFit.dll",
        r"C:\GIT\RMC-BestFit Version 2.0 (Beta-3)\Release\Libraries\RMC.BestFit.dll",
        r"C:\GIT\RMC-BestFit-Dev\RMC.BestFit\bin\Release\RMC.BestFit.dll",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("RMC.BestFit.dll not found. Set RMC_BESTFIT_DLL environment variable.")


def resolve_numerics_dll() -> Path:
    """Return the preferred Numerics.dll path.

    BestFit depends on Numerics. Prefer the Numerics.dll shipped beside the
    selected BestFit build before falling back to a standalone Numerics build.
    """
    candidates = [
        os.environ.get("RMC_NUMERICS_DLL", ""),
        r"C:\GIT\RMC-BestFit\src\RMC.BestFit\bin\Debug\net10.0\Numerics.dll",
        r"C:\GIT\RMC-BestFit Version 2.0 (Beta-3)\Release\Libraries\Numerics.dll",
        r"C:\GIT\RMC-BestFit-Dev\RMC.BestFit\bin\Release\Numerics.dll",
        r"C:\GIT\Numerics\Numerics\bin\Release\Numerics.dll",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError("Numerics.dll not found. Set RMC_NUMERICS_DLL environment variable.")


def convert_to_dotnet_array(values):
    """Convert a Python iterable of numeric values to System.Double[] for .NET APIs."""
    import System

    arr = list(float(v) for v in values)
    return System.Array[System.Double](arr)


def convert_to_donet_array(values):
    """Backward-compatible alias for the original misspelled helper name."""
    return convert_to_dotnet_array(values)
