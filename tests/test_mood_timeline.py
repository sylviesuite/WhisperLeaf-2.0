#!/usr/bin/env python3
"""
Test suite for WhisperLeaf Mood Timeline System
"""

import sys
import os
import tempfile
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.insert(0, '/home/ubuntu/whisperleaf')

from mood_timeline.timeline_manager import MoodTimelineManager
from mood_timeline.timeline_models import (
    MoodEntry, TimelineGranularity, MoodTrend, PatternType
)

def test_mood_timeline_system():
    """Test the complete mood timeline system"""
    
    print("🌿 Testing WhisperLeaf Mood Timeline System...")
    print("=" * 60)
    
    try:
        # Test timeline manager initialization
        test_timeline_manager_initialization()
        
        # Test mood entry management
        test_mood_entry_management()
        
        # Test timeline summaries
        test_timeline_summaries()
        
        # Test pattern recognition
        test_pattern_recognition()
        
        # Test visualization data generation
        test_visualization_data()
        
        # Test statistics and analytics
        test_statistics_and_analytics()
        
        print("=" * 60)
        print("🎉 ALL MOOD TIMELINE TESTS PASSED!")
        print("🌿 WhisperLeaf mood timeline system is ready for emotional tracking!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise

def test_timeline_manager_initialization():
    """Test timeline manager initialization"""
    print("🧠 Testing Timeline Manager Initialization...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Test initialization
        assert manager.data_dir.exists(), "Data directory should be created"
        assert manager.db_path.exists(), "Database should be created"
        assert isinstance(manager.patterns, dict), "Patterns should be initialized"
        assert isinstance(manager.insights, dict), "Insights should be initialized"
        assert isinstance(manager.timeline_stats, dict), "Timeline stats should be initialized"
        
        # Test initial statistics
        stats = manager.get_timeline_statistics()
        assert stats['timeline_stats']['total_entries'] == 0, "Should start with 0 entries"
        assert stats['patterns_summary']['total_patterns'] == 0, "Should start with 0 patterns"
        assert stats['insights_summary']['total_insights'] == 0, "Should start with 0 insights"
        
        print("   ✅ Timeline manager initialization test passed")

def test_mood_entry_management():
    """Test mood entry creation, storage, and retrieval"""
    print("📝 Testing Mood Entry Management...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Test adding mood entries
        now = datetime.now()
        
        # Add various mood entries
        test_entries = [
            {
                'mood': 'blue',
                'intensity': 0.6,
                'emotions': ['sad', 'reflective'],
                'context': {'location': 'home', 'activity': 'journaling'},
                'notes': 'Feeling contemplative today',
                'tags': ['reflection', 'home'],
                'timestamp': now - timedelta(hours=3)
            },
            {
                'mood': 'green',
                'intensity': 0.8,
                'emotions': ['calm', 'peaceful'],
                'context': {'location': 'park', 'activity': 'walking'},
                'notes': 'Beautiful walk in nature',
                'tags': ['nature', 'exercise'],
                'timestamp': now - timedelta(hours=2)
            },
            {
                'mood': 'yellow',
                'intensity': 0.4,
                'emotions': ['anxious', 'worried'],
                'context': {'location': 'work', 'activity': 'meeting'},
                'notes': 'Stressful presentation',
                'tags': ['work', 'stress'],
                'timestamp': now - timedelta(hours=1)
            }
        ]
        
        entry_ids = []
        for entry_data in test_entries:
            entry_id = manager.add_mood_entry(**entry_data)
            entry_ids.append(entry_id)
            assert entry_id.startswith('mood_'), f"Entry ID should start with 'mood_': {entry_id}"
        
        # Test retrieving entries
        all_entries = manager.get_mood_entries()
        assert len(all_entries) == 3, f"Should have 3 entries, got {len(all_entries)}"
        
        # Test filtering by mood
        blue_entries = manager.get_mood_entries(mood_filter=['blue'])
        assert len(blue_entries) == 1, f"Should have 1 blue entry, got {len(blue_entries)}"
        assert blue_entries[0].mood == 'blue', "Filtered entry should be blue mood"
        
        # Test date range filtering
        recent_entries = manager.get_mood_entries(start_date=now - timedelta(hours=2.5))
        assert len(recent_entries) == 2, f"Should have 2 recent entries, got {len(recent_entries)}"
        
        # Test limit
        limited_entries = manager.get_mood_entries(limit=2)
        assert len(limited_entries) == 2, f"Should have 2 limited entries, got {len(limited_entries)}"
        
        # Verify entry structure
        entry = all_entries[0]
        assert isinstance(entry, MoodEntry), "Should return MoodEntry objects"
        assert entry.mood in ['blue', 'green', 'yellow', 'purple', 'red'], "Should have valid mood"
        assert 0.0 <= entry.intensity <= 1.0, "Intensity should be between 0 and 1"
        assert isinstance(entry.emotions, list), "Emotions should be a list"
        assert isinstance(entry.context, dict), "Context should be a dictionary"
        
        print(f"      Added {len(entry_ids)} mood entries successfully")
        print(f"      Retrieved and filtered entries correctly")
        
        print("   ✅ Mood entry management test passed")

def test_timeline_summaries():
    """Test timeline summary generation"""
    print("📊 Testing Timeline Summaries...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Add test data spanning several days
        base_time = datetime.now() - timedelta(days=7)
        
        test_data = [
            ('blue', 0.3, ['sad'], base_time),
            ('blue', 0.4, ['melancholy'], base_time + timedelta(hours=6)),
            ('green', 0.7, ['calm'], base_time + timedelta(days=1)),
            ('green', 0.8, ['peaceful'], base_time + timedelta(days=1, hours=6)),
            ('yellow', 0.5, ['anxious'], base_time + timedelta(days=2)),
            ('purple', 0.9, ['creative'], base_time + timedelta(days=3)),
            ('red', 0.6, ['frustrated'], base_time + timedelta(days=4)),
            ('green', 0.8, ['content'], base_time + timedelta(days=5)),
        ]
        
        for mood, intensity, emotions, timestamp in test_data:
            manager.add_mood_entry(
                mood=mood,
                intensity=intensity,
                emotions=emotions,
                context={'test': True},
                timestamp=timestamp
            )
        
        # Test timeline summary
        start_date = base_time
        end_date = base_time + timedelta(days=6)
        
        summary = manager.get_timeline_summary(start_date, end_date, TimelineGranularity.DAILY)
        
        # Validate summary structure
        assert summary.total_entries == 8, f"Should have 8 entries, got {summary.total_entries}"
        assert isinstance(summary.mood_distribution, dict), "Should have mood distribution"
        assert summary.dominant_mood in ['blue', 'green', 'yellow', 'purple', 'red'], "Should have valid dominant mood"
        assert 0.0 <= summary.average_intensity <= 1.0, "Average intensity should be valid"
        assert isinstance(summary.mood_trend, MoodTrend), "Should have mood trend"
        assert 0.0 <= summary.volatility_score <= 1.0, "Volatility score should be valid"
        
        # Check mood distribution
        assert 'green' in summary.mood_distribution, "Should track green moods"
        assert 'blue' in summary.mood_distribution, "Should track blue moods"
        assert summary.mood_distribution['green'] == 3, "Should have 3 green entries"
        assert summary.mood_distribution['blue'] == 2, "Should have 2 blue entries"
        
        # Check that dominant mood is green (most frequent)
        assert summary.dominant_mood == 'green', f"Dominant mood should be green, got {summary.dominant_mood}"
        
        # Check average intensity calculation
        expected_avg = sum(intensity for _, intensity, _, _ in test_data) / len(test_data)
        assert abs(summary.average_intensity - expected_avg) < 0.01, "Average intensity should be calculated correctly"
        
        print(f"      Summary covers {summary.total_entries} entries over {(end_date - start_date).days} days")
        print(f"      Dominant mood: {summary.dominant_mood}")
        print(f"      Average intensity: {summary.average_intensity:.2f}")
        print(f"      Mood trend: {summary.mood_trend.value}")
        print(f"      Volatility: {summary.volatility_score:.2f}")
        
        print("   ✅ Timeline summaries test passed")

def test_pattern_recognition():
    """Test pattern recognition and analysis"""
    print("🔍 Testing Pattern Recognition...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Create pattern data - daily cycle
        base_time = datetime.now() - timedelta(days=10)
        
        # Simulate a daily pattern: blue mornings, green afternoons, yellow evenings
        pattern_data = []
        for day in range(10):
            day_base = base_time + timedelta(days=day)
            
            # Morning - blue (sad/reflective)
            pattern_data.append({
                'mood': 'blue',
                'intensity': 0.4,
                'emotions': ['reflective'],
                'context': {'time_of_day': 'morning'},
                'timestamp': day_base.replace(hour=8)
            })
            
            # Afternoon - green (calm)
            pattern_data.append({
                'mood': 'green',
                'intensity': 0.7,
                'emotions': ['calm'],
                'context': {'time_of_day': 'afternoon'},
                'timestamp': day_base.replace(hour=14)
            })
            
            # Evening - yellow (anxious)
            pattern_data.append({
                'mood': 'yellow',
                'intensity': 0.5,
                'emotions': ['anxious'],
                'context': {'time_of_day': 'evening'},
                'timestamp': day_base.replace(hour=20)
            })
        
        # Add all pattern data
        for entry_data in pattern_data:
            manager.add_mood_entry(**entry_data)
        
        # Force pattern analysis
        manager._analyze_patterns()
        
        # Check for detected patterns
        patterns = manager.get_patterns()
        
        # Should detect some patterns with this much structured data
        print(f"      Detected {len(patterns)} patterns")
        
        for pattern in patterns:
            print(f"        Pattern: {pattern.name} ({pattern.pattern_type.value})")
            print(f"          Strength: {pattern.strength:.2f}")
            print(f"          Confidence: {pattern.confidence:.2f}")
            print(f"          Triggers: {pattern.triggers}")
        
        # Test pattern filtering
        daily_patterns = manager.get_patterns(PatternType.DAILY_CYCLE)
        trigger_patterns = manager.get_patterns(PatternType.TRIGGER_BASED)
        
        print(f"      Daily patterns: {len(daily_patterns)}")
        print(f"      Trigger patterns: {len(trigger_patterns)}")
        
        # Patterns should be detected with this structured data
        assert len(patterns) > 0, "Should detect at least one pattern with structured data"
        
        print("   ✅ Pattern recognition test passed")

def test_visualization_data():
    """Test visualization data generation"""
    print("📈 Testing Visualization Data Generation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Add test data for visualization
        base_time = datetime.now() - timedelta(days=5)
        
        viz_data = [
            ('blue', 0.3, ['sad'], base_time),
            ('green', 0.7, ['calm'], base_time + timedelta(days=1)),
            ('yellow', 0.5, ['anxious'], base_time + timedelta(days=2)),
            ('purple', 0.9, ['creative'], base_time + timedelta(days=3)),
            ('red', 0.6, ['frustrated'], base_time + timedelta(days=4)),
        ]
        
        for mood, intensity, emotions, timestamp in viz_data:
            manager.add_mood_entry(
                mood=mood,
                intensity=intensity,
                emotions=emotions,
                context={'visualization_test': True},
                notes=f"Test entry for {mood} mood",
                timestamp=timestamp
            )
        
        # Generate visualization data
        start_date = base_time
        end_date = base_time + timedelta(days=5)
        
        viz = manager.generate_visualization_data(start_date, end_date, chart_type="line")
        
        # Validate visualization structure
        assert viz.visualization_id.startswith('timeline_'), "Should have proper visualization ID"
        assert viz.chart_type == "line", "Should preserve chart type"
        assert viz.time_range[0] == start_date, "Should preserve start date"
        assert viz.time_range[1] == end_date, "Should preserve end date"
        assert len(viz.data_points) == 5, f"Should have 5 data points, got {len(viz.data_points)}"
        
        # Check data points structure
        for point in viz.data_points:
            assert 'timestamp' in point, "Data point should have timestamp"
            assert 'mood' in point, "Data point should have mood"
            assert 'intensity' in point, "Data point should have intensity"
            assert 'emotions' in point, "Data point should have emotions"
            assert point['mood'] in ['blue', 'green', 'yellow', 'purple', 'red'], "Should have valid mood"
        
        # Check styling
        assert 'colors' in viz.styling, "Should have color styling"
        assert 'blue' in viz.styling['colors'], "Should have blue color defined"
        assert viz.styling['colors']['blue'] == '#4A90E2', "Should have correct blue color"
        
        # Check interactive elements
        assert 'zoom' in viz.interactive_elements, "Should support zoom interaction"
        assert 'hover' in viz.interactive_elements, "Should support hover interaction"
        
        print(f"      Generated visualization with {len(viz.data_points)} data points")
        print(f"      Chart type: {viz.chart_type}")
        print(f"      Interactive elements: {viz.interactive_elements}")
        print(f"      Color scheme: {len(viz.styling['colors'])} mood colors")
        
        print("   ✅ Visualization data generation test passed")

def test_statistics_and_analytics():
    """Test statistics and analytics features"""
    print("📊 Testing Statistics and Analytics...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = MoodTimelineManager(data_dir=temp_dir)
        
        # Add comprehensive test data
        base_time = datetime.now() - timedelta(days=14)
        
        # Create varied data for statistics
        stats_data = []
        moods = ['blue', 'green', 'yellow', 'purple', 'red']
        sources = ['manual', 'journal', 'conversation', 'prompt_response']
        
        for day in range(14):
            for i in range(2):  # 2 entries per day
                mood = moods[day % len(moods)]
                source = sources[i % len(sources)]
                timestamp = base_time + timedelta(days=day, hours=i*6)
                
                stats_data.append({
                    'mood': mood,
                    'intensity': 0.3 + (day * 0.05) % 0.7,  # Varying intensity
                    'emotions': [f'{mood}_emotion'],
                    'context': {'day': day, 'entry': i},
                    'source': source,
                    'timestamp': timestamp
                })
        
        # Add all data
        for entry_data in stats_data:
            manager.add_mood_entry(**entry_data)
        
        # Get comprehensive statistics
        stats = manager.get_timeline_statistics()
        
        # Validate statistics structure
        assert 'timeline_stats' in stats, "Should have timeline stats"
        assert 'patterns_summary' in stats, "Should have patterns summary"
        assert 'insights_summary' in stats, "Should have insights summary"
        
        timeline_stats = stats['timeline_stats']
        
        # Check basic counts
        assert timeline_stats['total_entries'] == len(stats_data), f"Should track total entries: {timeline_stats['total_entries']} vs {len(stats_data)}"
        
        # Check mood distribution
        assert 'entries_by_mood' in timeline_stats, "Should track entries by mood"
        mood_counts = timeline_stats['entries_by_mood']
        
        # Each mood should appear multiple times
        for mood in moods:
            if mood in mood_counts:
                assert mood_counts[mood] > 0, f"Should have entries for {mood} mood"
        
        # Check source distribution
        assert 'entries_by_source' in timeline_stats, "Should track entries by source"
        source_counts = timeline_stats['entries_by_source']
        
        for source in sources:
            if source in source_counts:
                assert source_counts[source] > 0, f"Should have entries for {source} source"
        
        # Check date tracking
        assert timeline_stats['first_entry'] is not None, "Should track first entry"
        assert timeline_stats['last_entry'] is not None, "Should track last entry"
        assert timeline_stats['tracking_days'] > 0, "Should calculate tracking days"
        
        # Check patterns summary
        patterns_summary = stats['patterns_summary']
        assert 'total_patterns' in patterns_summary, "Should track total patterns"
        assert 'patterns_by_type' in patterns_summary, "Should track patterns by type"
        
        # Check insights summary
        insights_summary = stats['insights_summary']
        assert 'total_insights' in insights_summary, "Should track total insights"
        assert 'insights_by_category' in insights_summary, "Should track insights by category"
        
        print(f"      Total entries: {timeline_stats['total_entries']}")
        print(f"      Tracking period: {timeline_stats['tracking_days']} days")
        print(f"      Mood distribution: {dict(list(mood_counts.items())[:3])}")
        print(f"      Source distribution: {dict(list(source_counts.items())[:3])}")
        print(f"      Patterns detected: {patterns_summary['total_patterns']}")
        print(f"      Insights generated: {insights_summary['total_insights']}")
        
        print("   ✅ Statistics and analytics test passed")

if __name__ == "__main__":
    test_mood_timeline_system()

