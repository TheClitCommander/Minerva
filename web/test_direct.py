#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test client for the direct API endpoint to debug Minerva's response generation
"""

import sys
import os
import time
import json
import requests

def test_direct_api(message, port=5000):
    """Test the direct API endpoint with a message"""
    url = f"http://localhost:{port}/api/direct"
    headers = {"Content-Type": "application/json"}
    payload = {"message": message}
    
    print(f"Sending message to {url}: {message}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("\nResponse data:")
            print(json.dumps(data, indent=2))
            
            if data.get('success', False):
                print("\nFormatted response:")
                print("=" * 50)
                print(data.get('response', 'No response generated'))
                print("=" * 50)
                return data
            else:
                print(f"Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Exception: {str(e)}")
    
    return None

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = "Tell me about how neural networks work"
    
    port = 5000
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except:
            print(f"Invalid port number: {sys.argv[2]}, using default: {port}")
    
    test_direct_api(message, port)

if __name__ == "__main__":
    main()
