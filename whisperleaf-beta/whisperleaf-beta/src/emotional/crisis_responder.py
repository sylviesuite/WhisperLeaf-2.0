"""
WhisperLeaf Crisis Responder
Emergency response system for crisis situations
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass

from .safety_monitor import SafetyAlert, SafetyLevel, InterventionType

logger = logging.getLogger(__name__)

class CrisisLevel(Enum):
    """Crisis severity levels"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class ResponseProtocol(Enum):
    """Crisis response protocols"""
    STANDARD_SUPPORT = "standard_support"
    ENHANCED_SUPPORT = "enhanced_support"
    CRISIS_INTERVENTION = "crisis_intervention"
    EMERGENCY_PROTOCOL = "emergency_protocol"

@dataclass
class CrisisResponse:
    """Crisis response with specific guidance and resources"""
    response_id: str
    timestamp: datetime
    crisis_level: CrisisLevel
    protocol: ResponseProtocol
    immediate_response: str
    follow_up_actions: List[str]
    resources: List[Dict[str, str]]
    safety_plan_elements: List[str]
    escalation_triggers: List[str]
    monitoring_required: bool

class CrisisResponder:
    """
    Crisis response system for emergency emotional situations
    Provides structured, evidence-based crisis intervention
    """
    
    def __init__(self):
        self.crisis_resources = self._load_crisis_resources()
        self.response_protocols = self._load_response_protocols()
        self.safety_plan_templates = self._load_safety_plan_templates()
        
        # Crisis response statistics
        self.response_stats = {
            'total_crisis_responses': 0,
            'emergency_protocols_activated': 0,
            'safety_plans_created': 0,
            'resource_referrals': 0,
            'last_crisis_response': None
        }
        
        # Active crisis tracking
        self.active_crises: Dict[str, Dict[str, Any]] = {}
        
        logger.info("CrisisResponder initialized with emergency protocols")
    
    def _load_crisis_resources(self) -> Dict[str, List[Dict[str, str]]]:
        """Load crisis intervention resources"""
        return {
            'immediate_help': [
                {
                    'name': 'National Suicide Prevention Lifeline',
                    'contact': '988',
                    'description': '24/7 crisis support and suicide prevention',
                    'type': 'phone'
                },
                {
                    'name': 'Crisis Text Line',
                    'contact': 'Text HOME to 741741',
                    'description': '24/7 crisis support via text message',
                    'type': 'text'
                },
                {
                    'name': 'Emergency Services',
                    'contact': '911',
                    'description': 'Immediate emergency response',
                    'type': 'emergency'
                }
            ],
            
            'mental_health_support': [
                {
                    'name': 'SAMHSA National Helpline',
                    'contact': '1-800-662-4357',
                    'description': 'Treatment referral and information service',
                    'type': 'phone'
                },
                {
                    'name': 'National Alliance on Mental Illness (NAMI)',
                    'contact': '1-800-950-6264',
                    'description': 'Mental health support and information',
                    'type': 'phone'
                },
                {
                    'name': 'Psychology Today Therapist Finder',
                    'contact': 'psychologytoday.com',
                    'description': 'Find local mental health professionals',
                    'type': 'website'
                }
            ],
            
            'specialized_support': [
                {
                    'name': 'National Domestic Violence Hotline',
                    'contact': '1-800-799-7233',
                    'description': 'Support for domestic violence situations',
                    'type': 'phone'
                },
                {
                    'name': 'RAINN National Sexual Assault Hotline',
                    'contact': '1-800-656-4673',
                    'description': 'Support for sexual assault survivors',
                    'type': 'phone'
                },
                {
                    'name': 'Trans Lifeline',
                    'contact': '877-565-8860',
                    'description': 'Crisis support for transgender individuals',
                    'type': 'phone'
                },
                {
                    'name': 'TrevorLifeline (LGBTQ Youth)',
                    'contact': '1-866-488-7386',
                    'description': 'Crisis support for LGBTQ youth',
                    'type': 'phone'
                }
            ],
            
            'online_resources': [
                {
                    'name': 'Crisis Chat',
                    'contact': 'suicidepreventionlifeline.org/chat',
                    'description': 'Online crisis chat support',
                    'type': 'chat'
                },
                {
                    'name': 'IMAlive',
                    'contact': 'imalive.org',
                    'description': 'Online crisis chat with volunteers',
                    'type': 'chat'
                },
                {
                    'name': 'BetterHelp',
                    'contact': 'betterhelp.com',
                    'description': 'Online therapy and counseling',
                    'type': 'therapy'
                }
            ]
        }
    
    def _load_response_protocols(self) -> Dict[ResponseProtocol, Dict[str, Any]]:
        """Load crisis response protocols"""
        return {
            ResponseProtocol.STANDARD_SUPPORT: {
                'description': 'Standard emotional support response',
                'immediate_actions': [
                    'Validate feelings and experiences',
                    'Provide empathetic listening',
                    'Offer general mental health resources',
                    'Encourage professional help if needed'
                ],
                'response_template': "I hear how difficult this is for you. Your feelings are completely valid, and you don't have to go through this alone.",
                'monitoring_level': 'low',
                'escalation_threshold': 0.5
            },
            
            ResponseProtocol.ENHANCED_SUPPORT: {
                'description': 'Enhanced support for moderate distress',
                'immediate_actions': [
                    'Provide crisis resources and hotlines',
                    'Suggest immediate coping strategies',
                    'Encourage reaching out to support network',
                    'Offer to help create safety plan'
                ],
                'response_template': "I'm concerned about you and want to help. You're not alone in this, and there are people and resources available to support you right now.",
                'monitoring_level': 'moderate',
                'escalation_threshold': 0.7
            },
            
            ResponseProtocol.CRISIS_INTERVENTION: {
                'description': 'Active crisis intervention protocol',
                'immediate_actions': [
                    'Assess immediate safety and suicide risk',
                    'Provide crisis hotline numbers immediately',
                    'Encourage contacting emergency services if needed',
                    'Help develop immediate safety plan',
                    'Stay engaged until safety is established'
                ],
                'response_template': "I'm very concerned about your safety right now. Please know that you're not alone, and there are people who want to help you through this crisis.",
                'monitoring_level': 'high',
                'escalation_threshold': 0.9
            },
            
            ResponseProtocol.EMERGENCY_PROTOCOL: {
                'description': 'Emergency response for imminent danger',
                'immediate_actions': [
                    'Strongly encourage immediate emergency contact',
                    'Provide emergency numbers (911, crisis lines)',
                    'Suggest going to emergency room if safe to do so',
                    'Encourage contacting trusted person immediately',
                    'Provide immediate safety planning'
                ],
                'response_template': "This sounds like an emergency situation. Your safety is the most important thing right now. Please contact emergency services (911) or a crisis hotline (988) immediately.",
                'monitoring_level': 'critical',
                'escalation_threshold': 1.0
            }
        }
    
    def _load_safety_plan_templates(self) -> Dict[str, List[str]]:
        """Load safety plan templates for different situations"""
        return {
            'immediate_safety': [
                "Remove or secure any means of self-harm",
                "Stay in a safe, public place if possible",
                "Contact a trusted friend or family member",
                "Call a crisis hotline for immediate support",
                "Go to the nearest emergency room if in immediate danger"
            ],
            
            'coping_strategies': [
                "Practice deep breathing exercises",
                "Use grounding techniques (5-4-3-2-1 method)",
                "Listen to calming music or sounds",
                "Take a warm shower or bath",
                "Write in a journal or express feelings creatively",
                "Engage in gentle physical activity like walking"
            ],
            
            'support_network': [
                "Identify 3 trusted people you can contact",
                "Keep crisis hotline numbers easily accessible",
                "Join a support group (online or in-person)",
                "Connect with a mental health professional",
                "Inform trusted friends about your situation"
            ],
            
            'warning_signs': [
                "Recognize your personal warning signs",
                "Notice changes in sleep or appetite",
                "Be aware of increased isolation",
                "Monitor thoughts of self-harm or suicide",
                "Pay attention to increased substance use"
            ],
            
            'professional_help': [
                "Schedule appointment with therapist or counselor",
                "Consider psychiatric evaluation if needed",
                "Explore medication options with doctor",
                "Look into intensive outpatient programs",
                "Consider inpatient treatment if recommended"
            ]
        }
    
    def assess_crisis_level(self, safety_alert: SafetyAlert, context: Dict[str, Any]) -> CrisisLevel:
        """
        Assess crisis level based on safety alert and context
        
        Args:
            safety_alert: Safety alert from monitoring system
            context: Additional context about the situation
            
        Returns:
            CrisisLevel indicating severity of crisis
        """
        
        # Base assessment on safety alert
        if safety_alert.safety_level == SafetyLevel.CRITICAL:
            base_level = CrisisLevel.CRITICAL
        elif safety_alert.safety_level == SafetyLevel.DANGER:
            base_level = CrisisLevel.HIGH
        elif safety_alert.safety_level == SafetyLevel.WARNING:
            base_level = CrisisLevel.MODERATE
        elif safety_alert.safety_level == SafetyLevel.CAUTION:
            base_level = CrisisLevel.LOW
        else:
            base_level = CrisisLevel.NONE
        
        # Adjust based on additional risk factors
        risk_multiplier = 1.0
        
        # Check for immediate danger indicators
        immediate_danger_keywords = [
            'tonight', 'right now', 'going to', 'plan to',
            'have the', 'ready to', 'decided to'
        ]
        
        message = safety_alert.trigger_content.lower()
        if any(keyword in message for keyword in immediate_danger_keywords):
            risk_multiplier += 0.5
        
        # Check for means/method mentions
        means_keywords = ['pills', 'rope', 'gun', 'bridge', 'overdose']
        if any(keyword in message for keyword in means_keywords):
            risk_multiplier += 0.3
        
        # Check emotional context
        emotions = context.get('emotions', [])
        high_risk_emotions = ['despair', 'hopelessness', 'rage', 'worthlessness']
        if any(emotion in emotions for emotion in high_risk_emotions):
            risk_multiplier += 0.2
        
        # Check for isolation factors
        if 'isolation' in safety_alert.risk_factors:
            risk_multiplier += 0.1
        
        # Adjust crisis level based on risk multiplier
        if risk_multiplier >= 1.5 and base_level != CrisisLevel.CRITICAL:
            if base_level == CrisisLevel.HIGH:
                return CrisisLevel.CRITICAL
            elif base_level == CrisisLevel.MODERATE:
                return CrisisLevel.HIGH
            elif base_level == CrisisLevel.LOW:
                return CrisisLevel.MODERATE
        
        return base_level
    
    def generate_crisis_response(self, safety_alert: SafetyAlert, 
                               context: Dict[str, Any]) -> CrisisResponse:
        """
        Generate comprehensive crisis response
        
        Args:
            safety_alert: Safety alert triggering crisis response
            context: Additional context about the situation
            
        Returns:
            CrisisResponse with detailed intervention plan
        """
        
        self.response_stats['total_crisis_responses'] += 1
        self.response_stats['last_crisis_response'] = datetime.now()
        
        # Assess crisis level
        crisis_level = self.assess_crisis_level(safety_alert, context)
        
        # Determine response protocol
        if crisis_level == CrisisLevel.CRITICAL:
            protocol = ResponseProtocol.EMERGENCY_PROTOCOL
            self.response_stats['emergency_protocols_activated'] += 1
        elif crisis_level == CrisisLevel.HIGH:
            protocol = ResponseProtocol.CRISIS_INTERVENTION
        elif crisis_level == CrisisLevel.MODERATE:
            protocol = ResponseProtocol.ENHANCED_SUPPORT
        else:
            protocol = ResponseProtocol.STANDARD_SUPPORT
        
        # Get protocol details
        protocol_data = self.response_protocols[protocol]
        
        # Generate immediate response
        immediate_response = self._generate_immediate_response(
            crisis_level, protocol, safety_alert, context
        )
        
        # Generate follow-up actions
        follow_up_actions = self._generate_follow_up_actions(
            crisis_level, protocol, safety_alert.risk_factors
        )
        
        # Select appropriate resources
        resources = self._select_crisis_resources(crisis_level, safety_alert.risk_factors)
        
        # Generate safety plan elements
        safety_plan_elements = self._generate_safety_plan(crisis_level, context)
        
        # Define escalation triggers
        escalation_triggers = self._define_escalation_triggers(crisis_level)
        
        # Create crisis response
        response = CrisisResponse(
            response_id=f"crisis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(),
            crisis_level=crisis_level,
            protocol=protocol,
            immediate_response=immediate_response,
            follow_up_actions=follow_up_actions,
            resources=resources,
            safety_plan_elements=safety_plan_elements,
            escalation_triggers=escalation_triggers,
            monitoring_required=crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]
        )
        
        # Track active crisis if high-level
        if crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            self.active_crises[response.response_id] = {
                'response': response,
                'start_time': datetime.now(),
                'last_check': datetime.now(),
                'status': 'active'
            }
        
        logger.info(f"Generated crisis response: {crisis_level.value} level, {protocol.value} protocol")
        
        return response
    
    def _generate_immediate_response(self, crisis_level: CrisisLevel, 
                                   protocol: ResponseProtocol,
                                   safety_alert: SafetyAlert,
                                   context: Dict[str, Any]) -> str:
        """Generate immediate crisis response message"""
        
        protocol_data = self.response_protocols[protocol]
        base_response = protocol_data['response_template']
        
        # Add crisis-specific elements
        response_parts = [base_response]
        
        if crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            # Add immediate safety emphasis
            response_parts.append("Your safety is the most important thing right now.")
            
            # Add crisis resources
            response_parts.append("Please reach out for immediate help:")
            response_parts.append("• National Suicide Prevention Lifeline: 988")
            response_parts.append("• Crisis Text Line: Text HOME to 741741")
            response_parts.append("• Emergency Services: 911")
        
        elif crisis_level == CrisisLevel.MODERATE:
            # Add supportive resources
            response_parts.append("There are people and resources available to help:")
            response_parts.append("• Crisis support: 988")
            response_parts.append("• Mental health support: 1-800-662-4357")
        
        # Add personalized elements based on context
        mood = context.get('mood')
        if mood == 'blue' and 'hopelessness' in safety_alert.risk_factors:
            response_parts.append("These feelings of hopelessness can change. You deserve support and care.")
        
        if 'isolation' in safety_alert.risk_factors:
            response_parts.append("You don't have to face this alone. Reaching out shows incredible strength.")
        
        return "\n\n".join(response_parts)
    
    def _generate_follow_up_actions(self, crisis_level: CrisisLevel, 
                                  protocol: ResponseProtocol,
                                  risk_factors: List[str]) -> List[str]:
        """Generate follow-up actions based on crisis assessment"""
        
        protocol_data = self.response_protocols[protocol]
        actions = protocol_data['immediate_actions'].copy()
        
        # Add specific actions based on risk factors
        if 'suicide_ideation' in risk_factors:
            actions.extend([
                "Remove access to means of self-harm",
                "Stay with trusted person or in safe public place",
                "Create detailed safety plan with specific steps"
            ])
        
        if 'self_harm' in risk_factors:
            actions.extend([
                "Secure or remove self-harm tools",
                "Use alternative coping strategies",
                "Consider medical attention if injuries present"
            ])
        
        if 'isolation' in risk_factors:
            actions.extend([
                "Reach out to at least one trusted person",
                "Consider joining support group or online community",
                "Schedule regular check-ins with support network"
            ])
        
        if 'substance_abuse' in risk_factors:
            actions.extend([
                "Consider substance abuse treatment resources",
                "Remove access to substances if possible",
                "Contact SAMHSA helpline for treatment referrals"
            ])
        
        return actions
    
    def _select_crisis_resources(self, crisis_level: CrisisLevel, 
                               risk_factors: List[str]) -> List[Dict[str, str]]:
        """Select appropriate crisis resources based on assessment"""
        
        resources = []
        
        # Always include immediate help for moderate+ crises
        if crisis_level in [CrisisLevel.MODERATE, CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            resources.extend(self.crisis_resources['immediate_help'])
        
        # Add mental health support
        resources.extend(self.crisis_resources['mental_health_support'][:2])
        
        # Add specialized resources based on risk factors
        if any(factor in risk_factors for factor in ['domestic_violence', 'abuse']):
            resources.append(self.crisis_resources['specialized_support'][0])  # Domestic violence
        
        if any(factor in risk_factors for factor in ['sexual_assault', 'trauma']):
            resources.append(self.crisis_resources['specialized_support'][1])  # RAINN
        
        # Add online resources for additional support
        if crisis_level in [CrisisLevel.LOW, CrisisLevel.MODERATE]:
            resources.extend(self.crisis_resources['online_resources'][:2])
        
        self.response_stats['resource_referrals'] += len(resources)
        
        return resources
    
    def _generate_safety_plan(self, crisis_level: CrisisLevel, 
                            context: Dict[str, Any]) -> List[str]:
        """Generate personalized safety plan elements"""
        
        safety_plan = []
        
        if crisis_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]:
            # Immediate safety is priority
            safety_plan.extend(self.safety_plan_templates['immediate_safety'])
        
        # Always include coping strategies
        safety_plan.extend(self.safety_plan_templates['coping_strategies'][:3])
        
        # Add support network elements
        safety_plan.extend(self.safety_plan_templates['support_network'][:3])
        
        # Add warning signs awareness
        if crisis_level != CrisisLevel.CRITICAL:  # Not immediate emergency
            safety_plan.extend(self.safety_plan_templates['warning_signs'][:2])
        
        # Add professional help recommendations
        safety_plan.extend(self.safety_plan_templates['professional_help'][:2])
        
        self.response_stats['safety_plans_created'] += 1
        
        return safety_plan
    
    def _define_escalation_triggers(self, crisis_level: CrisisLevel) -> List[str]:
        """Define triggers that would require escalation"""
        
        base_triggers = [
            "Explicit suicide plan with means and timeline",
            "Immediate access to lethal means",
            "Complete loss of hope or reasons to live",
            "Severe agitation or impulsivity",
            "Psychotic symptoms or severe disorganization"
        ]
        
        if crisis_level == CrisisLevel.CRITICAL:
            return base_triggers + [
                "Any indication of imminent self-harm",
                "Inability to contract for safety",
                "Lack of protective factors or support"
            ]
        
        elif crisis_level == CrisisLevel.HIGH:
            return base_triggers + [
                "Increasing frequency of suicidal thoughts",
                "Deteriorating mental state",
                "Substance use during crisis"
            ]
        
        else:
            return [
                "Development of specific suicide plan",
                "Significant increase in hopelessness",
                "Major life stressor or loss"
            ]
    
    def check_active_crises(self) -> List[Dict[str, Any]]:
        """Check status of active crises and identify those needing attention"""
        
        current_time = datetime.now()
        crises_needing_attention = []
        
        for crisis_id, crisis_data in self.active_crises.items():
            response = crisis_data['response']
            time_since_start = current_time - crisis_data['start_time']
            time_since_check = current_time - crisis_data['last_check']
            
            # Check if crisis needs attention based on time and level
            needs_attention = False
            
            if response.crisis_level == CrisisLevel.CRITICAL:
                # Critical crises need attention every 15 minutes
                if time_since_check > timedelta(minutes=15):
                    needs_attention = True
            
            elif response.crisis_level == CrisisLevel.HIGH:
                # High crises need attention every hour
                if time_since_check > timedelta(hours=1):
                    needs_attention = True
            
            # Auto-resolve crises after 24 hours without escalation
            if time_since_start > timedelta(hours=24):
                crisis_data['status'] = 'resolved'
                needs_attention = False
            
            if needs_attention:
                crises_needing_attention.append({
                    'crisis_id': crisis_id,
                    'crisis_level': response.crisis_level.value,
                    'time_since_start': str(time_since_start),
                    'time_since_check': str(time_since_check),
                    'escalation_triggers': response.escalation_triggers
                })
        
        # Clean up resolved crises
        self.active_crises = {k: v for k, v in self.active_crises.items() 
                             if v['status'] == 'active'}
        
        return crises_needing_attention
    
    def update_crisis_status(self, crisis_id: str, status: str, notes: str = ""):
        """Update status of active crisis"""
        if crisis_id in self.active_crises:
            self.active_crises[crisis_id]['status'] = status
            self.active_crises[crisis_id]['last_check'] = datetime.now()
            if notes:
                self.active_crises[crisis_id]['notes'] = notes
            
            logger.info(f"Updated crisis {crisis_id} status to {status}")
    
    def get_crisis_statistics(self) -> Dict[str, Any]:
        """Get crisis response statistics"""
        return {
            'response_stats': self.response_stats,
            'active_crises': len(self.active_crises),
            'crisis_levels_active': {
                level.value: sum(1 for crisis in self.active_crises.values() 
                               if crisis['response'].crisis_level == level)
                for level in CrisisLevel
            },
            'protocols_used': {
                protocol.value: sum(1 for crisis in self.active_crises.values() 
                                  if crisis['response'].protocol == protocol)
                for protocol in ResponseProtocol
            }
        }

