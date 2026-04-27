from pathlib import Path
import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


DATA_PATH = Path("data/mock/news_events.csv")
MODEL_PATH = Path("models/signal_classifier.pkl")


def load_training_data():
    df = pd.read_csv(DATA_PATH)

    required_columns = ["description", "matched_keywords", "signal_type"]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df = df.dropna(subset=["description", "signal_type"]).copy()

    df["matched_keywords"] = df["matched_keywords"].fillna("")
    df["text"] = (
        df["description"].astype(str) + " " +
        df["matched_keywords"].astype(str)
    )

    df = df[df["signal_type"].isin([
        "GENERAL_NEWS",
        "WEAK_SIGNAL",
        "RISK_SIGNAL",
        "CRITICAL_SIGNAL"
    ])]

    return df


def train_model():
    df = load_training_data()

    if len(df) < 10:
        raise ValueError("Not enough data to train the model. Collect more news first.")

    X = df["text"]
    y = df["signal_type"]

    stratify = y if y.value_counts().min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=5000
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("Classification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    train_model()