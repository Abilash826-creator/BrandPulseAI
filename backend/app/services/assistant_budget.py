import datetime
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import logger

async def check_and_update_token_budget(db, business_id: str, estimated_tokens: int = 500) -> int:
    """
    Enforces per-business monthly token budget.
    Raises HTTPException(429) if budget limit is exceeded.
    Returns remaining token budget for the current month.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    current_month = now.strftime("%Y-%m")
    budget_limit = getattr(settings, "ASSISTANT_MONTHLY_TOKEN_BUDGET", 50000)

    record = await db["business_token_usage"].find_one({
        "business_id": business_id,
        "month": current_month
    })

    current_usage = record.get("tokens_used", 0) if record else 0

    if current_usage + estimated_tokens > budget_limit:
        logger.warning(f"Assistant budget exceeded for business {business_id}: usage={current_usage}, limit={budget_limit}")
        raise HTTPException(
            status_code=429,
            detail=f"Monthly AI assistant message budget reached ({current_usage}/{budget_limit} tokens used). Please upgrade your plan or wait until next month."
        )

    # Increment token counter
    await db["business_token_usage"].update_one(
        {"business_id": business_id, "month": current_month},
        {
            "$inc": {"tokens_used": estimated_tokens},
            "$set": {"updated_at": now},
            "$setOnInsert": {"created_at": now}
        },
        upsert=True
    )

    remaining = max(0, budget_limit - (current_usage + estimated_tokens))
    return remaining

async def get_budget_status(db, business_id: str) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    current_month = now.strftime("%Y-%m")
    budget_limit = getattr(settings, "ASSISTANT_MONTHLY_TOKEN_BUDGET", 50000)

    record = await db["business_token_usage"].find_one({
        "business_id": business_id,
        "month": current_month
    })
    used = record.get("tokens_used", 0) if record else 0

    return {
        "current_month": current_month,
        "tokens_used": used,
        "token_limit": budget_limit,
        "remaining_tokens": max(0, budget_limit - used),
        "is_budget_exceeded": used >= budget_limit
    }
