"""SQLite registry access (schema is defined by existing `app.db` migrations)."""

from __future__ import annotations

import re
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Any, Generator

from . import config

ADMIN_ROLES = {"owner", "admin"}


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


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "workspace"


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


def user_org_role(user_id: str, organization_id: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT role
            FROM organization_memberships
            WHERE user_id = ?
              AND organization_id = ?
              AND status = 'active'
            LIMIT 1
            """,
            (user_id, organization_id),
        ).fetchone()
        if not row:
            return None
        return str(row["role"])


def user_is_org_admin(user_id: str, organization_id: str) -> bool:
    role = user_org_role(user_id, organization_id)
    return role in ADMIN_ROLES


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


def user_workspaces(user_id: str, organization_id: str) -> list[dict[str, Any]]:
    if user_is_org_admin(user_id, organization_id):
        return org_workspaces(organization_id)

    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT w.workspace_id, w.organization_id, w.workspace_name, w.workspace_slug,
                   w.description, w.status, w.purpose, w.workspace_type, w.created_at
            FROM workspaces w
            JOIN workspace_memberships wm
              ON wm.workspace_id = w.workspace_id
            WHERE w.organization_id = ?
              AND w.status = 'active'
              AND wm.user_id = ?
              AND wm.status = 'active'
            ORDER BY w.workspace_name
            """,
            (organization_id, user_id),
        )
        return fetchall_dicts(cur)


def user_can_access_workspace(user_id: str, workspace_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT w.organization_id
            FROM workspaces w
            WHERE w.workspace_id = ?
              AND w.status = 'active'
            LIMIT 1
            """,
            (workspace_id,),
        ).fetchone()
        if not row:
            return False
        organization_id = str(row["organization_id"])
        if user_is_org_admin(user_id, organization_id):
            return True
        member = conn.execute(
            """
            SELECT 1
            FROM workspace_memberships
            WHERE workspace_id = ?
              AND user_id = ?
              AND status = 'active'
            LIMIT 1
            """,
            (workspace_id, user_id),
        ).fetchone()
        return member is not None


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


def user_id_by_email(email: str) -> str | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE lower(email) = lower(?) LIMIT 1",
            (_normalize_email(email),),
        ).fetchone()
        if not row:
            return None
        return str(row["user_id"])


def user_record(user_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, email, display_name, auth_provider, auth_subject, status, created_at, last_login_at
            FROM users
            WHERE user_id = ?
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def ensure_user_for_auth_subject(
    auth_subject: str,
    email: str | None = None,
    display_name: str | None = None,
) -> str:
    existing = user_id_by_auth_subject(auth_subject)
    if existing:
        return existing

    normalized_email = _normalize_email(email) if email else None
    final_name = display_name or auth_subject

    if normalized_email:
        email_existing = user_id_by_email(normalized_email)
        if email_existing:
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE users
                    SET auth_provider = 'clerk',
                        auth_subject = ?,
                        display_name = COALESCE(?, display_name),
                        status = 'active',
                        last_login_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (auth_subject, display_name, email_existing),
                )
                conn.commit()
            return email_existing

    user_id = f"clerk:{uuid.uuid4().hex}"
    final_email = normalized_email or f"{auth_subject}@clerk.local"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id, email, display_name, auth_provider, auth_subject, status, last_login_at
            ) VALUES (?, ?, ?, 'clerk', ?, 'active', CURRENT_TIMESTAMP)
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


def ensure_invited_user(email: str, display_name: str | None = None) -> str:
    normalized_email = _normalize_email(email)
    existing = user_id_by_email(normalized_email)
    if existing:
        return existing

    user_id = f"invite:{uuid.uuid4().hex}"
    auth_subject = f"invite:{normalized_email}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (
                user_id, email, display_name, auth_provider, auth_subject, status
            ) VALUES (?, ?, ?, 'invite', ?, 'active')
            """,
            (
                user_id,
                normalized_email,
                display_name or normalized_email,
                auth_subject,
            ),
        )
        conn.commit()
    return user_id


def create_organization(
    owner_user_id: str,
    organization_name: str,
    industry: str = "other",
) -> dict[str, Any]:
    organization_id = f"org:{uuid.uuid4().hex}"
    default_workspace = create_workspace_record(
        organization_id=organization_id,
        workspace_name="General",
        description="Default workspace",
        purpose="General knowledge and collaboration",
        workspace_type="general",
    )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO organizations (
                organization_id, organization_name, industry, status, owner_user_id
            ) VALUES (?, ?, ?, 'active', ?)
            """,
            (organization_id, organization_name.strip(), industry.strip() or "other", owner_user_id),
        )
        conn.execute(
            """
            INSERT INTO organization_memberships (
                membership_id, user_id, organization_id, role, status, invited_by_user_id
            ) VALUES (?, ?, ?, 'owner', 'active', ?)
            """,
            (f"membership:{uuid.uuid4().hex}", owner_user_id, organization_id, owner_user_id),
        )
        conn.execute(
            """
            INSERT INTO workspaces (
                workspace_id, organization_id, workspace_name, workspace_slug, description,
                status, purpose, workspace_type
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                default_workspace["workspace_id"],
                organization_id,
                default_workspace["workspace_name"],
                default_workspace["workspace_slug"],
                default_workspace["description"],
                default_workspace["purpose"],
                default_workspace["workspace_type"],
            ),
        )
        conn.commit()

    return {
        "organization_id": organization_id,
        "organization_name": organization_name.strip(),
        "industry": industry.strip() or "other",
        "default_workspace": default_workspace,
    }


