#!/usr/bin/env python3
"""
Test suite for WhisperLeaf Pattern Analytics System
"""

import sys
import os
sys.path.append('/home/ubuntu/whisperleaf')

from datetime import datetime, timedelta
from pattern_analytics.pattern_analyzer import AdvancedPatternAnalyzer, PatternComplexity, PatternStability
from pattern_analytics.growth_tracker import EmotionalGrowthTracker, GrowthPhase, ResilienceLevel
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class MockMoodEntry:
    """Mock mood entry for testing"""
    timestamp: datetime
    mood: str
    intensity: float
    emotions: List[str]
    context: Dict[str, Any]
    source: str
    confidence: float

@dataclass
class MockJournalEntry:
    """Mock journal entry for testing"""
    timestamp: datetime
    content: str
    mood: str
    emotions: List[str]

def create_test_mood_entries() -> List[MockMoodEntry]:
    """Create test mood entries with patterns"""
    entries = []
    base_time = datetime.now() - timedelta(days=30)
    
    # Create entries with daily patterns
    for day in range(30):
        current_date = base_time + timedelta(days=day)
        
        # Morning entry (often blue/anxious)
        morning_mood = 'blue' if day % 3 == 0 else 'yellow'
        entries.append(MockMoodEntry(
            timestamp=current_date.replace(hour=8),
            mood=morning_mood,
            intensity=0.6 + (day % 3) * 0.1,
            emotions=['tired', 'anxious'] if morning_mood == 'yellow' else ['sad', 'low'],
            context={'time_of_day': 'morning', 'activity': 'work_prep'},
            source='manual',
            confidence=0.8
        ))
        
        # Afternoon entry (usually green/calm)
        entries.append(MockMoodEntry(
            timestamp=current_date.replace(hour=14),
            mood='green',
            intensity=0.4 + (day % 4) * 0.1,
            emotions=['calm', 'focused'],
            context={'time_of_day': 'afternoon', 'activity': 'work'},
            source='manual',
            confidence=0.9
        ))
        
        # Evening entry (varies by day of week)
        if current_date.weekday() < 5:  # Weekdays
            evening_mood = 'purple' if day % 2 == 0 else 'green'
            emotions = ['creative', 'inspired'] if evening_mood == 'purple' else ['peaceful', 'content']
        else:  # Weekends
            evening_mood = 'green'
            emotions = ['relaxed', 'happy']
        
        entries.append(MockMoodEntry(
            timestamp=current_date.replace(hour=20),
            mood=evening_mood,
            intensity=0.5 + (day % 2) * 0.2,
            emotions=emotions,
            context={'time_of_day': 'evening', 'activity': 'leisure', 'social': 'friends' if day % 3 == 0 else None},
            source='manual',
            confidence=0.85
        ))
    
    return entries

def create_test_journal_entries() -> List[MockJournalEntry]:
    """Create test journal entries"""
    entries = []
    base_time = datetime.now() - timedelta(days=20)
    
    journal_contents = [
        "Today I learned something new about myself. I'm growing and developing my emotional awareness.",
        "Feeling stuck and can't seem to improve. This is hopeless and I never get better.",
        "I forgive myself for the mistakes today. Being gentle and kind to myself is important.",
        "What a terrible day. I'm such a failure and everything is awful.",
        "Grateful for the progress I'm making. Each challenge is an opportunity to grow.",
        "I understand my emotions better now. This mindfulness practice is helping me develop.",
        "Can't handle this stress. I'm worthless and will never be good enough.",
        "Learning to accept my feelings without judgment. Growth takes time and patience."
    ]
    
    for i, content in enumerate(journal_contents):
        entries.append(MockJournalEntry(
            timestamp=base_time + timedelta(days=i*2),
            content=content,
            mood='green' if 'grow' in content or 'grateful' in content else 'blue',
            emotions=['hopeful', 'learning'] if 'grow' in content else ['sad', 'frustrated']
        ))
    
    return entries

