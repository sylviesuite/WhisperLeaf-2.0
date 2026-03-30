"""
WhisperLeaf Memory Models
Data models for emotional memory storage and management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid

class MemoryType(Enum):
    """Types of memories stored in the vault"""
    JOURNAL_ENTRY = "journal_entry"
    CONVERSATION = "conversation"
    EMOTIONAL_EVENT = "emotional_event"
    REFLECTION = "reflection"
    MILESTONE = "milestone"
    CRISIS_EVENT = "crisis_event"
    GROWTH_MOMENT = "growth_moment"
    PATTERN_INSIGHT = "pattern_insight"

class EmotionalIntensity(Enum):
    """Emotional intensity levels for memories"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class PrivacyLevel(Enum):
    """Privacy levels for memory access"""
    PUBLIC = "public"          # Can be shared in summaries
    PRIVATE = "private"        # Personal but can be referenced
    CONFIDENTIAL = "confidential"  # Highly sensitive
    ENCRYPTED = "encrypted"    # Encrypted storage required

@dataclass
class EmotionalContext:
    """Emotional context information for memories"""
    primary_mood: str
    secondary_mood: Optional[str] = None
    emotions: List[str] = field(default_factory=list)
    intensity: EmotionalIntensity = EmotionalIntensity.MODERATE
    complexity_score: float = 0.0
    crisis_level: str = "none"
    support_needs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'primary_mood': self.primary_mood,
            'secondary_mood': self.secondary_mood,
            'emotions': self.emotions,
            'intensity': self.intensity.value,
            'complexity_score': self.complexity_score,
            'crisis_level': self.crisis_level,
            'support_needs': self.support_needs
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalContext':
        return cls(
            primary_mood=data['primary_mood'],
            secondary_mood=data.get('secondary_mood'),
            emotions=data.get('emotions', []),
            intensity=EmotionalIntensity(data.get('intensity', 'moderate')),
            complexity_score=data.get('complexity_score', 0.0),
            crisis_level=data.get('crisis_level', 'none'),
            support_needs=data.get('support_needs', [])
        )

@dataclass
class MemoryMetadata:
    """Metadata for memory entries"""
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    people_mentioned: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    importance_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            'tags': self.tags,
            'categories': self.categories,
            'people_mentioned': self.people_mentioned,
            'locations': self.locations,
            'events': self.events,
            'themes': self.themes,
            'keywords': self.keywords,
            'sentiment_score': self.sentiment_score,
            'importance_score': self.importance_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryMetadata':
        return cls(
            tags=data.get('tags', []),
            categories=data.get('categories', []),
            people_mentioned=data.get('people_mentioned', []),
            locations=data.get('locations', []),
            events=data.get('events', []),
            themes=data.get('themes', []),
            keywords=data.get('keywords', []),
            sentiment_score=data.get('sentiment_score', 0.0),
            importance_score=data.get('importance_score', 0.0)
        )

@dataclass
class MemoryEntry:
    """Base memory entry for all types of emotional memories"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.EMOTIONAL_EVENT
    title: str = ""
    content: str = ""
    emotional_context: EmotionalContext = field(default_factory=EmotionalContext)
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)
    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accessed_count: int = 0
    last_accessed: Optional[datetime] = None
    related_memories: List[str] = field(default_factory=list)
    vector_embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict:
        """Convert memory entry to dictionary for storage"""
        return {
            'id': self.id,
            'memory_type': self.memory_type.value,
            'title': self.title,
            'content': self.content,
            'emotional_context': self.emotional_context.to_dict(),
            'metadata': self.metadata.to_dict(),
            'privacy_level': self.privacy_level.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'accessed_count': self.accessed_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'related_memories': self.related_memories,
            'vector_embedding': self.vector_embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        """Create memory entry from dictionary"""
        return cls(
            id=data['id'],
            memory_type=MemoryType(data['memory_type']),
            title=data['title'],
            content=data['content'],
            emotional_context=EmotionalContext.from_dict(data['emotional_context']),
            metadata=MemoryMetadata.from_dict(data['metadata']),
            privacy_level=PrivacyLevel(data['privacy_level']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            accessed_count=data.get('accessed_count', 0),
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None,
            related_memories=data.get('related_memories', []),
            vector_embedding=data.get('vector_embedding')
        )
    
    def update_access(self):
        """Update access tracking"""
        self.accessed_count += 1
        self.last_accessed = datetime.now()
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str):
        """Add a tag to the memory"""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.updated_at = datetime.now()
    
    def add_related_memory(self, memory_id: str):
        """Add a related memory reference"""
        if memory_id not in self.related_memories:
            self.related_memories.append(memory_id)
            self.updated_at = datetime.now()
    
    def get_summary(self, max_length: int = 200) -> str:
        """Get a summary of the memory content"""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length-3] + "..."
    
    def is_accessible(self, privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE) -> bool:
        """Check if memory is accessible at given privacy level"""
        privacy_hierarchy = {
            PrivacyLevel.PUBLIC: 0,
            PrivacyLevel.PRIVATE: 1,
            PrivacyLevel.CONFIDENTIAL: 2,
            PrivacyLevel.ENCRYPTED: 3
        }
        return privacy_hierarchy[self.privacy_level] <= privacy_hierarchy[privacy_level]

@dataclass
class JournalEntry(MemoryEntry):
    """Specialized memory entry for journal entries"""
    prompt: Optional[str] = None
    reflection_questions: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    gratitude: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None
    
    def __post_init__(self):
        self.memory_type = MemoryType.JOURNAL_ENTRY
    
    def to_dict(self) -> Dict:
        """Convert journal entry to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            'prompt': self.prompt,
            'reflection_questions': self.reflection_questions,
            'insights': self.insights,
            'goals': self.goals,
            'gratitude': self.gratitude,
            'challenges': self.challenges,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'JournalEntry':
        """Create journal entry from dictionary"""
        base_entry = super().from_dict(data)
        return cls(
            id=base_entry.id,
            title=base_entry.title,
            content=base_entry.content,
            emotional_context=base_entry.emotional_context,
            metadata=base_entry.metadata,
            privacy_level=base_entry.privacy_level,
            created_at=base_entry.created_at,
            updated_at=base_entry.updated_at,
            accessed_count=base_entry.accessed_count,
            last_accessed=base_entry.last_accessed,
            related_memories=base_entry.related_memories,
            vector_embedding=base_entry.vector_embedding,
            prompt=data.get('prompt'),
            reflection_questions=data.get('reflection_questions', []),
            insights=data.get('insights', []),
            goals=data.get('goals', []),
            gratitude=data.get('gratitude', []),
            challenges=data.get('challenges', []),
            mood_before=data.get('mood_before'),
            mood_after=data.get('mood_after')
        )

