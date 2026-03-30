"""
WhisperLeaf Crisis Detection System
Advanced detection and response for emotional crisis situations
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CrisisLevel(Enum):
    """Crisis severity levels"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class CrisisType(Enum):
    """Types of crisis situations"""
    SUICIDAL_IDEATION = "suicidal_ideation"
    SELF_HARM = "self_harm"
    SEVERE_DEPRESSION = "severe_depression"
    PANIC_ATTACK = "panic_attack"
    PSYCHOTIC_EPISODE = "psychotic_episode"
    SUBSTANCE_ABUSE = "substance_abuse"
    DOMESTIC_VIOLENCE = "domestic_violence"
    EATING_DISORDER = "eating_disorder"
    GENERAL_DISTRESS = "general_distress"

@dataclass
class CrisisIndicator:
    """Individual crisis indicator found in text"""
    type: CrisisType
    severity: CrisisLevel
    confidence: float
    trigger_phrase: str
    context: str
    position: int

@dataclass
class CrisisAssessment:
    """Complete crisis assessment result"""
    overall_level: CrisisLevel
    primary_crisis_type: Optional[CrisisType]
    indicators: List[CrisisIndicator]
    risk_factors: List[str]
    protective_factors: List[str]
    immediate_actions: List[str]
    resources: List[Dict[str, str]]
    confidence: float
    reasoning: str

