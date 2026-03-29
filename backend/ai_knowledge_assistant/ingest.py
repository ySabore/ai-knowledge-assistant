from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import config
from .auth import current_user_id
from . import registry
from .registry import get_connection

router = APIRouter()


class IngestRequest(BaseModel):
    namespace: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    source_type: str = Field(default="file")


def _workspace_org_id(workspace_id: str, user_id: str) -> str:
    if not registry.user_can_access_workspace(user_id, workspace_id):
        raise HTTPException(status_code=404, detail="Workspace not found")
    with get_connection() as conn:
        row = conn.execute(
            "SELECT organization_id FROM workspaces WHERE workspace_id = ?",
            (workspace_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return str(row["organization_id"])


def _queue_job(workspace_id: str, organization_id: str, namespace: str, source: str, source_type: str, user_id: str) -> dict[str, str]:
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
                organization_id,
                namespace,
                source,
                source_type,
                payload,
            ),
        )
        conn.commit()
    return {"job_id": job_id, "status": "queued"}


@router.post("/{workspace_id}/ingest")
def queue_ingest(
    workspace_id: str,
    body: IngestRequest,
    user_id: str = Depends(current_user_id),
):
    org_id = _workspace_org_id(workspace_id, user_id)
    return _queue_job(workspace_id, org_id, body.namespace, body.source, body.source_type, user_id)


@router.post("/{workspace_id}/upload")
async def upload_and_queue_ingest(
    workspace_id: str,
    namespace: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(current_user_id),
):
    org_id = _workspace_org_id(workspace_id, user_id)

    original_name = Path(file.filename or "upload.bin").name
    suffix = Path(original_name).suffix
    staged_name = f"{uuid.uuid4().hex}{suffix}"
    spool_dir = config.ingest_spool_dir()
    spool_dir.mkdir(parents=True, exist_ok=True)
    staged_path = spool_dir / staged_name

    max_bytes = config.max_file_size_bytes()
    total_written = 0

    try:
        with staged_path.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total_written += len(chunk)
                if total_written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {config.max_file_size_mb()} MB limit",
                    )
                handle.write(chunk)
    except Exception:
        if staged_path.exists():
            staged_path.unlink()
        raise
    finally:
        await file.close()

    job = _queue_job(workspace_id, org_id, namespace, str(staged_path), "file", user_id)
    return {
        **job,
        "filename": original_name,
        "stored_as": staged_path.name,
        "bytes": total_written,
    }
