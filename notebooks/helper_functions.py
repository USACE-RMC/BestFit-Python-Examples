"""Helper functions used by notebooks in this repository."""

from __future__ import annotations
from pathlib import Path
import os
from typing import Union

def resolve_bestfit_dll() -> Path:
    """Return the preferred RMC.BestFit.dll path.

    Searches for the RMC.BestFit.dll file in order of preference:
    1. Environment variable RMC_BESTFIT_DLL (for user-pinned specific builds)
    2. Local RMC-BestFit source build (keeps BestFit and Numerics paired)
    3. Beta-3 release bundle (useful for stable demo runs)
    4. Local dev clone (useful for testing development builds)

    Returns:
        Path: Absolute path to the RMC.BestFit.dll file.

    Raises:
        FileNotFoundError: If no valid DLL is found. Set the RMC_BESTFIT_DLL 
            environment variable to the full path of your DLL and try again.
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
    raise FileNotFoundError(
        "RMC.BestFit.dll not found in any candidate location. "
        "Set the RMC_BESTFIT_DLL environment variable to the full path of your DLL. "
        f"Searched: {[c for c in candidates if c]}"
    )


def resolve_numerics_dll() -> Path:
    """Return the preferred Numerics.dll path.

    Searches for the Numerics.dll file in order of preference. BestFit depends 
    on Numerics, so this function prefers the Numerics.dll shipped beside the 
    selected BestFit build before falling back to a standalone Numerics build.

    Returns:
        Path: Absolute path to the Numerics.dll file.

    Raises:
        FileNotFoundError: If no valid DLL is found. Set the RMC_NUMERICS_DLL 
            environment variable to the full path of your DLL and try again.
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
    raise FileNotFoundError(
        "Numerics.dll not found in any candidate location. "
        "Set the RMC_NUMERICS_DLL environment variable to the full path of your DLL. "
        f"Searched: {[c for c in candidates if c]}"
    )


def convert_to_dotnet_array(values: list[float]) -> object:
    """Convert a Python list into a 1D .NET array of doubles.

    This function enables seamless interoperability between Python and .NET by 
    converting native Python lists to .NET arrays, which are required by many 
    BestFit and Numerics methods.

    Args:
        values: A Python list or iterable of numeric values to be converted.

    Returns:
        object: A .NET Array[Double] containing the converted values.

    Raises:
        NameError: If the Numerics .NET runtime has not been loaded 
            (clr.AddReference has not been called).

    Note:
        Requires that the Numerics .NET runtime has already been loaded
        via clr.AddReference.
    """
    from System import Array, Double

    arr = list(float(v) for v in values)
    return Array[Double](arr)

def convert_to_dotnet_2d_array(matrix) -> object:
    """Convert a 2D NumPy array into a .NET 2D array of doubles.

    This function enables conversion of NumPy matrices to .NET 2D arrays, 
    which are required by certain BestFit and Numerics methods.

    Args:
        matrix: A 2D NumPy array with numeric values.

    Returns:
        object: A .NET 2D Array[Double] containing the converted values.

    Raises:
        NameError: If the Numerics .NET runtime has not been loaded.
        AttributeError: If the input is not a NumPy array with a .shape attribute.

    Note:
        Requires that the Numerics .NET runtime has already been loaded.
    """
    from System import Array, Double

    rows, cols = matrix.shape
    net_array = Array.CreateInstance(Double, rows, cols)
    for i in range(rows):
        for j in range(cols):
            net_array[i, j] = float(matrix[i, j])
    return net_array
