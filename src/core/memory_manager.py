"""
WhisperLeaf Memory Manager
Secure storage and management of emotional memories
"""

import sqlite3
import json
import os
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging
from cryptography.fernet import Fernet
import base64

from .memory_models import (
    MemoryEntry, JournalEntry, EmotionalMemory, MemoryPattern,
    MemoryType, PrivacyLevel, MemoryStats
)

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Secure memory management system for WhisperLeaf
    Handles storage, retrieval, and management of emotional memories
    """
    
    def __init__(self, data_dir: str = "data", encryption_key: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Database setup
        self.db_path = self.data_dir / "memories.db"
        self.connection = None
        
        # Encryption setup
        self.encryption_key = encryption_key
        self.cipher = None
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"MemoryManager initialized with database at {self.db_path}")
    
    def _initialize_database(self):
        """Initialize SQLite database with memory tables"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        
        cursor = self.connection.cursor()
        
        # Main memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                emotional_context TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                privacy_level TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                accessed_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                related_memories TEXT,
                vector_embedding TEXT,
                encrypted BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Journal entries table (extends memories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                memory_id TEXT PRIMARY KEY,
                prompt TEXT,
                reflection_questions TEXT,
                insights TEXT,
                goals TEXT,
                gratitude TEXT,
                challenges TEXT,
                mood_before TEXT,
                mood_after TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories (id)
            )
        """)
        
        # Emotional memories table (extends memories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emotional_memories (
                memory_id TEXT PRIMARY KEY,
                trigger_event TEXT NOT NULL,
                emotional_response TEXT NOT NULL,
                coping_strategies TEXT,
                lessons_learned TEXT,
                growth_indicators TEXT,
                support_received TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories (id)
            )
        """)
        
        # Memory patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                confidence REAL NOT NULL,
                supporting_memories TEXT,
                insights TEXT,
                recommendations TEXT,
                first_detected TEXT NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        
        # Memory relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id_1 TEXT NOT NULL,
                memory_id_2 TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                FOREIGN KEY (memory_id_1) REFERENCES memories (id),
                FOREIGN KEY (memory_id_2) REFERENCES memories (id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories (created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_privacy ON memories (privacy_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patterns_type ON memory_patterns (pattern_type)")
        
        self.connection.commit()
        logger.info("Database initialized successfully")
    
    def _encrypt_content(self, content: str) -> str:
        """Encrypt sensitive content"""
        if not self.cipher:
            return content
        return base64.b64encode(self.cipher.encrypt(content.encode())).decode()
    
    def _decrypt_content(self, encrypted_content: str) -> str:
        """Decrypt sensitive content"""
        if not self.cipher:
            return encrypted_content
        try:
            return self.cipher.decrypt(base64.b64decode(encrypted_content.encode())).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt content: {e}")
            return "[ENCRYPTED CONTENT - DECRYPTION FAILED]"
    
    def store_memory(self, memory: MemoryEntry) -> bool:
        """
        Store a memory entry in the vault
        
        Args:
            memory: MemoryEntry to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            
            # Encrypt content if privacy level requires it
            content = memory.content
            encrypted = False
            if memory.privacy_level == PrivacyLevel.ENCRYPTED:
                content = self._encrypt_content(content)
                encrypted = True
            
            # Store base memory
            cursor.execute("""
                INSERT OR REPLACE INTO memories (
                    id, memory_type, title, content, emotional_context,
                    metadata_json, privacy_level, created_at, updated_at,
                    accessed_count, last_accessed, related_memories,
                    vector_embedding, encrypted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory.id,
                memory.memory_type.value,
                memory.title,
                content,
                json.dumps(memory.emotional_context.to_dict()),
                json.dumps(memory.metadata.to_dict()),
                memory.privacy_level.value,
                memory.created_at.isoformat(),
                memory.updated_at.isoformat(),
                memory.accessed_count,
                memory.last_accessed.isoformat() if memory.last_accessed else None,
                json.dumps(memory.related_memories),
                json.dumps(memory.vector_embedding) if memory.vector_embedding else None,
                encrypted
            ))
            
            # Store specialized data based on memory type
            if isinstance(memory, JournalEntry):
                self._store_journal_entry(memory)
            elif isinstance(memory, EmotionalMemory):
                self._store_emotional_memory(memory)
            
            self.connection.commit()
            logger.info(f"Stored memory: {memory.id} ({memory.memory_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {memory.id}: {e}")
            self.connection.rollback()
            return False
    
    def _store_journal_entry(self, journal: JournalEntry):
        """Store journal-specific data"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO journal_entries (
                memory_id, prompt, reflection_questions, insights,
                goals, gratitude, challenges, mood_before, mood_after
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            journal.id,
            journal.prompt,
            json.dumps(journal.reflection_questions),
            json.dumps(journal.insights),
            json.dumps(journal.goals),
            json.dumps(journal.gratitude),
            json.dumps(journal.challenges),
            journal.mood_before,
            journal.mood_after
        ))
    
    def _store_emotional_memory(self, emotional_memory: EmotionalMemory):
        """Store emotional memory specific data"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO emotional_memories (
                memory_id, trigger_event, emotional_response,
                coping_strategies, lessons_learned, growth_indicators,
                support_received
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            emotional_memory.memory_entry.id,
            emotional_memory.trigger_event,
            emotional_memory.emotional_response,
            json.dumps(emotional_memory.coping_strategies),
            json.dumps(emotional_memory.lessons_learned),
            json.dumps(emotional_memory.growth_indicators),
            json.dumps(emotional_memory.support_received)
        ))
    
    def retrieve_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        Retrieve a memory by ID
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            MemoryEntry or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Decrypt content if necessary
            content = row['content']
            if row['encrypted']:
                content = self._decrypt_content(content)
            
            # Create base memory entry
            memory_data = {
                'id': row['id'],
                'memory_type': row['memory_type'],
                'title': row['title'],
                'content': content,
                'emotional_context': json.loads(row['emotional_context']),
                'metadata': json.loads(row['metadata_json']),
                'privacy_level': row['privacy_level'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'accessed_count': row['accessed_count'],
                'last_accessed': row['last_accessed'],
                'related_memories': json.loads(row['related_memories']) if row['related_memories'] else [],
                'vector_embedding': json.loads(row['vector_embedding']) if row['vector_embedding'] else None
            }
            
            # Load specialized data based on type
            memory_type = MemoryType(row['memory_type'])
            
            if memory_type == MemoryType.JOURNAL_ENTRY:
                return self._load_journal_entry(memory_data)
            elif memory_type == MemoryType.EMOTIONAL_EVENT:
                return self._load_emotional_memory(memory_data)
            else:
                return MemoryEntry.from_dict(memory_data)
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory {memory_id}: {e}")
            return None
    
    def _load_journal_entry(self, memory_data: Dict) -> JournalEntry:
        """Load journal entry with specialized data"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM journal_entries WHERE memory_id = ?", (memory_data['id'],))
        journal_row = cursor.fetchone()
        
        if journal_row:
            memory_data.update({
                'prompt': journal_row['prompt'],
                'reflection_questions': json.loads(journal_row['reflection_questions']) if journal_row['reflection_questions'] else [],
                'insights': json.loads(journal_row['insights']) if journal_row['insights'] else [],
                'goals': json.loads(journal_row['goals']) if journal_row['goals'] else [],
                'gratitude': json.loads(journal_row['gratitude']) if journal_row['gratitude'] else [],
                'challenges': json.loads(journal_row['challenges']) if journal_row['challenges'] else [],
                'mood_before': journal_row['mood_before'],
                'mood_after': journal_row['mood_after']
            })
        
        return JournalEntry.from_dict(memory_data)
    
    def _load_emotional_memory(self, memory_data: Dict) -> EmotionalMemory:
        """Load emotional memory with specialized data"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM emotional_memories WHERE memory_id = ?", (memory_data['id'],))
        emotional_row = cursor.fetchone()
        
        if emotional_row:
            emotional_data = {
                'memory_entry': memory_data,
                'trigger_event': emotional_row['trigger_event'],
                'emotional_response': emotional_row['emotional_response'],
                'coping_strategies': json.loads(emotional_row['coping_strategies']) if emotional_row['coping_strategies'] else [],
                'lessons_learned': json.loads(emotional_row['lessons_learned']) if emotional_row['lessons_learned'] else [],
                'growth_indicators': json.loads(emotional_row['growth_indicators']) if emotional_row['growth_indicators'] else [],
                'support_received': json.loads(emotional_row['support_received']) if emotional_row['support_received'] else []
            }
            return EmotionalMemory.from_dict(emotional_data)
        
        # Fallback to regular memory entry
        return MemoryEntry.from_dict(memory_data)
    
    def search_memories(self, query: str = "", memory_type: Optional[MemoryType] = None,
                       privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
                       date_range: Optional[Tuple[datetime, datetime]] = None,
                       tags: Optional[List[str]] = None,
                       limit: int = 50) -> List[MemoryEntry]:
        """
        Search memories with various filters
        
        Args:
            query: Text search query
            memory_type: Filter by memory type
            privacy_level: Maximum privacy level to include
            date_range: Tuple of (start_date, end_date)
            tags: List of tags to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching MemoryEntry objects
        """
        try:
            cursor = self.connection.cursor()
            
            # Build query
            sql = "SELECT * FROM memories WHERE 1=1"
            params = []
            
            # Privacy filter
            privacy_hierarchy = {
                PrivacyLevel.PUBLIC: ['public'],
                PrivacyLevel.PRIVATE: ['public', 'private'],
                PrivacyLevel.CONFIDENTIAL: ['public', 'private', 'confidential'],
                PrivacyLevel.ENCRYPTED: ['public', 'private', 'confidential', 'encrypted']
            }
            allowed_privacy = privacy_hierarchy[privacy_level]
            placeholders = ','.join(['?' for _ in allowed_privacy])
            sql += f" AND privacy_level IN ({placeholders})"
            params.extend(allowed_privacy)
            
            # Memory type filter
            if memory_type:
                sql += " AND memory_type = ?"
                params.append(memory_type.value)
            
            # Date range filter
            if date_range:
                sql += " AND created_at BETWEEN ? AND ?"
                params.extend([date_range[0].isoformat(), date_range[1].isoformat()])
            
            # Text search
            if query:
                sql += " AND (title LIKE ? OR content LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
            
            # Tags filter (search in metadata)
            if tags:
                for tag in tags:
                    sql += " AND metadata_json LIKE ?"
                    params.append(f"%{tag}%")
            
            # Order and limit
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert to memory objects
            memories = []
            for row in rows:
                memory = self.retrieve_memory(row['id'])
                if memory:
                    memories.append(memory)
            
            logger.info(f"Found {len(memories)} memories matching search criteria")
            return memories
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    def get_recent_memories(self, days: int = 7, limit: int = 20) -> List[MemoryEntry]:
        """Get recent memories from the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.search_memories(date_range=(start_date, end_date), limit=limit)
    
    def get_memories_by_mood(self, mood: str, limit: int = 20) -> List[MemoryEntry]:
        """Get memories associated with a specific mood"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM memories 
                WHERE emotional_context LIKE ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (f"%{mood}%", limit))
            
            rows = cursor.fetchall()
            memories = []
            for row in rows:
                memory = self.retrieve_memory(row['id'])
                if memory:
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to get memories by mood {mood}: {e}")
            return []
    
    def update_memory(self, memory: MemoryEntry) -> bool:
        """Update an existing memory"""
        memory.updated_at = datetime.now()
        return self.store_memory(memory)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory and all associated data
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cursor = self.connection.cursor()
            
            # Delete from specialized tables first
            cursor.execute("DELETE FROM journal_entries WHERE memory_id = ?", (memory_id,))
            cursor.execute("DELETE FROM emotional_memories WHERE memory_id = ?", (memory_id,))
            cursor.execute("DELETE FROM memory_relationships WHERE memory_id_1 = ? OR memory_id_2 = ?", 
                         (memory_id, memory_id))
            
            # Delete main memory
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            
            self.connection.commit()
            logger.info(f"Deleted memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id}: {e}")
            self.connection.rollback()
            return False
    
    def get_memory_stats(self) -> MemoryStats:
        """Get statistics about the memory vault"""
        try:
            cursor = self.connection.cursor()
            stats = MemoryStats()
            
            # Total memories
            cursor.execute("SELECT COUNT(*) as count FROM memories")
            stats.total_memories = cursor.fetchone()['count']
            
            # Memory types distribution
            cursor.execute("SELECT memory_type, COUNT(*) as count FROM memories GROUP BY memory_type")
            stats.memory_types = {row['memory_type']: row['count'] for row in cursor.fetchall()}
            
            # Privacy distribution
            cursor.execute("SELECT privacy_level, COUNT(*) as count FROM memories GROUP BY privacy_level")
            stats.privacy_distribution = {row['privacy_level']: row['count'] for row in cursor.fetchall()}
            
            # Most accessed memory
            cursor.execute("SELECT id, accessed_count FROM memories ORDER BY accessed_count DESC LIMIT 1")
            most_accessed = cursor.fetchone()
            if most_accessed:
                stats.most_accessed_memory = most_accessed['id']
            
            # Date range
            cursor.execute("SELECT MIN(created_at) as oldest, MAX(created_at) as newest FROM memories")
            date_range = cursor.fetchone()
            if date_range['oldest']:
                stats.oldest_memory = datetime.fromisoformat(date_range['oldest'])
            if date_range['newest']:
                stats.newest_memory = datetime.fromisoformat(date_range['newest'])
            
            # Database size
            stats.total_size_bytes = os.path.getsize(self.db_path)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return MemoryStats()
    
    def create_memory_relationship(self, memory_id_1: str, memory_id_2: str, 
                                 relationship_type: str, strength: float = 0.5) -> bool:
        """Create a relationship between two memories"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO memory_relationships (
                    memory_id_1, memory_id_2, relationship_type, strength, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (memory_id_1, memory_id_2, relationship_type, strength, datetime.now().isoformat()))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create memory relationship: {e}")
            return False
    
    def get_related_memories(self, memory_id: str, limit: int = 10) -> List[MemoryEntry]:
        """Get memories related to a specific memory"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT CASE 
                    WHEN memory_id_1 = ? THEN memory_id_2 
                    ELSE memory_id_1 
                END as related_id, strength
                FROM memory_relationships 
                WHERE memory_id_1 = ? OR memory_id_2 = ?
                ORDER BY strength DESC 
                LIMIT ?
            """, (memory_id, memory_id, memory_id, limit))
            
            related_memories = []
            for row in cursor.fetchall():
                memory = self.retrieve_memory(row['related_id'])
                if memory:
                    related_memories.append(memory)
            
            return related_memories
            
        except Exception as e:
            logger.error(f"Failed to get related memories for {memory_id}: {e}")
            return []
    
    def backup_memories(self, backup_path: str) -> bool:
        """Create a backup of all memories"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Memory backup created at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup memories: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Memory manager connection closed")

