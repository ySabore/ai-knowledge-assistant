"""Resolve ingestion sources to files under configured allowlisted roots."""

from __future__ import annotations

from pathlib import Path

from . import config


class PathNotAllowedError(ValueError):
    pass


def resolve_ingestion_file(source: str) -> Path:
    """Allow only files under INGEST_ALLOWED_PATHS (or default `demos/`)."""
    raw = source.strip()
    if not raw:
        raise PathNotAllowedError("empty source")
    candidate = Path(raw).expanduser()
    roots = config.ingest_allowed_roots()
    resolved: Path | None = None
    if candidate.is_absolute():
        rp = candidate.resolve()
        for root in roots:
            root_r = root.resolve()
            try:
                rp.relative_to(root_r)
            except ValueError:
                continue
            if rp.is_file():
                resolved = rp
                break
    else:
        for root in roots:
            rp = (root / candidate).resolve()
            try:
                rp.relative_to(root.resolve())
            except ValueError:
                continue
            if rp.is_file():
                resolved = rp
                break
    if resolved is None:
        raise PathNotAllowedError("source file is not under allowed roots or does not exist")
    return resolved
