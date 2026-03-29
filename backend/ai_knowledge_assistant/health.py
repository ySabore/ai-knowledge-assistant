"""Liveness and readiness endpoints."""

from __future__ import annotations

from . import config


def live() -> dict:
    return {"status": "ok"}


def ready(deep: bool = False) -> dict:
    """Readiness: registry DB reachable; RAG env complete. Optional deep Pinecone ping."""
    out: dict = {"status": "ready", "components": {}}
    db_path = config.registry_db_path()
    db_ok = db_path.is_file()
    out["components"]["registry_db"] = {"ok": db_ok, "path": str(db_path)}
    rag_errors = config.rag_configuration_errors()
    out["components"]["rag_env"] = {"ok": len(rag_errors) == 0, "errors": rag_errors}
    if not db_ok or rag_errors:
        out["status"] = "not_ready"
    elif deep and config.rag_is_configured():
        try:
            from .vectorstore import pinecone_ping

            out["components"]["pinecone"] = pinecone_ping()
        except Exception as e:
            out["components"]["pinecone"] = {"ok": False, "error": type(e).__name__}
            out["status"] = "degraded"
    return out
