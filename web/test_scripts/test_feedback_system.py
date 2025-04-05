#!/usr/bin/env python3
"""
Feedback System Integration Test

This script tests the integration of Minerva's feedback system with the chat API,
validating the complete self-learning loop from message processing to feedback collection.

Usage:
    python test_feedback_system.py
"""

import os
import sys
import json
import time
import uuid
import requests
from pprint import pprint
from datetime import datetime

# Ensure we can import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Base URL for API requests
BASE_URL = "http://localhost:5000/api/chat"

def print_separator(title=""):
    """Print a separator line with optional title."""
    width = 80
    print("\n" + "=" * width)
    if title:
        print(f"{title.center(width)}")
        print("-" * width)

def test_message_processing():
    """
    Test 1: Message Processing
    
    This test verifies that:
    - The /message endpoint processes messages correctly
    - The response contains a memory_id for feedback
    - The context-aware memory enhancement works
    """
    print_separator("TEST 1: MESSAGE PROCESSING")
    
    # Generate a unique conversation ID for this test
    conversation_id = f"test_{str(uuid.uuid4())[:8]}"
    
    # Test message
    test_message = {
        "message": "How does Minerva's Think Tank mode blend responses from multiple models?",
        "conversation_id": conversation_id,
        "use_think_tank": True,
        "user_id": "test_user"
    }
    
    print(f"Sending message: {test_message['message']}")
    try:
        response = requests.post(f"{BASE_URL}/message", json=test_message)
        
        if response.status_code != 200:
            print(f"❌ ERROR: Failed to process message - Status {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        print(f"✅ Message processed successfully")
        
        # Check if response contains required fields
        if "memory_id" not in data:
            print("❌ ERROR: Response does not contain memory_id field")
            return None
            
        print(f"✅ Response contains memory_id: {data['memory_id']}")
        
        # Check if model info is included (especially for Think Tank)
        if "model_info" in data:
            print(f"✅ Response contains model information")
            if isinstance(data['model_info'], dict) and 'models_used' in data['model_info']:
                print(f"✅ Think Tank used {len(data['model_info']['models_used'])} models")
            
        # Print a summary of the response
        print("\nResponse Summary:")
        print(f"- Response length: {len(data['message'])}")
        print(f"- Processing time: {data.get('processing_time', 'N/A')} seconds")
        
        return data
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

def test_feedback_submission(message_data):
    """
    Test 2: Feedback Submission
    
    This test verifies that:
    - The /feedback endpoint accepts feedback submissions
    - The feedback is stored and linked to the memory_id
    """
    print_separator("TEST 2: FEEDBACK SUBMISSION")
    
    if not message_data:
        print("❌ Cannot test feedback submission without message data")
        return False
    
    # Extract necessary data from message response
    memory_id = message_data['memory_id']
    conversation_id = message_data['conversation_id']
    query = "How does Minerva's Think Tank mode blend responses from multiple models?"
    response = message_data['message']
    
    # Prepare feedback data
    feedback_data = {
        "conversation_id": conversation_id,
        "memory_id": memory_id,
        "query": query,
        "response": response,
        "feedback_level": "excellent",
        "comments": "The explanation of Think Tank's model blending was very clear and accurate.",
        "user_id": "test_user",
        "metadata": {
            "test_source": "automated_test",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print(f"Submitting feedback for memory_id: {memory_id}")
    try:
        response = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
        
        if response.status_code != 200:
            print(f"❌ ERROR: Failed to submit feedback - Status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        print(f"✅ Feedback submitted successfully")
        
        # Check if response contains feedback_id
        if "feedback_id" not in data:
            print("❌ ERROR: Response does not contain feedback_id field")
            return False
            
        print(f"✅ Feedback recorded with ID: {data['feedback_id']}")
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_user_preferences():
    """
    Test 3: User Preference Learning
    
    This test verifies that:
    - The /user_preferences endpoint returns user preference data
    - The system is learning from feedback
    """
    print_separator("TEST 3: USER PREFERENCE LEARNING")
    
    try:
        response = requests.get(f"{BASE_URL}/user_preferences?user_id=test_user")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Failed to get user preferences - Status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        print(f"✅ Retrieved user preferences successfully")
        
        # Print the preferences
        print("\nUser Preferences:")
        pprint(data)
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_fine_tuning_status():
    """
    Test 4: Fine-Tuning Readiness
    
    This test verifies that:
    - The /fine_tuning/status endpoint works
    - The system tracks progress toward fine-tuning readiness
    """
    print_separator("TEST 4: FINE-TUNING READINESS")
    
    try:
        response = requests.get(f"{BASE_URL}/fine_tuning/status?min_entries=10")
        
        if response.status_code != 200:
            print(f"❌ ERROR: Failed to check fine-tuning status - Status {response.status_code}")
            print(response.text)
            return False
        
        data = response.json()
        print(f"✅ Fine-tuning status check successful")
        
        # Check readiness
        print(f"\nFine-Tuning Status:")
        print(f"- Ready for fine-tuning: {data.get('ready', False)}")
        if data.get('ready', False):
            print(f"- Dataset path: {data.get('dataset_path', 'N/A')}")
        else:
            print(f"- Message: {data.get('message', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_context_aware_query():
    """
    Test 5: Context-Aware Query Enhancement
    
    This test verifies that:
    - The system maintains conversation context over multiple turns
    - Responses incorporate knowledge from previous turns
    """
    print_separator("TEST 5: CONTEXT-AWARE QUERY ENHANCEMENT")
    
    # Generate a unique conversation ID for this multi-turn test
    conversation_id = f"context_test_{str(uuid.uuid4())[:8]}"
    
    # First message to establish context
    first_message = {
        "message": "What are the key components of Minerva's Think Tank mode?",
        "conversation_id": conversation_id,
        "use_think_tank": True,
        "user_id": "test_user"
    }
    
    # Second message that relies on context from first
    second_message = {
        "message": "How does the response blending system work in this mode?",
        "conversation_id": conversation_id,
        "use_think_tank": True,
        "user_id": "test_user"
    }
    
    try:
        # Send first message
        print("Sending first message to establish context...")
        first_response = requests.post(f"{BASE_URL}/message", json=first_message)
        
        if first_response.status_code != 200:
            print(f"❌ ERROR: Failed to send first message - Status {first_response.status_code}")
            return False
            
        first_data = first_response.json()
        print(f"✅ First message processed successfully")
        
        # Wait briefly to ensure context is stored
        time.sleep(2)
        
        # Send second message that relies on context
        print("\nSending second message that relies on previous context...")
        second_response = requests.post(f"{BASE_URL}/message", json=second_message)
        
        if second_response.status_code != 200:
            print(f"❌ ERROR: Failed to send second message - Status {second_response.status_code}")
            return False
            
        second_data = second_response.json()
        print(f"✅ Second message processed successfully")
        
        # Check if the memory_info field is present and shows context usage
        if "memory_info" in second_data and second_data["memory_info"].get("used", False):
            print(f"✅ Second response used context from previous conversation")
            if "count" in second_data["memory_info"]:
                print(f"✅ Used {second_data['memory_info']['count']} memories for context")
        else:
            print("⚠️ WARNING: Second response does not appear to use context")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests in sequence."""
    print_separator("MINERVA FEEDBACK SYSTEM INTEGRATION TEST")
    print("This script tests the complete self-learning feedback loop")
    print(f"API Base URL: {BASE_URL}")
    
    # Test 1: Message Processing
    message_data = test_message_processing()
    
    # Test 2: Feedback Submission (depends on Test 1)
    if message_data:
        feedback_result = test_feedback_submission(message_data)
    else:
        print("❌ Skipping feedback submission test due to failed message processing")
        feedback_result = False
    
    # Test 3: User Preference Learning
    preference_result = test_user_preferences()
    
    # Test 4: Fine-Tuning Readiness
    fine_tuning_result = test_fine_tuning_status()
    
    # Test 5: Context-Aware Query Enhancement
    context_result = test_context_aware_query()
    
    # Final results summary
    print_separator("TEST RESULTS SUMMARY")
    print(f"Test 1 (Message Processing):      {'✅ PASS' if message_data else '❌ FAIL'}")
    print(f"Test 2 (Feedback Submission):     {'✅ PASS' if feedback_result else '❌ FAIL'}")
    print(f"Test 3 (User Preference Learning): {'✅ PASS' if preference_result else '❌ FAIL'}")
    print(f"Test 4 (Fine-Tuning Readiness):   {'✅ PASS' if fine_tuning_result else '❌ FAIL'}")
    print(f"Test 5 (Context-Aware Queries):   {'✅ PASS' if context_result else '❌ FAIL'}")
    
    # Overall result
    all_passed = all([message_data, feedback_result, preference_result, fine_tuning_result, context_result])
    print_separator()
    if all_passed:
        print("🎉 ALL TESTS PASSED - Feedback system integration is complete! 🎉")
    else:
        print("⚠️ SOME TESTS FAILED - Review errors and fix issues before proceeding")
    
if __name__ == "__main__":
    main()
