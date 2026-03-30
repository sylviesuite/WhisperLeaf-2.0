"""
WhisperLeaf Emotional Processor
Main integration point for all emotional intelligence components
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

from .big_mood import BigMoodClassifier, MoodColor, MoodAnalysis
from .emotion_detector import EmotionDetector, EmotionAnalysis
from .tone_engine import AdaptiveToneEngine, ResponseGuidance, ToneProfile
from .crisis_detector import CrisisDetector, CrisisAssessment, CrisisLevel

logger = logging.getLogger(__name__)

@dataclass
class EmotionalResponse:
    """Complete emotional response with all analysis components"""
    emotion_analysis: EmotionAnalysis
    crisis_assessment: CrisisAssessment
    response_guidance: ResponseGuidance
    ai_prompt: str
    safety_flags: List[str]
    processing_metadata: Dict
    timestamp: datetime

class EmotionalProcessor:
    """
    Main emotional intelligence processor that coordinates all components:
    - Emotion detection and mood classification
    - Crisis assessment and safety protocols
    - Adaptive tone generation
    - Response guidance for AI system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize all emotional intelligence components
        self.big_mood = BigMoodClassifier()
        self.emotion_detector = EmotionDetector()
        self.tone_engine = AdaptiveToneEngine()
        self.crisis_detector = CrisisDetector()
        
        # Processing settings
        self.crisis_threshold = self.config.get('crisis_threshold', CrisisLevel.MODERATE)
        self.safety_mode = self.config.get('safety_mode', True)
        self.context_window = self.config.get('context_window', 5)
        
        logger.info("EmotionalProcessor initialized with all components")
    
    def process_emotional_input(self, text: str, context: Optional[Dict] = None) -> EmotionalResponse:
        """
        Process user input through complete emotional intelligence pipeline
        
        Args:
            text: User input text to analyze
            context: Optional conversation context and history
            
        Returns:
            EmotionalResponse with complete analysis and guidance
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Comprehensive emotion analysis
            emotion_analysis = self.emotion_detector.analyze_emotions(text, context)
            
            # Step 2: Crisis assessment and safety evaluation
            crisis_assessment = self.crisis_detector.assess_crisis(text, context)
            
            # Step 3: Generate adaptive tone and response guidance
            response_guidance = self.tone_engine.generate_tone_profile(emotion_analysis, context)
            
            # Step 4: Create AI prompt with emotional intelligence
            ai_prompt = self._generate_ai_prompt(emotion_analysis, crisis_assessment, response_guidance)
            
            # Step 5: Generate safety flags and warnings
            safety_flags = self._generate_safety_flags(crisis_assessment, emotion_analysis)
            
            # Step 6: Create processing metadata
            processing_metadata = self._create_processing_metadata(
                start_time, emotion_analysis, crisis_assessment, response_guidance
            )
            
            return EmotionalResponse(
                emotion_analysis=emotion_analysis,
                crisis_assessment=crisis_assessment,
                response_guidance=response_guidance,
                ai_prompt=ai_prompt,
                safety_flags=safety_flags,
                processing_metadata=processing_metadata,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in emotional processing: {e}")
            return self._create_error_response(text, str(e))
    
    def _generate_ai_prompt(self, emotion_analysis: EmotionAnalysis, 
                           crisis_assessment: CrisisAssessment,
                           response_guidance: ResponseGuidance) -> str:
        """Generate AI prompt with emotional intelligence guidance"""
        
        prompt_parts = []
        
        # Base emotional context
        mood = emotion_analysis.mood_analysis.primary_mood
        mood_description = self.big_mood.get_mood_description(mood)
        
        prompt_parts.append(f"EMOTIONAL CONTEXT:")
        prompt_parts.append(f"User is experiencing {mood.value} mood ({mood_description['emotions']})")
        
        # Primary emotions
        if emotion_analysis.primary_emotions:
            emotions = [e.emotion for e in emotion_analysis.primary_emotions[:3]]
            prompt_parts.append(f"Primary emotions: {', '.join(emotions)}")
        
        # Emotional intensity and complexity
        prompt_parts.append(f"Emotional intensity: {emotion_analysis.intensity_score:.1f}/1.0")
        if emotion_analysis.complexity_score > 0.5:
            prompt_parts.append(f"Complex emotional state (multiple conflicting emotions)")
        
        # Crisis assessment
        if crisis_assessment.overall_level != CrisisLevel.NONE:
            prompt_parts.append(f"\n⚠️ CRISIS ALERT: {crisis_assessment.overall_level.value.upper()} level")
            if crisis_assessment.primary_crisis_type:
                prompt_parts.append(f"Crisis type: {crisis_assessment.primary_crisis_type.value}")
            prompt_parts.append("PRIORITY: Emotional safety and crisis support")
        
        # Tone guidance
        tone_profile = response_guidance.tone_profile
        prompt_parts.append(f"\nTONE GUIDANCE:")
        prompt_parts.append(f"Style: {tone_profile.primary_style.value}")
        prompt_parts.append(f"Intensity: {tone_profile.intensity.value}")
        prompt_parts.append(f"Approach: {tone_profile.emotional_approach}")
        
        # Response guidance
        if response_guidance.suggested_openings:
            prompt_parts.append(f"\nSUGGESTED OPENINGS:")
            for opening in response_guidance.suggested_openings[:2]:
                prompt_parts.append(f"- {opening}")
        
        # Emotional validation
        if response_guidance.emotional_validation:
            prompt_parts.append(f"\nEMOTIONAL VALIDATION:")
            for validation in response_guidance.emotional_validation[:2]:
                prompt_parts.append(f"- {validation}")
        
        # Support strategies
        if response_guidance.support_strategies:
            prompt_parts.append(f"\nSUPPORT STRATEGIES:")
            for strategy in response_guidance.support_strategies[:2]:
                prompt_parts.append(f"- {strategy}")
        
        # Crisis protocols
        if response_guidance.crisis_protocols:
            prompt_parts.append(f"\nCRISIS PROTOCOLS:")
            for protocol in response_guidance.crisis_protocols[:3]:
                prompt_parts.append(f"- {protocol}")
        
        # Key themes to include
        if response_guidance.key_themes:
            themes = ', '.join(response_guidance.key_themes[:4])
            prompt_parts.append(f"\nKEY THEMES: {themes}")
        
        # What to avoid
        avoid_patterns = tone_profile.avoid_patterns
        if avoid_patterns:
            avoid_text = ', '.join(avoid_patterns[:3])
            prompt_parts.append(f"\nAVOID: {avoid_text}")
        
        # Constitutional guidance
        prompt_parts.append(f"\nCONSTITUTIONAL GUIDANCE:")
        prompt_parts.append("- Prioritize user emotional safety and wellbeing")
        prompt_parts.append("- Provide empathetic, non-judgmental support")
        prompt_parts.append("- Validate emotions while offering hope")
        prompt_parts.append("- Encourage professional help when appropriate")
        
        # Final instruction
        prompt_parts.append(f"\nRESPOND as WhisperLeaf with deep empathy, emotional intelligence, and appropriate tone.")
        
        return "\n".join(prompt_parts)
    
    def _generate_safety_flags(self, crisis_assessment: CrisisAssessment, 
                             emotion_analysis: EmotionAnalysis) -> List[str]:
        """Generate safety flags for monitoring and intervention"""
        flags = []
        
        # Crisis level flags
        if crisis_assessment.overall_level == CrisisLevel.CRITICAL:
            flags.append("CRITICAL_CRISIS_DETECTED")
        elif crisis_assessment.overall_level == CrisisLevel.HIGH:
            flags.append("HIGH_CRISIS_DETECTED")
        elif crisis_assessment.overall_level == CrisisLevel.MODERATE:
            flags.append("MODERATE_CRISIS_DETECTED")
        
        # Specific crisis type flags
        if crisis_assessment.primary_crisis_type:
            flags.append(f"CRISIS_TYPE_{crisis_assessment.primary_crisis_type.value.upper()}")
        
        # Crisis indicator flags
        if crisis_assessment.indicators:
            flags.append(f"CRISIS_INDICATORS_{len(crisis_assessment.indicators)}")
        
        # High emotional intensity flag
        if emotion_analysis.intensity_score > 0.8:
            flags.append("HIGH_EMOTIONAL_INTENSITY")
        
        # Complex emotional state flag
        if emotion_analysis.complexity_score > 0.7:
            flags.append("COMPLEX_EMOTIONAL_STATE")
        
        # Support need flags
        for need in emotion_analysis.support_needs:
            flags.append(f"SUPPORT_NEED_{need.upper()}")
        
        # Mood-specific flags
        mood = emotion_analysis.mood_analysis.primary_mood
        if mood == MoodColor.BLUE and emotion_analysis.intensity_score > 0.6:
            flags.append("SEVERE_SADNESS_DETECTED")
        elif mood == MoodColor.YELLOW and emotion_analysis.intensity_score > 0.7:
            flags.append("SEVERE_ANXIETY_DETECTED")
        elif mood == MoodColor.RED and emotion_analysis.intensity_score > 0.7:
            flags.append("SEVERE_ANGER_DETECTED")
        
        return flags
    
    def _create_processing_metadata(self, start_time: datetime, emotion_analysis: EmotionAnalysis,
                                  crisis_assessment: CrisisAssessment, 
                                  response_guidance: ResponseGuidance) -> Dict:
        """Create metadata about the processing pipeline"""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'processing_time_seconds': processing_time,
            'components_used': [
                'big_mood_classifier',
                'emotion_detector', 
                'crisis_detector',
                'adaptive_tone_engine'
            ],
            'mood_classification': {
                'primary_mood': emotion_analysis.mood_analysis.primary_mood.value,
                'confidence': emotion_analysis.mood_analysis.confidence,
                'secondary_mood': emotion_analysis.mood_analysis.secondary_mood.value if emotion_analysis.mood_analysis.secondary_mood else None
            },
            'emotion_detection': {
                'primary_emotions_count': len(emotion_analysis.primary_emotions),
                'intensity_score': emotion_analysis.intensity_score,
                'complexity_score': emotion_analysis.complexity_score
            },
            'crisis_assessment': {
                'level': crisis_assessment.overall_level.value,
                'confidence': crisis_assessment.confidence,
                'indicators_count': len(crisis_assessment.indicators),
                'risk_factors_count': len(crisis_assessment.risk_factors)
            },
            'tone_adaptation': {
                'primary_style': response_guidance.tone_profile.primary_style.value,
                'intensity': response_guidance.tone_profile.intensity.value,
                'crisis_mode': response_guidance.tone_profile.crisis_mode
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_error_response(self, text: str, error: str) -> EmotionalResponse:
        """Create error response when processing fails"""
        logger.error(f"Creating error response for: {error}")
        
        # Create minimal safe response
        from .big_mood import MoodAnalysis, MoodColor
        from .emotion_detector import EmotionAnalysis, EmotionalContext
        from .crisis_detector import CrisisAssessment, CrisisLevel
        from .tone_engine import ResponseGuidance, ToneProfile, ToneStyle, IntensityLevel
        
        # Safe defaults
        mood_analysis = MoodAnalysis(
            primary_mood=MoodColor.GREEN,
            confidence=0.3,
            reasoning="Error in processing - using safe defaults"
        )
        
        emotional_context = EmotionalContext(
            temporal_pattern='present',
            certainty_level='uncertain',
            social_context='self',
            action_orientation='passive'
        )
        
        emotion_analysis = EmotionAnalysis(
            primary_emotions=[],
            mood_analysis=mood_analysis,
            emotional_context=emotional_context,
            intensity_score=0.5,
            complexity_score=0.0,
            crisis_indicators=[],
            support_needs=['emotional_support'],
            reasoning=f"Processing error: {error}"
        )
        
        crisis_assessment = CrisisAssessment(
            overall_level=CrisisLevel.NONE,
            primary_crisis_type=None,
            indicators=[],
            risk_factors=[],
            protective_factors=[],
            immediate_actions=["Provide supportive response"],
            resources=[],
            confidence=0.5,
            reasoning="Error in crisis assessment - assuming safe"
        )
        
        tone_profile = ToneProfile(
            primary_style=ToneStyle.SUPPORTIVE,
            intensity=IntensityLevel.MODERATE,
            formality='balanced',
            directness='balanced',
            emotional_approach='validating',
            language_patterns=['support', 'understanding'],
            avoid_patterns=['technical_language', 'overwhelming']
        )
        
        response_guidance = ResponseGuidance(
            tone_profile=tone_profile,
            suggested_openings=["I'm here to listen and support you"],
            key_themes=['support', 'understanding', 'presence'],
            emotional_validation=["Your feelings are valid"],
            support_strategies=["Provide emotional support"],
            crisis_protocols=[],
            reasoning="Error recovery mode - using supportive defaults"
        )
        
        ai_prompt = """
        EMOTIONAL CONTEXT: Processing error occurred - using safe supportive mode
        
        TONE GUIDANCE:
        Style: supportive
        Intensity: moderate
        Approach: validating
        
        RESPONSE GUIDANCE:
        - Provide warm, supportive response
        - Acknowledge any difficulties shared
        - Offer continued support and listening
        - Avoid technical language or overwhelming information
        
        RESPOND as WhisperLeaf with empathy and support, acknowledging that you're here to help.
        """
        
        return EmotionalResponse(
            emotion_analysis=emotion_analysis,
            crisis_assessment=crisis_assessment,
            response_guidance=response_guidance,
            ai_prompt=ai_prompt,
            safety_flags=["PROCESSING_ERROR"],
            processing_metadata={
                'error': error,
                'fallback_mode': True,
                'timestamp': datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
    
    def get_emotional_summary(self, response: EmotionalResponse) -> Dict[str, str]:
        """Get human-readable summary of emotional analysis"""
        mood = response.emotion_analysis.mood_analysis.primary_mood
        crisis_level = response.crisis_assessment.overall_level
        
        summary = {
            'mood': f"{mood.value} mood",
            'intensity': f"{response.emotion_analysis.intensity_score:.1f}/1.0 intensity",
            'crisis_level': crisis_level.value,
            'tone_style': response.response_guidance.tone_profile.primary_style.value,
            'support_needs': ', '.join(response.emotion_analysis.support_needs) if response.emotion_analysis.support_needs else 'general support'
        }
        
        if response.emotion_analysis.primary_emotions:
            emotions = [e.emotion for e in response.emotion_analysis.primary_emotions[:3]]
            summary['primary_emotions'] = ', '.join(emotions)
        
        if response.safety_flags:
            summary['safety_flags'] = ', '.join(response.safety_flags)
        
        return summary
    
    def update_context(self, context: Dict, response: EmotionalResponse) -> Dict:
        """Update conversation context with emotional analysis results"""
        if not context:
            context = {}
        
        # Update mood history
        if 'mood_history' not in context:
            context['mood_history'] = []
        
        context['mood_history'].append({
            'mood': response.emotion_analysis.mood_analysis.primary_mood.value,
            'intensity': response.emotion_analysis.intensity_score,
            'timestamp': response.timestamp.isoformat()
        })
        
        # Keep only recent history
        context['mood_history'] = context['mood_history'][-self.context_window:]
        
        # Update crisis history
        if response.crisis_assessment.overall_level != CrisisLevel.NONE:
            if 'crisis_history' not in context:
                context['crisis_history'] = []
            
            context['crisis_history'].append({
                'level': response.crisis_assessment.overall_level.value,
                'type': response.crisis_assessment.primary_crisis_type.value if response.crisis_assessment.primary_crisis_type else None,
                'timestamp': response.timestamp.isoformat()
            })
            
            context['crisis_history'] = context['crisis_history'][-5:]  # Keep last 5 crisis events
        
        # Update conversation metadata
        context['last_emotional_analysis'] = response.timestamp.isoformat()
        context['conversation_length'] = context.get('conversation_length', 0) + 1
        
        return context

