from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

_TEST_DB_PATH = Path(__file__).resolve().parent / ".tmp-smoke-registry.db"


def _reset_smoke_db(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()

    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE users (
              user_id TEXT PRIMARY KEY,
              email TEXT NOT NULL UNIQUE,
              display_name TEXT NOT NULL,
              auth_provider TEXT NOT NULL DEFAULT 'dev-bearer',
              auth_subject TEXT NOT NULL UNIQUE,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              last_login_at TEXT
            );

            CREATE TABLE organizations (
              organization_id TEXT PRIMARY KEY,
              organization_name TEXT NOT NULL,
              industry TEXT NOT NULL DEFAULT 'other',
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              owner_user_id TEXT
            );

            CREATE TABLE workspaces (
              workspace_id TEXT PRIMARY KEY,
              organization_id TEXT NOT NULL,
              workspace_name TEXT NOT NULL,
              workspace_slug TEXT NOT NULL,
              description TEXT NOT NULL DEFAULT '',
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              purpose TEXT NOT NULL DEFAULT '',
              workspace_type TEXT NOT NULL DEFAULT 'general',
              UNIQUE(organization_id, workspace_slug)
            );

            CREATE TABLE organization_memberships (
              membership_id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              organization_id TEXT NOT NULL,
              role TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active',
              invited_by_user_id TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(user_id, organization_id)
            );

            CREATE TABLE workspace_memberships (
              workspace_membership_id TEXT PRIMARY KEY,
              workspace_id TEXT NOT NULL,
              user_id TEXT NOT NULL,
              role TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'active',
              invited_by_user_id TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              UNIQUE(workspace_id, user_id)
            );

            CREATE TABLE ingestion_jobs (
              job_id TEXT PRIMARY KEY,
              workspace_id TEXT NOT NULL,
              organization_id TEXT NOT NULL,
              namespace TEXT NOT NULL,
              source TEXT NOT NULL,
              source_type TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'queued',
              error_message TEXT,
              document_id TEXT,
              chunks_indexed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              started_at TEXT,
              finished_at TEXT,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              attempt_count INTEGER NOT NULL DEFAULT 0,
              max_attempts INTEGER NOT NULL DEFAULT 3,
              cancel_requested INTEGER NOT NULL DEFAULT 0,
              next_attempt_at TEXT,
              payload_json TEXT
            );
            """
        )

        conn.execute(
            """
            INSERT INTO users (user_id, email, display_name, auth_provider, auth_subject, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            ("user-alpha", "user-alpha@example.com", "User Alpha", "dev-bearer", "dev:user-alpha"),
        )
        conn.execute(
            """
            INSERT INTO organizations (organization_id, organization_name, industry, status, owner_user_id)
            VALUES (?, ?, ?, 'active', ?)
            """,
            ("auth-org-alpha", "Alpha Org", "technology", "user-alpha"),
        )
        conn.execute(
            """
            INSERT INTO organization_memberships (membership_id, user_id, organization_id, role, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            ("membership-alpha", "user-alpha", "auth-org-alpha", "owner"),
        )
        conn.execute(
            """
            INSERT INTO workspaces (
                workspace_id, organization_id, workspace_name, workspace_slug, description, status, purpose, workspace_type
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                "auth-org-alpha::support",
                "auth-org-alpha",
                "Support",
                "support",
                "Customer support workspace",
                "answer support questions",
                "knowledge",
            ),
        )
        conn.execute(
            """
            INSERT INTO workspace_memberships (
                workspace_membership_id, workspace_id, user_id, role, status
            ) VALUES (?, ?, ?, ?, 'active')
            """,
            ("workspace-membership-alpha", "auth-org-alpha::support", "user-alpha", "owner"),
        )
        conn.execute(
            """
            INSERT INTO users (user_id, email, display_name, auth_provider, auth_subject, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            ("user-beta", "user-beta@example.com", "User Beta", "dev-bearer", "dev:user-beta"),
        )
        conn.execute(
            """
            INSERT INTO organizations (organization_id, organization_name, industry, status, owner_user_id)
            VALUES (?, ?, ?, 'active', ?)
            """,
            ("auth-org-beta", "Beta Org", "finance", "user-beta"),
        )
        conn.execute(
            """
            INSERT INTO organization_memberships (membership_id, user_id, organization_id, role, status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            ("membership-beta", "user-beta", "auth-org-beta", "owner"),
        )
        conn.execute(
            """
            INSERT INTO workspaces (
                workspace_id, organization_id, workspace_name, workspace_slug, description, status, purpose, workspace_type
            ) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            """,
            (
                "auth-org-beta::finance",
                "auth-org-beta",
                "Finance",
                "finance",
                "Finance workspace",
                "finance ops",
                "knowledge",
            ),
        )
        conn.commit()


_reset_smoke_db(_TEST_DB_PATH)
os.environ["REGISTRY_DATABASE_PATH"] = str(_TEST_DB_PATH)
os.environ["AUTH_MODE"] = "dev"
os.environ["DEV_USER_ID"] = "user-alpha"

from ai_knowledge_assistant.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def cleanup_smoke_db():
    yield
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_me_organizations(client: TestClient):
    r = client.get("/me/organizations")
    assert r.status_code == 200
    data = r.json()
    assert "organizations" in data
    assert isinstance(data["organizations"], list)
    assert len(data["organizations"]) >= 1


def test_health_ready(client: TestClient):
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert "components" in body


def test_chat_without_rag_returns_503(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("PINECONE_INDEX_HOST", raising=False)
    monkeypatch.delenv("PINECONE_INDEX_NAME", raising=False)
    r = client.post(
        "/workspaces/auth-org-alpha::support/chat",
        json={"messages": [{"role": "user", "content": "Hello"}]},
    )
    assert r.status_code == 503


def test_create_organization_workspace_and_invite_member(client: TestClient):
    created_org = client.post(
        "/organizations",
        json={"organization_name": "Gamma Org", "industry": "healthcare"},
    )
    assert created_org.status_code == 200
    org = created_org.json()["organization"]
    organization_id = org["organization_id"]
    default_workspace_id = org["default_workspace"]["workspace_id"]

    created_workspace = client.post(
        f"/organizations/{organization_id}/workspaces",
        json={
            "workspace_name": "Policies",
            "description": "Policy workspace",
            "purpose": "Answer policy questions",
            "workspace_type": "knowledge",
        },
    )
    assert created_workspace.status_code == 200
    workspace_id = created_workspace.json()["workspace"]["workspace_id"]

    invited = client.post(
        f"/organizations/{organization_id}/members/invite",
        json={
            "email": "new.member@example.com",
            "display_name": "New Member",
            "role": "member",
            "workspace_ids": [workspace_id],
        },
    )
    assert invited.status_code == 200
    member = invited.json()["member"]
    assert member["email"] == "new.member@example.com"
    assert workspace_id in member["workspace_ids"]

    members = client.get(f"/organizations/{organization_id}/members")
    assert members.status_code == 200
    payload = members.json()["members"]
    emails = {row["email"] for row in payload}
    assert "new.member@example.com" in emails
    assert any(default_workspace_id == wid for row in payload for wid in row["workspace_ids"]) is True


def test_cross_org_workspace_access_returns_404(client: TestClient):
    r = client.get("/workspaces/auth-org-beta::finance/documents")
    assert r.status_code == 404


def test_workspace_file_upload_queues_ingest_job(client: TestClient):
    upload = client.post(
        "/workspaces/auth-org-alpha::support/upload",
        data={"namespace": "knowledge"},
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert upload.status_code == 200
    body = upload.json()
    assert body["status"] == "queued"
    assert body["filename"] == "notes.txt"
    assert body["bytes"] == 11
