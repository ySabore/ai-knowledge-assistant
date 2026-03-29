from __future__ import annotations

from fastapi import APIRouter, Depends

from .auth import current_user_id

router = APIRouter()


@router.get("/ping")
def admin_ping(user_id: str = Depends(current_user_id)):
    return {"ok": True, "user_id": user_id}
