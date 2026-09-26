"""Offline authoring audit for headless notebooks 03–06.

Run after scripts/validate_notebooks.py has produced fresh raw-only receipts.
This file is intentionally outside the notebook/runtime package: saved projects
are authoring evidence, never inputs to a notebook run.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bestfit_examples.project_data import load_project  # noqa: E402


NOTEBOOKS = {
    "03_stationary_information_expansion": ("viglione-et-al-2013",),
    "04_nonstationary_univariate": ("nsffa-brays-bayou-texas",),
    "05_bulletin_17c": ("bulletin-17c-examples",),
    "06_advanced_univariate": (
        "point-process-examples",
        "mixture-distribution-examples",
        "mixed-population-examples",
    ),
}
TABLE_MODELS = {
    "<Univariate Distribution>": "UnivariateDistribution",
    "<Bulletin 17C>": "Bulletin17CDistribution",
    "<Point Process>": "PointProcess",
    "<Mixture Distribution>": "MixtureDistribution",
}
COMPARE_BAYESIAN = (
    "Type NumberOfChains ThinningInterval WarmupIterations Iterations "
    "UseSimulationDefaults PRNGSeed InitialIterations Jump JumpThreshold "
    "SnookerThreshold Noise Scale Beta MaxTreeDepth "
    "UseAdvancedSimulationDefaults CredibleIntervalWidth OutputLength PointEstimator"
).split()
MODEL_DYNAMIC = {
    "Value",  # post-fit parameter estimate, not a prior or bound
    "Weights",  # fitted mixture weights
    "Parameters",  # fitted vector on a distribution element
    "OwnerName",  # serialized label, not a model constraint
}
DIST_CONFIG = {"Type", "IsZeroInflated", "ZeroWeight", "XTransform",
               "ProbabilityTransform", "Distributions", "Threshold"}
errors: list[str] = []
counts = {"analyses": 0, "bayesian": 0, "models": 0, "parameters": 0,
          "composites": 0, "ordinates": 0}


def norm(value: str | int | float | bool | None):
    if value is None:
        return None
    value = str(value)
    if value.lower() in {"true", "false"}:
        return value.lower()
    try:
        number = float(value)
    except ValueError:
        return value
    if math.isnan(number):
        return "nan"
    if math.isinf(number):
        return str(number)
    return number


def eq(label: str, wanted, actual):
    if isinstance(wanted, (float, int)) and isinstance(actual, (float, int)):
        same = math.isclose(wanted, actual, rel_tol=2e-13, abs_tol=0.0)
    else:
        same = wanted == actual
    if not same:
        errors.append(f"{label}: saved={wanted!r}; fresh={actual!r}")


def attrs(label: str, saved: ET.Element, fresh: ET.Element,
          *, skip: frozenset[str] = frozenset()):
    eq(f"{label}.tag", saved.tag, fresh.tag)
    keys = set(saved.attrib) | set(fresh.attrib)
    if saved.tag == "ParameterPenalty":
        skip |= frozenset({"Name"})  # same penalty, different UI prefix
    for key in sorted(keys - skip):
        eq(f"{label}.{key}", norm(saved.get(key)), norm(fresh.get(key)))


def model_tree(label: str, saved: ET.Element, fresh: ET.Element):
    """Compare active configuration, excluding only fitted coordinates."""
    attrs(label, saved, fresh, skip=frozenset({"IsEstimated"}))
    if saved.tag == "ModelParameter":
        counts["parameters"] += 1
    sc, fc = list(saved), list(fresh)
    eq(f"{label}.child_count", len(sc), len(fc))
    for i, (s, f) in enumerate(zip(sc, fc)):
        path = f"{label}/{s.tag}[{i}]"
        direct_skip = frozenset(MODEL_DYNAMIC)
        if s.tag == "Distribution":
            # Only the model root's direct Distribution is a fitted point
            # estimate. Nested Distributions are priors and are compared fully.
            direct_skip |= frozenset((set(s.attrib) | set(f.attrib)) - DIST_CONFIG)
        attrs(path, s, f, skip=direct_skip)
        if s.tag == "ModelParameter":
            counts["parameters"] += 1
        # Do not compare text in fitted-vector elements. Quantile priors and
        # trend coefficients are recursively compared, including their prior
        # family, bounds, IsPositive and IsFixed flags.
        if s.tag not in {"Distribution"}:
            recurse_children(path, s, f)


def recurse_children(label: str, saved: ET.Element, fresh: ET.Element):
    sc, fc = list(saved), list(fresh)
    eq(f"{label}.child_count", len(sc), len(fc))
    for i, (s, f) in enumerate(zip(sc, fc)):
        path = f"{label}/{s.tag}[{i}]"
        attrs(path, s, f, skip=frozenset(MODEL_DYNAMIC))
        if s.tag == "ModelParameter":
            counts["parameters"] += 1
        recurse_children(path, s, f)


def bayesian(label: str, saved_xml: str, fresh: ET.Element):
    saved = ET.fromstring(saved_xml)
    eq(f"{label}.tag", saved.tag, fresh.tag)
    for key in COMPARE_BAYESIAN:
        eq(f"{label}.{key}", norm(saved.get(key)), norm(fresh.get(key)))
    counts["bayesian"] += 1


def ordinates(label: str, saved_text: str, fresh: ET.Element):
    wanted = [float(v) for v in saved_text.split("|")]
    actual = [float(v) for v in (fresh.text or "").split("|")]
    eq(f"{label}.count", len(wanted), len(actual))
    for i, (w, a) in enumerate(zip(wanted, actual)):
        eq(f"{label}[{i}]", w, a)
    counts["ordinates"] += 1


def composite(label: str, row: dict, analysis: ET.Element):
    for key in ("CompositeDistributionType", "ModelAverageMethod", "Dependency", "IsMaximum"):
        wanted = bool(row[key]) if key == "IsMaximum" else row[key]
        eq(f"{label}.{key}", norm(wanted), norm(analysis.get(key)))
    saved_children = ET.fromstring(row["Analyses"])
    fresh_children = analysis.find("Analyses")
    eq(f"{label}.child_count", len(saved_children), len(fresh_children))
    for i, (s, f) in enumerate(zip(saved_children, fresh_children)):
        eq(f"{label}.child[{i}].tag", s.tag, f.tag)
        # Model-average weights are newly inferred from fresh child DIC; the
        # two mixed-population weights are intentional saved configuration.
        if row["CompositeDistributionType"] != "ModelAverage":
            eq(f"{label}.child[{i}].Weight", norm(s.get("Weight")), norm(f.get("Weight")))
        # Fresh CompositeAnalysis XML omits the child name; verify source-cell
        # literal membership separately below for each saved composite.
    counts["composites"] += 1


for stem, slugs in NOTEBOOKS.items():
    notebook = nbformat.read(ROOT / "notebooks" / f"{stem}.ipynb", as_version=4)
    source = "\n".join(c.source for c in notebook.cells)
    digest = hashlib.sha256(source.encode()).hexdigest()
    receipt = json.loads((ROOT / "validation" / "headless" / f"{stem}.json").read_text(encoding="utf-8"))
    eq(f"{stem}.status", "passed", receipt["status"])
    eq(f"{stem}.sourceSha256", digest, receipt["sourceSha256"])
    rows = {}
    for slug in slugs:
        project = load_project(slug)
        for table in (*TABLE_MODELS, "<Composite Distribution>"):
            if table in project["tables"]:
                for row in project["tables"][table]["rows"]:
                    rows[row["Name"]] = (table, row)
    for result in receipt["analyses"]:
        name = result["name"]
        if name not in rows:
            errors.append(f"{stem}/{name}: no saved case")
            continue
        table, row = rows[name]
        label = f"{stem}/{name}"
        analysis = ET.fromstring(result["analysisSettings"])
        counts["analyses"] += 1
        # Top-level row fields are the active settings. AnalysisXml may contain
        # stale nested model, Bayesian or results serialization and is not used
        # as an authority for those comparisons. B17C's UncertaintyMethod has
        # no top-level column, so its root AnalysisXml attribute is authoritative.
        bayesian(label + ".BayesianAnalysis", row["BayesianAnalysis"], analysis.find("BayesianAnalysis"))
        ordinates(label + ".ProbabilityOrdinates", row["ProbabilityOrdinates"], analysis.find("ProbabilityOrdinates"))
        if table == "<Composite Distribution>":
            composite(label, row, analysis)
        else:
            saved_model = ET.fromstring(row[TABLE_MODELS[table]])
            fresh_model = ET.fromstring(result["modelSettings"])
            model_tree(label + ".model", saved_model, fresh_model)
            counts["models"] += 1
            if table == "<Bulletin 17C>":
                eq(label + ".UncertaintyMethod", norm(ET.fromstring(row["AnalysisXml"]).get("UncertaintyMethod")),
                   norm(analysis.get("UncertaintyMethod")))

source_04 = nbformat.read(ROOT / "notebooks" / "04_nonstationary_univariate.ipynb", as_version=4)
source_06 = nbformat.read(ROOT / "notebooks" / "06_advanced_univariate.ipynb", as_version=4)
source_text_04 = "\n".join(c.source for c in source_04.cells)
source_text_06 = "\n".join(c.source for c in source_06.cells)
for term in ("NSFFA - Linear - Logistic", "NSFFA - Logistic - Logistic", "NSFFA - Step - Logistic"):
    if term not in source_text_04:
        errors.append(f"04 composite missing literal child {term}")
for term in ("Full POR Snow Driven", "Full POR Rainfall Driven",
             "Sub-Sample - Snow Driven", "Sub-Sample - Rain Driven"):
    if term not in source_text_06:
        errors.append(f"06 composite missing literal child {term}")

print("Audited", counts)
if errors:
    print("DRIFT:")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)
print("PASS: active saved sampler, model, priors, parameter flags/bounds, trend, composites and ordinates match fresh receipts")
