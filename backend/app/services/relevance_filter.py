"""
Relevance Filter, Brand Disambiguation & Context Intelligence Service for BrandPulse AI.
Accurately distinguishes brand/product entities from generic homonyms,
extracts granular product aspects, and detects sarcasm/negation patterns.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from app.services.ai_engine import ai_engine
from app.ml.brand_detection.predict import brand_detector
from app.ml.brand_detection.preprocess import DEFAULT_BRAND_DICTIONARY

logger = logging.getLogger("brandpulse.relevance")

class RelevanceFilter:
    def __init__(self):
        # Product Aspect Taxonomy & Associated Keywords
        self.aspect_keywords = {
            "battery": [
                "battery", "battery life", "battery health", "drained", "drain", "draining",
                "screen on time", "sot", "battery test", "battery backup", "power consumption"
            ],
            "camera": [
                "camera", "cameras", "zoom", "lens", "lenses", "sensor", "low-light",
                "megapixels", "photography", "photos", "photo quality", "portrait mode",
                "cinematic mode", "video quality", "4k", "optical zoom"
            ],
            "display": [
                "display", "screen", "oled", "amoled", "120hz", "promotion", "refresh rate",
                "brightness", "nits", "resolution", "bezel", "bezels", "always on display"
            ],
            "charging": [
                "charging", "charger", "fast charging", "charging speed", "usb-c", "magsafe",
                "wireless charging", "overheating while charging", "slow charge", "25w", "45w"
            ],
            "performance": [
                "performance", "speed", "fast", "smooth", "fluid", "lag", "stutter",
                "gaming", "fps", "chip", "processor", "a18", "snapdragon", "ram", "heat", "thermal"
            ],
            "build_quality": [
                "build quality", "titanium", "durability", "finish", "scratches", "shatter",
                "heavy", "lightweight", "feel in hand", "ergonomics", "colors", "buttons"
            ],
            "software_os": [
                "ios", "ios 18", "software", "firmware", "update", "apple intelligence",
                "ai features", "bug", "bugs", "glitch", "crash", "crashing", "apps", "interface"
            ],
            "customer_service": [
                "customer service", "customer support", "support", "applecare", "store",
                "genius bar", "warranty", "replacement", "refund", "technician", "repair"
            ],
            "pricing_value": [
                "price", "pricing", "cost", "expensive", "overpriced", "cheap", "worth it",
                "worth the money", "value for money", "discount", "trade-in", "bill", "billing"
            ],
            "food_taste": [
                "taste", "delicious", "crispy", "flavor", "tasty", "ghee roast", "dosa",
                "rava dosa", "chutney", "podi", "meals", "thali", "curd rice", "rasam", "poriyal", "payasam"
            ],
            "filter_coffee": [
                "filter coffee", "coffee", "degree coffee", "aroma", "froth", "brass tumbler",
                "davarah", "chicory", "hot coffee", "morning coffee"
            ],
            "sambar_flavor": [
                "sambar", "sambar vada", "shallots", "sambar dip", "sambar recipe",
                "idli sambar", "drumstick sambar"
            ],
            "waiting_time": [
                "waiting time", "wait time", "queue", "token", "crowd", "crowded",
                "rush", "long wait", "table waiting", "standing in line"
            ],
            "service_speed": [
                "service", "service speed", "waiter", "staff", "attentive", "slow service",
                "fast service", "table turnover", "courtesy", "hospitality"
            ],
            "cleanliness_hygiene": [
                "hygiene", "clean", "cleanliness", "sanitized", "neat", "washroom",
                "steel tumbler", "banana leaf", "dining hall"
            ],
            "parking_access": [
                "parking", "car parking", "valet", "traffic", "congestion", "two wheeler parking",
                "rs puram", "gandhipuram"
            ]
        }

        # Common fruit / non-brand disambiguation terms (for Apple, Orange, etc.)
        self.hard_fruit_negatives = [
            "eat", "ate", "eating", "eaten", "delicious", "tasty", "breakfast", "lunch", "dinner",
            "snack", "recipe", "juice", "cider", "pie", "orchard", "tree", "trees", "fruit",
            "fruits", "salad", "smoothie", "organic", "fresh", "crisp", "caramel", "cinnamon",
            "sweet", "sour", "grocery", "groceries", "calories", "diet", "nutrition"
        ]

        # Common celestial / astronomy disambiguation terms (for Galaxy)
        self.hard_space_negatives = [
            "milky way", "andromeda", "telescope", "stars", "nebula", "astronomy", "universe",
            "deep space", "space exploration", "nasa", "james webb"
        ]

        # Negation markers
        self.negation_patterns = [
            r"\b(not|never|no|hardly|scarcely|barely|without|neither|nor)\b",
            r"\b(isn't|aren't|wasn't|weren't|haven't|hasn't|hadn't|won't|wouldn't|don't|doesn't|didn't|can't|couldn't)\b"
        ]

        # Sarcasm / Irony cues
        self.sarcasm_patterns = [
            r"(wow|great|amazing|wonderful|brilliant|lightning fast)\W+.*\b(died in|broke in|crashed in|useless|terrible|worst|scam|garbage|wait|waited|waiting)\b",
            r"\bwhat a (battery|service|deal|experience|quality)\b.*\b(died|failed|broke|sucks|nightmare|disaster)\b",
            r"\b(lightning fast|fast service|quick service)\b.*\b(wait|waited|waiting|hours|minutes)\b",
            r"\bthanks a lot\b.*\b(ruined|wasted|broken|broke)\b",
            r"(!\?|\?!|🙄|🤦‍♂️|🤦‍♀️|🤡)"
        ]

    def analyze(
        self,
        text: str,
        brand_name: str = "Apple",
        tracked_products: Optional[List[str]] = None,
        tracked_keywords: Optional[List[str]] = None,
        tracked_hashtags: Optional[List[str]] = None,
        competitors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates text for brand relevance, product mentions, context, negation, sarcasm, and aspects.
        """
        if not text or not text.strip():
            return {
                "relevance_score": 0.0,
                "brand_detected": False,
                "product_detected": None,
                "detected_brands": [],
                "detected_products": [],
                "matched_keywords": [],
                "matched_hashtags": [],
                "aspects": [],
                "context": {"sarcasm": False, "negation": False, "intent": "general"},
                "reason": "Empty text provided"
            }

        text_lower = text.lower()
        clean_words = set(re.findall(r'\b\w+\b', text_lower))

        # 1. Check Brand & Product Detection via Trained ML Model & Dictionary
        tracked_brand_list = [brand_name]
        if competitors:
            tracked_brand_list.extend(competitors)

        det_result = brand_detector.detect(text, tracked_brands=tracked_brand_list)
        
        # 2. Check Custom Tracked Products & Keywords
        matched_products = []
        if tracked_products:
            for prod in tracked_products:
                if re.search(rf"\b{re.escape(prod.lower())}\b", text_lower):
                    matched_products.append(prod)
        if det_result.get("product") and det_result["product"] not in matched_products:
            matched_products.append(det_result["product"])

        matched_keywords = []
        if tracked_keywords:
            for kw in tracked_keywords:
                if re.search(rf"\b{re.escape(kw.lower())}\b", text_lower):
                    matched_keywords.append(kw)

        matched_hashtags = []
        if tracked_hashtags:
            for tag in tracked_hashtags:
                clean_t = tag.lower()
                if clean_t in text_lower:
                    matched_hashtags.append(tag)
        # Extract any embedded #hashtag in text
        raw_hashtags = re.findall(r'#\w+', text)
        for h in raw_hashtags:
            if h.lower() in [t.lower() for t in (tracked_hashtags or [])] or brand_name.lower() in h.lower():
                if h not in matched_hashtags:
                    matched_hashtags.append(h)

        # 3. Disambiguation Logic (e.g. Apple fruit vs Apple Inc)
        is_hard_negative = False
        if brand_name.lower() == "apple":
            fruit_matches = [w for w in self.hard_fruit_negatives if re.search(rf"\b{re.escape(w)}\b", text_lower)]
            # If text talks about food/fruit and doesn't mention iPhone/Mac/AirPods/tech
            tech_markers = ["iphone", "ipad", "macbook", "airpods", "ios", "apple watch", "vision pro", "applecare", "tim cook", "tech", "device", "specs", "app"]
            has_tech_context = any(re.search(rf"\b{re.escape(tm)}\b", text_lower) for tm in tech_markers)
            if fruit_matches and not has_tech_context:
                is_hard_negative = True

        elif "annapoorna" in brand_name.lower():
            temple_markers = ["temple", "pooja", "stotram", "goddess", "himalayan", "mountain", "sanctuary", "circuit", "trek"]
            temple_matches = [w for w in temple_markers if re.search(rf"\b{re.escape(w)}\b", text_lower)]
            food_markers = ["dosa", "coffee", "roast", "sambar", "vada", "hotel", "restaurant", "meals", "coimbatore", "rs puram", "gandhipuram", "breakfast", "lunch", "dinner", "tiffin", "sweet", "mysurpa"]
            has_food_context = any(re.search(rf"\b{re.escape(fm)}\b", text_lower) for fm in food_markers)
            if temple_matches and not has_food_context:
                is_hard_negative = True

        # 4. Calculate Relevance Score & Reason
        if is_hard_negative:
            brand_detected = False
            primary_product = None
            relevance_score = 0.01
            reason = f"Identified generic homonym context (e.g. food/fruit or celestial topic) unrelated to {brand_name}."
        elif matched_products and brand_name.lower() in text_lower:
            brand_detected = True
            primary_product = matched_products[0]
            relevance_score = 0.96
            reason = f"High-confidence match: Explicit mention of {brand_name} and product ({primary_product})."
        elif matched_products:
            brand_detected = True
            primary_product = matched_products[0]
            relevance_score = 0.94
            reason = f"Strong product-specific mention ({primary_product}) strongly associated with {brand_name}."
        elif brand_name.lower() in text_lower and (matched_keywords or matched_hashtags):
            brand_detected = True
            primary_product = None
            relevance_score = 0.88
            reason = f"Direct {brand_name} mention with tracked keywords/hashtags ({', '.join(matched_keywords + matched_hashtags)})."
        elif det_result.get("brand_present") and det_result.get("brand") == brand_name:
            brand_detected = True
            primary_product = det_result.get("product")
            relevance_score = det_result.get("confidence", 0.85)
            reason = f"Brand detected via entity recognition engine with confidence {relevance_score}."
        elif brand_name.lower() in text_lower:
            brand_detected = True
            primary_product = None
            relevance_score = 0.72
            reason = f"Generic brand name mention without explicit product/commercial modifiers."
        else:
            brand_detected = False
            primary_product = None
            relevance_score = 0.05
            reason = f"No direct match or commercial entity found for {brand_name}."

        # 5. Context Analysis: Negation & Sarcasm
        has_negation = any(re.search(p, text_lower) for p in self.negation_patterns)
        has_sarcasm = any(re.search(p, text_lower) for p in self.sarcasm_patterns)

        # 6. Intent Classification
        intent, intent_conf = ai_engine.classify_intent(text)

        # 7. Aspect Extraction & Sentiment per Aspect
        extracted_aspects = []
        for aspect_name, kws in self.aspect_keywords.items():
            matched_aspect_kws = [k for k in kws if re.search(rf"\b{re.escape(k)}\b", text_lower)]
            if matched_aspect_kws:
                # Find sentences or clauses containing the aspect
                clauses = re.split(r'[.,;!?\n]', text)
                relevant_clauses = [c for c in clauses if any(k in c.lower() for k in matched_aspect_kws)]
                aspect_snippet = " ".join(relevant_clauses) if relevant_clauses else text

                # Analyze sentiment of aspect snippet
                asp_sent, asp_score = ai_engine.analyze_sentiment(aspect_snippet)

                # If sarcasm or severe complaint clause is detected, flip or penalize sentiment
                if has_sarcasm and ("battery" in aspect_name or "camera" in aspect_name or "performance" in aspect_name):
                    if "died" in text_lower or "broke" in text_lower or "2 hours" in text_lower:
                        asp_sent = "negative"
                        asp_score = -0.75

                extracted_aspects.append({
                    "aspect": aspect_name,
                    "sentiment": asp_sent,
                    "sentiment_score": asp_score,
                    "matched_terms": matched_aspect_kws
                })

        return {
            "relevance_score": round(relevance_score, 3),
            "brand_detected": brand_detected,
            "product_detected": primary_product,
            "detected_brands": [brand_name] if brand_detected else [],
            "detected_products": matched_products,
            "matched_keywords": matched_keywords,
            "matched_hashtags": matched_hashtags,
            "aspects": extracted_aspects,
            "context": {
                "sarcasm": has_sarcasm,
                "negation": has_negation,
                "intent": intent
            },
            "reason": reason
        }

relevance_filter = RelevanceFilter()
