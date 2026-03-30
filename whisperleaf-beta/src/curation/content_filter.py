"""
Content Filtering and Quality Assessment System for Automated Curation.
"""

import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from collections import Counter
import math

@dataclass
class ContentScore:
    """Represents quality and relevance scores for content."""
    relevance_score: float  # 0.0 to 1.0
    quality_score: float    # 0.0 to 1.0
    overall_score: float    # 0.0 to 1.0
    confidence: float       # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class FilterAction(Enum):
    """Actions that can be taken on content."""
    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "review"
    QUARANTINE = "quarantine"

@dataclass
class FilterResult:
    """Result of content filtering."""
    action: FilterAction
    score: ContentScore
    content_hash: str
    filtered_at: datetime
    filter_version: str = "1.0"

@dataclass
class FilterRule:
    """Configuration for content filtering rules."""
    name: str
    description: str
    enabled: bool = True
    weight: float = 1.0
    
    # Keyword filtering
    required_keywords: List[str] = field(default_factory=list)
    excluded_keywords: List[str] = field(default_factory=list)
    
    # Content quality thresholds
    min_word_count: int = 50
    max_word_count: int = 50000
    min_quality_score: float = 0.3
    min_relevance_score: float = 0.4
    
    # Language filtering
    allowed_languages: Set[str] = field(default_factory=lambda: {"en"})
    
    # Source filtering
    trusted_domains: Set[str] = field(default_factory=set)
    blocked_domains: Set[str] = field(default_factory=set)
    
    # Content type filtering
    allowed_content_types: Set[str] = field(default_factory=lambda: {"article", "news", "blog", "documentation"})

