"""
WhisperLeaf Big Mood Classification System
Maps complex emotions to 5 intuitive color-coded categories
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MoodColor(Enum):
    """Big Mood color categories"""
    BLUE = "blue"      # Sadness, grief, melancholy
    GREEN = "green"    # Calm, balanced, content
    YELLOW = "yellow"  # Anxiety, worry, stress
    PURPLE = "purple"  # Creative, inspired, curious
    RED = "red"        # Anger, frustration, intensity

@dataclass
class MoodAnalysis:
    """Result of mood classification"""
    primary_mood: MoodColor
    confidence: float
    secondary_mood: Optional[MoodColor] = None
    intensity: float = 0.5
    indicators: List[str] = None
    reasoning: str = ""

class BigMoodClassifier:
    """
    Classifies emotional content into the Big Mood system
    Uses keyword analysis, linguistic patterns, and contextual cues
    """
    
    def __init__(self):
        self.mood_keywords = self._initialize_mood_keywords()
        self.intensity_modifiers = self._initialize_intensity_modifiers()
        self.negation_words = {'not', 'no', 'never', 'hardly', 'barely', 'scarcely'}
        
    def _initialize_mood_keywords(self) -> Dict[MoodColor, Dict[str, float]]:
        """Initialize keyword mappings for each mood with confidence weights"""
        return {
            MoodColor.BLUE: {
                # Core sadness indicators
                'sad': 0.9, 'sadness': 0.9, 'depressed': 0.95, 'depression': 0.95,
                'grief': 0.9, 'grieving': 0.9, 'mourning': 0.85, 'loss': 0.8,
                'heartbroken': 0.9, 'devastated': 0.85, 'crushed': 0.8,
                'melancholy': 0.8, 'blue': 0.7, 'down': 0.7, 'low': 0.6,
                'hopeless': 0.9, 'despair': 0.9, 'despairing': 0.9,
                'empty': 0.8, 'hollow': 0.8, 'numb': 0.8, 'void': 0.8,
                'crying': 0.8, 'tears': 0.7, 'weeping': 0.8, 'sobbing': 0.9,
                'lonely': 0.8, 'alone': 0.6, 'isolated': 0.8, 'abandoned': 0.9,
                'hurt': 0.7, 'pain': 0.7, 'ache': 0.7, 'suffering': 0.8,
                'broken': 0.8, 'shattered': 0.9, 'lost': 0.7, 'defeated': 0.8,
                'worthless': 0.9, 'useless': 0.8, 'failure': 0.8, 'disappointed': 0.7
            },
            
            MoodColor.GREEN: {
                # Calm and balanced indicators
                'calm': 0.9, 'peaceful': 0.9, 'serene': 0.9, 'tranquil': 0.9,
                'content': 0.8, 'satisfied': 0.8, 'comfortable': 0.7, 'relaxed': 0.8,
                'balanced': 0.8, 'centered': 0.8, 'grounded': 0.8, 'stable': 0.7,
                'happy': 0.8, 'joy': 0.8, 'joyful': 0.8, 'pleased': 0.7,
                'good': 0.6, 'fine': 0.6, 'okay': 0.6, 'alright': 0.6,
                'grateful': 0.8, 'thankful': 0.8, 'blessed': 0.8, 'appreciative': 0.8,
                'hopeful': 0.8, 'optimistic': 0.8, 'positive': 0.7, 'bright': 0.7,
                'warm': 0.7, 'cozy': 0.7, 'safe': 0.7, 'secure': 0.7,
                'gentle': 0.7, 'soft': 0.6, 'kind': 0.7, 'loving': 0.8,
                'mindful': 0.8, 'present': 0.7, 'aware': 0.7, 'clear': 0.7
            },
            
            MoodColor.YELLOW: {
                # Anxiety and stress indicators
                'anxious': 0.9, 'anxiety': 0.9, 'worried': 0.9, 'worry': 0.9,
                'stressed': 0.9, 'stress': 0.9, 'tense': 0.8, 'tension': 0.8,
                'nervous': 0.8, 'nerves': 0.8, 'jittery': 0.8, 'restless': 0.8,
                'panic': 0.95, 'panicked': 0.95, 'panicking': 0.95, 'frantic': 0.9,
                'overwhelmed': 0.9, 'swamped': 0.8, 'buried': 0.8, 'drowning': 0.9,
                'scared': 0.8, 'afraid': 0.8, 'fearful': 0.8, 'terrified': 0.9,
                'uncertain': 0.7, 'unsure': 0.7, 'confused': 0.7, 'lost': 0.7,
                'racing': 0.8, 'spinning': 0.8, 'spiraling': 0.9, 'chaotic': 0.8,
                'pressure': 0.8, 'burden': 0.8, 'weight': 0.7, 'heavy': 0.7,
                'tight': 0.7, 'constricted': 0.8, 'suffocating': 0.9, 'trapped': 0.8,
                'agitated': 0.8, 'restless': 0.8, 'uneasy': 0.8, 'disturbed': 0.8
            },
            
            MoodColor.PURPLE: {
                # Creative and inspired indicators
                'creative': 0.9, 'inspired': 0.9, 'inspiration': 0.9, 'imaginative': 0.8,
                'curious': 0.8, 'wonder': 0.8, 'wondering': 0.8, 'fascinated': 0.8,
                'excited': 0.8, 'enthusiasm': 0.8, 'enthusiastic': 0.8, 'energetic': 0.8,
                'motivated': 0.8, 'driven': 0.8, 'passionate': 0.9, 'engaged': 0.8,
                'exploring': 0.8, 'discovering': 0.8, 'learning': 0.7, 'growing': 0.7,
                'artistic': 0.8, 'expressive': 0.8, 'innovative': 0.8, 'original': 0.8,
                'dreaming': 0.8, 'visionary': 0.8, 'imaginative': 0.8, 'inventive': 0.8,
                'playful': 0.7, 'fun': 0.7, 'adventure': 0.8, 'adventurous': 0.8,
                'bright': 0.7, 'vibrant': 0.8, 'alive': 0.8, 'electric': 0.8,
                'flowing': 0.7, 'fluid': 0.7, 'dynamic': 0.8, 'expansive': 0.8,
                'possibility': 0.8, 'potential': 0.8, 'opportunity': 0.7, 'open': 0.7
            },
            
            MoodColor.RED: {
                # Anger and intensity indicators
                'angry': 0.9, 'anger': 0.9, 'mad': 0.8, 'furious': 0.95,
                'rage': 0.95, 'enraged': 0.95, 'livid': 0.9, 'irate': 0.9,
                'frustrated': 0.9, 'frustration': 0.9, 'irritated': 0.8, 'annoyed': 0.7,
                'pissed': 0.9, 'outraged': 0.9, 'indignant': 0.8, 'resentful': 0.8,
                'hostile': 0.9, 'aggressive': 0.9, 'violent': 0.9, 'explosive': 0.9,
                'heated': 0.8, 'hot': 0.7, 'burning': 0.8, 'fire': 0.8,
                'intense': 0.8, 'fierce': 0.8, 'powerful': 0.7, 'strong': 0.6,
                'boiling': 0.9, 'steaming': 0.8, 'seething': 0.9, 'fuming': 0.9,
                'bitter': 0.8, 'harsh': 0.8, 'sharp': 0.7, 'cutting': 0.8,
                'demanding': 0.7, 'insistent': 0.7, 'forceful': 0.8, 'urgent': 0.7,
                'injustice': 0.8, 'unfair': 0.8, 'wrong': 0.7, 'betrayed': 0.8
            }
        }
    
    def _initialize_intensity_modifiers(self) -> Dict[str, float]:
        """Initialize words that modify emotional intensity"""
        return {
            # High intensity
            'extremely': 1.5, 'incredibly': 1.4, 'absolutely': 1.3, 'completely': 1.3,
            'totally': 1.3, 'utterly': 1.4, 'deeply': 1.3, 'profoundly': 1.4,
            'intensely': 1.4, 'severely': 1.4, 'desperately': 1.5, 'overwhelmingly': 1.5,
            
            # Medium-high intensity
            'very': 1.2, 'really': 1.2, 'quite': 1.1, 'pretty': 1.1,
            'fairly': 1.1, 'rather': 1.1, 'significantly': 1.2, 'considerably': 1.2,
            
            # Low intensity
            'somewhat': 0.8, 'slightly': 0.7, 'a bit': 0.7, 'a little': 0.7,
            'kind of': 0.8, 'sort of': 0.8, 'mildly': 0.7, 'barely': 0.6,
            
            # Temporal modifiers
            'always': 1.3, 'constantly': 1.3, 'continuously': 1.3, 'forever': 1.4,
            'never': 1.2, 'sometimes': 0.8, 'occasionally': 0.7, 'rarely': 0.7
        }
    
    def classify_mood(self, text: str, context: Optional[Dict] = None) -> MoodAnalysis:
        """
        Classify the emotional mood of text input
        
        Args:
            text: Input text to analyze
            context: Optional context from previous interactions
            
        Returns:
            MoodAnalysis with primary mood, confidence, and details
        """
        if not text or not text.strip():
            return MoodAnalysis(
                primary_mood=MoodColor.GREEN,
                confidence=0.3,
                reasoning="No text provided for analysis"
            )
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Calculate mood scores
        mood_scores = self._calculate_mood_scores(normalized_text)
        
        # Apply intensity modifiers
        mood_scores = self._apply_intensity_modifiers(normalized_text, mood_scores)
        
        # Handle negations
        mood_scores = self._handle_negations(normalized_text, mood_scores)
        
        # Apply context if available
        if context:
            mood_scores = self._apply_context(mood_scores, context)
        
        # Determine primary and secondary moods
        sorted_moods = sorted(mood_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary_mood = sorted_moods[0][0]
        primary_confidence = sorted_moods[0][1]
        
        secondary_mood = None
        if len(sorted_moods) > 1 and sorted_moods[1][1] > 0.3:
            secondary_mood = sorted_moods[1][0]
        
        # Calculate overall intensity
        intensity = self._calculate_intensity(normalized_text, primary_confidence)
        
        # Generate reasoning
        indicators = self._find_mood_indicators(normalized_text, primary_mood)
        reasoning = self._generate_reasoning(primary_mood, indicators, primary_confidence)
        
        return MoodAnalysis(
            primary_mood=primary_mood,
            confidence=min(primary_confidence, 1.0),
            secondary_mood=secondary_mood,
            intensity=intensity,
            indicators=indicators,
            reasoning=reasoning
        )
    
    def _calculate_mood_scores(self, text: str) -> Dict[MoodColor, float]:
        """Calculate base mood scores from keyword matching"""
        mood_scores = {mood: 0.0 for mood in MoodColor}
        
        words = re.findall(r'\b\w+\b', text)
        
        for mood, keywords in self.mood_keywords.items():
            for word in words:
                if word in keywords:
                    mood_scores[mood] += keywords[word]
        
        # Normalize scores
        total_score = sum(mood_scores.values())
        if total_score > 0:
            for mood in mood_scores:
                mood_scores[mood] /= total_score
        else:
            # Default to green (neutral) if no keywords found
            mood_scores[MoodColor.GREEN] = 0.5
        
        return mood_scores
    
    def _apply_intensity_modifiers(self, text: str, mood_scores: Dict[MoodColor, float]) -> Dict[MoodColor, float]:
        """Apply intensity modifiers to mood scores"""
        words = text.split()
        
        for i, word in enumerate(words):
            if word in self.intensity_modifiers:
                modifier = self.intensity_modifiers[word]
                
                # Apply modifier to nearby mood words (within 3 words)
                for j in range(max(0, i-3), min(len(words), i+4)):
                    if j != i:
                        nearby_word = words[j]
                        for mood, keywords in self.mood_keywords.items():
                            if nearby_word in keywords:
                                mood_scores[mood] *= modifier
        
        return mood_scores
    
    def _handle_negations(self, text: str, mood_scores: Dict[MoodColor, float]) -> Dict[MoodColor, float]:
        """Handle negation words that reverse emotional meaning"""
        words = text.split()
        
        for i, word in enumerate(words):
            if word in self.negation_words:
                # Apply negation to nearby mood words (within 2 words)
                for j in range(i+1, min(len(words), i+3)):
                    nearby_word = words[j]
                    for mood, keywords in self.mood_keywords.items():
                        if nearby_word in keywords:
                            # Reduce the mood score and boost opposite moods
                            mood_scores[mood] *= 0.3
                            
                            # Boost neutral mood when negating emotions
                            mood_scores[MoodColor.GREEN] += 0.2
        
        return mood_scores
    
    def _apply_context(self, mood_scores: Dict[MoodColor, float], context: Dict) -> Dict[MoodColor, float]:
        """Apply contextual information to mood scores"""
        # Apply recent mood history
        if 'recent_moods' in context:
            recent_moods = context['recent_moods']
            for mood in recent_moods:
                if mood in mood_scores:
                    mood_scores[mood] *= 1.1  # Slight boost for consistency
        
        # Apply time of day context
        if 'time_of_day' in context:
            time_of_day = context['time_of_day']
            if time_of_day == 'night':
                mood_scores[MoodColor.BLUE] *= 1.1  # Sadness more common at night
                mood_scores[MoodColor.YELLOW] *= 1.1  # Anxiety more common at night
        
        return mood_scores
    
    def _calculate_intensity(self, text: str, confidence: float) -> float:
        """Calculate emotional intensity from text patterns"""
        intensity = 0.5  # Base intensity
        
        # Punctuation indicators
        exclamation_count = text.count('!')
        question_count = text.count('?')
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        
        # Adjust intensity based on patterns
        intensity += min(exclamation_count * 0.1, 0.3)
        intensity += min(question_count * 0.05, 0.2)
        intensity += min(caps_ratio * 0.5, 0.3)
        
        # Repetition patterns
        words = text.split()
        repeated_words = len(words) - len(set(words))
        intensity += min(repeated_words * 0.05, 0.2)
        
        # Confidence affects intensity
        intensity *= confidence
        
        return min(intensity, 1.0)
    
    def _find_mood_indicators(self, text: str, mood: MoodColor) -> List[str]:
        """Find specific words that indicated the classified mood"""
        indicators = []
        words = re.findall(r'\b\w+\b', text)
        
        if mood in self.mood_keywords:
            for word in words:
                if word in self.mood_keywords[mood]:
                    indicators.append(word)
        
        return indicators[:5]  # Limit to top 5 indicators
    
    def _generate_reasoning(self, mood: MoodColor, indicators: List[str], confidence: float) -> str:
        """Generate human-readable reasoning for the mood classification"""
        mood_descriptions = {
            MoodColor.BLUE: "sadness, grief, or melancholy",
            MoodColor.GREEN: "calm, balance, or contentment", 
            MoodColor.YELLOW: "anxiety, worry, or stress",
            MoodColor.PURPLE: "creativity, inspiration, or curiosity",
            MoodColor.RED: "anger, frustration, or intensity"
        }
        
        description = mood_descriptions.get(mood, "emotional content")
        
        if indicators:
            indicator_text = ", ".join(indicators[:3])
            reasoning = f"Detected {description} based on indicators: {indicator_text}"
        else:
            reasoning = f"Detected {description} from overall emotional tone"
        
        confidence_text = "high" if confidence > 0.7 else "moderate" if confidence > 0.4 else "low"
        reasoning += f" (confidence: {confidence_text})"
        
        return reasoning
    
    def get_mood_description(self, mood: MoodColor) -> Dict[str, str]:
        """Get detailed description of a mood color"""
        descriptions = {
            MoodColor.BLUE: {
                "name": "Blue Mood",
                "emotions": "Sadness, grief, melancholy, loss",
                "characteristics": "Gentle, reflective, processing difficult emotions",
                "response_style": "Validating, comforting, hope-offering",
                "avoid": "Dismissive cheerfulness, minimizing feelings"
            },
            MoodColor.GREEN: {
                "name": "Green Mood", 
                "emotions": "Calm, balanced, content, peaceful",
                "characteristics": "Stable, grounded, open to conversation",
                "response_style": "Warm, natural, supportive engagement",
                "avoid": "Overwhelming intensity, disrupting peace"
            },
            MoodColor.YELLOW: {
                "name": "Yellow Mood",
                "emotions": "Anxiety, worry, stress, nervousness", 
                "characteristics": "Heightened alertness, seeking safety",
                "response_style": "Calming, grounding, reassuring",
                "avoid": "Adding pressure, urgency, or overwhelm"
            },
            MoodColor.PURPLE: {
                "name": "Purple Mood",
                "emotions": "Creativity, inspiration, curiosity, wonder",
                "characteristics": "Engaged, exploring, open to possibilities",
                "response_style": "Encouraging, exploratory, growth-oriented",
                "avoid": "Dampening enthusiasm, being overly practical"
            },
            MoodColor.RED: {
                "name": "Red Mood",
                "emotions": "Anger, frustration, intensity, passion",
                "characteristics": "High energy, strong feelings, need for expression",
                "response_style": "Calm, non-confrontational, validating",
                "avoid": "Escalating, arguing, dismissing feelings"
            }
        }
        
        return descriptions.get(mood, {})

