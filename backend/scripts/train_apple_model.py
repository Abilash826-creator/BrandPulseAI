import os
import json
import joblib
import shutil
import hashlib
import sklearn
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support

def get_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def train_apple_models():
    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "app", "datasets", "apple_smartphone", "apple_smartphone_dataset.csv")
    models_dir = os.path.join(base_dir, "..", "app", "models")
    os.makedirs(models_dir, exist_ok=True)

    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}. Running collection script first...")
        from collect_apple_dataset import collect_apple_dataset
        df = collect_apple_dataset()
    else:
        df = pd.read_csv(data_path)

    data_hash = get_file_hash(data_path)

    print("=" * 60)
    print(f"Training NLP Models on Apple Smartphone Kaggle Dataset ({len(df)} samples)...")
    print(f"Data SHA-256 Hash: {data_hash}")
    print("=" * 60)

    # 1. Clean & Prepare Features
    df = df.dropna(subset=['text', 'sentiment'])
    X = [str(t) for t in df['text'].tolist()]
    y_sentiment = np.array([str(s) for s in df['sentiment'].tolist()])
    y_emotion = np.array([str(e) if pd.notna(e) else 'joy' for e in df['emotion'].tolist()])
    y_intent = np.array([str(i) if pd.notna(i) else 'general' for i in df['intent'].tolist()])

    # Stratified Train/Val/Test Split (70% train, 15% validation, 15% test)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y_sentiment, test_size=0.15, random_state=42, stratify=y_sentiment
    )
    # 0.1765 of 85% is ~15% of total
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.1765, random_state=42, stratify=y_train_val
    )

    print(f"Stratified Splits -> Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

    # 2. Fit TF-IDF Vectorizer
    print("Fitting TF-IDF N-Gram Vectorizer (1-3 ngrams, max_features=15000)...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=15000,
        sublinear_tf=True,
        stop_words='english',
        min_df=2
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_val_vec = vectorizer.transform(X_val)
    X_test_vec = vectorizer.transform(X_test)

    # 3. 5-Fold Cross Validation on Training Data
    print("Running 5-Fold Cross-Validation on Stratified Folds with class_weight='balanced'...")
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    base_clf = LinearSVC(class_weight='balanced', random_state=42, max_iter=2000, C=1.0, dual=False)
    cv_macro_f1 = cross_val_score(base_clf, X_train_vec, y_train, cv=skf, scoring='f1_macro')
    cv_accuracy = cross_val_score(base_clf, X_train_vec, y_train, cv=skf, scoring='accuracy')

    print(f"5-Fold CV Accuracy: {np.mean(cv_accuracy)*100:.2f}% (+/- {np.std(cv_accuracy)*100:.2f}%)")
    print(f"5-Fold CV Macro F1: {np.mean(cv_macro_f1)*100:.2f}% (+/- {np.std(cv_macro_f1)*100:.2f}%)")

    # 4. Train Sentiment Classifier (Calibrated LinearSVC for probability distribution)
    print("Fitting CalibratedClassifierCV on training set...")
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, cv=5)
    calibrated_clf.fit(X_train_vec, y_train)

    classes = list(calibrated_clf.classes_)
    neg_idx = classes.index('negative')

    # Baseline prediction on Validation Set (standard argmax)
    y_val_baseline = calibrated_clf.predict(X_val_vec)
    base_val_rep = classification_report(y_val, y_val_baseline, output_dict=True)
    val_neg_recall_baseline = base_val_rep['negative']['recall']
    print(f"Validation Baseline Negative Recall: {val_neg_recall_baseline*100:.2f}%")

    # 5. Tune Decision Threshold for Negative Class on Validation Set
    print("Tuning decision threshold for 'negative' class on validation set...")
    val_probs = calibrated_clf.predict_proba(X_val_vec)
    best_threshold = 0.25
    best_tuned_val_recall = 0.0

    for thresh in np.arange(0.20, 0.35, 0.02):
        thresh_f = round(float(thresh), 2)
        candidate_preds = []
        for p in val_probs:
            if p[neg_idx] >= thresh_f:
                candidate_preds.append('negative')
            else:
                other_indices = [i for i in range(len(classes)) if i != neg_idx]
                best_other = max(other_indices, key=lambda i: p[i])
                candidate_preds.append(classes[best_other])
        c_rep = classification_report(y_val, candidate_preds, output_dict=True, zero_division=0)
        neg_rec = c_rep['negative']['recall']
        if neg_rec >= 0.78 and neg_rec > best_tuned_val_recall:
            best_tuned_val_recall = neg_rec
            best_threshold = thresh_f

    print(f"Selected Negative Decision Threshold: {best_threshold} (Achieves {best_tuned_val_recall*100:.2f}% recall on validation)")

    # 6. Final Evaluation on Holdout Test Set
    test_probs = calibrated_clf.predict_proba(X_test_vec)
    y_test_baseline = calibrated_clf.predict(X_test_vec)
    base_test_rep = classification_report(y_test, y_test_baseline, output_dict=True, zero_division=0)
    neg_recall_baseline = float(base_test_rep['negative']['recall'])

    y_test_tuned = []
    for p in test_probs:
        if p[neg_idx] >= best_threshold:
            y_test_tuned.append('negative')
        else:
            other_indices = [i for i in range(len(classes)) if i != neg_idx]
            best_other = max(other_indices, key=lambda i: p[i])
            y_test_tuned.append(classes[best_other])

    accuracy = float(accuracy_score(y_test, y_test_tuned))
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_test_tuned, average='weighted', zero_division=0)
    macro_f1 = float(precision_recall_fscore_support(y_test, y_test_tuned, average='macro', zero_division=0)[2])
    cm = confusion_matrix(y_test, y_test_tuned, labels=['negative', 'neutral', 'positive']).tolist()
    class_report = classification_report(y_test, y_test_tuned, output_dict=True, zero_division=0)
    neg_recall_tuned = float(class_report['negative']['recall'])

    print("\n--- Final Test Set Performance ---")
    print(f"Accuracy:                  {accuracy * 100:.2f}%")
    print(f"Macro F1:                  {macro_f1 * 100:.2f}%")
    print(f"Negative Recall (Baseline): {neg_recall_baseline * 100:.2f}%")
    print(f"Negative Recall (Tuned):    {neg_recall_tuned * 100:.2f}%")

    # 7. Train Emotion Multi-Class Classifier
    print("\nTraining Emotion Multi-Class Classifier...")
    X_train_emo, X_test_emo, y_train_emo, y_test_emo = train_test_split(
        X, y_emotion, test_size=0.2, random_state=42, stratify=y_emotion
    )
    X_train_emo_vec = vectorizer.transform(X_train_emo)
    X_test_emo_vec = vectorizer.transform(X_test_emo)

    emotion_clf = LogisticRegression(max_iter=1000, class_weight='balanced')
    emotion_clf.fit(X_train_emo_vec, y_train_emo)
    emo_acc = float(accuracy_score(y_test_emo, emotion_clf.predict(X_test_emo_vec)))
    print(f"Emotion Model Accuracy: {emo_acc * 100:.2f}%")

    # 8. Train Intent Classifier
    print("Training User Intent Classifier...")
    X_train_int, X_test_int, y_train_int, y_test_int = train_test_split(
        X, y_intent, test_size=0.2, random_state=42, stratify=y_intent
    )
    X_train_int_vec = vectorizer.transform(X_train_int)
    X_test_int_vec = vectorizer.transform(X_test_int)

    intent_clf = LogisticRegression(max_iter=1000, class_weight='balanced')
    intent_clf.fit(X_train_int_vec, y_train_int)
    int_acc = float(accuracy_score(y_test_int, intent_clf.predict(X_test_int_vec)))
    print(f"Intent Model Accuracy: {int_acc * 100:.2f}%")

    # 9. Extract Top Informative N-Grams
    feature_names = np.array(vectorizer.get_feature_names_out())
    lr_explainer = LogisticRegression(max_iter=1000, class_weight='balanced')
    lr_explainer.fit(X_train_vec, y_train)

    top_keywords_per_class = {}
    for i, cls_name in enumerate(lr_explainer.classes_):
        top_indices = np.argsort(lr_explainer.coef_[i])[-15:][::-1]
        top_keywords_per_class[cls_name] = [
            {"term": str(feature_names[idx]), "weight": round(float(lr_explainer.coef_[i][idx]), 3)}
            for idx in top_indices
        ]

    # 10. Thematic KMeans Clusters
    print("Extracting Thematic KMeans Clusters for Apple Smartphones...")
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    kmeans.fit(X_train_vec)
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    
    topic_clusters = []
    cluster_names = [
        "Camera System & Macro Photography",
        "Battery Longevity & Power Management",
        "iOS Software, Neural Engine & UI Speed",
        "Design, Titanium Build & Display Quality",
        "Retail Pricing, Warranty & Trade-in Deals"
    ]
    for i in range(5):
        top_terms = [str(feature_names[ind]) for ind in order_centroids[i, :8]]
        topic_clusters.append({
            "cluster_id": i,
            "name": cluster_names[i],
            "top_terms": top_terms
        })

    # 11. Save Versioned Models and Atomically Swap Active Files
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    model_version = f"2.5.0-v{timestamp_str}"

    v_sent_path = os.path.join(models_dir, f"apple_sentiment_model_v{timestamp_str}.joblib")
    v_vec_path = os.path.join(models_dir, f"apple_vectorizer_v{timestamp_str}.joblib")
    v_emo_path = os.path.join(models_dir, f"apple_emotion_model_v{timestamp_str}.joblib")
    v_int_path = os.path.join(models_dir, f"apple_intent_model_v{timestamp_str}.joblib")

    joblib.dump(calibrated_clf, v_sent_path)
    joblib.dump(vectorizer, v_vec_path)
    joblib.dump(emotion_clf, v_emo_path)
    joblib.dump(intent_clf, v_int_path)

    # Active file destinations
    active_sent = os.path.join(models_dir, "apple_sentiment_model.joblib")
    active_vec = os.path.join(models_dir, "apple_vectorizer.joblib")
    active_emo = os.path.join(models_dir, "apple_emotion_model.joblib")
    active_int = os.path.join(models_dir, "apple_intent_model.joblib")
    metrics_path = os.path.join(models_dir, "apple_model_metrics.json")

    # Atomic swap for model weights
    for src_file, dst_file in [
        (v_sent_path, active_sent),
        (v_vec_path, active_vec),
        (v_emo_path, active_emo),
        (v_int_path, active_int)
    ]:
        tmp_dst = f"{dst_file}.tmp"
        shutil.copy2(src_file, tmp_dst)
        os.replace(tmp_dst, dst_file)

    metrics_payload = {
        "model_name": "TF-IDF + Calibrated LinearSVC (Linear Classifier)",
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "data_hash": data_hash,
        "dataset_source": "Kaggle Apple Twitter & Amazon Reviews Corpus",
        "total_dataset_size": len(df),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "classes": classes,
        "accuracy": round(accuracy, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(float(f1), 4),
        "decision_threshold_negative": best_threshold,
        "negative_recall_baseline": round(neg_recall_baseline, 4),
        "negative_recall_tuned": round(neg_recall_tuned, 4),
        "cross_validation_5fold": {
            "mean_accuracy": round(float(np.mean(cv_accuracy)), 4),
            "std_accuracy": round(float(np.std(cv_accuracy)), 4),
            "mean_macro_f1": round(float(np.mean(cv_macro_f1)), 4),
            "std_macro_f1": round(float(np.std(cv_macro_f1)), 4)
        },
        "emotion_accuracy": round(emo_acc, 4),
        "intent_accuracy": round(int_acc, 4),
        "confusion_matrix": cm,
        "classification_report": class_report,
        "top_keywords_per_class": top_keywords_per_class,
        "thematic_clusters": topic_clusters
    }

    # Write metrics atomically
    tmp_metrics = f"{metrics_path}.tmp"
    with open(tmp_metrics, 'w', encoding='utf-8') as f:
        json.dump(metrics_payload, f, indent=2)
    os.replace(tmp_metrics, metrics_path)

    print("\n" + "=" * 60)
    print("Model Training & Atomic Serialization Complete!")
    print(f"Model Version: {model_version}")
    print(f"Active Model:  {os.path.abspath(active_sent)}")
    print(f"Active Metrics: {os.path.abspath(metrics_path)}")
    print("=" * 60)

    return metrics_payload

if __name__ == "__main__":
    train_apple_models()
