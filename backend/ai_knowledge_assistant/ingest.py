from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .auth import current_user_id
from . import registry
from .registry import get_connection

router = APIRouter()


class IngestRequest(BaseModel):
    namespace: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    source_type: str = Field(default="file")


@router.post("/{workspace_id}/ingest")
def queue_ingest(
    workspace_id: str,
    body: IngestRequest,
    user_id: str = Depends(current_user_id),
):
    if not registry.user_can_access_workspace(user_id, workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    org_id = None
    with get_connection() as conn:
        row = conn.execute(
            "SELECT organization_id FROM workspaces WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workspace not found")
        org_id = row["organization_id"]
    job_id = str(uuid.uuid4())
    payload = json.dumps({"queued_by": user_id, "at": datetime.now(timezone.utc).isoformat()})
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO ingestion_jobs (
                job_id, workspace_id, organization_id, namespace, source, source_type,
                status, document_id, chunks_indexed, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, 'queued', NULL, 0, ?)
            """,
            (
                job_id,
                workspace_id,
                org_id,
                body.namespace,
                body.source,
                body.source_type,
                payload,
            ),
        )
        conn.commit()
    return {"job_id": job_id, "status": "queued"}