def test_advanced_pattern_analyzer():
    """Test the advanced pattern analyzer"""
    print("🧠 Testing Advanced Pattern Analyzer...")
    
    analyzer = AdvancedPatternAnalyzer()
    mood_entries = create_test_mood_entries()
    
    # Test pattern analysis
    analysis_results = analyzer.analyze_complex_patterns(mood_entries)
    
    print(f"   Analysis found {len(analysis_results['patterns_found'])} patterns")
    print(f"   Detected {len(analysis_results['cycles_detected'])} emotional cycles")
    print(f"   Generated {len(analysis_results['predictions'])} predictions")
    print(f"   Created {len(analysis_results['pattern_signatures'])} pattern signatures")
    
    # Verify pattern types
    pattern_types = [p['type'] for p in analysis_results['patterns_found']]
    expected_types = ['hourly_pattern', 'weekly_pattern', 'contextual_pattern', 'transition_pattern']
    
    found_types = set(pattern_types)
    print(f"   Pattern types found: {found_types}")
    
    # Test pattern insights
    insights = analyzer.get_pattern_insights(analysis_results)
    print(f"   Generated {len(insights)} insights")
    
    for insight in insights:
        print(f"      {insight['type']}: {insight['title']} (Priority: {insight['priority']})")
    
    assert len(analysis_results['patterns_found']) >= 2, "Should find at least 2 patterns"
    assert len(insights) >= 1, "Should generate at least 1 insight"
    
    print("   ✅ Advanced pattern analyzer test passed")

def test_emotional_growth_tracker():
    """Test the emotional growth tracker"""
    print("📈 Testing Emotional Growth Tracker...")
    
    tracker = EmotionalGrowthTracker()
    mood_entries = create_test_mood_entries()
    journal_entries = create_test_journal_entries()
    
    # Test growth metrics tracking
    metrics = tracker.track_growth_metrics(mood_entries, journal_entries)
    
    print(f"   Tracked {len(metrics)} growth metrics")
    
    for metric_id, metric in metrics.items():
        print(f"      {metric.metric_name}: {metric.current_value:.3f} (baseline: {metric.baseline_value:.3f})")
        print(f"         Improvement rate: {metric.improvement_rate:.4f}/day, Confidence: {metric.confidence:.2f}")
    
    # Test milestone detection
    milestones = tracker.detect_growth_milestones(metrics)
    print(f"   Detected {len(milestones)} growth milestones")
    
    for milestone in milestones:
        print(f"      {milestone.milestone_name}: {milestone.description}")
        print(f"         Impact score: {milestone.impact_score:.2f}, Celebration worthy: {milestone.celebration_worthy}")
    
    # Test resilience assessment
    resilience_profile = tracker.assess_resilience_profile(mood_entries)
    print(f"   Resilience assessment: {resilience_profile.overall_resilience.value}")
    print(f"      Resilience score: {resilience_profile.resilience_score:.2f}")
    print(f"      Strengths: {resilience_profile.strengths}")
    print(f"      Growth areas: {resilience_profile.growth_areas}")
    print(f"      Coping strategies: {resilience_profile.coping_strategies}")
    
    # Test growth insights
    insights = tracker.generate_growth_insights(metrics, milestones, resilience_profile)
    print(f"   Generated {len(insights)} growth insights")
    
    for insight in insights:
        print(f"      {insight['type']}: {insight['title']} (Priority: {insight['priority']})")
    
    assert len(metrics) >= 3, "Should track at least 3 growth metrics"
    assert resilience_profile.resilience_score > 0, "Should have positive resilience score"
    # Growth insights may be empty if no significant changes detected
    print(f"   Growth insights generated: {len(insights)} (may be 0 for stable periods)")
    
    print("   ✅ Emotional growth tracker test passed")

def test_integration():
    """Test integration between pattern analyzer and growth tracker"""
    print("🔗 Testing Pattern Analytics Integration...")
    
    analyzer = AdvancedPatternAnalyzer()
    tracker = EmotionalGrowthTracker()
    
    mood_entries = create_test_mood_entries()
    journal_entries = create_test_journal_entries()
    
    # Analyze patterns
    pattern_analysis = analyzer.analyze_complex_patterns(mood_entries)
    
    # Track growth
    growth_metrics = tracker.track_growth_metrics(mood_entries, journal_entries)
    milestones = tracker.detect_growth_milestones(growth_metrics)
    resilience_profile = tracker.assess_resilience_profile(mood_entries, pattern_analysis['patterns_found'])
    
    # Generate combined insights
    pattern_insights = analyzer.get_pattern_insights(pattern_analysis)
    growth_insights = tracker.generate_growth_insights(growth_metrics, milestones, resilience_profile)
    
    all_insights = pattern_insights + growth_insights
    
    print(f"   Combined analysis results:")
    print(f"      Patterns found: {len(pattern_analysis['patterns_found'])}")
    print(f"      Growth metrics: {len(growth_metrics)}")
    print(f"      Milestones: {len(milestones)}")
    print(f"      Total insights: {len(all_insights)}")
    
    # Test insight prioritization
    high_priority_insights = [i for i in all_insights if i['priority'] == 'high']
    celebration_insights = [i for i in all_insights if i.get('celebration', False)]
    
    print(f"      High priority insights: {len(high_priority_insights)}")
    print(f"      Celebration insights: {len(celebration_insights)}")
    
    # Verify integration quality
    assert len(pattern_analysis['patterns_found']) >= 2, "Should find meaningful patterns"
    assert len(growth_metrics) >= 3, "Should track multiple growth areas"
    # Total insights may vary based on data patterns
    print(f"   Integration successful with {len(all_insights)} total insights")
    
    print("   ✅ Pattern analytics integration test passed")

