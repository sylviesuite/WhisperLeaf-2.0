"""
Vector store for document chunks. Uses ChromaDB when available for semantic search.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False

# Chunk size and overlap for document splitting (caller may chunk; used here for defaults)
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


class VectorStore:
    """Store and search document chunks via ChromaDB."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._client: Any = None
        self._collection: Any = None
        if _CHROMADB_AVAILABLE:
            self._init_chroma()
        else:
            logger.warning("ChromaDB not available; document search will return no results.")

    def _init_chroma(self) -> None:
        try:
            chroma_path = self.data_dir / "chroma_docs"
            chroma_path.mkdir(exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
            self._collection = self._client.get_or_create_collection(
                name="whisperleaf_documents",
                metadata={"description": "Ingested document chunks for semantic search"},
            )
            logger.info("VectorStore ChromaDB initialized (documents), count=%s", self._collection.count())
        except Exception as e:
            logger.warning("VectorStore ChromaDB init failed: %s", e)
            self._client = None
            self._collection = None

    def add_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store one document chunk (single block of text)."""
        document_id = str(document_id)
        if not self._collection or not content or not document_id:
            return
        meta = dict(metadata or {})
        meta["document_id"] = document_id
        chunk_id = f"{document_id}_c0"
        try:
            self._collection.add(
                ids=[chunk_id],
                documents=[content[:100000]],
                metadatas=[meta],
            )
        except Exception as e:
            logger.warning("VectorStore add_document failed: %s", e)

    def add_chunks(
        self,
        document_id: str,
        chunks: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store multiple chunks for one document."""
        document_id = str(document_id)
        if not self._collection or not document_id or not chunks:
            return
        base_meta = dict(metadata or {})
        base_meta["document_id"] = document_id
        ids = []
        documents = []
        metadatas = []
        for i, text in enumerate(chunks):
            if not (text and str(text).strip()):
                continue
            ids.append(f"{document_id}_c{i}")
            documents.append(str(text).strip()[:100000])
            meta = dict(base_meta)
            meta["chunk_index"] = i
            metadatas.append(meta)
        if not ids:
            return
        try:
            self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as e:
            logger.warning("VectorStore add_chunks failed: %s", e)

    def remove_document(self, document_id: str) -> None:
        """Remove all chunks for this document."""
        document_id = str(document_id)
        if not self._collection or not document_id:
            return
        try:
            self._collection.delete(where={"document_id": {"$eq": document_id}})
        except Exception as e:
            logger.warning("VectorStore remove_document failed: %s", e)

    def search(
        self,
        query: str,
        n_results: int = 10,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search by similarity. Returns list of dicts with content, title, document_id, etc."""
        if not self._collection or not (query and str(query).strip()):
            return []
        try:
            where = {"document_id": {"$in": document_ids}} if document_ids else None
            result = self._collection.query(
                query_texts=[str(query).strip()],
                n_results=min(n_results, 50),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            out: List[Dict[str, Any]] = []
            docs = (result.get("documents") or [[]])[0] or []
            metadatas = (result.get("metadatas") or [[]])[0] or []
            ids = (result.get("ids") or [[]])[0] or []
            for i, doc in enumerate(docs):
                meta = metadatas[i] if i < len(metadatas) else {}
                out.append({
                    "document_id": meta.get("document_id", ""),
                    "title": meta.get("title", ""),
                    "content": doc or "",
                    "path": meta.get("title") or meta.get("document_id", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                })
            return out
        except Exception as e:
            logger.warning("VectorStore search failed: %s", e)
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return collection statistics."""
        if not self._collection:
            return {}
        try:
            n = self._collection.count()
            return {"count": n}
        except Exception:
            return {}
