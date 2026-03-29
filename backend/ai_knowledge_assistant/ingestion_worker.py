"""
Background ingestion worker: dequeue jobs, extract text, chunk, embed, upsert Pinecone.

Run:  cd backend && python -m ai_knowledge_assistant.ingestion_worker
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import requests

from . import chunking, config, embeddings, text_extract, vectorstore
from .embeddings import validate_embedding_dimension
from .path_allowlist import PathNotAllowedError, resolve_ingestion_file
from .registry import get_connection
from .startup import load_env_files

log = logging.getLogger(__name__)

MAX_URL_BYTES = 15 * 1024 * 1024
EMBED_BATCH = 32
UPSERT_BATCH = 64


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _fetch_next_job(conn) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT job_id, workspace_id, organization_id, namespace, source, source_type,
               attempt_count, max_attempts
        FROM ingestion_jobs
        WHERE status = 'queued'
        ORDER BY created_at ASC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _claim_job(conn, job_id: str) -> bool:
    cur = conn.execute(
        """
        UPDATE ingestion_jobs
        SET status = 'processing', started_at = ?, updated_at = ?
        WHERE job_id = ? AND status = 'queued'
        """,
        (_utc_now(), _utc_now(), job_id),
    )
    return cur.rowcount > 0


def _load_text(source: str, source_type: str) -> str:
    st = (source_type or "file").strip().lower()
    if st in ("url", "http", "https"):
        if not source.startswith(("http://", "https://")):
            raise ValueError("URL source must start with http:// or https://")
        r = requests.get(source, timeout=120)
        r.raise_for_status()
        data = r.content[:MAX_URL_BYTES]
        return data.decode("utf-8", errors="replace")
    path = resolve_ingestion_file(source)
    return text_extract.extract_text(path)


def _process_job_row(job: dict[str, Any]) -> None:
    if not config.rag_is_configured():
        raise RuntimeError(
            "RAG is not configured; cannot ingest: " + "; ".join(config.rag_configuration_errors())
        )

    workspace_id = job["workspace_id"]
    organization_id = job["organization_id"]
    namespace = job["namespace"]
    source = job["source"]
    source_type = job["source_type"]
    job_id = job["job_id"]

    body = _load_text(source, source_type)
    parts = chunking.chunk_text(body, config.rag_chunk_size(), config.rag_chunk_overlap())
    if not parts:
        raise ValueError("no text extracted or document is empty")

    document_id = str(uuid.uuid4())
    embedder = embeddings.build_embedder()
    meta_cap = config.metadata_text_max_chars()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (
                document_id, namespace, source, source_type, chunk_count,
                workspace_id, organization_id, record_status, ingestion_status, health_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 'processing', 'pending', ?)
            """,
            (
                document_id,
                namespace,
                source,
                source_type,
                len(parts),
                workspace_id,
                organization_id,
                _utc_now(),
            ),
        )
        conn.commit()

    all_vectors: list[dict[str, Any]] = []
    chunk_rows: list[tuple[str, str, str, str, int, str, str, str]] = []

    for start in range(0, len(parts), EMBED_BATCH):
        batch = parts[start : start + EMBED_BATCH]
        vecs = embedder.embed_documents(batch)
        for i, (text, vec) in enumerate(zip(batch, vecs, strict=True)):
            global_idx = start + i
            validate_embedding_dimension(vec)
            vid = f"{document_id}:{global_idx}"
            meta = {
                "workspace_id": workspace_id,
                "organization_id": organization_id,
                "namespace": namespace,
                "document_id": document_id,
                "source": source,
                "chunk_number": global_idx,
                "text": text[:meta_cap],
            }
            all_vectors.append({"id": vid, "values": vec, "metadata": meta})
            chunk_id = str(uuid.uuid4())
            chunk_rows.append(
                (
                    chunk_id,
                    document_id,
                    namespace,
                    source,
                    global_idx,
                    vid,
                    workspace_id,
                    organization_id,
                )
            )

    for u in range(0, len(all_vectors), UPSERT_BATCH):
        vectorstore.upsert_vectors(workspace_id, all_vectors[u : u + UPSERT_BATCH])

    with get_connection() as conn:
        for row in chunk_rows:
            conn.execute(
                """
                INSERT INTO chunks (
                    chunk_id, document_id, namespace, source, chunk_number,
                    vector_id, workspace_id, organization_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row + (_utc_now(),),
            )
        conn.execute(
            """
            UPDATE documents
            SET ingestion_status = 'indexed', health_status = 'ok', last_ingested_at = ?, last_error = NULL
            WHERE document_id = ?
            """,
            (_utc_now(), document_id),
        )
        conn.execute(
            """
            UPDATE ingestion_jobs
            SET status = 'completed',
                finished_at = ?,
                updated_at = ?,
                document_id = ?,
                chunks_indexed = ?,
                error_message = NULL
            WHERE job_id = ?
            """,
            (_utc_now(), _utc_now(), document_id, len(parts), job_id),
        )
        conn.commit()

    log.info("ingestion job %s completed: document_id=%s chunks=%s", job_id, document_id, len(parts))


def _fail_job(job_id: str, err: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE ingestion_jobs
            SET status = 'failed',
                finished_at = ?,
                updated_at = ?,
                error_message = ?,
                attempt_count = attempt_count + 1
            WHERE job_id = ?
            """,
            (_utc_now(), _utc_now(), err[:4000], job_id),
        )
        conn.commit()


def process_one_job() -> bool:
    """Return True if a job was processed (or attempted)."""
    load_env_files()
    with get_connection() as conn:
        job = _fetch_next_job(conn)
        if not job:
            return False
        job_id = job["job_id"]
        if not _claim_job(conn, job_id):
            conn.commit()
            return False
        conn.commit()

    try:
        _process_job_row(job)
    except PathNotAllowedError as e:
        log.warning("job %s path denied: %s", job["job_id"], e)
        _fail_job(job["job_id"], f"path not allowed: {e}")
    except Exception as e:
        log.exception("job %s failed", job["job_id"])
        _fail_job(job["job_id"], f"{type(e).__name__}: {e}")
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_env_files()
    log.info("ingestion worker started (poll %.1fs)", config.ingest_poll_interval_seconds())
    if not config.rag_is_configured():
        log.error("RAG not configured: %s", config.rag_configuration_errors())
    while True:
        try:
            worked = process_one_job()
            if not worked:
                time.sleep(config.ingest_poll_interval_seconds())
        except KeyboardInterrupt:
            log.info("ingestion worker stopped")
            raise


if __name__ == "__main__":
    main()