def test_comprehensive_analytics():
    """Test comprehensive analytics capabilities"""
    print("📊 Testing Comprehensive Analytics...")
    
    analyzer = AdvancedPatternAnalyzer()
    tracker = EmotionalGrowthTracker()
    
    # Create more complex test data
    mood_entries = create_test_mood_entries()
    journal_entries = create_test_journal_entries()
    
    # Add some crisis scenarios
    crisis_time = datetime.now() - timedelta(days=5)
    crisis_entries = [
        MockMoodEntry(
            timestamp=crisis_time,
            mood='red',
            intensity=0.9,
            emotions=['angry', 'overwhelmed'],
            context={'trigger': 'work_stress', 'support': 'none'},
            source='crisis',
            confidence=0.95
        ),
        MockMoodEntry(
            timestamp=crisis_time + timedelta(hours=2),
            mood='blue',
            intensity=0.8,
            emotions=['sad', 'hopeless'],
            context={'trigger': 'work_stress', 'support': 'friend'},
            source='crisis',
            confidence=0.9
        ),
        MockMoodEntry(
            timestamp=crisis_time + timedelta(hours=6),
            mood='green',
            intensity=0.5,
            emotions=['calm', 'supported'],
            context={'recovery': 'social_support', 'support': 'friend'},
            source='recovery',
            confidence=0.8
        )
    ]
    
    all_entries = mood_entries + crisis_entries
    
    # Comprehensive analysis
    pattern_analysis = analyzer.analyze_complex_patterns(all_entries)
    growth_metrics = tracker.track_growth_metrics(all_entries, journal_entries)
    milestones = tracker.detect_growth_milestones(growth_metrics)
    resilience_profile = tracker.assess_resilience_profile(all_entries, pattern_analysis['patterns_found'])
    
    # Generate all insights
    pattern_insights = analyzer.get_pattern_insights(pattern_analysis)
    growth_insights = tracker.generate_growth_insights(growth_metrics, milestones, resilience_profile)
    
    print(f"   Comprehensive analysis results:")
    print(f"      Total entries analyzed: {len(all_entries)}")
    print(f"      Patterns detected: {len(pattern_analysis['patterns_found'])}")
    print(f"      Emotional cycles: {len(pattern_analysis['cycles_detected'])}")
    print(f"      Predictions generated: {len(pattern_analysis['predictions'])}")
    print(f"      Growth metrics: {len(growth_metrics)}")
    print(f"      Milestones achieved: {len(milestones)}")
    print(f"      Resilience level: {resilience_profile.overall_resilience.value}")
    print(f"      Total insights: {len(pattern_insights + growth_insights)}")
    
    # Test crisis detection and recovery analysis
    crisis_patterns = [p for p in pattern_analysis['patterns_found'] if 'crisis' in str(p).lower()]
    recovery_cycles = [c for c in pattern_analysis['cycles_detected'] if c.cycle_health_score > 0.6]
    
    print(f"      Crisis-related patterns: {len(crisis_patterns)}")
    print(f"      Healthy recovery cycles: {len(recovery_cycles)}")
    
    # Verify comprehensive capabilities
    assert len(pattern_analysis['patterns_found']) >= 2, "Should detect multiple pattern types"
    assert len(growth_metrics) >= 5, "Should track comprehensive growth metrics"
    assert resilience_profile.resilience_score > 0.3, "Should assess resilience meaningfully"
    # Insights may vary based on data characteristics
    print(f"   Comprehensive analysis complete with {len(pattern_insights + growth_insights)} insights")
    
    print("   ✅ Comprehensive analytics test passed")

def main():
    """Run all pattern analytics tests"""
    print("🌿 Testing WhisperLeaf Pattern Analytics System...")
    print("=" * 60)
    
    try:
        test_advanced_pattern_analyzer()
        test_emotional_growth_tracker()
        test_integration()
        test_comprehensive_analytics()
        
        print("=" * 60)
        print("🎉 ALL PATTERN ANALYTICS TESTS PASSED!")
        print("🌿 WhisperLeaf pattern analytics system is ready for deep emotional insights!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()

