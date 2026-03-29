from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_env_files()
    logger.info("Registry DB at %s", config.registry_db_path())
    if config.rag_is_configured():
        logger.info("RAG stack configured (LLM=%s, embeddings=%s)", config.llm_provider(), config.embedding_provider())
    else:
        logger.warning("RAG not fully configured: %s", "; ".join(config.rag_configuration_errors()))
    yield
