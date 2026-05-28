import os

import joblib


def load_detector_model(model_path):
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None


def save_detector_model(model, model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)


def predict_malicious_probability(model, prompt):
    if model is None or not hasattr(model, "predict_proba"):
        return 0.0

    probabilities = model.predict_proba([prompt])[0]
    if hasattr(model, "classes_") and 1 in model.classes_:
        malicious_index = list(model.classes_).index(1)
    else:
        malicious_index = min(1, len(probabilities) - 1)

    return float(probabilities[malicious_index])
