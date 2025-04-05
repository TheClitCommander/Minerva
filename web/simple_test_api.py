#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified test script for Minerva API endpoints
This script tests various API endpoints without relying on complex model loading
"""

import sys
import json
import requests
import uuid
from datetime import datetime
import argparse

def test_simple_endpoint(message, endpoint="simple_test", host="localhost", port=9876, method="POST", debug=False):
    """Test the simple API endpoints that don't rely on model loading"""
    
    url = f"http://{host}:{port}/api/{endpoint}"
    print(f"Testing {method} request to {url} with message: '{message}'")
    
    # Make the API request
    try:
        if method.upper() == "POST":
            # Prepare payload
            payload = {"message": message}
            
            if debug:
                print("Request payload:")
                print(json.dumps(payload, indent=2))
                
            # Send POST request
            response = requests.post(url, json=payload, timeout=10)
        else:  # GET
            # Send GET request with query parameters
            response = requests.get(f"{url}?message={requests.utils.quote(message)}", timeout=10)
        
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
                return True, data["response"]
            else:
                print("\nNo response text found in the API response")
                return False, "No response text found"
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            return False, f"HTTP Error: {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to the server")
        print(f"Make sure the Flask server is running on {host}:{port}")
        return False, "Connection Error"
    except requests.exceptions.Timeout:
        print("Timeout Error: The request timed out")
        return False, "Timeout Error"
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Exception: {str(e)}"

def test_server_health(host="localhost", port=9876):
    """Test if the Flask server is running and responsive"""
    url = f"http://{host}:{port}/api/simple_test"
    print(f"Testing server health at {url}")
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("Server is running and responsive!")
            return True
        else:
            print(f"Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to the server")
        print(f"Make sure the Flask server is running on {host}:{port}")
        return False
    except requests.exceptions.Timeout:
        print("Timeout Error: The request timed out")
        return False
    except Exception as e:
        print(f"Exception: {str(e)}")
        return False

def main():
    """Parse command line arguments and run tests"""
    parser = argparse.ArgumentParser(description="Test Minerva's simplified API endpoints")
    parser.add_argument("message", nargs="?", default="Test message", help="Message to send")
    parser.add_argument("--host", default="localhost", help="Host name (default: localhost)")
    parser.add_argument("--port", type=int, default=9876, help="Port number (default: 9876)")
    parser.add_argument("--endpoint", default="simple_test", choices=["simple_test", "test_direct", "direct"], help="Endpoint to test (default: simple_test)")
    parser.add_argument("--method", default="POST", choices=["GET", "POST"], help="HTTP method to use (default: POST)")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--check-server", action="store_true", help="Only check if the server is running")
    
    args = parser.parse_args()
    
    # First check if server is running if requested
    if args.check_server:
        server_ok = test_server_health(args.host, args.port)
        sys.exit(0 if server_ok else 1)
    
    # Test the requested endpoint
    success, _ = test_simple_endpoint(
        args.message, 
        endpoint=args.endpoint,
        host=args.host, 
        port=args.port,
        method=args.method,
        debug=args.debug
    )
    
    # Return exit code based on success
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
