"""
Minimal vector store stub for document search.
"""

from typing import List, Optional, Dict, Any


class VectorStore:
    """Minimal stub for vector store operations."""

    def __init__(self) -> None:
        pass

    def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store document content for search."""
        pass

    def remove_document(self, document_id: str) -> None:
        """Remove document from the store."""
        pass

    def search(
        self,
        query: str,
        n_results: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search documents by similarity. Returns list of result dicts."""
        return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        return {}
