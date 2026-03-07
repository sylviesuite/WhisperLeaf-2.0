"""
WhisperLeaf Emotional Constitution
Framework for defining and managing emotional AI behavior rules
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class RulePriority(Enum):
    """Priority levels for constitutional rules"""
    CRITICAL = "critical"      # Never violate (safety, crisis)
    HIGH = "high"             # Strong preference (emotional support)
    MEDIUM = "medium"         # General guidance (tone, style)
    LOW = "low"              # Suggestions (preferences)

class RuleScope(Enum):
    """Scope of rule application"""
    GLOBAL = "global"         # Always applies
    CONTEXTUAL = "contextual" # Applies in specific contexts
    MOOD_BASED = "mood_based" # Applies for specific moods
    CRISIS = "crisis"         # Applies during crisis situations
    TEMPORAL = "temporal"     # Applies during specific times

class RuleType(Enum):
    """Types of constitutional rules"""
    SAFETY = "safety"                    # Safety and crisis prevention
    EMOTIONAL_SUPPORT = "emotional_support"  # Emotional support guidelines
    COMMUNICATION = "communication"      # Communication style and tone
    PRIVACY = "privacy"                 # Privacy and data protection
    BOUNDARIES = "boundaries"           # Personal boundaries and limits
    THERAPEUTIC = "therapeutic"         # Therapeutic approach guidelines

class ConstitutionalRule:
    """Individual constitutional rule for AI behavior"""
    
    def __init__(self, 
                 rule_id: str,
                 name: str,
                 description: str,
                 rule_type: RuleType,
                 priority: RulePriority,
                 scope: RuleScope,
                 conditions: Dict[str, Any],
                 actions: Dict[str, Any],
                 enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.rule_type = rule_type
        self.priority = priority
        self.scope = scope
        self.conditions = conditions
        self.actions = actions
        self.enabled = enabled
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.usage_count = 0
        self.last_triggered = None
    
    def matches_context(self, context: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Check if rule applies to given context
        
        Args:
            context: Current interaction context
            
        Returns:
            Tuple of (matches, confidence_score)
        """
        if not self.enabled:
            return False, 0.0
        
        # Check scope applicability
        if self.scope == RuleScope.GLOBAL:
            scope_match = True
        elif self.scope == RuleScope.CRISIS:
            scope_match = context.get('crisis_level', 'none') != 'none'
        elif self.scope == RuleScope.MOOD_BASED:
            scope_match = context.get('mood') in self.conditions.get('applicable_moods', [])
        elif self.scope == RuleScope.CONTEXTUAL:
            scope_match = any(
                context.get(key) == value 
                for key, value in self.conditions.get('context_requirements', {}).items()
            )
        elif self.scope == RuleScope.TEMPORAL:
            # Check time-based conditions
            current_hour = datetime.now().hour
            time_range = self.conditions.get('time_range', [0, 23])
            scope_match = time_range[0] <= current_hour <= time_range[1]
        else:
            scope_match = True
        
        if not scope_match:
            return False, 0.0
        
        # Calculate confidence based on condition matching
        confidence = 1.0
        
        # Check specific conditions
        for condition_key, condition_value in self.conditions.items():
            if condition_key == 'keywords':
                # Check for keyword presence
                text = context.get('message', '').lower()
                keyword_matches = sum(1 for keyword in condition_value if keyword.lower() in text)
                if keyword_matches == 0:
                    confidence *= 0.5
                else:
                    confidence *= min(1.0, keyword_matches / len(condition_value))
            
            elif condition_key == 'emotional_state':
                # Check emotional state matching
                current_emotions = context.get('emotions', [])
                required_emotions = condition_value
                emotion_match = any(emotion in current_emotions for emotion in required_emotions)
                if not emotion_match:
                    confidence *= 0.7
            
            elif condition_key == 'crisis_indicators':
                # Check for crisis indicators
                message = context.get('message', '').lower()
                crisis_words = condition_value
                crisis_match = any(word.lower() in message for word in crisis_words)
                if crisis_match:
                    confidence = 1.0  # Crisis rules get full confidence
                elif self.rule_type == RuleType.SAFETY:
                    confidence *= 0.3  # Safety rules need crisis indicators
        
        return confidence > 0.3, confidence
    
    def get_action_guidance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get action guidance based on rule and context"""
        
        guidance = {
            'rule_id': self.rule_id,
            'rule_name': self.name,
            'priority': self.priority.value,
            'rule_type': self.rule_type.value,
            'actions': self.actions.copy()
        }
        
        # Add context-specific modifications
        if self.rule_type == RuleType.COMMUNICATION:
            mood = context.get('mood', 'neutral')
            if mood in self.actions.get('mood_specific_tone', {}):
                guidance['actions']['tone'] = self.actions['mood_specific_tone'][mood]
        
        elif self.rule_type == RuleType.SAFETY:
            crisis_level = context.get('crisis_level', 'none')
            if crisis_level != 'none':
                guidance['actions']['response_type'] = 'crisis_support'
                guidance['actions']['escalation_needed'] = crisis_level in ['high', 'critical']
        
        # Update usage statistics
        self.usage_count += 1
        self.last_triggered = datetime.now()
        
        return guidance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type.value,
            'priority': self.priority.value,
            'scope': self.scope.value,
            'conditions': self.conditions,
            'actions': self.actions,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'usage_count': self.usage_count,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConstitutionalRule':
        """Create rule from dictionary"""
        rule = cls(
            rule_id=data['rule_id'],
            name=data['name'],
            description=data['description'],
            rule_type=RuleType(data['rule_type']),
            priority=RulePriority(data['priority']),
            scope=RuleScope(data['scope']),
            conditions=data['conditions'],
            actions=data['actions'],
            enabled=data.get('enabled', True)
        )
        
        rule.created_at = datetime.fromisoformat(data['created_at'])
        rule.last_modified = datetime.fromisoformat(data['last_modified'])
        rule.usage_count = data.get('usage_count', 0)
        if data.get('last_triggered'):
            rule.last_triggered = datetime.fromisoformat(data['last_triggered'])
        
        return rule

class EmotionalConstitution:
    """
    Main constitutional framework for emotional AI governance
    Manages rules, evaluates contexts, and provides guidance
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/emotional_constitution.json")
        self.rules: Dict[str, ConstitutionalRule] = {}
        self.rule_stats = {
            'total_evaluations': 0,
            'rules_triggered': 0,
            'crisis_interventions': 0,
            'safety_blocks': 0,
            'last_evaluation': None
        }
        
        # Load or create default constitution
        self._load_constitution()
        if not self.rules:
            self._create_default_constitution()
        
        logger.info(f"EmotionalConstitution initialized with {len(self.rules)} rules")
    
    def _load_constitution(self):
        """Load constitution from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                
                # Load rules
                for rule_data in data.get('rules', []):
                    rule = ConstitutionalRule.from_dict(rule_data)
                    self.rules[rule.rule_id] = rule
                
                # Load statistics
                self.rule_stats.update(data.get('statistics', {}))
                
                logger.info(f"Loaded {len(self.rules)} constitutional rules")
        
        except Exception as e:
            logger.error(f"Failed to load constitution: {e}")
    
    def _save_constitution(self):
        """Save constitution to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'rules': [rule.to_dict() for rule in self.rules.values()],
                'statistics': self.rule_stats,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Constitution saved successfully")
        
        except Exception as e:
            logger.error(f"Failed to save constitution: {e}")
    
    def _create_default_constitution(self):
        """Create default constitutional rules for emotional AI"""
        
        default_rules = [
            # Critical Safety Rules
            ConstitutionalRule(
                rule_id="safety_001",
                name="Crisis Detection and Response",
                description="Detect crisis situations and provide appropriate support",
                rule_type=RuleType.SAFETY,
                priority=RulePriority.CRITICAL,
                scope=RuleScope.GLOBAL,
                conditions={
                    'crisis_indicators': [
                        'suicide', 'kill myself', 'end it all', 'not worth living',
                        'hurt myself', 'self harm', 'cutting', 'overdose',
                        'hopeless', 'can\'t go on', 'want to die'
                    ]
                },
                actions={
                    'response_type': 'crisis_support',
                    'tone': 'calm_supportive',
                    'provide_resources': True,
                    'escalation_needed': True,
                    'immediate_response': 'I\'m really concerned about you. You\'re not alone, and there are people who want to help.'
                }
            ),
            
            ConstitutionalRule(
                rule_id="safety_002", 
                name="Harmful Content Prevention",
                description="Prevent generation of harmful or dangerous content",
                rule_type=RuleType.SAFETY,
                priority=RulePriority.CRITICAL,
                scope=RuleScope.GLOBAL,
                conditions={
                    'keywords': ['violence', 'harm', 'dangerous', 'illegal']
                },
                actions={
                    'block_harmful_content': True,
                    'redirect_to_support': True,
                    'tone': 'gentle_redirect'
                }
            ),
            
            # Emotional Support Rules
            ConstitutionalRule(
                rule_id="support_001",
                name="Empathetic Response for Sadness",
                description="Provide warm, empathetic support for sadness and grief",
                rule_type=RuleType.EMOTIONAL_SUPPORT,
                priority=RulePriority.HIGH,
                scope=RuleScope.MOOD_BASED,
                conditions={
                    'applicable_moods': ['blue'],
                    'emotional_state': ['sadness', 'grief', 'loss', 'loneliness']
                },
                actions={
                    'tone': 'warm_empathetic',
                    'validation': True,
                    'gentle_encouragement': True,
                    'avoid_toxic_positivity': True,
                    'response_style': 'I hear how difficult this is for you. Your feelings are completely valid.'
                }
            ),
            
            ConstitutionalRule(
                rule_id="support_002",
                name="Calming Response for Anxiety",
                description="Provide grounding and calming support for anxiety",
                rule_type=RuleType.EMOTIONAL_SUPPORT,
                priority=RulePriority.HIGH,
                scope=RuleScope.MOOD_BASED,
                conditions={
                    'applicable_moods': ['yellow'],
                    'emotional_state': ['anxiety', 'worry', 'panic', 'stress']
                },
                actions={
                    'tone': 'calm_grounding',
                    'breathing_techniques': True,
                    'grounding_exercises': True,
                    'reassurance': True,
                    'response_style': 'Let\'s take this one step at a time. You\'re safe right now.'
                }
            ),
            
            # Communication Rules
            ConstitutionalRule(
                rule_id="comm_001",
                name="Adaptive Communication Style",
                description="Adapt communication style based on user's emotional state",
                rule_type=RuleType.COMMUNICATION,
                priority=RulePriority.MEDIUM,
                scope=RuleScope.GLOBAL,
                conditions={},
                actions={
                    'mood_specific_tone': {
                        'blue': 'gentle_supportive',
                        'green': 'warm_encouraging', 
                        'yellow': 'calm_reassuring',
                        'purple': 'curious_engaging',
                        'red': 'patient_understanding'
                    },
                    'avoid_dismissive_language': True,
                    'use_person_first_language': True
                }
            ),
            
            # Privacy Rules
            ConstitutionalRule(
                rule_id="privacy_001",
                name="Data Privacy Protection",
                description="Protect user privacy and confidentiality",
                rule_type=RuleType.PRIVACY,
                priority=RulePriority.HIGH,
                scope=RuleScope.GLOBAL,
                conditions={},
                actions={
                    'never_share_personal_info': True,
                    'local_processing_only': True,
                    'user_controls_data': True,
                    'transparent_about_limitations': True
                }
            ),
            
            # Boundary Rules
            ConstitutionalRule(
                rule_id="boundary_001",
                name="Therapeutic Boundaries",
                description="Maintain appropriate therapeutic boundaries",
                rule_type=RuleType.BOUNDARIES,
                priority=RulePriority.HIGH,
                scope=RuleScope.GLOBAL,
                conditions={},
                actions={
                    'not_a_replacement_for_therapy': True,
                    'encourage_professional_help': True,
                    'acknowledge_limitations': True,
                    'supportive_not_diagnostic': True
                }
            )
        ]
        
        # Add all default rules
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
        
        # Save the default constitution
        self._save_constitution()
        
        logger.info(f"Created default constitution with {len(default_rules)} rules")
    
    def evaluate_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate context against constitutional rules
        
        Args:
            context: Current interaction context including message, mood, emotions, etc.
            
        Returns:
            Dictionary with applicable rules, guidance, and safety flags
        """
        
        self.rule_stats['total_evaluations'] += 1
        self.rule_stats['last_evaluation'] = datetime.now()
        
        applicable_rules = []
        safety_flags = []
        guidance = {
            'tone': 'supportive',
            'response_type': 'normal',
            'safety_level': 'safe',
            'escalation_needed': False,
            'crisis_detected': False
        }
        
        # Evaluate each rule
        for rule in self.rules.values():
            matches, confidence = rule.matches_context(context)
            
            if matches:
                rule_guidance = rule.get_action_guidance(context)
                applicable_rules.append({
                    'rule': rule_guidance,
                    'confidence': confidence
                })
                
                # Apply rule guidance based on priority
                if rule.priority == RulePriority.CRITICAL:
                    if rule.rule_type == RuleType.SAFETY:
                        guidance['safety_level'] = 'critical'
                        guidance['crisis_detected'] = True
                        guidance['escalation_needed'] = True
                        self.rule_stats['crisis_interventions'] += 1
                        
                        if 'immediate_response' in rule.actions:
                            guidance['immediate_response'] = rule.actions['immediate_response']
                        
                        safety_flags.append({
                            'rule_id': rule.rule_id,
                            'rule_name': rule.name,
                            'severity': 'critical',
                            'action_required': True
                        })
                
                elif rule.priority == RulePriority.HIGH:
                    # High priority rules influence tone and approach
                    if 'tone' in rule.actions:
                        guidance['tone'] = rule.actions['tone']
                    if 'response_type' in rule.actions:
                        guidance['response_type'] = rule.actions['response_type']
        
        # Sort applicable rules by priority and confidence
        applicable_rules.sort(key=lambda x: (
            RulePriority(x['rule']['priority']).value,
            -x['confidence']
        ))
        
        if applicable_rules:
            self.rule_stats['rules_triggered'] += 1
        
        # Save updated statistics
        self._save_constitution()
        
        result = {
            'applicable_rules': applicable_rules,
            'guidance': guidance,
            'safety_flags': safety_flags,
            'evaluation_timestamp': datetime.now().isoformat(),
            'context_summary': {
                'mood': context.get('mood'),
                'emotions': context.get('emotions', []),
                'crisis_level': context.get('crisis_level', 'none'),
                'message_length': len(context.get('message', ''))
            }
        }
        
        logger.debug(f"Constitutional evaluation: {len(applicable_rules)} rules applied, safety level: {guidance['safety_level']}")
        
        return result
    
    def add_rule(self, rule: ConstitutionalRule) -> bool:
        """Add a new constitutional rule"""
        try:
            self.rules[rule.rule_id] = rule
            self._save_constitution()
            logger.info(f"Added constitutional rule: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add rule {rule.rule_id}: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing constitutional rule"""
        try:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            
            # Update allowed fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.last_modified = datetime.now()
            self._save_constitution()
            
            logger.info(f"Updated constitutional rule: {rule_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update rule {rule_id}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a constitutional rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                self._save_constitution()
                logger.info(f"Removed constitutional rule: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rule {rule_id}: {e}")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[ConstitutionalRule]:
        """Get a specific constitutional rule"""
        return self.rules.get(rule_id)
    
    def list_rules(self, rule_type: Optional[RuleType] = None, 
                   priority: Optional[RulePriority] = None) -> List[ConstitutionalRule]:
        """List constitutional rules with optional filtering"""
        rules = list(self.rules.values())
        
        if rule_type:
            rules = [r for r in rules if r.rule_type == rule_type]
        
        if priority:
            rules = [r for r in rules if r.priority == priority]
        
        return sorted(rules, key=lambda r: (r.priority.value, r.name))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get constitutional rule usage statistics"""
        rule_usage = {}
        for rule_id, rule in self.rules.items():
            rule_usage[rule_id] = {
                'name': rule.name,
                'usage_count': rule.usage_count,
                'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None,
                'enabled': rule.enabled
            }
        
        return {
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules.values() if r.enabled),
            'rule_types': {rt.value: sum(1 for r in self.rules.values() if r.rule_type == rt) 
                          for rt in RuleType},
            'priority_distribution': {rp.value: sum(1 for r in self.rules.values() if r.priority == rp) 
                                    for rp in RulePriority},
            'usage_statistics': self.rule_stats,
            'rule_usage': rule_usage
        }

