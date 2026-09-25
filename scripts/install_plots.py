"""Install the publicly available plotting package pinned by runtime-lock.json."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def git_environment(environ=None):
    """Enable Windows long paths for child Git processes without global changes."""
    child = dict(os.environ if environ is None else environ)
    count = int(child.get("GIT_CONFIG_COUNT", "0"))
    child[f"GIT_CONFIG_KEY_{count}"] = "core.longpaths"
    child[f"GIT_CONFIG_VALUE_{count}"] = "true"
    child["GIT_CONFIG_COUNT"] = str(count + 1)
    return child


def main():
    lock = json.loads((ROOT / "runtime-lock.json").read_text(encoding="utf-8"))
    requirement = (f"bestfit-plots @ git+{lock['bestFitRepository']}@{lock['bestFitCommit']}"
                   "#subdirectory=skills/bestfit-frequency")
    # Upstream snapshots share a package version. Force this exact revision
    # even when a different 0.1.0 is installed; examples requirements supply
    # the NumPy/Matplotlib dependencies without upgrading them a second time.
    subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", requirement],
                   env=git_environment(), check=True)


if __name__ == "__main__":
    main()
