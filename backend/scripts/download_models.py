"""
Model & Dataset Setup and Git LFS Download Helper.
Verifies presence of machine learning model checkpoints (.joblib) and training datasets.
If missing or unpopulated Git LFS pointer files, automatically runs 'git lfs pull'
or executes localized model training scripts to restore them.
"""
import os
import sys
import subprocess
import hashlib
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("download_models")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BACKEND_DIR, "app", "models")
DATASETS_DIR = os.path.join(BACKEND_DIR, "app", "datasets")

REQUIRED_MODELS = [
    "apple_sentiment_model.joblib",
    "apple_emotion_model.joblib",
    "apple_intent_model.joblib",
    "apple_vectorizer.joblib",
    "annapoorna_sentiment_model.joblib",
    "annapoorna_emotion_model.joblib",
    "annapoorna_intent_model.joblib",
    "annapoorna_vectorizer.joblib",
]

REQUIRED_DATASETS = [
    os.path.join(DATASETS_DIR, "apple_smartphone", "apple_smartphone_dataset.csv"),
    os.path.join(DATASETS_DIR, "annapoorna_hospitality", "annapoorna_instagram_dataset.csv"),
]


def is_lfs_pointer(filepath: str) -> bool:
    """Checks if a file is an unresolved Git LFS pointer text file."""
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            header = f.read(100)
            return "version https://git-lfs.github.com/spec/v1" in header
    except Exception:
        return False


def pull_lfs() -> bool:
    """Attempts to pull Git LFS objects if git-lfs is available."""
    try:
        logger.info("Attempting 'git lfs pull' to fetch large models and datasets...")
        res = subprocess.run(["git", "lfs", "pull"], cwd=BACKEND_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("Git LFS pull completed successfully.")
            return True
        else:
            logger.warning(f"Git LFS pull returned non-zero code: {res.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.warning("Git or Git LFS executable not found in PATH.")
        return False


def verify_or_restore():
    """Verifies all required models and datasets. Triggers training if needed."""
    missing_models = []
    lfs_pointers = []

    for model_name in REQUIRED_MODELS:
        path = os.path.join(MODELS_DIR, model_name)
        if not os.path.exists(path):
            missing_models.append(model_name)
        elif is_lfs_pointer(path):
            lfs_pointers.append(model_name)

    if lfs_pointers:
        logger.warning(f"Detected {len(lfs_pointers)} Git LFS pointer files. Pulling actual binary assets...")
        pull_lfs()

    # Re-check
    missing_models = [m for m in REQUIRED_MODELS if not os.path.exists(os.path.join(MODELS_DIR, m))]

    if missing_models:
        logger.warning(f"Missing models: {missing_models}. Attempting to train models from local datasets...")
        train_script = os.path.join(BACKEND_DIR, "scripts", "train_apple_model.py")
        if os.path.exists(train_script):
            subprocess.run([sys.executable, train_script], cwd=BACKEND_DIR, check=True)
        annapoorna_script = os.path.join(BACKEND_DIR, "scripts", "train_annapoorna_model.py")
        if os.path.exists(annapoorna_script):
            subprocess.run([sys.executable, annapoorna_script], cwd=BACKEND_DIR, check=True)

    logger.info("Verification complete: all models and datasets are ready.")


if __name__ == "__main__":
    verify_or_restore()
