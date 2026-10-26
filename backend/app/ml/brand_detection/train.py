import os
import json
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
from app.ml.brand_detection.predict import BrandDetector
from app.ml.brand_detection.preprocess import DEFAULT_BRAND_DICTIONARY
from app.core.logging import logger

def evaluate_brand_detection() -> Dict[str, Any]:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    proc_dir = os.path.join(base_dir, "datasets", "brand_relevance", "processed")
    eval_dir = os.path.join(base_dir, "backend", "app", "ml", "evaluation")
    model_dir = os.path.join(base_dir, "backend", "app", "ml", "brand_detection", "model")
    os.makedirs(eval_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    test_csv = os.path.join(proc_dir, "test.csv")
    train_csv = os.path.join(proc_dir, "train.csv")

    if not os.path.exists(test_csv):
        from backend.scripts.generate_brand_relevance_dataset import generate_dataset
        generate_dataset()

    test_df = pd.read_csv(test_csv)
    train_df = pd.read_csv(train_csv)

    detector = BrandDetector(DEFAULT_BRAND_DICTIONARY)

    logger.info(f"EVALUATING BRAND DETECTION MODULE ON TEST SET ({len(test_df)} samples)...")

    y_true = []
    y_pred = []
    brand_true = []
    brand_pred = []

    for _, row in test_df.iterrows():
        text = str(row["text"])
        expected_brand_present = int(row["brand_present"])
        expected_brand = str(row["brand"]) if pd.notna(row["brand"]) and row["brand"] else None
        
        # Run detection
        tracked = [expected_brand] if expected_brand else None
        res = detector.detect(text, tracked_brands=tracked)
        
        pred_present = 1 if res["brand_present"] else 0
        y_true.append(expected_brand_present)
        y_pred.append(pred_present)

        brand_true.append(expected_brand or "NONE")
        brand_pred.append(res["brand"] or "NONE")

    # Metrics
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)

    # Brand exact match metric
    brand_match_count = sum(1 for bt, bp in zip(brand_true, brand_pred) if bt == bp)
    brand_match_acc = brand_match_count / len(brand_true) if brand_true else 1.0

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    metrics = {
        "module": "Brand & Product Entity Detection",
        "dataset_size_train": len(train_df),
        "dataset_size_test": len(test_df),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "macro_f1": round(macro_f1, 4),
        "brand_name_exact_accuracy": round(brand_match_acc, 4),
        "supported_brands_count": len(DEFAULT_BRAND_DICTIONARY),
        "classification_report": report
    }

    # Save to evaluation directory
    metrics_path = os.path.join(eval_dir, "brand_detection_metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save dictionary artifact in model dir
    dict_path = os.path.join(model_dir, "brand_dictionary.json")
    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_BRAND_DICTIONARY, f, indent=2)

    logger.info(f"Brand Detection Accuracy: {acc * 100:.2f}%")
    logger.info(f"Precision: {prec * 100:.2f}% | Recall: {rec * 100:.2f}% | F1: {f1 * 100:.2f}%")
    logger.info(f"Brand Exact Match Accuracy: {brand_match_acc * 100:.2f}%")
    logger.info(f"Metrics saved to: {metrics_path}")

    return metrics

if __name__ == "__main__":
    evaluate_brand_detection()
