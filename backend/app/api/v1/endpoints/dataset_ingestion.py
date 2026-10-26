import os
import io
import json
import re
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from starlette.concurrency import run_in_threadpool
from app.api.v1.endpoints.auth import get_current_user
from app.services.dataset_ingestor import dataset_ingestor
from app.core.database import get_db, clean_doc
from app.api.v1.endpoints.brands import get_brand_for_user, get_user_brand_ids
from app.services.ai_engine import ai_engine
from app.schemas.all_schemas import PasteReviewsRequest

router = APIRouter()

@router.post("/preview")
async def preview_dataset_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns an instant schema and content preview of an uploaded CSV, PDF, JSON, or TXT file.
    """
    try:
        content = await file.read()
        preview_data = dataset_ingestor.preview_file(content, file.filename)
        return {
            "filename": file.filename,
            "size_bytes": len(content),
            **preview_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File preview failed: {str(e)}")

@router.post("/upload")
async def upload_and_ingest_dataset(
    file: UploadFile = File(...),
    brand_id: Optional[str] = Form(None),
    brand_name: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    industry: Optional[str] = Form(None),
    mode: str = Form("append"), # "append" or "replace"
    generate_summary: bool = Form(True),
    current_user: dict = Depends(get_current_user)
):
    """
    Uploads a dataset file (CSV or PDF), parses records, runs full AI inference (Sentiment, Emotion, Intent, ABSA),
    updates brand products and keywords in MongoDB, and updates all metrics across the Dashboard.
    """
    if brand_id:
        await get_brand_for_user(brand_id, current_user)

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = await dataset_ingestor.process_and_ingest(
            file_bytes=content,
            filename=file.filename,
            brand_id=brand_id,
            brand_name=brand_name,
            product_name=product_name,
            industry=industry,
            mode=mode,
            generate_summary=generate_summary,
            current_user=current_user
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dataset processing failed: {str(e)}")

@router.get("/samples")
async def get_sample_datasets(current_user: dict = Depends(get_current_user)):
    """
    Returns pre-packaged sample datasets available for instant one-click testing.
    All pre-loaded sample datasets have been removed.
    """
    return []

@router.post("/ingest-sample/{sample_id}")
async def ingest_sample_dataset(
    sample_id: str,
    brand_id: Optional[str] = None,
    mode: str = "append",
    current_user: dict = Depends(get_current_user)
):
    """
    Ingests a pre-packaged sample dataset directly into MongoDB.
    All pre-loaded sample datasets have been removed.
    """
    raise HTTPException(status_code=404, detail=f"Sample dataset '{sample_id}' has been removed.")

@router.post("/paste-reviews")
async def paste_and_ingest_reviews(
    body: PasteReviewsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ingests pasted customer review text or screenshot OCR text directly.
    Splits text by double newlines or numbered lines (1., 2., etc.), runs NLP,
    and inserts into db.mentions with source='pasted' (or specified source).
    """
    brand_id = body.business_id or body.brand_id
    if not brand_id:
        user_brand_ids = await get_user_brand_ids(current_user)
        if user_brand_ids:
            brand_id = user_brand_ids[0]
        else:
            raise HTTPException(status_code=400, detail="brand_id or business_id is required")

    brand = await get_brand_for_user(brand_id, current_user)
    raw_text = body.text.strip()
    if not raw_text:
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    # Split lines / blocks
    lines = [line.strip() for line in re.split(r'\n{2,}|\r\n{2,}|\n(?=\d+[\.\)])', raw_text) if line.strip()]
    if len(lines) == 1 and len(raw_text.split('\n')) > 1:
        lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 8]

    if not lines:
        lines = [raw_text]

    db = get_db()
    ingested_mentions = []
    now_dt = datetime.datetime.now(datetime.timezone.utc)

    for idx, rev_text in enumerate(lines[:100]):
        clean_rev = re.sub(r'^\d+[\.\)]\s*', '', rev_text).strip()
        if not clean_rev:
            continue

        lang = await run_in_threadpool(ai_engine.detect_language, clean_rev)
        translated_text = await run_in_threadpool(ai_engine.translate_to_english, clean_rev, lang) if lang != "en" else None
        sentiment_res = await run_in_threadpool(ai_engine.analyze_sentiment, clean_rev, lang)
        sentiment, sentiment_score = sentiment_res[0], sentiment_res[1]
        emotions, dominant_emotion = await run_in_threadpool(ai_engine.detect_emotions, clean_rev)
        intent, intent_confidence = await run_in_threadpool(ai_engine.classify_intent, clean_rev)
        preset_key = brand.get("preset_key") or brand.get("industry")
        topics = await run_in_threadpool(ai_engine.tag_preset_topics, clean_rev, preset_key)
        if not topics:
            topics = brand.get("topics", [])[:2]

        m_id = f"men_pasted_{uuid.uuid4().hex[:10]}"
        m_time = (now_dt - datetime.timedelta(hours=idx * 2)).isoformat()
        doc = {
            "id": m_id,
            "brand_id": brand_id,
            "business_id": brand_id,
            "brand_name": brand["name"],
            "source": body.source or "manual",
            "platform": body.source or "manual",
            "author": f"Customer {idx + 1}",
            "author_handle": f"@customer_{idx + 1}",
            "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed=pasted_{idx}",
            "author_followers": 150,
            "content": clean_rev,
            "original_text": clean_rev,
            "language": lang,
            "translated_text": translated_text,
            "rating": 5 if sentiment == "positive" else (1 if sentiment == "negative" else 3),
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "sentiment_confidence": getattr(sentiment_res, "confidence", 0.9),
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "topics": topics,
            "reach": 150,
            "engagement_score": 10,
            "virality_score": 35.0,
            "is_crisis_flag": False,
            "is_simulated": False,
            "replied": False,
            "reply_text": None,
            "reply_timestamp": None,
            "timestamp": m_time,
            "created_at": m_time,
            "url": "https://brandpulse.ai"
        }
        await db["mentions"].insert_one(doc)
        ingested_mentions.append(clean_doc(doc))

    return {
        "status": "success",
        "message": f"Successfully ingested {len(ingested_mentions)} pasted reviews.",
        "brand_id": brand_id,
        "count": len(ingested_mentions),
        "total_reviews_parsed": len(ingested_mentions),
        "reviews": ingested_mentions[:5]
    }

