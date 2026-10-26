from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import datetime

# User Schemas
class UserBase(BaseModel):
    email: str
    full_name: str
    organization: Optional[str] = "Organization"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: str
    role: str = "owner"
    is_active: bool = True
    created_at: str
    brand_ids: List[str] = []
    photo_url: Optional[str] = None

class FirebaseUserAuth(BaseModel):
    id_token: str
    organization: Optional[str] = "Enterprise"

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    refresh_token: Optional[str] = None

# Location Schemas for Business Branches
class Location(BaseModel):
    id: str
    name: str # e.g. "Main Branch", "T. Nagar", "Indiranagar"
    address: Optional[str] = ""
    city: Optional[str] = ""
    phone: Optional[str] = ""
    google_place_id: Optional[str] = ""
    is_primary: bool = False

class LocationCreate(BaseModel):
    name: str
    address: Optional[str] = ""
    city: Optional[str] = ""
    phone: Optional[str] = ""
    google_place_id: Optional[str] = ""
    is_primary: bool = False

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    google_place_id: Optional[str] = None
    is_primary: Optional[bool] = None

# Business / Brand Schemas (Local Shop & Multi-location focus)
class BrandBase(BaseModel):
    name: str
    business_type: str = "retail" # restaurant, bakery, retail, salon, clinic, supermarket, electronics, other
    type: Optional[str] = None # Alias for business_type
    address: Optional[str] = ""
    city: Optional[str] = ""
    phone: Optional[str] = ""
    languages: List[str] = ["en"] # en, ta, hi, tanglish, hinglish
    google_maps_url: Optional[str] = ""
    google_place_id: Optional[str] = ""
    place_id: Optional[str] = "" # Alias for google_place_id
    instagram_handle: Optional[str] = ""
    industry: str = "Local Business"
    description: Optional[str] = ""
    locations: List[Location] = []
    topics: List[str] = [] # e.g. food quality, taste, staff behavior, waiting time, price/value, cleanliness, ambience, parking, delivery, packaging
    products: List[str] = []
    keywords: List[str] = []
    hashtags: List[str] = []
    social_handles: Dict[str, str] = {}
    competitors: List[str] = []
    crisis_threshold_negative: float = 0.35
    is_primary: bool = False

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    business_type: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    languages: Optional[List[str]] = None
    google_maps_url: Optional[str] = None
    google_place_id: Optional[str] = None
    place_id: Optional[str] = None
    instagram_handle: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    locations: Optional[List[Location]] = None
    topics: Optional[List[str]] = None
    products: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    social_handles: Optional[Dict[str, str]] = None
    competitors: Optional[List[str]] = None
    crisis_threshold_negative: Optional[float] = None
    is_primary: Optional[bool] = None

class BrandResponse(BrandBase):
    id: str
    owner_id: str
    created_at: str
    mentions_count: int = 0
    sentiment_score: float = 0.0

# Backward-compatible and semantic aliases
BusinessBase = BrandBase
BusinessCreate = BrandCreate
BusinessUpdate = BrandUpdate
BusinessResponse = BrandResponse

# Mention Schemas (Small Business Customer Reviews & Social Listening)
class MentionCreate(BaseModel):
    brand_id: Optional[str] = None
    business_id: Optional[str] = None
    location_id: Optional[str] = None
    source: Optional[str] = "google" # google, instagram, facebook, whatsapp, justdial, zomato, manual, csv
    platform: Optional[str] = None # Backward compatibility alias for source
    author: str = "Customer"
    author_handle: Optional[str] = "@customer"
    author_followers: int = 0
    content: Optional[str] = None
    original_text: Optional[str] = None # Native review text
    translated_text: Optional[str] = None # English translation for non-English reviews
    rating: Optional[int] = None # 1 to 5 star rating
    sentiment: Optional[str] = "neutral" # positive, negative, neutral
    sentiment_score: Optional[float] = 0.0
    topics: List[str] = []
    url: Optional[str] = ""
    timestamp: Optional[str] = None
    created_at: Optional[str] = None
    media_type: Optional[str] = "REVIEW" # REVIEW, POST, COMMENT, IMAGE, VIDEO
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = []
    mentions: Optional[List[str]] = []
    transcript: Optional[str] = None
    language: Optional[str] = None
    is_simulated: Optional[bool] = False
    replied: Optional[bool] = False
    reply_text: Optional[str] = None
    reply_timestamp: Optional[str] = None

