#!/usr/bin/env python3
"""
Debugging script to test mode parameter extraction in WebSocket messages.
"""

import sys
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_mode")

def simulate_mode_extraction(message_json):
    """Simulate how the server extracts the mode parameter"""
    try:
        # Parse the message data
        data = json.loads(message_json)
        print(f"Original message data: {data}")
        
        # Extract mode with the original logic
        mode = data.get('mode', '')
        print(f"Mode extracted (original logic): '{mode}'")
        
        # Extract mode with the enhanced logic
        enhanced_mode = mode
        if not enhanced_mode and isinstance(data, dict):
            if 'parameters' in data and isinstance(data['parameters'], dict):
                enhanced_mode = data['parameters'].get('mode', '')
            elif 'options' in data and isinstance(data['options'], dict):
                enhanced_mode = data['options'].get('mode', '')
            elif 'data' in data and isinstance(data['data'], dict):
                enhanced_mode = data['data'].get('mode', '')
        
        print(f"Mode extracted (enhanced logic): '{enhanced_mode}'")
        
        # Check if mode would be recognized for Think Tank
        is_think_tank = enhanced_mode == 'think_tank'
        print(f"Would be recognized as Think Tank mode: {is_think_tank}")
        
        return enhanced_mode
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

def test_message_formats():
    """Test various message formats to ensure mode is extracted correctly"""
    test_messages = [
        # Standard format
        '{"message": "Hello", "mode": "think_tank", "test_mode": true}',
        
        # Mode in parameters
        '{"message": "Hello", "parameters": {"mode": "think_tank"}, "test_mode": true}',
        
        # Mode in options
        '{"message": "Hello", "options": {"mode": "think_tank"}, "test_mode": true}',
        
        # Mode in data
        '{"message": "Hello", "data": {"mode": "think_tank"}, "test_mode": true}',
        
        # No mode specified
        '{"message": "Hello", "test_mode": true}',
        
        # Format from the WebSocket client
        '["chat_message",{"message":"What is quantum computing?","mode":"think_tank","test_mode":true,"include_model_info":true}]'
    ]
    
    print("===== TESTING MODE EXTRACTION WITH VARIOUS MESSAGE FORMATS =====")
    for i, msg in enumerate(test_messages):
        print(f"\n----- Test Case {i+1} -----")
        
        # Handle Socket.IO format (array with event name and data)
        try:
            parsed = json.loads(msg)
            if isinstance(parsed, list) and len(parsed) >= 2 and parsed[0] == "chat_message":
                print(f"Detected Socket.IO message format with event: {parsed[0]}")
                data = parsed[1]
                print(f"Extracted data part: {data}")
                # Convert back to JSON string for the extractor
                msg = json.dumps(data)
        except:
            pass
            
        mode = simulate_mode_extraction(msg)
        print(f"Final result: {mode}")
    
    print("\n===== TESTING COMPLETE =====")

if __name__ == "__main__":
    test_message_formats()
