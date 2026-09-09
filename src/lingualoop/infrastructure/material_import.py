from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lingualoop.core.domain import MaterialSourceType


@dataclass(frozen=True)
class ImportedMaterial:
    title: str
    raw_content: str
    normalized_content: str
    source_type: MaterialSourceType
    source_path: str
    diagnostics: list[str]


def import_material_file(path: Path | str) -> ImportedMaterial:
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise FileNotFoundError(f"Material file does not exist: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        raw = file_path.read_text(encoding="utf-8")
        source_type = MaterialSourceType.ARTICLE
    elif suffix == ".docx":
        raw = _read_docx(file_path)
        source_type = MaterialSourceType.NOTE
    else:
        raise ValueError("Only .md, .markdown, and .docx files are supported.")

    normalized, diagnostics = normalize_material(raw, suffix)
    if not normalized:
        raise ValueError("The selected material does not contain readable text.")
    return ImportedMaterial(
        title=file_path.stem.replace("_", " ").replace("-", " ").strip() or "Imported material",
        raw_content=raw,
        normalized_content=normalized,
        source_type=source_type,
        source_path=str(file_path.resolve()),
        diagnostics=diagnostics,
    )


def normalize_material(raw: str, suffix: str = ".md") -> tuple[str, list[str]]:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    diagnostics: list[str] = []
    if suffix in {".md", ".markdown"}:
        text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)
        text = re.sub(r"```[\w-]*\n(.*?)```", r"\1", text, flags=re.DOTALL)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
        diagnostics.append("Removed Markdown formatting while preserving readable text.")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    normalized = "\n".join(line.strip() for line in text.splitlines()).strip()
    if normalized != raw.strip():
        diagnostics.append("Created a lesson-ready normalized copy; raw content is preserved.")
    return normalized, diagnostics


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX import requires the python-docx dependency.") from exc

    document = Document(path)
    blocks = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            values = [cell.text.strip() for cell in row.cells]
            if any(values):
                blocks.append(" | ".join(values))
    return "\n\n".join(blocks)