class CrisisDetector:
    """
    Advanced crisis detection system using multiple detection methods:
    - Pattern matching for explicit crisis language
    - Contextual analysis for implicit crisis indicators
    - Risk factor accumulation
    - Temporal pattern analysis
    """
    
    def __init__(self):
        self.crisis_patterns = self._initialize_crisis_patterns()
        self.risk_factors = self._initialize_risk_factors()
        self.protective_factors = self._initialize_protective_factors()
        self.crisis_resources = self._initialize_crisis_resources()
        self.severity_weights = self._initialize_severity_weights()
        
    def _initialize_crisis_patterns(self) -> Dict[CrisisType, Dict]:
        """Initialize crisis detection patterns for each crisis type"""
        return {
            CrisisType.SUICIDAL_IDEATION: {
                'critical': [
                    r'\b(?:want\s+to\s+die|wish\s+i\s+was\s+dead|kill\s+myself)\b',
                    r'\b(?:end\s+it\s+all|not\s+worth\s+living|better\s+off\s+dead)\b',
                    r'\b(?:suicide|suicidal|end\s+my\s+life|take\s+my\s+life)\b',
                    r'\b(?:planning\s+to\s+die|ready\s+to\s+die|time\s+to\s+go)\b'
                ],
                'high': [
                    r'\b(?:no\s+reason\s+to\s+live|life\s+is\s+meaningless|pointless\s+to\s+continue)\b',
                    r'\b(?:everyone\s+would\s+be\s+better\s+off|burden\s+to\s+everyone)\b',
                    r'\b(?:can\'t\s+take\s+it\s+anymore|reached\s+my\s+limit)\b'
                ],
                'moderate': [
                    r'\b(?:don\'t\s+want\s+to\s+be\s+here|wish\s+i\s+wasn\'t\s+born)\b',
                    r'\b(?:tired\s+of\s+living|exhausted\s+by\s+life)\b',
                    r'\b(?:what\'s\s+the\s+point|why\s+bother\s+continuing)\b'
                ]
            },
            
            CrisisType.SELF_HARM: {
                'critical': [
                    r'\b(?:cutting\s+myself|hurt\s+myself|harm\s+myself)\b',
                    r'\b(?:self\s+harm|self\s+injury|self\s+mutilation)\b',
                    r'\b(?:burning\s+myself|hitting\s+myself)\b'
                ],
                'high': [
                    r'\b(?:urge\s+to\s+cut|want\s+to\s+hurt|need\s+to\s+cut)\b',
                    r'\b(?:deserve\s+pain|need\s+to\s+feel\s+pain)\b',
                    r'\b(?:punish\s+myself|hate\s+my\s+body)\b'
                ],
                'moderate': [
                    r'\b(?:thinking\s+about\s+cutting|tempted\s+to\s+hurt)\b',
                    r'\b(?:used\s+to\s+cut|history\s+of\s+self\s+harm)\b'
                ]
            },
            
            CrisisType.SEVERE_DEPRESSION: {
                'high': [
                    r'\b(?:completely\s+hopeless|utterly\s+despair|total\s+darkness)\b',
                    r'\b(?:can\'t\s+function|can\'t\s+get\s+out\s+of\s+bed|can\'t\s+do\s+anything)\b',
                    r'\b(?:numb\s+to\s+everything|feel\s+nothing|emotionally\s+dead)\b'
                ],
                'moderate': [
                    r'\b(?:severely\s+depressed|major\s+depression|clinical\s+depression)\b',
                    r'\b(?:lost\s+all\s+hope|no\s+hope\s+left|hopeless\s+situation)\b',
                    r'\b(?:can\'t\s+see\s+a\s+future|no\s+future|everything\s+is\s+dark)\b'
                ]
            },
            
            CrisisType.PANIC_ATTACK: {
                'high': [
                    r'\b(?:panic\s+attack|having\s+a\s+panic\s+attack|can\'t\s+breathe)\b',
                    r'\b(?:heart\s+racing|chest\s+pain|feel\s+like\s+dying)\b',
                    r'\b(?:losing\s+control|going\s+crazy|losing\s+my\s+mind)\b'
                ],
                'moderate': [
                    r'\b(?:severe\s+anxiety|overwhelming\s+panic|intense\s+fear)\b',
                    r'\b(?:hyperventilating|shaking\s+uncontrollably|sweating\s+profusely)\b'
                ]
            },
            
            CrisisType.SUBSTANCE_ABUSE: {
                'high': [
                    r'\b(?:overdose|overdosed|too\s+much\s+drugs|too\s+much\s+alcohol)\b',
                    r'\b(?:can\'t\s+stop\s+drinking|can\'t\s+stop\s+using|addicted)\b',
                    r'\b(?:withdrawal|detox|need\s+a\s+fix)\b'
                ],
                'moderate': [
                    r'\b(?:drinking\s+too\s+much|using\s+drugs|substance\s+abuse)\b',
                    r'\b(?:relapsed|fell\s+off\s+the\s+wagon|back\s+to\s+using)\b'
                ]
            },
            
            CrisisType.DOMESTIC_VIOLENCE: {
                'critical': [
                    r'\b(?:he\s+hit\s+me|she\s+hit\s+me|being\s+abused|domestic\s+violence)\b',
                    r'\b(?:afraid\s+for\s+my\s+life|going\s+to\s+kill\s+me|threatened\s+to\s+hurt)\b'
                ],
                'high': [
                    r'\b(?:abusive\s+relationship|violent\s+partner|scared\s+of\s+him|scared\s+of\s+her)\b',
                    r'\b(?:controls\s+everything|won\'t\s+let\s+me\s+leave|isolates\s+me)\b'
                ]
            },
            
            CrisisType.EATING_DISORDER: {
                'high': [
                    r'\b(?:starving\s+myself|haven\'t\s+eaten|refusing\s+to\s+eat)\b',
                    r'\b(?:purging|throwing\s+up|laxatives|diet\s+pills)\b',
                    r'\b(?:anorexia|bulimia|binge\s+eating)\b'
                ],
                'moderate': [
                    r'\b(?:obsessed\s+with\s+weight|hate\s+my\s+body|fat\s+and\s+ugly)\b',
                    r'\b(?:extreme\s+diet|dangerous\s+weight\s+loss)\b'
                ]
            }
        }
    
    def _initialize_risk_factors(self) -> List[str]:
        """Initialize risk factors that increase crisis likelihood"""
        return [
            # Social isolation
            'alone', 'lonely', 'isolated', 'no friends', 'no family',
            'abandoned', 'rejected', 'outcast', 'nobody cares',
            
            # Hopelessness
            'hopeless', 'no hope', 'pointless', 'meaningless', 'no future',
            'nothing to live for', 'no way out', 'trapped',
            
            # Recent losses
            'lost my job', 'relationship ended', 'death in family', 'divorce',
            'breakup', 'fired', 'evicted', 'bankruptcy',
            
            # Mental health history
            'depression', 'anxiety', 'bipolar', 'ptsd', 'trauma',
            'mental illness', 'psychiatric', 'therapy', 'medication',
            
            # Substance use
            'drinking', 'drugs', 'alcohol', 'high', 'drunk', 'wasted',
            'addiction', 'substance', 'pills', 'cocaine', 'heroin',
            
            # Physical health
            'chronic pain', 'terminal illness', 'disability', 'sick',
            'medical condition', 'health problems',
            
            # Financial stress
            'broke', 'debt', 'money problems', 'can\'t pay', 'financial crisis',
            'homeless', 'eviction', 'foreclosure',
            
            # Legal problems
            'arrested', 'jail', 'prison', 'court', 'legal trouble',
            'lawsuit', 'criminal charges'
        ]
    
    def _initialize_protective_factors(self) -> List[str]:
        """Initialize protective factors that reduce crisis risk"""
        return [
            # Social support
            'family support', 'good friends', 'loving relationship', 'therapist',
            'support group', 'counselor', 'people who care', 'not alone',
            
            # Coping skills
            'meditation', 'exercise', 'therapy', 'coping strategies',
            'mindfulness', 'breathing exercises', 'journaling', 'art',
            
            # Hope and meaning
            'hope', 'future plans', 'goals', 'dreams', 'purpose',
            'meaning', 'reasons to live', 'things to look forward to',
            
            # Stability
            'stable job', 'good health', 'safe home', 'financial security',
            'routine', 'structure', 'stability',
            
            # Treatment
            'taking medication', 'seeing therapist', 'in treatment',
            'getting help', 'support system', 'professional help'
        ]
    
    def _initialize_crisis_resources(self) -> Dict[CrisisType, List[Dict]]:
        """Initialize crisis resources for each crisis type"""
        return {
            CrisisType.SUICIDAL_IDEATION: [
                {
                    'name': 'National Suicide Prevention Lifeline',
                    'contact': '988',
                    'description': '24/7 crisis support and suicide prevention',
                    'type': 'phone'
                },
                {
                    'name': 'Crisis Text Line',
                    'contact': 'Text HOME to 741741',
                    'description': '24/7 text-based crisis support',
                    'type': 'text'
                },
                {
                    'name': 'Emergency Services',
                    'contact': '911',
                    'description': 'For immediate emergency situations',
                    'type': 'emergency'
                }
            ],
            
            CrisisType.SELF_HARM: [
                {
                    'name': 'Self-Injury Outreach & Support',
                    'contact': 'sioutreach.org',
                    'description': 'Resources and support for self-injury',
                    'type': 'website'
                },
                {
                    'name': 'Crisis Text Line',
                    'contact': 'Text HOME to 741741',
                    'description': '24/7 text-based crisis support',
                    'type': 'text'
                }
            ],
            
            CrisisType.DOMESTIC_VIOLENCE: [
                {
                    'name': 'National Domestic Violence Hotline',
                    'contact': '1-800-799-7233',
                    'description': '24/7 support for domestic violence survivors',
                    'type': 'phone'
                },
                {
                    'name': 'Emergency Services',
                    'contact': '911',
                    'description': 'For immediate danger situations',
                    'type': 'emergency'
                }
            ],
            
            CrisisType.SUBSTANCE_ABUSE: [
                {
                    'name': 'SAMHSA National Helpline',
                    'contact': '1-800-662-4357',
                    'description': '24/7 treatment referral service',
                    'type': 'phone'
                }
            ],
            
            CrisisType.EATING_DISORDER: [
                {
                    'name': 'National Eating Disorders Association',
                    'contact': '1-800-931-2237',
                    'description': 'Support for eating disorders',
                    'type': 'phone'
                }
            ]
        }
    
    def _initialize_severity_weights(self) -> Dict[str, float]:
        """Initialize weights for calculating overall crisis severity"""
        return {
            'critical_patterns': 1.0,
            'high_patterns': 0.7,
            'moderate_patterns': 0.4,
            'low_patterns': 0.2,
            'risk_factors': 0.1,
            'protective_factors': -0.1,
            'multiple_types': 0.3,
            'temporal_urgency': 0.2
        }
    
    def assess_crisis(self, text: str, context: Optional[Dict] = None) -> CrisisAssessment:
        """
        Perform comprehensive crisis assessment on text input
        
        Args:
            text: Input text to analyze for crisis indicators
            context: Optional context from conversation history
            
        Returns:
            CrisisAssessment with detailed crisis analysis
        """
        if not text or not text.strip():
            return self._create_no_crisis_assessment()
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Detect crisis indicators
        indicators = self._detect_crisis_indicators(normalized_text)
        
        # Identify risk and protective factors
        risk_factors = self._identify_risk_factors(normalized_text)
        protective_factors = self._identify_protective_factors(normalized_text)
        
        # Calculate overall crisis level
        overall_level, confidence = self._calculate_crisis_level(
            indicators, risk_factors, protective_factors, context
        )
        
        # Determine primary crisis type
        primary_crisis_type = self._determine_primary_crisis_type(indicators)
        
        # Generate immediate actions
        immediate_actions = self._generate_immediate_actions(overall_level, primary_crisis_type)
        
        # Get relevant resources
        resources = self._get_relevant_resources(primary_crisis_type, overall_level)
        
        # Generate reasoning
        reasoning = self._generate_crisis_reasoning(
            overall_level, indicators, risk_factors, protective_factors
        )
        
        return CrisisAssessment(
            overall_level=overall_level,
            primary_crisis_type=primary_crisis_type,
            indicators=indicators,
            risk_factors=risk_factors,
            protective_factors=protective_factors,
            immediate_actions=immediate_actions,
            resources=resources,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _detect_crisis_indicators(self, text: str) -> List[CrisisIndicator]:
        """Detect crisis indicators in text using pattern matching"""
        indicators = []
        
        for crisis_type, patterns in self.crisis_patterns.items():
            for severity_level, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    for match in matches:
                        # Calculate confidence based on pattern specificity
                        confidence = self._calculate_pattern_confidence(pattern, match.group())
                        
                        # Get context around the match
                        context = self._extract_context(text, match.start(), match.end())
                        
                        indicators.append(CrisisIndicator(
                            type=crisis_type,
                            severity=CrisisLevel(severity_level),
                            confidence=confidence,
                            trigger_phrase=match.group(),
                            context=context,
                            position=match.start()
                        ))
        
        # Sort by severity and confidence
        indicators.sort(key=lambda x: (x.severity.value, x.confidence), reverse=True)
        
        return indicators
    
    def _identify_risk_factors(self, text: str) -> List[str]:
        """Identify risk factors present in the text"""
        found_factors = []
        
        for factor in self.risk_factors:
            if factor.lower() in text:
                found_factors.append(factor)
        
        return found_factors
    
    def _identify_protective_factors(self, text: str) -> List[str]:
        """Identify protective factors present in the text"""
        found_factors = []
        
        for factor in self.protective_factors:
            if factor.lower() in text:
                found_factors.append(factor)
        
        return found_factors
    
    def _calculate_crisis_level(self, indicators: List[CrisisIndicator], 
                              risk_factors: List[str], protective_factors: List[str],
                              context: Optional[Dict]) -> Tuple[CrisisLevel, float]:
        """Calculate overall crisis level and confidence"""
        
        if not indicators:
            return CrisisLevel.NONE, 0.9
        
        # Calculate base score from indicators
        score = 0.0
        weights = self.severity_weights
        
        for indicator in indicators:
            if indicator.severity == CrisisLevel.CRITICAL:
                score += weights['critical_patterns'] * indicator.confidence
            elif indicator.severity == CrisisLevel.HIGH:
                score += weights['high_patterns'] * indicator.confidence
            elif indicator.severity == CrisisLevel.MODERATE:
                score += weights['moderate_patterns'] * indicator.confidence
            else:
                score += weights['low_patterns'] * indicator.confidence
        
        # Add risk factors
        score += len(risk_factors) * weights['risk_factors']
        
        # Subtract protective factors
        score += len(protective_factors) * weights['protective_factors']
        
        # Multiple crisis types increase severity
        crisis_types = set(i.type for i in indicators)
        if len(crisis_types) > 1:
            score += weights['multiple_types']
        
        # Apply context adjustments
        if context:
            score = self._apply_context_to_score(score, context)
        
        # Determine crisis level from score
        if score >= 0.8:
            level = CrisisLevel.CRITICAL
        elif score >= 0.6:
            level = CrisisLevel.HIGH
        elif score >= 0.4:
            level = CrisisLevel.MODERATE
        elif score >= 0.2:
            level = CrisisLevel.LOW
        else:
            level = CrisisLevel.NONE
        
        # Calculate confidence
        confidence = min(score, 1.0) if indicators else 0.9
        
        return level, confidence
    
    def _determine_primary_crisis_type(self, indicators: List[CrisisIndicator]) -> Optional[CrisisType]:
        """Determine the primary crisis type from indicators"""
        if not indicators:
            return None
        
        # Count indicators by type and severity
        type_scores = {}
        
        for indicator in indicators:
            if indicator.type not in type_scores:
                type_scores[indicator.type] = 0
            
            # Weight by severity
            if indicator.severity == CrisisLevel.CRITICAL:
                type_scores[indicator.type] += 1.0
            elif indicator.severity == CrisisLevel.HIGH:
                type_scores[indicator.type] += 0.7
            elif indicator.severity == CrisisLevel.MODERATE:
                type_scores[indicator.type] += 0.4
            else:
                type_scores[indicator.type] += 0.2
        
        # Return type with highest score
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return None
    
    def _generate_immediate_actions(self, level: CrisisLevel, 
                                  crisis_type: Optional[CrisisType]) -> List[str]:
        """Generate immediate actions based on crisis level and type"""
        actions = []
        
        if level == CrisisLevel.CRITICAL:
            actions.extend([
                "Encourage immediate professional help",
                "Provide crisis hotline information",
                "Assess immediate safety",
                "Stay with the person if possible",
                "Consider emergency services if in immediate danger"
            ])
        elif level == CrisisLevel.HIGH:
            actions.extend([
                "Strongly encourage professional help",
                "Provide crisis resources",
                "Assess safety planning needs",
                "Offer continued support"
            ])
        elif level == CrisisLevel.MODERATE:
            actions.extend([
                "Suggest professional support",
                "Provide relevant resources",
                "Encourage safety planning",
                "Offer emotional support"
            ])
        elif level == CrisisLevel.LOW:
            actions.extend([
                "Monitor for escalation",
                "Provide supportive resources",
                "Encourage self-care"
            ])
        
        # Add crisis-type specific actions
        if crisis_type == CrisisType.SUICIDAL_IDEATION:
            actions.append("Create safety plan with specific coping strategies")
        elif crisis_type == CrisisType.DOMESTIC_VIOLENCE:
            actions.append("Discuss safety planning and escape routes")
        elif crisis_type == CrisisType.SUBSTANCE_ABUSE:
            actions.append("Discuss treatment options and support groups")
        
        return actions
    
    def _get_relevant_resources(self, crisis_type: Optional[CrisisType], 
                              level: CrisisLevel) -> List[Dict[str, str]]:
        """Get relevant crisis resources"""
        resources = []
        
        # Always include general crisis resources for moderate+ levels
        if level in [CrisisLevel.MODERATE, CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            resources.extend(self.crisis_resources.get(CrisisType.SUICIDAL_IDEATION, []))
        
        # Add specific resources for crisis type
        if crisis_type and crisis_type in self.crisis_resources:
            type_resources = self.crisis_resources[crisis_type]
            for resource in type_resources:
                if resource not in resources:
                    resources.append(resource)
        
        return resources
    
    def _calculate_pattern_confidence(self, pattern: str, match: str) -> float:
        """Calculate confidence score for pattern match"""
        # More specific patterns get higher confidence
        if len(pattern) > 50:  # Very specific pattern
            return 0.9
        elif len(pattern) > 30:  # Moderately specific
            return 0.8
        elif len(pattern) > 15:  # Somewhat specific
            return 0.7
        else:  # General pattern
            return 0.6
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around a pattern match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _apply_context_to_score(self, score: float, context: Dict) -> float:
        """Apply contextual factors to crisis score"""
        
        # Recent crisis history increases score
        if context.get('recent_crisis_history'):
            score += 0.2
        
        # Time of day factors
        if context.get('time_of_day') == 'night':
            score += 0.1  # Crisis more likely at night
        
        # Conversation length - longer conversations may indicate more serious issues
        if context.get('conversation_length', 0) > 10:
            score += 0.1
        
        # Recent mood decline
        if context.get('mood_trend') == 'declining':
            score += 0.15
        
        return score
    
    def _generate_crisis_reasoning(self, level: CrisisLevel, indicators: List[CrisisIndicator],
                                 risk_factors: List[str], protective_factors: List[str]) -> str:
        """Generate human-readable reasoning for crisis assessment"""
        reasoning_parts = []
        
        # Crisis level
        reasoning_parts.append(f"Crisis level: {level.value}")
        
        # Indicators
        if indicators:
            indicator_count = len(indicators)
            crisis_types = list(set(i.type.value for i in indicators))
            reasoning_parts.append(f"Detected {indicator_count} crisis indicators")
            reasoning_parts.append(f"Crisis types: {', '.join(crisis_types)}")
        
        # Risk factors
        if risk_factors:
            reasoning_parts.append(f"Risk factors present: {len(risk_factors)}")
        
        # Protective factors
        if protective_factors:
            reasoning_parts.append(f"Protective factors present: {len(protective_factors)}")
        
        # Specific high-risk indicators
        critical_indicators = [i for i in indicators if i.severity == CrisisLevel.CRITICAL]
        if critical_indicators:
            reasoning_parts.append("⚠️ Critical risk indicators detected")
        
        return ". ".join(reasoning_parts)
    
    def _create_no_crisis_assessment(self) -> CrisisAssessment:
        """Create assessment for no crisis detected"""
        return CrisisAssessment(
            overall_level=CrisisLevel.NONE,
            primary_crisis_type=None,
            indicators=[],
            risk_factors=[],
            protective_factors=[],
            immediate_actions=["Continue supportive conversation"],
            resources=[],
            confidence=0.9,
            reasoning="No crisis indicators detected in text"
        )
    
    def get_crisis_response_template(self, assessment: CrisisAssessment) -> Dict[str, str]:
        """Get response template for crisis situation"""
        if assessment.overall_level == CrisisLevel.CRITICAL:
            return {
                'opening': "I'm very concerned about what you've shared with me.",
                'validation': "You're going through something incredibly difficult right now.",
                'immediate_support': "Your safety is the most important thing right now.",
                'resources': "I want to connect you with people who can provide immediate help.",
                'presence': "You don't have to face this alone."
            }
        elif assessment.overall_level == CrisisLevel.HIGH:
            return {
                'opening': "I can hear that you're in a lot of pain right now.",
                'validation': "These feelings must be overwhelming.",
                'support': "There are people who can help you through this.",
                'resources': "Let me share some resources that might be helpful.",
                'hope': "Things can get better with the right support."
            }
        else:
            return {
                'opening': "Thank you for sharing what you're going through.",
                'validation': "It takes courage to talk about difficult feelings.",
                'support': "I'm here to listen and support you.",
                'resources': "There are resources available if you need additional help."
            }

