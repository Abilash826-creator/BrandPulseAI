from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import datetime

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user
from app.integrations.google_business import google_business_client
from app.services.data_collection import data_collection_service
from app.schemas.all_schemas import ReviewReplyRequest

router = APIRouter()

@router.get("/status")
async def get_google_status(
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns connection status and place details for Google Business Profile.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()
    
    place_id = brand.get("google_place_id") or brand.get("place_id")
    is_connected = bool(place_id or brand.get("google_maps_url"))
    
    total_reviews = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "source": "google"
    })
    
    unreplied_reviews = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "source": "google",
        "replied": {"$ne": True}
    })

    return {
        "is_connected": is_connected,
        "place_id": place_id,
        "google_maps_url": brand.get("google_maps_url", ""),
        "total_synced_reviews": total_reviews,
        "unreplied_reviews": unreplied_reviews,
        "mock_mode": google_business_client.mock_mode
    }

from app.schemas.all_schemas import ReviewReplyRequest, GoogleConnectRequest

@router.post("/connect")
async def connect_google_profile(
    body: GoogleConnectRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Connects or updates Google Business Profile / Maps details.
    """
    brand_id = body.brand_id
    await get_brand_for_user(brand_id, current_user)
    db = get_db()

    updates = {}
    resolved_place_id = body.place_id
    if resolved_place_id:
        updates["google_place_id"] = resolved_place_id
        updates["place_id"] = resolved_place_id
    resolved_maps_url = body.google_maps_url or body.maps_url
    if resolved_maps_url:
        updates["google_maps_url"] = resolved_maps_url
    if body.location_name:
        updates["location_name"] = body.location_name

    if not updates:
        raise HTTPException(status_code=400, detail="place_id or google_maps_url must be provided.")

    await db["brands"].update_one({"id": brand_id}, {"$set": updates})

    return {
        "status": "success",
        "success": True,
        "connected": True,
        "message": "Google Business Profile connected successfully.",
        "brand_id": brand_id
    }


@router.post("/sync")
async def sync_google_reviews(
    brand_id: str = Query(...),
    place_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches and syncs Google reviews for the business.
    """
    await get_brand_for_user(brand_id, current_user)
    try:
        result = await data_collection_service.sync_google_reviews(brand_id, place_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync Google reviews: {str(e)}")

@router.post("/reviews/{mention_id}/reply")
async def reply_to_google_review(
    mention_id: str,
    body: ReviewReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Post or record owner reply to a Google review.
    """
    db = get_db()
    mention = await db["mentions"].find_one({"id": mention_id})
    if not mention:
        raise HTTPException(status_code=404, detail="Review not found.")

    # Validate business ownership
    await get_brand_for_user(mention["brand_id"], current_user)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    client_res = google_business_client.post_reply(mention_id, body.reply_text)

    await db["mentions"].update_one(
        {"id": mention_id},
        {"$set": {
            "replied": True,
            "reply_text": body.reply_text,
            "reply_timestamp": now_iso
        }}
    )

    return {
        "status": "success",
        "message": "Reply recorded successfully.",
        "mention_id": mention_id,
        "reply_text": body.reply_text,
        "reply_timestamp": now_iso,
        "mode": client_res.get("mode", "mock")
    }
