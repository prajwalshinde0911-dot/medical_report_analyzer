"""core/anemia_predictor.py - load the trained model and predict from report values."""
import re
from pathlib import Path

import joblib
import streamlit as st

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "anemia_model.pkl"

# Must match how Gender is encoded in data/anemia.csv.
# In the rows you pasted, Hb 12.4 with Gender 0 is "not anemic" while Hb 12.7 with
# Gender 1 is "anemic", which fits 0 = Female (cutoff ~12) and 1 = Male (cutoff ~13).
# Please double-check this against your dataset's source page.
GENDER_CODES = {"Female": 0, "Male": 1}

# Sanity ranges so a bad OCR/parse value or wrong unit isn't silently used.
PLAUSIBLE = {
    "Hemoglobin": (3, 25),   # g/dL
    "MCH": (10, 50),         # pg
    "MCHC": (20, 45),        # g/dL
    "MCV": (50, 130),        # fL
}


def model_available():
    return MODEL_PATH.exists()


@st.cache_resource
def _load_model():
    return joblib.load(MODEL_PATH)


def _identify(name):
    """Map a report parameter name to one of our feature names (or None)."""
    n = re.sub(r"\s+", " ", name.lower()).strip()
    if re.search(r"\bmchc\b|corpuscular h[a]?emoglobin conc", n):
        return "MCHC"
    if re.search(r"\bmch\b|mean corpuscular h[a]?emoglobin|mean cell h[a]?emoglobin", n):
        return "MCH"
    if re.search(r"\bmcv\b|mean corpuscular volume|mean cell volume", n):
        return "MCV"
    if re.search(r"h[a]?emoglobin|\bhb\b|\bhgb\b", n) and "corpuscular" not in n:
        return "Hemoglobin"
    return None


def extract_features(df):
    """Return {feature: float} for whichever of the 4 blood values were found."""
    found = {}
    for _, row in df.iterrows():
        feat = _identify(str(row["Parameter"]))
        if feat is None or feat in found:
            continue
        try:
            found[feat] = float(row["Result"])
        except (TypeError, ValueError):
            continue
    return found


def check_plausible(values):
    """Return a list of warnings for values outside plausible ranges."""
    warnings = []
    for feat, (lo, hi) in PLAUSIBLE.items():
        v = values.get(feat)
        if v is not None and not (lo <= v <= hi):
            warnings.append(f"{feat} = {v} looks unusual (expected roughly {lo}-{hi}). Check the unit or extraction.")
    return warnings


def predict(gender_label, values):
    """Return (is_anemic: bool, probability_of_anemia: float)."""
    bundle = _load_model()
    row = {"Gender": GENDER_CODES[gender_label], **values}
    X = [[row[f] for f in bundle["features"]]]
    model = bundle["model"]
    pred = int(model.predict(X)[0])
    prob = float(model.predict_proba(X)[0][1]) if hasattr(model, "predict_proba") else float(pred)
    return bool(pred), prob
