import os
import joblib
import logging
from typing import Dict, Any, Optional
from app.ml.relevance.preprocess import clean_relevance_text

logger = logging.getLogger("brandpulse.relevance")

class RelevanceClassifier:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), "model")
        self.model_dir = model_dir
        self.model = None
        self.vectorizer = None
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(self.model_dir, "relevance_model.joblib")
        vec_path = os.path.join(self.model_dir, "relevance_vectorizer.joblib")
        if os.path.exists(model_path) and os.path.exists(vec_path):
            try:
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vec_path)
            except Exception as e:
                logger.warning(f"[RelevanceClassifier] Error loading model: {e}")

    def classify(self, text: str, brand: Optional[str] = None) -> Dict[str, Any]:
        """
        Classifies whether the text is genuinely relevant to the tracked business.
        Returns:
            {
                "relevant": bool,
                "relevance_score": float,
                "classification": "relevant" | "irrelevant"
            }
        """
        if not text or not text.strip():
            return {
                "relevant": False,
                "relevance_score": 0.0,
                "classification": "irrelevant"
            }

        # If model is not loaded yet, attempt reload or train
        if self.model is None or self.vectorizer is None:
            self._load_model()

        if self.model is not None and self.vectorizer is not None:
            try:
                feature_text = clean_relevance_text(text, brand)
                vec = self.vectorizer.transform([feature_text])
                probs = self.model.predict_proba(vec)[0]
                relevance_score = float(probs[1]) if len(probs) > 1 else float(probs[0])
                relevant = relevance_score >= 0.50
                return {
                    "relevant": relevant,
                    "relevance_score": round(relevance_score, 4),
                    "classification": "relevant" if relevant else "irrelevant"
                }
            except Exception as e:
                logger.warning(f"[RelevanceClassifier] Inference exception: {e}")

        # Heuristic fallback if model weights not yet serialized
        text_lower = text.lower()
        if brand and brand.lower() in text_lower:
            return {
                "relevant": True,
                "relevance_score": 0.85,
                "classification": "relevant"
            }
        return {
            "relevant": False,
            "relevance_score": 0.15,
            "classification": "irrelevant"
        }

relevance_classifier = RelevanceClassifier()
