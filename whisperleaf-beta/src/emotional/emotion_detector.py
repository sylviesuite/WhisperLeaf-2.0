"""
WhisperLeaf Emotion Detection System
Advanced natural language analysis for emotional understanding
"""

import re
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging

from .big_mood import BigMoodClassifier, MoodColor, MoodAnalysis

logger = logging.getLogger(__name__)

@dataclass
class EmotionSignal:
    """Individual emotional signal detected in text"""
    emotion: str
    intensity: float
    confidence: float
    source: str  # word, phrase, or pattern that triggered detection
    position: int  # position in text

@dataclass
class EmotionalContext:
    """Contextual information about emotional state"""
    temporal_pattern: str  # past, present, future
    certainty_level: str   # certain, uncertain, questioning
    social_context: str    # self, others, relationships
    action_orientation: str # passive, active, seeking_help

@dataclass
class EmotionAnalysis:
    """Comprehensive emotion analysis result"""
    primary_emotions: List[EmotionSignal]
    mood_analysis: MoodAnalysis
    emotional_context: EmotionalContext
    intensity_score: float
    complexity_score: float
    crisis_indicators: List[str]
    support_needs: List[str]
    reasoning: str

class EmotionDetector:
    """
    Advanced emotion detection using multiple analysis techniques:
    - Lexical analysis (emotion words and phrases)
    - Syntactic patterns (sentence structure)
    - Semantic analysis (meaning and context)
    - Pragmatic analysis (implied emotions)
    """
    
    def __init__(self):
        self.big_mood = BigMoodClassifier()
        self.emotion_lexicon = self._initialize_emotion_lexicon()
        self.linguistic_patterns = self._initialize_linguistic_patterns()
        self.crisis_patterns = self._initialize_crisis_patterns()
        self.support_indicators = self._initialize_support_indicators()
        
    def _initialize_emotion_lexicon(self) -> Dict[str, Dict[str, float]]:
        """Initialize comprehensive emotion word lexicon"""
        return {
            # Primary emotions with intensity scores
            'joy': {
                'happy': 0.7, 'joyful': 0.9, 'elated': 0.9, 'ecstatic': 0.95,
                'delighted': 0.8, 'cheerful': 0.7, 'pleased': 0.6, 'glad': 0.6,
                'thrilled': 0.9, 'overjoyed': 0.95, 'euphoric': 0.95, 'blissful': 0.9,
                'content': 0.6, 'satisfied': 0.6, 'fulfilled': 0.8, 'grateful': 0.7
            },
            'sadness': {
                'sad': 0.8, 'depressed': 0.9, 'melancholy': 0.7, 'gloomy': 0.7,
                'dejected': 0.8, 'despondent': 0.9, 'downhearted': 0.8, 'blue': 0.6,
                'grief': 0.9, 'sorrow': 0.8, 'mourning': 0.9, 'heartbroken': 0.9,
                'devastated': 0.95, 'crushed': 0.9, 'shattered': 0.9, 'broken': 0.8
            },
            'anger': {
                'angry': 0.8, 'furious': 0.95, 'enraged': 0.95, 'livid': 0.9,
                'irritated': 0.6, 'annoyed': 0.5, 'frustrated': 0.7, 'mad': 0.8,
                'outraged': 0.9, 'indignant': 0.8, 'resentful': 0.7, 'bitter': 0.8,
                'hostile': 0.9, 'aggressive': 0.8, 'violent': 0.95, 'explosive': 0.9
            },
            'fear': {
                'afraid': 0.8, 'scared': 0.8, 'terrified': 0.95, 'frightened': 0.8,
                'anxious': 0.7, 'worried': 0.6, 'nervous': 0.6, 'panicked': 0.9,
                'alarmed': 0.8, 'startled': 0.7, 'apprehensive': 0.7, 'uneasy': 0.6,
                'paranoid': 0.8, 'phobic': 0.9, 'dread': 0.8, 'horror': 0.9
            },
            'surprise': {
                'surprised': 0.7, 'amazed': 0.8, 'astonished': 0.9, 'shocked': 0.9,
                'stunned': 0.8, 'bewildered': 0.7, 'confused': 0.6, 'perplexed': 0.6,
                'baffled': 0.7, 'puzzled': 0.6, 'mystified': 0.7, 'flabbergasted': 0.9
            },
            'disgust': {
                'disgusted': 0.8, 'revolted': 0.9, 'repulsed': 0.9, 'sickened': 0.8,
                'nauseated': 0.8, 'appalled': 0.8, 'horrified': 0.9, 'repelled': 0.8
            },
            'trust': {
                'trusting': 0.7, 'confident': 0.7, 'secure': 0.7, 'safe': 0.6,
                'assured': 0.7, 'certain': 0.6, 'comfortable': 0.6, 'relaxed': 0.6
            },
            'anticipation': {
                'excited': 0.8, 'eager': 0.8, 'hopeful': 0.7, 'optimistic': 0.7,
                'expectant': 0.7, 'enthusiastic': 0.8, 'motivated': 0.7, 'inspired': 0.8
            }
        }
    
    def _initialize_linguistic_patterns(self) -> Dict[str, List[str]]:
        """Initialize linguistic patterns that indicate emotions"""
        return {
            'intensity_amplifiers': [
                r'\bso\s+(\w+)', r'\bvery\s+(\w+)', r'\bextremely\s+(\w+)',
                r'\bincredibly\s+(\w+)', r'\babsolutely\s+(\w+)', r'\bcompletely\s+(\w+)',
                r'\btotally\s+(\w+)', r'\butterly\s+(\w+)', r'\bdeeply\s+(\w+)'
            ],
            'emotional_questions': [
                r'why\s+(?:am|do)\s+i\s+feel', r'what\s+(?:is|\'s)\s+wrong\s+with\s+me',
                r'how\s+(?:can|do)\s+i\s+(?:stop|deal|cope)', r'will\s+(?:i|this)\s+ever'
            ],
            'temporal_indicators': [
                r'(?:always|never|constantly|forever)\s+feel',
                r'(?:lately|recently|today|tonight)\s+(?:i\'ve|i)\s+been',
                r'(?:used\s+to|once|before)\s+(?:i\s+was|felt)'
            ],
            'social_context': [
                r'(?:my|our)\s+(?:relationship|family|friends)',
                r'(?:people|everyone|nobody)\s+(?:think|say|believe)',
                r'(?:alone|lonely|isolated|abandoned)'
            ],
            'help_seeking': [
                r'(?:need|want|looking\s+for)\s+(?:help|support|advice)',
                r'(?:don\'t\s+know|unsure)\s+(?:what\s+to\s+do|how\s+to)',
                r'(?:should\s+i|what\s+would\s+you)\s+(?:do|suggest)'
            ]
        }
    
    def _initialize_crisis_patterns(self) -> List[str]:
        """Initialize patterns that indicate crisis situations"""
        return [
            # Suicidal ideation
            r'\b(?:want\s+to\s+die|wish\s+i\s+was\s+dead|kill\s+myself)\b',
            r'\b(?:end\s+it\s+all|not\s+worth\s+living|better\s+off\s+dead)\b',
            r'\b(?:suicide|suicidal|end\s+my\s+life)\b',
            
            # Self-harm
            r'\b(?:hurt\s+myself|cut\s+myself|harm\s+myself)\b',
            r'\b(?:self\s+harm|self\s+injury|cutting)\b',
            
            # Hopelessness
            r'\b(?:no\s+hope|hopeless|nothing\s+left|give\s+up)\b',
            r'\b(?:can\'t\s+go\s+on|no\s+point|why\s+bother)\b',
            
            # Crisis situations
            r'\b(?:emergency|crisis|desperate|can\'t\s+cope)\b',
            r'\b(?:breaking\s+down|falling\s+apart|losing\s+it)\b'
        ]
    
    def _initialize_support_indicators(self) -> Dict[str, List[str]]:
        """Initialize indicators of different support needs"""
        return {
            'emotional_support': [
                'need someone to talk to', 'feeling alone', 'need comfort',
                'want understanding', 'need validation', 'feel unheard'
            ],
            'practical_help': [
                'don\'t know what to do', 'need advice', 'how do i',
                'what should i', 'need guidance', 'need direction'
            ],
            'professional_help': [
                'need therapy', 'should see someone', 'need professional help',
                'mental health', 'counseling', 'psychiatrist'
            ],
            'crisis_intervention': [
                'emergency', 'crisis', 'immediate help', 'right now',
                'can\'t wait', 'urgent', 'desperate'
            ]
        }
    
    def analyze_emotions(self, text: str, context: Optional[Dict] = None) -> EmotionAnalysis:
        """
        Perform comprehensive emotion analysis on text
        
        Args:
            text: Input text to analyze
            context: Optional context from conversation history
            
        Returns:
            EmotionAnalysis with detailed emotional understanding
        """
        if not text or not text.strip():
            return self._create_empty_analysis()
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Detect primary emotions
        primary_emotions = self._detect_primary_emotions(normalized_text)
        
        # Analyze mood using Big Mood system
        mood_analysis = self.big_mood.classify_mood(text, context)
        
        # Extract emotional context
        emotional_context = self._extract_emotional_context(normalized_text)
        
        # Calculate intensity and complexity
        intensity_score = self._calculate_intensity_score(normalized_text, primary_emotions)
        complexity_score = self._calculate_complexity_score(primary_emotions, emotional_context)
        
        # Detect crisis indicators
        crisis_indicators = self._detect_crisis_indicators(normalized_text)
        
        # Identify support needs
        support_needs = self._identify_support_needs(normalized_text, primary_emotions)
        
        # Generate reasoning
        reasoning = self._generate_analysis_reasoning(
            primary_emotions, mood_analysis, emotional_context, crisis_indicators
        )
        
        return EmotionAnalysis(
            primary_emotions=primary_emotions,
            mood_analysis=mood_analysis,
            emotional_context=emotional_context,
            intensity_score=intensity_score,
            complexity_score=complexity_score,
            crisis_indicators=crisis_indicators,
            support_needs=support_needs,
            reasoning=reasoning
        )
    
    def _detect_primary_emotions(self, text: str) -> List[EmotionSignal]:
        """Detect primary emotions in text using lexical analysis"""
        emotions = []
        words = re.findall(r'\b\w+\b', text)
        
        for i, word in enumerate(words):
            for emotion_category, emotion_words in self.emotion_lexicon.items():
                if word in emotion_words:
                    intensity = emotion_words[word]
                    
                    # Apply intensity modifiers
                    modified_intensity = self._apply_intensity_modifiers(text, i, intensity)
                    
                    emotions.append(EmotionSignal(
                        emotion=emotion_category,
                        intensity=modified_intensity,
                        confidence=0.8,
                        source=word,
                        position=i
                    ))
        
        # Sort by intensity and return top emotions
        emotions.sort(key=lambda x: x.intensity, reverse=True)
        return emotions[:5]  # Return top 5 emotions
    
    def _apply_intensity_modifiers(self, text: str, word_position: int, base_intensity: float) -> float:
        """Apply intensity modifiers to emotion words"""
        words = text.split()
        modified_intensity = base_intensity
        
        # Check for intensity amplifiers near the emotion word
        for pattern in self.linguistic_patterns['intensity_amplifiers']:
            matches = re.finditer(pattern, text)
            for match in matches:
                match_words = match.group().split()
                match_start = text[:match.start()].count(' ')
                
                # If amplifier is near our emotion word
                if abs(match_start - word_position) <= 2:
                    amplifier = match_words[0].lower()
                    if amplifier in ['so', 'very']:
                        modified_intensity *= 1.2
                    elif amplifier in ['extremely', 'incredibly', 'absolutely']:
                        modified_intensity *= 1.4
                    elif amplifier in ['completely', 'totally', 'utterly']:
                        modified_intensity *= 1.5
        
        return min(modified_intensity, 1.0)
    
    def _extract_emotional_context(self, text: str) -> EmotionalContext:
        """Extract contextual information about emotional state"""
        
        # Analyze temporal patterns
        temporal_pattern = 'present'  # default
        if any(word in text for word in ['was', 'were', 'used to', 'before', 'yesterday']):
            temporal_pattern = 'past'
        elif any(word in text for word in ['will', 'going to', 'tomorrow', 'future', 'hope']):
            temporal_pattern = 'future'
        
        # Analyze certainty level
        certainty_level = 'certain'  # default
        if any(word in text for word in ['maybe', 'perhaps', 'might', 'could', 'unsure']):
            certainty_level = 'uncertain'
        elif '?' in text or any(word in text for word in ['why', 'how', 'what', 'when']):
            certainty_level = 'questioning'
        
        # Analyze social context
        social_context = 'self'  # default
        if any(word in text for word in ['we', 'us', 'our', 'together', 'relationship']):
            social_context = 'relationships'
        elif any(word in text for word in ['they', 'people', 'everyone', 'others']):
            social_context = 'others'
        
        # Analyze action orientation
        action_orientation = 'passive'  # default
        if any(word in text for word in ['will', 'going to', 'plan to', 'want to']):
            action_orientation = 'active'
        elif any(word in text for word in ['help', 'advice', 'support', 'guidance']):
            action_orientation = 'seeking_help'
        
        return EmotionalContext(
            temporal_pattern=temporal_pattern,
            certainty_level=certainty_level,
            social_context=social_context,
            action_orientation=action_orientation
        )
    
    def _calculate_intensity_score(self, text: str, emotions: List[EmotionSignal]) -> float:
        """Calculate overall emotional intensity score"""
        if not emotions:
            return 0.0
        
        # Base intensity from emotions
        emotion_intensity = sum(e.intensity for e in emotions) / len(emotions)
        
        # Linguistic intensity indicators
        linguistic_intensity = 0.0
        
        # Punctuation intensity
        exclamation_count = text.count('!')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        linguistic_intensity += min(exclamation_count * 0.1, 0.3)
        linguistic_intensity += min(caps_ratio * 0.5, 0.3)
        
        # Repetition intensity
        words = text.split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = 1 - (unique_words / len(words))
            linguistic_intensity += repetition_ratio * 0.2
        
        # Combine emotion and linguistic intensity
        total_intensity = (emotion_intensity * 0.7) + (linguistic_intensity * 0.3)
        
        return min(total_intensity, 1.0)
    
    def _calculate_complexity_score(self, emotions: List[EmotionSignal], context: EmotionalContext) -> float:
        """Calculate emotional complexity score"""
        complexity = 0.0
        
        # Multiple emotions increase complexity
        if len(emotions) > 1:
            complexity += 0.3
        if len(emotions) > 3:
            complexity += 0.2
        
        # Conflicting emotions increase complexity
        emotion_types = [e.emotion for e in emotions]
        if 'joy' in emotion_types and 'sadness' in emotion_types:
            complexity += 0.3
        if 'anger' in emotion_types and 'fear' in emotion_types:
            complexity += 0.2
        
        # Uncertain or questioning context increases complexity
        if context.certainty_level in ['uncertain', 'questioning']:
            complexity += 0.2
        
        # Social context adds complexity
        if context.social_context in ['relationships', 'others']:
            complexity += 0.1
        
        return min(complexity, 1.0)
    
    def _detect_crisis_indicators(self, text: str) -> List[str]:
        """Detect crisis indicators in text"""
        indicators = []
        
        for pattern in self.crisis_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                indicators.extend(matches)
        
        return list(set(indicators))  # Remove duplicates
    
    def _identify_support_needs(self, text: str, emotions: List[EmotionSignal]) -> List[str]:
        """Identify what type of support the person might need"""
        needs = []
        
        for need_type, indicators in self.support_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text:
                    needs.append(need_type)
                    break
        
        # Infer needs from emotions
        emotion_types = [e.emotion for e in emotions]
        
        if 'sadness' in emotion_types or 'fear' in emotion_types:
            if 'emotional_support' not in needs:
                needs.append('emotional_support')
        
        if 'anger' in emotion_types and 'frustration' in text:
            if 'practical_help' not in needs:
                needs.append('practical_help')
        
        return list(set(needs))
    
    def _generate_analysis_reasoning(self, emotions: List[EmotionSignal], mood: MoodAnalysis, 
                                   context: EmotionalContext, crisis: List[str]) -> str:
        """Generate human-readable reasoning for the analysis"""
        reasoning_parts = []
        
        # Primary emotions
        if emotions:
            top_emotions = [e.emotion for e in emotions[:3]]
            reasoning_parts.append(f"Primary emotions detected: {', '.join(top_emotions)}")
        
        # Mood classification
        reasoning_parts.append(f"Overall mood: {mood.primary_mood.value} ({mood.reasoning})")
        
        # Context
        if context.temporal_pattern != 'present':
            reasoning_parts.append(f"Temporal focus: {context.temporal_pattern}")
        
        if context.certainty_level != 'certain':
            reasoning_parts.append(f"Certainty level: {context.certainty_level}")
        
        # Crisis indicators
        if crisis:
            reasoning_parts.append(f"⚠️ Crisis indicators detected: {len(crisis)} patterns")
        
        return ". ".join(reasoning_parts)
    
    def _create_empty_analysis(self) -> EmotionAnalysis:
        """Create empty analysis for invalid input"""
        return EmotionAnalysis(
            primary_emotions=[],
            mood_analysis=MoodAnalysis(
                primary_mood=MoodColor.GREEN,
                confidence=0.3,
                reasoning="No text provided for analysis"
            ),
            emotional_context=EmotionalContext(
                temporal_pattern='present',
                certainty_level='certain',
                social_context='self',
                action_orientation='passive'
            ),
            intensity_score=0.0,
            complexity_score=0.0,
            crisis_indicators=[],
            support_needs=[],
            reasoning="No emotional content to analyze"
        )

