"""Offline authoring-setting parity check for freshly executed notebooks 07–09.

This reviewer tool reads the checksum-verified *historical* source exports and
headless-run receipts. It is never imported by a teaching notebook or staged
raw-only execution workspace. Fitted values/results are deliberately excluded.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from bestfit_examples.project_data import load_project

SOURCE_TABLE = {
    "07_bivariate_analysis": [("bivariate-distribution-examples", "<Bivariate Distribution>"),
                              ("bivariate-distribution-examples", "<Univariate Distribution>")],
    "08_coincident_frequency": [(slug, table) for slug in ("sum-two-normals", "waimea-river-stage-frequency")
                                for table in ("<Bivariate Distribution>", "<Univariate Distribution>",
                                              "<Coincident Frequency>")],
    "09_rating_curves": [(slug, "Rating Curve Analysis") for slug in
                         ("synthetic-rating-curve-examples", "usgs-07024175-mississippi-rating-curve")],
}
MODEL_COLUMN = {"<Bivariate Distribution>": "BivariateDistribution",
                "<Univariate Distribution>": "UnivariateDistribution",
                "Rating Curve Analysis": "RatingCurve"}
ESTIMATED = {"DIC", "WAIC", "WAIC_pD", "LOOIC", "LOO_pD", "LOOIC_SE", "IsEstimated", "ElapsedTime"}
ALIASES = {"Y Marginal - Rho = +0.5": "Y Marginal - Rho =+0.5",
           "Normal Copula - Rho = +0.5": "Normal Copula - Rho =+0.5"}
WAIMEA_SELECTED = {"Normal Copula - Conditional", "CFA - Normal - Conditional",
                   "WaimeaPk - Exact + Historical + RR Prior_RSkew",
                   "MakaweliPk - Cond - Exact"}
issues = []


def check(label, same):
    if not same:
        issues.append(label)


def authoring_parameters(element):
    """Use active top-level model parameters; omit MCMC-derived Value."""
    parent = element.find("Parameters")
    if parent is None:
        return []
    result = []
    for parameter in parent:
        prior = parameter.find("Distribution")
        result.append({"LowerBound": parameter.get("LowerBound"),
                       "UpperBound": parameter.get("UpperBound"),
                       "IsPositive": parameter.get("IsPositive"),
                       "IsFixed": parameter.get("IsFixed"),
                       "Prior": dict(prior.attrib) if prior is not None else None})
    return result


def priors(element):
    parent = element.find("QuantilePriors")
    if parent is None:
        return []
    return [(item.get("Alpha"), dict(item.find("Distribution").attrib)) for item in parent]


for stem, tables in SOURCE_TABLE.items():
    source = {}
    for slug, table in tables:
        project = load_project(slug)  # verifies data/source-manifest.json export hash
        for row in project["tables"][table]["rows"]:
            if stem == "08_coincident_frequency" and slug == "waimea-river-stage-frequency" \
                    and row["Name"] not in WAIMEA_SELECTED:
                continue
            source[row["Name"]] = (slug, table, row)
    receipt = json.loads((ROOT / "validation/headless" / (stem + ".json")).read_text(encoding="utf-8"))
    check(stem + " validation status", receipt["status"] == "passed")
    actual = {ALIASES.get(item["name"], item["name"]): item for item in receipt["analyses"]}
    check(stem + " case roster", set(actual) == set(source))
    for name in set(actual) & set(source):
        run = actual[name]
        _, table, row = source[name]
        analysis = ET.fromstring(run["analysisSettings"])
        old_bayes = ET.fromstring(row["BayesianAnalysis"])
        new_bayes = analysis.find("BayesianAnalysis")
        check(name + " Bayesian node", new_bayes is not None)
        if new_bayes is not None:
            for key, value in old_bayes.attrib.items():
                if key not in ESTIMATED:
                    check(name + " sampler " + key, new_bayes.get(key) == value)
        if table == "<Coincident Frequency>":
            check(name + " response bins", int(analysis.get("NumberOfBins")) == int(row["NumberOfBins"]))
            continue
        old_model = ET.fromstring(row[MODEL_COLUMN[table]])
        new_model = ET.fromstring(run["modelSettings"])
        check(name + " model root", old_model.attrib == new_model.attrib)
        check(name + " active parameter configuration", authoring_parameters(old_model) == authoring_parameters(new_model))
        if table == "<Univariate Distribution>":
            check(name + " quantile priors", priors(old_model) == priors(new_model))
            # Stationary production prior likelihood uses top-level Parameters.
            # The saved Waimea TrendModels include stale, inactive alternate priors.
            if name == "WaimeaPk - Exact + Historical + RR Prior_RSkew":
                check(name + " stationary", old_model.get("IsNonstationary") == "False"
                      and new_model.get("IsNonstationary") == "False")
        if table == "Rating Curve Analysis":
            for key in ("MinStage", "MaxStage", "StageBins", "UseDefaultStageBins"):
                expected = row[key]
                observed = analysis.get(key)
                if key in ("MinStage", "MaxStage"):
                    same = abs(float(expected) - float(observed)) <= 1e-10
                elif key == "UseDefaultStageBins":
                    same = bool(int(expected)) == (observed.lower() == "true")
                else:
                    same = int(expected) == int(observed)
                check(name + " stage grid " + key, same)
    print(f"{stem}: {len(actual)} fresh analyses, {receipt['figures']} figures")

if issues:
    raise SystemExit("Authoring-setting mismatches:\n" + "\n".join(sorted(issues)))
print("All active authoring settings match; fitted state and inactive stationary trend priors excluded.")
