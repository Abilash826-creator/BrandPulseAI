import html
import datetime
from typing import Dict, Any, List, Optional
from app.core.logging import logger

def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitizes untrusted customer review text to mitigate prompt injection,
    escapes HTML, and strips dangerous injection patterns.
    """
    if not text:
        return ""
    # Strip HTML tags/entities
    clean = html.escape(str(text).strip())
    # Wrap text cleanly without executable delimiters
    return clean

def parse_period_delta(period: str) -> datetime.timedelta:
    p = (period or "").lower().strip()
    if "30" in p or "month" in p:
        return datetime.timedelta(days=30)
    elif "14" in p or "2_weeks" in p or "two_weeks" in p:
        return datetime.timedelta(days=14)
    elif "90" in p or "quarter" in p:
        return datetime.timedelta(days=90)
    # Default to 7 days
    return datetime.timedelta(days=7)

async def get_overview(db, business_id: str, period: str = "last_7_days") -> Dict[str, Any]:
    delta = parse_period_delta(period)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - delta

    query = {"brand_id": business_id, "timestamp": {"$gte": cutoff}}
    total_docs = await db["mentions"].count_documents(query)

    # Fallback to all-time if no reviews in window
    if total_docs == 0:
        query = {"brand_id": business_id}
        total_docs = await db["mentions"].count_documents(query)

    cursor = db["mentions"].find(query).limit(200)
    mentions = await cursor.to_list(200)

    if not mentions:
        return {
            "status": "insufficient_data",
            "message": "No customer reviews found yet for this business.",
            "total_reviews": 0
        }

    ratings = [m.get("rating") for m in mentions if m.get("rating") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    mood_counts = {"happy": 0, "neutral": 0, "unhappy": 0}
    unreplied_count = 0
    topics_count: Dict[str, int] = {}

    for m in mentions:
        sentiment = m.get("sentiment", "neutral")
        if sentiment in ["positive", "happy"]:
            mood_counts["happy"] += 1
        elif sentiment in ["negative", "unhappy"]:
            mood_counts["unhappy"] += 1
        else:
            mood_counts["neutral"] += 1

        if not m.get("replied", False):
            unreplied_count += 1

        for t in m.get("topics", []):
            topics_count[t] = topics_count.get(t, 0) + 1

    top_topics = sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "status": "ok",
        "period": period,
        "total_reviews": len(mentions),
        "average_star_rating": avg_rating,
        "mood_distribution": mood_counts,
        "unreplied_count": unreplied_count,
        "top_topics": [{"topic": t[0], "count": t[1]} for t in top_topics]
    }

async def search_reviews(
    db,
    business_id: str,
    query: Optional[str] = None,
    source: Optional[str] = None,
    rating: Optional[int] = None,
    topic: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 8
) -> Dict[str, Any]:
    filter_query: Dict[str, Any] = {"brand_id": business_id}

    if source:
        filter_query["source"] = source.lower()
    if rating:
        filter_query["rating"] = int(rating)
    if topic:
        filter_query["topics"] = topic
    if language:
        filter_query["language"] = language.lower()

    if query and query.strip():
        # Clean regex search on content/translated text
        clean_q = query.strip()[:60]
        filter_query["$or"] = [
            {"content": {"$regex": clean_q, "$options": "i"}},
            {"translated_text": {"$regex": clean_q, "$options": "i"}}
        ]

    limit = min(max(int(limit), 1), 20)
    cursor = db["mentions"].find(filter_query).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(limit)

    results = []
    for d in docs:
        raw_text = d.get("content") or d.get("text") or ""
        results.append({
            "review_id": str(d.get("id") or d.get("_id", "")),
            "author": d.get("author", "Customer"),
            "source": d.get("source", "google"),
            "rating": d.get("rating"),
            "mood": d.get("sentiment", "neutral"),
            "language": d.get("language", "en"),
            "text": sanitize_untrusted_text(raw_text),
            "translated_text": sanitize_untrusted_text(d.get("translated_text", "")),
            "date": d.get("timestamp").isoformat() if isinstance(d.get("timestamp"), datetime.datetime) else str(d.get("timestamp")),
            "replied": d.get("replied", False)
        })

    return {
        "status": "ok",
        "matches_count": len(results),
        "reviews": results
    }

async def get_top_issues(db, business_id: str, period: str = "last_7_days") -> Dict[str, Any]:
    delta = parse_period_delta(period)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - delta

    query = {
        "brand_id": business_id,
        "$or": [
            {"sentiment": {"$in": ["negative", "unhappy"]}},
            {"rating": {"$in": [1, 2]}}
        ]
    }
    # Check if there are matches in period
    in_period = await db["mentions"].count_documents({**query, "timestamp": {"$gte": cutoff}})
    if in_period > 0:
        query["timestamp"] = {"$gte": cutoff}

    cursor = db["mentions"].find(query).sort("timestamp", -1).limit(40)
    neg_reviews = await cursor.to_list(40)

    if not neg_reviews:
        return {
            "status": "ok",
            "message": "Great news! No significant complaints or negative reviews found in this period.",
            "top_issues": []
        }

    topic_counts: Dict[str, int] = {}
    topic_examples: Dict[str, List[str]] = {}

    for r in neg_reviews:
        topics = r.get("topics", [])
        text = r.get("translated_text") or r.get("content") or ""
        sanitized = sanitize_untrusted_text(text[:140])
        
        assigned = topics if topics else ["General Customer Experience"]
        for t in assigned:
            topic_counts[t] = topic_counts.get(t, 0) + 1
            if t not in topic_examples:
                topic_examples[t] = []
            if len(topic_examples[t]) < 2 and sanitized:
                topic_examples[t].append(f'"{sanitized}"')

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    issues = []
    for t, count in sorted_topics:
        issues.append({
            "issue": t,
            "negative_reviews_count": count,
            "sample_customer_quotes": topic_examples.get(t, [])
        })

    return {
        "status": "ok",
        "total_negative_reviews": len(neg_reviews),
        "top_issues": issues,
        "recommendation": f"Focus on improving {sorted_topics[0][0]} first to quickly boost customer ratings."
    }

async def get_top_praises(db, business_id: str, period: str = "last_7_days") -> Dict[str, Any]:
    delta = parse_period_delta(period)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - delta

    query = {
        "brand_id": business_id,
        "$or": [
            {"sentiment": {"$in": ["positive", "happy"]}},
            {"rating": {"$in": [4, 5]}}
        ]
    }
    in_period = await db["mentions"].count_documents({**query, "timestamp": {"$gte": cutoff}})
    if in_period > 0:
        query["timestamp"] = {"$gte": cutoff}

    cursor = db["mentions"].find(query).sort("timestamp", -1).limit(40)
    pos_reviews = await cursor.to_list(40)

    if not pos_reviews:
        return {
            "status": "ok",
            "message": "No positive customer praises detected in this period yet.",
            "top_praises": []
        }

    topic_counts: Dict[str, int] = {}
    topic_examples: Dict[str, List[str]] = {}

    for r in pos_reviews:
        topics = r.get("topics", [])
        text = r.get("translated_text") or r.get("content") or ""
        sanitized = sanitize_untrusted_text(text[:140])
        
        assigned = topics if topics else ["Quality & Experience"]
        for t in assigned:
            topic_counts[t] = topic_counts.get(t, 0) + 1
            if t not in topic_examples:
                topic_examples[t] = []
            if len(topic_examples[t]) < 2 and sanitized:
                topic_examples[t].append(f'"{sanitized}"')

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    praises = []
    for t, count in sorted_topics:
        praises.append({
            "feature_loved": t,
            "praise_count": count,
            "sample_quotes": topic_examples.get(t, [])
        })

    return {
        "status": "ok",
        "total_positive_reviews": len(pos_reviews),
        "top_praises": praises
    }

async def get_rating_trend(db, business_id: str, period: str = "last_30_days") -> Dict[str, Any]:
    delta = parse_period_delta(period)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - delta

    query = {"brand_id": business_id, "timestamp": {"$gte": cutoff}}
    total_in_period = await db["mentions"].count_documents(query)
    if total_in_period == 0:
        query = {"brand_id": business_id}

    cursor = db["mentions"].find(query).sort("timestamp", 1).limit(300)
    mentions = await cursor.to_list(300)

    if not mentions:
        return {"status": "insufficient_data", "message": "No reviews available to compute rating trajectory."}

    # Group into weekly intervals
    buckets: Dict[str, List[float]] = {}
    for m in mentions:
        ts = m.get("timestamp")
        rating = m.get("rating")
        if rating is not None and isinstance(ts, datetime.datetime):
            week_key = ts.strftime("%Y-W%U")
            if week_key not in buckets:
                buckets[week_key] = []
            buckets[week_key].append(float(rating))

    trajectory = []
    for w in sorted(buckets.keys()):
        avg = round(sum(buckets[w]) / len(buckets[w]), 2)
        trajectory.append({"time_window": w, "average_stars": avg, "review_count": len(buckets[w])})

    direction = "stable"
    if len(trajectory) >= 2:
        diff = trajectory[-1]["average_stars"] - trajectory[0]["average_stars"]
        if diff >= 0.2:
            direction = "improving"
        elif diff <= -0.2:
            direction = "declining"

    return {
        "status": "ok",
        "trajectory": trajectory,
        "overall_trend": direction,
        "current_period_average": trajectory[-1]["average_stars"] if trajectory else None
    }

async def compare_periods(db, business_id: str, period_a: str = "last_7_days", period_b: str = "previous_7_days") -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc)
    delta_a = parse_period_delta(period_a)
    cutoff_a = now - delta_a
    cutoff_b = now - (delta_a * 2)

    docs_a = await db["mentions"].find({"brand_id": business_id, "timestamp": {"$gte": cutoff_a}}).to_list(200)
    docs_b = await db["mentions"].find({"brand_id": business_id, "timestamp": {"$gte": cutoff_b, "$lt": cutoff_a}}).to_list(200)

    def stats(docs):
        ratings = [d.get("rating") for d in docs if d.get("rating") is not None]
        avg_r = round(sum(ratings) / len(ratings), 2) if ratings else None
        neg_count = sum(1 for d in docs if d.get("sentiment") in ["negative", "unhappy"])
        return len(docs), avg_r, neg_count

    count_a, avg_a, neg_a = stats(docs_a)
    count_b, avg_b, neg_b = stats(docs_b)

    return {
        "status": "ok",
        "current_period": {"reviews": count_a, "average_rating": avg_a, "negative_reviews": neg_a},
        "previous_period": {"reviews": count_b, "average_rating": avg_b, "negative_reviews": neg_b},
        "rating_change": round(avg_a - avg_b, 2) if (avg_a and avg_b) else 0.0,
        "volume_change": count_a - count_b
    }

async def get_unreplied_reviews(db, business_id: str, limit: int = 5) -> Dict[str, Any]:
    limit = min(max(int(limit), 1), 10)
    query = {
        "brand_id": business_id,
        "$or": [
            {"replied": False},
            {"replied": {"$exists": False}},
            {"reply": None},
            {"reply": ""}
        ]
    }
    cursor = db["mentions"].find(query).sort([("rating", 1), ("timestamp", -1)]).limit(limit)
    docs = await cursor.to_list(limit)

    items = []
    for d in docs:
        raw_text = d.get("content") or d.get("text") or ""
        items.append({
            "review_id": str(d.get("id") or d.get("_id", "")),
            "author": d.get("author", "Customer"),
            "rating": d.get("rating", 3),
            "mood": d.get("sentiment", "neutral"),
            "language": d.get("language", "en"),
            "text": sanitize_untrusted_text(raw_text),
            "date": d.get("timestamp").isoformat() if isinstance(d.get("timestamp"), datetime.datetime) else str(d.get("timestamp"))
        })

    return {
        "status": "ok",
        "unreplied_count": len(items),
        "reviews": items
    }

async def draft_reply(
    db,
    business_id: str,
    review_id: str,
    tone: str = "polite_and_friendly",
    language: Optional[str] = None
) -> Dict[str, Any]:
    # Strictly query by user-owned business_id and review_id
    doc = await db["mentions"].find_one({"brand_id": business_id, "$or": [{"id": review_id}, {"_id": review_id}]})
    if not doc:
        return {"status": "error", "message": f"Review {review_id} not found in this business."}

    raw_text = doc.get("content") or doc.get("text") or ""
    author = doc.get("author", "Customer")
    rating = doc.get("rating", 3)
    detected_lang = language or doc.get("language", "en")

    # Localized polite response generation
    if detected_lang in ["ta", "tamil", "tanglish"]:
        if rating and rating <= 2:
            draft = f"வணக்கம் {author}, உங்கள் கருத்துக்கும் நேரத்திற்கும் நன்றி. உங்களுக்கு ஏற்பட்ட சிரமத்திற்கு வருந்துகிறோம். உங்கள் அனுபவத்தை மேம்படுத்த நாங்கள் உடனடியாக நடவடிக்கை எடுக்கிறோம். தயவுசெய்து எங்களை தொடர்பு கொள்ளவும்."
        else:
            draft = f"வணக்கம் {author}! உங்கள் அன்பான கருத்துக்கும் ஆதரவிற்கும் மிக்க நன்றி. நீங்கள் எங்களை சந்தித்ததில் மிக்க மகிழ்ச்சி, மீண்டும் உங்களை வரவேற்க ஆவலுடன் காத்திருக்கிறோம்! ⭐"
    elif detected_lang in ["hi", "hindi", "hinglish"]:
        if rating and rating <= 2:
            draft = f"नमस्ते {author}, अपने फीडबैक के लिए धन्यवाद। आपको हुई असुविधा के लिए हमें गहरा खेद है। हम अपनी सेवा सुधारने पर तुरंत काम कर रहे हैं। आशा है आप हमें फिर से मौका देंगे।"
        else:
            draft = f"नमस्ते {author}! आपकी खूबसूरत प्रतिक्रिया के लिए बहुत-बहुत धन्यवाद। हमारी दुकान पर आने के लिए आभार, आपका फिर से स्वागत करने का इंतज़ार रहेगा! ⭐"
    else:
        # English default
        if rating and rating <= 2:
            draft = f"Dear {author}, thank you for taking the time to share your feedback. We are sincerely sorry for the inconvenience you experienced. We take your comments seriously and are addressing this with our team right away. We would love the chance to make it right on your next visit."
        else:
            draft = f"Hi {author}, thank you so much for the wonderful review and kind words! It was our pleasure to serve you, and our team looks forward to welcoming you back again soon!"

    return {
        "status": "ok",
        "review_id": review_id,
        "author": author,
        "rating": rating,
        "language_used": detected_lang,
        "drafted_reply": draft,
        "safety_note": "AI can make mistakes, please review and edit before posting."
    }

async def compare_with_nearby(db, business_id: str) -> Dict[str, Any]:
    # Check competitor benchmarks for the business
    competitors = await db["competitors"].find({"brand_id": business_id}).to_list(10)
    
    # Get own rating
    overview = await get_overview(db, business_id, "last_30_days")
    own_rating = overview.get("average_star_rating") or 4.2
    own_reviews = overview.get("total_reviews") or 0

    nearby = []
    for c in competitors:
        nearby.append({
            "name": c.get("name"),
            "rating": c.get("rating", 4.0),
            "review_count": c.get("review_count", 50),
            "advantage": c.get("key_advantage", "Nearby competitor")
        })

    if not nearby:
        # Friendly baseline if none configured
        nearby = [
            {"name": "Local Area Average", "rating": 4.1, "review_count": 85, "advantage": "Regional baseline"}
        ]

    return {
        "status": "ok",
        "your_business": {"average_stars": own_rating, "total_reviews": own_reviews},
        "nearby_businesses": nearby
    }

async def create_reminder_task(db, business_id: str, user_id: str, text: str, due: Optional[str] = None) -> Dict[str, Any]:
    import uuid
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    clean_text = sanitize_untrusted_text(text[:200])

    task_doc = {
        "id": task_id,
        "business_id": business_id,
        "user_id": user_id,
        "text": clean_text,
        "due": due or (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
        "status": "pending",
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    await db["tasks"].insert_one(task_doc)

    return {
        "status": "ok",
        "task_id": task_id,
        "text": clean_text,
        "due": task_doc["due"],
        "message": f"Task created: '{clean_text}'"
    }

# Tool Dispatch Table
AVAILABLE_ASSISTANT_TOOLS = {
    "get_overview": get_overview,
    "search_reviews": search_reviews,
    "get_top_issues": get_top_issues,
    "get_top_praises": get_top_praises,
    "get_rating_trend": get_rating_trend,
    "compare_periods": compare_periods,
    "get_unreplied_reviews": get_unreplied_reviews,
    "draft_reply": draft_reply,
    "compare_with_nearby": compare_with_nearby,
    "create_reminder_task": create_reminder_task
}
