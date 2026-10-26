import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
from app.ml.relevance.preprocess import clean_relevance_text
from app.core.logging import logger

def train_relevance_model() -> Dict[str, Any]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    proc_dir = os.path.join(base_dir, "datasets", "brand_relevance", "processed")
    eval_dir = os.path.join(base_dir, "backend", "app", "ml", "evaluation")
    model_dir = os.path.join(base_dir, "backend", "app", "ml", "relevance", "model")
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    train_path = os.path.join(proc_dir, "train.csv")
    val_path = os.path.join(proc_dir, "validation.csv")
    test_path = os.path.join(proc_dir, "test.csv")

    if not os.path.exists(train_path):
        from backend.scripts.generate_brand_relevance_dataset import generate_dataset
        generate_dataset()

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"TRAINING RELEVANCE CLASSIFICATION MODEL ({len(train_df)} train, {len(val_df)} val, {len(test_df)} test)...")

    # Prepare features
    X_train_raw = [clean_relevance_text(row["text"], row["brand"] if pd.notna(row["brand"]) else None) for _, row in train_df.iterrows()]
    y_train = train_df["relevant"].astype(int).tolist()

    X_val_raw = [clean_relevance_text(row["text"], row["brand"] if pd.notna(row["brand"]) else None) for _, row in val_df.iterrows()]
    y_val = val_df["relevant"].astype(int).tolist()

    X_test_raw = [clean_relevance_text(row["text"], row["brand"] if pd.notna(row["brand"]) else None) for _, row in test_df.iterrows()]
    y_test = test_df["relevant"].astype(int).tolist()

    # 1. Fit TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=10000,
        sublinear_tf=True,
        stop_words="english",
        min_df=1
    )
    X_train_vec = vectorizer.fit_transform(X_train_raw)
    X_val_vec = vectorizer.transform(X_val_raw)
    X_test_vec = vectorizer.transform(X_test_raw)

    # 2. Train Calibrated Logistic Classifier with 3-fold cross-validation calibration
    base_clf = LogisticRegression(C=3.0, class_weight="balanced", max_iter=1000, random_state=42)
    calibrated_model = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=3)
    calibrated_model.fit(X_train_vec, y_train)

    # 3. Evaluate on Test Set
    y_test_pred = calibrated_model.predict(X_test_vec)
    y_test_probs = calibrated_model.predict_proba(X_test_vec)[:, 1]

    acc = accuracy_score(y_test, y_test_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_test_pred, average="binary", zero_division=0)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_test, y_test_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_test, y_test_pred).tolist()
    report = classification_report(y_test, y_test_pred, output_dict=True, zero_division=0)

    # Save artifacts
    model_path = os.path.join(model_dir, "relevance_model.joblib")
    vec_path = os.path.join(model_dir, "relevance_vectorizer.joblib")
    joblib.dump(calibrated_model, model_path)
    joblib.dump(vectorizer, vec_path)

    metrics = {
        "module": "Relevance Classification (Context-Aware)",
        "dataset_size_train": len(train_df),
        "dataset_size_validation": len(val_df),
        "dataset_size_test": len(test_df),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "macro_f1": round(macro_f1, 4),
        "confusion_matrix": cm,
        "classification_report": report
    }

    metrics_path = os.path.join(eval_dir, "relevance_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Relevance Test Accuracy: {acc * 100:.2f}%")
    logger.info(f"Precision: {prec * 100:.2f}% | Recall: {rec * 100:.2f}% | F1: {f1 * 100:.2f}%")
    logger.info(f"Confusion Matrix: {cm}")
    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Vectorizer saved to: {vec_path}")
    logger.info(f"Metrics saved to: {metrics_path}")

    return metrics

if __name__ == "__main__":
    train_relevance_model()
