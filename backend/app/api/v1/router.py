from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    brands,
    monitoring,
    analytics,
    crisis,
    competitors,
    reports,
    system,
    ml_studio,
    social_media,
    dataset_ingestion,
    google_business,
    facebook,
    assistant,
    notifications,
    billing
)

api_router = APIRouter()

# Primary REST v1 Endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(brands.router, prefix="/brands", tags=["Brand Management"])
api_router.include_router(brands.router, prefix="/businesses", tags=["Business Management"], include_in_schema=False)
api_router.include_router(assistant.router, prefix="/assistant", tags=["AI Business Assistant"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Social Listening & Mentions"])
api_router.include_router(social_media.router, prefix="/instagram", tags=["Instagram & Meta Social Listening"])
api_router.include_router(google_business.router, prefix="/google", tags=["Google Business Profile"])
api_router.include_router(facebook.router, prefix="/facebook", tags=["Facebook Page Reviews"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Sentiment & Topic Analytics"])
api_router.include_router(crisis.router, prefix="/crisis", tags=["Crisis Management & Alerts"])
api_router.include_router(competitors.router, prefix="/competitors", tags=["Competitor Benchmarking"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Exports"])
api_router.include_router(system.router, prefix="/system", tags=["System & Database"])
api_router.include_router(ml_studio.router, prefix="/ml", tags=["Machine Learning & Datasets"])
api_router.include_router(dataset_ingestion.router, prefix="/dataset", tags=["Dataset Ingestion & PDF/CSV Feeder"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications & Alerts"])
api_router.include_router(billing.router, prefix="/billing", tags=["Plans & Quotas"])
