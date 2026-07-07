"""Helper functions used by notebooks in this repository."""

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
    """Convert a Python list into a 1D .NET array of doubles.

    Requires that the Numerics .NET runtime has already been loaded
    (i.e., clr.AddReference has been called)."""
    from System import Array, Double


    arr = list(float(v) for v in values)
    return Array[Double](arr)

def convert_to_dotnet_2d_array(matrix):
    """Convert a 2D NumPy array into a .NET 2D array of doubles.

    Requires that the Numerics .NET runtime has already been loaded
    (i.e., clr.AddReference has been called).
    """
    from System import Array, Double

    rows, cols = matrix.shape
    net_array = Array.CreateInstance(Double, rows, cols)
    for i in range(rows):
        for j in range(cols):
            net_array[i, j] = float(matrix[i, j])
    return net_array
