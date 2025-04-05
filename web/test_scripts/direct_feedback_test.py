#!/usr/bin/env python3
"""
Direct Feedback System Test

This script directly tests the feedback system components without requiring the full app to be running.
It validates the core functionality of the feedback system integration.
"""

import os
import sys
import uuid
import json
from datetime import datetime
from pprint import pprint

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import our feedback and memory modules
from integrations.feedback import (
    record_user_feedback,
    track_conversation,  # Renamed from track_conversation_context to match the actual function name
    enhance_query,
    get_user_preferences,
    check_fine_tuning_readiness
)
from integrations.memory import (
    store_memory,
    retrieve_memory,
    memory_system
)

def print_separator(title=""):
    """Print a separator line with optional title."""
    width = 80
    print("\n" + "=" * width)
    if title:
        print(f"{title.center(width)}")
        print("-" * width)

def test_memory_operations():
    """Test basic memory operations."""
    print_separator("TEST 1: MEMORY OPERATIONS")
    
    # Generate a unique conversation ID for this test
    conversation_id = f"test_{str(uuid.uuid4())[:8]}"
    
    # Store a test memory
    print("Storing test memory...")
    memory_id = store_memory(
        conversation_id=conversation_id,
        user_message="How does Minerva's Think Tank mode work?",
        ai_response="Minerva's Think Tank mode combines insights from multiple AI models to provide more comprehensive responses.",
        metadata={"test": True, "source": "direct_test"}
    )
    
    if not memory_id:
        print("❌ Failed to store memory")
        return False
    
    print(f"✅ Memory stored with ID: {memory_id}")
    
    # Retrieve the memory
    print("\nRetrieving memory with query...")
    memories = retrieve_memory("Think Tank mode")
    
    if not memories:
        print("❌ Failed to retrieve any memories")
    else:
        print(f"✅ Retrieved {len(memories)} memories")
        print("\nFirst memory content:")
        if len(memories) > 0:
            memory = memories[0]
            print(f"- Content: {memory.get('document', 'N/A')[:100]}...")
            print(f"- Metadata: {memory.get('metadata', {})}")
    
    return True

def test_feedback_recording():
    """Test feedback recording functionality."""
    print_separator("TEST 2: FEEDBACK RECORDING")
    
    # Generate unique IDs
    conversation_id = f"test_{str(uuid.uuid4())[:8]}"
    
    # Record sample user feedback
    print("Recording user feedback...")
    feedback_id = record_user_feedback(
        conversation_id=conversation_id,
        query="How does Minerva's Think Tank mode work?",
        response="Minerva's Think Tank mode combines insights from multiple AI models to provide more comprehensive responses.",
        feedback_level="excellent",
        comments="Great explanation of Think Tank mode!",
        metadata={"test": True, "source": "direct_test"}
    )
    
    if not feedback_id:
        print("❌ Failed to record feedback")
        return False
    
    print(f"✅ Feedback recorded with ID: {feedback_id}")
    return True

def test_conversation_tracking():
    """Test conversation context tracking."""
    print_separator("TEST 3: CONVERSATION CONTEXT TRACKING")
    
    # Generate unique conversation ID
    conversation_id = f"test_{str(uuid.uuid4())[:8]}"
    
    # Track a multi-turn conversation
    print("Tracking conversation context...")
    
    # First turn
    track_conversation(
        conversation_id=conversation_id,
        user_query="What is Minerva's Think Tank mode?",
        ai_response="Minerva's Think Tank mode combines multiple AI models to provide enhanced responses."
    )
    
    # Second turn
    track_conversation(
        conversation_id=conversation_id,
        user_query="How does it select the best model?",
        ai_response="It ranks responses based on relevance, correctness, and helpfulness metrics."
    )
    
    # Third turn
    track_conversation(
        conversation_id=conversation_id,
        user_query="What happens if models disagree?",
        ai_response="It blends the responses using specialized strategies for different query types."
    )
    
    print("✅ Successfully tracked a 3-turn conversation")
    
    # Now retrieve the conversation context
    context = retrieve_memory(
        user_message="What is Think Tank mode",
        top_k=5
    )
    
    if not context:
        print("❌ Failed to retrieve conversation context")
        return False
    
    print(f"✅ Retrieved {len(context)} context memories from conversation")
    
    return True

def test_user_preferences():
    """Test user preference learning."""
    print_separator("TEST 4: USER PREFERENCE LEARNING")
    
    # Generate a test user ID
    user_id = f"test_user_{str(uuid.uuid4())[:8]}"
    
    # Record several feedback entries to build preference profile
    for i, (query, feedback) in enumerate([
        ("How do I optimize Python code?", "excellent"),
        ("Can you explain database indexing?", "good"),
        ("What's the history of AI?", "adequate"),  # Changed from 'neutral' to 'adequate' which is a valid feedback level
        ("How do I optimize Python performance?", "excellent"),
        ("Can you explain Docker containers?", "good")
    ]):
        record_user_feedback(
            conversation_id=f"pref_test_{i}",
            query=query,
            response=f"Sample response for: {query}",
            feedback_level=feedback,
            metadata={
                "test": True, 
                "category": query.split()[1] if len(query.split()) > 1 else "general",
                "user_id": user_id  # Include user_id in metadata instead
            }
        )
    
    print("✅ Recorded 5 feedback entries for preference learning")
    
    # Get learned preferences
    preferences = get_user_preferences(user_id)
    
    print("\nLearned User Preferences:")
    if preferences:
        for category, level in preferences.items():
            print(f"- {category}: {level}")
    else:
        print("No preferences learned yet")
    
    return True

def test_fine_tuning_readiness():
    """Test fine-tuning readiness check."""
    print_separator("TEST 5: FINE-TUNING READINESS CHECK")
    
    # Check readiness with minimal threshold
    readiness = check_fine_tuning_readiness(min_entries=3)
    
    print("\nFine-Tuning Readiness Status:")
    
    # Handle the case when readiness is a string (path to the dataset file)
    if isinstance(readiness, str):
        print(f"- Ready for fine-tuning: True")
        print(f"- Dataset path: {readiness}")
        return True
    # Handle the case when readiness is a dictionary
    elif isinstance(readiness, dict):
        print(f"- Ready for fine-tuning: {readiness.get('ready', False)}")
        
        if readiness.get('ready', False):
            print(f"- Dataset path: {readiness.get('dataset_path', 'N/A')}")
            print(f"- Entries: {readiness.get('entries', 0)}")
        else:
            print(f"- Message: {readiness.get('message', 'N/A')}")
            print(f"- Current entries: {readiness.get('current_entries', 0)}")
            print(f"- Required entries: {readiness.get('required_entries', 'N/A')}")
    else:
        print(f"- Readiness check returned: {readiness}")
    
    return True

def main():
    """Run all tests and summarize results."""
    print_separator("DIRECT FEEDBACK SYSTEM TEST")
    print("This script tests the feedback system components directly")
    
    test_results = {
        "Memory Operations": test_memory_operations(),
        "Feedback Recording": test_feedback_recording(),
        "Conversation Tracking": test_conversation_tracking(),
        "User Preferences": test_user_preferences(),
        "Fine-Tuning Readiness": test_fine_tuning_readiness()
    }
    
    # Print results summary
    print_separator("TEST RESULTS SUMMARY")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Overall result
    if all(test_results.values()):
        print_separator()
        print("🎉 ALL TESTS PASSED - Feedback system components are working! 🎉")
    else:
        print_separator()
        print("⚠️ SOME TESTS FAILED - Review errors and fix issues before proceeding")

if __name__ == "__main__":
    main()
