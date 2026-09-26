"""Run the visible notebook workflows in independent kernels from raw inputs."""
from pathlib import Path
import json
import sys
from validate_notebooks import main

if __name__ == "__main__":
    if sys.argv[1:] == ["--list"]:
        groups = json.loads((Path(__file__).resolve().parents[1] / "curriculum-cases.json").read_text())
        for group in groups:
            for name in group["names"]:
                print(f"{group['notebook']}: {group['slug']} | {name}")
        print(f"{sum(len(g['names']) for g in groups)} selected cases; execute by notebook, including its dependencies")
    else:
        raise SystemExit(main())
