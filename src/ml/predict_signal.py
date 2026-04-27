from pathlib import Path
import joblib


MODEL_PATH = Path("models/signal_classifier.pkl")


def load_model():
    if not MODEL_PATH.exists():
        return None

    return joblib.load(MODEL_PATH)


def predict_signal_type(description, matched_keywords=""):
    model = load_model()

    if model is None:
        return None, None

    text = f"{description or ''} {matched_keywords or ''}"

    prediction = model.predict([text])[0]

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    confidence = float(max(probabilities))

    return prediction, round(confidence, 2)