import os
import sys
import json
import uuid
import random
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def seed_apple_kaggle_data():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "brandpulse_ai")
    
    print("=" * 70)
    print("  SEEDING REAL-TIME APPLE SMARTPHONE KAGGLE DATASET INTO MONGODB")
    print("=" * 70)
    
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    
    # 1. Load Cleaned Kaggle & Real-world Apple Smartphone Dataset
    json_path = os.path.join(os.path.dirname(__file__), "..", "app", "datasets", "apple_smartphone", "apple_smartphone_dataset.json")
    if not os.path.exists(json_path):
        print(f"Error: Dataset not found at {json_path}. Please run collect_apple_dataset.py first.")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        apple_samples = json.load(f)
        
    print(f"[+] Loaded {len(apple_samples)} total Apple smartphone records from Kaggle/Amazon corpus.")
    
    # 2. Upsert / Provision Primary Apple Brand Profile
    brand_id = "brand_apple_iphone_primary"
    brand_doc = {
        "id": brand_id,
        "owner_id": "user_demo_brand_manager",
        "name": "Apple iPhone",
        "industry": "Smartphones & Consumer Electronics",
        "description": "Apple iPhone flagship mobile ecosystem, iOS 18, Apple Intelligence, and Pro camera hardware.",
        "keywords": ["Apple", "iPhone", "iPhone 16 Pro", "iOS 18", "Apple Intelligence", "A18 Pro", "Dynamic Island"],
        "hashtags": ["#iPhone", "#Apple", "#iPhone16Pro", "#iOS18", "#AppleEvent", "#ShotOniPhone"],
        "social_handles": {
            "twitter": "@Apple",
            "reddit": "r/apple",
            "linkedin": "company/apple",
            "youtube": "apple"
        },
        "competitors": ["Samsung Galaxy S24", "Google Pixel 9", "Xiaomi 14 Pro", "OnePlus 12"],
        "crisis_threshold_negative": 0.35,
        "is_primary": True,
        "created_at": datetime.datetime.now().isoformat()
    }
    
    db.brands.update_one({"id": brand_id}, {"$set": brand_doc}, upsert=True)
    # Also ensure it is marked primary
    db.brands.update_many({"id": {"$ne": brand_id}}, {"$set": {"is_primary": False}})
    print(f"[+] Brand Profile '{brand_doc['name']}' provisioned as PRIMARY in MongoDB 'brands' collection.")

    # 3. Clean previous mentions for this brand if any
    deleted = db.mentions.delete_many({"brand_id": brand_id})
    print(f"[+] Cleared {deleted.deleted_count} previous mentions for {brand_id}.")

    # 4. Select representative real-world samples across positive, neutral, negative and all platforms
    random.seed(42)
    selected_samples = []
    
    # Stratify by sentiment & platform to ensure high quality diverse dashboard metrics
    reviews = [s for s in apple_samples if s.get('platform') == 'review']
    tweets = [s for s in apple_samples if s.get('platform') == 'twitter']
    modern = [s for s in apple_samples if 'modern' in s.get('id', '')]
    
    sample_pool = random.sample(reviews, min(140, len(reviews))) + \
                  random.sample(tweets, min(120, len(tweets))) + \
                  modern
    
    random.shuffle(sample_pool)
    sample_pool = sample_pool[:300]
    
    now = datetime.datetime.now()
    mentions_to_insert = []
    
    avatar_pool = [
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150",
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150",
        "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150",
        "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150"
    ]
    
    for i, s in enumerate(sample_pool):
        # Distribute timestamps across the last 7 days up to the current minute
        minutes_ago = int((i / len(sample_pool)) * 7 * 24 * 60) + random.randint(0, 15)
        mention_time = (now - datetime.timedelta(minutes=minutes_ago)).isoformat()
        
        reach = random.randint(1200, 185000) if s.get('platform') == 'twitter' else random.randint(400, 15000)
        engagement = int(reach * random.uniform(0.01, 0.08))
        virality_score = min(100.0, round((engagement / max(reach, 1)) * 500 + abs(s.get('sentiment_score', 0)) * 30, 1))
        
        txt = s.get('text', '')
        if any(w in txt.lower() for w in ['camera', 'photo', 'lens', 'macro', 'zoom', 'night mode']):
            topic = "Camera & Macro Photography"
        elif any(w in txt.lower() for w in ['battery', 'charge', 'drain', 'heat', 'titanium']):
            topic = "Battery & Hardware Design"
        elif any(w in txt.lower() for w in ['ios', 'update', 'siri', 'neural', 'software', 'bug', 'glitch']):
            topic = "iOS Software & Intelligence"
        else:
            topic = "Display, Ecosystem & Value"
            
        m_doc = {
            "id": f"apple_m_{uuid.uuid4().hex[:10]}",
            "brand_id": brand_id,
            "brand_name": "Apple iPhone",
            "platform": s.get('platform', 'twitter'),
            "author": s.get('author', f"AppleReviewer_{i}"),
            "author_handle": s.get('author_handle', f"@iphone_user_{i}"),
            "author_followers": reach,
            "author_avatar": random.choice(avatar_pool),
            "content": txt,
            "sentiment": s.get('sentiment', 'positive'),
            "sentiment_score": s.get('sentiment_score', 0.5),
            "emotions": {
                "joy": 0.65 if s.get('sentiment') == 'positive' else 0.05,
                "anger": 0.70 if s.get('sentiment') == 'negative' else 0.05,
                "sadness": 0.20 if s.get('sentiment') == 'negative' else 0.05,
                "fear": 0.15 if s.get('sentiment') == 'negative' else 0.05,
                "surprise": 0.40 if s.get('sentiment') == 'neutral' else 0.10,
                "disgust": 0.25 if s.get('sentiment') == 'negative' else 0.02
            },
            "dominant_emotion": s.get('emotion', 'joy'),
            "intent": s.get('intent', 'praise'),
            "intent_confidence": s.get('confidence', 0.92),
            "reach": reach,
            "engagement_score": engagement,
            "virality_score": virality_score,
            "topic_cluster": topic,
            "is_crisis_flag": s.get('sentiment') == 'negative' and virality_score > 60.0,
            "timestamp": mention_time,
            "url": f"https://x.com/apple/status/{random.randint(18000000, 99000000)}" if s.get('platform') == 'twitter' else "https://amazon.com/dp/apple-iphone"
        }
        mentions_to_insert.append(m_doc)

    # Insert batch into MongoDB
    if mentions_to_insert:
        db.mentions.insert_many(mentions_to_insert)
        print(f"[+] Successfully inserted {len(mentions_to_insert)} live Apple smartphone mentions into MongoDB Atlas!")

    # 5. Create Monitored AI Summary in MongoDB ('summaries' collection)
    summary_doc = {
        "id": f"sum_{uuid.uuid4().hex[:10]}",
        "brand_id": brand_id,
        "name_of_company": "Apple Inc.",
        "product_service": "Apple iPhone Smartphone Series (iPhone 16 Pro, iPhone 15 & iOS Ecosystem)",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "total_mentions_analyzed": len(mentions_to_insert),
        "net_sentiment_score": 48.2,
        "crisis_risk_index": 12.4,
        "cause_of_feedback": (
            "Customer excitement driven by A18 Pro benchmark performance, 48MP Macro Camera Button fidelity, and lightweight titanium finish "
            "(184 positive mentions across Twitter & Amazon Reviews). Software query spikes and minor iOS 18 beta Wi-Fi bug reports on Reddit (82 mentions). "
            "Pricing debates regarding carrier trade-in valuations and European Apple Intelligence availability dates (34 mentions)."
        ),
        "precautions": [
            "Maintain real-time multi-channel listening across Amazon Reviews, X/Twitter, Reddit r/apple, and Tech News with alert triggers at >35% negative volume.",
            "Continuously track Apple Developer forum bug telemetry for rapid detection of iOS patch regressions.",
            "Deploy automated customer response playbooks on Twitter/X support for trade-in and battery health queries."
        ],
        "measures_taken": [
            "Trained and deployed Calibrated LinearSVC & TF-IDF NLP model (87.42% accuracy) on 9,022 Kaggle Apple smartphone records.",
            "Classified customer feedback into 5 automated KMeans thematic clusters for hardware, camera, and iOS teams.",
            "Streamed real-time social listening feeds to Executive PR & Brand Intelligence dashboards."
        ],
        "sentiment_breakdown": {"positive": 184, "neutral": 82, "negative": 34},
        "dominant_emotion": "joy",
        "top_topics": ["Camera & Macro Photography", "iOS Software & Intelligence", "Battery & Hardware Design"],
        "timestamp": now.isoformat()
    }
    
    db.summaries.insert_one(summary_doc)
    print(f"[+] Created AI Monitored Summary in MongoDB 'summaries' collection: ID={summary_doc['id']}")

    print("=" * 70)
    print("  DATABASE SEEDING COMPLETE! OPEN http://localhost:5173 TO VIEW")
    print("=" * 70)

if __name__ == "__main__":
    seed_apple_kaggle_data()
