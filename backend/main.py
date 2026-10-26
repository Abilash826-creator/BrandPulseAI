import os
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import db_manager, get_db
from app.core.security import get_password_hash
from app.api.v1.router import api_router
from app.services.scraper_simulator import scraper_simulator

import uuid
from starlette.requests import Request
from app.core.logging import setup_logging, logger, set_request_id

# Configure structured logging with request IDs
setup_logging()

# Optional Sentry Error Monitoring & Telemetry
sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        )
        logger.info(f"[{settings.PROJECT_NAME}] Sentry telemetry initialized successfully.")
    except Exception as e:
        logger.warning(f"[{settings.PROJECT_NAME}] Could not initialize Sentry: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect directly to MongoDB (Atlas or Local fallback) and initialize database
    logger.info(f"[{settings.PROJECT_NAME}] Initializing database and services...")
    success, msg = await db_manager.connect()
    if not success:
        logger.warning(f"[{settings.PROJECT_NAME}] WARNING: Could not connect to MongoDB at startup ({msg}).")
    else:
        logger.info(f"[{settings.PROJECT_NAME}] Startup ready: {msg}")

    yield
    # Shutdown
    logger.info(f"[{settings.PROJECT_NAME}] Shutting down database connections...")
    await db_manager.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade AI Social Listening, Fine-Grained Sentiment/Emotion Detection, Crisis Management, and Brand Intelligence Platform.",
    lifespan=lifespan
)

# Request ID Middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = req_id
    set_request_id(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

# Production Security Headers Middleware (OWASP recommended)
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# CORS configuration with explicit origins from CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.firewall import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount API router only once under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Database and Runtime Exception Handler
@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request, exc: RuntimeError):
    err_str = str(exc)
    if "MongoDB" in err_str or "database" in err_str.lower():
        return JSONResponse(
            status_code=503,
            content={
                "detail": f"Database connection unavailable: {err_str}",
                "suggestion": "Please verify MONGODB_URI on Render environment variables and whitelist IP 0.0.0.0/0 on MongoDB Atlas."
            }
        )
    return JSONResponse(
        status_code=500,
        content={"detail": err_str}
    )

# Universal Health Check Endpoints
@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"])
async def health_check():
    from app.services.ai_engine import ai_engine
    return {
        "status": "ok",
        "service": "BrandPulse AI API",
        "version": settings.VERSION,
        "database_connected": db_manager.is_mongodb_connected or (db_manager.db is not None),
        "model_statuses": ai_engine.get_model_statuses(),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "status": "ok",
        "service": "BrandPulse AI API",
        "message": f"Welcome to {settings.PROJECT_NAME} API. Visit /docs for OpenAPI interactive documentation.",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
        "api_v1_prefix": "/api/v1",
        "metrics_url": "/metrics"
    }

@app.get("/metrics", tags=["System"])
async def prometheus_metrics():
    """Prometheus-compatible telemetry & health metrics for Kubernetes/Grafana."""
    from fastapi.responses import PlainTextResponse
    from app.services.ai_engine import ai_engine
    from app.core.firewall import security_firewall
    
    db_status = 1 if (db_manager.is_mongodb_connected or db_manager.db is not None) else 0
    active_quarantines = len([ip for ip, rec in security_firewall.ip_rate_limits.items() if rec.get("quarantine_until", 0) > datetime.datetime.now().timestamp()])
    models = ai_engine.get_model_statuses()
    loaded_models = sum(1 for m in models.values() if m.get("loaded"))
    
    metrics_lines = [
        "# HELP brandpulse_db_connected Database connection health (1 = connected, 0 = disconnected)",
        "# TYPE brandpulse_db_connected gauge",
        f"brandpulse_db_connected {db_status}",
        "# HELP brandpulse_models_loaded Number of active NLP/ML models loaded in memory",
        "# TYPE brandpulse_models_loaded gauge",
        f"brandpulse_models_loaded {loaded_models}",
        "# HELP brandpulse_active_quarantines Number of IPs currently quarantined by firewall",
        "# TYPE brandpulse_active_quarantines gauge",
        f"brandpulse_active_quarantines {active_quarantines}",
        "# HELP brandpulse_firewall_inspections_total Total WAF payload inspections performed",
        "# TYPE brandpulse_firewall_inspections_total counter",
        f"brandpulse_firewall_inspections_total {security_firewall.stats.get('total_inspections', 0)}",
        "# HELP brandpulse_firewall_blocked_total Total requests blocked by firewall",
        "# TYPE brandpulse_firewall_blocked_total counter",
        f"brandpulse_firewall_blocked_total {security_firewall.stats.get('blocked_brute_force', 0) + security_firewall.stats.get('blocked_malicious_ua', 0)}"
    ]
    return PlainTextResponse("\n".join(metrics_lines) + "\n", media_type="text/plain; version=0.0.4")

@app.get("/reports/download/{filename}", include_in_schema=False)
async def root_download_report_alias(filename: str, request: Request, token: str = None):
    from app.api.v1.endpoints.reports import download_report_file
    return await download_report_file(filename=filename, request=request, token=token)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

