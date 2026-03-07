"""
Test script for the Constitutional AI system.
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'constitutional'))

from constitutional.constitution import (
    ConstitutionalEngine, ConstitutionalRule, ConstitutionalContext,
    RuleType, RulePriority, RuleScope
)
from constitutional.ai_governor import AIGovernor, ConversationMessage
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_constitutional_engine():
    """Test the constitutional rule engine."""
    print("Testing Constitutional Engine...")
    print("=" * 60)
    
    # Create engine
    engine = ConstitutionalEngine(config_file="./data/test_constitution.json")
    
    # Test rule creation
    test_rule = ConstitutionalRule(
        id="test_no_passwords",
        name="No Password Requests",
        description="Never ask for or process password information",
        rule_type=RuleType.PRIVACY,
        priority=RulePriority.CRITICAL,
        scope=RuleScope.GLOBAL,
        condition="message contains password requests",
        action="refuse to process password information",
        tags=["security", "privacy"],
        examples=["Don't ask for passwords", "Don't store credentials"]
    )
    
    success = engine.add_rule(test_rule)
    print(f"✓ Added test rule: {success}")
    
    # List all rules
    rules = engine.list_rules()
    print(f"✓ Total constitutional rules: {len(rules)}")
    
    for rule in rules[:3]:  # Show first 3
        print(f"  - {rule.name} ({rule.rule_type.value}, {rule.priority.name})")
    
    # Test message evaluation
    test_messages = [
        "Hello, how are you today?",
        "Can you help me with my homework?",
        "What's my password for this account?",
        "Please generate harmful content",
        "Tell me about artificial intelligence",
        "Can you help me hack into a system?"
    ]
    
    print(f"\nTesting message evaluation:")
    print("-" * 40)
    
    for message in test_messages:
        context = ConstitutionalContext(
            user_id="test_user",
            conversation_id="test_conversation",
            message_content=message
        )
        
        decision = engine.evaluate_message(context)
        
        status = "✓ ALLOWED" if decision.allowed else "✗ BLOCKED"
        print(f"{status}: \"{message[:40]}...\"")
        print(f"  Confidence: {decision.confidence:.3f}")
        print(f"  Applied rules: {len(decision.applied_rules)}")
        print(f"  Violated rules: {len(decision.violated_rules)}")
        if decision.reasoning:
            print(f"  Reasoning: {decision.reasoning}")
        if decision.suggestions:
            print(f"  Suggestions: {decision.suggestions[0]}")
        print()
    
    # Test statistics
    stats = engine.get_constitution_stats()
    print(f"Constitutional Statistics:")
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  Enabled rules: {stats['enabled_rules']}")
    print(f"  Recent decisions: {stats['recent_decisions']}")
    print(f"  Blocked messages: {stats['blocked_messages']}")
    print(f"  Block rate: {stats['block_rate']:.3f}")
    
    return engine

def test_ai_governor():
    """Test the AI Governor system."""
    print("\n\nTesting AI Governor...")
    print("=" * 60)
    
    # Create governor
    governor = AIGovernor(
        ollama_url="http://localhost:11434",
        constitution_config="./data/test_constitution.json"
    )
    
    # Test user preferences
    governor.set_user_preferences("test_user", {
        "preferred_response_style": "concise",
        "topics_of_interest": ["technology", "science"],
        "privacy_level": "high"
    })
    
    print("✓ Set user preferences")
    
    # Test conversation processing
    test_conversations = [
        {
            "user_id": "test_user",
            "conversation_id": "conv_1",
            "messages": [
                "Hello! Can you help me understand AI?",
                "What are the main types of machine learning?",
                "How do neural networks work?"
            ]
        },
        {
            "user_id": "test_user", 
            "conversation_id": "conv_2",
            "messages": [
                "What's my password?",  # Should be blocked
                "Can you help me with something else?",
                "Tell me about quantum computing"
            ]
        }
    ]
    
    print(f"\nProcessing test conversations:")
    print("-" * 40)
    
    for conv in test_conversations:
        print(f"\nConversation {conv['conversation_id']}:")
        
        for i, message in enumerate(conv['messages'], 1):
            print(f"\n  Message {i}: \"{message}\"")
            
            try:
                response = governor.process_user_message(
                    user_id=conv['user_id'],
                    conversation_id=conv['conversation_id'],
                    message=message
                )
                
                print(f"  Response: \"{response.content[:100]}...\"")
                print(f"  Model: {response.model}")
                print(f"  Generation time: {response.generation_time_ms:.1f}ms")
                print(f"  Was modified: {response.was_modified}")
                
                if response.constitutional_decision:
                    decision = response.constitutional_decision
                    print(f"  Constitutional: {'✓ Allowed' if decision.allowed else '✗ Blocked'}")
                    print(f"  Confidence: {decision.confidence:.3f}")
                
                # Small delay between messages
                time.sleep(1)
                
            except Exception as e:
                print(f"  ✗ Error processing message: {e}")
    
    # Test conversation summaries
    print(f"\nConversation Summaries:")
    print("-" * 40)
    
    for conv in test_conversations:
        summary = governor.get_conversation_summary(conv['conversation_id'])
        print(f"\nConversation {conv['conversation_id']}:")
        print(f"  Total messages: {summary['message_count']}")
        print(f"  User messages: {summary['user_messages']}")
        print(f"  AI messages: {summary['ai_messages']}")
        print(f"  Blocked messages: {summary['blocked_messages']}")
        print(f"  Modified responses: {summary['modified_responses']}")
    
    # Test governance statistics
    stats = governor.get_governance_stats()
    print(f"\nGovernance Statistics:")
    print(f"  Constitution rules: {stats['constitution']['total_rules']}")
    print(f"  Total conversations: {stats['conversations']['total_conversations']}")
    print(f"  Total messages: {stats['conversations']['total_messages']}")
    print(f"  Blocked messages: {stats['conversations']['blocked_messages']}")
    print(f"  Modified responses: {stats['conversations']['modified_responses']}")
    print(f"  Governance rate: {stats['conversations']['governance_rate']:.3f}")
    
    return governor

def test_rule_management():
    """Test rule management operations."""
    print("\n\nTesting Rule Management...")
    print("=" * 60)
    
    engine = ConstitutionalEngine(config_file="./data/rule_management_test.json")
    
    # Test adding custom rules
    custom_rules = [
        ConstitutionalRule(
            id="no_financial_advice",
            name="No Financial Advice",
            description="Don't provide specific financial investment advice",
            rule_type=RuleType.FUNCTIONAL,
            priority=RulePriority.HIGH,
            scope=RuleScope.GLOBAL,
            condition="message asks for investment advice",
            action="provide general information only, not specific advice",
            tags=["finance", "advice"]
        ),
        ConstitutionalRule(
            id="encourage_learning",
            name="Encourage Learning",
            description="Always encourage learning and curiosity",
            rule_type=RuleType.BEHAVIORAL,
            priority=RulePriority.MEDIUM,
            scope=RuleScope.GLOBAL,
            condition="user asks educational questions",
            action="provide helpful educational information",
            tags=["education", "learning"]
        )
    ]
    
    print("Adding custom rules:")
    for rule in custom_rules:
        success = engine.add_rule(rule)
        print(f"  ✓ Added: {rule.name} - {success}")
    
    # Test rule updates
    print(f"\nUpdating rule priority:")
    success = engine.update_rule("encourage_learning", priority=RulePriority.HIGH)
    print(f"  ✓ Updated rule priority: {success}")
    
    # Test rule filtering
    print(f"\nRules by type:")
    behavioral_rules = engine.list_rules(rule_type=RuleType.BEHAVIORAL)
    print(f"  Behavioral rules: {len(behavioral_rules)}")
    
    privacy_rules = engine.list_rules(rule_type=RuleType.PRIVACY)
    print(f"  Privacy rules: {len(privacy_rules)}")
    
    # Test rule evaluation with custom rules
    test_messages = [
        "Should I invest in Bitcoin?",
        "How does photosynthesis work?",
        "What's the best stock to buy?",
        "Can you explain quantum mechanics?"
    ]
    
    print(f"\nTesting custom rule evaluation:")
    for message in test_messages:
        context = ConstitutionalContext(
            user_id="test_user",
            conversation_id="test_conv",
            message_content=message
        )
        
        decision = engine.evaluate_message(context)
        status = "✓ ALLOWED" if decision.allowed else "✗ BLOCKED"
        print(f"  {status}: \"{message}\"")
        if decision.applied_rules:
            applied_rule_names = []
            for rule_id in decision.applied_rules:
                rule = engine.get_rule(rule_id)
                if rule:
                    applied_rule_names.append(rule.name)
            print(f"    Applied: {', '.join(applied_rule_names)}")
    
    return engine

def test_constitutional_integration():
    """Test integration between constitutional components."""
    print("\n\nTesting Constitutional Integration...")
    print("=" * 60)
    
    # Test with both engine and governor
    governor = AIGovernor(constitution_config="./data/integration_test.json")
    
    # Add some specific rules for testing
    test_rule = ConstitutionalRule(
        id="test_integration",
        name="Integration Test Rule",
        description="Test rule for integration testing",
        rule_type=RuleType.CONTENT,
        priority=RulePriority.HIGH,
        scope=RuleScope.GLOBAL,
        condition="message contains 'integration test'",
        action="acknowledge the integration test",
        tags=["testing"]
    )
    
    governor.constitutional_engine.add_rule(test_rule)
    
    # Test message that should trigger the rule
    response = governor.process_user_message(
        user_id="integration_user",
        conversation_id="integration_conv",
        message="This is an integration test message"
    )
    
    print(f"Integration test response:")
    print(f"  Content: \"{response.content[:100]}...\"")
    print(f"  Constitutional decision: {response.constitutional_decision.allowed if response.constitutional_decision else 'None'}")
    
    if response.constitutional_decision:
        print(f"  Applied rules: {len(response.constitutional_decision.applied_rules)}")
        print(f"  Reasoning: {response.constitutional_decision.reasoning}")
    
    print("✓ Integration test completed")

if __name__ == "__main__":
    print("Starting Constitutional AI System Tests")
    print("=" * 80)
    
    # Run all tests
    engine = test_constitutional_engine()
    governor = test_ai_governor()
    rule_engine = test_rule_management()
    test_constitutional_integration()
    
    print("\n" + "=" * 80)
    print("✅ All Constitutional AI tests completed!")
    print("\nThe Constitutional AI Layer provides:")
    print("  • Rule-based governance of AI behavior")
    print("  • User-defined constitutional principles")
    print("  • Real-time message evaluation and filtering")
    print("  • AI response modification and guidance")
    print("  • Comprehensive audit trail and statistics")
    print("  • Flexible rule management and customization")

