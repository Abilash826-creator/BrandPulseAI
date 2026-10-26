import os
import io
import re
import csv
import json
import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

import pypdf
from app.core.database import get_db, clean_doc, clean_docs
from app.services.ai_engine import ai_engine
from app.services.relevance_filter import relevance_filter
from app.services.crisis_detector import crisis_detector

logger = logging.getLogger("brandpulse.dataset_ingestor")

class DatasetIngestor:
    """
    Enterprise Dataset Ingestion & AI Parsing Service.
    Supports CSV, PDF, TXT, and JSON ingestion.
    Extracts text records, disambiguates Brand & Product entities,
    computes full AI inferences (sentiment, emotion, intent, ABSA),
    and updates MongoDB collections & Live Dashboard metrics.
    """

    KNOWN_PRODUCT_PATTERNS = [
        # Tech & Electronics
        r"(iPhone\s*(?:16|15|14|13|12|11)?\s*(?:Pro\s*Max|Pro|Plus|Mini)?)",
        r"(MacBook\s*(?:Pro|Air)\s*(?:M\d)?)",
        r"(iPad\s*(?:Pro|Air|Mini)?)",
        r"(Apple\s*Watch\s*(?:Ultra|Series\s*\d)?)",
        r"(AirPods\s*(?:Pro|Max|3|2)?)",
        r"(Apple\s*Intelligence|iOS\s*\d+|Vision\s*Pro)",
        r"(Galaxy\s*S\d+\s*(?:Ultra|Plus|\+)?)",
        r"(Pixel\s*\d+\s*(?:Pro)?)",
        # Hospitality / Food
        r"(Ghee\s*Roast(?:\s*Dosa)?)",
        r"(Filter\s*Coffee|Degree\s*Coffee)",
        r"(Sambar\s*(?:Vada|Dip)?)",
        r"(Rava\s*Dosa|Onion\s*Rava)",
        r"(Poori\s*Masala|Meals\s*Thali)",
        r"(Mysurpa|Badam\s*Halwa)",
        # Enterprise Software
        r"(Cloud\s*Platform|AI\s*Analytics\s*Suite|Enterprise\s*API|Brand\s*Pulse\s*AI)"
    ]

    def __init__(self):
        pass

    def preview_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Generates a lightweight preview of uploaded CSV or PDF before full ingestion.
        """
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            return self._preview_csv(file_bytes)
        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            return self._preview_excel(file_bytes)
        elif filename_lower.endswith(".pdf"):
            return self._preview_pdf(file_bytes)
        elif filename_lower.endswith(".json"):
            return self._preview_json(file_bytes)
        elif filename_lower.endswith(".txt"):
            return self._preview_txt(file_bytes)
        else:
            raise ValueError("Unsupported file format. Please upload a .csv, .xlsx, .xls, .pdf, .json, or .txt file.")


    def _preview_csv(self, file_bytes: bytes) -> Dict[str, Any]:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8", nrows=10, on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1", nrows=10, on_bad_lines='skip')
            except Exception:
                # Fallback to standard csv module
                text = file_bytes.decode('utf-8', errors='ignore')
                reader = csv.reader(io.StringIO(text))
                rows = list(reader)[:11]
                if rows:
                    cols = rows[0]
                    data = rows[1:]
                    df = pd.DataFrame(data, columns=cols if len(cols) == len(data[0]) else None)
                else:
                    df = pd.DataFrame()

        columns = list(df.columns)
        detected_text_col = self._detect_text_column(columns)
        detected_product_col = self._detect_product_column(columns)
        sample_rows = df.fillna("").to_dict(orient="records")

        # Extract potential product names from sample rows
        extracted_products = []
        if detected_product_col:
            extracted_products = list(set([str(r[detected_product_col]).strip() for r in sample_rows if str(r.get(detected_product_col, "")).strip()]))[:5]
        else:
            # Look in text
            sample_text = " ".join([str(r.get(detected_text_col, "")) for r in sample_rows])
            extracted_products = self._extract_products_from_text(sample_text)

        return {
            "format": "csv",
            "total_preview_rows": len(sample_rows),
            "columns": columns,
            "detected_text_column": detected_text_col,
            "detected_product_column": detected_product_col,
            "extracted_products": extracted_products,
            "sample_records": sample_rows[:5]
        }

    def _preview_excel(self, file_bytes: bytes) -> Dict[str, Any]:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), nrows=10)
        except Exception as e:
            logger.error(f"Failed to read Excel preview: {e}")
            raise ValueError(f"Unable to read Excel file: {e}")

        columns = [str(c) for c in df.columns]
        detected_text_col = self._detect_text_column(columns)
        detected_product_col = self._detect_product_column(columns)
        sample_rows = df.fillna("").to_dict(orient="records")

        extracted_products = []
        if detected_product_col:
            extracted_products = list(set([str(r[detected_product_col]).strip() for r in sample_rows if str(r.get(detected_product_col, "")).strip()]))[:5]
        else:
            sample_text = " ".join([str(r.get(detected_text_col, "")) for r in sample_rows])
            extracted_products = self._extract_products_from_text(sample_text)

        return {
            "format": "excel",
            "total_preview_rows": len(sample_rows),
            "columns": columns,
            "detected_text_column": detected_text_col,
            "detected_product_column": detected_product_col,
            "extracted_products": extracted_products,
            "sample_records": sample_rows[:5]
        }


    def _preview_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        num_pages = len(reader.pages)
        sample_text = ""
        for i in range(min(num_pages, 3)):
            sample_text += reader.pages[i].extract_text() or ""

        chunks = self._segment_pdf_text(sample_text)
        extracted_products = self._extract_products_from_text(sample_text)
        brand_guess = self._extract_brand_from_text(sample_text)

        return {
            "format": "pdf",
            "total_pages": num_pages,
            "extracted_chunks_count": len(chunks),
            "brand_guess": brand_guess,
            "extracted_products": extracted_products,
            "sample_records": [{"content": c[:250] + ("..." if len(c) > 250 else "")} for c in chunks[:5]]
        }

    def _preview_json(self, file_bytes: bytes) -> Dict[str, Any]:
        data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
        if isinstance(data, dict):
            items = data.get("mentions", data.get("reviews", data.get("data", [data])))
        elif isinstance(data, list):
            items = data
        else:
            items = []

        sample_items = items[:5]
        sample_text = " ".join([str(item.get("content", item.get("text", ""))) for item in sample_items if isinstance(item, dict)])
        extracted_products = self._extract_products_from_text(sample_text)

        return {
            "format": "json",
            "total_preview_rows": len(items),
            "extracted_products": extracted_products,
            "sample_records": sample_items
        }

    def _preview_txt(self, file_bytes: bytes) -> Dict[str, Any]:
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        sample_text = " ".join(lines[:10])
        extracted_products = self._extract_products_from_text(sample_text)

        return {
            "format": "txt",
            "total_lines": len(lines),
            "extracted_products": extracted_products,
            "sample_records": [{"content": l} for l in lines[:5]]
        }

    # =========================================================================
    # FULL INGESTION & AI SCORING PIPELINE
    # =========================================================================
    async def process_and_ingest(
        self,
        file_bytes: bytes,
        filename: str,
        brand_id: Optional[str] = None,
        brand_name: Optional[str] = None,
        product_name: Optional[str] = None,
        industry: Optional[str] = None,
        mode: str = "append", # "append" or "replace"
        generate_summary: bool = True,
        current_user: Optional[Dict[str, Any]] = None,
        is_simulated: bool = False
    ) -> Dict[str, Any]:
        """
        Executes full ingestion:
        1. Parses records from CSV/PDF/JSON/TXT
        2. Disambiguates Brand & Product Names
        3. Runs Batch AI Multitask Scoring (Sentiment, Emotion, Intent, ABSA)
        4. Updates MongoDB (brands, mentions, summaries, alerts)
        5. Returns complete dashboard-ready analytics
        """
        db = get_db()
        filename_lower = filename.lower()

        # Step 1: Parse raw records
        if filename_lower.endswith(".csv"):
            raw_records = self._parse_csv_records(file_bytes)
        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            raw_records = self._parse_excel_records(file_bytes)
        elif filename_lower.endswith(".pdf"):
            raw_records = self._parse_pdf_records(file_bytes)
        elif filename_lower.endswith(".json"):
            raw_records = self._parse_json_records(file_bytes)
        elif filename_lower.endswith(".txt"):
            raw_records = self._parse_txt_records(file_bytes)
        else:
            raise ValueError("Unsupported format. Allowed: .csv, .xlsx, .xls, .pdf, .json, .txt")


        if not raw_records:
            raise ValueError("Could not extract any valid feedback or mention records from the uploaded file.")

        # Step 2: Auto-detect or resolve Brand & Product Names
        all_text = " ".join([r["content"] for r in raw_records[:50]])
        detected_brand = brand_name or self._extract_brand_from_filename_or_text(filename, all_text) or "Enterprise Brand"
        
        detected_products = []
        if product_name and product_name.strip() and len(product_name.strip()) <= 40:
            detected_products.append(product_name.strip())
        
        # Discover products from individual record metadata or text
        for r in raw_records:
            if r.get("product"):
                p_clean = str(r["product"]).strip()
                if p_clean and p_clean not in detected_products and len(p_clean) <= 40 and not any(p_clean.endswith(x) for x in ['.', '!', '?']):
                    detected_products.append(p_clean)

        discovered_from_text = self._extract_products_from_text(all_text)
        for dp in discovered_from_text:
            if dp not in detected_products and len(dp) <= 40:
                detected_products.append(dp)

        # Fallback contextual product names if none detected
        if not detected_products:
            lower_txt = all_text.lower()
            if any(w in lower_txt for w in ["hotel", "room", "stay", "resort", "suite", "breakfast", "staff", "booking"]):
                detected_products = ["Deluxe Rooms & Suites", "Hospitality & Guest Experience", "Dining & Breakfast"]
            elif any(w in lower_txt for w in ["food", "dosa", "coffee", "roast", "restaurant"]):
                detected_products = ["Signature Dishes", "Beverages & Coffee", "Dining Experience"]
            elif any(w in lower_txt for w in ["phone", "camera", "battery", "screen", "ios"]):
                detected_products = ["Flagship Smartphone", "Camera & Display", "Battery & OS"]
            else:
                detected_products = ["Core Product Platform", "Customer Experience"]

        primary_product = detected_products[0]

        # Step 3: Resolve / Create Target Brand Document in MongoDB
        target_brand_doc = None
        if brand_id:
            target_brand_doc = await db["brands"].find_one({"id": brand_id})
        
        if not target_brand_doc and brand_name:
            target_brand_doc = await db["brands"].find_one({"name": {"$regex": f"^{re.escape(brand_name)}$", "$options": "i"}})

        if not target_brand_doc:
            # Create Brand Document
            new_brand_id = f"brand_{uuid.uuid4().hex[:8]}"
            owner_id = current_user.get("id", "usr_admin") if current_user else "usr_admin"
            
            # Infer industry
            inferred_industry = industry
            if not inferred_industry:
                lower_b = (detected_brand + " " + all_text[:200]).lower()
                if any(w in lower_b for w in ["hotel", "resort", "stay", "villa", "suites", "inn"]):
                    inferred_industry = "Hospitality, Travel & Resorts"
                elif any(w in lower_b for w in ["apple", "tech", "cloud", "pixel", "samsung", "software", "api"]):
                    inferred_industry = "Consumer Electronics & Technology"
                elif any(w in lower_b for w in ["annapoorna", "restaurant", "cafe", "food", "dining"]):
                    inferred_industry = "Hospitality & Food Services"
                else:
                    inferred_industry = "Enterprise Products & Services"

            target_brand_doc = {
                "id": new_brand_id,
                "owner_id": owner_id,
                "name": detected_brand,
                "industry": inferred_industry,
                "description": f"Auto-configured brand profile from dataset: {filename}",
                "products": detected_products,
                "keywords": [detected_brand] + [p for p in detected_products[:3]],
                "hashtags": [f"#{detected_brand.replace(' ', '')}"],
                "social_handles": {
                    "twitter": f"@{detected_brand.replace(' ', '')}",
                    "instagram": f"@{detected_brand.lower().replace(' ', '')}"
                },
                "competitors": [],
                "crisis_threshold_negative": 0.35,
                "is_primary": True,
                "created_at": datetime.datetime.now().isoformat()
            }
            await db["brands"].insert_one(target_brand_doc)
            
            # Associate with user
            if current_user and "id" in current_user:
                await db["users"].update_one(
                    {"id": current_user["id"]},
                    {"$addToSet": {"brand_ids": new_brand_id}}
                )
            logger.info(f"Created new brand document {new_brand_id} for {detected_brand}")
        else:
            # Update existing brand with newly detected products & keywords
            merged_products = list(set(target_brand_doc.get("products", []) + detected_products))
            merged_keywords = list(set(target_brand_doc.get("keywords", []) + [detected_brand] + detected_products[:3]))
            
            await db["brands"].update_one(
                {"id": target_brand_doc["id"]},
                {"$set": {
                    "products": merged_products,
                    "keywords": merged_keywords,
                    "updated_at": datetime.datetime.now().isoformat()
                }}
            )
            target_brand_doc["products"] = merged_products

        target_brand_id = target_brand_doc["id"]
        brand_display_name = target_brand_doc.get("name", detected_brand)

        # Enforce review quota limits (Free tier: max 100 reviews/mo)
        if not is_simulated:
            from app.services.plan_limits import check_can_add_reviews
            await check_can_add_reviews(target_brand_id, len(raw_records), db, current_user)

        # Archive raw upload behind storage interface
        try:
            from app.core.storage import get_storage
            get_storage().save(f"upload_{target_brand_id}_{filename}", file_bytes)
        except Exception as e:
            logger.warning(f"Could not archive raw upload to storage: {e}")

        # If mode == "replace", clear previous mentions for this brand
        if mode == "replace":
            await db["mentions"].delete_many({"brand_id": target_brand_id})
            logger.info(f"Cleared existing mentions for brand {target_brand_id} (replace mode)")

        # Step 4: Run AI Pipeline on all records
        processed_mentions = []
        positive_count = 0
        neutral_count = 0
        negative_count = 0
        sentiment_scores = []
        emotions_agg = {"joy": 0, "anger": 0, "sadness": 0, "surprise": 0, "fear": 0}
        aspect_praise_counts = {}
        aspect_friction_counts = {}

        now_dt = datetime.datetime.now()

        for idx, rec in enumerate(raw_records):
            content = rec["content"]
            
            # AI Inference & Multilingual Support
            lang = ai_engine.detect_language(content)
            translated_text = ai_engine.translate_to_english(content, lang) if lang != "en" else None
            sentiment_res = ai_engine.analyze_sentiment(content, lang=lang)
            sentiment, sent_score = sentiment_res[0], sentiment_res[1]
            emotions, dominant_emotion = ai_engine.detect_emotions(content)
            intent, intent_confidence = ai_engine.classify_intent(content)
            
            # Relevance and Aspects
            rel_res = relevance_filter.analyze(
                text=content,
                brand_name=brand_display_name,
                tracked_products=detected_products,
                tracked_keywords=target_brand_doc.get("keywords", [])
            )

            # Preset topic tagging with fallback to aspects
            preset_key = target_brand_doc.get("preset_key") or target_brand_doc.get("industry")
            tagged_topics = ai_engine.tag_preset_topics(content, preset_key)
            if not tagged_topics and rel_res.get("aspects"):
                tagged_topics = [a["aspect"] for a in rel_res.get("aspects", [])]

            # Aggregate stats
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1

            sentiment_scores.append(sent_score)
            emotions_agg[dominant_emotion] = emotions_agg.get(dominant_emotion, 0) + 1

            # Count aspects
            for aspect_item in rel_res.get("aspects", []):
                asp_name = aspect_item.get("aspect", "").replace("_", " ").title()
                asp_sent = aspect_item.get("sentiment", "neutral")
                if asp_sent == "positive":
                    aspect_praise_counts[asp_name] = aspect_praise_counts.get(asp_name, 0) + 1
                elif asp_sent == "negative":
                    aspect_friction_counts[asp_name] = aspect_friction_counts.get(asp_name, 0) + 1

            # Determine timestamp
            rec_time = rec.get("timestamp")
            if not rec_time:
                # Spread over past 7 days
                offset_hours = (len(raw_records) - idx) * (168.0 / max(len(raw_records), 1))
                rec_dt = now_dt - datetime.timedelta(hours=offset_hours)
                rec_time = rec_dt.isoformat()

            author = rec.get("author") or f"Customer_{idx+1}"
            author_handle = rec.get("author_handle") or f"user_{idx+1}"
            reach = int(rec.get("reach") or (500 + (idx * 37) % 4500))
            eng = int(rec.get("engagement") or max(int(reach * 0.04), 10))
            virality = ai_engine.calculate_virality_score(reach, eng, sent_score)

            mention_doc = {
                "id": f"ds_men_{uuid.uuid4().hex[:10]}",
                "brand_id": target_brand_id,
                "brand_name": brand_display_name,
                "platform": rec.get("platform") or ("PDF Ingest" if filename_lower.endswith(".pdf") else "CSV Dataset"),
                "author": author,
                "author_handle": author_handle,
                "author_followers": reach,
                "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={author_handle}",
                "content": content,
                "product_name": rec.get("product") or primary_product,
                "sentiment": sentiment,
                "sentiment_score": sent_score,
                "sentiment_confidence": getattr(sentiment_res, "confidence", 0.9),
                "emotions": emotions,
                "dominant_emotion": dominant_emotion,
                "intent": intent,
                "intent_confidence": intent_confidence,
                "reach": reach,
                "engagement_score": eng,
                "virality_score": virality,
                "is_crisis_flag": (sentiment == "negative" and (virality > 65.0 or dominant_emotion in ["anger", "fear"])),
                "is_simulated": is_simulated,
                "business_id": target_brand_id,
                "language": lang,
                "original_text": content,
                "translated_text": translated_text,
                "source": rec.get("platform") or ("PDF Ingest" if filename_lower.endswith(".pdf") else "CSV Dataset"),
                "rating": rec.get("rating", 5 if sentiment == "positive" else (1 if sentiment == "negative" else 3)),
                "topics": tagged_topics,
                "created_at": rec_time,
                "relevance_score": rel_res.get("relevance_score", 0.95),
                "aspects": rel_res.get("aspects", []),
                "aspect_ratings": {a["aspect"]: (1.0 if a["sentiment"] == "positive" else -1.0) for a in rel_res.get("aspects", [])},
                "context": rel_res.get("context", {}),
                "timestamp": rec_time,
                "dataset_source": filename
            }
            processed_mentions.append(mention_doc)

        # Step 5: Save Mentions in bulk to MongoDB
        if processed_mentions:
            await db["mentions"].insert_many(processed_mentions)
            logger.info(f"Ingested {len(processed_mentions)} records into db.mentions for brand {target_brand_id}")

        # Compute dataset summary metrics
        total_records = len(processed_mentions)
        pos_pct = (positive_count / max(total_records, 1)) * 100
        neg_pct = (negative_count / max(total_records, 1)) * 100
        nss = round(pos_pct - neg_pct, 1)
        avg_sentiment = round(sum(sentiment_scores) / max(len(sentiment_scores), 1), 3)

        # Top Praise & Top Complaints list
        top_praise = sorted([{"aspect": k, "count": v} for k, v in aspect_praise_counts.items()], key=lambda x: x["count"], reverse=True)[:5]
        top_friction = sorted([{"aspect": k, "count": v} for k, v in aspect_friction_counts.items()], key=lambda x: x["count"], reverse=True)[:5]

        # Step 6: Generate Monitored Summary document in MongoDB
        summary_doc = None
        if generate_summary and total_records > 0:
            summary_id = f"sum_{uuid.uuid4().hex[:8]}"
            
            praise_terms = ", ".join([p["aspect"] for p in top_praise[:3]]) or "general quality"
            friction_terms = ", ".join([f["aspect"] for f in top_friction[:2]]) or "isolated customer queries"

            cause_str = (
                f"Dataset analysis across {total_records} mentions for {brand_display_name} ({primary_product}). "
                f"Key customer enthusiasm driven by {praise_terms}, while friction emerged around {friction_terms}."
            )

            precautions_list = [
                f"Monitor real-time feedback thresholds for {primary_product} across social listening channels.",
                f"Address friction reported in {friction_terms} to maintain Net Sentiment above +{max(nss, 20)}%."
            ]
            if top_friction:
                precautions_list.append(f"Deploy automated response workflows for issues related to {top_friction[0]['aspect']}.")

            measures_list = [
                f"Ingested dataset '{filename}' into BrandPulse AI multi-model NLP pipeline.",
                f"Synchronized sentiment trends, emotion radar, and aspect intelligence for {primary_product} in live command dashboard.",
                f"Established real-time alert trigger at {target_brand_doc.get('crisis_threshold_negative', 0.35) * 100}% negative threshold."
            ]

            summary_doc = {
                "id": summary_id,
                "brand_id": target_brand_id,
                "name_of_company": brand_display_name,
                "product_service": primary_product,
                "date": now_dt.strftime("%Y-%m-%d"),
                "time": now_dt.strftime("%H:%M:%S"),
                "total_mentions_analyzed": total_records,
                "net_sentiment_score": nss,
                "cause_of_feedback": cause_str,
                "precautions": precautions_list,
                "measures_taken": measures_list,
                "timestamp": now_dt.isoformat(),
                "dataset_file": filename,
                "is_simulated": is_simulated
            }
            await db["summaries"].insert_one(summary_doc)
            logger.info(f"Stored Monitored Summary {summary_id} in MongoDB for {brand_display_name}")

        return {
            "status": "success",
            "message": f"Successfully parsed and ingested {total_records} records into {brand_display_name} dashboard.",
            "brand_id": target_brand_id,
            "brand_name": brand_display_name,
            "primary_product": primary_product,
            "detected_products": detected_products,
            "total_records_processed": total_records,
            "positive_count": positive_count,
            "neutral_count": neutral_count,
            "negative_count": negative_count,
            "net_sentiment_score": nss,
            "average_sentiment_score": avg_sentiment,
            "emotions_breakdown": emotions_agg,
            "top_aspect_praise": top_praise,
            "top_aspect_friction": top_friction,
            "summary_id": summary_doc["id"] if summary_doc else None,
            "sample_processed_records": clean_docs(processed_mentions[:5])
        }

    # =========================================================================
    # INTERNAL PARSING HELPERS
    # =========================================================================
    def _detect_text_column(self, columns: List[str]) -> str:
        candidates = ["review", "comment", "text", "content", "tweet", "feedback", "post", "caption", "message", "body", "review_text", "summary"]
        for cand in candidates:
            for col in columns:
                if cand in col.lower():
                    return col
        return columns[0] if columns else "text"

    def _detect_product_column(self, columns: List[str]) -> Optional[str]:
        # Exclude 'title' as review titles are full sentences, not product entities
        candidates = ["product", "product_name", "model", "item", "device", "brand_model", "dish", "dish_name", "category", "room_type", "service"]
        for cand in candidates:
            for col in columns:
                if cand == col.lower() or f"{cand}_" in col.lower() or f"_{cand}" in col.lower():
                    return col
        return None

    def _detect_rating_column(self, columns: List[str]) -> Optional[str]:
        candidates = ["rating", "stars", "star", "score", "grade"]
        for cand in candidates:
            for col in columns:
                if cand in col.lower():
                    return col
        return None

    def _parse_csv_records(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8", on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1", on_bad_lines='skip')
            except Exception:
                text = file_bytes.decode('utf-8', errors='ignore')
                reader = csv.DictReader(io.StringIO(text))
                return [{"content": row.get(self._detect_text_column(list(row.keys())), ""), "product": row.get("product")} for row in reader if row]

        columns = list(df.columns)
        text_col = self._detect_text_column(columns)
        product_col = self._detect_product_column(columns)
        rating_col = self._detect_rating_column(columns)
        
        # Author / Platform detection
        author_col = next((c for c in columns if any(k in c.lower() for k in ["author", "user", "username", "customer", "reviewer", "reviewername"])), None)
        platform_col = next((c for c in columns if any(k in c.lower() for k in ["platform", "source", "channel", "site"])), None)
        date_col = next((c for c in columns if any(k in c.lower() for k in ["date", "time", "timestamp", "created_at", "reviewdate"])), None)

        records = []
        for _, row in df.iterrows():
            content = str(row.get(text_col, "")).strip()
            if not content or content.lower() == "nan":
                continue
            
            raw_prod = str(row.get(product_col, "")).strip() if product_col and str(row.get(product_col, "")).lower() != "nan" else None
            clean_prod = raw_prod if raw_prod and len(raw_prod) <= 35 and not any(raw_prod.endswith(x) for x in ['.', '!', '?']) else None

            rating_val = None
            if rating_col and str(row.get(rating_col, "")).strip().lower() != "nan":
                try:
                    r_num = float(row.get(rating_col))
                    if 1 <= r_num <= 5:
                        rating_val = int(round(r_num))
                except (ValueError, TypeError):
                    pass

            item = {
                "content": content,
                "product": clean_prod,
                "author": str(row.get(author_col, "")).strip() if author_col and str(row.get(author_col, "")).lower() != "nan" else None,
                "platform": str(row.get(platform_col, "")).strip() if platform_col and str(row.get(platform_col, "")).lower() != "nan" else "CSV Upload",
                "timestamp": str(row.get(date_col, "")).strip() if date_col and str(row.get(date_col, "")).lower() != "nan" else None,
                "rating": rating_val
            }
            records.append(item)

        return records

    def _parse_excel_records(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            logger.error(f"Failed to read Excel records: {e}")
            raise ValueError(f"Unable to read Excel file: {e}")

        columns = [str(c) for c in df.columns]
        text_col = self._detect_text_column(columns)
        product_col = self._detect_product_column(columns)
        rating_col = self._detect_rating_column(columns)
        author_col = next((c for c in columns if any(k in c.lower() for k in ["author", "user", "username", "customer", "reviewer", "reviewername"])), None)
        platform_col = next((c for c in columns if any(k in c.lower() for k in ["platform", "source", "channel", "site"])), None)
        date_col = next((c for c in columns if any(k in c.lower() for k in ["date", "time", "timestamp", "created_at", "reviewdate"])), None)

        records = []
        for _, row in df.iterrows():
            content = str(row.get(text_col, "")).strip()
            if not content or content.lower() == "nan":
                continue

            raw_prod = str(row.get(product_col, "")).strip() if product_col and str(row.get(product_col, "")).lower() != "nan" else None
            clean_prod = raw_prod if raw_prod and len(raw_prod) <= 35 and not any(raw_prod.endswith(x) for x in ['.', '!', '?']) else None

            rating_val = None
            if rating_col and str(row.get(rating_col, "")).strip().lower() != "nan":
                try:
                    r_num = float(row.get(rating_col))
                    if 1 <= r_num <= 5:
                        rating_val = int(round(r_num))
                except (ValueError, TypeError):
                    pass

            item = {
                "content": content,
                "product": clean_prod,
                "author": str(row.get(author_col, "")).strip() if author_col and str(row.get(author_col, "")).lower() != "nan" else None,
                "platform": str(row.get(platform_col, "")).strip() if platform_col and str(row.get(platform_col, "")).lower() != "nan" else "Excel Upload",
                "timestamp": str(row.get(date_col, "")).strip() if date_col and str(row.get(date_col, "")).lower() != "nan" else None,
                "rating": rating_val
            }
            records.append(item)

        return records


    def _parse_pdf_records(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        full_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

        chunks = self._segment_pdf_text(full_text)
        records = []
        for c in chunks:
            # Check for inline product indicators e.g. "Product: iPhone 16 Pro"
            prod_match = re.search(r"(?:Product|Item|Model|Dish):\s*([^\n\.,]+)", c, re.IGNORECASE)
            product_tag = prod_match.group(1).strip() if prod_match else None
            
            records.append({
                "content": c,
                "product": product_tag,
                "platform": "PDF Report / Audit",
                "author": "Verified Customer Review"
            })
        return records

    def _segment_pdf_text(self, text: str) -> List[str]:
        """
        Segments long PDF text into distinct review items / feedback paragraphs.
        """
        # Split by numbered items e.g. "1. ", "2. ", or bullet points
        blocks = re.split(r'\n(?:\d+[\.\)]|\-|\*|•|\#)\s+', text)
        if len(blocks) > 3:
            res = []
            for idx, b in enumerate(blocks):
                cleaned = b.strip()
                if len(cleaned) <= 15:
                    continue
                # If first block is just a document header/preamble, skip it
                if idx == 0 and any(h in cleaned.lower() for h in ['report', 'dataset', 'document type', 'feedback audit', 'audit report', 'page 1', 'table of contents']):
                    continue
                res.append(cleaned)
            return res if res else [b.strip() for b in blocks if len(b.strip()) > 15]

        # Split by double newlines or paragraph blocks
        paragraphs = text.split("\n\n")
        valid_paras = [p.replace("\n", " ").strip() for p in paragraphs if len(p.strip()) > 20]
        if valid_paras:
            return valid_paras

        # Split by sentences if paragraphs are single lines
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20]
        return lines if lines else [text[:500]]

    def _parse_json_records(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        data = json.loads(file_bytes.decode("utf-8", errors="ignore"))
        if isinstance(data, dict):
            items = data.get("mentions", data.get("reviews", data.get("data", [data])))
        elif isinstance(data, list):
            items = data
        else:
            items = []

        records = []
        for obj in items:
            if isinstance(obj, dict):
                content = obj.get("content") or obj.get("text") or obj.get("review") or obj.get("message")
                if content and str(content).strip():
                    records.append({
                        "content": str(content).strip(),
                        "product": obj.get("product") or obj.get("product_name"),
                        "author": obj.get("author") or obj.get("user"),
                        "platform": obj.get("platform") or "JSON Ingestion",
                        "timestamp": obj.get("timestamp") or obj.get("date")
                    })
        return records

    def _parse_txt_records(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        lines = [l.strip() for l in raw_text.splitlines() if len(l.strip()) > 15]
        return [{"content": l, "platform": "Text Document"} for l in lines]

    def _extract_products_from_text(self, text: str) -> List[str]:
        found = []
        for pat in self.KNOWN_PRODUCT_PATTERNS:
            matches = re.findall(pat, text, re.IGNORECASE)
            for m in matches:
                clean_m = m.strip()
                if clean_m and clean_m not in found and len(clean_m) > 2 and len(clean_m) <= 35:
                    found.append(clean_m)
        return found[:6]

    def _extract_brand_from_filename_or_text(self, filename: str, text: str) -> Optional[str]:
        # 1. Inspect clean filename
        if filename:
            clean_fn = re.sub(r'[-_](?:20\d\d[-_]\d\d[-_]\d\d|\d+|reviews|dataset|data|feedback|mentions|corpus).*$', '', filename, flags=re.IGNORECASE)
            clean_fn = re.sub(r'\.(?:csv|pdf|json|txt)$', '', clean_fn, flags=re.IGNORECASE).replace('_', ' ').replace('-', ' ').strip()
            if clean_fn and len(clean_fn) > 2 and clean_fn.lower() not in ["reviews", "dataset", "feedback", "data", "mentions"]:
                # If hotel / resort
                if "hotel" not in clean_fn.lower() and any(w in text.lower() for w in ["hotel", "room", "booking", "resort"]):
                    return f"{clean_fn.title()} Hotel"
                return clean_fn.title()

        # 2. Inspect text content
        lower = text.lower()
        if "annapoorna" in lower:
            return "Sree Annapoorna"
        elif "apple" in lower or "iphone" in lower or "macbook" in lower or "ios" in lower:
            return "Apple"
        elif "samsung" in lower or "galaxy" in lower:
            return "Samsung"
        elif "google" in lower or "pixel" in lower:
            return "Google Pixel"
        elif "technova" in lower:
            return "TechNova AI"
        return None

    def _extract_brand_from_text(self, text: str) -> Optional[str]:
        return self._extract_brand_from_filename_or_text("", text)

dataset_ingestor = DatasetIngestor()
