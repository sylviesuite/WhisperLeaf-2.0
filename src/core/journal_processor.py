"""
WhisperLeaf Journal Processor
Intelligent processing and analysis of journal entries
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

from .memory_models import JournalEntry, MemoryMetadata, EmotionalContext, PrivacyLevel
from emotional_engine.emotional_processor import EmotionalProcessor

logger = logging.getLogger(__name__)

class JournalProcessor:
    """
    Intelligent journal processing system that:
    - Analyzes emotional content in journal entries
    - Extracts insights, themes, and patterns
    - Generates reflective prompts
    - Categorizes and tags entries
    - Tracks emotional growth over time
    """
    
    def __init__(self, emotional_processor: Optional[EmotionalProcessor] = None):
        self.emotional_processor = emotional_processor or EmotionalProcessor()
        
        # Initialize processing patterns
        self.insight_patterns = self._initialize_insight_patterns()
        self.theme_patterns = self._initialize_theme_patterns()
        self.growth_indicators = self._initialize_growth_indicators()
        self.reflection_prompts = self._initialize_reflection_prompts()
        
        logger.info("JournalProcessor initialized")
    
    def _initialize_insight_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for extracting insights from journal text"""
        return {
            'realization': [
                r'i\s+(?:realized|understand|learned|discovered|figured\s+out)',
                r'it\s+(?:dawned\s+on\s+me|became\s+clear|clicked)',
                r'(?:suddenly|finally)\s+(?:understood|realized|saw)',
                r'(?:aha|eureka)\s+moment'
            ],
            'growth': [
                r'i\s+(?:grew|developed|improved|progressed|evolved)',
                r'i\s+(?:became|got)\s+(?:better|stronger|wiser|more)',
                r'(?:progress|improvement|development|growth)',
                r'i\s+(?:overcame|conquered|defeated|mastered)'
            ],
            'lesson': [
                r'(?:lesson|teaching|wisdom|knowledge)\s+(?:learned|gained)',
                r'(?:taught\s+me|showed\s+me|revealed)',
                r'(?:important|valuable)\s+(?:lesson|insight|learning)',
                r'(?:takeaway|key\s+point|main\s+thing)'
            ],
            'pattern': [
                r'(?:pattern|trend|cycle|habit|routine)',
                r'(?:always|usually|often|frequently)\s+(?:do|feel|think)',
                r'(?:notice|see|observe)\s+(?:that|how)',
                r'(?:tendency|inclination|propensity)'
            ]
        }
    
    def _initialize_theme_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for identifying themes in journal entries"""
        return {
            'relationships': [
                r'(?:friend|family|partner|spouse|colleague|relationship)',
                r'(?:love|friendship|connection|bond|intimacy)',
                r'(?:conflict|argument|disagreement|tension)',
                r'(?:support|understanding|empathy|compassion)'
            ],
            'work_career': [
                r'(?:work|job|career|profession|office)',
                r'(?:boss|manager|colleague|coworker|client)',
                r'(?:project|deadline|meeting|presentation)',
                r'(?:promotion|raise|performance|achievement)'
            ],
            'health_wellness': [
                r'(?:health|wellness|fitness|exercise|diet)',
                r'(?:doctor|medical|therapy|treatment|medication)',
                r'(?:sleep|rest|energy|fatigue|tired)',
                r'(?:mental\s+health|wellbeing|self\s+care)'
            ],
            'personal_growth': [
                r'(?:growth|development|improvement|progress)',
                r'(?:goal|aspiration|dream|ambition|vision)',
                r'(?:learning|education|skill|knowledge)',
                r'(?:confidence|self\s+esteem|self\s+worth)'
            ],
            'creativity': [
                r'(?:creative|creativity|art|artistic|imagination)',
                r'(?:writing|painting|music|design|craft)',
                r'(?:inspiration|inspired|motivated|passionate)',
                r'(?:project|creation|expression|innovation)'
            ],
            'spirituality': [
                r'(?:spiritual|spirituality|faith|belief|religion)',
                r'(?:meditation|prayer|mindfulness|contemplation)',
                r'(?:meaning|purpose|soul|divine|sacred)',
                r'(?:gratitude|blessing|thankful|appreciation)'
            ],
            'challenges': [
                r'(?:challenge|difficulty|problem|struggle|obstacle)',
                r'(?:stress|pressure|overwhelm|burden|hardship)',
                r'(?:fear|anxiety|worry|concern|doubt)',
                r'(?:failure|mistake|setback|disappointment)'
            ],
            'achievements': [
                r'(?:achievement|accomplishment|success|victory|win)',
                r'(?:proud|pride|satisfaction|fulfillment|joy)',
                r'(?:goal\s+reached|milestone|breakthrough|triumph)',
                r'(?:celebration|reward|recognition|praise)'
            ]
        }
    
    def _initialize_growth_indicators(self) -> List[str]:
        """Initialize indicators of emotional and personal growth"""
        return [
            'increased self-awareness',
            'better emotional regulation',
            'improved communication skills',
            'stronger boundaries',
            'greater resilience',
            'enhanced empathy',
            'deeper self-compassion',
            'clearer values and priorities',
            'better stress management',
            'improved relationships',
            'increased confidence',
            'greater life satisfaction',
            'enhanced problem-solving skills',
            'stronger sense of purpose',
            'better work-life balance'
        ]
    
    def _initialize_reflection_prompts(self) -> Dict[str, List[str]]:
        """Initialize reflective prompts based on emotional states and themes"""
        return {
            'blue_mood': [
                "What would you tell a friend who was feeling the same way?",
                "What small step could you take today to care for yourself?",
                "What are three things you're grateful for, even in this difficult time?",
                "How have you overcome similar feelings in the past?",
                "What support do you need right now, and how can you ask for it?"
            ],
            'yellow_mood': [
                "What specific thoughts are contributing to your anxiety?",
                "What aspects of this situation are within your control?",
                "What would help you feel more grounded right now?",
                "How can you break this worry down into smaller, manageable pieces?",
                "What evidence do you have that contradicts your anxious thoughts?"
            ],
            'red_mood': [
                "What values or boundaries feel like they're being violated?",
                "How can you express this anger in a healthy, constructive way?",
                "What would resolution look like in this situation?",
                "What can you learn about yourself from this anger?",
                "How can you channel this energy into positive action?"
            ],
            'green_mood': [
                "What contributed to this sense of peace and balance?",
                "How can you maintain this positive state?",
                "What insights are emerging for you in this calm space?",
                "What are you most grateful for right now?",
                "How can you share this positive energy with others?"
            ],
            'purple_mood': [
                "What new ideas or possibilities are exciting you?",
                "How can you nurture and develop this creative energy?",
                "What would you create if there were no limitations?",
                "How does this inspiration connect to your deeper purpose?",
                "What first step can you take to bring this vision to life?"
            ],
            'relationships': [
                "How did this interaction reflect your values and boundaries?",
                "What patterns do you notice in your relationships?",
                "How can you communicate your needs more effectively?",
                "What are you learning about love and connection?",
                "How can you show up more authentically in your relationships?"
            ],
            'work_career': [
                "How does this work align with your values and goals?",
                "What skills are you developing through these challenges?",
                "How can you find more meaning and purpose in your work?",
                "What boundaries do you need to set for better work-life balance?",
                "What would your ideal work situation look like?"
            ],
            'personal_growth': [
                "What patterns are you noticing about yourself?",
                "How have you grown or changed recently?",
                "What beliefs about yourself are you ready to release?",
                "What new aspects of yourself are you discovering?",
                "How can you be more compassionate with yourself?"
            ]
        }
    
    def process_journal_entry(self, content: str, title: str = "", 
                            prompt: Optional[str] = None,
                            privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE) -> JournalEntry:
        """
        Process a journal entry with full emotional and thematic analysis
        
        Args:
            content: Journal entry text
            title: Optional title for the entry
            prompt: Optional prompt that inspired the entry
            privacy_level: Privacy level for the entry
            
        Returns:
            Processed JournalEntry with analysis and insights
        """
        
        # Perform emotional analysis
        emotional_response = self.emotional_processor.process_emotional_input(content)
        
        # Extract insights and themes
        insights = self._extract_insights(content)
        themes = self._identify_themes(content)
        
        # Generate metadata
        metadata = self._generate_metadata(content, themes, insights)
        
        # Create emotional context
        emotional_context = EmotionalContext(
            primary_mood=emotional_response.emotion_analysis.mood_analysis.primary_mood.value,
            secondary_mood=emotional_response.emotion_analysis.mood_analysis.secondary_mood.value if emotional_response.emotion_analysis.mood_analysis.secondary_mood else None,
            emotions=[e.emotion for e in emotional_response.emotion_analysis.primary_emotions[:5]],
            intensity=self._map_intensity(emotional_response.emotion_analysis.intensity_score),
            complexity_score=emotional_response.emotion_analysis.complexity_score,
            crisis_level=emotional_response.crisis_assessment.overall_level.value,
            support_needs=emotional_response.emotion_analysis.support_needs
        )
        
        # Generate reflection questions
        reflection_questions = self._generate_reflection_questions(
            emotional_response.emotion_analysis.mood_analysis.primary_mood.value,
            themes
        )
        
        # Identify growth indicators
        growth_indicators = self._identify_growth_indicators(content, insights)
        
        # Create journal entry
        journal_entry = JournalEntry(
            title=title or self._generate_title(content, themes),
            content=content,
            emotional_context=emotional_context,
            metadata=metadata,
            privacy_level=privacy_level,
            prompt=prompt,
            reflection_questions=reflection_questions,
            insights=insights,
            goals=self._extract_goals(content),
            gratitude=self._extract_gratitude(content),
            challenges=self._extract_challenges(content)
        )
        
        logger.info(f"Processed journal entry: {len(content)} chars, {len(insights)} insights, {len(themes)} themes")
        return journal_entry
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract insights and realizations from journal content"""
        insights = []
        content_lower = content.lower()
        
        for insight_type, patterns in self.insight_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    # Extract the sentence containing the insight
                    start = max(0, content.rfind('.', 0, match.start()) + 1)
                    end = content.find('.', match.end())
                    if end == -1:
                        end = len(content)
                    
                    insight_text = content[start:end].strip()
                    if insight_text and len(insight_text) > 20:  # Filter out very short insights
                        insights.append(insight_text)
        
        # Remove duplicates and limit to most relevant
        unique_insights = list(dict.fromkeys(insights))  # Preserves order
        return unique_insights[:5]  # Limit to top 5 insights
    
    def _identify_themes(self, content: str) -> List[str]:
        """Identify themes present in the journal content"""
        themes = []
        content_lower = content.lower()
        
        for theme, patterns in self.theme_patterns.items():
            theme_score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                theme_score += matches
            
            if theme_score > 0:
                themes.append((theme, theme_score))
        
        # Sort by relevance and return theme names
        themes.sort(key=lambda x: x[1], reverse=True)
        return [theme[0] for theme in themes[:3]]  # Top 3 themes
    
    def _generate_metadata(self, content: str, themes: List[str], insights: List[str]) -> MemoryMetadata:
        """Generate comprehensive metadata for the journal entry"""
        
        # Extract keywords (simple approach - can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Filter short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keyword_list = [word for word, freq in keywords]
        
        # Extract people mentioned (simple pattern matching)
        people_patterns = [
            r'\b(?:my|with|and)\s+([A-Z][a-z]+)\b',  # Names after common words
            r'\b([A-Z][a-z]+)\s+(?:said|told|asked|mentioned)\b'  # Names before speech verbs
        ]
        people = []
        for pattern in people_patterns:
            matches = re.findall(pattern, content)
            people.extend(matches)
        
        # Calculate sentiment score (simple approach)
        positive_words = ['happy', 'joy', 'love', 'excited', 'grateful', 'proud', 'amazing', 'wonderful', 'great', 'good']
        negative_words = ['sad', 'angry', 'frustrated', 'worried', 'anxious', 'terrible', 'awful', 'bad', 'hate', 'upset']
        
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
        
        if positive_count + negative_count > 0:
            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
        else:
            sentiment_score = 0.0
        
        # Calculate importance score based on length, insights, and emotional intensity
        importance_score = min(1.0, (len(content) / 1000) * 0.3 + len(insights) * 0.2 + len(themes) * 0.1)
        
        return MemoryMetadata(
            tags=themes + ['journal_entry'],
            categories=['personal_reflection', 'emotional_processing'],
            people_mentioned=list(set(people))[:5],  # Unique people, max 5
            themes=themes,
            keywords=keyword_list,
            sentiment_score=sentiment_score,
            importance_score=importance_score
        )
    
    def _map_intensity(self, intensity_score: float):
        """Map numerical intensity to enum"""
        from .memory_models import EmotionalIntensity
        
        if intensity_score >= 0.8:
            return EmotionalIntensity.VERY_HIGH
        elif intensity_score >= 0.6:
            return EmotionalIntensity.HIGH
        elif intensity_score >= 0.4:
            return EmotionalIntensity.MODERATE
        elif intensity_score >= 0.2:
            return EmotionalIntensity.LOW
        else:
            return EmotionalIntensity.VERY_LOW
    
    def _generate_reflection_questions(self, mood: str, themes: List[str]) -> List[str]:
        """Generate personalized reflection questions"""
        questions = []
        
        # Add mood-based questions
        mood_key = f"{mood}_mood"
        if mood_key in self.reflection_prompts:
            questions.extend(self.reflection_prompts[mood_key][:2])
        
        # Add theme-based questions
        for theme in themes[:2]:  # Top 2 themes
            if theme in self.reflection_prompts:
                questions.extend(self.reflection_prompts[theme][:1])
        
        # Add general reflection questions if needed
        if len(questions) < 3:
            general_questions = [
                "What emotions came up for you while writing this?",
                "What would you like to remember about this experience?",
                "How does this connect to your broader life story?",
                "What are you learning about yourself through this reflection?"
            ]
            questions.extend(general_questions[:3-len(questions)])
        
        return questions[:3]  # Limit to 3 questions
    
    def _identify_growth_indicators(self, content: str, insights: List[str]) -> List[str]:
        """Identify signs of personal growth in the journal entry"""
        growth_found = []
        content_lower = content.lower()
        
        for indicator in self.growth_indicators:
            # Check if growth indicator concepts are present
            indicator_words = indicator.lower().split()
            if any(word in content_lower for word in indicator_words):
                growth_found.append(indicator)
        
        # Also check insights for growth language
        insight_text = ' '.join(insights).lower()
        growth_keywords = ['learned', 'grew', 'developed', 'improved', 'realized', 'understood', 'overcame']
        
        if any(keyword in insight_text for keyword in growth_keywords):
            growth_found.append('increased self-awareness')
        
        return list(set(growth_found))[:3]  # Unique growth indicators, max 3
    
    def _extract_goals(self, content: str) -> List[str]:
        """Extract goals and intentions from journal content"""
        goal_patterns = [
            r'(?:i\s+want\s+to|i\s+will|i\s+plan\s+to|i\s+hope\s+to|i\s+intend\s+to)\s+([^.!?]+)',
            r'(?:my\s+goal|goal\s+is|objective\s+is|aim\s+is)\s+([^.!?]+)',
            r'(?:i\s+need\s+to|i\s+should|i\s+must)\s+([^.!?]+)'
        ]
        
        goals = []
        for pattern in goal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            goals.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        return goals[:3]  # Limit to 3 goals
    
    def _extract_gratitude(self, content: str) -> List[str]:
        """Extract expressions of gratitude from journal content"""
        gratitude_patterns = [
            r'(?:grateful\s+for|thankful\s+for|appreciate)\s+([^.!?]+)',
            r'(?:i\s+am\s+grateful|i\s+am\s+thankful)\s+([^.!?]+)',
            r'(?:blessing|blessed\s+to\s+have)\s+([^.!?]+)'
        ]
        
        gratitude = []
        for pattern in gratitude_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            gratitude.extend([match.strip() for match in matches if len(match.strip()) > 5])
        
        return gratitude[:3]  # Limit to 3 gratitude items
    
    def _extract_challenges(self, content: str) -> List[str]:
        """Extract challenges and difficulties from journal content"""
        challenge_patterns = [
            r'(?:struggling\s+with|difficulty\s+with|challenge\s+is)\s+([^.!?]+)',
            r'(?:hard\s+to|difficult\s+to|challenging\s+to)\s+([^.!?]+)',
            r'(?:problem\s+is|issue\s+is|concern\s+is)\s+([^.!?]+)'
        ]
        
        challenges = []
        for pattern in challenge_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            challenges.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        return challenges[:3]  # Limit to 3 challenges
    
    def _generate_title(self, content: str, themes: List[str]) -> str:
        """Generate an appropriate title for the journal entry"""
        
        # Try to extract a meaningful first sentence
        sentences = re.split(r'[.!?]+', content)
        first_sentence = sentences[0].strip() if sentences else ""
        
        if len(first_sentence) > 10 and len(first_sentence) < 60:
            return first_sentence
        
        # Use themes to generate title
        if themes:
            primary_theme = themes[0].replace('_', ' ').title()
            return f"Reflections on {primary_theme}"
        
        # Default title with date
        return f"Journal Entry - {datetime.now().strftime('%B %d, %Y')}"
    
    def generate_writing_prompt(self, mood: str, recent_themes: List[str] = None) -> str:
        """Generate a personalized writing prompt based on mood and recent themes"""
        
        mood_prompts = {
            'blue': [
                "What would you tell a younger version of yourself who was feeling this way?",
                "Describe a time when you felt this way before and how you moved through it.",
                "What small act of self-compassion could you offer yourself today?",
                "Write about someone who has shown you kindness during difficult times."
            ],
            'yellow': [
                "What are three things you can control in your current situation?",
                "Describe your ideal peaceful place in vivid detail.",
                "What advice would you give to a friend feeling anxious about the same thing?",
                "Write about a time when you felt completely calm and centered."
            ],
            'red': [
                "What values or boundaries feel important to you right now?",
                "Describe what justice or fairness means to you in this situation.",
                "What would you do if you had unlimited power to change this situation?",
                "Write about a time when you channeled anger into positive action."
            ],
            'green': [
                "What are you most grateful for in this moment?",
                "Describe the people, places, or activities that bring you peace.",
                "What wisdom would you share with someone who is struggling?",
                "Write about a moment of perfect contentment in your life."
            ],
            'purple': [
                "What would you create if you had unlimited resources and time?",
                "Describe a wild, impossible dream you've never shared with anyone.",
                "What new skill or knowledge are you curious about?",
                "Write about a time when you felt most creative and alive."
            ]
        }
        
        # Get mood-specific prompts
        prompts = mood_prompts.get(mood, mood_prompts['green'])
        
        # Consider recent themes
        if recent_themes:
            theme_specific_prompts = {
                'relationships': "Write about the most important relationship in your life right now.",
                'work_career': "Describe your ideal work day from start to finish.",
                'personal_growth': "What is one thing you've learned about yourself recently?",
                'health_wellness': "How do you want to feel in your body and mind?"
            }
            
            for theme in recent_themes:
                if theme in theme_specific_prompts:
                    prompts.append(theme_specific_prompts[theme])
        
        # Return a random prompt
        import random
        return random.choice(prompts)
    
    def analyze_journal_patterns(self, journal_entries: List[JournalEntry], 
                                days: int = 30) -> Dict[str, Any]:
        """Analyze patterns across multiple journal entries"""
        
        if not journal_entries:
            return {}
        
        # Filter to recent entries
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = [
            entry for entry in journal_entries 
            if entry.created_at >= cutoff_date
        ]
        
        if not recent_entries:
            return {}
        
        # Analyze patterns
        mood_distribution = {}
        theme_frequency = {}
        sentiment_trend = []
        growth_indicators = []
        
        for entry in recent_entries:
            # Mood distribution
            mood = entry.emotional_context.primary_mood
            mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
            
            # Theme frequency
            for theme in entry.metadata.themes:
                theme_frequency[theme] = theme_frequency.get(theme, 0) + 1
            
            # Sentiment trend
            sentiment_trend.append({
                'date': entry.created_at.isoformat(),
                'sentiment': entry.metadata.sentiment_score
            })
            
            # Growth indicators
            if hasattr(entry, 'insights'):
                growth_indicators.extend(entry.insights)
        
        return {
            'analysis_period_days': days,
            'total_entries': len(recent_entries),
            'mood_distribution': mood_distribution,
            'top_themes': sorted(theme_frequency.items(), key=lambda x: x[1], reverse=True)[:5],
            'sentiment_trend': sentiment_trend,
            'average_sentiment': sum(entry.metadata.sentiment_score for entry in recent_entries) / len(recent_entries),
            'growth_indicators': list(set(growth_indicators))[:10],
            'writing_frequency': len(recent_entries) / days,
            'most_reflective_day': max(recent_entries, key=lambda x: len(x.insights)).created_at.strftime('%Y-%m-%d') if recent_entries else None
        }