class ReviewReplyRequest(BaseModel):
    reply_text: str

class MentionFeedbackRequest(BaseModel):
    corrected_sentiment: Optional[str] = None
    corrected_topics: Optional[List[str]] = None
    notes: Optional[str] = None

class PasteReviewsRequest(BaseModel):
    text: str
    brand_id: Optional[str] = None
    business_id: Optional[str] = None
    source: Optional[str] = "manual"

class ProductAspect(BaseModel):
    aspect: str
    sentiment: str
    sentiment_score: Optional[float] = 0.0

class ContextMeta(BaseModel):
    sarcasm: bool = False
    negation: bool = False
    intent: str = "general"

class MentionResponse(BaseModel):
    id: str
    brand_id: str
    business_id: Optional[str] = None
    brand_name: Optional[str] = ""
    location_id: Optional[str] = None
    source: str = "google" # google, instagram, facebook, whatsapp, justdial, zomato, manual, csv
    platform: str = "google" # Backward compatibility alias
    author: str = "Customer"
    author_handle: str = "@customer"
    author_followers: int = 0
    author_avatar: Optional[str] = ""
    content: str = ""
    original_text: str = ""
    translated_text: Optional[str] = None
    rating: Optional[int] = None # 1 to 5 star rating
    caption: Optional[str] = ""
    hashtags: List[str] = []
    mentions: List[str] = []
    media_type: Optional[str] = "REVIEW"
    sentiment: str = "neutral" # positive, neutral, negative
    sentiment_score: float = 0.0
    topics: List[str] = []
    emotions: Dict[str, float] = {}
    dominant_emotion: str = "neutral"
    intent: str = "general"
    intent_confidence: float = 0.0
    reach: int = 0
    engagement_score: int = 0
    virality_score: float = 0.0
    topic_cluster: Optional[str] = "General"
    is_crisis_flag: bool = False
    is_simulated: bool = False
    language: Optional[str] = "en"
    sentiment_confidence: Optional[float] = 1.0
    replied: bool = False
    reply_text: Optional[str] = None
    reply_timestamp: Optional[str] = None
    timestamp: str
    created_at: Optional[str] = None
    url: Optional[str] = ""
    
    # Instagram & Fine-grained Intelligence fields
    brand_detected: Optional[bool] = True
    product_detected: Optional[str] = None
    detected_brands: Optional[List[str]] = []
    detected_products: Optional[List[str]] = []
    matched_keywords: Optional[List[str]] = []
    matched_hashtags: Optional[List[str]] = []
    relevance_score: Optional[float] = 0.85
    relevance_reason: Optional[str] = ""
    aspects: Optional[List[Dict[str, Any]]] = []
    context: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    media_analysis_available: Optional[bool] = False
    media_analysis_status: Optional[str] = "available"

# Instagram Integration Schemas
class InstagramAuthUrlResponse(BaseModel):
    auth_url: str
    is_mock: bool = False
    mock_mode: bool = False

class InstagramConnectionResponse(BaseModel):
    id: str
    brand_id: str
    user_id: str
    instagram_business_account_id: str
    instagram_username: str
    account_name: str
    profile_picture_url: Optional[str] = ""
    followers_count: Optional[int] = 0
    status: str # connected, disconnected, expired
    permissions: List[str] = []
    connected_at: str
    last_synced_at: Optional[str] = None
    is_mock: bool = False

class InstagramSyncResponse(BaseModel):
    status: str
    synced_items_count: int
    posts_count: int
    reels_count: int
    comments_count: int
    relevant_items_count: int
    brand_name: str
    sync_timestamp: str
    message: str

class InstagramMetricsResponse(BaseModel):
    total_instagram_mentions: int
    relevant_mentions_count: int
    relevance_rate_pct: float
    average_relevance_score: float
    sentiment_breakdown: Dict[str, int]
    sentiment_pcts: Dict[str, float]
    top_keywords: List[Dict[str, Any]]
    top_hashtags: List[Dict[str, Any]]
    top_discussed_products: List[Dict[str, Any]]
    top_aspect_complaints: List[Dict[str, Any]]
    top_aspect_praise: List[Dict[str, Any]]
    media_type_distribution: Dict[str, int]
    is_connected: bool
    account_username: Optional[str] = None
    last_synced_at: Optional[str] = None


