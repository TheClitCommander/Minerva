#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for debugging Minerva chat responses
This bypasses the web interface and makes direct API calls to test the chat functionality
"""

import sys
import os
import json
import requests
import uuid
from datetime import datetime
import argparse

def test_chat_api(message, api_url="http://localhost:9876/api/chat/message", debug=False):
    """Test the chat API endpoint directly"""
    
    print(f"Testing chat API with message: '{message}'")
    print(f"Sending request to: {api_url}")
    
    # Generate a unique message ID
    message_id = str(uuid.uuid4())
    
    # Prepare the payload for a standard chat message
    payload = {
        "message": message,
        "message_id": message_id,
        "mode": "standard",  # Could be 'standard' or 'think_tank'
        "show_debug": debug,
        "bypass_validation": True  # Important for testing
    }
    
    if debug:
        print("Request payload:")
        print(json.dumps(payload, indent=2))
    
    # Make the API request
    try:
        response = requests.post(api_url, json=payload)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if debug:
                print("\nFull API Response:")
                print("="*80)
                print(json.dumps(data, indent=2))
                print("="*80)
            
            # Print the actual response text
            if "response" in data:
                print("\nResponse Text:")
                print("-"*80)
                print(data["response"])
                print("-"*80)
            else:
                print("\nNo response text found in the API response")
                
            # Check for any errors
            if "error" in data:
                print(f"\nError: {data['error']}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_direct_api(message, api_url="http://localhost:9876/api/direct", debug=False):
    """Test the direct API endpoint"""
    
    print(f"Testing direct API with message: '{message}'")
    print(f"Sending request to: {api_url}")
    
    # Prepare the payload
    payload = {
        "message": message,
        "bypass_validation": True,
        "use_process_function": True,
        "max_tokens": 500,
        "temperature": 0.7,
        "model_type": "basic"
    }
    
    if debug:
        print("Request payload:")
        print(json.dumps(payload, indent=2))
    
    # Make the API request
    try:
        response = requests.post(api_url, json=payload)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if debug:
                print("\nFull API Response:")
                print("="*80)
                print(json.dumps(data, indent=2))
                print("="*80)
            
            # Print the actual response text
            if "response" in data:
                print("\nResponse Text:")
                print("-"*80)
                print(data["response"])
                print("-"*80)
            else:
                print("\nNo response text found in the API response")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_think_tank(message, api_url="http://localhost:9876/api/chat/message", debug=False):
    """Test the think tank mode specifically"""
    
    print(f"Testing think tank mode with message: '{message}'")
    print(f"Sending request to: {api_url}")
    
    # Generate a unique message ID
    message_id = str(uuid.uuid4())
    
    # Prepare the payload specifically for think tank mode
    payload = {
        "message": message,
        "message_id": message_id,
        "mode": "think_tank",  # Important: set to think_tank mode
        "show_debug": debug,
        "bypass_validation": True  # Important for testing
    }
    
    if debug:
        print("Request payload:")
        print(json.dumps(payload, indent=2))
    
    # Make the API request
    try:
        response = requests.post(api_url, json=payload)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if debug:
                print("\nFull API Response:")
                print("="*80)
                print(json.dumps(data, indent=2))
                print("="*80)
            
            # Print the actual response text
            if "response" in data:
                print("\nResponse Text:")
                print("-"*80)
                print(data["response"])
                print("-"*80)
            else:
                print("\nNo response text found in the API response")
                
            # Check for any errors
            if "error" in data:
                print(f"\nError: {data['error']}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Parse command line arguments and run tests"""
    parser = argparse.ArgumentParser(description="Test Minerva's API endpoints")
    parser.add_argument("message", help="Message to send")
    parser.add_argument("--port", type=int, default=9876, help="Port number (default: 9876)")
    parser.add_argument("--mode", choices=["chat", "direct", "think_tank"], default="direct", 
                       help="Which API mode to test (default: direct)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    
    args = parser.parse_args()
    
    # Construct the API URL
    base_url = f"http://localhost:{args.port}"
    
    if args.mode == "chat":
        api_url = f"{base_url}/api/chat/message"
        test_chat_api(args.message, api_url, args.debug)
    elif args.mode == "direct":
        api_url = f"{base_url}/api/direct"
        test_direct_api(args.message, api_url, args.debug)
    elif args.mode == "think_tank":
        api_url = f"{base_url}/api/chat/message"
        test_think_tank(args.message, api_url, args.debug)

if __name__ == "__main__":
    main()
