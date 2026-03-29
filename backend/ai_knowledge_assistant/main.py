from __future__ import annotations

import logging

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import admin, chat, config, documents, health, ingest, me
from .middleware.request_context import RequestContextMiddleware
from .startup import lifespan, load_env_files

load_env_files()

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Knowledge Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

app.include_router(me.router, prefix="/me", tags=["me"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(documents.router, prefix="/workspaces", tags=["documents"])
app.include_router(chat.router, prefix="/workspaces", tags=["chat"])
app.include_router(ingest.router, prefix="/workspaces", tags=["ingest"])


@app.get("/health")
def health_live():
    return health.live()


@app.get("/health/ready")
def health_ready(
    deep: bool = Query(False, description="If true, ping Pinecone (requires network)."),
):
    return health.ready(deep=deep)
