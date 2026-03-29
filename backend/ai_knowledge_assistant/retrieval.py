"""Retrieve relevant chunks from Pinecone for a workspace."""

from __future__ import annotations

import logging
from typing import Any

from . import config
from .embeddings import build_embedder, validate_embedding_dimension
from .vectorstore import query_similar

log = logging.getLogger(__name__)


def retrieve(query: str, workspace_id: str, limit: int | None = None) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    lim = limit if limit is not None else config.rag_retrieval_limit()
    embedder = build_embedder()
    vec = embedder.embed_query(query)
    validate_embedding_dimension(vec)
    raw = query_similar(workspace_id, vec, top_k=lim, include_metadata=True)
    out: list[dict[str, Any]] = []
    for row in raw:
        meta = row.get("metadata") or {}
        text = str(meta.get("text") or "")
        out.append(
            {
                "id": row.get("id"),
                "score": row.get("score"),
                "text": text,
                "source": meta.get("source"),
                "namespace": meta.get("namespace"),
                "document_id": meta.get("document_id"),
                "chunk_number": meta.get("chunk_number"),
            }
        )
    return out
