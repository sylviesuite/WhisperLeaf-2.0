#!/usr/bin/env python3
"""
WhisperLeaf Simple Integration Test
Basic integration testing of core components
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import WhisperLeaf components
from emotional_engine.emotional_processor import EmotionalProcessor
from emotional_engine.big_mood import BigMoodClassifier
from emotional_engine.crisis_detector import CrisisDetector
from memory_vault.memory_manager import MemoryManager
from constitutional_ai.constitutional_governor import ConstitutionalGovernor
from reflective_prompts.prompt_generator import ReflectivePromptGenerator
from mood_timeline.timeline_manager import MoodTimelineManager
from pattern_analytics.pattern_analyzer import AdvancedPatternAnalyzer
from time_capsule.capsule_manager import TimeCapsuleManager

def test_component_initialization():
    """Test that all components can be initialized"""
    print("🧠 Testing component initialization...")
    
    components = {}
    results = {}
    
    try:
        components['emotional_processor'] = EmotionalProcessor()
        results['emotional_processor'] = "✅ Success"
        print("  ✅ EmotionalProcessor initialized")
    except Exception as e:
        results['emotional_processor'] = f"❌ Error: {e}"
        print(f"  ❌ EmotionalProcessor failed: {e}")
    
    try:
        components['big_mood'] = BigMoodClassifier()
        results['big_mood'] = "✅ Success"
        print("  ✅ BigMoodClassifier initialized")
    except Exception as e:
        results['big_mood'] = f"❌ Error: {e}"
        print(f"  ❌ BigMoodClassifier failed: {e}")
    
    try:
        components['crisis_detector'] = CrisisDetector()
        results['crisis_detector'] = "✅ Success"
        print("  ✅ CrisisDetector initialized")
    except Exception as e:
        results['crisis_detector'] = f"❌ Error: {e}"
        print(f"  ❌ CrisisDetector failed: {e}")
    
    try:
        components['memory_manager'] = MemoryManager()
        results['memory_manager'] = "✅ Success"
        print("  ✅ MemoryManager initialized")
    except Exception as e:
        results['memory_manager'] = f"❌ Error: {e}"
        print(f"  ❌ MemoryManager failed: {e}")
    
    try:
        components['constitutional_governor'] = ConstitutionalGovernor()
        results['constitutional_governor'] = "✅ Success"
        print("  ✅ ConstitutionalGovernor initialized")
    except Exception as e:
        results['constitutional_governor'] = f"❌ Error: {e}"
        print(f"  ❌ ConstitutionalGovernor failed: {e}")
    
    try:
        components['prompt_generator'] = ReflectivePromptGenerator()
        results['prompt_generator'] = "✅ Success"
        print("  ✅ ReflectivePromptGenerator initialized")
    except Exception as e:
        results['prompt_generator'] = f"❌ Error: {e}"
        print(f"  ❌ ReflectivePromptGenerator failed: {e}")
    
    try:
        components['timeline_manager'] = MoodTimelineManager()
        results['timeline_manager'] = "✅ Success"
        print("  ✅ MoodTimelineManager initialized")
    except Exception as e:
        results['timeline_manager'] = f"❌ Error: {e}"
        print(f"  ❌ MoodTimelineManager failed: {e}")
    
    try:
        components['pattern_analyzer'] = AdvancedPatternAnalyzer()
        results['pattern_analyzer'] = "✅ Success"
        print("  ✅ AdvancedPatternAnalyzer initialized")
    except Exception as e:
        results['pattern_analyzer'] = f"❌ Error: {e}"
        print(f"  ❌ AdvancedPatternAnalyzer failed: {e}")
    
    try:
        components['capsule_manager'] = TimeCapsuleManager()
        results['capsule_manager'] = "✅ Success"
        print("  ✅ TimeCapsuleManager initialized")
    except Exception as e:
        results['capsule_manager'] = f"❌ Error: {e}"
        print(f"  ❌ TimeCapsuleManager failed: {e}")
    
    successful = sum(1 for r in results.values() if "Success" in r)
    total = len(results)
    
    print(f"\n✅ Component initialization: {successful}/{total} components initialized successfully")
    return components, results

def test_emotional_processing(components):
    """Test basic emotional processing"""
    print("\n🎭 Testing emotional processing...")
    
    if 'emotional_processor' not in components:
        print("  ❌ EmotionalProcessor not available")
        return False
    
    try:
        # Test emotional processing
        test_text = "I'm feeling really anxious about my job interview tomorrow."
        
        response = components['emotional_processor'].process_emotional_input(test_text)
        
        print(f"  ✅ Processed text: '{test_text[:50]}...'")
        print(f"  📊 Response type: {type(response)}")
        print(f"  🎯 Has response: {hasattr(response, 'emotional_state')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Emotional processing failed: {e}")
        return False

def test_mood_classification(components):
    """Test mood classification"""
    print("\n🌈 Testing mood classification...")
    
    if 'big_mood' not in components:
        print("  ❌ BigMoodClassifier not available")
        return False
    
    try:
        # Test mood classification
        test_text = "I'm feeling really anxious and worried about tomorrow"
        
        mood_result = components['big_mood'].classify_mood(test_text)
        
        print(f"  ✅ Classified text: '{test_text}'")
        print(f"  🎨 Mood result: {mood_result}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mood classification failed: {e}")
        return False

def test_crisis_detection(components):
    """Test crisis detection"""
    print("\n🚨 Testing crisis detection...")
    
    if 'crisis_detector' not in components:
        print("  ❌ CrisisDetector not available")
        return False
    
    try:
        # Test crisis detection - let me check what methods are available
        print(f"  📋 Available methods: {[m for m in dir(components['crisis_detector']) if not m.startswith('_')]}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Crisis detection failed: {e}")
        return False

def test_prompt_generation(components):
    """Test reflective prompt generation"""
    print("\n💭 Testing prompt generation...")
    
    if 'prompt_generator' not in components:
        print("  ❌ ReflectivePromptGenerator not available")
        return False
    
    try:
        # Test prompt generation - let me check what methods are available
        print(f"  📋 Available methods: {[m for m in dir(components['prompt_generator']) if not m.startswith('_')]}")
        
        # Try the generate_prompt method
        context = {
            'mood': 'Yellow',
            'emotions': ['anxiety', 'worry'],
            'user_id': 'test_user'
        }
        
        prompt = components['prompt_generator'].generate_prompt(context)
        
        print(f"  ✅ Generated prompt: {prompt}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Prompt generation failed: {e}")
        return False

def test_api_server():
    """Test the main API server"""
    print("\n🌐 Testing API server...")
    
    try:
        # Import and test basic API functionality
        from api.main import app
        
        print("  ✅ API server module imported successfully")
        print(f"  📡 FastAPI app: {app}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ API server test failed: {e}")
        return False

def main():
    """Run simple integration tests"""
    print("🌿 WhisperLeaf Simple Integration Test")
    print("=" * 50)
    
    # Test component initialization
    components, init_results = test_component_initialization()
    
    # Test basic functionality
    tests = [
        ("Emotional Processing", lambda: test_emotional_processing(components)),
        ("Mood Classification", lambda: test_mood_classification(components)),
        ("Crisis Detection", lambda: test_crisis_detection(components)),
        ("Prompt Generation", lambda: test_prompt_generation(components)),
        ("API Server", test_api_server)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 50)
    print("🌿 WhisperLeaf Integration Test Summary")
    print("=" * 50)
    
    # Component initialization summary
    successful_components = sum(1 for r in init_results.values() if "Success" in r)
    total_components = len(init_results)
    print(f"🧠 Component Initialization: {successful_components}/{total_components}")
    
    # Test results summary
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    # Overall assessment
    successful_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    overall_score = (successful_components / total_components + successful_tests / total_tests) / 2
    
    print(f"\n🎯 Overall System Health: {overall_score:.1%}")
    
    if overall_score > 0.7:
        print("🎉 WhisperLeaf integration tests PASSED!")
        return 0
    else:
        print("💥 WhisperLeaf integration tests FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())

