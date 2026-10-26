import os
import json
import logging
import datetime
import random
from typing import Dict, List, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
import certifi
from app.core.config import settings

logger = logging.getLogger("brandpulse.db")

class DatabaseManager:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.is_mongodb_connected: bool = False
        self.active_uri: str = settings.MONGODB_URI

    def _mask_uri(self, uri: str) -> str:
        if not uri:
            return ""
        if "@" in uri:
            try:
                prefix, rest = uri.split("://", 1)
                user_pass, host_part = rest.split("@", 1)
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    return f"{prefix}://{user}:****@{host_part}"
                return f"{prefix}://****@{host_part}"
            except Exception:
                return uri
        return uri

    def _create_client(self, uri: str) -> AsyncIOMotorClient:
        is_tls = "mongodb+srv://" in uri or "ssl=true" in uri.lower() or "tls=true" in uri.lower()
        kwargs = {
            "serverSelectionTimeoutMS": 6000,
            "connectTimeoutMS": 6000,
        }
        if is_tls:
            try:
                ca_path = certifi.where()
                if ca_path and os.path.exists(ca_path):
                    kwargs["tlsCAFile"] = ca_path
            except Exception:
                pass
            
        return AsyncIOMotorClient(uri, **kwargs)


    async def connect(self, custom_uri: Optional[str] = None) -> Tuple[bool, str]:
        target_uri = (custom_uri.strip() if custom_uri else None) or settings.MONGODB_URI
        
        logger.info(f"[DB] Attempting connection to MongoDB: {self._mask_uri(target_uri)}")
        
        # 1. Attempt primary target URI
        success, client, msg = await self._test_connection(target_uri)
        
        # 2. If target failed and it was the default startup without explicit custom_uri, try local fallback
        if not success and not custom_uri:
            fallback_uri = "mongodb://127.0.0.1:27017"
            if target_uri != fallback_uri:
                logger.info(f"[DB] Primary MongoDB unreachable. Trying local fallback: {fallback_uri}")
                fb_success, fb_client, fb_msg = await self._test_connection(fallback_uri)
                if fb_success:
                    target_uri = fallback_uri
                    success = True
                    client = fb_client
                    msg = "Connected via local fallback"

        if success and client:
            old_client = self.client
            self.client = client
            self.db = self.client[settings.DATABASE_NAME]
            self.is_mongodb_connected = True
            self.active_uri = target_uri

            if old_client and old_client != client:
                try:
                    old_client.close()
                except Exception:
                    pass

            # Ensure indexes & seed default dataset if empty
            await self._ensure_seeded(self.db)
            
            db_type = "MongoDB Atlas (Live Cloud)" if "mongodb+srv://" in target_uri else "Local MongoDB (localhost:27017)"
            friendly_msg = f"Connected successfully to {db_type} — Database: {settings.DATABASE_NAME}"
            logger.info(f"[DB] {friendly_msg}")
            return True, friendly_msg
        elif not custom_uri:
            try:
                import mongomock_motor
                logger.info("[DB] Live MongoDB unreachable on localhost. Initializing local in-memory MongoMock storage fallback...")
                mock_client = mongomock_motor.AsyncMongoMockClient()
                self.client = mock_client
                self.db = mock_client[settings.DATABASE_NAME]
                self.is_mongodb_connected = True
                self.active_uri = "mongomock://inmemory"
                await self._ensure_seeded(self.db)
                friendly_msg = f"Connected to In-Memory MongoMock (Local Dev Fallback) — Database: {settings.DATABASE_NAME}"
                logger.info(f"[DB] {friendly_msg}")
                return True, friendly_msg
            except Exception as mock_err:
                logger.warning(f"[DB] Could not initialize mongomock fallback: {mock_err}")
                self.db = None
                self.is_mongodb_connected = False
                return False, f"MongoDB connection failed: {msg}"
        else:
            # If we were already connected to a working instance, preserve it
            if self.client and self.db is not None:
                logger.warning(f"[DB] Failed to switch to {self._mask_uri(target_uri)}, preserving existing connection: {msg}")
                return False, f"Could not connect to requested URI ({msg}). Preserving existing active database."
                
            self.db = None
            self.is_mongodb_connected = False
            return False, f"MongoDB connection failed: {msg}"

    async def _test_connection(self, uri: str) -> Tuple[bool, Optional[AsyncIOMotorClient], str]:
        try:
            client = self._create_client(uri)
            await client.admin.command("ping")
            return True, client, "OK"
        except Exception as e:
            err_str = str(e)
            if "Authentication failed" in err_str or "bad auth" in err_str.lower():
                msg = "Authentication failed: Verify MongoDB username and password."
            elif "timed out" in err_str.lower() or "timeout" in err_str.lower():
                msg = "Connection timed out: Check IP Access List (whitelist 0.0.0.0/0 on Atlas) or local service status."
            elif "SSL" in err_str or "handshake" in err_str.lower():
                msg = "SSL/TLS handshake error: Ensure SSL is enabled only for Atlas clusters, not local non-TLS instances."
            else:
                msg = err_str
            return False, None, msg

    async def _ensure_seeded(self, db):
        """
        Creates indexes and seeds initial demo workspace data if the database is newly initialized.
        """
        try:
            from app.core.security import get_password_hash
            from app.services.scraper_simulator import scraper_simulator

            # 1. Indexes
            try:
                await db["users"].create_index("email", unique=True)
                await db["brands"].create_index("id", unique=True)
                await db["mentions"].create_index([("brand_id", 1), ("timestamp", -1)])
                await db["mentions"].create_index([("brand_id", 1), ("platform", 1)])
                await db["mentions"].create_index([("business_id", 1), ("created_at", -1)])
                await db["mentions"].create_index([("brand_id", 1), ("is_simulated", 1)])
                await db["instagram_connections"].create_index("brand_id", unique=True)
                # Phase 3 Required Indexes
                await db["alerts"].create_index([("brand_id", 1), ("status", 1), ("created_at", -1)])
                await db["alerts"].create_index([("brand_id", 1), ("is_simulated", 1)])
                await db["summaries"].create_index([("brand_id", 1), ("created_at", -1)])
                await db["auth_logs"].create_index([("user_id", 1), ("login_timestamp", -1)])
                await db["firewall_logs"].create_index([("timestamp", -1)])
                # 90-day TTL indexes (90 * 86400 = 7,776,000 seconds)
                try:
                    await db["auth_logs"].create_index("login_timestamp", expireAfterSeconds=7776000)
                except Exception:
                    pass
                try:
                    await db["firewall_logs"].create_index("timestamp", expireAfterSeconds=7776000)
                except Exception:
                    pass
            except Exception as idx_err:
                logger.debug(f"[DB Seed] Index check: {idx_err}")

            # 2. Seed Platform Admin User if not already present
            admin_user = await db["users"].find_one({"role": "admin"})
            if not admin_user:
                admin_doc = {
                    "id": "user_admin_01",
                    "email": "admin@brandpulse.ai",
                    "full_name": "Platform Administrator",
                    "role": "admin",
                    "organization": "BrandPulse Operations",
                    "hashed_password": get_password_hash("admin1234"),
                    "is_active": True,
                    "created_at": utc_now().isoformat(),
                    "brand_ids": [],
                    "login_count": 0,
                    "last_login": utc_now().isoformat()
                }
                await db["users"].insert_one(admin_doc)

            # 3. Seed demo workspace ONLY when DEMO_MODE is true
            if settings.DEMO_MODE:
                demo_user = await db["users"].find_one({"email": "demo@brandpulse.ai"})
                default_brand_id = "brand_demo_owner_default"

                if not demo_user:
                    logger.info("[DB Seed] DEMO_MODE is true. Seeding demo workspace and sample dataset...")

                    # Seed Demo User
                    user_doc = {
                        "id": "user_demo_owner",
                        "email": "demo@brandpulse.ai",
                        "full_name": "Ramesh Kumar",
                        "role": "owner",
                        "organization": "Annapoorna Bhavan",
                        "hashed_password": get_password_hash("demo1234"),
                        "is_active": True,
                        "created_at": utc_now().isoformat(),
                        "brand_ids": [default_brand_id],
                        "login_count": 1,
                        "last_login": utc_now().isoformat()
                    }
                    await db["users"].insert_one(user_doc)

                    # Also seed demo_owner@brandpulse.ai for demo-login compatibility
                    demo_owner_doc = {
                        "id": "user_demo_owner_alt",
                        "email": "demo_owner@brandpulse.ai",
                        "full_name": "Demo Business Owner",
                        "role": "owner",
                        "organization": "Annapoorna Bhavan",
                        "hashed_password": get_password_hash("demo1234"),
                        "is_active": True,
                        "created_at": utc_now().isoformat(),
                        "brand_ids": [default_brand_id],
                        "login_count": 1,
                        "last_login": utc_now().isoformat()
                    }
                    await db["users"].insert_one(demo_owner_doc)

                    # Seed Default Business (Local Restaurant & Sweets)
                    brand_doc = {
                        "id": default_brand_id,
                        "owner_id": user_doc["id"],
                        "name": "Annapoorna Bhavan",
                        "business_type": "restaurant",
                        "industry": "Food & Beverage",
                        "description": "Authentic South Indian vegetarian dining, quick snacks, and fresh traditional sweets.",
                        "locations": [
                            {
                                "id": "loc_tnagar_main",
                                "name": "T. Nagar Main Branch",
                                "address": "42 Usman Road, T. Nagar",
                                "city": "Chennai",
                                "phone": "+91 98401 23456",
                                "google_place_id": "ChIJ_annapoorna_tnagar",
                                "is_primary": True
                            },
                            {
                                "id": "loc_annanagar_branch",
                                "name": "Anna Nagar Branch",
                                "address": "2nd Avenue, Anna Nagar",
                                "city": "Chennai",
                                "phone": "+91 98402 34567",
                                "google_place_id": "ChIJ_annapoorna_annanagar",
                                "is_primary": False
                            }
                        ],
                        "topics": ["Food Quality & Taste", "Service Speed", "Cleanliness & Hygiene", "Waiting Time", "Price & Portion", "Staff Behavior"],
                        "products": ["Special Ghee Roast Dosa", "Filter Coffee", "Mysore Pak", "Mini Tiffin", "Sambar Vada"],
                        "keywords": ["Annapoorna", "Annapoorna Bhavan", "Dosa", "Filter Coffee"],
                        "hashtags": ["#AnnapoornaBhavan", "#ChennaiFoodie", "#SouthIndianFood"],
                        "social_handles": {},
                        "competitors": [], # Neutral empty defaults
                        "crisis_threshold_negative": 0.35,
                        "is_primary": True,
                        "created_at": utc_now().isoformat()
                    }
                    await db["brands"].insert_one(brand_doc)

                    # Seed 7-day Historical Mentions
                    historical = scraper_simulator.generate_historical_dataset(
                        brand_name=brand_doc["name"],
                        brand_id=default_brand_id,
                        days=7,
                        mentions_per_day=30,
                        competitors=brand_doc["competitors"]
                    )
                    if historical:
                        await db["mentions"].insert_many(historical)

                    # Seed Initial Notice / Alert
                    sample_alert = {
                        "id": "alert_initial_sample_01",
                        "brand_id": default_brand_id,
                        "brand_name": brand_doc["name"],
                        "title": "[ATTENTION] Weekend Evening Waiting Time Spike",
                        "severity": "medium",
                        "metric_type": "negative_sentiment_spike",
                        "trigger_value": 38.5,
                        "threshold_value": 35.0,
                        "description": "Detected cluster of 6 Google Reviews and customer comments pointing to long table queues (over 25 mins) between 7:30 PM and 9:00 PM.",
                        "ai_root_cause": "Increased footfall during weekend festival rush with slower billing counter turnover.",
                        "recommendations": [
                            "Open a dedicated express counter for takeaway parcels during peak evening hours.",
                            "Direct waiting customers to the first-floor seating section.",
                            "Respond to Google reviews with a warm apology and note on operational adjustments."
                        ],
                        "status": "active",
                        "is_simulated": True,
                        "created_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3))
                    }
                    await db["alerts"].insert_one(sample_alert)

                    # 3. Check and seed initial Monitored Data Summary if summaries collection is empty
                    summary_count = await db["summaries"].count_documents({})
                    if summary_count == 0:
                        logger.info("[DB Seed] Seeding initial Monitored Data Summary document in MongoDB 'summaries' collection...")
                        now = datetime.datetime.now(datetime.timezone.utc)
                        sample_summary = {
                            "id": "sum_annapoorna_initial_01",
                            "brand_id": default_brand_id,
                            "name_of_company": "Annapoorna Bhavan",
                            "product_service": "Authentic South Indian Vegetarian Dining & Sweets",
                            "company_details": {
                                "business_type": "restaurant",
                                "industry": "Food & Beverage",
                                "description": "Authentic South Indian vegetarian dining, quick snacks, and fresh traditional sweets.",
                                "keywords": ["Annapoorna", "Annapoorna Bhavan", "Dosa", "Filter Coffee"],
                                "hashtags": ["#AnnapoornaBhavan", "#ChennaiFoodie"],
                                "social_handles": {},
                                "competitors": [],
                                "website": "",
                                "owner_organization": "Annapoorna Bhavan"
                            },
                            "date": now.strftime("%Y-%m-%d"),
                            "time": now.strftime("%H:%M:%S"),
                            "timestamp": now.isoformat(),
                            "cause_of_feedback": "Customer feedback is predominantly positive (+68.4% sentiment) celebrating fresh filter coffee, authentic sambhar taste, and hygienic dining ambiance, balanced by occasional feedback regarding weekend evening table waiting queues.",
                            "precautions": [
                                "Monitor Google Reviews and customer comments daily for prompt grievance redressal.",
                                "Maintain strict kitchen hygiene and verify parcel packaging seals.",
                                "Coordinate billing counter staff during peak dinner hours to reduce queue times."
                            ],
                            "measures_taken": [
                                "Introduced dedicated parcel takeaway queue to decongest main dining hall.",
                                "Conducted brief refresher for dining staff on courteous customer engagement.",
                                "Responded to 100% of negative customer reviews on Google with owner contact info."
                            ],
                            "total_mentions_analyzed": 210,
                            "net_sentiment_score": 68.4,
                            "sentiment_breakdown": {
                                "positive_count": 145,
                                "neutral_count": 45,
                                "negative_count": 20,
                                "positive_percentage": 69.0,
                                "neutral_percentage": 21.4,
                                "negative_percentage": 9.6
                            },
                            "dominant_emotions": [
                                {"emotion": "Joy", "percentage": 47.9, "count": 315},
                                {"emotion": "Anger", "percentage": 14.7, "count": 30},
                                {"emotion": "Sadness", "percentage": 14.6, "count": 0},
                                {"emotion": "Fear", "percentage": 12.4, "count": 8},
                                {"emotion": "Surprise", "percentage": 10.4, "count": 0}
                            ],
                            "status": "generated",
                            "created_at": now.isoformat(),
                            "created_by": "AI_Automated_Monitor"
                        }
                        sample_summary["is_simulated"] = True
                        await db["summaries"].insert_one(sample_summary)
                        logger.info("[DB Seed] Monitored Summary seeded successfully in MongoDB.")

        except Exception as seed_err:
            logger.warning(f"[DB Seed] Notice during database check/seed: {seed_err}")

    async def get_status(self) -> Dict[str, Any]:
        coll_counts = {}
        collections_to_check = ["users", "brands", "mentions", "alerts", "reports", "summaries", "auth_logs"]
        
        if self.db is not None and self.is_mongodb_connected:
            for c in collections_to_check:
                try:
                    coll = self.db[c]
                    count = await coll.count_documents({})
                    coll_counts[c] = count
                except Exception:
                    coll_counts[c] = 0
                    
        is_atlas = "mongodb+srv://" in self.active_uri
        mode_str = "MongoDB Atlas (Live Cloud Database)" if is_atlas else ("Local MongoDB (localhost:27017)" if self.is_mongodb_connected else "Disconnected (Database Required)")
        
        return {
            "is_connected": self.is_mongodb_connected,
            "mode": mode_str,
            "database_name": settings.DATABASE_NAME,
            "uri": self._mask_uri(self.active_uri),
            "collections": coll_counts,
            "total_documents": sum(coll_counts.values())
        }

    async def close(self):
        if self.client:
            self.client.close()

db_manager = DatabaseManager()

def get_db():
    if db_manager.db is None or not db_manager.is_mongodb_connected:
        raise RuntimeError("MongoDB connection is not available. Please verify MONGODB_URI in backend/.env or connect via UI")
    return db_manager.db

def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

def format_iso_z(dt: Any) -> str:
    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        else:
            dt = dt.astimezone(datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(dt, str):
        if dt.endswith("Z"):
            return dt
        try:
            parsed = datetime.datetime.fromisoformat(dt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            else:
                parsed = parsed.astimezone(datetime.timezone.utc)
            return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return dt
    return str(dt)

def clean_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    for k, v in list(d.items()):
        if isinstance(v, datetime.datetime):
            d[k] = format_iso_z(v)
        elif isinstance(v, dict):
            d[k] = clean_doc(v)
        elif isinstance(v, list):
            cleaned_list = []
            for x in v:
                if isinstance(x, dict):
                    cleaned_list.append(clean_doc(x))
                elif isinstance(x, datetime.datetime):
                    cleaned_list.append(format_iso_z(x))
                else:
                    cleaned_list.append(x)
            d[k] = cleaned_list
    return d

def clean_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [clean_doc(d) for d in docs]
