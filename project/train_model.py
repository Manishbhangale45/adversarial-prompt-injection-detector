import csv
import os
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from config import Config
from ml_model import save_detector_model


def load_dataset(csv_path):
    prompts = []
    labels = []
    with open(csv_path, mode="r", encoding="utf-8") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            prompts.append(row["prompt"].strip())
            labels.append(int(row["label"]))
    return prompts, labels


def build_pipeline():
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True, stop_words="english")),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )


def train():
    prompts, labels = load_dataset(Config.DATASET_PATH)

    if len(set(labels)) < 2:
        raise ValueError("The dataset must contain both benign and malicious samples.")

    X_train, X_test, y_train, y_test = train_test_split(
        prompts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print("Model trained successfully.")
    print(f"Test accuracy: {accuracy:.3f}")
    print(classification_report(y_test, predictions, digits=3))
    print(f"Class balance: {dict(Counter(labels))}")

    save_detector_model(pipeline, Config.MODEL_PATH)
    print(f"Model saved to: {Config.MODEL_PATH}")


if __name__ == "__main__":
    train()
