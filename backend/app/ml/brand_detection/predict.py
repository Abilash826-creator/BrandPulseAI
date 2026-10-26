import re
from typing import List, Dict, Any, Optional, Tuple
from app.ml.brand_detection.preprocess import DEFAULT_BRAND_DICTIONARY, clean_text

class BrandDetector:
    def __init__(self, dictionary: Optional[Dict[str, Dict[str, Any]]] = None):
        self.dictionary = dictionary or DEFAULT_BRAND_DICTIONARY

    def register_brand(
        self,
        brand_name: str,
        products: Optional[List[str]] = None,
        services: Optional[List[str]] = None,
        aliases: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        common_spellings: Optional[List[str]] = None,
        disambiguation_negatives: Optional[List[str]] = None,
        business_type: str = "product"
    ):
        """Allows dynamic runtime registration of new product or service businesses."""
        self.dictionary[brand_name] = {
            "brand_names": [brand_name],
            "products": products or [],
            "services": services or [],
            "aliases": aliases or [],
            "hashtags": hashtags or [f"#{brand_name.lower().replace(' ', '')}"],
            "common_spellings": common_spellings or [brand_name.lower()],
            "disambiguation_negatives": disambiguation_negatives or [],
            "business_type": business_type
        }

    def detect(self, text: str, tracked_brands: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Context-aware Brand, Product, and Service detection.
        Returns:
            {
                "brand": Optional[str],
                "product": Optional[str],
                "brand_present": bool,
                "confidence": float,
                "entity_type": Optional[str],
                "matched_terms": List[str]
            }
        """
        text = clean_text(text)
        if not text:
            return {
                "brand": None,
                "product": None,
                "brand_present": False,
                "confidence": 0.0,
                "entity_type": None,
                "matched_terms": []
            }

        text_lower = text.lower()
        candidates: List[Dict[str, Any]] = []

        # Commercial / Tech / Service reinforcement keywords
        commercial_markers = [
            "buy", "bought", "purchase", "order", "delivery", "price", "pricing", "cost", "warranty",
            "customer service", "support", "battery", "camera", "update", "os", "ios", "app", "crash",
            "glitch", "bug", "refund", "store", "features", "spec", "specs", "model", "release",
            "announced", "launched", "unboxing", "review", "upgrade", "trade-in", "device", "hardware",
            "software", "firmware", "subscription", "stream", "streaming", "driver", "ride", "cab",
            "food", "groceries", "valet", "ceo", "company", "earbuds", "headphones", "shoes", "sneakers"
        ]
        has_commercial_context = any(re.search(rf"\b{re.escape(marker)}\b", text_lower) for marker in commercial_markers)

        # Evaluate dictionary
        for brand_name, data in self.dictionary.items():
            matched_products = []
            matched_services = []
            matched_brand_names = []
            matched_hashtags = []
            matched_aliases = []

            # 1. Product Match (e.g. iPhone, Galaxy Buds, PlayStation)
            for prod in data.get("products", []):
                pattern = rf"\b{re.escape(prod.lower())}\b"
                if re.search(pattern, text_lower):
                    matched_products.append(prod)

            # 2. Service Match (e.g. Apple Pay, Swiggy Instamart, Uber Eats)
            for srv in data.get("services", []):
                pattern = rf"\b{re.escape(srv.lower())}\b"
                if re.search(pattern, text_lower):
                    matched_services.append(srv)

            # 3. Hashtags
            for tag in data.get("hashtags", []):
                if tag.lower() in text_lower:
                    matched_hashtags.append(tag)

            # 4. Aliases
            for alias in data.get("aliases", []):
                pattern = rf"\b{re.escape(alias.lower())}\b"
                if re.search(pattern, text_lower):
                    matched_aliases.append(alias)

            # 5. Direct Brand Name Match (e.g. Apple, Samsung, Uber, TCS)
            for b_alias in data.get("brand_names", []):
                pattern = rf"\b{re.escape(b_alias.lower())}\b"
                if re.search(pattern, text_lower):
                    matched_brand_names.append(b_alias)

            total_matches = len(matched_products) + len(matched_services) + len(matched_hashtags) + len(matched_aliases) + len(matched_brand_names)

            if total_matches > 0:
                # Disambiguation Check: Check for negative non-brand contexts
                is_hard_negative = False
                for neg in data.get("disambiguation_negatives", []):
                    if neg in text_lower:
                        is_hard_negative = True
                        break

                # If hard negative pattern found, only allow if explicit strong product or service matched
                if is_hard_negative and not (matched_products or matched_services):
                    # Ambiguous common word (e.g. "I ate an apple yesterday", "Apple trees are beautiful", "row your boat", "uber cool")
                    continue

                # Calculate confidence score
                confidence = 0.85
                if matched_products and matched_brand_names:
                    confidence = 0.99
                elif matched_products or matched_services:
                    confidence = 0.98
                elif matched_brand_names and has_commercial_context:
                    confidence = 0.96
                elif matched_brand_names and matched_hashtags:
                    confidence = 0.97
                elif matched_brand_names:
                    # Generic brand mention without explicit product
                    # If brand name is an ambiguous common word (Apple, boAt, Uber, Nike), check commercial context
                    if brand_name.lower() in ["apple", "boat", "uber", "nike"] and not has_commercial_context:
                        confidence = 0.50
                    else:
                        confidence = 0.92

                # Determine primary detected product/service
                detected_product = None
                if matched_products:
                    detected_product = matched_products[0]
                elif matched_services:
                    detected_product = matched_services[0]

                all_matched_terms = matched_products + matched_services + matched_brand_names + matched_hashtags + matched_aliases

                candidates.append({
                    "brand": brand_name,
                    "product": detected_product,
                    "brand_present": True,
                    "confidence": round(confidence, 4),
                    "entity_type": data.get("business_type", "product"),
                    "matched_terms": list(set(all_matched_terms))
                })

        # If tracked_brands is provided, prioritize / filter by tracked brand
        if tracked_brands:
            tracked_candidates = [c for c in candidates if c["brand"] in tracked_brands]
            if tracked_candidates:
                # Return highest confidence candidate
                tracked_candidates.sort(key=lambda x: x["confidence"], reverse=True)
                return tracked_candidates[0]
            else:
                # If text does not mention the tracked brand (or mentions irrelevant / competitor)
                return {
                    "brand": None,
                    "product": None,
                    "brand_present": False,
                    "confidence": 0.0,
                    "entity_type": None,
                    "matched_terms": []
                }

        if candidates:
            # Sort by confidence descending
            candidates.sort(key=lambda x: x["confidence"], reverse=True)
            top_candidate = candidates[0]
            if top_candidate["confidence"] >= 0.70:
                return top_candidate

        return {
            "brand": None,
            "product": None,
            "brand_present": False,
            "confidence": 0.0,
            "entity_type": None,
            "matched_terms": []
        }

brand_detector = BrandDetector()
