from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from pydantic import BaseModel, Field

from .auth import current_user_id
from . import config
from . import registry
from .rag_service import run_rag_chat

router = APIRouter()
log = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/{workspace_id}/chat")
def chat_workspace(
    workspace_id: str,
    body: ChatRequest,
    request: Request,
    user_id: str = Depends(current_user_id),
):
    if not registry.user_can_access_workspace(user_id, workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")
    if not config.rag_is_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "error": "rag_not_configured",
                "messages": config.rag_configuration_errors(),
            },
        )
    rid = getattr(request.state, "request_id", None)
    try:
        reply, sources = run_rag_chat(body.messages, workspace_id)
    except ValueError as e:
        log.warning("chat validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.exception("chat RAG failure")
        raise HTTPException(
            status_code=502,
            detail={"error": "rag_upstream_failure", "type": type(e).__name__},
        ) from e
    return {
        "reply": reply,
        "sources": sources,
        "request_id": rid,
    }
