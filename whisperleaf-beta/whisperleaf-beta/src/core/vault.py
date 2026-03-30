"""
Vault management system for secure document storage and retrieval.
"""

import os
import hashlib
import shutil
from typing import List, Optional, Dict, Any
from pathlib import Path
import mimetypes
from datetime import datetime

from sqlalchemy.orm import Session
from .models import Document, User
from .database import get_db

class VaultManager:
    """Manages secure document storage and retrieval in the vault."""
    
    def __init__(self, vault_path: str = "./data/vault"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # Allowed file types for security
        self.allowed_extensions = {
            '.txt', '.md', '.pdf', '.docx', '.doc', '.html', '.htm',
            '.json', '.xml', '.csv', '.rtf', '.odt'
        }
        
        # Maximum file size (100MB by default)
        self.max_file_size = 100 * 1024 * 1024
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_safe_filename(self, filename: str, document_id: str) -> str:
        """Generate a safe filename for storage."""
        # Remove potentially dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_"
        safe_filename = "".join(c for c in filename if c in safe_chars)
        
        # Ensure we have an extension
        if not safe_filename:
            safe_filename = "document"
        
        # Add document ID to ensure uniqueness
        name, ext = os.path.splitext(safe_filename)
        return f"{document_id}_{name}{ext}"
    
    def _validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate file before adding to vault."""
        if not file_path.exists():
            raise ValueError("File does not exist")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")
        
        # Check file extension
        file_extension = file_path.suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"File type '{file_extension}' is not allowed")
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"
        
        return {
            "size": file_size,
            "extension": file_extension,
            "mime_type": mime_type
        }
    
    def add_document(
        self,
        file_path: str,
        title: str,
        user_id: str,
        db: Session,
        source_url: Optional[str] = None,
        source_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Add a document to the vault."""
        source_path = Path(file_path)
        
        # Validate the file
        file_info = self._validate_file(source_path)
        
        # Create document record
        document = Document(
            title=title,
            content_type=file_info["mime_type"],
            file_path="",  # Will be set after copying
            file_size=file_info["size"],
            source_url=source_url,
            source_type=source_type,
            tags=tags or [],
            metadata_json=metadata or {},
            user_id=user_id
        )
        
        # Add to database to get ID
        db.add(document)
        db.flush()  # Get the ID without committing
        
        # Generate safe filename and copy file
        safe_filename = self._get_safe_filename(source_path.name, document.id)
        vault_file_path = self.vault_path / safe_filename
        
        # Copy file to vault
        shutil.copy2(source_path, vault_file_path)
        
        # Calculate hash and update document
        document.content_hash = self._calculate_file_hash(vault_file_path)
        document.file_path = str(vault_file_path)
        
        # Commit the transaction
        db.commit()
        db.refresh(document)
        
        return document
    
    def get_document(self, document_id: str, user_id: str, db: Session) -> Optional[Document]:
        """Retrieve a document by ID."""
        return db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
    
    def list_documents(
        self,
        user_id: str,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        tags: Optional[List[str]] = None,
        content_type: Optional[str] = None
    ) -> List[Document]:
        """List documents with optional filtering."""
        query = db.query(Document).filter(Document.user_id == user_id)
        
        if tags:
            # Filter by tags (this is a simplified implementation)
            for tag in tags:
                query = query.filter(Document.tags.contains([tag]))
        
        if content_type:
            query = query.filter(Document.content_type == content_type)
        
        return query.offset(skip).limit(limit).all()
    
    def update_document(
        self,
        document_id: str,
        user_id: str,
        db: Session,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Document]:
        """Update document metadata."""
        document = self.get_document(document_id, user_id, db)
        if not document:
            return None
        
        if title is not None:
            document.title = title
        if tags is not None:
            document.tags = tags
        if metadata is not None:
            document.metadata_json = metadata
        
        document.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(document)
        
        return document
    
    def delete_document(self, document_id: str, user_id: str, db: Session) -> bool:
        """Delete a document from the vault."""
        document = self.get_document(document_id, user_id, db)
        if not document:
            return False
        
        # Delete physical file
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        db.delete(document)
        db.commit()
        
        return True
    
    def get_document_content(self, document_id: str, user_id: str, db: Session) -> Optional[bytes]:
        """Get the raw content of a document."""
        document = self.get_document(document_id, user_id, db)
        if not document:
            return None
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            return None
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    def verify_document_integrity(self, document_id: str, user_id: str, db: Session) -> bool:
        """Verify the integrity of a document using its hash."""
        document = self.get_document(document_id, user_id, db)
        if not document:
            return False
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            return False
        
        current_hash = self._calculate_file_hash(file_path)
        return current_hash == document.content_hash
    
    def get_vault_statistics(self, user_id: str, db: Session) -> Dict[str, Any]:
        """Get statistics about the user's vault."""
        documents = self.list_documents(user_id, db, limit=None)
        
        total_documents = len(documents)
        total_size = sum(doc.file_size or 0 for doc in documents)
        
        # Count by content type
        content_types = {}
        for doc in documents:
            content_type = doc.content_type
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "content_types": content_types,
            "vault_path": str(self.vault_path)
        }

