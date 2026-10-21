"""
Train the anemia classifier on data/anemia.csv and save it to models/anemia_model.pkl

Run from the project root (next to app.py):
    python train_anemia_model.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

DATA_PATH = Path("data/anemia.csv")
MODEL_PATH = Path("models/anemia_model.pkl")

# ORDER MATTERS: core/anemia_predictor.py must use exactly this order.
FEATURES = ["Gender", "Hemoglobin", "MCH", "MCHC", "MCV"]
TARGET = "Result"


def main():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = df[FEATURES + [TARGET]].dropna()
    print(f"Loaded {len(df)} rows")
    print("Class balance:\n", df[TARGET].value_counts(), "\n")

    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    candidates = {
        "Logistic Regression": Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000)),
        ]),
        "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
    }

    best_name, best_model, best_score = None, None, -1.0
    for name, model in candidates.items():
        score = cross_val_score(model, X_train, y_train, cv=5, scoring="f1").mean()
        print(f"{name:20s} 5-fold CV F1 = {score:.3f}")
        if score > best_score:
            best_name, best_model, best_score = name, model, score

    print(f"\nBest model: {best_name}")
    best_model.fit(X_train, y_train)

    preds = best_model.predict(X_test)
    print("\nConfusion matrix (rows = actual, cols = predicted):")
    print(confusion_matrix(y_test, preds))
    print("\nClassification report:")
    print(classification_report(y_test, preds, target_names=["Not anemic (0)", "Anemic (1)"]))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": best_model, "features": FEATURES, "name": best_name}, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
