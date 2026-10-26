from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
import datetime

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user
from app.integrations.facebook import facebook_client
from app.services.data_collection import data_collection_service
from app.schemas.all_schemas import ReviewReplyRequest

router = APIRouter()

@router.get("/status")
async def get_facebook_status(
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns connection status and metrics for Facebook Page.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()
    
    fb_handle = brand.get("social_handles", {}).get("facebook", "")
    is_connected = bool(fb_handle or facebook_client.page_id)
    
    total_reviews = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "source": "facebook"
    })
    
    unreplied = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "source": "facebook",
        "replied": {"$ne": True}
    })

    return {
        "is_connected": is_connected,
        "facebook_page": fb_handle,
        "total_synced_reviews": total_reviews,
        "unreplied_reviews": unreplied,
        "mock_mode": facebook_client.mock_mode
    }

@router.post("/sync")
async def sync_facebook_reviews(
    brand_id: str = Query(...),
    page_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Fetches and syncs Facebook Page reviews and comments.
    """
    await get_brand_for_user(brand_id, current_user)
    try:
        result = await data_collection_service.sync_facebook_data(brand_id, page_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync Facebook reviews: {str(e)}")

@router.post("/reviews/{mention_id}/reply")
async def reply_to_facebook_review(
    mention_id: str,
    body: ReviewReplyRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Post or record owner reply to a Facebook review / comment.
    """
    db = get_db()
    mention = await db["mentions"].find_one({"id": mention_id})
    if not mention:
        raise HTTPException(status_code=404, detail="Review not found.")

    await get_brand_for_user(mention["brand_id"], current_user)

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
        "reply_timestamp": now_iso
    }
