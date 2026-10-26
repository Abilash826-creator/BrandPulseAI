"""
Seed Sree Annapoorna (Coimbatore, Tamil Nadu) brand, Instagram connection,
and real-time Instagram mentions into MongoDB Atlas database.
"""

import os
import sys
import json
import asyncio
import datetime

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from app.core.config import settings
from app.services.relevance_filter import relevance_filter
from app.services.ai_engine import ai_engine

async def seed_annapoorna():
    print(f"[*] Connecting to MongoDB Atlas: {settings.DATABASE_NAME}...")
    is_tls = "mongodb+srv://" in settings.MONGODB_URI or "ssl=true" in settings.MONGODB_URI.lower()
    kwargs = {"serverSelectionTimeoutMS": 10000}
    if is_tls:
        kwargs["tlsCAFile"] = certifi.where()

    client = AsyncIOMotorClient(settings.MONGODB_URI, **kwargs)
    db = client[settings.DATABASE_NAME]

    brand_id = "brand_annapoorna_cbe"
    user_id = "user_demo_brand_manager"

    # 1. Seed or Update Sree Annapoorna Brand Document
    brand_doc = {
        "id": brand_id,
        "owner_id": user_id,
        "name": "Sree Annapoorna",
        "industry": "Hospitality, Food & South Indian Culinary Heritage",
        "description": "The Pride of Coimbatore — Iconic South Indian vegetarian restaurant chain renowned for legendary Ghee Roast, Filter Coffee, and Sambar since 1968.",
        "products": [
            "Ghee Roast Dosa", "Filter Coffee", "Sambar Vada", "Rava Dosa",
            "Idli Sambar", "Poori Masala", "Meals", "Mysurpa", "Annapoorna Sweets"
        ],
        "keywords": [
            "Annapoorna", "Sree Annapoorna", "Ghee Roast", "Filter Coffee", "Sambar Vada",
            "RS Puram", "Gandhipuram", "Avinashi Road", "Peoples Park", "Coimbatore Food", "Mysurpa"
        ],
        "hashtags": [
            "#Annapoorna", "#SreeAnnapoorna", "#CoimbatoreFood", "#AnnapoornaCoffee",
            "#GheeRoast", "#CoimbatoreEats", "#SouthIndianFood", "#AnnapoornaSweets"
        ],
        "social_handles": {
            "instagram": "@sreeannapoorna_cbe",
            "twitter": "@sreeannapoorna",
            "facebook": "sreeannapoornacbe"
        },
        "competitors": ["Anandhaas", "Hari Bhavanam", "A2B (Adyar Ananda Bhavan)", "Geetha Canteen", "Saravana Bhavan"],
        "crisis_threshold_negative": 0.35,
        "is_primary": False,
        "created_at": datetime.datetime.now().isoformat()
    }

    await db["brands"].update_one(
        {"id": brand_id},
        {"$set": brand_doc},
        upsert=True
    )
    print(f"[+] Brand '{brand_doc['name']}' saved to MongoDB Atlas.")

    # 2. Seed Connected Instagram Account
    conn_doc = {
        "id": "ig_conn_annapoorna_cbe",
        "brand_id": brand_id,
        "user_id": user_id,
        "instagram_business_account_id": "17841408892341901",
        "instagram_username": "sreeannapoorna_cbe",
        "account_name": "Sree Annapoorna Official (Coimbatore)",
        "profile_picture_url": "https://images.unsplash.com/photo-1552611052-33e04de081de?w=150",
        "followers_count": 148500,
        "status": "connected",
        "permissions": [
            "instagram_basic", "pages_show_list", "pages_read_engagement",
            "pages_manage_posts", "instagram_manage_comments", "instagram_manage_insights"
        ],
        "connected_at": datetime.datetime.now().isoformat(),
        "last_synced_at": datetime.datetime.now().isoformat(),
        "access_token": "EAAB_mock_annapoorna_token_cbe",
        "is_mock": True
    }

    await db["instagram_connections"].update_one(
        {"brand_id": brand_id},
        {"$set": conn_doc},
        upsert=True
    )
    print(f"[+] Instagram Connection for '@{conn_doc['instagram_username']}' saved.")

    # 3. Load & Enrich Annapoorna Instagram Dataset
    dataset_path = os.path.join(backend_dir, "app", "datasets", "annapoorna_coimbatore", "annapoorna_instagram_dataset.json")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    # Delete existing mentions for clean re-seed
    await db["mentions"].delete_many({"brand_id": brand_id})

    mentions_to_insert = []
    for item in records:
        content = item["text"]
        transcript = item.get("transcript")
        combined_text = content
        if transcript:
            combined_text = f"{content}\n[Audio Transcript]: {transcript}"

        # Analyze relevance and context
        rel_data = relevance_filter.analyze(
            text=combined_text,
            brand_name=brand_doc["name"],
            tracked_products=brand_doc["products"],
            tracked_keywords=brand_doc["keywords"],
            tracked_hashtags=brand_doc["hashtags"],
            competitors=brand_doc["competitors"]
        )

        sent, sent_score = ai_engine.analyze_sentiment(combined_text)
        if item.get("sentiment") == "negative":
            sent = "negative"
            sent_score = -0.72
        elif item.get("sentiment") == "positive":
            sent = "positive"
            sent_score = 0.88

        emotions, dominant_emotion = ai_engine.detect_emotions(combined_text)
        if item.get("emotion"):
            dominant_emotion = item["emotion"]
            emotions[item["emotion"]] = 0.65

        reach = item.get("author_followers", 25000)
        likes = item.get("like_count", 450)
        comments_cnt = item.get("comments_count", 35)
        virality_score = ai_engine.calculate_virality_score(reach, likes + comments_cnt, sent_score)
        is_crisis_flag = (sent == "negative" and (virality_score > 65.0 or dominant_emotion in ["anger", "fear"]))

        is_comm = item.get("media_type") == "COMMENT" or bool(item.get("comment_id"))
        post_id = item.get("post_id") or item["id"]
        comm_id = item.get("comment_id")
        
        if is_comm and comm_id:
            direct_url = f"https://www.instagram.com/p/{post_id}/c/{comm_id}/"
            parent_url = f"https://www.instagram.com/p/{post_id}/"
        elif item.get("media_type") == "REEL":
            direct_url = f"https://www.instagram.com/reel/{post_id}/"
            parent_url = None
        else:
            direct_url = f"https://www.instagram.com/p/{post_id}/"
            parent_url = None

        mention_doc = {
            "id": f"men_{item['id']}",
            "brand_id": brand_id,
            "brand_name": brand_doc["name"],
            "platform": "instagram",
            "post_id": post_id,
            "comment_id": comm_id,
            "parent_post_id": post_id if is_comm else None,
            "parent_post_url": parent_url,
            "parent_media_type": "REEL" if item.get("media_type") == "REEL" else "POST",
            "parent_caption": f"Sree Annapoorna Iconic Dishes & Daily Specials in {item.get('branch_location', 'Coimbatore')}" if is_comm else None,
            "author": item["author"],
            "author_handle": item["author_handle"],
            "author_followers": reach,
            "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={item['author_handle']}",
            "content": content,
            "caption": content,
            "hashtags": rel_data["matched_hashtags"],
            "mentions": ["@sreeannapoorna_cbe"],
            "media_type": item.get("media_type", "POST"),
            "sentiment": sent,
            "sentiment_score": sent_score,
            "emotions": emotions,
            "dominant_emotion": dominant_emotion,
            "intent": item.get("intent", rel_data["context"].get("intent", "general")),
            "intent_confidence": 0.90,
            "reach": reach,
            "engagement_score": likes + comments_cnt,
            "virality_score": virality_score,
            "topic_cluster": f"Annapoorna {item.get('branch_location', 'Coimbatore')} Dishes",
            "is_crisis_flag": is_crisis_flag,
            "timestamp": item.get("timestamp", datetime.datetime.now().isoformat()),
            "url": direct_url,
            
            "brand_detected": rel_data["brand_detected"],
            "product_detected": item.get("product") or rel_data["product_detected"],
            "detected_brands": ["Sree Annapoorna"],
            "detected_products": [item.get("product")] if item.get("product") else rel_data["detected_products"],
            "matched_keywords": rel_data["matched_keywords"],
            "matched_hashtags": rel_data["matched_hashtags"],
            "relevance_score": rel_data["relevance_score"],
            "relevance_reason": rel_data["reason"],
            "aspects": rel_data["aspects"],
            "context": rel_data["context"],
            "transcript": transcript,
            "media_analysis_available": bool(transcript),
            "media_analysis_status": item.get("media_analysis_status", "transcript_analyzed" if transcript else "not_video")
        }
        mentions_to_insert.append(mention_doc)

    if mentions_to_insert:
        await db["mentions"].insert_many(mentions_to_insert)
        print(f"[+] Successfully seeded {len(mentions_to_insert)} Instagram mentions for Sree Annapoorna.")

    # 4. Also add Annapoorna to Demo User's accessible brand IDs
    await db["users"].update_one(
        {"email": "demo@brandpulse.ai"},
        {"$addToSet": {"brand_ids": brand_id}}
    )

    print("\n>>> Sree Annapoorna Coimbatore Seed Complete! <<<")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_annapoorna())
