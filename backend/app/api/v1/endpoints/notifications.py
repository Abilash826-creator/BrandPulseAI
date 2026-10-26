from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from app.core.database import get_db, clean_doc
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user
from app.services.notifications import notification_dispatcher, notification_provider

router = APIRouter()


class NotificationSettingsUpdate(BaseModel):
    notify_bad_reviews: Optional[bool] = None
    notify_weekly_summary: Optional[bool] = None
    notify_spike: Optional[bool] = None
    weekly_digest_day: Optional[str] = "Monday"
    weekly_digest_time: Optional[str] = "09:00"
    email_opt_in: Optional[bool] = True
    whatsapp_opt_in: Optional[bool] = False
    sms_opt_in: Optional[bool] = False
    notification_email: Optional[str] = None
    notification_phone: Optional[str] = None


class NotificationTestRequest(BaseModel):
    brand_id: str
    channel: str = "email" # "email", "whatsapp", or "sms"
    recipient: Optional[str] = None


@router.get("/settings")
async def get_notification_settings(
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Returns the owner's notification settings, alert preferences, and opt-in status.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    return {
        "brand_id": brand_id,
        "notify_bad_reviews": brand.get("notify_bad_reviews", True),
        "notify_weekly_summary": brand.get("notify_weekly_summary", True),
        "notify_spike": brand.get("notify_spike", True),
        "weekly_digest_day": brand.get("weekly_digest_day", "Monday"),
        "weekly_digest_time": brand.get("weekly_digest_time", "09:00"),
        "email_opt_in": brand.get("email_opt_in", True),
        "whatsapp_opt_in": brand.get("whatsapp_opt_in", False),
        "sms_opt_in": brand.get("sms_opt_in", False),
        "notification_email": brand.get("notification_email") or current_user.get("email"),
        "notification_phone": brand.get("notification_phone", "")
    }


@router.put("/settings")
async def update_notification_settings(
    brand_id: str = Query(...),
    payload: NotificationSettingsUpdate = ...,
    current_user: dict = Depends(get_current_user)
):
    """
    Updates notification alert preferences, weekly digest day & time, and opt-in channels.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()

    update_fields = {}
    for k, v in payload.model_dump(exclude_unset=True).items():
        update_fields[k] = v

    if update_fields:
        await db["brands"].update_one(
            {"id": brand_id},
            {"$set": update_fields}
        )

    updated_brand = await db["brands"].find_one({"id": brand_id})
    return clean_doc(updated_brand)


@router.post("/test")
async def send_test_notification(
    req: NotificationTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Sends a test alert across email, WhatsApp, or SMS to verify provider delivery.
    """
    brand = await get_brand_for_user(req.brand_id, current_user)
    recipient = req.recipient or brand.get("notification_email") or current_user.get("email")

    if req.channel == "email":
        target = recipient
        subj = f"🧪 [{brand.get('name')}] Test Alert from BrandPulse AI"
        body = f"This is a test notification confirming that email alerts are working for {brand.get('name')}."
        success = notification_provider.send_email(target, subj, body)
        return {"status": "sent", "channel": "email", "recipient": target, "delivered": success}

    elif req.channel == "whatsapp":
        target = req.recipient or brand.get("notification_phone")
        if not target:
            raise HTTPException(status_code=400, detail="Please provide a phone number for WhatsApp test.")
        msg = f"🧪 *{brand.get('name')}*: Test alert from BrandPulse AI. WhatsApp notifications are active!"
        success = notification_provider.send_whatsapp(target, msg)
        return {"status": "sent", "channel": "whatsapp", "recipient": target, "delivered": success}

    elif req.channel == "sms":
        target = req.recipient or brand.get("notification_phone")
        if not target:
            raise HTTPException(status_code=400, detail="Please provide a phone number for SMS test.")
        msg = f"{brand.get('name')}: Test SMS alert from BrandPulse AI."
        success = notification_provider.send_sms(target, msg)
        return {"status": "sent", "channel": "sms", "recipient": target, "delivered": success}

    raise HTTPException(status_code=400, detail="Unknown channel. Use 'email', 'whatsapp', or 'sms'.")


@router.post("/trigger-digest")
async def trigger_weekly_digest(
    brand_id: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually triggers generation and dispatch of the weekly digest for the shop owner.
    """
    brand = await get_brand_for_user(brand_id, current_user)
    db = get_db()

    mentions = await db["mentions"].find({"brand_id": brand_id}).sort("timestamp", -1).to_list(100)
    total = len(mentions)
    pos = sum(1 for m in mentions if m.get("sentiment") == "positive")
    pos_pct = round((pos / max(total, 1)) * 100, 1)

    summary_text = (
        f"This week you received {total} customer reviews with a {pos_pct}% positive customer mood. "
        f"Customers praised the food taste and courteous staff. "
        f"Keep an eye on weekend table wait times during peak dinner rush."
    )

    stats = {
        "total_reviews": total,
        "positive_pct": pos_pct,
        "top_praise": "Food taste & staff",
        "top_fix": "Weekend wait times"
    }

    result = notification_dispatcher.dispatch_weekly_digest(brand, summary_text, stats)
    return {"status": "digest_triggered", "result": result}
