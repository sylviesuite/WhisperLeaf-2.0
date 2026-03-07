"""
WhisperLeaf Adaptive Tone Engine
Dynamically adjusts communication style based on emotional context
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from .big_mood import MoodColor, MoodAnalysis
from .emotion_detector import EmotionAnalysis, EmotionalContext

logger = logging.getLogger(__name__)

class ToneStyle(Enum):
    """Available tone styles for responses"""
    GENTLE = "gentle"
    WARM = "warm"
    CALMING = "calming"
    ENGAGING = "engaging"
    SUPPORTIVE = "supportive"
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    SERIOUS = "serious"

class IntensityLevel(Enum):
    """Response intensity levels"""
    SOFT = "soft"
    MODERATE = "moderate"
    STRONG = "strong"
    INTENSE = "intense"

@dataclass
class ToneProfile:
    """Complete tone profile for response generation"""
    primary_style: ToneStyle
    intensity: IntensityLevel
    formality: str  # casual, balanced, formal
    directness: str  # indirect, balanced, direct
    emotional_approach: str  # validating, exploring, problem_solving
    language_patterns: List[str]
    avoid_patterns: List[str]
    crisis_mode: bool = False

@dataclass
class ResponseGuidance:
    """Guidance for generating appropriate responses"""
    tone_profile: ToneProfile
    suggested_openings: List[str]
    key_themes: List[str]
    emotional_validation: List[str]
    support_strategies: List[str]
    crisis_protocols: List[str]
    reasoning: str

class AdaptiveToneEngine:
    """
    Generates appropriate tone and response guidance based on emotional analysis
    Adapts communication style to match user's emotional needs
    """
    
    def __init__(self):
        self.mood_tone_mapping = self._initialize_mood_tone_mapping()
        self.crisis_tone_overrides = self._initialize_crisis_overrides()
        self.language_patterns = self._initialize_language_patterns()
        self.validation_phrases = self._initialize_validation_phrases()
        self.support_strategies = self._initialize_support_strategies()
        
    def _initialize_mood_tone_mapping(self) -> Dict[MoodColor, Dict]:
        """Initialize tone mappings for each Big Mood color"""
        return {
            MoodColor.BLUE: {
                'primary_style': ToneStyle.GENTLE,
                'intensity': IntensityLevel.SOFT,
                'formality': 'balanced',
                'directness': 'indirect',
                'emotional_approach': 'validating',
                'themes': ['comfort', 'hope', 'understanding', 'presence'],
                'avoid': ['cheerful_dismissal', 'quick_fixes', 'minimizing']
            },
            MoodColor.GREEN: {
                'primary_style': ToneStyle.WARM,
                'intensity': IntensityLevel.MODERATE,
                'formality': 'casual',
                'directness': 'balanced',
                'emotional_approach': 'exploring',
                'themes': ['growth', 'reflection', 'possibilities', 'balance'],
                'avoid': ['overwhelming', 'intense_emotions', 'disruption']
            },
            MoodColor.YELLOW: {
                'primary_style': ToneStyle.CALMING,
                'intensity': IntensityLevel.SOFT,
                'formality': 'balanced',
                'directness': 'indirect',
                'emotional_approach': 'validating',
                'themes': ['safety', 'grounding', 'control', 'breathing'],
                'avoid': ['urgency', 'pressure', 'overwhelming_info']
            },
            MoodColor.PURPLE: {
                'primary_style': ToneStyle.ENGAGING,
                'intensity': IntensityLevel.MODERATE,
                'formality': 'casual',
                'directness': 'balanced',
                'emotional_approach': 'exploring',
                'themes': ['curiosity', 'creativity', 'growth', 'possibilities'],
                'avoid': ['dampening', 'overly_practical', 'discouraging']
            },
            MoodColor.RED: {
                'primary_style': ToneStyle.SUPPORTIVE,
                'intensity': IntensityLevel.MODERATE,
                'formality': 'balanced',
                'directness': 'balanced',
                'emotional_approach': 'validating',
                'themes': ['understanding', 'validation', 'regulation', 'respect'],
                'avoid': ['confrontational', 'escalating', 'dismissive']
            }
        }
    
    def _initialize_crisis_overrides(self) -> Dict[str, Dict]:
        """Initialize tone overrides for crisis situations"""
        return {
            'suicidal_ideation': {
                'primary_style': ToneStyle.GENTLE,
                'intensity': IntensityLevel.STRONG,
                'formality': 'formal',
                'directness': 'direct',
                'emotional_approach': 'validating',
                'crisis_mode': True
            },
            'self_harm': {
                'primary_style': ToneStyle.SUPPORTIVE,
                'intensity': IntensityLevel.STRONG,
                'formality': 'balanced',
                'directness': 'direct',
                'emotional_approach': 'validating',
                'crisis_mode': True
            },
            'severe_distress': {
                'primary_style': ToneStyle.CALMING,
                'intensity': IntensityLevel.MODERATE,
                'formality': 'balanced',
                'directness': 'balanced',
                'emotional_approach': 'validating',
                'crisis_mode': True
            }
        }
    
    def _initialize_language_patterns(self) -> Dict[ToneStyle, Dict]:
        """Initialize language patterns for each tone style"""
        return {
            ToneStyle.GENTLE: {
                'openings': [
                    "I can hear that you're going through something difficult",
                    "It sounds like you're carrying a lot right now",
                    "I'm here with you in this moment",
                    "What you're feeling makes complete sense"
                ],
                'patterns': [
                    'soft_acknowledgment', 'gentle_validation', 'hope_offering',
                    'presence_statements', 'comfort_language'
                ],
                'avoid': [
                    'harsh_words', 'demanding_language', 'urgent_tone',
                    'dismissive_phrases', 'overly_cheerful'
                ]
            },
            ToneStyle.WARM: {
                'openings': [
                    "Thank you for sharing that with me",
                    "I appreciate you opening up about this",
                    "It's wonderful that you're reflecting on this",
                    "I'm glad you're taking time to explore your feelings"
                ],
                'patterns': [
                    'appreciation', 'warmth', 'encouragement',
                    'natural_conversation', 'supportive_engagement'
                ],
                'avoid': [
                    'cold_language', 'clinical_tone', 'overwhelming_intensity',
                    'formal_distance', 'impersonal_responses'
                ]
            },
            ToneStyle.CALMING: {
                'openings': [
                    "Let's take this one step at a time",
                    "You're safe here, and we can work through this together",
                    "It's okay to feel overwhelmed - let's slow down",
                    "Take a deep breath with me"
                ],
                'patterns': [
                    'grounding_language', 'safety_assurance', 'slow_pacing',
                    'breathing_reminders', 'present_moment_focus'
                ],
                'avoid': [
                    'urgent_language', 'pressure_words', 'overwhelming_information',
                    'fast_paced_responses', 'anxiety_inducing_phrases'
                ]
            },
            ToneStyle.ENGAGING: {
                'openings': [
                    "That's such an interesting perspective",
                    "I love how you're thinking about this",
                    "What a fascinating way to look at it",
                    "Your curiosity about this is wonderful"
                ],
                'patterns': [
                    'curiosity_encouragement', 'exploration_support', 'growth_language',
                    'possibility_focus', 'creative_engagement'
                ],
                'avoid': [
                    'dampening_language', 'overly_practical', 'discouraging_words',
                    'limiting_statements', 'pessimistic_tone'
                ]
            },
            ToneStyle.SUPPORTIVE: {
                'openings': [
                    "Your feelings are completely valid",
                    "I understand why you'd feel that way",
                    "It makes sense that you're experiencing this",
                    "You have every right to feel what you're feeling"
                ],
                'patterns': [
                    'validation_language', 'understanding_statements', 'support_offers',
                    'strength_recognition', 'empathy_expressions'
                ],
                'avoid': [
                    'invalidating_language', 'dismissive_tone', 'judgment_words',
                    'minimizing_phrases', 'comparison_statements'
                ]
            }
        }
    
    def _initialize_validation_phrases(self) -> Dict[str, List[str]]:
        """Initialize emotional validation phrases"""
        return {
            'sadness': [
                "It's okay to feel sad about this",
                "Sadness is a natural response to loss and disappointment",
                "Your sadness shows how much this matters to you",
                "Grief and sadness are part of being human"
            ],
            'anger': [
                "Your anger is understandable given the situation",
                "It makes sense that you'd feel frustrated about this",
                "Anger often shows us what we value and care about",
                "Your feelings of anger are valid"
            ],
            'fear': [
                "Fear is a natural response to uncertainty",
                "It's normal to feel scared when facing the unknown",
                "Your anxiety shows that you care about the outcome",
                "Fear often means we're stepping outside our comfort zone"
            ],
            'joy': [
                "I'm so glad you're experiencing this happiness",
                "It's wonderful to hear the joy in your words",
                "You deserve to feel this good",
                "Your happiness is contagious"
            ],
            'confusion': [
                "It's okay not to have all the answers right now",
                "Confusion often comes before clarity",
                "Not knowing can be uncomfortable, and that's normal",
                "Sometimes sitting with uncertainty is part of the process"
            ]
        }
    
    def _initialize_support_strategies(self) -> Dict[str, List[str]]:
        """Initialize support strategies for different situations"""
        return {
            'emotional_support': [
                "I'm here to listen without judgment",
                "Your feelings matter and deserve to be heard",
                "You don't have to go through this alone",
                "Take all the time you need to process this"
            ],
            'practical_help': [
                "Let's break this down into manageable steps",
                "What feels like the most important thing to address first?",
                "Sometimes it helps to start with small, concrete actions",
                "We can explore different options together"
            ],
            'crisis_intervention': [
                "Your life has value and meaning",
                "These intense feelings won't last forever",
                "There are people who want to help you through this",
                "You've survived difficult times before"
            ],
            'grounding': [
                "Let's focus on what you can control right now",
                "Notice five things you can see around you",
                "Feel your feet on the ground",
                "Take three slow, deep breaths with me"
            ]
        }
    
    def generate_tone_profile(self, emotion_analysis: EmotionAnalysis, 
                            context: Optional[Dict] = None) -> ResponseGuidance:
        """
        Generate appropriate tone profile and response guidance
        
        Args:
            emotion_analysis: Complete emotional analysis of user input
            context: Optional conversation context
            
        Returns:
            ResponseGuidance with tone profile and response strategies
        """
        
        # Check for crisis situations first
        if emotion_analysis.crisis_indicators:
            return self._generate_crisis_response_guidance(emotion_analysis)
        
        # Get base tone mapping from mood
        mood = emotion_analysis.mood_analysis.primary_mood
        base_mapping = self.mood_tone_mapping[mood]
        
        # Create tone profile
        tone_profile = self._create_tone_profile(base_mapping, emotion_analysis, context)
        
        # Generate response guidance
        guidance = self._generate_response_guidance(tone_profile, emotion_analysis)
        
        return guidance
    
    def _create_tone_profile(self, base_mapping: Dict, emotion_analysis: EmotionAnalysis,
                           context: Optional[Dict]) -> ToneProfile:
        """Create detailed tone profile from base mapping and analysis"""
        
        # Start with base mapping
        profile = ToneProfile(
            primary_style=base_mapping['primary_style'],
            intensity=base_mapping['intensity'],
            formality=base_mapping['formality'],
            directness=base_mapping['directness'],
            emotional_approach=base_mapping['emotional_approach'],
            language_patterns=base_mapping['themes'],
            avoid_patterns=base_mapping['avoid']
        )
        
        # Adjust based on emotional intensity
        if emotion_analysis.intensity_score > 0.8:
            profile.intensity = IntensityLevel.STRONG
        elif emotion_analysis.intensity_score < 0.3:
            profile.intensity = IntensityLevel.SOFT
        
        # Adjust based on emotional complexity
        if emotion_analysis.complexity_score > 0.7:
            profile.directness = 'indirect'  # More gentle approach for complex emotions
            profile.emotional_approach = 'validating'
        
        # Adjust based on support needs
        if 'professional_help' in emotion_analysis.support_needs:
            profile.formality = 'formal'
            profile.directness = 'direct'
        
        # Apply context adjustments
        if context:
            profile = self._apply_context_adjustments(profile, context)
        
        return profile
    
    def _apply_context_adjustments(self, profile: ToneProfile, context: Dict) -> ToneProfile:
        """Apply contextual adjustments to tone profile"""
        
        # Time of day adjustments
        if context.get('time_of_day') == 'night':
            if profile.intensity == IntensityLevel.STRONG:
                profile.intensity = IntensityLevel.MODERATE  # Softer at night
        
        # Conversation history adjustments
        if context.get('conversation_length', 0) > 5:
            profile.formality = 'casual'  # More casual in longer conversations
        
        # Recent mood pattern adjustments
        if context.get('recent_mood_pattern') == 'declining':
            profile.primary_style = ToneStyle.GENTLE
            profile.emotional_approach = 'validating'
        
        return profile
    
    def _generate_crisis_response_guidance(self, emotion_analysis: EmotionAnalysis) -> ResponseGuidance:
        """Generate specialized guidance for crisis situations"""
        
        # Determine crisis type
        crisis_type = 'severe_distress'  # default
        crisis_indicators = emotion_analysis.crisis_indicators
        
        if any('suicide' in indicator or 'die' in indicator for indicator in crisis_indicators):
            crisis_type = 'suicidal_ideation'
        elif any('harm' in indicator or 'hurt' in indicator for indicator in crisis_indicators):
            crisis_type = 'self_harm'
        
        # Get crisis override settings
        crisis_settings = self.crisis_tone_overrides[crisis_type]
        
        # Create crisis tone profile
        tone_profile = ToneProfile(
            primary_style=crisis_settings['primary_style'],
            intensity=crisis_settings['intensity'],
            formality=crisis_settings['formality'],
            directness=crisis_settings['directness'],
            emotional_approach=crisis_settings['emotional_approach'],
            language_patterns=['crisis_support', 'immediate_safety', 'professional_resources'],
            avoid_patterns=['minimizing', 'dismissive', 'overwhelming'],
            crisis_mode=True
        )
        
        # Generate crisis-specific guidance
        return ResponseGuidance(
            tone_profile=tone_profile,
            suggested_openings=self._get_crisis_openings(crisis_type),
            key_themes=['immediate_safety', 'professional_help', 'hope', 'support'],
            emotional_validation=self._get_crisis_validation(crisis_type),
            support_strategies=self.support_strategies['crisis_intervention'],
            crisis_protocols=self._get_crisis_protocols(crisis_type),
            reasoning=f"Crisis response mode activated for {crisis_type}"
        )
    
    def _generate_response_guidance(self, tone_profile: ToneProfile, 
                                  emotion_analysis: EmotionAnalysis) -> ResponseGuidance:
        """Generate comprehensive response guidance"""
        
        # Get language patterns for the tone style
        style_patterns = self.language_patterns[tone_profile.primary_style]
        
        # Generate suggested openings
        suggested_openings = style_patterns['openings']
        
        # Determine key themes
        key_themes = tone_profile.language_patterns
        
        # Get appropriate emotional validation
        emotional_validation = self._get_emotional_validation(emotion_analysis)
        
        # Get support strategies
        support_strategies = self._get_support_strategies(emotion_analysis.support_needs)
        
        # Generate reasoning
        reasoning = self._generate_tone_reasoning(tone_profile, emotion_analysis)
        
        return ResponseGuidance(
            tone_profile=tone_profile,
            suggested_openings=suggested_openings,
            key_themes=key_themes,
            emotional_validation=emotional_validation,
            support_strategies=support_strategies,
            crisis_protocols=[],
            reasoning=reasoning
        )
    
    def _get_emotional_validation(self, emotion_analysis: EmotionAnalysis) -> List[str]:
        """Get appropriate emotional validation phrases"""
        validation = []
        
        # Get validation for primary emotions
        for emotion_signal in emotion_analysis.primary_emotions[:3]:
            emotion_type = emotion_signal.emotion
            if emotion_type in self.validation_phrases:
                validation.extend(self.validation_phrases[emotion_type][:2])
        
        # Add general validation if no specific emotions found
        if not validation:
            validation = [
                "Your feelings are completely valid",
                "It makes sense that you're experiencing this"
            ]
        
        return validation[:3]  # Limit to 3 validation phrases
    
    def _get_support_strategies(self, support_needs: List[str]) -> List[str]:
        """Get appropriate support strategies based on identified needs"""
        strategies = []
        
        for need in support_needs:
            if need in self.support_strategies:
                strategies.extend(self.support_strategies[need][:2])
        
        # Add default emotional support if no specific needs identified
        if not strategies:
            strategies = self.support_strategies['emotional_support'][:2]
        
        return strategies[:4]  # Limit to 4 strategies
    
    def _get_crisis_openings(self, crisis_type: str) -> List[str]:
        """Get crisis-appropriate opening statements"""
        crisis_openings = {
            'suicidal_ideation': [
                "I'm really concerned about you and want you to know that you're not alone",
                "Thank you for trusting me with these difficult feelings",
                "Your life has value, and I'm here to support you through this"
            ],
            'self_harm': [
                "I'm worried about you and want to help you stay safe",
                "These urges to hurt yourself must be really overwhelming",
                "You deserve care and support, not harm"
            ],
            'severe_distress': [
                "I can see you're in a lot of pain right now",
                "You're going through something really difficult",
                "I'm here with you in this difficult moment"
            ]
        }
        
        return crisis_openings.get(crisis_type, crisis_openings['severe_distress'])
    
    def _get_crisis_validation(self, crisis_type: str) -> List[str]:
        """Get crisis-appropriate validation statements"""
        return [
            "These feelings are overwhelming, but they won't last forever",
            "You're showing incredible strength by reaching out",
            "It's okay to not be okay right now"
        ]
    
    def _get_crisis_protocols(self, crisis_type: str) -> List[str]:
        """Get crisis intervention protocols"""
        protocols = [
            "Encourage immediate professional help",
            "Provide crisis hotline information",
            "Assess immediate safety",
            "Maintain supportive presence"
        ]
        
        if crisis_type == 'suicidal_ideation':
            protocols.extend([
                "National Suicide Prevention Lifeline: 988",
                "Crisis Text Line: Text HOME to 741741",
                "Emergency services: 911 if in immediate danger"
            ])
        
        return protocols
    
    def _generate_tone_reasoning(self, tone_profile: ToneProfile, 
                               emotion_analysis: EmotionAnalysis) -> str:
        """Generate reasoning for tone selection"""
        reasoning_parts = []
        
        # Primary style reasoning
        reasoning_parts.append(f"Selected {tone_profile.primary_style.value} tone")
        
        # Mood-based reasoning
        mood = emotion_analysis.mood_analysis.primary_mood
        reasoning_parts.append(f"based on {mood.value} mood classification")
        
        # Intensity reasoning
        if emotion_analysis.intensity_score > 0.7:
            reasoning_parts.append("with heightened intensity due to strong emotional signals")
        elif emotion_analysis.intensity_score < 0.3:
            reasoning_parts.append("with gentle intensity for subtle emotional content")
        
        # Support needs reasoning
        if emotion_analysis.support_needs:
            needs_text = ", ".join(emotion_analysis.support_needs)
            reasoning_parts.append(f"addressing {needs_text} needs")
        
        return ". ".join(reasoning_parts)
    
    def get_tone_guidelines(self, tone_profile: ToneProfile) -> Dict[str, List[str]]:
        """Get detailed guidelines for implementing the tone profile"""
        style_patterns = self.language_patterns[tone_profile.primary_style]
        
        return {
            'do_use': [
                f"Use {tone_profile.primary_style.value} language patterns",
                f"Maintain {tone_profile.intensity.value} intensity level",
                f"Apply {tone_profile.formality} formality",
                f"Use {tone_profile.directness} communication style"
            ] + style_patterns['patterns'],
            'avoid': style_patterns['avoid'] + tone_profile.avoid_patterns,
            'key_phrases': style_patterns['openings'][:3],
            'emotional_approach': [tone_profile.emotional_approach]
        }

