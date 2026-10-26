import sys
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Force UTF-8 on Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv("backend/.env")

def view_data():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DATABASE_NAME", "brandpulse_ai")
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
        client.admin.command('ping')
        db = client[db_name]
        is_atlas = "mongodb+srv://" in uri
        mode_str = "MongoDB Atlas (Cloud)" if is_atlas else "Local MongoDB (localhost:27017)"
        print("=" * 70)
        print(f"  CONNECTED TO LIVE MONGODB: {db_name} [{mode_str}]")
        print("=" * 70)
        
        collections = db.list_collection_names()
        print(f"\n[+] COLLECTIONS FOUND ({len(collections)}): {', '.join(collections)}\n")
        
        # 1. Brands
        print("-" * 70)
        print(f"[1] BRANDS (Total Documents: {db.brands.count_documents({})})")
        print("-" * 70)
        for b in db.brands.find().limit(3):
            print(f" • [{b.get('id')}] {b.get('name')} | Industry: {b.get('industry')}")
            print(f"   Keywords: {b.get('keywords')}")
            print(f"   Competitors: {b.get('competitors')}\n")

        # 2. Monitored Data Summaries (Collection: summaries / 'Summary')
        print("-" * 70)
        print(f"[2] MONITORED DATA SUMMARIES (Collection: 'summaries', Total Docs: {db.summaries.count_documents({})})")
        print("-" * 70)
        for s in db.summaries.find().sort("timestamp", -1).limit(3):
            print(f" • [{s.get('id')}] Company: {s.get('name_of_company')} | Product/Service: {s.get('product_service')}")
            print(f"   Date: {s.get('date')} | Time: {s.get('time')} | Mentions: {s.get('total_mentions_analyzed')} | NSS: +{s.get('net_sentiment_score')}%")
            print(f"   Cause of Feedback: {s.get('cause_of_feedback')}")
            print(f"   Precautions ({len(s.get('precautions', []))}):")
            for p in s.get('precautions', [])[:2]:
                print(f"     - {p}")
            print(f"   Measures Taken ({len(s.get('measures_taken', []))}):")
            for m in s.get('measures_taken', [])[:2]:
                print(f"     - {m}")
            print()

        # 3. Authentication Audit Logs (Collection: auth_logs)
        print("-" * 70)
        print(f"[3] AUTHENTICATION AUDIT LOGS (Collection: 'auth_logs', Total Docs: {db.auth_logs.count_documents({})})")
        print("-" * 70)
        for l in db.auth_logs.find().sort("login_timestamp", -1).limit(5):
            print(f" • [{l.get('status')}] User: {l.get('full_name')} ({l.get('email')}) | Role: {l.get('role')}")
            print(f"   Login: {l.get('login_date')} {l.get('login_time')} | IP: {l.get('ip_address')} | Method: {l.get('auth_method')}")
            print(f"   Client: {l.get('user_agent', '')[:70]}...\n")

        # 4. Crisis Alerts
        print("-" * 70)
        print(f"[4] CRISIS ALERTS (Total Documents: {db.alerts.count_documents({})})")
        print("-" * 70)
        for a in db.alerts.find().limit(3):
            print(f" • [{a.get('severity', '').upper()}] {a.get('title')} ({a.get('status')})")
            print(f"   Root cause: {a.get('ai_root_cause')}\n")

        # 5. Recent Mentions
        print("-" * 70)
        print(f"[5] RECENT SOCIAL MENTIONS (Total Documents: {db.mentions.count_documents({})})")
        print("-" * 70)
        for m in db.mentions.find().sort("timestamp", -1).limit(3):
            print(f" • [{m.get('platform', '').upper()}] @{m.get('author_handle', 'anon')} ({m.get('timestamp')})")
            print(f"   Sentiment: {m.get('sentiment', '').upper()} (Score: {m.get('sentiment_score')}) | Emotion: {m.get('dominant_emotion')}")
            print(f"   Content: \"{m.get('content')}\"\n")

        print("=" * 70)
        print("  Database verification successful!")
        print("=" * 70)

    except Exception as e:
        print(f"[!] Could not connect to MongoDB: {e}")

if __name__ == "__main__":
    view_data()