# Crisis Alert Schemas
class AlertCreate(BaseModel):
    brand_id: str
    title: str
    severity: str # low, medium, critical
    metric_type: str # negative_spike, viral_complaint, volume_surge
    trigger_value: float
    threshold_value: float
    description: str
    ai_root_cause: str
    recommendations: List[str]

class AlertResponse(BaseModel):
    id: str
    brand_id: str
    brand_name: Optional[str] = ""
    title: str
    severity: str # low, medium, critical
    metric_type: str
    trigger_value: float
    threshold_value: float
    description: str
    ai_root_cause: str
    recommendations: List[str]
    status: str # active, acknowledged, resolved
    is_simulated: bool = False
    created_at: str
    resolved_at: Optional[str] = None
    acknowledged_by: Optional[str] = None

# Analytics Schemas
class AnalyticsOverview(BaseModel):
    total_mentions: int
    net_sentiment_score: float
    positive_count: int
    neutral_count: int
    negative_count: int
    crisis_risk_index: float
    share_of_voice: float
    estimated_reach: int
    total_engagement: int
    sentiment_trend_pct: float
    volume_trend_pct: float

# Topic Modeling Schema
class TopicCluster(BaseModel):
    cluster_id: int
    name: str
    top_keywords: List[str]
    mentions_count: int
    dominant_sentiment: str
    sentiment_breakdown: Dict[str, float]
    sample_text: str

# Report Schema
class ReportRequest(BaseModel):
    brand_id: str
    report_type: str = "executive_summary" # executive_summary, full_audit, crisis_postmortem
    time_range: str = "7d" # 24h, 7d, 30d
    format: str = "pdf" # pdf, csv, json
    include_simulated: bool = True

# Company Details Schema
class CompanyDetails(BaseModel):
    industry: str = "Technology & AI"
    description: Optional[str] = ""
    keywords: List[str] = []
    hashtags: List[str] = []
    social_handles: Dict[str, str] = {}
    competitors: List[str] = []
    website: Optional[str] = "https://brandpulse.ai"
    owner_organization: Optional[str] = "Enterprise Organization"

# Monitored Data Summary Schemas (Stored in MongoDB 'summaries' collection / 'Summary' entity)
class SummaryCreate(BaseModel):
    brand_id: str
    name_of_company: str
    product_service: str
    company_details: CompanyDetails
    date: str # e.g. "2026-08-25"
    time: str # e.g. "09:25:30"
    timestamp: Optional[str] = None
    cause_of_feedback: str
    precautions: List[str]
    measures_taken: List[str]
    total_mentions_analyzed: int = 0
    net_sentiment_score: float = 0.0
    sentiment_breakdown: Dict[str, Any] = {}
    dominant_emotions: List[Dict[str, Any]] = []
    status: str = "generated" # generated, in_progress, resolved

class SummaryUpdate(BaseModel):
    measures_taken: Optional[List[str]] = None
    precautions: Optional[List[str]] = None
    status: Optional[str] = None
    cause_of_feedback: Optional[str] = None

class SummaryResponse(BaseModel):
    id: str
    brand_id: str
    name_of_company: str
    product_service: str
    company_details: CompanyDetails
    date: str
    time: str
    timestamp: str
    cause_of_feedback: str
    precautions: List[str]
    measures_taken: List[str]
    total_mentions_analyzed: int
    net_sentiment_score: float
    sentiment_breakdown: Dict[str, Any]
    dominant_emotions: List[Dict[str, Any]]
    status: str
    is_simulated: bool = False
    created_at: str
    created_by: Optional[str] = "AI_Automated_Monitor"

# Authentication Audit Log Schema
class AuthLogResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: str
    status: str # AUTHENTICATED, SUCCESS, FAILED
    login_date: str
    login_time: str
    login_timestamp: str
    ip_address: str
    user_agent: str
    auth_method: str # credentials, demo_login, registration


class GoogleConnectRequest(BaseModel):
    brand_id: str
    place_id: Optional[str] = None
    google_maps_url: Optional[str] = None
    maps_url: Optional[str] = None
    location_name: Optional[str] = None


