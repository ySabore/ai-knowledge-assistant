from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
import sqlite3

from dotenv import load_dotenv
from fastapi import FastAPI

from . import config

logger = logging.getLogger(__name__)


def load_env_files() -> None:
    if os.environ.get("PYTHON_DOTENV_DISABLED", "").strip() == "1":
        return
    for path in config.env_file_paths():
        if path.is_file():
            try:
                load_dotenv(path, override=False)
            except UnicodeDecodeError:
                logger.warning("Skipping env file (not valid UTF-8): %s", path)


def ensure_registry_schema() -> None:
    path = config.registry_db_path()
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS workspace_memberships (
                workspace_membership_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'member',
                status TEXT NOT NULL DEFAULT 'active',
                invited_by_user_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(workspace_id, user_id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workspace_memberships_workspace_status
            ON workspace_memberships (workspace_id, status)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workspace_memberships_user_status
            ON workspace_memberships (user_id, status)
            """
        )
        conn.commit()

    config.ingest_spool_dir().mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_env_files()
    ensure_registry_schema()
    logger.info("Registry DB at %s", config.registry_db_path())
    if config.rag_is_configured():
        logger.info("RAG stack configured (LLM=%s, embeddings=%s)", config.llm_provider(), config.embedding_provider())
    else:
        logger.warning("RAG not fully configured: %s", "; ".join(config.rag_configuration_errors()))
    yield
