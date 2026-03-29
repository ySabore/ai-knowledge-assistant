from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .auth import current_user_id
from . import registry

router = APIRouter()


@router.get("/{workspace_id}/documents")
def list_workspace_documents(
    workspace_id: str,
    user_id: str = Depends(current_user_id),
):
    if not registry.user_can_access_workspace(user_id, workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"documents": registry.list_documents_for_workspace(workspace_id)}
