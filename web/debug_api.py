#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced debug tool for direct API testing
"""

import sys
import os
import json
import time
import requests
from pprint import pprint

def test_direct_api(message, 
                    host="localhost", 
                    port=9876, 
                    max_tokens=500, 
                    temperature=0.7, 
                    bypass_validation=True, 
                    use_process_function=True,
                    model_type="basic",
                    timeout=30):
    """Test the direct API with various configuration options
    
    Args:
        message: Message to send to the API
        host: Hostname of the server
        port: Port number
        max_tokens: Maximum number of tokens to generate
        temperature: Temperature for generation
        bypass_validation: Whether to bypass validation
        use_process_function: Whether to use the process function
        model_type: Type of model to use
        timeout: Request timeout in seconds
    """
    
    url = f"http://{host}:{port}/api/direct"
    print(f"Sending request to: {url}")
    
    # Prepare payload with debugging options
    payload = {
        "message": message,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "bypass_validation": bypass_validation,
        "use_process_function": use_process_function,
        "model_type": model_type
    }
    
    print(f"Request payload:")
    pprint(payload)
    
    # Make the request
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=timeout)
        request_time = time.time() - start_time
        
        print(f"Request completed in {request_time:.2f}s")
        print(f"Status code: {response.status_code}")
        
        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            
            print("\nAPI Response:")
            print("=" * 80)
            pprint(response_data)
            print("=" * 80)
            
            if response_data.get('success', False):
                # Get the response and processing method
                response_text = response_data.get('response', 'No response text found')
                proc_method = response_data.get('processing_method', 'unknown')
                
                print("\nGenerated Response Text:")
                print("-" * 80)
                print(response_text)
                print("-" * 80)
                
                # Analyze the response quality
                print("\nResponse Analysis:")
                
                # Basic statistics
                char_count = len(response_text)
                word_count = len(response_text.split())
                sentence_count = len([s for s in response_text.split('.') if s.strip()])
                print(f"  Statistics: {char_count} chars, {word_count} words, ~{sentence_count} sentences")
                
                # Check for template responses
                template_markers = [
                    "This is a simulated response",
                    "I received your message",
                    "I received your question about",
                    "While I'd like to provide a detailed response",
                    "I'm currently operating with limited capabilities",
                    "Currently, my AI models are unavailable"
                ]
                
                is_template = any(marker in response_text for marker in template_markers)
                is_fallback = 'fallback' in proc_method.lower() or proc_method == 'placeholder'
                
                if is_template or is_fallback:
                    print("  ❌ WARNING: This appears to be a template/fallback response")
                    print(f"  Processing method: {proc_method}")
                else:
                    print("  ✓ This appears to be an actual AI-generated response")
                    print(f"  Processing method: {proc_method}")
                
                # Display debug info if available
                if 'debug_info' in response_data:
                    print("\nDebug Information:")
                    pprint(response_data['debug_info'])
            else:
                print(f"API Error: {response_data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to the server")
        print(f"Make sure the Flask server is running on {host}:{port}")
    except requests.exceptions.Timeout:
        print(f"Timeout Error: The request timed out after {timeout}s")
        print("The server may be overloaded or the model may be taking too long to initialize")
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def test_simple_endpoint(message, host="localhost", port=9876, timeout=10):
    """Test the simple_test endpoint that doesn't rely on model loading
    
    Args:
        message: Message to send to the API
        host: Hostname of the server
        port: Port number
        timeout: Request timeout in seconds
    """
    
    url = f"http://{host}:{port}/api/simple_test"
    print(f"Testing simple endpoint at: {url}")
    print(f"Message: '{message}'")
    
    # Prepare payload
    payload = {"message": message}
    
    # Make the request
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=timeout)
        request_time = time.time() - start_time
        
        print(f"Request completed in {request_time:.2f}s")
        print(f"Status code: {response.status_code}")
        
        # Parse the response
        if response.status_code == 200:
            response_data = response.json()
            
            print("\nAPI Response:")
            print("=" * 80)
            pprint(response_data)
            print("=" * 80)
            
            if response_data.get('success', False):
                print("\nResponse Text:")
                print("-" * 80)
                response_text = response_data.get('response', 'No response text found')
                print(response_text)
                print("-" * 80)
                
                # Show processing method if available
                proc_method = response_data.get('processing_method', 'unknown')
                print(f"Processing method: {proc_method}")
            else:
                print(f"API Error: {response_data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to the server")
        print(f"Make sure the Flask server is running on {host}:{port}")
    except requests.exceptions.Timeout:
        print(f"Timeout Error: The request timed out after {timeout}s")
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Parse command line arguments and run the test"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Minerva Direct API")
    parser.add_argument("message", help="Message to send")
    parser.add_argument("--port", type=int, default=9876, help="Port number")
    parser.add_argument("--host", default="localhost", help="Host address")
    parser.add_argument("--max-tokens", type=int, default=500, help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.8, help="Temperature for sampling")
    parser.add_argument("--validate", action="store_true", help="Enable validation (default: disabled)")
    parser.add_argument("--skip-process", action="store_true", help="Skip the process function (default: use it)")
    parser.add_argument("--model-type", default="basic", help="Model type to use for formatting (basic, zephyr, mistral-7b, code-llama, etc.)")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--simple-test", action="store_true", help="Use simple_test endpoint instead of direct")
    
    args = parser.parse_args()
    
    if args.simple_test:
        # Use the simple test endpoint instead
        test_simple_endpoint(
            message=args.message,
            host=args.host,
            port=args.port
        )
    else:
        # Use the direct API endpoint
        test_direct_api(
            message=args.message,
            host=args.host,
            port=args.port,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            bypass_validation=not args.validate,
            use_process_function=not args.skip_process,
            model_type=args.model_type,
            timeout=args.timeout
        )

if __name__ == "__main__":
    main()
