from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.database import db_manager, get_db
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user, require_role

router = APIRouter()

@router.get("/db-status")
async def get_db_status(current_user: dict = Depends(require_role("admin"))) -> Dict[str, Any]:
    """
    Get real-time database connection status, collection sizes, and active driver mode.
    Restricted to admins.
    """
    return await db_manager.get_status()

