"""
Minimal document processor stub for vault processing.
"""

from pathlib import Path
from typing import Dict, Any, List


class DocumentProcessor:
    """Minimal stub for document processing."""

    def __init__(self) -> None:
        pass

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document file. Returns dict with processing_status, text, word_count."""
        return {
            "processing_status": "success",
            "text": "",
            "word_count": 0,
        }

    def get_supported_types(self) -> List[str]:
        """Return list of supported file type extensions."""
        return [".txt", ".md"]
