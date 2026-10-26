import uuid
import json
import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.database import get_db, clean_doc
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.brands import get_brand_for_user
from app.services.assistant_budget import check_and_update_token_budget, get_budget_status
from app.services.assistant_llm import get_assistant_llm_provider
from app.services.assistant_tools import sanitize_untrusted_text, get_unreplied_reviews, get_overview

router = APIRouter()

class ChatRequest(BaseModel):
    business_id: str
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "en"

class SuggestedQuestionsResponse(BaseModel):
    business_id: str
    questions: List[str]

@router.get("/suggested-questions", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions(
    business_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Returns 4 contextual prompts based on the business's actual real-time review data.
    """
    await get_brand_for_user(business_id, current_user)
    db = get_db()

    # Inspect current business situation
    overview = await get_overview(db, business_id=business_id, period="last_7_days")
    unreplied = await get_unreplied_reviews(db, business_id=business_id, limit=1)

    questions = []

    # Contextual check 1: Complaints / Issues
    if overview.get("mood_distribution", {}).get("unhappy", 0) > 0:
        questions.append("What did customers complain about this week?")
    else:
        questions.append("What are customers saying about our service?")

    # Contextual check 2: Unreplied reviews
    if unreplied.get("unreplied_count", 0) > 0:
        questions.append("Write a reply to my latest unreplied review")
    else:
        questions.append("What are the top 3 things customers love most?")

    # Contextual check 3: Rating / Trend
    questions.append("Why did my customer rating change recently?")

    # Contextual check 4: Action item
    questions.append("What should I fix first to improve customer satisfaction?")

    return SuggestedQuestionsResponse(
        business_id=business_id,
        questions=questions[:4]
    )

@router.get("/budget-status")
async def get_assistant_budget(
    business_id: str,
    current_user: dict = Depends(get_current_user)
):
    await get_brand_for_user(business_id, current_user)
    db = get_db()
    return await get_budget_status(db, business_id=business_id)

@router.get("/conversations")
async def list_conversations(
    business_id: str,
    current_user: dict = Depends(get_current_user)
):
    await get_brand_for_user(business_id, current_user)
    db = get_db()
    cursor = db["assistant_conversations"].find({
        "business_id": business_id,
        "user_id": current_user["id"]
    }).sort("updated_at", -1).limit(30)
    convs = await cursor.to_list(30)
    return [clean_doc(c) for c in convs]

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    conv = await db["assistant_conversations"].find_one({"id": conversation_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await get_brand_for_user(conv["business_id"], current_user)
    return clean_doc(conv)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    conv = await db["assistant_conversations"].find_one({"id": conversation_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await get_brand_for_user(conv["business_id"], current_user)
    await db["assistant_conversations"].delete_one({"id": conversation_id})
    return {"status": "deleted", "id": conversation_id}

@router.post("/chat")
async def chat_with_assistant(
    req: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Streams AI Assistant answers via Server-Sent Events (SSE).
    Enforces tenant isolation, token budgets, and untrusted review isolation.
    """
    brand = await get_brand_for_user(req.business_id, current_user)
    db = get_db()

    # Enforce monthly token budget (will raise 429 if exceeded)
    await check_and_update_token_budget(db, business_id=req.business_id, estimated_tokens=400)

    # Enforce plan limits (Free plan = 20 messages/month)
    from app.services.plan_limits import check_can_send_ai_chat, record_ai_chat_usage
    await check_can_send_ai_chat(current_user, req.business_id, db)
    await record_ai_chat_usage(current_user, req.business_id, db)

    user_msg_clean = sanitize_untrusted_text(req.message)
    if not user_msg_clean:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Manage or create conversation
    now = datetime.datetime.now(datetime.timezone.utc)
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"

    conv = await db["assistant_conversations"].find_one({"id": conv_id})
    if not conv:
        conv = {
            "id": conv_id,
            "business_id": req.business_id,
            "business_name": brand["name"],
            "user_id": current_user["id"],
            "title": user_msg_clean[:40] + ("..." if len(user_msg_clean) > 40 else ""),
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
    else:
        # Verify ownership
        await get_brand_for_user(conv["business_id"], current_user)

    # Append user message
    user_msg_obj = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "role": "user",
        "content": user_msg_clean,
        "created_at": now.isoformat()
    }
    history = list(conv.get("messages", []))
    history.append(user_msg_obj)

    llm = get_assistant_llm_provider()

    async def event_generator():
        collected_response = []
        assistant_msg_id = f"msg_{uuid.uuid4().hex[:8]}"

        try:
            async for chunk in llm.chat_stream(
                db=db,
                business_id=req.business_id,
                user_id=current_user["id"],
                messages=history,
                user_language=req.language or "en"
            ):
                event_type = chunk.get("type")
                if event_type == "text_delta":
                    collected_response.append(chunk.get("delta", ""))
                
                # Stream JSON SSE frame
                yield f"data: {json.dumps(chunk)}\n\n"

            # Final assistant message object
            full_text = "".join(collected_response)
            assistant_msg_obj = {
                "id": assistant_msg_id,
                "role": "assistant",
                "content": full_text,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            history.append(assistant_msg_obj)

            # Persist updated conversation
            await db["assistant_conversations"].update_one(
                {"id": conv_id},
                {
                    "$set": {
                        "messages": history,
                        "updated_at": datetime.datetime.now(datetime.timezone.utc),
                        "business_id": req.business_id,
                        "user_id": current_user["id"],
                        "title": conv.get("title") or user_msg_clean[:40]
                    },
                    "$setOnInsert": {
                        "id": conv_id,
                        "created_at": now
                    }
                },
                upsert=True
            )

            # Send final completion event
            done_payload = {
                "type": "completed",
                "conversation_id": conv_id,
                "message_id": assistant_msg_id
            }
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            err_payload = {"type": "error", "detail": str(e)}
            yield f"data: {json.dumps(err_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
