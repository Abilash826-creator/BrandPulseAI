import os
import re
import math
import json
import random
import logging
import datetime
import joblib
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from langdetect import DetectorFactory, detect
    DetectorFactory.seed = 0
except ImportError:
    detect = None

class SentimentResult(tuple):
    """
    Subclass of 2-tuple (sentiment, score) that also exposes .confidence.
    Enables unpacking as `sentiment, score = analyze_sentiment(...)` without breaking any existing callers.
    """
    def __new__(cls, sentiment: str, score: float, confidence: float = 1.0):
        return super(SentimentResult, cls).__new__(cls, (sentiment, score))

    def __init__(self, sentiment: str, score: float, confidence: float = 1.0):
        self.sentiment = sentiment
        self.score = score
        self.confidence = round(confidence, 4)

class AIEngine:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        
        # Load Trained ML Models
        self.models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        self.datasets_dir = os.path.join(os.path.dirname(__file__), "..", "datasets", "apple_smartphone")
        
        self.sentiment_model = None
        self.vectorizer = None
        self.emotion_model = None
        self.intent_model = None
        self.metrics_data = {}
        
        self._load_trained_models()

        # Emotion Lexicon and Keyword Associations
        self.emotion_lexicons = {
            "joy": [
                "love", "amazing", "great", "excellent", "superb", "brilliant", "happy", "delighted", 
                "thrilled", "smooth", "flawless", "awesome", "perfect", "fantastic", "excited", "best",
                "innovative", "impressive", "recommend", "helpful", "game-changer", "kudos", "win"
            ],
            "anger": [
                "furious", "angry", "terrible", "worst", "hate", "scam", "rip-off", "outage", "broken",
                "horrible", "annoyed", "unacceptable", "disaster", "garbage", "trash", "sucks", "fail",
                "frustrating", "awful", "boycott", "fraud", "stealing", "useless", "lawsuit", "refund"
            ],
            "sadness": [
                "disappointed", "sad", "unfortunate", "regret", "miss", "lost", "depressed", "unhappy",
                "shame", "downgrade", "crying", "letdown", "bummed", "sorry", "pity", "poor"
            ],
            "surprise": [
                "wow", "unbelievable", "shocking", "unexpected", "mindblowing", "surprised", "whoa",
                "astonishing", "stunning", "unreal", "never expected", "crazy", "fascinating"
            ],
            "fear": [
                "afraid", "scared", "worry", "risk", "leak", "privacy", "breach", "hack", "danger",
                "security", "vulnerability", "threat", "unsafe", "exposed", "compromised", "concern"
            ]
        }
        
        # Intent Lexicons
        self.intent_patterns = {
            "complaint": [
                r"\b(broken|bug|error|glitch|down|outage|refund|terrible|slow|crash|issue|failed|fix|horrible|sucks|not working|waste)\b",
                r"\b(why is|can't login|charging me|canceled|unacceptable)\b"
            ],
            "query": [
                r"\b(how do i|how to|is there|can i|where is|when will|does it support|what is|any way to|anyone know)\b",
                r"\?"
            ],
            "purchase_intent": [
                r"\b(buy|purchase|pricing|discount|cost|upgrade|deal|subscription|tier|worth buying|how much|coupon|switch to)\b"
            ],
            "praise": [
                r"\b(love|awesome|great job|thank you|thanks to|kudos|best|shoutout|amazing|brilliant|recommend|game changer)\b"
            ]
        }

        # Multilingual Language Markers
        self.TANGLISH_MARKERS = {
            "romba", "nalla", "irukku", "illa", "illai", "sappadu", "saapadu", "supera", "vandhadhu", "semma",
            "kaasu", "kadai", "venum", "thanni", "dhool", "machan", "seri", "paravala", "kodungada",
            "kuduthaanga", "saptein", "sapten", "annachi", "kitta", "enga", "epdi", "enna", "iruku",
            "irundhathu", "irundhadhu", "mudiyala", "theriyala", "poitaanga", "ponga", "vaanga", "saapida",
            "parotta", "kothu", "kudukala", "varala", "pannanga", "solranga", "thappu", "mosam", "arputham"
        }

        self.HINGLISH_MARKERS = {
            "bahut", "bohot", "accha", "achha", "acchi", "nahi", "kya", "hai", "tha", "thi", "bhai",
            "sahi", "swaad", "khana", "paisa", "vasool", "kripya", "bekaar", "bekar", "mazza", "maza",
            "aaya", "dhanyavad", "chahiye", "dukaan", "bhiya", "bhaiya", "lao", "bolo", "mast", "ekdum",
            "shandar", "zabardast", "matlab", "kuch", "karlo", "hoga", "hota", "milega", "pasand", "kharab",
            "bakwas", "ganda", "mehenga", "sasta", "acche", "badhiya", "lajawab"
        }

        # Multilingual Sentiment Lexicons
        self.MULTILINGUAL_POSITIVE = {
            "nalla", "supera", "semma", "dhool", "arputham", "pramadham", "super", "tasty",
            "fresh", "crispy", "hot", "perfection", "kuduthanga", "satisfaction", "clean", "arumai", "sirappu",
            "accha", "achha", "acchi", "mast", "swaad", "vasool", "shandar", "zabardast", "lajawab",
            "mazza", "maza", "badhiya", "ekdum", "pasand", "best", "sahi", "badhia",
            "நல்ல", "சூப்பர்", "அருமை", "சுவை", "சிறப்பு", "மகிழ்ச்சி", "அற்புதம்", "சாப்பாடு", "ரொம்ப", "சுவையான",
            "अच्छा", "बढ़िया", "स्वादिष्ट", "लाजवाब", "शानदार", "पसंद", "सुंदर"
        }

        self.MULTILINGUAL_NEGATIVE = {
            "bekaar", "waste", "mosam", "illa", "illai", "slow", "delay", "late", "mudiyala", "kevalam",
            "thappu", "bad", "worst", "salty", "cold", "poor", "dirty", "overpriced", "kudukala", "varala",
            "bekar", "kharab", "bakwas", "ganda", "faltu", "nahi", "thanda", "mehenga",
            "dhoka", "loot", "rude", "slow",
            "மோசம்", "கெட்ட", "தாமதம்", "பிடிக்கவில்லை", "வீண்",
            "खराब", "बकवास", "गंदा", "बेकार", "महंगा", "धोखा", "पसंद नहीं"
        }

        self.TRANSLATION_MAP = {
            "romba nalla irukku": "is very good",
            "romba nalla": "very good",
            "semma taste": "awesome taste",
            "supera irukku": "is superb",
            "nalla illa": "not good",
            "nalla irukku": "is good",
            "bahut accha hai": "is very good",
            "bohot accha": "very good",
            "bahut accha": "very good",
            "paisa vasool": "worth the money",
            "ekdum mast": "absolutely fantastic",
            "swaad mast hai": "taste is fantastic",
            "bekaar service": "useless service",
            "pasand nahi aaya": "did not like it",
            "bilkul bekar": "completely useless",
            "khana kharab tha": "food was bad",
            "service romba slow": "service is very slow",
            "cleanliness nalla illa": "cleanliness is not good",
            "swaad lajawab hai": "taste is unmatched",
            "kadai clean ah irukku": "shop is clean",
            "super kadai": "superb shop",
            "ரொம்ப நல்லா இருக்கு": "very good",
            "சுவை அருமை": "taste is wonderful",
            "சேவை மோசம்": "service is bad",
            "ரொம்ப நல்ல": "very good",
            "மிகவும் நன்று": "very good",
            "மோசமான சேவை": "terrible service",
            "बहुत अच्छा खाना है": "the food is very good",
            "सेवा बहुत खराब है": "service is very bad",
            "पैसे वसूल": "value for money",
            "बहुत बढ़िया": "very good",
            "स्वादिष्ट खाना": "delicious food",
            "खराब खाना": "bad food"
        }

        self.PRESET_TOPIC_KEYWORDS = {
            "Food Quality": ["food", "taste", "delicious", "crispy", "spicy", "hot", "sweet", "tea", "coffee", "dosa", "puff", "cake", "meal", "fresh", "chutney", "sambar", "flavour", "flavor", "swaad", "roast", "parotta", "biscuit", "roti", "curry", "ghee", "biryani"],
            "Food Quality & Taste": ["food", "taste", "delicious", "crispy", "spicy", "hot", "sweet", "tea", "coffee", "dosa", "puff", "cake", "meal", "fresh", "chutney", "sambar", "flavour", "flavor", "swaad", "roast", "parotta", "biscuit", "roti", "curry", "ghee", "biryani"],
            "Service & Staff": ["service", "staff", "waiter", "manager", "polite", "rude", "behavior", "counter", "attend", "delay", "helpful", "friendly", "listen", "bhiya", "bhaiya", "bill", "billing"],
            "Cleanliness & Hygiene": ["clean", "dirty", "hygiene", "hygienic", "sanitized", "fly", "hair", "washroom", "tables", "floor", "neat", "dust", "sanitizer", "ganda", "mosquito"],
            "Hygiene & Cleanliness": ["clean", "dirty", "hygiene", "hygienic", "sanitized", "fly", "hair", "washroom", "tables", "floor", "neat", "dust", "sanitizer", "ganda", "mosquito"],
            "Value & Pricing": ["price", "cost", "expensive", "cheap", "bill", "amount", "worth", "paisa", "vasool", "rate", "charges", "discount", "offer", "mehenga", "sasta"],
            "Price & Portion": ["price", "cost", "expensive", "cheap", "portion", "quantity", "worth", "paisa", "vasool", "rate", "charges"],
            "Wait Time": ["wait", "waiting", "time", "reception", "queue", "delay", "minutes"],
            "Waiting Time": ["wait", "waiting", "time", "reception", "queue", "delay", "minutes"],
            "Doctor Care": ["doctor", "dr", "diagnosis", "care", "caring", "physician", "dentist", "treatment", "medicine"],
            "Doctor Consultation": ["doctor", "dr", "diagnosis", "care", "caring", "physician", "dentist", "treatment", "medicine"],
            "Stylist Skill": ["stylist", "haircut", "styling", "hair", "cut", "barber", "grooming", "beard", "salon"],
            "Hair Services": ["stylist", "haircut", "styling", "hair", "cut", "barber", "grooming", "beard", "salon"],
            "Delivery & Packaging": ["packaging", "parcel", "delivery", "swiggy", "zomato", "spill", "packing", "carry bag", "box", "takeaway", "ontime"],
            "Atmosphere & Ambience": ["seating", "ac", "music", "crowd", "parking", "noise", "interior", "vibe", "ambience", "lighting", "space"]
        }


    def _load_trained_models(self):
        """Loads serialized Scikit-learn models trained on Kaggle Apple smartphone data."""
        try:
            # Load Apple Models
            sent_path = os.path.join(self.models_dir, "apple_sentiment_model.joblib")
            vec_path = os.path.join(self.models_dir, "apple_vectorizer.joblib")
            emo_path = os.path.join(self.models_dir, "apple_emotion_model.joblib")
            int_path = os.path.join(self.models_dir, "apple_intent_model.joblib")
            met_path = os.path.join(self.models_dir, "apple_model_metrics.json")

            if os.path.exists(sent_path) and os.path.exists(vec_path):
                self.sentiment_model = joblib.load(sent_path)
                self.vectorizer = joblib.load(vec_path)
                logger.info("[Brandpulse AI] Loaded trained Apple Sentiment Model & Vectorizer.")

            if os.path.exists(emo_path):
                self.emotion_model = joblib.load(emo_path)
            if os.path.exists(int_path):
                self.intent_model = joblib.load(int_path)
            if os.path.exists(met_path):
                with open(met_path, 'r', encoding='utf-8') as f:
                    self.metrics_data = json.load(f)

            # Load Annapoorna Models
            anna_sent = os.path.join(self.models_dir, "annapoorna_sentiment_model.joblib")
            anna_vec = os.path.join(self.models_dir, "annapoorna_vectorizer.joblib")
            anna_emo = os.path.join(self.models_dir, "annapoorna_emotion_model.joblib")
            anna_int = os.path.join(self.models_dir, "annapoorna_intent_model.joblib")

            self.annapoorna_sentiment_model = None
            self.annapoorna_vectorizer = None
            self.annapoorna_emotion_model = None
            self.annapoorna_intent_model = None

            if os.path.exists(anna_sent) and os.path.exists(anna_vec):
                self.annapoorna_sentiment_model = joblib.load(anna_sent)
                self.annapoorna_vectorizer = joblib.load(anna_vec)
                logger.info("[Brandpulse AI] Loaded trained Annapoorna Coimbatore Model & Vectorizer.")
            if os.path.exists(anna_emo):
                self.annapoorna_emotion_model = joblib.load(anna_emo)
            if os.path.exists(anna_int):
                self.annapoorna_intent_model = joblib.load(anna_int)
        except (OSError, IOError, ValueError, KeyError, EOFError) as e:
            logger.warning(f"[Brandpulse AI] Warning loading ML models: {e}")

    def get_model_statuses(self) -> Dict[str, str]:
        """Exposes model operational status: loaded or fallback."""
        return {
            "apple_sentiment": "loaded" if (self.sentiment_model is not None and self.vectorizer is not None) else "fallback",
            "apple_emotion": "loaded" if self.emotion_model is not None else "fallback",
            "apple_intent": "loaded" if self.intent_model is not None else "fallback",
            "annapoorna_sentiment": "loaded" if (self.annapoorna_sentiment_model is not None and self.annapoorna_vectorizer is not None) else "fallback",
            "annapoorna_emotion": "loaded" if self.annapoorna_emotion_model is not None else "fallback",
            "annapoorna_intent": "loaded" if self.annapoorna_intent_model is not None else "fallback"
        }

    def detect_language(self, text: str) -> str:
        """
        Detects primary language and dialect:
        - 'ta': Tamil Unicode script
        - 'hi': Hindi Devanagari script
        - 'tanglish': Romanized Tamil text
        - 'hinglish': Romanized Hindi text
        - 'en': English (or default)
        """
        if not text or not text.strip():
            return "en"
        
        # 1. Unicode script detection
        if re.search(r'[\u0B80-\u0BFF]', text):
            return "ta"
        if re.search(r'[\u0900-\u097F]', text):
            return "hi"
            
        words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', text)]
        if not words:
            return "en"
            
        words_set = set(words)
        tanglish_matches = words_set.intersection(self.TANGLISH_MARKERS)
        hinglish_matches = words_set.intersection(self.HINGLISH_MARKERS)

        # Check strong distinctive dialect markers or at least 2 marker hits
        strong_tanglish = {"romba", "irukku", "semma", "kadai", "saptein", "kuduthaanga", "arputham", "kaasu", "vandhadhu", "sappadu", "mudiyala", "theriyala"}
        strong_hinglish = {"bahut", "bohot", "accha", "achha", "swaad", "khana", "bekar", "bakwas", "ekdum", "lajawab", "badhiya", "kharab", "ganda", "mehenga", "dhanyavad", "chahiye", "paisa", "vasool"}

        is_tanglish = bool(words_set.intersection(strong_tanglish)) or len(tanglish_matches) >= 2
        is_hinglish = bool(words_set.intersection(strong_hinglish)) or len(hinglish_matches) >= 2

        if is_tanglish and len(tanglish_matches) >= len(hinglish_matches):
            return "tanglish"
        if is_hinglish:
            return "hinglish"
            
        if detect is not None:
            try:
                d_lang = detect(text)
                if d_lang:
                    return d_lang
            except Exception as e:
                logger.debug("Language detection fallback for text '%s': %s", text[:30], e)

        return "en"

    def translate_to_english(self, text: str, lang: Optional[str] = None) -> Optional[str]:
        """Translates non-English review text to plain English."""
        if not text or not text.strip():
            return None
        d_lang = lang or self.detect_language(text)
        if d_lang == "en":
            return text
            
        translated = text
        # 1. Exact phrase matches from TRANSLATION_MAP
        for phrase, eng_eq in self.TRANSLATION_MAP.items():
            if re.search(re.escape(phrase), translated, re.IGNORECASE):
                translated = re.sub(re.escape(phrase), eng_eq, translated, flags=re.IGNORECASE)
                
        # 2. Word-level heuristic replacement for remaining Tanglish / Hinglish
        word_map = {
            "romba": "very", "nalla": "good", "illa": "not", "illai": "not", "irukku": "is", "irundhathu": "was",
            "sappadu": "food", "saapadu": "food", "semma": "awesome", "kaasu": "money", "kadai": "shop",
            "thanni": "water", "supera": "superb", "dhool": "terrific", "paravala": "okay", "seri": "fine",
            "bahut": "very", "bohot": "very", "accha": "good", "achha": "good", "acchi": "good", "nahi": "not",
            "swaad": "taste", "khana": "food", "paisa": "money", "vasool": "worth", "bekaar": "useless",
            "bekar": "useless", "mazza": "fun / delight", "kharab": "bad", "bakwas": "terrible", "mast": "fantastic",
            "ekdum": "totally", "shandar": "magnificent", "mehenga": "expensive", "sasta": "cheap"
        }
        tokens = re.split(r'(\W+)', translated)
        replaced = []
        for t in tokens:
            lower_t = t.lower()
            if lower_t in word_map:
                replaced.append(word_map[lower_t])
            else:
                replaced.append(t)
        final_trans = "".join(replaced).strip()
        final_trans = re.sub(r'\s+', ' ', final_trans)
        return final_trans if final_trans != text else f"Translated: {text}"

    def analyze_multilingual_sentiment(self, text: str, lang: str) -> SentimentResult:
        """
        Specialized multilingual sentiment scorer for Tamil, Hindi, Tanglish, and Hinglish.
        Does NOT apply English VADER blindly. Marks confidence explicitly (0.65 - 0.75).
        """
        lower = text.lower()
        words = set(re.findall(r'[\u0B80-\u0BFF]+|[\u0900-\u097F]+|[a-zA-Z]+', lower))
        
        pos_hits = len(words.intersection(self.MULTILINGUAL_POSITIVE))
        neg_hits = len(words.intersection(self.MULTILINGUAL_NEGATIVE))

        for kw in self.MULTILINGUAL_POSITIVE:
            if len(kw) >= 3 and kw in lower and kw not in words:
                pos_hits += 1
        for kw in self.MULTILINGUAL_NEGATIVE:
            if len(kw) >= 3 and kw in lower and kw not in words:
                neg_hits += 1

        # Check multi-word phrase cues
        if any(p in lower for p in ["romba nalla", "bahut accha", "bohot accha", "paisa vasool", "semma taste", "swaad mast", "supera irukku"]):
            pos_hits += 2
        if any(p in lower for p in ["nalla illa", "bekaar service", "pasand nahi", "bilkul bekar", "khana kharab", "service romba slow"]):
            neg_hits += 2

        if pos_hits > neg_hits:
            score = round(min(0.35 + (pos_hits * 0.2), 0.95), 2)
            return SentimentResult("positive", score, confidence=0.72)
        elif neg_hits > pos_hits:
            score = round(max(-0.35 - (neg_hits * 0.2), -0.95), 2)
            return SentimentResult("negative", score, confidence=0.72)
        else:
            return SentimentResult("neutral", 0.0, confidence=0.55)

    def tag_preset_topics(
        self,
        text: str,
        business_type: Optional[str] = None,
        preset_topics: Optional[List[str]] = None,
        preset_key: Optional[str] = None
    ) -> List[str]:
        """Tags a review with matching small business preset topics."""
        lower = text.lower()
        matched = []
        p_key = (preset_key or business_type or "").lower()
        target_topics = preset_topics
        if not target_topics:
            if "clinic" in p_key:
                target_topics = ["Doctor Care", "Wait Time", "Cleanliness & Hygiene", "Value & Pricing"]
            elif "salon" in p_key:
                target_topics = ["Hair Services", "Stylist Skill", "Cleanliness & Hygiene", "Wait Time", "Value & Pricing"]
            elif "bakery" in p_key:
                target_topics = ["Food Quality", "Cleanliness & Hygiene", "Service & Staff", "Value & Pricing"]
            elif "restaurant" in p_key:
                target_topics = ["Food Quality", "Service & Staff", "Wait Time", "Cleanliness & Hygiene", "Value & Pricing"]
            else:
                target_topics = list(self.PRESET_TOPIC_KEYWORDS.keys())

        for top in target_topics:
            kws = self.PRESET_TOPIC_KEYWORDS.get(top, [w.lower() for w in top.split()])
            if any(re.search(r'\b' + re.escape(k) + r'\b', lower) for k in kws):
                matched.append(top)
        return matched if matched else (target_topics[:1] if target_topics else ["Customer Experience"])

    def _run_multilingual_model(self, text: str, lang: str) -> Tuple[str, float, float]:
        """Optional hook for multilingual model (XLM-R / IndicBERT) behind config flag."""
        logger.info("Running multilingual model '%s' for language '%s'", settings.MULTILINGUAL_MODEL_NAME, lang)
        return "neutral", 0.0, 0.70

    def analyze_sentiment(self, text: str, lang: Optional[str] = None) -> SentimentResult:
        """
        Calculates sentiment polarity using trained Calibrated ML Model combined with VADER lexicon.
        Returns SentimentResult(sentiment_label, score, confidence) where score is between -1.0 and 1.0.
        If non-English, does not apply VADER blindly; uses dedicated multilingual scorer.
        """
        if not text or not text.strip():
            return SentimentResult("neutral", 0.0, 1.0)

        detected_lang = lang or self.detect_language(text)
        if detected_lang != "en":
            if settings.ENABLE_MULTILINGUAL_MODEL:
                sent, sc, conf = self._run_multilingual_model(text, detected_lang)
                return SentimentResult(sent, sc, conf)
            if detected_lang in ("ta", "hi", "tanglish", "hinglish"):
                return self.analyze_multilingual_sentiment(text, detected_lang)
            return SentimentResult("neutral", 0.0, confidence=0.40)


        # Determine appropriate model based on context (Food/Annapoorna vs Tech/Apple)
        active_model = self.sentiment_model
        active_vectorizer = self.vectorizer

        lower_check = text.lower()
        if any(w in lower_check for w in ["annapoorna", "ghee roast", "dosa", "sambar", "filter coffee", "mysurpa", "coimbatore", "vada", "chutney"]):
            if self.annapoorna_sentiment_model is not None and self.annapoorna_vectorizer is not None:
                active_model = self.annapoorna_sentiment_model
                active_vectorizer = self.annapoorna_vectorizer

        if active_model is not None and active_vectorizer is not None:
            try:
                vec = active_vectorizer.transform([text])
                classes = list(active_model.classes_)
                probs = active_model.predict_proba(vec)[0]
                prob_dict = dict(zip(classes, probs))
                
                pos_p = prob_dict.get('positive', 0.0)
                neu_p = prob_dict.get('neutral', 0.0)
                neg_p = prob_dict.get('negative', 0.0)

                # Compound continuous score from probabilities
                ml_score = round(pos_p - neg_p, 3)

                # Use tuned negative decision threshold for crisis detection
                threshold_neg = float(self.metrics_data.get("decision_threshold_negative", 0.25))
                if neg_p >= threshold_neg:
                    sentiment = "negative"
                    ml_score = -abs(ml_score) if ml_score != 0 else -0.35
                elif pos_p > neu_p:
                    sentiment = "positive"
                else:
                    sentiment = "neutral"

                # Check high-severity keywords
                lower_text = text.lower()
                if any(w in lower_text for w in ["scam", "boycott", "lawsuit", "disaster", "security breach", "data leak"]):
                    ml_score = min(ml_score, -0.75)
                    sentiment = "negative"
                elif any(w in lower_text for w in ["game changer", "revolutionary", "best tool ever", "absolute masterclass"]):
                    ml_score = max(ml_score, 0.75)
                    sentiment = "positive"

                conf = round(float(max(pos_p, neu_p, neg_p)), 4)
                return SentimentResult(sentiment, ml_score, conf)
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning("Sentiment ML inference error, falling back: %s", e)

        # Fallback to VADER for English
        scores = self.vader.polarity_scores(text)
        compound = scores["compound"]
        
        lower_text = text.lower()
        if any(w in lower_text for w in ["scam", "boycott", "lawsuit", "disaster", "security breach", "data leak"]):
            compound = min(compound, -0.75)
        elif any(w in lower_text for w in ["game changer", "revolutionary", "best tool ever", "absolute masterclass"]):
            compound = max(compound, 0.75)

        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        conf = round(float(abs(compound)), 4) if compound != 0 else 0.65
        return SentimentResult(sentiment, round(compound, 3), max(conf, 0.50))

    def detect_emotions(self, text: str, sentiment_score: Optional[float] = None) -> Tuple[Dict[str, float], str]:
        """
        Detects distribution of Joy, Anger, Sadness, Surprise, and Fear.
        """
        lower = text.lower()
        counts = {"joy": 0.1, "anger": 0.1, "sadness": 0.1, "surprise": 0.1, "fear": 0.1}
        
        words = re.findall(r'\b\w+\b', lower)
        for emotion, keywords in self.emotion_lexicons.items():
            for kw in keywords:
                if kw in lower:
                    weight = 2.0 if kw in words else 1.0
                    counts[emotion] += weight

        # If emotion classifier available
        if self.emotion_model is not None and self.vectorizer is not None:
            try:
                vec = self.vectorizer.transform([text])
                pred_emo = self.emotion_model.predict(vec)[0]
                if pred_emo in counts:
                    counts[pred_emo] += 3.0
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning("Emotion model inference error: %s", e)

        # Sentiment alignment adjustment (re-use score if provided, avoiding redundant inference)
        if sentiment_score is not None:
            sc = sentiment_score
        else:
            sentiment_res = self.analyze_sentiment(text)
            sc = sentiment_res[1]

        if sc > 0.4:
            counts["joy"] += 2.5
        elif sc < -0.4:
            counts["anger"] += 2.0
            counts["sadness"] += 1.5

        total = sum(counts.values())
        proportions = {k: round(v / total, 3) for k, v in counts.items()}
        dominant = max(proportions.items(), key=lambda x: x[1])[0]

        return proportions, dominant

    def classify_intent(self, text: str) -> Tuple[str, float]:
        """
        Classifies user post intent: Complaint, Query, Purchase Intent, Praise, General.
        """
        if self.intent_model is not None and self.vectorizer is not None:
            try:
                vec = self.vectorizer.transform([text])
                pred_intent = self.intent_model.predict(vec)[0]
                probs = self.intent_model.predict_proba(vec)[0]
                conf = float(np.max(probs))
                return pred_intent, round(conf, 2)
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning("Intent model inference error: %s", e)

        lower = text.lower()
        scores = {"complaint": 0.05, "query": 0.05, "purchase_intent": 0.05, "praise": 0.05, "general": 0.1}
        
        for intent, patterns in self.intent_patterns.items():
            for p in patterns:
                matches = len(re.findall(p, lower))
                if matches > 0:
                    scores[intent] += matches * 1.5
        
        dominant_intent = max(scores.items(), key=lambda x: x[1])
        total = sum(scores.values())
        confidence = round(dominant_intent[1] / total, 2)
        
        if scores[dominant_intent[0]] <= 0.1:
            return "general", 0.70
            
        return dominant_intent[0], confidence

    def predict_full_nlp(self, text: str) -> Dict[str, Any]:
        """
        Runs comprehensive inference pipeline on arbitrary text.
        """
        lang = self.detect_language(text)
        sentiment_res = self.analyze_sentiment(text, lang=lang)
        sentiment, score = sentiment_res[0], sentiment_res[1]
        confidence = sentiment_res.confidence
        emotions, dominant_emotion = self.detect_emotions(text)
        intent, intent_conf = self.classify_intent(text)

        probabilities = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
        if self.sentiment_model is not None and self.vectorizer is not None:
            try:
                vec = self.vectorizer.transform([text])
                classes = list(self.sentiment_model.classes_)
                probs = self.sentiment_model.predict_proba(vec)[0]
                for c, p in zip(classes, probs):
                    probabilities[c] = round(float(p), 4)
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning("Sentiment probability calculation error: %s", e)
        
        # If fallback
        if sum(probabilities.values()) == 0:
            if sentiment == "positive":
                probabilities = {"positive": 0.85, "neutral": 0.10, "negative": 0.05}
            elif sentiment == "negative":
                probabilities = {"positive": 0.05, "neutral": 0.15, "negative": 0.80}
            else:
                probabilities = {"positive": 0.15, "neutral": 0.70, "negative": 0.15}

        # Highlight top informative n-grams in input text
        matched_tokens = []
        words = re.findall(r'\b\w+\b', text.lower())
        for w in words:
            if w in self.emotion_lexicons.get("joy", []):
                matched_tokens.append({"word": w, "influence": "positive", "score": "+0.8"})
            elif w in self.emotion_lexicons.get("anger", []) or w in self.emotion_lexicons.get("sadness", []):
                matched_tokens.append({"word": w, "influence": "negative", "score": "-0.8"})

        model_name = self.metrics_data.get("model_name") or "TF-IDF + Calibrated LinearSVC (Linear Classifier)"
        translated_text = self.translate_to_english(text, lang) if lang != "en" else None
        return {
            "text": text,
            "language": lang,
            "translated_text": translated_text,
            "sentiment": sentiment,
            "sentiment_score": score,
            "confidence": confidence,
            "probabilities": probabilities,
            "dominant_emotion": dominant_emotion,
            "emotion_breakdown": emotions,
            "intent": intent,
            "intent_confidence": intent_conf,
            "matched_keywords": matched_tokens,
            "model_engine": model_name,
            "model_statuses": self.get_model_statuses()
        }

    def get_model_metrics(self) -> Dict[str, Any]:
        """Returns the serialized training metrics for the Apple NLP model."""
        metrics = {}
        if self.metrics_data:
            metrics = dict(self.metrics_data)
        else:
            met_path = os.path.join(self.models_dir, "apple_model_metrics.json")
            if os.path.exists(met_path):
                try:
                    with open(met_path, 'r', encoding='utf-8') as f:
                        self.metrics_data = json.load(f)
                    metrics = dict(self.metrics_data)
                except (OSError, IOError, json.JSONDecodeError) as e:
                    logger.warning("Failed reading apple_model_metrics.json: %s", e)
                    metrics = {
                        "status": "not_trained",
                        "message": "Model has not been trained yet. Click 'Train Model' to initiate."
                    }
            else:
                metrics = {
                    "status": "not_trained",
                    "message": "Model has not been trained yet. Click 'Train Model' to initiate."
                }

        metrics["model_statuses"] = self.get_model_statuses()
        return metrics

    def get_dataset_overview(self) -> Dict[str, Any]:
        """Reads dataset stats from apple_smartphone_dataset.csv."""
        csv_path = os.path.join(self.datasets_dir, "apple_smartphone_dataset.csv")
        if not os.path.exists(csv_path):
            return {"status": "not_found", "total_samples": 0}
        
        import pandas as pd
        df = pd.read_csv(csv_path)
        
        sent_counts = df['sentiment'].value_counts().to_dict()
        plat_counts = df['platform'].value_counts().to_dict()
        
        samples = df[['platform', 'text', 'sentiment', 'product_model']].head(10).to_dict(orient='records')
        
        return {
            "dataset_name": "Apple Smartphone & iPhone Multi-Channel Social & Review Dataset",
            "source": "Kaggle (Figure Eight Apple Twitter & Amazon iPhone Customer Reviews)",
            "total_samples": len(df),
            "sentiment_distribution": sent_counts,
            "platform_distribution": plat_counts,
            "sample_records": samples
        }

    def trigger_retraining(self) -> Dict[str, Any]:
        """Re-runs the model training script and reloads model weights into memory."""
        from scripts.train_apple_model import train_apple_models
        metrics = train_apple_models()
        self._load_trained_models()
        return metrics

    def calculate_virality_score(self, reach: int, engagement: int, sentiment_score: float) -> float:
        polarization = abs(sentiment_score) * 1.5
        reach_factor = math.log10(max(reach, 10)) / 6.0
        engagement_factor = math.log10(max(engagement, 1)) / 4.0
        raw_virality = (reach_factor * 0.4 + engagement_factor * 0.4 + polarization * 0.2) * 100.0
        return round(min(max(raw_virality, 5.0), 99.8), 1)

    def extract_preset_topics_and_clusters(
        self,
        texts: List[Dict[str, Any]],
        preset_topics: Optional[List[str]] = None,
        preset_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Groups customer reviews into business preset topics using keyword matching
        instead of KMeans clustering (used when business has fewer than 100 mentions).
        """
        if not texts:
            return []
        p_key = (preset_key or "").lower()
        target_topics = preset_topics
        if not target_topics:
            if "clinic" in p_key:
                target_topics = ["Doctor Care", "Wait Time", "Cleanliness & Hygiene", "Value & Pricing"]
            elif "salon" in p_key:
                target_topics = ["Stylist Skill", "Cleanliness & Hygiene", "Wait Time", "Value & Pricing"]
            elif "restaurant" in p_key:
                target_topics = ["Food Quality", "Service & Staff", "Cleanliness & Hygiene", "Value & Pricing"]
            else:
                target_topics = ["Food Quality", "Service & Staff", "Cleanliness & Hygiene", "Value & Pricing"]

        topics_map: Dict[str, Dict[str, Any]] = {}
        for idx, top in enumerate(target_topics):
            topics_map[top] = {
                "name": top,
                "topic": top,
                "cluster_id": idx,
                "mentions": [],
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "keywords": set()
            }
        
        for item in texts:
            content = item.get("content", "")
            sent = item.get("sentiment", "neutral")
            matched_any = False
            for top_name, top_data in topics_map.items():
                kw_list = self.PRESET_TOPIC_KEYWORDS.get(top_name, [w.lower() for w in top_name.split()])
                matches = [w for w in kw_list if re.search(r'\b' + re.escape(w) + r'\b', content, re.IGNORECASE)]
                if matches:
                    matched_any = True
                    top_data["mentions"].append(item)
                    if sent == "positive":
                        top_data["positive"] += 1
                    elif sent == "negative":
                        top_data["negative"] += 1
                    else:
                        top_data["neutral"] += 1
                    top_data["keywords"].update(matches[:3])
            
            # If no keyword matched, assign to first relevant topic
            if not matched_any and target_topics:
                first_top = target_topics[0]
                topics_map[first_top]["mentions"].append(item)
                if sent == "positive":
                    topics_map[first_top]["positive"] += 1
                elif sent == "negative":
                    topics_map[first_top]["negative"] += 1
                else:
                    topics_map[first_top]["neutral"] += 1

        clusters_result = []
        for top_name, top_data in topics_map.items():
            count = len(top_data["mentions"])
            if count == 0:
                continue
            pos = top_data["positive"]
            neu = top_data["neutral"]
            neg = top_data["negative"]
            dom = "positive" if pos >= neg and pos >= neu else ("negative" if neg >= pos and neg >= neu else "neutral")
            sample = top_data["mentions"][0].get("content", "") if top_data["mentions"] else ""
            clusters_result.append({
                "cluster_id": top_data["cluster_id"],
                "name": top_name,
                "topic": top_name,
                "top_keywords": list(top_data["keywords"])[:5] or [w.lower() for w in top_name.split()[:2]],
                "mentions_count": count,
                "dominant_sentiment": dom,
                "sentiment_breakdown": {
                    "positive": round((pos / count) * 100, 1),
                    "neutral": round((neu / count) * 100, 1),
                    "negative": round((neg / count) * 100, 1)
                },
                "sample_text": sample[:140] + "..." if len(sample) > 140 else sample
            })
        
        clusters_result.sort(key=lambda c: c["mentions_count"], reverse=True)
        return clusters_result

    def extract_topics_and_clusters(
        self,
        texts: List[Dict[str, Any]],
        n_clusters: int = 4,
        preset_topics: Optional[List[str]] = None,
        preset_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts topic clusters from reviews.
        When business has fewer than 100 mentions, uses preset topics with keyword tagging instead of KMeans.
        """
        if not texts:
            return []

        raw_corpus = [item.get("content", "") for item in texts if item.get("content")]
        if len(raw_corpus) < n_clusters and not preset_topics and not preset_key:
            return []

        # Use business-type preset topics when mentions count is under 100
        if len(texts) < 100 or preset_topics or preset_key:
            return self.extract_preset_topics_and_clusters(texts, preset_topics, preset_key)
        
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=250,
            ngram_range=(1, 2)
        )
        
        try:
            X = vectorizer.fit_transform(raw_corpus)
            n_clusters = min(n_clusters, len(raw_corpus))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
            kmeans.fit(X)
            
            terms = vectorizer.get_feature_names_out()
            order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
            
            clusters_result = []
            for i in range(n_clusters):
                cluster_indices = [idx for idx, label in enumerate(kmeans.labels_) if label == i]
                cluster_items = [texts[idx] for idx in cluster_indices]
                if not cluster_items:
                    continue
                
                top_terms = [terms[ind] for ind in order_centroids[i, :5]]
                
                sentiments = [item.get("sentiment", "neutral") for item in cluster_items]
                pos = sentiments.count("positive")
                neu = sentiments.count("neutral")
                neg = sentiments.count("negative")
                total_c = max(len(cluster_items), 1)
                
                dom_sentiment = "positive"
                if neg > pos and neg > neu:
                    dom_sentiment = "negative"
                elif neu > pos and neu > neg:
                    dom_sentiment = "neutral"
                
                top_title = " & ".join([t.title() for t in top_terms[:2]]) + " Discussions" if top_terms else "Topic Cluster"
                sample = cluster_items[0].get("content", "") if cluster_items else ""
                
                clusters_result.append({
                    "cluster_id": i,
                    "name": top_title,
                    "top_keywords": top_terms,
                    "mentions_count": len(cluster_items),
                    "dominant_sentiment": dom_sentiment,
                    "sentiment_breakdown": {
                        "positive": round((pos / total_c) * 100, 1),
                        "neutral": round((neu / total_c) * 100, 1),
                        "negative": round((neg / total_c) * 100, 1)
                    },
                    "sample_text": sample[:140] + "..." if len(sample) > 140 else sample
                })
            
            clusters_result.sort(key=lambda c: c["mentions_count"], reverse=True)
            return clusters_result
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning("Topic clustering failed, falling back to preset topics: %s", e)
            return self.extract_preset_topics_and_clusters(texts, preset_topics)


    def forecast_trends(self, historical_daily_counts: List[Dict[str, Any]], forecast_days: int = 3) -> List[Dict[str, Any]]:
        if not historical_daily_counts or len(historical_daily_counts) < 3:
            return []
        
        vols = [d.get("volume", 0) for d in historical_daily_counts]
        sents = [d.get("sentiment_score", 0.0) for d in historical_daily_counts]
        
        avg_vol = sum(vols[-3:]) / max(len(vols[-3:]), 1)
        avg_sent = sum(sents[-3:]) / max(len(sents[-3:]), 1)
        trend_factor = (vols[-1] - vols[0]) / max(len(vols) - 1, 1)
        sent_trend_factor = (sents[-1] - sents[0]) / max(len(sents) - 1, 1)
        
        forecast = []
        last_date_str = historical_daily_counts[-1].get("date", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"))
        try:
            curr_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d")
        except (ValueError, TypeError) as e:
            logger.warning("Failed parsing date '%s' in forecast_trends, falling back to UTC now: %s", last_date_str, e)
            curr_date = datetime.datetime.now(datetime.timezone.utc)
            
        for day_i in range(1, forecast_days + 1):
            next_date = curr_date + datetime.timedelta(days=day_i)
            # Deterministic linear trend calculation without random noise
            proj_vol = int(max(round(avg_vol + (trend_factor * day_i * 0.6)), 0))
            proj_sent = round(min(max(avg_sent + (sent_trend_factor * day_i * 0.1), -1.0), 1.0), 3)
            
            uncertainty = day_i * 8
            forecast.append({
                "date": next_date.strftime("%b %d"),
                "predicted_volume": proj_vol,
                "predicted_sentiment": proj_sent,
                "lower_bound": max(proj_vol - uncertainty, 0),
                "upper_bound": proj_vol + uncertainty,
                "is_forecast": True
            })
            
        return forecast

    def generate_executive_insights(
        self,
        brand_name: str,
        nss: float,
        top_clusters: List[Dict[str, Any]],
        dominant_emotion: str,
        complaint_rate: float,
        crisis_active: bool
    ) -> Dict[str, Any]:
        sentiment_health = "Strong & Positive" if nss > 30 else ("Moderate / Stable" if nss >= 0 else "Vulnerable / High Risk")
        cluster_names = [c["name"] for c in top_clusters[:2]] if top_clusters else ["Customer Experience"]
        nss_str = f"+{nss}%" if nss > 0 else f"{nss}%"
        
        insights = {
            "health_status": sentiment_health,
            "executive_summary": (
                f"{brand_name}'s digital brand pulse currently displays a Net Sentiment Score of {nss_str}. "
                f"Conversations are predominantly steered by '{', '.join(cluster_names)}'. "
                f"The prevailing audience emotion is '{dominant_emotion.upper()}', with a complaint velocity of {complaint_rate}%."
            ),
            "key_drivers": [
                f"High engagement observed in '{cluster_names[0]}' with {top_clusters[0]['sentiment_breakdown']['positive'] if top_clusters else 70}% positive advocacy.",
                f"Primary customer friction points center around {dominant_emotion if dominant_emotion in ['anger', 'sadness'] else 'response delays and feature inquiries'}.",
                "Emerging cross-channel discussions show expanding purchase intent on LinkedIn and Reddit."
            ],
            "recommended_actions": [
                "Amplify top-performing praise content across verified channels to boost positive Share of Voice.",
                "Deploy proactive CS responses to fast-growing query threads to intercept sentiment churn.",
                "Review crisis triggers and adjust threshold parameters for real-time alert escalation." if not crisis_active else "IMMEDIATE: Execute Crisis PR holding statement on X/Twitter and address user bug reports directly."
            ]
        }
        return insights

    def synthesize_monitored_summary(
        self,
        brand_doc: Dict[str, Any],
        mentions: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        brand_name = brand_doc.get("name", "Apple Inc. (iPhone)")
        industry = brand_doc.get("industry", "Consumer Electronics & Mobile Computing")
        description = brand_doc.get("description", "Global technology leader designing iPhones, iOS, and Apple Silicon chips.")
        competitors = brand_doc.get("competitors", ["Samsung Galaxy", "Google Pixel", "Xiaomi"])
        social_handles = brand_doc.get("social_handles", {})
        keywords = brand_doc.get("keywords", [brand_name, "iPhone", "iOS 18", "Apple Intelligence"])

        product_service = f"{brand_name} Smartphone & iOS Mobile Ecosystem"

        total_mentions = len(mentions)
        pos = sum(1 for m in mentions if m.get("sentiment") == "positive")
        neg = sum(1 for m in mentions if m.get("sentiment") == "negative")
        neu = sum(1 for m in mentions if m.get("sentiment") == "neutral")
        nss = round(((pos - neg) / max(total_mentions, 1)) * 100, 1)

        emotion_totals = {"joy": 0, "anger": 0, "sadness": 0, "surprise": 0, "fear": 0}
        for m in mentions:
            dom = m.get("dominant_emotion", "joy")
            if dom in emotion_totals:
                emotion_totals[dom] += 1
        
        dominant_emotions_list = [
            {"emotion": k.capitalize(), "percentage": round((v / max(total_mentions, 1)) * 100, 1), "count": v}
            for k, v in sorted(emotion_totals.items(), key=lambda x: x[1], reverse=True)
        ]

        complaints = [m for m in mentions if m.get("intent") == "complaint" or m.get("sentiment") == "negative"]
        praises = [m for m in mentions if m.get("intent") == "praise" or m.get("sentiment") == "positive"]
        queries = [m for m in mentions if m.get("intent") == "query"]

        causes = []
        if praises:
            causes.append(f"Positive feedback driven by exceptional camera fidelity, Apple Silicon speed, and iOS fluidity ({len(praises)} praise mentions).")
        
        if complaints:
            sample_complaint = complaints[0].get("content", "")
            if "battery" in sample_complaint.lower() or "charging" in sample_complaint.lower():
                causes.append(f"Customer friction centers on battery longevity and thermal management under intensive gaming ({len(complaints)} complaints).")
            elif "price" in sample_complaint.lower() or "trade" in sample_complaint.lower():
                causes.append(f"Discussions regarding high retail pricing and trade-in valuation tiers ({len(complaints)} mentions).")
            else:
                causes.append(f"Software queries and minor iOS update bug reports on Reddit & X ({len(complaints)} issue threads).")
        else:
            causes.append("General customer engagement and steady brand affinity with no critical anomalies detected.")

        if queries:
            causes.append(f"User inquiries focusing on Apple Intelligence rollout dates, promotion display specs, and trade-in eligibility ({len(queries)} questions).")

        cause_of_feedback_text = " ".join(causes)

        precautions = [
            f"Maintain continuous multi-channel listening across X/Twitter, Reddit, Tech News, and Amazon with negative anomaly triggers at >35%.",
            "Monitor Apple Developer and beta forum telemetry for rapid detection of iOS patch regressions.",
            "Deploy proactive customer success guidance for battery health optimization and trade-in credit transparency.",
            "Perform weekly competitive benchmarking against Samsung Galaxy S24 and Google Pixel 9 Pro."
        ]

        measures_taken = [
            "Executed automated Kaggle-trained ML NLP sentiment & emotion scan across all smartphone review channels.",
            "Flagged high-priority camera feedback to hardware intelligence engineers for upcoming iOS updates.",
            "Synchronized product sentiment telemetry into executive intelligence brief."
        ]
        
        if alerts and any(a.get("status") == "active" for a in alerts):
            measures_taken.append("Activated Tier-1 Crisis Management protocol and initiated rapid developer advisory statement.")
        else:
            measures_taken.append("Verified healthy brand baseline: Net Sentiment Score stable at +" + str(nss) + "%.")

        return {
            "name_of_company": brand_name,
            "product_service": product_service,
            "company_details": {
                "industry": industry,
                "description": description,
                "keywords": keywords,
                "hashtags": brand_doc.get("hashtags", ["#iPhone16", "#AppleIntelligence", "#iOS18"]),
                "social_handles": social_handles,
                "competitors": competitors,
                "website": brand_doc.get("website", "https://apple.com"),
                "owner_organization": brand_doc.get("owner_organization", "Apple Inc.")
            },
            "date": date_str,
            "time": time_str,
            "timestamp": now.isoformat(),
            "cause_of_feedback": cause_of_feedback_text,
            "precautions": precautions,
            "measures_taken": measures_taken,
            "total_mentions_analyzed": total_mentions,
            "net_sentiment_score": nss,
            "sentiment_breakdown": {
                "positive_count": pos,
                "neutral_count": neu,
                "negative_count": neg,
                "positive_percentage": round((pos / max(total_mentions, 1)) * 100, 1),
                "neutral_percentage": round((neu / max(total_mentions, 1)) * 100, 1),
                "negative_percentage": round((neg / max(total_mentions, 1)) * 100, 1)
            },
            "dominant_emotions": dominant_emotions_list,
            "status": "generated"
        }

ai_engine = AIEngine()
