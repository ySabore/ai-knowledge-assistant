from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(_BACKEND))

os.environ.setdefault("REGISTRY_DATABASE_PATH", str(_BACKEND.parent / "app.db"))
os.environ.setdefault("DEV_USER_ID", "user-alpha")

from ai_knowledge_assistant.main import app  # noqa: E402


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
