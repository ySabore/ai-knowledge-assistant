"""Pinecone index access (serverless host or index name)."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from pinecone import Pinecone

from . import config

log = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _client() -> Pinecone:
    key = config.pinecone_api_key()
    if not key:
        raise RuntimeError("PINECONE_API_KEY is not set")
    return Pinecone(api_key=key)


@lru_cache(maxsize=1)
def get_index():
    """Return a Pinecone Index handle (cached)."""
    pc = _client()
    host = config.pinecone_index_host()
    name = config.pinecone_index_name()
    if host:
        idx = pc.Index(host=host)
        log.info("Pinecone index connected via host")
        return idx
    if name:
        idx = pc.Index(name)
        log.info("Pinecone index connected via name=%s", name)
        return idx
    raise RuntimeError("PINECONE_INDEX_HOST or PINECONE_INDEX_NAME is required")


def pinecone_ping() -> dict[str, Any]:
    """Lightweight stats call for readiness checks."""
    idx = get_index()
    stats = idx.describe_index_stats()
    return {"ok": True, "namespaces": getattr(stats, "namespaces", None) or str(stats)}


def upsert_vectors(
    workspace_id: str,
    vectors: list[dict[str, Any]],
) -> None:
    """vectors: items with keys id, values, metadata (Pinecone format)."""
    if not vectors:
        return
    idx = get_index()
    idx.upsert(vectors=vectors, namespace=workspace_id, show_progress=False)


def query_similar(
    workspace_id: str,
    vector: list[float],
    top_k: int,
    include_metadata: bool = True,
) -> list[dict[str, Any]]:
    idx = get_index()
    tk = max(2, int(top_k))
    res = idx.query(
        vector=vector,
        top_k=tk,
        namespace=workspace_id,
        include_metadata=include_metadata,
    )
    matches = []
    for m in res.matches or []:
        meta = dict(m.metadata) if m.metadata else {}
        matches.append(
            {
                "id": m.id,
                "score": float(m.score) if m.score is not None else 0.0,
                "metadata": meta,
            }
        )
    return matches
