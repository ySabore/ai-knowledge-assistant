#!/usr/bin/env python3
"""
Normalize text files to UTF-8 (no BOM). Safe for UTF-16 / UTF-8 BOM inputs.

Usage (from repo root):
  python3 scripts/normalize-text-encoding.py           # write changes
  python3 scripts/normalize-text-encoding.py --dry-run # list only

Skips: .git, node_modules, .venv, venv, __pycache__, build artifacts, binary extensions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".turbo",
    "coverage",
    "htmlcov",
}

SKIP_EXT = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".pdf",
    ".zip",
    ".sqlite3",
    ".db",
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".mp4",
    ".webm",
    ".mp3",
    ".wasm",
    ".bin",
}

TEXT_EXT = {
    ".md",
    ".txt",
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".cjs",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".xml",
    ".csv",
    ".ini",
    ".cfg",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".html",
    ".htm",
    ".css",
    ".scss",
    ".less",
    ".env",
    ".example",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".sql",
    ".http",
    ".svg",
    ".mdx",
    ".rst",
    ".properties",
    ".gradle",
    ".kts",
}

SPECIAL_NAMES = {
    "Makefile",
    "Dockerfile",
    "Procfile",
    "LICENSE",
    "LICENSE.md",
    "CONTRIBUTING.md",
    "CODEOWNERS",
    "Rakefile",
    "Gemfile",
    "Vagrantfile",
}

MAX_BYTES = 8_000_000


def should_process(path: Path) -> bool:
    name = path.name
    if name.startswith("._") or name == ".DS_Store":
        return False
    suf = path.suffix.lower()
    if suf in SKIP_EXT:
        return False
    if name == "package-lock.json" or name.endswith(".json"):
        return True
    if name.endswith(".example") or name == ".env" or ".env." in name:
        return True
    if suf in TEXT_EXT:
        return True
    if name in SPECIAL_NAMES:
        return True
    return False


def normalize_newlines(text: str) -> str:
    if not text:
        return ""
    return "\n".join(text.splitlines()) + "\n"


def process_file(path: Path, dry: bool) -> tuple[str, str] | None:
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        return None

    how: str
    text: str

    if raw.startswith(b"\xef\xbb\xbf"):
        text = raw[3:].decode("utf-8")
        how = "utf-8-strip-bom"
    elif raw.startswith(b"\xff\xfe"):
        text = raw[2:].decode("utf-16-le")
        how = "utf-16-le-bom"
    elif raw.startswith(b"\xfe\xff"):
        text = raw[2:].decode("utf-16-be")
        how = "utf-16-be-bom"
    else:
        try:
            text = raw.decode("utf-8")
            if "\r" not in text:
                return None
            how = "utf-8-crlf"
        except UnicodeDecodeError:
            if len(raw) % 2 == 0 and len(raw) >= 4:
                try:
                    t2 = raw.decode("utf-16-le")
                    good = sum(1 for c in t2 if c.isprintable() or c in "\n\r\t")
                    if good > len(t2) * 0.75:
                        text = t2
                        how = "utf-16-le-nobom"
                    else:
                        raise ValueError
                except Exception:
                    text = raw.decode("utf-8", errors="replace")
                    how = "utf-8-replace"
            else:
                text = raw.decode("utf-8", errors="replace")
                how = "utf-8-replace"

    out = normalize_newlines(text)
    if dry:
        return how, out

    path.write_text(out, encoding="utf-8", newline="\n")
    return how, out


def main() -> None:
    dry = "--dry-run" in sys.argv
    changed = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if not should_process(p):
                continue
            try:
                r = process_file(p, dry=dry)
                if r is None:
                    continue
                how, _ = r
                print(f"{how}\t{p.relative_to(ROOT)}")
                changed += 1
            except OSError as e:
                print(f"ERR\t{p.relative_to(ROOT)}\t{e}", file=sys.stderr)

    print(f"---\n{'Would update' if dry else 'Updated'} {changed} file(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
