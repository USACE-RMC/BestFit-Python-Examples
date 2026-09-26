"""Build notebooks from readable Python sources, never from saved results."""
from pathlib import Path
import argparse
import hashlib
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def build(path):
    cells, lines, kind = [], [], None
    def append():
        if kind is None:
            return
        source = "\n".join(lines).strip()
        if kind == "markdown":
            source = "\n".join(line[2:] if line.startswith("# ") else line[1:] if line.startswith("#") else line for line in source.splitlines())
            cell = nbformat.v4.new_markdown_cell(source)
        else:
            cell = nbformat.v4.new_code_cell(source)
        cell["id"] = hashlib.sha256((path.name + str(len(cells)) + source).encode()).hexdigest()[:12]
        cells.append(cell)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# %%"):
            append()
            kind = "markdown" if "[markdown]" in line else "code"
            lines = []
        else:
            lines.append(line)
    append()
    return nbformat.v4.new_notebook(cells=cells, metadata={
        "kernelspec": {"display_name": "BestFit examples", "language": "python", "name": "bestfit-examples"},
        "language_info": {"name": "python", "version": "3.12"}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebooks", nargs="*")
    args = parser.parse_args()
    for path in sorted((ROOT / "scripts/notebook_sources").glob("*.py")):
        if args.notebooks and path.stem not in args.notebooks:
            continue
        book = build(path)
        nbformat.write(book, ROOT / "notebooks" / (path.stem + ".ipynb"))
        print(path.stem, len(book.cells), "cells")


if __name__ == "__main__":
    main()
