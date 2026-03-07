"""
Database models for the Sovereign AI system.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    constitutional_rules = relationship("ConstitutionalRule", back_populates="user")
    content_sources = relationship("ContentSource", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")

class Document(Base):
    """Document model for vault content metadata."""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    file_path = Column(Text, nullable=False)
    content_hash = Column(String(64))  # SHA-256 hash for integrity
    file_size = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    source_url = Column(Text)
    source_type = Column(String(50))
    metadata_json = Column(JSON)
    tags = Column(JSON)  # Store as JSON array
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="documents")

class ConstitutionalRule(Base):
    """Constitutional rules for AI governance."""
    __tablename__ = "constitutional_rules"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    rule_text = Column(Text, nullable=False)
    priority = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="constitutional_rules")

class ContentSource(Base):
    """Content sources for the curation engine."""
    __tablename__ = "content_sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # rss, web, api, etc.
    url = Column(Text, nullable=False)
    configuration = Column(JSON)  # Source-specific configuration
    active = Column(Boolean, default=True)
    last_scan = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="content_sources")

class Conversation(Base):
    """Conversation history for chat interface."""
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    """Individual messages within conversations."""
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON)  # Store additional message metadata
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class SystemLog(Base):
    """System logs for audit and monitoring."""
    __tablename__ = "system_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, etc.
    component = Column(String(50), nullable=False)  # vault, airlock, constitution, etc.
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    user_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

class BackupRecord(Base):
    """Records of system backups for time capsule functionality."""
    __tablename__ = "backup_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    backup_type = Column(String(50), nullable=False)  # full, incremental, documents, etc.
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer)
    checksum = Column(String(64))
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

