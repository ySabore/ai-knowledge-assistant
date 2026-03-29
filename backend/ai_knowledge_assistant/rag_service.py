"""Orchestrate retrieval + LLM for workspace chat."""

from __future__ import annotations

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from . import config
from .retrieval import retrieve

SYSTEM_RAG = (
    "You are an enterprise knowledge assistant. Answer using the provided context from the "
    "organization's documents. If the context does not contain enough information, say so "
    "clearly and do not invent facts. When helpful, refer to sources by their bracket numbers."
)


def _build_chat_model():
    lp = config.llm_provider()
    if lp == "ollama":
        return ChatOllama(
            model=config.ollama_chat_model(),
            base_url=config.ollama_base_url(),
            temperature=config.rag_temperature(),
        )
    if lp == "anthropic":
        key = config.anthropic_api_key()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for Anthropic chat")
        return ChatAnthropic(
            model=config.anthropic_chat_model(),
            api_key=key,
            temperature=config.rag_temperature(),
        )
    key = config.openai_api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required for OpenAI chat")
    return ChatOpenAI(
        model=config.openai_chat_model(),
        api_key=key,
        temperature=config.rag_temperature(),
    )


def _format_context(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(No matching document excerpts were retrieved for this workspace.)"
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        src = c.get("source") or "unknown"
        body = (c.get("text") or "").strip()
        parts.append(f"[{i}] source={src}\n{body}")
    return "\n\n---\n\n".join(parts)


def _sources_payload(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for c in chunks:
        key = (c.get("document_id"), c.get("chunk_number"), c.get("source"))
        if key in seen:
            continue
        seen.add(key)
        text = c.get("text") or ""
        out.append(
            {
                "document_id": c.get("document_id"),
                "source": c.get("source"),
                "namespace": c.get("namespace"),
                "score": c.get("score"),
                "snippet": text[:800],
            }
        )
    return out


def _to_lc_messages(raw: list[dict[str, Any]], context_block: str) -> list[Any]:
    system_parts = [SYSTEM_RAG, "Context excerpts:\n" + context_block]
    rest: list[Any] = []
    for m in raw:
        role = str(m.get("role") or "user").lower()
        content = str(m.get("content") or "")
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            rest.append(AIMessage(content=content))
        else:
            rest.append(HumanMessage(content=content))
    combined = "\n\n".join(system_parts)
    return [SystemMessage(content=combined)] + rest


def last_user_text(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if str(m.get("role") or "").lower() == "user":
            return str(m.get("content") or "")
    return ""


def run_rag_chat(
    messages: list[dict[str, Any]],
    workspace_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    query = last_user_text(messages)
    chunks = retrieve(query, workspace_id, limit=config.rag_retrieval_limit())
    context = _format_context(chunks)
    lc_messages = _to_lc_messages(messages, context)
    model = _build_chat_model()
    out = model.invoke(lc_messages)
    text = out.content if isinstance(out.content, str) else str(out.content)
    return text, _sources_payload(chunks)