@dataclass
class EmotionalMemory:
    """Specialized memory for significant emotional events"""
    memory_entry: MemoryEntry
    trigger_event: str
    emotional_response: str
    coping_strategies: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    growth_indicators: List[str] = field(default_factory=list)
    support_received: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.memory_entry.memory_type = MemoryType.EMOTIONAL_EVENT
    
    def to_dict(self) -> Dict:
        """Convert emotional memory to dictionary"""
        return {
            'memory_entry': self.memory_entry.to_dict(),
            'trigger_event': self.trigger_event,
            'emotional_response': self.emotional_response,
            'coping_strategies': self.coping_strategies,
            'lessons_learned': self.lessons_learned,
            'growth_indicators': self.growth_indicators,
            'support_received': self.support_received
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EmotionalMemory':
        """Create emotional memory from dictionary"""
        return cls(
            memory_entry=MemoryEntry.from_dict(data['memory_entry']),
            trigger_event=data['trigger_event'],
            emotional_response=data['emotional_response'],
            coping_strategies=data.get('coping_strategies', []),
            lessons_learned=data.get('lessons_learned', []),
            growth_indicators=data.get('growth_indicators', []),
            support_received=data.get('support_received', [])
        )

@dataclass
class MemoryPattern:
    """Detected patterns in emotional memories"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = ""  # mood_cycle, trigger_response, growth_trend, etc.
    description: str = ""
    confidence: float = 0.0
    supporting_memories: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    first_detected: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'pattern_id': self.pattern_id,
            'pattern_type': self.pattern_type,
            'description': self.description,
            'confidence': self.confidence,
            'supporting_memories': self.supporting_memories,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'first_detected': self.first_detected.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryPattern':
        return cls(
            pattern_id=data['pattern_id'],
            pattern_type=data['pattern_type'],
            description=data['description'],
            confidence=data['confidence'],
            supporting_memories=data.get('supporting_memories', []),
            insights=data.get('insights', []),
            recommendations=data.get('recommendations', []),
            first_detected=datetime.fromisoformat(data['first_detected']),
            last_updated=datetime.fromisoformat(data['last_updated'])
        )

class MemoryStats:
    """Statistics about memory vault contents"""
    
    def __init__(self):
        self.total_memories = 0
        self.memory_types = {}
        self.emotional_distribution = {}
        self.privacy_distribution = {}
        self.average_importance = 0.0
        self.most_accessed_memory = None
        self.oldest_memory = None
        self.newest_memory = None
        self.total_size_bytes = 0
        
    def to_dict(self) -> Dict:
        return {
            'total_memories': self.total_memories,
            'memory_types': self.memory_types,
            'emotional_distribution': self.emotional_distribution,
            'privacy_distribution': self.privacy_distribution,
            'average_importance': self.average_importance,
            'most_accessed_memory': self.most_accessed_memory,
            'oldest_memory': self.oldest_memory.isoformat() if self.oldest_memory else None,
            'newest_memory': self.newest_memory.isoformat() if self.newest_memory else None,
            'total_size_bytes': self.total_size_bytes
        }

