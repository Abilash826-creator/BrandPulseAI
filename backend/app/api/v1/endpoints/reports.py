import os
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.core.storage import get_storage
from app.core.database import get_db, clean_doc, clean_docs
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user, get_user_brand_ids
from app.schemas.all_schemas import ReportRequest
from app.services.ai_engine import ai_engine
from app.services.report_generator import report_generator
from app.core.security import decode_access_token

router = APIRouter()

@router.post("/generate")
async def generate_report(
    req: ReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generates an executive PDF report, CSV data export, or JSON dataset for a user-owned brand.
    """
    brand = await get_brand_for_user(req.brand_id, current_user)
    brand_name = brand["name"]
    db = get_db()

    mentions_query = {"brand_id": req.brand_id}
    if not req.include_simulated:
        mentions_query["is_simulated"] = {"$ne": True}

    mentions = await db["mentions"].find(mentions_query).sort("timestamp", -1).to_list(500)
    
    total = len(mentions)
    pos = sum(1 for m in mentions if m.get("sentiment") == "positive")
    neg = sum(1 for m in mentions if m.get("sentiment") == "negative")
    neu = sum(1 for m in mentions if m.get("sentiment") == "neutral")
    nss = round(((pos - neg) / max(total, 1)) * 100, 1)

    kpi_data = {
        "total_mentions": total,
        "net_sentiment_score": nss,
        "positive_count": pos,
        "neutral_count": neu,
        "negative_count": neg,
        "crisis_risk_index": 18.5,
        "share_of_voice": 38.2,
        "estimated_reach": sum(m.get("reach", 0) for m in mentions)
    }

    clusters = ai_engine.extract_topics_and_clusters(mentions, n_clusters=4)
    alerts = await db["alerts"].find({"brand_id": req.brand_id}).to_list(10)
    
    insights = ai_engine.generate_executive_insights(
        brand_name=brand_name,
        nss=nss,
        top_clusters=clusters,
        dominant_emotion="Joy",
        complaint_rate=round((neg / max(total, 1)) * 100, 1),
        crisis_active=False
    )

    filename = ""
    file_type = req.format.lower()
    
    if file_type == "pdf":
        filename = await run_in_threadpool(
            report_generator.generate_pdf_report,
            brand_name=brand_name,
            kpi_data=kpi_data,
            clusters=clusters,
            alerts=alerts,
            executive_insights=insights,
            time_range=req.time_range
        )
    elif file_type == "csv":
        filename = await run_in_threadpool(
            report_generator.generate_csv_export,
            brand_name=brand_name,
            mentions=mentions
        )
    else: # json
        export_payload = {
            "brand": brand_name,
            "report_type": req.report_type,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "kpis": kpi_data,
            "topic_clusters": clusters,
            "executive_insights": insights,
            "mentions_sample": mentions[:50]
        }
        filename = await run_in_threadpool(
            report_generator.generate_json_export,
            brand_name=brand_name,
            data=export_payload
        )

    report_record = {
        "id": f"rep_{uuid.uuid4().hex[:8]}",
        "brand_id": req.brand_id,
        "brand_name": brand_name,
        "owner_id": current_user["id"],
        "report_type": req.report_type,
        "format": file_type,
        "time_range": req.time_range,
        "filename": filename,
        "download_url": get_storage().get_url(filename),
        "is_simulated": any(m.get("is_simulated", False) for m in mentions) if mentions else False,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "created_by": current_user.get("full_name", "User")
    }

    await db["reports"].insert_one(report_record)
    return clean_doc(report_record)

@router.get("/history")
async def list_report_history(
    brand_id: Optional[str] = None,
    is_simulated: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns audit log of generated reports scoped to the user's brands.
    """
    db = get_db()
    query = {}
    if brand_id:
        await get_brand_for_user(brand_id, current_user)
        query["brand_id"] = brand_id
    else:
        user_brand_ids = await get_user_brand_ids(current_user)
        query["brand_id"] = {"$in": user_brand_ids}

    if is_simulated is not None:
        query["is_simulated"] = is_simulated

    cursor = db["reports"].find(query).sort("created_at", -1)
    reports = await cursor.to_list(50)
    return clean_docs(reports)

@router.get("/download/{filename}")
async def download_report_file(
    filename: str,
    request: Request,
    token: Optional[str] = Query(None)
):
    """
    Authenticated direct file download endpoint for PDF, CSV, and JSON reports.
    Verifies that the report exists and belongs to a brand owned by the authenticated user.
    """
    # Authenticate via Authorization header, ?token= query parameter, or query string
    auth_header = request.headers.get("authorization", "")
    auth_token = token or request.query_params.get("token")
    if auth_header.startswith("Bearer "):
        auth_token = auth_header.split(" ", 1)[1]

    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required to download reports")

    payload = decode_access_token(auth_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")

    db = get_db()
    user_id = payload.get("sub")
    current_user = await db["users"].find_one({"$or": [{"id": user_id}, {"_id": user_id}]})
    if not current_user or not current_user.get("is_active", False):
        raise HTTPException(status_code=401, detail="User not found or account deactivated")

    safe_filename = os.path.basename(filename)
    
    # Verify report in MongoDB
    report = await db["reports"].find_one({"filename": safe_filename})
    if not report:
        raise HTTPException(status_code=404, detail="Requested report not found")

    # Verify report belongs to user's brand
    await get_brand_for_user(report.get("brand_id", ""), current_user)

    storage = get_storage()
    if not storage.exists(safe_filename):
        raise HTTPException(status_code=404, detail="Requested report file not found on disk")

    media_type = "application/pdf"
    if safe_filename.endswith(".csv"):
        media_type = "text/csv"
    elif safe_filename.endswith(".json"):
        media_type = "application/json"

    file_path = storage.get_file_path(safe_filename)
    if file_path:
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=safe_filename,
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
        )

    file_bytes = storage.get_bytes(safe_filename)
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )
