"""
Facebook Page Reviews & Comments Integration Client for BrandPulse AI.
Supports Meta Graph API for Facebook Pages and mock development mode.
"""

import os
import time
import logging
import datetime
from typing import Dict, List, Any, Optional
import requests

from app.core.config import settings

logger = logging.getLogger("brandpulse.facebook")

class FacebookAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, raw_error: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_error = raw_error

class FacebookClient:
    def __init__(self):
        self.page_id = settings.FACEBOOK_PAGE_ID
        self.access_token = settings.FACEBOOK_ACCESS_TOKEN
        self.mock_mode = settings.FACEBOOK_MOCK_MODE or not bool(self.access_token)
        self.graph_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.graph_version}"

    def is_connected(self, brand_doc: Optional[Dict[str, Any]] = None) -> bool:
        if not brand_doc:
            return False
        handles = brand_doc.get("social_handles", {})
        return bool(handles.get("facebook") or self.page_id)

    def fetch_page_reviews(self, page_id: Optional[str] = None, brand_name: str = "Local Business", max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Fetch Facebook ratings and recommendations.
        """
        active_page_id = page_id or self.page_id
        if not self.mock_mode and self.access_token and active_page_id:
            try:
                url = f"{self.base_url}/{active_page_id}/ratings"
                params = {
                    "fields": "created_time,has_rating,rating,review_text,reviewer{name,id}",
                    "access_token": self.access_token
                }
                resp = requests.get(url, params=params, timeout=10)
                data = resp.json()
                if "data" in data:
                    processed = []
                    for r in data["data"][:max_results]:
                        reviewer = r.get("reviewer", {})
                        processed.append({
                            "review_id": f"fb_rev_{r.get('id', int(time.time()))}",
                            "author": reviewer.get("name", "Facebook User"),
                            "author_handle": f"@{reviewer.get('name', 'user').lower().replace(' ', '_')}",
                            "author_avatar": f"https://graph.facebook.com/{reviewer.get('id', 'user')}/picture?type=normal",
                            "rating": int(r.get("rating", 5) if r.get("has_rating") else 4),
                            "original_text": r.get("review_text", ""),
                            "content": r.get("review_text", ""),
                            "language": "en",
                            "timestamp": r.get("created_time") or datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "source": "facebook",
                            "platform": "facebook",
                            "replied": False,
                            "reply_text": None,
                            "reply_timestamp": None,
                            "url": f"https://www.facebook.com/{active_page_id}"
                        })
                    return processed
            except Exception as e:
                logger.error(f"Error fetching Facebook ratings: {e}. Falling back to mock data.")

        return self._get_mock_reviews(active_page_id or "shop_page", brand_name, max_results)

    def _get_mock_reviews(self, page_id: str, brand_name: str, count: int = 10) -> List[Dict[str, Any]]:
        now = datetime.datetime.now(datetime.timezone.utc)
        sample_pool = [
            {
                "author": "Naveen Chandran",
                "author_handle": "@naveen_c_official",
                "rating": 5,
                "text": "Highly recommend this shop for festival sweet boxes and warm savories. On-time delivery every time!",
                "days_ago": 1,
                "replied": True,
                "reply": "Thank you Naveen for trusting us with your family festival celebrations!"
            },
            {
                "author": "Meera Krishnan",
                "author_handle": "@meera_k_bakes",
                "rating": 4,
                "text": "Ordered custom photo cake for our anniversary. Design was stunning and sponge was super moist.",
                "days_ago": 3,
                "replied": False,
                "reply": None
            },
            {
                "author": "Rohan Deshmukh",
                "author_handle": "@rohan_desh",
                "rating": 2,
                "text": "Packaging box was slightly torn when received via delivery partner today. Good food, but check parcel handling.",
                "days_ago": 5,
                "replied": False,
                "reply": None
            },
            {
                "author": "Swetha Ram",
                "author_handle": "@swetha_ram",
                "rating": 5,
                "text": "Best evening tea spot! Samosa and chai combo is 10/10.",
                "days_ago": 6,
                "replied": False,
                "reply": None
            }
        ]

        results = []
        for idx, item in enumerate(sample_pool[:count]):
            rev_time = (now - datetime.timedelta(days=item["days_ago"], hours=idx * 3)).isoformat()
            results.append({
                "review_id": f"fb_mock_rev_{page_id[:6]}_{idx}",
                "author": item["author"],
                "author_handle": item["author_handle"],
                "author_avatar": f"https://api.dicebear.com/7.x/bottts/svg?seed={item['author_handle']}",
                "rating": item["rating"],
                "original_text": item["text"],
                "content": item["text"],
                "language": "en",
                "timestamp": rev_time,
                "created_at": rev_time,
                "source": "facebook",
                "platform": "facebook",
                "replied": item["replied"],
                "reply_text": item["reply"],
                "reply_timestamp": (now - datetime.timedelta(days=item["days_ago"] - 1)).isoformat() if item["replied"] else None,
                "url": "https://facebook.com",
                "is_simulated": True
            })
        return results

facebook_client = FacebookClient()