def create_workspace_record(
    organization_id: str,
    workspace_name: str,
    description: str = "",
    purpose: str = "",
    workspace_type: str = "general",
) -> dict[str, Any]:
    workspace_name = workspace_name.strip()
    base_slug = slugify(workspace_name)
    workspace_id = f"{organization_id}::{base_slug}"
    return {
        "workspace_id": workspace_id,
        "organization_id": organization_id,
        "workspace_name": workspace_name,
        "workspace_slug": base_slug,
        "description": description.strip(),
        "purpose": purpose.strip(),
        "workspace_type": workspace_type.strip() or "general",
    }


def create_workspace(
    organization_id: str,
    workspace_name: str,
    description: str = "",
    purpose: str = "",
    workspace_type: str = "general",
) -> dict[str, Any]:
    record = create_workspace_record(organization_id, workspace_name, description, purpose, workspace_type)
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT 1 FROM workspaces
            WHERE organization_id = ? AND workspace_slug = ?
            LIMIT 1
            """,
            (organization_id, record["workspace_slug"]),
        ).fetchone()
        if existing:
            raise ValueError("Workspace slug already exists for this organization")
        conn.execute(
            """
            INSERT INTO workspaces (
                workspace_id, organization_id, workspace_name, workspace_slug, description,
                status, purpose, workspace_type
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                record["workspace_id"],
                organization_id,
                record["workspace_name"],
                record["workspace_slug"],
                record["description"],
                record["purpose"],
                record["workspace_type"],
            ),
        )
        conn.commit()
    return record


def organization_members(organization_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT om.membership_id, om.organization_id, om.user_id, om.role, om.status,
                   om.invited_by_user_id, om.created_at,
                   u.email, u.display_name
            FROM organization_memberships om
            JOIN users u ON u.user_id = om.user_id
            WHERE om.organization_id = ?
            ORDER BY u.email
            """,
            (organization_id,),
        )
        members = fetchall_dicts(cur)
        for member in members:
            member["workspace_ids"] = workspace_ids_for_user(member["user_id"], organization_id)
        return members


def workspace_ids_for_user(user_id: str, organization_id: str) -> list[str]:
    if user_is_org_admin(user_id, organization_id):
        return [ws["workspace_id"] for ws in org_workspaces(organization_id)]
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT wm.workspace_id
            FROM workspace_memberships wm
            JOIN workspaces w ON w.workspace_id = wm.workspace_id
            WHERE wm.user_id = ?
              AND wm.status = 'active'
              AND w.organization_id = ?
              AND w.status = 'active'
            ORDER BY wm.workspace_id
            """,
            (user_id, organization_id),
        )
        return [str(row["workspace_id"]) for row in cur.fetchall()]


def workspace_members(workspace_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT wm.workspace_membership_id, wm.workspace_id, wm.user_id, wm.role, wm.status,
                   wm.invited_by_user_id, wm.created_at, u.email, u.display_name
            FROM workspace_memberships wm
            JOIN users u ON u.user_id = wm.user_id
            WHERE wm.workspace_id = ?
            ORDER BY u.email
            """,
            (workspace_id,),
        )
        return fetchall_dicts(cur)


def grant_workspace_access(
    workspace_id: str,
    user_id: str,
    role: str = "member",
    invited_by_user_id: str | None = None,
) -> None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT workspace_membership_id
            FROM workspace_memberships
            WHERE workspace_id = ? AND user_id = ?
            LIMIT 1
            """,
            (workspace_id, user_id),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE workspace_memberships
                SET role = ?, status = 'active', invited_by_user_id = COALESCE(?, invited_by_user_id)
                WHERE workspace_membership_id = ?
                """,
                (role, invited_by_user_id, row["workspace_membership_id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO workspace_memberships (
                    workspace_membership_id, workspace_id, user_id, role, status, invited_by_user_id
                ) VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (f"wsm:{uuid.uuid4().hex}", workspace_id, user_id, role, invited_by_user_id),
            )
        conn.commit()


def invite_member_to_organization(
    organization_id: str,
    email: str,
    display_name: str | None,
    role: str,
    workspace_ids: list[str],
    invited_by_user_id: str,
) -> dict[str, Any]:
    invited_user_id = ensure_invited_user(email, display_name)
    normalized_role = role.strip().lower() or "member"

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT membership_id
            FROM organization_memberships
            WHERE user_id = ? AND organization_id = ?
            LIMIT 1
            """,
            (invited_user_id, organization_id),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE organization_memberships
                SET role = ?, status = 'active', invited_by_user_id = COALESCE(?, invited_by_user_id)
                WHERE membership_id = ?
                """,
                (normalized_role, invited_by_user_id, row["membership_id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO organization_memberships (
                    membership_id, user_id, organization_id, role, status, invited_by_user_id
                ) VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (
                    f"membership:{uuid.uuid4().hex}",
                    invited_user_id,
                    organization_id,
                    normalized_role,
                    invited_by_user_id,
                ),
            )
        conn.commit()

    if normalized_role not in ADMIN_ROLES:
        for workspace_id in workspace_ids:
            grant_workspace_access(workspace_id, invited_user_id, "member", invited_by_user_id)

    return {
        "user_id": invited_user_id,
        "email": _normalize_email(email),
        "role": normalized_role,
        "workspace_ids": workspace_ids if normalized_role not in ADMIN_ROLES else [ws["workspace_id"] for ws in org_workspaces(organization_id)],
    }
