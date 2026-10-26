"""
Official Meta / Instagram Graph API Integration Client for BrandPulse AI.
Strictly compliant with official Meta Graph API v19.0+ endpoints, OAuth 2.0 flow, and permissions.
Includes rich development mock mode when INSTAGRAM_MOCK_MODE=true.
"""

import os
import re
import json
import uuid
import random
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
import requests

from app.core.config import settings

logger = logging.getLogger("brandpulse.instagram")

class InstagramAPIError(Exception):
    """Custom exception for official Meta/Instagram Graph API errors."""
    def __init__(self, message: str, code: Optional[int] = None, subcode: Optional[int] = None, raw_error: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.subcode = subcode
        self.raw_error = raw_error or {}

class InstagramClient:
    def __init__(self):
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        self.graph_version = settings.INSTAGRAM_GRAPH_VERSION
        self.base_url = f"https://graph.facebook.com/{self.graph_version}"
        self.oauth_dialog_url = f"https://www.facebook.com/{self.graph_version}/dialog/oauth"
        
        # Official Meta Graph Scopes for Instagram Professional / Business Accounts
        self.scopes = [
            "instagram_basic",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_posts",
            "instagram_manage_comments",
            "instagram_manage_insights",
            "public_profile"
        ]

    @property
    def is_mock_mode(self) -> bool:
        """Determines whether to use Mock Mode or Live Graph API."""
        return settings.INSTAGRAM_MOCK_MODE or not bool(self.app_id and self.app_secret)

    def get_authorization_url(self, brand_id: str, state: Optional[str] = None) -> str:
        """
        Builds the official OAuth 2.0 authorization URL for Meta Login for Business.
        """
        if self.is_mock_mode:
            state_param = state or f"mock_state_{brand_id}_{uuid.uuid4().hex[:6]}"
            return f"{self.redirect_uri}?mock_auth=success&brand_id={brand_id}&code=mock_meta_auth_code_{uuid.uuid4().hex[:12]}&state={state_param}"

        scope_str = ",".join(self.scopes)
        state_payload = state or f"bp_{brand_id}_{uuid.uuid4().hex[:8]}"
        
        auth_url = (
            f"{self.oauth_dialog_url}?"
            f"client_id={self.app_id}&"
            f"redirect_uri={requests.utils.quote(self.redirect_uri)}&"
            f"scope={requests.utils.quote(scope_str)}&"
            f"response_type=code&"
            f"state={requests.utils.quote(state_payload)}"
        )
        return auth_url

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchanges the authorization code from Meta OAuth redirect for a short-lived user access token.
        """
        if self.is_mock_mode or code.startswith("mock_"):
            return {
                "access_token": f"EAAB_mock_user_token_{uuid.uuid4().hex}",
                "token_type": "bearer",
                "expires_in": 5184000,
                "is_mock": True
            }

        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise InstagramAPIError(
                    message=err.get("message", "OAuth token exchange failed"),
                    code=err.get("code"),
                    subcode=err.get("error_subcode"),
                    raw_error=err
                )
            return data
        except requests.RequestException as e:
            logger.error(f"[Instagram OAuth] Token exchange network error: {e}")
            raise InstagramAPIError(f"Network error connecting to Meta Graph API: {str(e)}")

    def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """
        Exchanges a short-lived user token for a 60-day long-lived access token.
        """
        if self.is_mock_mode or "mock" in short_lived_token:
            return {
                "access_token": f"EAAB_mock_long_lived_{uuid.uuid4().hex}",
                "token_type": "bearer",
                "expires_in": 5184000
            }

        url = f"{self.base_url}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise InstagramAPIError(
                    message=err.get("message", "Failed to retrieve long-lived token"),
                    code=err.get("code"),
                    subcode=err.get("error_subcode"),
                    raw_error=err
                )
            return data
        except requests.RequestException as e:
            logger.error(f"[Instagram OAuth] Long-lived token error: {e}")
            raise InstagramAPIError(f"Network error getting long-lived token: {str(e)}")

    def get_instagram_accounts(self, user_access_token: str) -> List[Dict[str, Any]]:
        """
        Queries /me/accounts to find Facebook Pages and their connected Instagram Business Accounts.
        """
        if self.is_mock_mode or "mock" in user_access_token:
            return [
                {
                    "page_id": "104928374910293",
                    "page_name": "BrandPulse Official HQ",
                    "page_access_token": f"EAAB_mock_page_{uuid.uuid4().hex[:10]}",
                    "instagram_business_account": {
                        "id": "17841405928374192",
                        "username": "brandpulse_hq",
                        "name": "BrandPulse AI Official",
                        "profile_picture_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150",
                        "followers_count": 84200,
                        "biography": "AI-Powered Social Listening, Fine-Grained Sentiment & Brand Intelligence."
                    }
                }
            ]

        url = f"{self.base_url}/me/accounts"
        params = {
            "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url,followers_count,biography}",
            "access_token": user_access_token
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise InstagramAPIError(
                    message=err.get("message", "Failed to fetch Facebook Pages / Instagram Accounts"),
                    code=err.get("code"),
                    subcode=err.get("error_subcode"),
                    raw_error=err
                )
            
            pages_list = []
            for item in data.get("data", []):
                if "instagram_business_account" in item:
                    pages_list.append({
                        "page_id": item["id"],
                        "page_name": item.get("name", "Facebook Page"),
                        "page_access_token": item.get("access_token", ""),
                        "instagram_business_account": item["instagram_business_account"]
                    })
            return pages_list
        except requests.RequestException as e:
            logger.error(f"[Instagram Accounts] API request error: {e}")
            raise InstagramAPIError(f"Network error fetching Instagram accounts: {str(e)}")

    def fetch_account_media(
        self,
        ig_user_id: str,
        access_token: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetches published media (Images, Videos, Reels, Carousels) from the Instagram Business Account.
        """
        if self.is_mock_mode or "mock" in access_token:
            return self._generate_mock_media(ig_user_id)

        url = f"{self.base_url}/{ig_user_id}/media"
        params = {
            "fields": "id,caption,media_type,media_product_type,media_url,permalink,thumbnail_url,timestamp,username,like_count,comments_count,children{media_url,media_type}",
            "limit": limit,
            "access_token": access_token
        }

        try:
            resp = requests.get(url, params=params, timeout=12)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise InstagramAPIError(
                    message=err.get("message", "Failed to fetch Instagram Media"),
                    code=err.get("code"),
                    raw_error=err
                )
            return data.get("data", [])
        except requests.RequestException as e:
            logger.error(f"[Instagram Media] Network error: {e}")
            raise InstagramAPIError(f"Network error fetching media: {str(e)}")

    def fetch_media_comments(
        self,
        media_id: str,
        access_token: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetches public comments on a specific Instagram media post.
        """
        if self.is_mock_mode or "mock" in access_token:
            return self._generate_mock_comments(media_id)

        url = f"{self.base_url}/{media_id}/comments"
        params = {
            "fields": "id,text,timestamp,username,like_count,from{id,username}",
            "limit": limit,
            "access_token": access_token
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise InstagramAPIError(
                    message=err.get("message", f"Failed to fetch comments for media {media_id}"),
                    code=err.get("code"),
                    raw_error=err
                )
            return data.get("data", [])
        except requests.RequestException as e:
            logger.error(f"[Instagram Comments] Network error: {e}")
            return []

    def fetch_tagged_and_mentioned(
        self,
        ig_user_id: str,
        access_token: str
    ) -> List[Dict[str, Any]]:
        """
        Fetches media where the business is @mentioned or tagged.
        """
        if self.is_mock_mode or "mock" in access_token:
            return self._generate_mock_tagged_media(ig_user_id)

        url = f"{self.base_url}/{ig_user_id}/tags"
        params = {
            "fields": "id,caption,media_type,media_product_type,media_url,permalink,timestamp,username,like_count,comments_count",
            "access_token": access_token
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "error" in data:
                return []
            return data.get("data", [])
        except Exception:
            return []

    def search_hashtag_media(
        self,
        ig_user_id: str,
        hashtag: str,
        access_token: str,
        limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Searches recent top public media for a given hashtag via Instagram Graph API.
        """
        clean_tag = hashtag.strip().lstrip("#")
        if not clean_tag:
            return []

        if self.is_mock_mode or "mock" in access_token:
            return self._generate_mock_hashtag_media(clean_tag)

        # 1. Search Hashtag ID
        search_url = f"{self.base_url}/ig_hashtag_search"
        search_params = {
            "user_id": ig_user_id,
            "q": clean_tag,
            "access_token": access_token
        }

        try:
            search_resp = requests.get(search_url, params=search_params, timeout=10)
            search_data = search_resp.json()
            if "error" in search_data or not search_data.get("data"):
                return []
            
            hashtag_id = search_data["data"][0]["id"]

            # 2. Fetch Recent Media for Hashtag
            recent_url = f"{self.base_url}/{hashtag_id}/recent_media"
            recent_params = {
                "user_id": ig_user_id,
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": limit,
                "access_token": access_token
            }
            recent_resp = requests.get(recent_url, params=recent_params, timeout=12)
            recent_data = recent_resp.json()
            return recent_data.get("data", [])
        except Exception as e:
            logger.warning(f"[Instagram Hashtag Search] Error searching #{clean_tag}: {e}")
            return []

    # =========================================================================
    # REALISTIC MOCK DATA GENERATOR
    # Supports Apple, Smartphones, TechNova AI, and Fruit/Tech Disambiguation
    # =========================================================================

    def _generate_mock_media(self, ig_user_id: str) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        
        mock_posts = [
            {
                "id": f"ig_media_101_{uuid.uuid4().hex[:6]}",
                "caption": "Apple released a new iPhone and the battery is amazing. Tested for 48 hours nonstop! 🔋✨ #Apple #iPhone16 #battery #techreview",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "media_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "permalink": "https://www.instagram.com/reel/C8apple101/",
                "timestamp": (now - datetime.timedelta(hours=2)).isoformat(),
                "username": "tech_insider_daily",
                "like_count": 14200,
                "comments_count": 890,
                "mock_transcript": "Apple released the new iPhone 16 and the battery is amazing. I have been running camera tests, 4K rendering and gaming for two straight days without needing a single charge.",
                "media_accessible": True
            },
            {
                "id": f"ig_media_102_{uuid.uuid4().hex[:6]}",
                "caption": "The camera zoom on the iPhone 16 Pro Max is unbelievable. Incredible low-light sensor and cinematic color grading. 📸🔥 #iPhone16Pro #camera #photography #Apple",
                "media_type": "IMAGE",
                "media_product_type": "FEED",
                "media_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600",
                "permalink": "https://www.instagram.com/p/C8apple102/",
                "timestamp": (now - datetime.timedelta(hours=6)).isoformat(),
                "username": "gadget_review_hub",
                "like_count": 8750,
                "comments_count": 420,
                "mock_transcript": None,
                "media_accessible": True
            },
            {
                "id": f"ig_media_103_{uuid.uuid4().hex[:6]}",
                "caption": "Wow, what a battery life! It died in 2 hours. Completely unacceptable for a flagship device charging $1200. 😡 #iPhone #battery #disappointed",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "media_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "permalink": "https://www.instagram.com/reel/C8apple103/",
                "timestamp": (now - datetime.timedelta(hours=14)).isoformat(),
                "username": "angry_consumer_watch",
                "like_count": 23400,
                "comments_count": 2100,
                "mock_transcript": "Wow, what a battery life! It died in two hours. I unplugged at 100 percent and just by running navigation the phone got blazing hot and died before noon.",
                "media_accessible": True
            },
            {
                "id": f"ig_media_104_{uuid.uuid4().hex[:6]}",
                "caption": "I had an apple for breakfast with some Greek yogurt and cinnamon. Feeling refreshed and ready for a healthy morning workout! 🍏🥣 #healthyeating #breakfast #apple #nutrition",
                "media_type": "IMAGE",
                "media_product_type": "FEED",
                "media_url": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600",
                "permalink": "https://www.instagram.com/p/C8apple104/",
                "timestamp": (now - datetime.timedelta(hours=18)).isoformat(),
                "username": "fit_healthy_lifestyle",
                "like_count": 3100,
                "comments_count": 85,
                "mock_transcript": None,
                "media_accessible": True
            },
            {
                "id": f"ig_media_105_{uuid.uuid4().hex[:6]}",
                "caption": "Comparing the new AirPods Pro 2 active noise cancellation vs Sony WF-1000XM5. The transparency mode on Apple AirPods is unmatched! 🎧🚀 #AirPods #Apple #Sony #audio",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "media_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
                "permalink": "https://www.instagram.com/reel/C8apple105/",
                "timestamp": (now - datetime.timedelta(days=1)).isoformat(),
                "username": "audiophile_lounge",
                "like_count": 16900,
                "comments_count": 780,
                "mock_transcript": "Testing the AirPods Pro noise cancellation on a noisy subway train. The spatial audio and voice isolation are noticeably sharper than previous models.",
                "media_accessible": True
            },
            {
                "id": f"ig_media_106_{uuid.uuid4().hex[:6]}",
                "caption": "Samsung Galaxy S24 Ultra display brightness outdoors is crazy good. Beats iPhone in direct sunlight display tests. ☀️📱 #Samsung #GalaxyS24 #display #competitor",
                "media_type": "IMAGE",
                "media_product_type": "FEED",
                "media_url": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?w=600",
                "permalink": "https://www.instagram.com/p/C8apple106/",
                "timestamp": (now - datetime.timedelta(days=2)).isoformat(),
                "username": "smartphone_wars",
                "like_count": 9200,
                "comments_count": 640,
                "mock_transcript": None,
                "media_accessible": True
            },
            {
                "id": f"ig_media_107_{uuid.uuid4().hex[:6]}",
                "caption": "BrandPulse AI real-time social listening intelligence suite just launched. Automated sentiment tracking across all brand channels! 🚀📊 #BrandPulse #SocialListening #AI",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "media_url": "", # Media restricted / unavailable test case
                "permalink": "https://www.instagram.com/reel/C8apple107/",
                "timestamp": (now - datetime.timedelta(days=3)).isoformat(),
                "username": "technova_official",
                "like_count": 4500,
                "comments_count": 210,
                "mock_transcript": None,
                "media_accessible": False
            }
        ]
        return mock_posts

    def _generate_mock_comments(self, media_id: str) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        comments_pool = [
            {
                "id": f"comm_1_{uuid.uuid4().hex[:6]}",
                "text": "The battery drained within 2 hours while gaming. Need an update ASAP!",
                "timestamp": (now - datetime.timedelta(minutes=45)).isoformat(),
                "username": "mobile_gamer_99",
                "like_count": 84
            },
            {
                "id": f"comm_2_{uuid.uuid4().hex[:6]}",
                "text": "I was hesitant at first, but the performance and camera quality on the new model are genuinely the best ever.",
                "timestamp": (now - datetime.timedelta(hours=1)).isoformat(),
                "username": "sarah_photovault",
                "like_count": 142
            },
            {
                "id": f"comm_3_{uuid.uuid4().hex[:6]}",
                "text": "Charging speed is still only 25W. Why haven't they upgraded fast charging yet?",
                "timestamp": (now - datetime.timedelta(hours=3)).isoformat(),
                "username": "speedy_charge_fan",
                "like_count": 56
            },
            {
                "id": f"comm_4_{uuid.uuid4().hex[:6]}",
                "text": "Customer service at the store replaced my damaged screen in under 30 minutes. Super satisfied with AppleCare!",
                "timestamp": (now - datetime.timedelta(hours=5)).isoformat(),
                "username": "marcus_enterprise",
                "like_count": 31
            }
        ]
        return comments_pool

    def _generate_mock_tagged_media(self, ig_user_id: str) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        return [
            {
                "id": f"ig_tagged_201_{uuid.uuid4().hex[:6]}",
                "caption": "Huge shoutout to @apple for the new iOS accessibility features! Game changing for creators.",
                "media_type": "IMAGE",
                "media_product_type": "FEED",
                "media_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=600",
                "permalink": "https://www.instagram.com/p/C8tagged201/",
                "timestamp": (now - datetime.timedelta(hours=10)).isoformat(),
                "username": "creative_tech_voice",
                "like_count": 5600,
                "comments_count": 180
            }
        ]

    def _generate_mock_hashtag_media(self, hashtag: str) -> List[Dict[str, Any]]:
        now = datetime.datetime.now()
        return [
            {
                "id": f"ig_hash_301_{uuid.uuid4().hex[:6]}",
                "caption": f"Hands-on review with #{hashtag}. The build quality and display resolution exceeded expectations! 🔥",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "media_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "permalink": f"https://www.instagram.com/reel/C8hash_{hashtag[:6]}/",
                "timestamp": (now - datetime.timedelta(hours=12)).isoformat(),
                "username": "daily_hardware_pulse",
                "like_count": 7800,
                "comments_count": 390,
                "mock_transcript": f"Testing the latest hardware tagged with {hashtag}. The titanium finish feels premium and light in hand.",
                "media_accessible": True
            }
        ]

instagram_client = InstagramClient()
