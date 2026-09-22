"""Verified saved walkthroughs, with an explicit original-settings rerun path."""
from __future__ import annotations
from dataclasses import dataclass
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Case:
    """Visible settings, numerical summaries and a small named-plot interface."""
    data: dict

    @property
    def settings(self):
        import pandas as pd
        important={"Type","NumberOfChains","ThinningInterval","WarmupIterations","Iterations","UseSimulationDefaults",
                   "PRNGSeed","CredibleIntervalWidth","PointEstimator","OutputLength"}
        return pd.DataFrame([{"Setting":k,"Saved choice":v} for k,v in self.data["settings"].items()
                             if (not k.startswith("BayesianAnalysis.") or k.split(".")[-1] in important)
                             and k not in {"Saved project","IsEstimated"}])

    @property
    def parameters(self):
        import pandas as pd
        return pd.DataFrame(self.data.get("parameters", []))

    @property
    def metrics(self):
        import pandas as pd
        return pd.Series(self.data.get("metrics", {}), name=self.data["name"])

    @property
    def candidates(self):
        import pandas as pd
        return pd.DataFrame(self.data.get("candidates", []))

    def plot(self, name="frequency"):
        from bestfit_plots import render_plot
        return render_plot(self.data["plots"][name])

    def show(self, name="frequency"):
        from IPython.display import display
        import matplotlib.pyplot as plt
        figure = self.plot(name)
        display(figure)
        plt.close(figure)

    def frequency_table(self, probabilities=(.5,.1,.01,.002,.001)):
        """Select saved ordinates; never interpolate or refit for a table."""
        import pandas as pd
        spec = self.data["plots"]["frequency"]
        curves = [s for s in spec["series"] if s["kind"] == "line"]
        rows = []
        for probability in probabilities:
            record = {"AEP":probability}
            for curve in curves:
                found = [y for x,y in zip(curve["x"],curve["y"]) if abs(x-probability)<1e-12]
                if found:
                    record[curve["name"]] = found[0]
            if len(record)>1:
                rows.append(record)
        return pd.DataFrame(rows)


def saved_case(slug, name, *, table=None, run=False, root=None):
    """Read one checked result; CLR is needed only for the explicit rerun branch."""
    root = Path(root or ROOT)
    manifest = json.loads((root/"results"/"manifest.json").read_text(encoding="utf-8"))
    matches = [c for c in manifest["cases"] if c["slug"]==slug and c["name"]==name and (table is None or c["table"]==table)]
    if len(matches)!=1:
        raise KeyError(f"Expected one saved case for {slug}/{name}; found {len(matches)}")
    entry = matches[0]
    content = (root/"results"/entry["file"]).read_bytes()
    if hashlib.sha256(content).hexdigest()!=entry["sha256"]:
        raise ValueError(f"Saved result checksum mismatch: {name}")
    data = json.loads(gzip.decompress(content))
    lock = json.loads((root/"runtime-lock.json").read_text(encoding="utf-8"))
    if data["runtimeCommit"]!=lock["bestFitCommit"]:
        raise ValueError("Saved result software revision differs from runtime-lock.json; rebuild validated results")
    sources = json.loads((root/"data"/"source-manifest.json").read_text(encoding="utf-8"))
    source = sources["projects"][slug]
    if data["sourceSha256"] != source["source_sha256"]:
        raise ValueError("Saved result source checksum differs from frozen project")
    if "export_sha256" in source:
        path = root/"data"/source["export_relative_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest()!=source["export_sha256"]:
            raise ValueError("Frozen project export checksum mismatch")
    if run:
        from .analysis import rerun_analysis
        from .snapshot import analysis_snapshot
        receipt_path = root/"output"/"reruns"/(entry["file"].replace(".json.gz", "-receipt.json"))
        result = rerun_analysis(slug, entry["table"], name, receipt_path, return_restored=True)
        data = analysis_snapshot(slug, result["restored"])
        data["origin"] = "fresh-run"
        data["receipt"] = result["receipt"]
    return Case(data)
