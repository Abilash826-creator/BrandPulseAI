import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(backend_dir, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

def _get_cors_origins() -> List[str]:
    defaults = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    # Check multiple possible frontend env variable keys
    for env_key in ["CORS_ORIGINS", "FRONTEND_URL", "VERCEL_URL"]:
        val = os.getenv(env_key, "").strip()
        if val:
            for origin in val.split(","):
                cleaned = origin.strip().strip("'\"").rstrip("/")
                if cleaned:
                    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
                        cleaned = f"https://{cleaned}"
                    if cleaned not in defaults:
                        defaults.append(cleaned)
    return defaults

raw_secret_key = os.getenv("SECRET_KEY")
if not raw_secret_key or len(raw_secret_key) < 32:
    raise RuntimeError("SECRET_KEY environment variable is required and must be at least 32 characters long.")

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=env_path if os.path.exists(env_path) else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "BrandPulse AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Security
    SECRET_KEY: str = raw_secret_key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    TRUSTED_PROXIES: List[str] = ["127.0.0.1", "::1"]
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # Database (supports both MONGODB_URI and MONGO_URI, DATABASE_NAME and MONGODB_DATABASE)
    MONGODB_URI: str = os.getenv("MONGODB_URI", os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", os.getenv("MONGODB_DATABASE", "brandpulse_ai"))
    
    # Rate Limiting & Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = _get_cors_origins()
    
    # Storage
    STORAGE_BACKEND: str = os.getenv("STORAGE_BACKEND", "local")  # "local" or "s3"
    REPORTS_DIR: str = os.path.join(backend_dir, "storage", "reports")
    DATA_DIR: str = os.path.join(backend_dir, "storage", "data")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_ENDPOINT_URL: str = os.getenv("AWS_ENDPOINT_URL", "")
    
    # Crisis Detector Defaults
    CRISIS_NEGATIVE_THRESHOLD: float = float(os.getenv("CRISIS_NEGATIVE_THRESHOLD", 0.35))
    CRISIS_VOLUME_MULTIPLIER: float = float(os.getenv("CRISIS_VOLUME_MULTIPLIER", 2.0))
    
    # AI Engine & Multilingual Analysis Config
    DEFAULT_BRAND_NAME: str = "Brand Workspace"
    ENABLE_MULTILINGUAL_MODEL: bool = os.getenv("ENABLE_MULTILINGUAL_MODEL", "false").lower() in ("true", "1", "yes")
    MULTILINGUAL_MODEL_NAME: str = os.getenv("MULTILINGUAL_MODEL_NAME", "xlm-roberta-base")
    ANALYSIS_BACKEND: str = os.getenv("ANALYSIS_BACKEND", "local")  # "local" or "llm"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # "gemini", "openai", "groq", or "mock"
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    MONTHLY_LLM_COST_CAP: float = float(os.getenv("MONTHLY_LLM_COST_CAP", 10.0))
    ASSISTANT_MONTHLY_TOKEN_BUDGET: int = int(os.getenv("ASSISTANT_MONTHLY_TOKEN_BUDGET", 50000))


    # Instagram / Meta Graph API Config
    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", "")
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", "")
    INSTAGRAM_REDIRECT_URI: str = os.getenv("INSTAGRAM_REDIRECT_URI", "http://localhost:5173/brand-settings")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_GRAPH_VERSION: str = os.getenv("INSTAGRAM_GRAPH_VERSION", "v19.0")
    INSTAGRAM_MOCK_MODE: bool = os.getenv("INSTAGRAM_MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Google Places / Business Profile API
    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", os.getenv("GOOGLE_MAPS_API_KEY", ""))
    GOOGLE_BUSINESS_MOCK_MODE: bool = os.getenv("GOOGLE_BUSINESS_MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Facebook Page Graph API
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
    FACEBOOK_MOCK_MODE: bool = os.getenv("FACEBOOK_MOCK_MODE", "false").lower() in ("true", "1", "yes")

    # Notification Providers (Email via Resend/SMTP, WhatsApp/SMS via Twilio, with Mock fallback)
    NOTIFICATION_PROVIDER: str = os.getenv("NOTIFICATION_PROVIDER", "resend")
    NOTIFICATION_MOCK_MODE: bool = os.getenv("NOTIFICATION_MOCK_MODE", "false").lower() in ("true", "1", "yes")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "alerts@brandpulse.ai")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_PHONE: str = os.getenv("TWILIO_FROM_PHONE", "")
    TWILIO_WHATSAPP_FROM: str = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

    # Plans and Limits (Free = 1 business, 100 reviews/mo, 20 AI chat/mo)
    PLAN_FREE_MAX_BUSINESSES: int = int(os.getenv("PLAN_FREE_MAX_BUSINESSES", 1))
    PLAN_FREE_MAX_REVIEWS_PER_MONTH: int = int(os.getenv("PLAN_FREE_MAX_REVIEWS_PER_MONTH", 100))
    PLAN_FREE_MAX_AI_CHAT_PER_MONTH: int = int(os.getenv("PLAN_FREE_MAX_AI_CHAT_PER_MONTH", 20))
    PLAN_PRO_MAX_BUSINESSES: int = int(os.getenv("PLAN_PRO_MAX_BUSINESSES", 10))
    PLAN_PRO_MAX_REVIEWS_PER_MONTH: int = int(os.getenv("PLAN_PRO_MAX_REVIEWS_PER_MONTH", 5000))
    # Razorpay Payment & Subscription Gateway
    RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    # Meta WhatsApp Business Cloud API (Direct Meta Cloud)
    WHATSAPP_CLOUD_ACCESS_TOKEN: str = os.getenv("WHATSAPP_CLOUD_ACCESS_TOKEN", "")
    WHATSAPP_CLOUD_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_CLOUD_PHONE_NUMBER_ID", "")
    WHATSAPP_CLOUD_TEMPLATE_NAME: str = os.getenv("WHATSAPP_CLOUD_TEMPLATE_NAME", "crisis_alert_v1")

settings = Settings()

os.makedirs(settings.REPORTS_DIR, exist_ok=True)
os.makedirs(settings.DATA_DIR, exist_ok=True)


