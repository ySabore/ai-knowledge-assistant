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
        conn.commit()


_reset_smoke_db(_TEST_DB_PATH)
os.environ["REGISTRY_DATABASE_PATH"] = str(_TEST_DB_PATH)
os.environ.setdefault("DEV_USER_ID", "user-alpha")

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
