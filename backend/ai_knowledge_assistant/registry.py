"""SQLite registry access (schema is defined by existing `app.db` migrations)."""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from typing import Any, Generator

from . import config


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    path = config.registry_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def fetchall_dicts(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def user_organizations(user_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT o.organization_id AS organization_id,
                   o.organization_name AS organization_name,
                   o.industry AS industry,
                   o.status AS status,
                   om.role AS role
            FROM organizations o
            JOIN organization_memberships om
              ON om.organization_id = o.organization_id
            WHERE om.user_id = ?
              AND om.status = 'active'
              AND o.status = 'active'
            ORDER BY o.organization_name
            """,
            (user_id,),
        )
        return fetchall_dicts(cur)


def org_workspaces(organization_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT workspace_id, organization_id, workspace_name, workspace_slug,
                   description, status, purpose, workspace_type, created_at
            FROM workspaces
            WHERE organization_id = ? AND status = 'active'
            ORDER BY workspace_name
            """,
            (organization_id,),
        )
        return fetchall_dicts(cur)


def user_can_access_workspace(user_id: str, workspace_id: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT 1
            FROM workspaces w
            JOIN organization_memberships om
              ON om.organization_id = w.organization_id
            WHERE w.workspace_id = ?
              AND w.status = 'active'
              AND om.user_id = ?
              AND om.status = 'active'
            LIMIT 1
            """,
            (workspace_id, user_id),
        )
        return cur.fetchone() is not None


def list_documents_for_workspace(workspace_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT document_id, namespace, source, source_type, chunk_count,
                   created_at, workspace_id, organization_id, record_status,
                   ingestion_status, health_status, last_error, last_ingested_at
            FROM documents
            WHERE workspace_id = ? AND record_status = 'active'
            ORDER BY created_at DESC
            """,
            (workspace_id,),
        )
        return fetchall_dicts(cur)


def user_id_by_auth_subject(auth_subject: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE auth_subject = ? LIMIT 1",
            (auth_subject,),
        ).fetchone()
        if not row:
            return None
        return str(row["user_id"])


def ensure_user_for_auth_subject(
    auth_subject: str,
    email: str | None = None,
    display_name: str | None = None,
) -> str:
    existing = user_id_by_auth_subject(auth_subject)
    if existing:
        return existing

    user_id = f"clerk:{uuid.uuid4().hex}"
    final_email = email or f"{auth_subject}@clerk.local"
    final_name = display_name or auth_subject

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id, email, display_name, auth_provider, auth_subject, status
            ) VALUES (?, ?, ?, 'clerk', ?, 'active')
            """,
            (
                user_id,
                final_email,
                final_name,
                auth_subject,
            ),
        )
        conn.commit()

    return user_id
