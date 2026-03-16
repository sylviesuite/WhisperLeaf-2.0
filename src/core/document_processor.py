"""
Document processing: extract text and split into chunks for embedding.
"""

from pathlib import Path
import re
from typing import Any, Dict, List

# Chunk size and overlap (chars)
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80
SUPPORTED_EXTENSIONS = [".txt", ".md", ".markdown"]


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    text = (text or "").strip()
    if not text:
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if end < len(text):
            last_break = max(
                chunk.rfind("\n\n"),
                chunk.rfind("\n"),
                chunk.rfind(". "),
                chunk.rfind(" "),
            )
            if last_break > chunk_size // 2:
                chunk = chunk[: last_break + 1]
                end = start + len(chunk)
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap if overlap < end - start else end
    return chunks


class DocumentProcessor:
    """Extract text from supported files and chunk for vector store."""

    def __init__(self) -> None:
        pass

    def get_supported_types(self) -> List[str]:
        """Return list of supported file type extensions."""
        return list(SUPPORTED_EXTENSIONS)

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Read document and return extracted text plus chunks.
        Returns dict: processing_status, text, word_count, chunks (list of strings).
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return {
                "processing_status": "error",
                "text": "",
                "word_count": 0,
                "chunks": [],
            }
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return {
                "processing_status": "unsupported_type",
                "text": "",
                "word_count": 0,
                "chunks": [],
            }
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {
                "processing_status": "error",
                "text": "",
                "word_count": 0,
                "chunks": [],
            }
        text = re.sub(r"\r\n", "\n", raw).strip()
        word_count = len(text.split())
        chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        return {
            "processing_status": "success",
            "text": text,
            "word_count": word_count,
            "chunks": chunks,
        }