class ContentQualityAnalyzer:
    """Analyzes content quality using various metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common quality indicators
        self.quality_indicators = {
            'positive': [
                'research', 'study', 'analysis', 'evidence', 'data', 'findings',
                'methodology', 'conclusion', 'abstract', 'introduction',
                'references', 'bibliography', 'peer-reviewed', 'published',
                'university', 'institute', 'journal', 'academic'
            ],
            'negative': [
                'clickbait', 'shocking', 'unbelievable', 'secret', 'trick',
                'hate', 'scam', 'fake', 'hoax', 'conspiracy', 'rumor',
                'gossip', 'tabloid', 'sensational', 'outrageous'
            ]
        }
        
        # Readability metrics
        self.readability_weights = {
            'avg_sentence_length': 0.3,
            'avg_word_length': 0.2,
            'paragraph_structure': 0.2,
            'punctuation_ratio': 0.1,
            'capitalization_ratio': 0.1,
            'spelling_errors': 0.1
        }
    
    def analyze_quality(self, content: str, metadata: Dict[str, Any] = None) -> ContentScore:
        """
        Analyze content quality using multiple metrics.
        
        Args:
            content: Text content to analyze
            metadata: Additional metadata about the content
            
        Returns:
            ContentScore with quality assessment
        """
        if not content or not content.strip():
            return ContentScore(
                relevance_score=0.0,
                quality_score=0.0,
                overall_score=0.0,
                confidence=1.0,
                reasons=["Empty content"]
            )
        
        metadata = metadata or {}
        reasons = []
        quality_metrics = {}
        
        # Basic content metrics
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len(re.findall(r'[.!?]+', content))
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        quality_metrics.update({
            'word_count': word_count,
            'char_count': char_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count
        })
        
        # Length-based quality
        length_score = self._analyze_length_quality(word_count, reasons)
        
        # Readability analysis
        readability_score = self._analyze_readability(content, reasons)
        
        # Structure analysis
        structure_score = self._analyze_structure(content, metadata, reasons)
        
        # Language quality
        language_score = self._analyze_language_quality(content, reasons)
        
        # Content indicators
        indicator_score = self._analyze_content_indicators(content, reasons)
        
        # Calculate overall quality score
        quality_score = (
            length_score * 0.2 +
            readability_score * 0.25 +
            structure_score * 0.25 +
            language_score * 0.15 +
            indicator_score * 0.15
        )
        
        # Calculate confidence based on content length and analysis depth
        confidence = min(1.0, (word_count / 100) * 0.1 + 0.5)
        
        return ContentScore(
            relevance_score=0.5,  # Will be calculated separately
            quality_score=quality_score,
            overall_score=quality_score * 0.7 + 0.5 * 0.3,  # Weighted with relevance
            confidence=confidence,
            reasons=reasons,
            metadata=quality_metrics
        )
    
    def _analyze_length_quality(self, word_count: int, reasons: List[str]) -> float:
        """Analyze quality based on content length."""
        if word_count < 50:
            reasons.append("Content too short")
            return 0.2
        elif word_count < 100:
            reasons.append("Content quite short")
            return 0.5
        elif word_count > 10000:
            reasons.append("Content very long")
            return 0.7
        elif 200 <= word_count <= 2000:
            reasons.append("Good content length")
            return 0.9
        else:
            return 0.8
    
    def _analyze_readability(self, content: str, reasons: List[str]) -> float:
        """Analyze readability metrics."""
        words = content.split()
        sentences = re.findall(r'[.!?]+', content)
        
        if not words or not sentences:
            return 0.3
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        sentence_score = 1.0 - min(1.0, abs(avg_sentence_length - 15) / 20)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        word_score = 1.0 - min(1.0, abs(avg_word_length - 5) / 5)
        
        # Punctuation ratio
        punctuation_count = len(re.findall(r'[.!?,;:]', content))
        punctuation_ratio = punctuation_count / len(words)
        punct_score = min(1.0, punctuation_ratio * 10)
        
        readability_score = (sentence_score + word_score + punct_score) / 3
        
        if readability_score > 0.7:
            reasons.append("Good readability")
        elif readability_score < 0.4:
            reasons.append("Poor readability")
        
        return readability_score
    
    def _analyze_structure(self, content: str, metadata: Dict[str, Any], reasons: List[str]) -> float:
        """Analyze content structure quality."""
        structure_score = 0.5
        
        # Check for title
        title = metadata.get('title', '')
        if title and len(title.split()) >= 3:
            structure_score += 0.1
            reasons.append("Has meaningful title")
        
        # Check for paragraphs
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 2:
            structure_score += 0.1
            reasons.append("Well-structured paragraphs")
        
        # Check for headings (simple heuristic)
        potential_headings = re.findall(r'^[A-Z][^.!?]*$', content, re.MULTILINE)
        if potential_headings:
            structure_score += 0.1
            reasons.append("Contains headings")
        
        # Check for lists or bullet points
        if re.search(r'^\s*[-*•]\s+', content, re.MULTILINE):
            structure_score += 0.05
            reasons.append("Contains lists")
        
        # Check for links or references
        links = metadata.get('links', [])
        if links and len(links) > 0:
            structure_score += 0.1
            reasons.append("Contains references/links")
        
        return min(1.0, structure_score)
    
    def _analyze_language_quality(self, content: str, reasons: List[str]) -> float:
        """Analyze language quality."""
        # Check for excessive capitalization
        caps_ratio = sum(1 for c in content if c.isupper()) / len(content)
        if caps_ratio > 0.3:
            reasons.append("Excessive capitalization")
            return 0.3
        
        # Check for repeated characters (like "!!!" or "???")
        repeated_chars = len(re.findall(r'(.)\1{2,}', content))
        if repeated_chars > 5:
            reasons.append("Excessive repeated characters")
            return 0.4
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', content)
        proper_sentences = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        sentence_ratio = proper_sentences / max(1, len(sentences))
        
        if sentence_ratio > 0.8:
            reasons.append("Good sentence structure")
            return 0.9
        elif sentence_ratio > 0.6:
            return 0.7
        else:
            reasons.append("Poor sentence structure")
            return 0.5
    
    def _analyze_content_indicators(self, content: str, reasons: List[str]) -> float:
        """Analyze content using quality indicators."""
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.quality_indicators['positive'] 
                           if word in content_lower)
        negative_count = sum(1 for word in self.quality_indicators['negative'] 
                           if word in content_lower)
        
        if positive_count > 0:
            reasons.append(f"Contains {positive_count} quality indicators")
        if negative_count > 0:
            reasons.append(f"Contains {negative_count} negative indicators")
        
        # Calculate score based on indicator balance
        total_indicators = positive_count + negative_count
        if total_indicators == 0:
            return 0.5
        
        indicator_score = positive_count / total_indicators
        return indicator_score

class RelevanceAnalyzer:
    """Analyzes content relevance based on keywords and topics."""
    
    def __init__(self, user_interests: List[str] = None):
        self.user_interests = user_interests or []
        self.logger = logging.getLogger(__name__)
        
        # TF-IDF-like scoring for relevance
        self.interest_weights = {}
        for interest in self.user_interests:
            self.interest_weights[interest.lower()] = 1.0
    
    def analyze_relevance(self, content: str, metadata: Dict[str, Any] = None) -> float:
        """
        Analyze content relevance to user interests.
        
        Args:
            content: Text content to analyze
            metadata: Additional metadata (title, tags, etc.)
            
        Returns:
            Relevance score from 0.0 to 1.0
        """
        if not self.user_interests:
            return 0.5  # Neutral relevance if no interests defined
        
        metadata = metadata or {}
        content_lower = content.lower()
        
        # Combine content with metadata for analysis
        analysis_text = content_lower
        
        # Add title with higher weight
        title = metadata.get('title', '')
        if title:
            analysis_text += ' ' + title.lower() * 3  # Title gets 3x weight
        
        # Add tags with higher weight
        tags = metadata.get('tags', [])
        if tags:
            tag_text = ' '.join(str(tag).lower() for tag in tags)
            analysis_text += ' ' + tag_text * 2  # Tags get 2x weight
        
        # Calculate relevance based on interest matching
        relevance_scores = []
        
        for interest in self.user_interests:
            interest_lower = interest.lower()
            
            # Direct keyword matching
            direct_matches = analysis_text.count(interest_lower)
            
            # Fuzzy matching for related terms
            related_matches = self._find_related_terms(interest_lower, analysis_text)
            
            # Calculate score for this interest
            total_matches = direct_matches + related_matches * 0.5
            interest_score = min(1.0, total_matches / 10)  # Normalize to 0-1
            
            relevance_scores.append(interest_score)
        
        # Return the maximum relevance score
        return max(relevance_scores) if relevance_scores else 0.0
    
    def _find_related_terms(self, interest: str, text: str) -> int:
        """Find terms related to the interest in the text."""
        # Simple related term matching
        related_terms = {
            'ai': ['artificial intelligence', 'machine learning', 'neural network', 'deep learning'],
            'technology': ['tech', 'software', 'hardware', 'digital', 'computer'],
            'science': ['research', 'study', 'experiment', 'scientific', 'discovery'],
            'programming': ['coding', 'development', 'software', 'algorithm', 'code'],
            'business': ['company', 'startup', 'entrepreneur', 'market', 'finance']
        }
        
        related = related_terms.get(interest, [])
        return sum(text.count(term) for term in related)

class DuplicateDetector:
    """Detects duplicate or near-duplicate content."""
    
    def __init__(self):
        self.content_hashes: Dict[str, Dict[str, Any]] = {}
        self.similarity_threshold = 0.8
        self.logger = logging.getLogger(__name__)
    
    def is_duplicate(self, content: str, metadata: Dict[str, Any] = None) -> Tuple[bool, float, Optional[str]]:
        """
        Check if content is a duplicate of previously seen content.
        
        Args:
            content: Text content to check
            metadata: Additional metadata
            
        Returns:
            Tuple of (is_duplicate, similarity_score, original_hash)
        """
        if not content or not content.strip():
            return False, 0.0, None
        
        # Generate content hash
        content_hash = self._generate_content_hash(content)
        
        # Check for exact duplicates
        if content_hash in self.content_hashes:
            return True, 1.0, content_hash
        
        # Check for near-duplicates using similarity
        for existing_hash, existing_data in self.content_hashes.items():
            similarity = self._calculate_similarity(content, existing_data['content'])
            
            if similarity >= self.similarity_threshold:
                return True, similarity, existing_hash
        
        # Store this content for future duplicate detection
        self.content_hashes[content_hash] = {
            'content': content[:1000],  # Store first 1000 chars for similarity
            'metadata': metadata or {},
            'added_at': datetime.now(timezone.utc),
            'full_hash': content_hash
        }
        
        return False, 0.0, None
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash for content."""
        # Normalize content for hashing
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two pieces of content."""
        # Simple word-based similarity
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_duplicate_stats(self) -> Dict[str, Any]:
        """Get statistics about duplicate detection."""
        return {
            'total_content_hashes': len(self.content_hashes),
            'similarity_threshold': self.similarity_threshold,
            'oldest_content': min(
                (data['added_at'] for data in self.content_hashes.values()),
                default=None
            )
        }

class ContentFilter:
    """Main content filtering system."""
    
    def __init__(self, filter_rules: List[FilterRule] = None):
        self.filter_rules = filter_rules or [self._create_default_rule()]
        self.quality_analyzer = ContentQualityAnalyzer()
        self.relevance_analyzer = RelevanceAnalyzer()
        self.duplicate_detector = DuplicateDetector()
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'accept': 0,
            'reject': 0,
            'review': 0,
            'quarantine': 0,
            'duplicates_found': 0
        }
    
    def filter_content(self, content: str, metadata: Dict[str, Any] = None, 
                      source_url: str = None) -> FilterResult:
        """
        Filter content through all configured rules.
        
        Args:
            content: Text content to filter
            metadata: Additional metadata about the content
            source_url: Source URL of the content
            
        Returns:
            FilterResult with filtering decision and scores
        """
        self.stats['total_processed'] += 1
        metadata = metadata or {}
        
        # Generate content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check for duplicates first
        is_duplicate, similarity, original_hash = self.duplicate_detector.is_duplicate(content, metadata)
        if is_duplicate:
            self.stats['duplicates_found'] += 1
            return FilterResult(
                action=FilterAction.REJECT,
                score=ContentScore(0.0, 0.0, 0.0, 1.0, ["Duplicate content"]),
                content_hash=content_hash,
                filtered_at=datetime.now(timezone.utc)
            )
        
        # Analyze quality
        quality_score = self.quality_analyzer.analyze_quality(content, metadata)
        
        # Analyze relevance
        relevance_score = self.relevance_analyzer.analyze_relevance(content, metadata)
        quality_score.relevance_score = relevance_score
        
        # Update overall score
        quality_score.overall_score = (
            quality_score.quality_score * 0.6 + 
            quality_score.relevance_score * 0.4
        )
        
        # Apply filter rules
        action = self._apply_filter_rules(content, metadata, quality_score, source_url)
        
        # Update statistics
        self.stats[action.value] += 1
        
        return FilterResult(
            action=action,
            score=quality_score,
            content_hash=content_hash,
            filtered_at=datetime.now(timezone.utc)
        )
    
    def _apply_filter_rules(self, content: str, metadata: Dict[str, Any], 
                          score: ContentScore, source_url: str = None) -> FilterAction:
        """Apply all filter rules to determine action."""
        
        for rule in self.filter_rules:
            if not rule.enabled:
                continue
            
            # Check word count limits
            word_count = len(content.split())
            if word_count < rule.min_word_count or word_count > rule.max_word_count:
                score.reasons.append(f"Word count {word_count} outside limits")
                return FilterAction.REJECT
            
            # Check quality thresholds
            if score.quality_score < rule.min_quality_score:
                score.reasons.append(f"Quality score {score.quality_score:.2f} below threshold")
                return FilterAction.REJECT
            
            if score.relevance_score < rule.min_relevance_score:
                score.reasons.append(f"Relevance score {score.relevance_score:.2f} below threshold")
                return FilterAction.REJECT
            
            # Check required keywords
            if rule.required_keywords:
                content_lower = content.lower()
                has_required = any(keyword.lower() in content_lower 
                                 for keyword in rule.required_keywords)
                if not has_required:
                    score.reasons.append("Missing required keywords")
                    return FilterAction.REJECT
            
            # Check excluded keywords
            if rule.excluded_keywords:
                content_lower = content.lower()
                has_excluded = any(keyword.lower() in content_lower 
                                 for keyword in rule.excluded_keywords)
                if has_excluded:
                    score.reasons.append("Contains excluded keywords")
                    return FilterAction.REJECT
            
            # Check domain restrictions
            if source_url:
                from urllib.parse import urlparse
                domain = urlparse(source_url).netloc
                
                if rule.blocked_domains and domain in rule.blocked_domains:
                    score.reasons.append(f"Domain {domain} is blocked")
                    return FilterAction.REJECT
                
                if rule.trusted_domains and domain not in rule.trusted_domains:
                    score.reasons.append(f"Domain {domain} not in trusted list")
                    return FilterAction.REVIEW
        
        # Determine final action based on scores
        if score.overall_score >= 0.8:
            score.reasons.append("High quality content")
            return FilterAction.ACCEPT
        elif score.overall_score >= 0.6:
            score.reasons.append("Good quality content")
            return FilterAction.ACCEPT
        elif score.overall_score >= 0.4:
            score.reasons.append("Moderate quality content")
            return FilterAction.REVIEW
        else:
            score.reasons.append("Low quality content")
            return FilterAction.REJECT
    
    def _create_default_rule(self) -> FilterRule:
        """Create a default filter rule."""
        return FilterRule(
            name="Default Filter",
            description="Default content filtering rule",
            min_word_count=50,
            max_word_count=10000,
            min_quality_score=0.3,
            min_relevance_score=0.2,
            allowed_languages={"en"},
            allowed_content_types={"article", "news", "blog", "documentation"}
        )
    
    def add_filter_rule(self, rule: FilterRule):
        """Add a new filter rule."""
        self.filter_rules.append(rule)
        self.logger.info(f"Added filter rule: {rule.name}")
    
    def set_user_interests(self, interests: List[str]):
        """Set user interests for relevance analysis."""
        self.relevance_analyzer.user_interests = interests
        self.relevance_analyzer.interest_weights = {
            interest.lower(): 1.0 for interest in interests
        }
        self.logger.info(f"Updated user interests: {interests}")
    
    def get_filter_stats(self) -> Dict[str, Any]:
        """Get filtering statistics."""
        total = self.stats['total_processed']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'acceptance_rate': self.stats['accept'] / total,
            'rejection_rate': self.stats['reject'] / total,
            'review_rate': self.stats['review'] / total,
            'duplicate_rate': self.stats['duplicates_found'] / total,
            'quality_analyzer_stats': {},
            'duplicate_detector_stats': self.duplicate_detector.get_duplicate_stats()
        }

