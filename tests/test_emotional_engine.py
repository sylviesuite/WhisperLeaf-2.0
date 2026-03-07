#!/usr/bin/env python3
"""
WhisperLeaf Emotional Intelligence Engine Test Suite
Tests all emotional intelligence components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import emotional engine components
sys.path.append('/home/ubuntu/whisperleaf')
from emotional_engine.big_mood import BigMoodClassifier, MoodColor, MoodAnalysis
from emotional_engine.emotion_detector import EmotionDetector
from emotional_engine.tone_engine import AdaptiveToneEngine
from emotional_engine.crisis_detector import CrisisDetector, CrisisLevel
from emotional_engine.emotional_processor import EmotionalProcessor

def test_big_mood_classifier():
    """Test Big Mood classification system"""
    print("🎨 Testing Big Mood Classifier...")
    
    classifier = BigMoodClassifier()
    
    # Test different mood scenarios
    test_cases = [
        ("I'm feeling really sad today", MoodColor.BLUE),
        ("I'm so anxious about tomorrow", MoodColor.YELLOW),
        ("I'm feeling calm and peaceful", MoodColor.GREEN),
        ("I'm so angry and frustrated", MoodColor.RED),
        ("I'm feeling creative and inspired", MoodColor.PURPLE)
    ]
    
    for text, expected_mood in test_cases:
        analysis = classifier.classify_mood(text)
        print(f"   Text: '{text}'")
        print(f"   Expected: {expected_mood.value}, Got: {analysis.primary_mood.value}")
        print(f"   Confidence: {analysis.confidence:.2f}")
        print(f"   Reasoning: {analysis.reasoning}")
        
        assert analysis.primary_mood == expected_mood, f"Expected {expected_mood}, got {analysis.primary_mood}"
        assert analysis.confidence > 0.3, f"Low confidence: {analysis.confidence}"
        print("   ✅ Passed\n")
    
    print("   🎉 Big Mood Classifier tests complete!")

def test_emotion_detector():
    """Test emotion detection system"""
    print("\n💝 Testing Emotion Detector...")
    
    detector = EmotionDetector()
    
    # Test emotion detection
    test_cases = [
        "I'm feeling incredibly sad and hopeless",
        "I'm so excited about this new opportunity!",
        "I'm really worried about my health",
        "I'm furious about what happened",
        "I feel completely lost and confused"
    ]
    
    for text in test_cases:
        analysis = detector.analyze_emotions(text)
        print(f"   Text: '{text}'")
        print(f"   Primary emotions: {[e.emotion for e in analysis.primary_emotions[:3]]}")
        print(f"   Mood: {analysis.mood_analysis.primary_mood.value}")
        print(f"   Intensity: {analysis.intensity_score:.2f}")
        print(f"   Complexity: {analysis.complexity_score:.2f}")
        print(f"   Support needs: {analysis.support_needs}")
        
        assert len(analysis.primary_emotions) > 0, "No emotions detected"
        assert analysis.intensity_score >= 0.0, "Invalid intensity score"
        print("   ✅ Passed\n")
    
    print("   🎉 Emotion Detector tests complete!")

def test_crisis_detector():
    """Test crisis detection system"""
    print("\n🚨 Testing Crisis Detector...")
    
    detector = CrisisDetector()
    
    # Test crisis scenarios
    test_cases = [
        ("I'm having a great day!", CrisisLevel.NONE),
        ("I'm feeling a bit down", CrisisLevel.NONE),
        ("I'm really struggling and feel hopeless", CrisisLevel.LOW),
        ("I can't take it anymore, I want to die", CrisisLevel.CRITICAL),
        ("I'm thinking about hurting myself", CrisisLevel.HIGH)
    ]
    
    for text, expected_level in test_cases:
        assessment = detector.assess_crisis(text)
        print(f"   Text: '{text}'")
        print(f"   Expected level: {expected_level.value}, Got: {assessment.overall_level.value}")
        print(f"   Confidence: {assessment.confidence:.2f}")
        print(f"   Indicators: {len(assessment.indicators)}")
        print(f"   Immediate actions: {len(assessment.immediate_actions)}")
        
        # For critical cases, ensure proper detection
        if expected_level == CrisisLevel.CRITICAL:
            assert assessment.overall_level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL], \
                f"Failed to detect crisis: {assessment.overall_level.value}"
        elif expected_level == CrisisLevel.NONE:
            assert assessment.overall_level in [CrisisLevel.NONE, CrisisLevel.LOW], \
                f"False positive crisis detection: {assessment.overall_level.value}"
        
        print("   ✅ Passed\n")
    
    print("   🎉 Crisis Detector tests complete!")

def test_adaptive_tone_engine():
    """Test adaptive tone engine"""
    print("\n🎭 Testing Adaptive Tone Engine...")
    
    # Create mock emotion analysis for testing
    from emotional_engine.emotion_detector import EmotionAnalysis, EmotionalContext
    from emotional_engine.big_mood import MoodAnalysis
    
    tone_engine = AdaptiveToneEngine()
    
    # Test different emotional scenarios
    scenarios = [
        {
            'name': 'Sad user',
            'mood': MoodColor.BLUE,
            'intensity': 0.8,
            'expected_style': 'gentle'
        },
        {
            'name': 'Anxious user',
            'mood': MoodColor.YELLOW,
            'intensity': 0.7,
            'expected_style': 'calming'
        },
        {
            'name': 'Creative user',
            'mood': MoodColor.PURPLE,
            'intensity': 0.6,
            'expected_style': 'engaging'
        }
    ]
    
    for scenario in scenarios:
        # Create mock emotion analysis
        mood_analysis = MoodAnalysis(
            primary_mood=scenario['mood'],
            confidence=0.8,
            reasoning="Test scenario"
        )
        
        emotional_context = EmotionalContext(
            temporal_pattern='present',
            certainty_level='certain',
            social_context='self',
            action_orientation='passive'
        )
        
        emotion_analysis = EmotionAnalysis(
            primary_emotions=[],
            mood_analysis=mood_analysis,
            emotional_context=emotional_context,
            intensity_score=scenario['intensity'],
            complexity_score=0.3,
            crisis_indicators=[],
            support_needs=['emotional_support'],
            reasoning="Test analysis"
        )
        
        guidance = tone_engine.generate_tone_profile(emotion_analysis)
        
        print(f"   Scenario: {scenario['name']}")
        print(f"   Tone style: {guidance.tone_profile.primary_style.value}")
        print(f"   Intensity: {guidance.tone_profile.intensity.value}")
        print(f"   Suggested openings: {len(guidance.suggested_openings)}")
        print(f"   Support strategies: {len(guidance.support_strategies)}")
        
        assert guidance.tone_profile.primary_style.value == scenario['expected_style'], \
            f"Expected {scenario['expected_style']}, got {guidance.tone_profile.primary_style.value}"
        assert len(guidance.suggested_openings) > 0, "No suggested openings"
        print("   ✅ Passed\n")
    
    print("   🎉 Adaptive Tone Engine tests complete!")

def test_emotional_processor():
    """Test main emotional processor integration"""
    print("\n🧠 Testing Emotional Processor Integration...")
    
    processor = EmotionalProcessor()
    
    # Test various emotional inputs
    test_inputs = [
        "I'm feeling really happy today!",
        "I'm so worried about my job interview tomorrow",
        "I feel completely hopeless and want to give up",
        "I'm excited about starting this new creative project",
        "I'm angry that nobody seems to understand me"
    ]
    
    for text in test_inputs:
        response = processor.process_emotional_input(text)
        
        print(f"   Input: '{text}'")
        print(f"   Mood: {response.emotion_analysis.mood_analysis.primary_mood.value}")
        print(f"   Crisis level: {response.crisis_assessment.overall_level.value}")
        print(f"   Tone style: {response.response_guidance.tone_profile.primary_style.value}")
        print(f"   Safety flags: {len(response.safety_flags)}")
        print(f"   Processing time: {response.processing_metadata['processing_time_seconds']:.3f}s")
        
        # Verify response structure
        assert response.emotion_analysis is not None, "Missing emotion analysis"
        assert response.crisis_assessment is not None, "Missing crisis assessment"
        assert response.response_guidance is not None, "Missing response guidance"
        assert response.ai_prompt is not None, "Missing AI prompt"
        assert len(response.ai_prompt) > 100, "AI prompt too short"
        
        # Check for crisis detection in concerning text
        if "hopeless" in text or "give up" in text:
            assert response.crisis_assessment.overall_level != CrisisLevel.NONE, \
                "Failed to detect crisis in concerning text"
        
        print("   ✅ Passed\n")
    
    print("   🎉 Emotional Processor integration tests complete!")

def test_ai_prompt_generation():
    """Test AI prompt generation quality"""
    print("\n📝 Testing AI Prompt Generation...")
    
    processor = EmotionalProcessor()
    
    # Test crisis scenario
    crisis_text = "I can't take it anymore, I want to end it all"
    response = processor.process_emotional_input(crisis_text)
    
    print(f"   Crisis text: '{crisis_text}'")
    print(f"   AI Prompt length: {len(response.ai_prompt)} characters")
    print(f"   Contains crisis alert: {'CRISIS ALERT' in response.ai_prompt}")
    print(f"   Contains tone guidance: {'TONE GUIDANCE' in response.ai_prompt}")
    print(f"   Contains constitutional guidance: {'CONSTITUTIONAL GUIDANCE' in response.ai_prompt}")
    
    # Verify crisis prompt quality
    assert "CRISIS ALERT" in response.ai_prompt, "Missing crisis alert in prompt"
    assert "TONE GUIDANCE" in response.ai_prompt, "Missing tone guidance"
    assert "emotional safety" in response.ai_prompt.lower(), "Missing safety emphasis"
    assert len(response.ai_prompt) > 500, "AI prompt too short for crisis situation"
    
    print("   ✅ Crisis prompt generation passed")
    
    # Test normal scenario
    normal_text = "I'm feeling pretty good today, just reflecting on life"
    response = processor.process_emotional_input(normal_text)
    
    print(f"\n   Normal text: '{normal_text}'")
    print(f"   AI Prompt length: {len(response.ai_prompt)} characters")
    print(f"   Contains emotional context: {'EMOTIONAL CONTEXT' in response.ai_prompt}")
    print(f"   No crisis alert: {'CRISIS ALERT' not in response.ai_prompt}")
    
    # Verify normal prompt quality
    assert "EMOTIONAL CONTEXT" in response.ai_prompt, "Missing emotional context"
    assert "CRISIS ALERT" not in response.ai_prompt, "False crisis alert"
    assert len(response.ai_prompt) > 200, "AI prompt too short"
    
    print("   ✅ Normal prompt generation passed")
    print("   🎉 AI Prompt generation tests complete!")

def test_performance():
    """Test processing performance"""
    print("\n⚡ Testing Processing Performance...")
    
    processor = EmotionalProcessor()
    
    # Test processing speed
    test_text = "I'm feeling anxious about my presentation tomorrow but also excited about the opportunity"
    
    import time
    start_time = time.time()
    
    # Process multiple times to get average
    for _ in range(5):
        response = processor.process_emotional_input(test_text)
    
    end_time = time.time()
    avg_time = (end_time - start_time) / 5
    
    print(f"   Average processing time: {avg_time:.3f} seconds")
    print(f"   Processing speed: {'✅ Fast' if avg_time < 1.0 else '⚠️ Slow'}")
    
    # Verify performance is reasonable
    assert avg_time < 2.0, f"Processing too slow: {avg_time:.3f}s"
    
    # Test memory usage is reasonable
    response = processor.process_emotional_input(test_text)
    metadata = response.processing_metadata
    
    print(f"   Components used: {len(metadata['components_used'])}")
    print(f"   Metadata size: {len(str(metadata))} characters")
    
    assert len(metadata['components_used']) == 4, "Missing components"
    
    print("   🎉 Performance tests complete!")

def main():
    """Run all emotional intelligence tests"""
    print("🌿 WhisperLeaf Emotional Intelligence Test Suite")
    print("=" * 60)
    
    try:
        test_big_mood_classifier()
        test_emotion_detector()
        test_crisis_detector()
        test_adaptive_tone_engine()
        test_emotional_processor()
        test_ai_prompt_generation()
        test_performance()
        
        print("\n" + "=" * 60)
        print("🎉 ALL EMOTIONAL INTELLIGENCE TESTS PASSED!")
        print("🌿 WhisperLeaf emotional engine is ready for empathetic AI!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

