"""Load plain text from supported file types."""

from __future__ import annotations

from pathlib import Path


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            parts.append(t)
        return "\n\n".join(parts)
    if suffix == ".docx":
        import docx

        doc = docx.Document(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text)
    if suffix in {".html", ".htm"}:
        from bs4 import BeautifulSoup

        raw = path.read_text(encoding="utf-8", errors="replace")
        return BeautifulSoup(raw, "html.parser").get_text(separator="\n", strip=True)
    return path.read_text(encoding="utf-8", errors="replace")
