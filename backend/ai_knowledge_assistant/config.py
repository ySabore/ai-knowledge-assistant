"""Runtime configuration (env-driven)."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


def registry_db_path() -> Path:
    raw = os.environ.get("REGISTRY_DATABASE_PATH", "").strip()
    if raw:
        return Path(raw).expanduser()
    return PROJECT_ROOT / "app.db"


def cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


def dev_bearer_token() -> str:
    return os.environ.get("DEV_BEARER_TOKEN", "dev-local-token")


def dev_user_id() -> str | None:
    v = os.environ.get("DEV_USER_ID", "").strip()
    return v or None


# --- RAG / LLM (enterprise: all secrets and endpoints from env) ---


def llm_provider() -> str:
    """Chat model: `openai` (default), `anthropic`, or `ollama` for local development."""
    return os.environ.get("LLM_PROVIDER", "openai").strip().lower()


def embedding_provider() -> str:
    """Embeddings must match Pinecone index dimension. `openai` or `ollama`."""
    return os.environ.get("EMBEDDING_PROVIDER", "openai").strip().lower()


def openai_api_key() -> str | None:
    v = os.environ.get("OPENAI_API_KEY", "").strip()
    return v or None


def openai_chat_model() -> str:
    return os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip()


def openai_embedding_model() -> str:
    return os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()


def ollama_base_url() -> str:
    return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def ollama_chat_model() -> str:
    return os.environ.get("OLLAMA_CHAT_MODEL", "llama3.2").strip()


def ollama_embedding_model() -> str:
    return os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text").strip()


def anthropic_api_key() -> str | None:
    v = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return v or None


def anthropic_chat_model() -> str:
    return os.environ.get("ANTHROPIC_CHAT_MODEL", "claude-3-5-sonnet-20241022").strip()


def pinecone_api_key() -> str | None:
    v = os.environ.get("PINECONE_API_KEY", "").strip()
    return v or None


def pinecone_index_host() -> str | None:
    """Serverless / dedicated: full host URL from the Pinecone console (preferred)."""
    v = os.environ.get("PINECONE_INDEX_HOST", "").strip()
    return v or None


def pinecone_index_name() -> str | None:
    """Legacy / name-only index handle (used when host is not set)."""
    v = os.environ.get("PINECONE_INDEX_NAME", "").strip()
    return v or None


def pinecone_embedding_dimension() -> int:
    """Must match the index dimension. OpenAI text-embedding-3-small default: 1536; nomic-embed-text: 768."""
    raw = os.environ.get("PINECONE_EMBEDDING_DIMENSION", "").strip()
    if raw:
        return int(raw)
    return 1536 if embedding_provider() == "openai" else 768


def rag_retrieval_limit() -> int:
    return max(2, int(os.environ.get("RAG_RETRIEVAL_LIMIT", "8")))


def rag_chunk_size() -> int:
    return max(256, int(os.environ.get("RAG_CHUNK_SIZE", "1200")))


def rag_chunk_overlap() -> int:
    return max(0, int(os.environ.get("RAG_CHUNK_OVERLAP", "150")))


def rag_temperature() -> float:
    return float(os.environ.get("RAG_TEMPERATURE", "0.2"))


def ingest_poll_interval_seconds() -> float:
    return max(1.0, float(os.environ.get("INGEST_POLL_INTERVAL_SECONDS", "5")))


def ingest_allowed_roots() -> list[Path]:
    raw = os.environ.get("INGEST_ALLOWED_PATHS", "").strip()
    if raw:
        return [Path(p.strip()).expanduser().resolve() for p in raw.split(",") if p.strip()]
    return [(PROJECT_ROOT / "demos").resolve()]


def metadata_text_max_chars() -> int:
    return max(1000, int(os.environ.get("RAG_METADATA_TEXT_MAX_CHARS", "12000")))


def rag_configuration_errors() -> list[str]:
    """Human-readable missing/invalid configuration for RAG."""
    errors: list[str] = []
    if not pinecone_api_key():
        errors.append("PINECONE_API_KEY is not set")
    if not pinecone_index_host() and not pinecone_index_name():
        errors.append("Set PINECONE_INDEX_HOST (serverless) or PINECONE_INDEX_NAME")
    ep = embedding_provider()
    if ep == "openai" and not openai_api_key():
        errors.append("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
    if ep not in ("openai", "ollama"):
        errors.append("EMBEDDING_PROVIDER must be openai or ollama")
    lp = llm_provider()
    if lp == "openai" and not openai_api_key():
        errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
    if lp == "anthropic" and not anthropic_api_key():
        errors.append("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
    if lp not in ("openai", "anthropic", "ollama"):
        errors.append("LLM_PROVIDER must be openai, anthropic, or ollama")
    return errors


def rag_is_configured() -> bool:
    return len(rag_configuration_errors()) == 0


def env_file_paths() -> list[Path]:
    """Locations tried by `load_env_files` in startup."""
    return [
        PROJECT_ROOT / ".env",
        BACKEND_DIR / ".env",
    ]
