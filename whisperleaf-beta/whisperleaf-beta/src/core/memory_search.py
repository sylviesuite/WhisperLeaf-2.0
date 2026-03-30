"""
WhisperLeaf Memory Search
Vector-based semantic search for emotional memories
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
import json
import re
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("ChromaDB not available, using fallback search")

from .memory_models import MemoryEntry, MemoryType, PrivacyLevel
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class MemorySearch:
    """
    Advanced semantic search system for emotional memories
    Uses vector embeddings for semantic similarity search
    """
    
    def __init__(self, data_dir: str = "data", memory_manager: Optional[MemoryManager] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.memory_manager = memory_manager
        self.chroma_client = None
        self.collection = None
        
        # Initialize vector database
        if CHROMADB_AVAILABLE:
            self._initialize_chromadb()
        else:
            logger.warning("Using fallback search without vector embeddings")
        
        # Search statistics
        self.search_stats = {
            'total_searches': 0,
            'semantic_searches': 0,
            'keyword_searches': 0,
            'average_results': 0,
            'last_search': None
        }
        
        logger.info("MemorySearch initialized")
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB for vector storage"""
        try:
            # Create ChromaDB client
            chroma_path = self.data_dir / "chroma_db"
            chroma_path.mkdir(exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="whisperleaf_memories",
                metadata={"description": "WhisperLeaf emotional memories with semantic search"}
            )
            
            logger.info(f"ChromaDB initialized with {self.collection.count()} existing memories")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None
    
    def add_memory_to_search(self, memory: MemoryEntry) -> bool:
        """
        Add a memory to the search index
        
        Args:
            memory: MemoryEntry to index
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.collection:
                logger.warning("ChromaDB not available, memory not indexed for semantic search")
                return False
            
            # Prepare text for embedding
            search_text = self._prepare_search_text(memory)
            
            # Create metadata for filtering
            metadata = {
                'memory_type': memory.memory_type.value,
                'privacy_level': memory.privacy_level.value,
                'created_at': memory.created_at.isoformat(),
                'primary_mood': memory.emotional_context.primary_mood,
                'crisis_level': memory.emotional_context.crisis_level,
                'themes': json.dumps(memory.metadata.themes),
                'tags': json.dumps(memory.metadata.tags),
                'sentiment_score': memory.metadata.sentiment_score,
                'importance_score': memory.metadata.importance_score
            }
            
            # Add to collection
            self.collection.add(
                documents=[search_text],
                metadatas=[metadata],
                ids=[memory.id]
            )
            
            logger.debug(f"Added memory {memory.id} to search index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add memory {memory.id} to search index: {e}")
            return False
    
    def _prepare_search_text(self, memory: MemoryEntry) -> str:
        """Prepare text content for embedding and search"""
        
        # Combine title and content
        text_parts = [memory.title, memory.content]
        
        # Add emotional context
        text_parts.append(f"Mood: {memory.emotional_context.primary_mood}")
        if memory.emotional_context.emotions:
            text_parts.append(f"Emotions: {', '.join(memory.emotional_context.emotions)}")
        
        # Add themes and tags
        if memory.metadata.themes:
            text_parts.append(f"Themes: {', '.join(memory.metadata.themes)}")
        if memory.metadata.tags:
            text_parts.append(f"Tags: {', '.join(memory.metadata.tags)}")
        
        # Add insights for journal entries
        if hasattr(memory, 'insights') and memory.insights:
            text_parts.append(f"Insights: {', '.join(memory.insights)}")
        
        return " ".join(text_parts)
    
    def semantic_search(self, query: str, limit: int = 10, 
                       privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
                       memory_types: Optional[List[MemoryType]] = None,
                       mood_filter: Optional[str] = None,
                       date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Tuple[MemoryEntry, float]]:
        """
        Perform semantic search using vector embeddings
        
        Args:
            query: Search query text
            limit: Maximum number of results
            privacy_level: Maximum privacy level to include
            memory_types: Filter by memory types
            mood_filter: Filter by specific mood
            date_range: Filter by date range
            
        Returns:
            List of (MemoryEntry, similarity_score) tuples
        """
        
        self.search_stats['total_searches'] += 1
        self.search_stats['semantic_searches'] += 1
        self.search_stats['last_search'] = datetime.now()
        
        if not self.collection:
            logger.warning("ChromaDB not available, falling back to keyword search")
            return self.keyword_search(query, limit, privacy_level, memory_types, mood_filter, date_range)
        
        try:
            # Build metadata filters
            where_conditions = self._build_where_conditions(
                privacy_level, memory_types, mood_filter, date_range
            )
            
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_conditions if where_conditions else None
            )
            
            # Convert results to memory entries
            memory_results = []
            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    if self.memory_manager:
                        memory = self.memory_manager.retrieve_memory(memory_id)
                        if memory:
                            similarity_score = 1.0 - results['distances'][0][i]  # Convert distance to similarity
                            memory_results.append((memory, similarity_score))
            
            self.search_stats['average_results'] = (
                self.search_stats['average_results'] * (self.search_stats['total_searches'] - 1) + 
                len(memory_results)
            ) / self.search_stats['total_searches']
            
            logger.info(f"Semantic search for '{query}' returned {len(memory_results)} results")
            return memory_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self.keyword_search(query, limit, privacy_level, memory_types, mood_filter, date_range)
    
    def keyword_search(self, query: str, limit: int = 10,
                      privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
                      memory_types: Optional[List[MemoryType]] = None,
                      mood_filter: Optional[str] = None,
                      date_range: Optional[Tuple[datetime, datetime]] = None) -> List[Tuple[MemoryEntry, float]]:
        """
        Fallback keyword-based search
        
        Args:
            query: Search query text
            limit: Maximum number of results
            privacy_level: Maximum privacy level to include
            memory_types: Filter by memory types
            mood_filter: Filter by specific mood
            date_range: Filter by date range
            
        Returns:
            List of (MemoryEntry, relevance_score) tuples
        """
        
        self.search_stats['total_searches'] += 1
        self.search_stats['keyword_searches'] += 1
        self.search_stats['last_search'] = datetime.now()
        
        if not self.memory_manager:
            logger.error("No memory manager available for keyword search")
            return []
        
        try:
            # Get memories using memory manager search
            memories = self.memory_manager.search_memories(
                query=query,
                memory_type=memory_types[0] if memory_types else None,
                privacy_level=privacy_level,
                date_range=date_range,
                limit=limit
            )
            
            # Filter by mood if specified
            if mood_filter:
                memories = [m for m in memories if m.emotional_context.primary_mood == mood_filter]
            
            # Calculate relevance scores
            query_words = set(query.lower().split())
            memory_results = []
            
            for memory in memories:
                score = self._calculate_keyword_relevance(memory, query_words)
                memory_results.append((memory, score))
            
            # Sort by relevance score
            memory_results.sort(key=lambda x: x[1], reverse=True)
            
            self.search_stats['average_results'] = (
                self.search_stats['average_results'] * (self.search_stats['total_searches'] - 1) + 
                len(memory_results)
            ) / self.search_stats['total_searches']
            
            logger.info(f"Keyword search for '{query}' returned {len(memory_results)} results")
            return memory_results[:limit]
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def _build_where_conditions(self, privacy_level: PrivacyLevel,
                               memory_types: Optional[List[MemoryType]],
                               mood_filter: Optional[str],
                               date_range: Optional[Tuple[datetime, datetime]]) -> Optional[Dict]:
        """Build ChromaDB where conditions for filtering"""
        
        conditions = {}
        
        # Privacy level filter
        privacy_hierarchy = {
            PrivacyLevel.PUBLIC: ['public'],
            PrivacyLevel.PRIVATE: ['public', 'private'],
            PrivacyLevel.CONFIDENTIAL: ['public', 'private', 'confidential'],
            PrivacyLevel.ENCRYPTED: ['public', 'private', 'confidential', 'encrypted']
        }
        allowed_privacy = privacy_hierarchy[privacy_level]
        conditions['privacy_level'] = {'$in': allowed_privacy}
        
        # Memory type filter
        if memory_types:
            type_values = [mt.value for mt in memory_types]
            conditions['memory_type'] = {'$in': type_values}
        
        # Mood filter
        if mood_filter:
            conditions['primary_mood'] = mood_filter
        
        # Date range filter
        if date_range:
            conditions['created_at'] = {
                '$gte': date_range[0].isoformat(),
                '$lte': date_range[1].isoformat()
            }
        
        return conditions if conditions else None
    
    def _calculate_keyword_relevance(self, memory: MemoryEntry, query_words: set) -> float:
        """Calculate relevance score for keyword search"""
        
        # Combine all searchable text
        searchable_text = f"{memory.title} {memory.content}".lower()
        
        # Add emotional context
        searchable_text += f" {memory.emotional_context.primary_mood}"
        if memory.emotional_context.emotions:
            searchable_text += f" {' '.join(memory.emotional_context.emotions)}"
        
        # Add metadata
        if memory.metadata.themes:
            searchable_text += f" {' '.join(memory.metadata.themes)}"
        if memory.metadata.tags:
            searchable_text += f" {' '.join(memory.metadata.tags)}"
        
        # Calculate word matches
        text_words = set(re.findall(r'\b\w+\b', searchable_text))
        matches = len(query_words.intersection(text_words))
        
        if len(query_words) == 0:
            return 0.0
        
        # Base relevance score
        relevance = matches / len(query_words)
        
        # Boost based on importance and recency
        importance_boost = memory.metadata.importance_score * 0.2
        
        # Recency boost (more recent memories get slight boost)
        days_old = (datetime.now() - memory.created_at).days
        recency_boost = max(0, (30 - days_old) / 30) * 0.1
        
        return min(1.0, relevance + importance_boost + recency_boost)
    
    def find_similar_memories(self, memory: MemoryEntry, limit: int = 5) -> List[Tuple[MemoryEntry, float]]:
        """
        Find memories similar to a given memory
        
        Args:
            memory: Reference memory to find similar ones
            limit: Maximum number of similar memories
            
        Returns:
            List of (MemoryEntry, similarity_score) tuples
        """
        
        if not self.collection:
            return self._find_similar_memories_fallback(memory, limit)
        
        try:
            # Use the memory's content as query
            search_text = self._prepare_search_text(memory)
            
            # Search for similar memories (exclude the original)
            results = self.collection.query(
                query_texts=[search_text],
                n_results=limit + 1,  # +1 to account for excluding original
                where={'memory_type': {'$ne': 'placeholder'}}  # Dummy condition
            )
            
            # Convert results and exclude original memory
            similar_memories = []
            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    if memory_id != memory.id and self.memory_manager:
                        similar_memory = self.memory_manager.retrieve_memory(memory_id)
                        if similar_memory:
                            similarity_score = 1.0 - results['distances'][0][i]
                            similar_memories.append((similar_memory, similarity_score))
            
            return similar_memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar memories: {e}")
            return self._find_similar_memories_fallback(memory, limit)
    
    def _find_similar_memories_fallback(self, memory: MemoryEntry, limit: int) -> List[Tuple[MemoryEntry, float]]:
        """Fallback method for finding similar memories without vector search"""
        
        if not self.memory_manager:
            return []
        
        # Find memories with same mood
        similar_memories = self.memory_manager.get_memories_by_mood(
            memory.emotional_context.primary_mood, limit * 2
        )
        
        # Filter out the original memory
        similar_memories = [m for m in similar_memories if m.id != memory.id]
        
        # Calculate similarity based on themes and tags
        memory_results = []
        memory_themes = set(memory.metadata.themes)
        memory_tags = set(memory.metadata.tags)
        
        for similar_memory in similar_memories:
            similar_themes = set(similar_memory.metadata.themes)
            similar_tags = set(similar_memory.metadata.tags)
            
            # Calculate Jaccard similarity for themes and tags
            theme_similarity = len(memory_themes.intersection(similar_themes)) / len(memory_themes.union(similar_themes)) if memory_themes.union(similar_themes) else 0
            tag_similarity = len(memory_tags.intersection(similar_tags)) / len(memory_tags.union(similar_tags)) if memory_tags.union(similar_tags) else 0
            
            # Combined similarity score
            similarity = (theme_similarity + tag_similarity) / 2
            
            # Boost for same mood
            if similar_memory.emotional_context.primary_mood == memory.emotional_context.primary_mood:
                similarity += 0.2
            
            memory_results.append((similar_memory, similarity))
        
        # Sort by similarity and return top results
        memory_results.sort(key=lambda x: x[1], reverse=True)
        return memory_results[:limit]
    
    def search_by_emotion(self, emotion: str, limit: int = 10) -> List[Tuple[MemoryEntry, float]]:
        """Search for memories containing specific emotions"""
        
        if not self.memory_manager:
            return []
        
        # Get all memories and filter by emotion
        all_memories = self.memory_manager.search_memories(limit=1000)  # Get a large set
        
        emotion_memories = []
        for memory in all_memories:
            # Handle different memory types
            if hasattr(memory, 'emotional_context') and memory.emotional_context:
                emotions = memory.emotional_context.emotions
                intensity = memory.emotional_context.intensity
            elif hasattr(memory, 'memory_entry') and memory.memory_entry.emotional_context:
                emotions = memory.memory_entry.emotional_context.emotions
                intensity = memory.memory_entry.emotional_context.intensity
            else:
                continue
            
            if emotion.lower() in [e.lower() for e in emotions]:
                # Calculate relevance based on emotion intensity and recency
                if hasattr(intensity, 'value'):
                    intensity_value = intensity.value
                else:
                    intensity_value = str(intensity)
                
                if intensity_value == 'very_high':
                    relevance = 1.0
                elif intensity_value == 'high':
                    relevance = 0.8
                elif intensity_value == 'moderate':
                    relevance = 0.6
                elif intensity_value == 'low':
                    relevance = 0.4
                else:
                    relevance = 0.2
                
                emotion_memories.append((memory, relevance))
        
        # Sort by relevance and return top results
        emotion_memories.sort(key=lambda x: x[1], reverse=True)
        return emotion_memories[:limit]
    
    def search_by_date_range(self, start_date: datetime, end_date: datetime,
                           limit: int = 50) -> List[MemoryEntry]:
        """Search for memories within a specific date range"""
        
        if not self.memory_manager:
            return []
        
        return self.memory_manager.search_memories(
            date_range=(start_date, end_date),
            limit=limit
        )
    
    def get_memory_timeline(self, days: int = 30) -> Dict[str, List[MemoryEntry]]:
        """Get memories organized by date for timeline view"""
        
        if not self.memory_manager:
            return {}
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        memories = self.search_by_date_range(start_date, end_date, limit=1000)
        
        # Organize by date
        timeline = {}
        for memory in memories:
            # Handle different memory types
            if hasattr(memory, 'created_at'):
                created_at = memory.created_at
            elif hasattr(memory, 'memory_entry') and hasattr(memory.memory_entry, 'created_at'):
                created_at = memory.memory_entry.created_at
            else:
                continue
                
            date_key = created_at.strftime('%Y-%m-%d')
            if date_key not in timeline:
                timeline[date_key] = []
            timeline[date_key].append(memory)
        
        # Sort memories within each date
        for date_key in timeline:
            def get_sort_key(memory):
                if hasattr(memory, 'created_at'):
                    return memory.created_at
                elif hasattr(memory, 'memory_entry') and hasattr(memory.memory_entry, 'created_at'):
                    return memory.memory_entry.created_at
                else:
                    return datetime.now()
            
            timeline[date_key].sort(key=get_sort_key)
        
        return timeline
    
    def update_memory_in_search(self, memory: MemoryEntry) -> bool:
        """Update a memory in the search index"""
        
        if not self.collection:
            return False
        
        try:
            # Remove old version
            self.remove_memory_from_search(memory.id)
            
            # Add updated version
            return self.add_memory_to_search(memory)
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory.id} in search index: {e}")
            return False
    
    def remove_memory_from_search(self, memory_id: str) -> bool:
        """Remove a memory from the search index"""
        
        if not self.collection:
            return False
        
        try:
            self.collection.delete(ids=[memory_id])
            logger.debug(f"Removed memory {memory_id} from search index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove memory {memory_id} from search index: {e}")
            return False
    
    def get_search_stats(self) -> Dict[str, Any]:
        """Get search usage statistics"""
        return {
            **self.search_stats,
            'chromadb_available': CHROMADB_AVAILABLE,
            'indexed_memories': self.collection.count() if self.collection else 0,
            'last_search_formatted': self.search_stats['last_search'].strftime('%Y-%m-%d %H:%M:%S') if self.search_stats['last_search'] else None
        }
    
    def rebuild_search_index(self) -> bool:
        """Rebuild the entire search index from memory manager"""
        
        if not self.collection or not self.memory_manager:
            return False
        
        try:
            # Clear existing index
            self.collection.delete()
            
            # Get all memories
            all_memories = self.memory_manager.search_memories(limit=10000)
            
            # Re-index all memories
            success_count = 0
            for memory in all_memories:
                if self.add_memory_to_search(memory):
                    success_count += 1
            
            logger.info(f"Rebuilt search index with {success_count}/{len(all_memories)} memories")
            return success_count == len(all_memories)
            
        except Exception as e:
            logger.error(f"Failed to rebuild search index: {e}")
            return False

