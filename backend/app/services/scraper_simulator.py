import os
import json
import uuid
import random
import datetime
from typing import List, Dict, Any, Optional
import logging
from app.services.ai_engine import ai_engine

logger = logging.getLogger("brandpulse.scraper_simulator")

class ScraperSimulator:
    def __init__(self):
        self.authors_pool = [
            {"name": "Karthik Subramanian", "handle": "karthik_subramanian", "followers": 240, "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150"},
            {"name": "Pooja Sharma", "handle": "pooja_s", "followers": 180, "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150"},
            {"name": "Rohan Mehta", "handle": "rohan_m", "followers": 310, "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150"},
            {"name": "Deepa Sundaram", "handle": "deepa_sundaram", "followers": 95, "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"},
            {"name": "Arjun Reddy", "handle": "arjun_r", "followers": 520, "avatar": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150"},
            {"name": "Meera Krishnan", "handle": "meera_k", "followers": 140, "avatar": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150"},
            {"name": "Anand Verma", "handle": "anand_v", "followers": 85, "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150"},
            {"name": "Divya Nair", "handle": "divya_nair", "followers": 290, "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150"}
        ]

        self.platforms = ["google_reviews", "facebook", "instagram", "review"]

        # Cache Kaggle Apple smartphone samples if available
        self.apple_dataset_cache = []
        self._load_apple_dataset()

        # Context templates tailored for local shops and small businesses
        self.templates = {
            "normal": {
                "positive": [
                    "Awesome quality and courteous staff at {brand}! Fresh items and prompt service every time. Highly recommended! ⭐⭐⭐⭐⭐",
                    "Food romba nalla irundhuchu at {brand}! Sambhar and chutney taste was authentic. Definitely coming back. ⭐⭐⭐⭐⭐",
                    "Bohot achha experience raha! Staff behaviour was polite and store premises are neat and clean. ⭐⭐⭐⭐",
                    "Visited {brand} this morning. Clean ambiance, quick billing counter, and reasonable prices. Worth every rupee!",
                    "Best customer service in the neighborhood! The manager at {brand} personally helped us find what we needed. ⭐⭐⭐⭐⭐"
                ],
                "neutral": [
                    "Average experience at {brand}. Items were good but parking space was very limited during rush hours. ⭐⭐⭐",
                    "Price thoda zyada hai compared to nearby shops, but product quality at {brand} is decent. ⭐⭐⭐",
                    "Standard service at {brand}. Nothing special to complain about, but waiting time can be reduced. ⭐⭐⭐",
                    "Decent collection at {brand}. Would like to see more varieties in stock next time."
                ],
                "negative": [
                    "Very disappointed with the waiting time at {brand}. We waited over 35 minutes just to get our order! ⭐⭐",
                    "Rude behavior from the billing counter staff today. Poor customer handling at {brand}! ⭐",
                    "Cleanliness was not maintained well near the dining area at {brand}. Management please look into this. ⭐⭐",
                    "Charged higher than MRP for a few items at {brand}. Check your receipt before leaving! ⭐"
                ]
            },
            "crisis": {
                "negative": [
                    "WORST EXPERIENCE EVER at {brand}! Found hair in the food and staff was completely unapologetic! Refunding refused! ⭐",
                    "Terrible hygiene and foul smell near the counter at {brand}. Multiple customers were complaining today! ⭐",
                    "Do NOT visit {brand}! Extremely bad attitude from the supervisor when we pointed out expired stock on display. ⭐",
                    "Billing software crashed and we were stuck at {brand} for 45 minutes with zero assistance! ⭐"
                ],
                "neutral": [
                    "Local community alert: Several complaints reported regarding long queues and slow billing at {brand} this weekend.",
                    "Discussion in local WhatsApp group regarding recent service quality dips at {brand}."
                ],
                "positive": [
                    "The owner of {brand} quickly apologized and sorted out the issue with our bill. Appreciate the prompt resolution."
                ]
            },
            "viral_launch": {
                "positive": [
                    "New branch of {brand} is mind-blowing! Outstanding hospitality, fresh items, and beautiful interiors! 🔥",
                    "Everyone in our locality is talking about {brand}'s weekend specials. Taste is unbeatable! ⭐⭐⭐⭐⭐",
                    "Genuinely one of the finest shops in town. {brand} has set the benchmark for customer care and hygiene!"
                ],
                "neutral": [
                    "Grand opening of {brand}'s new branch drew huge crowds today. Expect heavy waiting times."
                ]
            },
            "competitor_attack": {
                "positive": [
                    "{brand} still wins on service quality and friendly staff compared to nearby shops.",
                    "Visited other shops nearby but {brand}'s cleanliness and taste are far superior."
                ],
                "neutral": [
                    "Comparing rates between {brand} and other shops in the locality. Pretty close on most everyday items."
                ],
                "negative": [
                    "Nearby shops are offering better festive discounts right now compared to {brand}.",
                    "A new shop opened down the road from {brand} with more parking space and cheaper prices."
                ]
            }
        }

    def _load_apple_dataset(self):
        json_path = os.path.join(os.path.dirname(__file__), "..", "datasets", "apple_smartphone", "apple_smartphone_dataset.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.apple_dataset_cache = json.load(f)
            except Exception as e:
                logger.warning(f"[Brandpulse AI] Warning loading Apple dataset cache: {e}")

    def generate_mention(
        self,
        brand_name: str,
        brand_id: str,
        scenario: str = "normal",
        competitors: Optional[List[str]] = None,
        custom_sentiment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a single mention enriched with trained ML sentiment, emotion, intent, and virality.
        Draws from real Kaggle Apple dataset if brand is Apple / iPhone.
        """
        is_apple = "apple" in brand_name.lower() or "iphone" in brand_name.lower()

        if is_apple and self.apple_dataset_cache and scenario == "normal" and not custom_sentiment:
            sample = random.choice(self.apple_dataset_cache)
            content = sample["text"]
            platform = sample.get("platform", "twitter")
            author_name = sample.get("author", "AppleUser")
            author_handle = sample.get("author_handle", "@apple_fan")
        else:
            competitor_name = random.choice(competitors) if competitors else "ApexCloud"
            scenario_data = self.templates.get(scenario, self.templates["normal"])
            
            if custom_sentiment:
                sentiment_choice = custom_sentiment
            else:
                if scenario == "crisis":
                    sentiment_choice = random.choices(["negative", "neutral", "positive"], weights=[0.85, 0.10, 0.05])[0]
                elif scenario == "viral_launch":
                    sentiment_choice = random.choices(["positive", "neutral", "negative"], weights=[0.88, 0.09, 0.03])[0]
                elif scenario == "competitor_attack":
                    sentiment_choice = random.choices(["negative", "neutral", "positive"], weights=[0.55, 0.25, 0.20])[0]
                else:
                    sentiment_choice = random.choices(["positive", "neutral", "negative"], weights=[0.60, 0.25, 0.15])[0]

            pool = scenario_data.get(sentiment_choice, scenario_data.get("positive", ["Great platform!"]))
            template = random.choice(pool)
            content = template.format(brand=brand_name, competitor=competitor_name)

            author = random.choice(self.authors_pool)
            author_name = author["name"]
            author_handle = author["handle"]
            platform = random.choice(self.platforms)
        
        # AI analysis using trained ML models
        sentiment, sentiment_score = ai_engine.analyze_sentiment(content)
        emotions, dominant_emotion = ai_engine.detect_emotions(content)
        intent, intent_confidence = ai_engine.classify_intent(content)
        
        # Realistic reach & engagement
        author_ref = next((a for a in self.authors_pool if a["handle"] == author_handle), None)
        base_reach = author_ref["followers"] if author_ref else random.randint(5000, 85000)
        
        if scenario == "crisis" and sentiment == "negative":
            reach = int(base_reach * random.uniform(1.2, 3.5))
            engagement = int(reach * random.uniform(0.04, 0.15))
        elif scenario == "viral_launch" and sentiment == "positive":
            reach = int(base_reach * random.uniform(1.5, 4.0))
            engagement = int(reach * random.uniform(0.05, 0.20))
        else:
            reach = int(base_reach * random.uniform(0.2, 0.8))
            engagement = int(reach * random.uniform(0.01, 0.04))

        virality_score = ai_engine.calculate_virality_score(reach, engagement, sentiment_score)
        is_crisis_flag = (sentiment == "negative" and (virality_score > 70.0 or dominant_emotion in ["anger", "fear"]))

        mention_id = f"men_{uuid.uuid4().hex[:10]}"
        url_map = {
            "twitter": f"https://x.com/{author_handle.replace('@', '')}/status/{random.randint(10000000, 99999999)}",
            "reddit": f"https://reddit.com/r/apple/comments/{mention_id}/",
            "linkedin": f"https://linkedin.com/feed/update/{mention_id}/",
            "news": f"https://techcrunch.com/2026/08/{mention_id}/",
            "review": f"https://amazon.com/dp/B0BN56QXX_{mention_id}"
        }

        mention_doc = {
            "id": mention_id,
            "brand_id": str(brand_id),
            "brand_name": str(brand_name),
            "platform": str(platform),
            "author": str(author_name),
            "author_handle": str(author_handle),
            "author_followers": int(base_reach),
            "author_avatar": f"https://images.unsplash.com/photo-{1500000000000 + (abs(hash(author_name)) % 50000000)}?w=150",
            "content": str(content),
            "sentiment": str(sentiment),
            "sentiment_score": float(sentiment_score),
            "emotions": {k: float(v) for k, v in emotions.items()} if isinstance(emotions, dict) else {},
            "dominant_emotion": str(dominant_emotion),
            "intent": str(intent),
            "intent_confidence": float(intent_confidence),
            "reach": int(reach),
            "engagement_score": int(engagement),
            "virality_score": float(virality_score),
            "topic_cluster": "Camera & Display" if any(w in content.lower() for w in ["camera", "display", "photo", "screen"]) else ("Battery & Hardware" if any(w in content.lower() for w in ["battery", "charge", "titanium", "heat"]) else "iOS & Ecosystem"),
            "is_crisis_flag": bool(is_crisis_flag),
            "is_simulated": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "url": url_map.get(platform, "https://apple.com")
        }
        return mention_doc

    def generate_historical_dataset(
        self,
        brand_name: str,
        brand_id: str,
        days: int = 7,
        mentions_per_day: int = 25,
        competitors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        historical_mentions = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for d in range(days, 0, -1):
            day_date = now - datetime.timedelta(days=d)
            day_volume = int(mentions_per_day * random.uniform(0.7, 1.4))
            for i in range(day_volume):
                minute_offset = random.randint(0, 1439)
                mention_time = day_date.replace(hour=0, minute=0, second=0) + datetime.timedelta(minutes=minute_offset)
                
                mention = self.generate_mention(brand_name, brand_id, scenario="normal", competitors=competitors)
                mention["timestamp"] = mention_time
                mention["is_simulated"] = True
                historical_mentions.append(mention)

        historical_mentions.sort(key=lambda m: m["timestamp"] if isinstance(m["timestamp"], datetime.datetime) else str(m["timestamp"]))
        return historical_mentions

scraper_simulator = ScraperSimulator()
