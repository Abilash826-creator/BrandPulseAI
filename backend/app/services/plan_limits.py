import datetime
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger("brandpulse.plan_limits")


def _get_current_month_range() -> tuple[datetime.datetime, datetime.datetime]:
    """Returns (start_of_month, end_of_month) in UTC."""
    now = datetime.datetime.now(datetime.timezone.utc)
    start = datetime.datetime(now.year, now.month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    if now.month == 12:
        end = datetime.datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    else:
        end = datetime.datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    return start, end


def get_user_plan(user: Optional[Dict[str, Any]]) -> str:
    """Returns 'pro' or 'free' based on user document."""
    if not user:
        return "free"
    # Admin roles default to pro
    if user.get("role") in ("admin", "executive"):
        return "pro"
    return user.get("plan", "free").lower().strip()


async def check_can_create_business(user: Dict[str, Any], db: Any) -> None:
    """
    Enforces plan limit on number of tracked businesses.
    Free tier allows 1 business.
    """
    plan = get_user_plan(user)
    max_businesses = settings.PLAN_PRO_MAX_BUSINESSES if plan == "pro" else settings.PLAN_FREE_MAX_BUSINESSES

    # Count businesses owned by user
    count = await db["brands"].count_documents({"owner_id": user.get("id")})
    if count >= max_businesses:
        raise HTTPException(
            status_code=402,
            detail=(
                f"The Free plan allows tracking 1 business profile ({count}/{max_businesses} used). "
                f"Please upgrade to Pro to add multiple outlets, branches, and locations."
            ),
            headers={"X-Upgrade-Required": "true", "X-Plan": plan}
        )


async def check_can_add_reviews(
    brand_id: str,
    new_reviews_count: int,
    db: Any,
    user: Optional[Dict[str, Any]] = None
) -> None:
    """
    Enforces monthly review ingestion quota.
    Free tier allows 100 reviews/month.
    """
    plan = get_user_plan(user)
    max_monthly = settings.PLAN_PRO_MAX_REVIEWS_PER_MONTH if plan == "pro" else settings.PLAN_FREE_MAX_REVIEWS_PER_MONTH

    start_of_month, _ = _get_current_month_range()
    iso_start = start_of_month.isoformat()

    # Count reviews ingested this calendar month for this brand
    current_month_count = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "created_at": {"$gte": iso_start}
    })

    # Fallback to timestamp field if created_at not present on older records
    if current_month_count == 0:
        current_month_count = await db["mentions"].count_documents({
            "brand_id": brand_id,
            "timestamp": {"$gte": iso_start}
        })

    if (current_month_count + new_reviews_count) > max_monthly:
        remaining = max(0, max_monthly - current_month_count)
        raise HTTPException(
            status_code=402,
            detail=(
                f"Monthly limit of {max_monthly} reviews reached for this shop on the {plan.capitalize()} plan "
                f"({current_month_count} used, {remaining} remaining). "
                f"Please upgrade to Pro to analyze unlimited customer reviews and feedback."
            ),
            headers={"X-Upgrade-Required": "true", "X-Plan": plan}
        )


async def check_can_send_ai_chat(user: Dict[str, Any], business_id: str, db: Any) -> None:
    """
    Enforces monthly quota on Ask AI conversational messages.
    Free tier allows 20 messages/month.
    """
    plan = get_user_plan(user)
    max_chat = settings.PLAN_PRO_MAX_AI_CHAT_PER_MONTH if plan == "pro" else settings.PLAN_FREE_MAX_AI_CHAT_PER_MONTH

    start_of_month, _ = _get_current_month_range()
    iso_start = start_of_month.isoformat()

    # Count messages sent by user/business this month
    chat_count = await db["ai_chat_usage"].count_documents({
        "business_id": business_id,
        "timestamp": {"$gte": iso_start}
    })

    if chat_count >= max_chat:
        raise HTTPException(
            status_code=402,
            detail=(
                f"You have used all {max_chat} Ask AI assistant messages for this month on the Free plan. "
                f"Upgrade to Pro for unlimited AI business analysis, review summaries, and polite response drafts."
            ),
            headers={"X-Upgrade-Required": "true", "X-Plan": plan}
        )


async def record_ai_chat_usage(user: Dict[str, Any], business_id: str, db: Any) -> None:
    """
    Logs an AI chat invocation to track monthly quota.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    await db["ai_chat_usage"].insert_one({
        "user_id": user.get("id"),
        "business_id": business_id,
        "timestamp": now
    })


async def get_plan_usage_summary(brand_id: str, user: Dict[str, Any], db: Any) -> Dict[str, Any]:
    """
    Returns comprehensive plan quota usage for the shop owner dashboard.
    """
    plan = get_user_plan(user)
    start_of_month, _ = _get_current_month_range()
    iso_start = start_of_month.isoformat()

    businesses_used = await db["brands"].count_documents({"owner_id": user.get("id")})
    businesses_max = settings.PLAN_PRO_MAX_BUSINESSES if plan == "pro" else settings.PLAN_FREE_MAX_BUSINESSES

    reviews_used = await db["mentions"].count_documents({
        "brand_id": brand_id,
        "$or": [
            {"created_at": {"$gte": iso_start}},
            {"timestamp": {"$gte": iso_start}}
        ]
    })
    reviews_max = settings.PLAN_PRO_MAX_REVIEWS_PER_MONTH if plan == "pro" else settings.PLAN_FREE_MAX_REVIEWS_PER_MONTH

    chat_used = await db["ai_chat_usage"].count_documents({
        "business_id": brand_id,
        "timestamp": {"$gte": iso_start}
    })
    chat_max = settings.PLAN_PRO_MAX_AI_CHAT_PER_MONTH if plan == "pro" else settings.PLAN_FREE_MAX_AI_CHAT_PER_MONTH

    return {
        "plan": plan,
        "is_free": plan == "free",
        "limits": {
            "businesses": {"used": businesses_used, "max": businesses_max, "pct": round((businesses_used / businesses_max) * 100, 1)},
            "reviews_per_month": {"used": reviews_used, "max": reviews_max, "pct": round((reviews_used / reviews_max) * 100, 1)},
            "ai_chat_per_month": {"used": chat_used, "max": chat_max, "pct": round((chat_used / chat_max) * 100, 1)}
        }
    }
