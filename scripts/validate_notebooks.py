"""Execute walkthroughs in independent kernels using this interpreter, with receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
NOTEBOOKS=("00_time_series_data", "01_input_data", "02_distribution_fitting",
           "03_stationary_information_expansion", "04_nonstationary_univariate", "05_bulletin_17c",
           "06_advanced_univariate", "07_bivariate_analysis", "08_coincident_frequency", "09_rating_curves",
           "10_classic_time_series", "11_regression")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebooks",nargs="*",default=list(NOTEBOOKS))
    parser.add_argument("--write",action="store_true",help="Retain intentional output in the notebooks")
    args=parser.parse_args()
    kernel_root=ROOT/".runtime"/"jupyter"
    kernel=kernel_root/"kernels"/"bestfit-examples"
    kernel.mkdir(parents=True,exist_ok=True)
    (kernel/"kernel.json").write_text(json.dumps({"argv":[sys.executable,"-X","utf8","-m","ipykernel_launcher","-f","{connection_file}"],
                                                "display_name":"BestFit examples","language":"python"}))
    os.environ["JUPYTER_PATH"]=str(kernel_root)+os.pathsep+os.environ.get("JUPYTER_PATH", "")
    os.environ["JUPYTER_RUNTIME_DIR"]=str(ROOT/".runtime"/"jupyter-runtime")
    os.environ["IPYTHONDIR"]=str(ROOT/".runtime"/"ipython")
    os.environ["PYTHONUTF8"]="1"
    import nbformat
    from nbclient import NotebookClient
    destination=ROOT/"validation"/"notebooks"
    destination.mkdir(parents=True,exist_ok=True)
    for stem in args.notebooks:
        if stem not in NOTEBOOKS:
            raise ValueError(f"Not a curriculum notebook: {stem}")
        path=ROOT/"notebooks"/(stem+".ipynb")
        book=nbformat.read(path,as_version=4)
        nbformat.validate(book)
        start=time.monotonic()
        receipt={"notebook":path.name,"status":"running","python":sys.version.split()[0],"independentKernel":True}
        print(f"Executing {path.name}",flush=True)
        try:
            NotebookClient(book,kernel_name="bestfit-examples",timeout=600,resources={"metadata":{"path":str(ROOT)}}).execute()
            errors=[o for c in book.cells if c.cell_type=="code" for o in c.get("outputs",[]) if o.output_type=="error"]
            if errors:
                raise RuntimeError(f"{len(errors)} notebook errors")
            # Execution timestamps are incidental; retain code, prose and intentional output.
            for cell in book.cells:
                cell.metadata.pop("execution",None)
            if args.write:
                nbformat.write(book,path)
            receipt.update(status="passed",codeCells=sum(c.cell_type=="code" for c in book.cells),
                           errorOutputs=0,notebookSha256=hashlib.sha256(path.read_bytes()).hexdigest())
        except Exception as error:
            receipt.update(status="failed",error=str(error))
            raise
        finally:
            receipt["elapsedSeconds"]=round(time.monotonic()-start,3)
            (destination/(stem+".json")).write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
            print(f"{receipt['status']}: {path.name} ({receipt['elapsedSeconds']} s)",flush=True)


if __name__=="__main__":main()
