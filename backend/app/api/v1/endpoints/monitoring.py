import json
import uuid
import re
import asyncio
import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.core.database import get_db, clean_doc, clean_docs
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user, get_user_brand_ids
from app.schemas.all_schemas import (
    MentionResponse, 
    MentionCreate, 
    ReviewReplyRequest,
    MentionFeedbackRequest,
    SummaryCreate, 
    SummaryUpdate, 
    SummaryResponse
)
from app.services.ai_engine import ai_engine
from app.services.crisis_detector import crisis_detector
from app.services.scraper_simulator import scraper_simulator
from app.core.security import decode_access_token

logger = logging.getLogger("brandpulse.monitoring")

router = APIRouter()

@router.get("/mentions", response_model=List[MentionResponse])
async def list_mentions(
    brand_id: Optional[str] = None,
    platform: Optional[str] = None,
    source: Optional[str] = None,
    rating: Optional[int] = None,
    mood: Optional[str] = None,
    replied: Optional[bool] = None,
    language: Optional[str] = None,
    topic: Optional[str] = None,
    sentiment: Optional[str] = None,
    emotion: Optional[str] = None,
    intent: Optional[str] = None,
    search: Optional[str] = None,
    is_crisis_flag: Optional[bool] = None,
    is_simulated: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    query = {}
    
    if brand_id:
        await get_brand_for_user(brand_id, current_user)
        query["brand_id"] = brand_id
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        query["brand_id"] = {"$in": user_brand_ids}

    # Source / Platform filter
    active_source = source or platform
    if active_source and active_source != "all":
        query["$or"] = [
            {"source": active_source},
            {"platform": active_source}
        ]

    # Rating filter (1-5 stars)
    if rating is not None and rating > 0:
        query["rating"] = rating

    # Mood filter (Happy -> positive, Unhappy -> negative, Neutral -> neutral)
    active_sentiment = sentiment
    if mood and mood != "all":
        m_lower = mood.lower()
        if "happy" in m_lower or m_lower == "positive":
            active_sentiment = "positive"
        elif "unhappy" in m_lower or m_lower == "negative":
            active_sentiment = "negative"
        else:
            active_sentiment = "neutral"

    if active_sentiment and active_sentiment != "all":
        query["sentiment"] = active_sentiment

    # Replied status filter
    if replied is not None:
        if replied:
            query["replied"] = True
        else:
            query["replied"] = {"$ne": True}

    # Language filter
    if language and language != "all":
        query["language"] = language

    # Topic filter
    if topic and topic != "all":
        query["topics"] = topic

    if emotion and emotion != "all":
        query["dominant_emotion"] = emotion
    if intent and intent != "all":
        query["intent"] = intent
    if is_crisis_flag is not None:
        query["is_crisis_flag"] = is_crisis_flag
    if is_simulated is not None:
        query["is_simulated"] = is_simulated
        
    if search:
        clean_search = re.escape(search.strip()[:100])
        search_or = [
            {"content": {"$regex": clean_search, "$options": "i"}},
            {"original_text": {"$regex": clean_search, "$options": "i"}},
            {"author": {"$regex": clean_search, "$options": "i"}},
            {"author_handle": {"$regex": clean_search, "$options": "i"}}
        ]
        if "$or" in query:
            query["$and"] = [{"$or": query.pop("$or")}, {"$or": search_or}]
        else:
            query["$or"] = search_or

    cursor = db["mentions"].find(query).sort("timestamp", -1).skip(skip).limit(limit)
    mentions = await cursor.to_list(limit)
    result = []
    for m in mentions:
        d = clean_doc(m)
        d["source"] = d.get("source") or d.get("platform") or "google"
        d["platform"] = d["source"]
        d["business_id"] = d.get("business_id") or d.get("brand_id")
        d["original_text"] = d.get("original_text") or d.get("content") or ""
        d["content"] = d["original_text"]
        d["created_at"] = d.get("created_at") or d.get("timestamp")
        d["timestamp"] = d["created_at"]
        d["topics"] = d.get("topics") or []
        d["replied"] = bool(d.get("replied", False))
        d["reply_text"] = d.get("reply_text")
        d["reply_timestamp"] = d.get("reply_timestamp")
        result.append(MentionResponse(**d))
    return result

@router.post("/mentions", response_model=MentionResponse)
async def create_mention(
    mention_in: MentionCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Ingest a new mention for a user-owned business, run NLP analysis, and trigger crisis detection if needed.
    """
    target_brand_id = mention_in.business_id or mention_in.brand_id
    if not target_brand_id:
        raise HTTPException(status_code=400, detail="business_id or brand_id is required")

    brand = await get_brand_for_user(target_brand_id, current_user)
    brand_name = brand["name"]
    db = get_db()

    from app.services.plan_limits import check_can_add_reviews
    await check_can_add_reviews(target_brand_id, 1, db, current_user)

    raw_text = mention_in.original_text or mention_in.content or ""
    src = mention_in.source or mention_in.platform or "google"
    created_time = mention_in.created_at or mention_in.timestamp or datetime.datetime.now(datetime.timezone.utc)

    # AI Pipeline via run_in_threadpool
    lang = mention_in.language or await run_in_threadpool(ai_engine.detect_language, raw_text)
    translated_text = mention_in.translated_text
    if not translated_text and lang != "en":
        translated_text = await run_in_threadpool(ai_engine.translate_to_english, raw_text, lang)

    sentiment_res = await run_in_threadpool(ai_engine.analyze_sentiment, raw_text, lang)
    sentiment, sentiment_score = sentiment_res[0], sentiment_res[1]
    sentiment_confidence = sentiment_res.confidence
    emotions, dominant_emotion = await run_in_threadpool(ai_engine.detect_emotions, raw_text, sentiment_score)
    intent, intent_confidence = await run_in_threadpool(ai_engine.classify_intent, raw_text)
    
    preset_key = brand.get("preset_key") or brand.get("industry")
    topics = mention_in.topics
    if not topics:
        topics = await run_in_threadpool(ai_engine.tag_preset_topics, raw_text, preset_key) or brand.get("topics", [])[:2]

    reach = mention_in.author_followers
    engagement = int(reach * 0.03)
    virality_score = ai_engine.calculate_virality_score(reach, engagement, sentiment_score)
    is_crisis_flag = (sentiment == "negative" and (virality_score > 70.0 or dominant_emotion in ["anger", "fear"]))

    mention_id = f"men_{uuid.uuid4().hex[:10]}"
    mention_doc = {
        "id": mention_id,
        "brand_id": target_brand_id,
        "business_id": target_brand_id,
        "location_id": mention_in.location_id,
        "brand_name": brand_name,
        "source": src,
        "platform": src,
        "author": mention_in.author,
        "author_handle": mention_in.author_handle or "@customer",
        "author_followers": mention_in.author_followers,
        "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={mention_in.author_handle or 'user'}",
        "content": raw_text,
        "original_text": raw_text,
        "translated_text": translated_text,
        "rating": mention_in.rating,
        "topics": topics,
        "language": lang,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "sentiment_confidence": sentiment_confidence,
        "emotions": emotions,
        "dominant_emotion": dominant_emotion,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "reach": reach,
        "engagement_score": engagement,
        "virality_score": virality_score,
        "topic_cluster": "Custom User Ingestion",
        "is_crisis_flag": is_crisis_flag,
        "is_simulated": mention_in.is_simulated or False,
        "replied": mention_in.replied or False,
        "reply_text": mention_in.reply_text,
        "reply_timestamp": mention_in.reply_timestamp,
        "timestamp": created_time,
        "created_at": created_time,
        "url": mention_in.url or "https://brandpulse.ai"
    }

    await db["mentions"].insert_one(mention_doc)

    # Check Crisis Anomaly Trigger
    recent_mentions = await db["mentions"].find({"brand_id": target_brand_id}).sort("timestamp", -1).limit(30).to_list(30)
    risk_score, severity, alert_payload = crisis_detector.calculate_crisis_risk(recent_mentions)
    if alert_payload and severity in ["medium", "critical"]:
        alert_payload["brand_id"] = target_brand_id
        alert_payload["brand_name"] = brand_name
        alert_payload["is_simulated"] = False
        existing_alert = await db["alerts"].find_one({"brand_id": target_brand_id, "status": "active"})
        if not existing_alert:
            await db["alerts"].insert_one(alert_payload)

    # Trigger notification alert if bad review (1 or 2 stars)
    if mention_doc.get("rating") and mention_doc.get("rating") <= 2:
        try:
            from app.services.notifications import notification_dispatcher
            await run_in_threadpool(notification_dispatcher.dispatch_bad_review_alert, brand, mention_doc)
        except Exception as e:
            logger.warning(f"Could not dispatch bad review notification: {e}")

    ret = clean_doc(mention_doc)
    ret["source"] = ret.get("source") or ret.get("platform") or "google"
    ret["platform"] = ret["source"]
    ret["business_id"] = ret.get("business_id") or ret.get("brand_id")
    ret["original_text"] = ret.get("original_text") or ret.get("content") or ""
    ret["content"] = ret["original_text"]
    ret["created_at"] = ret.get("created_at") or ret.get("timestamp")
    ret["timestamp"] = ret["created_at"]
    ret["topics"] = ret.get("topics") or []
    ret["replied"] = bool(ret.get("replied", False))
    return MentionResponse(**ret)

@router.post("/mentions/{mention_id}/reply", response_model=MentionResponse)
@router.patch("/mentions/{mention_id}/reply", response_model=MentionResponse)
async def reply_to_mention(
    mention_id: str,
    reply_in: ReviewReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Records owner response to a customer review/mention.
    """
    db = get_db()
    mention = await db["mentions"].find_one({"id": mention_id})
    if not mention:
        raise HTTPException(status_code=404, detail="Review not found")

    await get_brand_for_user(mention["brand_id"], current_user)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await db["mentions"].update_one(
        {"id": mention_id},
        {"$set": {
            "replied": True,
            "reply_text": reply_in.reply_text,
            "reply_timestamp": now_iso
        }}
    )

    updated = await db["mentions"].find_one({"id": mention_id})
    d = clean_doc(updated)
    d["source"] = d.get("source") or d.get("platform") or "google"
    d["platform"] = d["source"]
    d["business_id"] = d.get("business_id") or d.get("brand_id")
    d["original_text"] = d.get("original_text") or d.get("content") or ""
    d["content"] = d["original_text"]
    d["created_at"] = d.get("created_at") or d.get("timestamp")
    d["timestamp"] = d["created_at"]
    d["topics"] = d.get("topics") or []
    d["replied"] = True
    d["reply_text"] = reply_in.reply_text
    d["reply_timestamp"] = now_iso
    return MentionResponse(**d)

@router.post("/mentions/{mention_id}/feedback", response_model=MentionResponse)
async def submit_mention_feedback(
    mention_id: str,
    feedback_in: MentionFeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submits user feedback to correct AI-predicted sentiment or topics for continuous learning.
    """
    db = get_db()
    mention = await db["mentions"].find_one({"id": mention_id})
    if not mention:
        raise HTTPException(status_code=404, detail="Mention not found")

    await get_brand_for_user(mention["brand_id"], current_user)
    
    update_fields = {"has_feedback": True}
    if feedback_in.corrected_sentiment:
        update_fields["sentiment"] = feedback_in.corrected_sentiment
        if feedback_in.corrected_sentiment == "positive":
            update_fields["sentiment_score"] = max(0.5, float(mention.get("sentiment_score", 0.5)))
        elif feedback_in.corrected_sentiment == "negative":
            update_fields["sentiment_score"] = min(-0.5, float(mention.get("sentiment_score", -0.5)))
        else:
            update_fields["sentiment_score"] = 0.0

    if feedback_in.corrected_topics is not None:
        update_fields["topics"] = feedback_in.corrected_topics

    await db["mentions"].update_one({"id": mention_id}, {"$set": update_fields})
    
    # Store feedback event for active model retraining
    feedback_log = {
        "id": f"fb_{uuid.uuid4().hex[:10]}",
        "mention_id": mention_id,
        "brand_id": mention["brand_id"],
        "user_id": current_user["id"],
        "original_sentiment": mention.get("sentiment"),
        "corrected_sentiment": feedback_in.corrected_sentiment,
        "original_topics": mention.get("topics", []),
        "corrected_topics": feedback_in.corrected_topics,
        "notes": feedback_in.notes,
        "text": mention.get("original_text") or mention.get("content") or "",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    await db["model_feedback"].insert_one(feedback_log)
    
    updated = await db["mentions"].find_one({"id": mention_id})
    ret = clean_doc(updated)
    ret["source"] = ret.get("source") or ret.get("platform") or "google"
    ret["platform"] = ret["source"]
    ret["business_id"] = ret.get("business_id") or ret.get("brand_id")
    ret["original_text"] = ret.get("original_text") or ret.get("content") or ""
    ret["content"] = ret["original_text"]
    ret["created_at"] = ret.get("created_at") or ret.get("timestamp")
    ret["timestamp"] = ret["created_at"]
    ret["topics"] = ret.get("topics") or []
    ret["replied"] = bool(ret.get("replied", False))
    return MentionResponse(**ret)

@router.post("/simulate")
async def simulate_incoming_mention(
    brand_id: str,
    scenario: str = "normal",
    current_user: dict = Depends(get_current_user)
):
    """
    Simulates a realistic incoming mention for the chosen scenario on a user-owned brand.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()

    mention_doc = scraper_simulator.generate_mention(
        brand_name=brand["name"],
        brand_id=brand_id,
        scenario=scenario,
        competitors=brand.get("competitors", ["ApexCloud"])
    )
    mention_doc["is_simulated"] = True

    await db["mentions"].insert_one(mention_doc)

    # Crisis trigger check
    recent_mentions = await db["mentions"].find({"brand_id": brand_id}).sort("timestamp", -1).limit(30).to_list(30)
    risk_score, severity, alert_payload = crisis_detector.calculate_crisis_risk(recent_mentions)
    
    alert_created = None
    if alert_payload and severity in ["medium", "critical"]:
        alert_payload["brand_id"] = brand_id
        alert_payload["brand_name"] = brand["name"]
        alert_payload["is_simulated"] = True
        existing_alert = await db["alerts"].find_one({"brand_id": brand_id, "status": "active"})
        if not existing_alert:
            await db["alerts"].insert_one(alert_payload)
            alert_created = alert_payload

    return {
        "mention": MentionResponse(**clean_doc(mention_doc)),
        "crisis_risk_score": risk_score,
        "crisis_severity": severity,
        "alert_triggered": alert_created is not None
    }

@router.post("/test-nlp")
async def test_nlp_endpoint(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Interactive test studio (requires authentication).
    """
    lang = await run_in_threadpool(ai_engine.detect_language, text)
    sentiment_res = await run_in_threadpool(ai_engine.analyze_sentiment, text, lang)
    sentiment, sentiment_score = sentiment_res[0], sentiment_res[1]
    emotions, dominant_emotion = await run_in_threadpool(ai_engine.detect_emotions, text, sentiment_score)
    intent, intent_confidence = await run_in_threadpool(ai_engine.classify_intent, text)

    return {
        "text": text,
        "language": lang,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "sentiment_confidence": sentiment_res.confidence,
        "emotions": emotions,
        "dominant_emotion": dominant_emotion,
        "intent": intent,
        "intent_confidence": intent_confidence
    }

@router.get("/stream")
async def stream_live_feed(
    request: Request,
    brand_id: Optional[str] = None,
    token: Optional[str] = None,
    limit: Optional[int] = Query(None)
):
    """
    Server-Sent Events (SSE) stream pushing new live mentions to authenticated clients.
    Accepts Bearer token in Authorization header or as a ?token= query parameter.
    """
    # 1. Authenticate user from header or query param
    auth_header = request.headers.get("authorization", "")
    bearer_token = token
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header.split(" ", 1)[1]
    
    if not bearer_token:
        raise HTTPException(status_code=401, detail="Authentication token required for live stream")
    
    payload = decode_access_token(bearer_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired stream authentication token")
    
    db = get_db()
    current_user = await db["users"].find_one({"id": payload.get("sub")})
    if not current_user or not current_user.get("is_active", False):
        raise HTTPException(status_code=401, detail="User not found or account deactivated")

    # 2. Scope target brand
    if brand_id:
        target_brand = await get_brand_for_user(brand_id, current_user)
        target_brand_id = target_brand["id"]
        brand_name = target_brand["name"]
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        if not user_brand_ids:
            raise HTTPException(status_code=404, detail="No brands found for user")
        target_brand_id = user_brand_ids[0]
        b = await db["brands"].find_one({"id": target_brand_id})
        brand_name = b["name"] if b else "Brand"

    async def event_generator():
        last_check = datetime.datetime.now(datetime.timezone.utc)
        count = 0
        while True:
            if await request.is_disconnected():
                break

            if settings.DEMO_MODE:
                # In DEMO_MODE, push simulated stream events to UI without writing to DB!
                mention = scraper_simulator.generate_mention(brand_name=brand_name, brand_id=target_brand_id, scenario="normal")
                mention["is_simulated"] = True
                cleaned = clean_doc(mention)
                data_json = json.dumps(cleaned, default=str)
                yield f"data: {data_json}\n\n"
            else:
                # When DEMO_MODE is false: do not insert fake data! Check for newly inserted real mentions
                now_check = datetime.datetime.now(datetime.timezone.utc)
                new_mentions = await db["mentions"].find({
                    "brand_id": target_brand_id,
                    "timestamp": {"$gte": last_check}
                }).sort("timestamp", 1).to_list(10)
                last_check = now_check
                if new_mentions:
                    for m in new_mentions:
                        cleaned = clean_doc(m)
                        data_json = json.dumps(cleaned, default=str)
                        yield f"data: {data_json}\n\n"
                else:
                    # Keep-alive heartbeat comment so SSE stream remains healthy
                    yield ": keep-alive\n\n"

            count += 1
            if limit is not None and count >= limit:
                break

            try:
                await asyncio.sleep(0.1 if limit is not None else 5)
            except asyncio.CancelledError:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ============================================================================
# MONITORED DATA SUMMARIES ENDPOINTS (Persisted into MongoDB 'summaries')
# ============================================================================

@router.post("/summaries/generate", response_model=SummaryResponse)
async def generate_and_save_monitored_summary(
    brand_id: str = Query(..., description="Brand ID to summarize"),
    current_user: dict = Depends(get_current_user)
):
    """
    Synthesizes an AI Summary for a user-owned brand.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()

    mentions = await db["mentions"].find({"brand_id": brand_id}).sort("timestamp", -1).to_list(300)
    alerts = await db["alerts"].find({"brand_id": brand_id}).to_list(20)

    summary_dict = ai_engine.synthesize_monitored_summary(
        brand_doc=brand,
        mentions=mentions,
        alerts=alerts
    )

    summary_id = f"sum_{uuid.uuid4().hex[:10]}"
    summary_doc = {
        "id": summary_id,
        "brand_id": brand_id,
        "name_of_company": summary_dict["name_of_company"],
        "product_service": summary_dict["product_service"],
        "company_details": summary_dict["company_details"],
        "date": summary_dict["date"],
        "time": summary_dict["time"],
        "timestamp": summary_dict["timestamp"],
        "cause_of_feedback": summary_dict["cause_of_feedback"],
        "precautions": summary_dict["precautions"],
        "measures_taken": summary_dict["measures_taken"],
        "total_mentions_analyzed": summary_dict["total_mentions_analyzed"],
        "net_sentiment_score": summary_dict["net_sentiment_score"],
        "sentiment_breakdown": summary_dict["sentiment_breakdown"],
        "dominant_emotions": summary_dict["dominant_emotions"],
        "status": "generated",
        "is_simulated": any(m.get("is_simulated", False) for m in mentions) if mentions else False,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "created_by": current_user.get("full_name", "AI_Automated_Monitor")
    }

    await db["summaries"].insert_one(summary_doc)
    return clean_doc(summary_doc)

@router.get("/summaries", response_model=List[SummaryResponse])
async def list_monitored_summaries(
    brand_id: Optional[str] = Query(None, description="Optional brand filter"),
    is_simulated: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    query = {}
    if brand_id:
        await get_brand_for_user(brand_id, current_user)
        query["brand_id"] = brand_id
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        query["brand_id"] = {"$in": user_brand_ids}

    if is_simulated is not None:
        query["is_simulated"] = is_simulated

    cursor = db["summaries"].find(query).sort("created_at", -1).limit(limit)
    summaries = await cursor.to_list(limit)
    return clean_docs(summaries)

@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
async def get_monitored_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    summary = await db["summaries"].find_one({"id": summary_id})
    if not summary:
        raise HTTPException(status_code=404, detail="Summary document not found")

    # Verify that the summary's brand belongs to the user
    await get_brand_for_user(summary.get("brand_id", ""), current_user)
    return clean_doc(summary)

@router.patch("/summaries/{summary_id}", response_model=SummaryResponse)
async def update_monitored_summary(
    summary_id: str,
    payload: SummaryUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    summary = await db["summaries"].find_one({"id": summary_id})
    if not summary:
        raise HTTPException(status_code=404, detail="Summary document not found")

    # Verify that the summary's brand belongs to the user
    await get_brand_for_user(summary.get("brand_id", ""), current_user)

    update_fields = {}
    if payload.measures_taken is not None:
        update_fields["measures_taken"] = payload.measures_taken
    if payload.precautions is not None:
        update_fields["precautions"] = payload.precautions
    if payload.status is not None:
        update_fields["status"] = payload.status
    if payload.cause_of_feedback is not None:
        update_fields["cause_of_feedback"] = payload.cause_of_feedback

    if update_fields:
        await db["summaries"].update_one({"id": summary_id}, {"$set": update_fields})
        summary = await db["summaries"].find_one({"id": summary_id})

    return clean_doc(summary)

@router.delete("/summaries/{summary_id}")
async def delete_monitored_summary(
    summary_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    summary = await db["summaries"].find_one({"id": summary_id})
    if not summary:
        raise HTTPException(status_code=404, detail="Summary document not found")

    # Verify that the summary's brand belongs to the user
    await get_brand_for_user(summary.get("brand_id", ""), current_user)

    await db["summaries"].delete_one({"id": summary_id})
    return {"success": True, "message": "Summary deleted from MongoDB", "id": summary_id}
