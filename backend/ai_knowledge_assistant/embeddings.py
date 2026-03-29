"""Embedding backends: OpenAI (hosted) and Ollama (local)."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from . import config


def build_embedder() -> Embeddings:
    if config.embedding_provider() == "ollama":
        return OllamaEmbeddings(
            model=config.ollama_embedding_model(),
            base_url=config.ollama_base_url(),
        )
    key = config.openai_api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI embeddings")
    return OpenAIEmbeddings(
        api_key=key,
        model=config.openai_embedding_model(),
    )


def validate_embedding_dimension(vector: list[float]) -> None:
    expected = config.pinecone_embedding_dimension()
    if len(vector) != expected:
        raise ValueError(
            f"Embedding dimension {len(vector)} does not match PINECONE_EMBEDDING_DIMENSION={expected}"
        )
