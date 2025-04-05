#!/usr/bin/env python3
"""
Simple test script for the Minerva Think Tank API
This script uses only standard library modules to test the real processor integration
"""

import urllib.request
import urllib.parse
import json
import time
import sys

API_URL = "http://localhost:8888/api/think-tank"

def test_think_tank_api(message):
    """Test the Think Tank API with a specific message"""
    print(f"\n===== Testing Think Tank API with message: =====")
    print(f"\"{message[:50]}...\"")
    
    headers = {
        "Content-Type": "application/json",
        "X-Test-Mode": "true",  # Enable test mode for more diagnostic info
    }
    
    payload = json.dumps({"message": message}).encode('utf-8')
    
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers=headers,
        method="POST"
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            processing_time = time.time() - start_time
            response_data = response.read().decode('utf-8')
            status_code = response.status
            
            print(f"\nAPI Response (took {processing_time:.2f}s):")
            print(f"Status code: {status_code}")
            
            if status_code == 200:
                try:
                    data = json.loads(response_data)
                    
                    # Print response summary
                    print("\n--- Response Summary ---")
                    print(f"Status: {data.get('status', 'unknown')}")
                    
                    # Check if we got a model info section
                    model_info = data.get('model_info', {})
                    if model_info:
                        primary_model = model_info.get('primary_model', 'unknown')
                        models_used = model_info.get('models_used', [])
                        model_count = len(models_used)
                        print(f"Primary model: {primary_model}")
                        print(f"Models used: {model_count}")
                        
                        # List the models used
                        if models_used:
                            print("\nModels:")
                            for model in models_used:
                                print(f"- {model.get('name', 'unknown')}: {model.get('contribution', 0)}%")
                        
                        # Check for model rankings
                        if 'rankings' in model_info:
                            print("\n--- Model Rankings ---")
                            for i, ranking in enumerate(model_info['rankings'][:3]):  # Show top 3
                                print(f"{i+1}. {ranking['model']} (Score: {ranking.get('score', 0):.2f})")
                                print(f"   Reason: {ranking.get('reason', 'No reason provided')}")
                        
                        # Check for blending info
                        if 'blending_strategy' in model_info:
                            print(f"\nBlending strategy: {model_info['blending_strategy']}")
                            if 'blending_info' in model_info:
                                print(f"Strategy name: {model_info['blending_info'].get('strategy_name', 'unknown')}")
                                print(f"Blending quality: {model_info['blending_info'].get('quality', 0.0):.2f}")
                        
                        # Check for query analysis
                        if 'query_analysis' in model_info:
                            print("\n--- Query Analysis ---")
                            qa = model_info['query_analysis']
                            print(f"Type: {qa.get('type', 'unknown')}")
                            print(f"Complexity: {qa.get('complexity', 'unknown')}")
                            print(f"Confidence: {qa.get('confidence', 0.0):.2f}")
                        
                    # Print first few lines of the response
                    print("\n--- Response First Lines ---")
                    response_lines = data.get('response', '').split('\n')
                    for line in response_lines[:3]:
                        print(line)
                    print("...")
                    
                    # Check for errors
                    if 'error' in model_info:
                        print("\n--- ERROR ---")
                        print(model_info['error'])
                        if 'error_details' in model_info:
                            print("Error details available in full response")
                    
                    # Save the full response to a file for inspection
                    with open(f"test_response_{int(time.time())}.json", "w") as f:
                        json.dump(data, f, indent=2)
                        print(f"\nFull response saved to {f.name}")
                        
                except Exception as e:
                    print(f"Error parsing response: {e}")
                    print(f"Raw response: {response_data[:200]}...")
            else:
                print(f"Error: {response_data}")
    except urllib.error.URLError as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    # Get message from command line arguments or use a default message
    test_message = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Explain quantum computing in simple terms"
    test_think_tank_api(test_message)
