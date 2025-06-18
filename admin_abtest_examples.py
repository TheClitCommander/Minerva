#!/usr/bin/env python3
"""
Example usage of Minerva's admin-only A/B testing API endpoints.
This script demonstrates how to call the admin endpoints properly with the appropriate
authentication header.
"""
import requests
import json
import os

# Base URL and admin key
BASE_URL = "http://localhost:5000"  # Change to your Minerva server URL
ADMIN_KEY = os.environ.get("MINERVA_ADMIN_KEY", "minerva-admin-key")

def print_response(response):
    """Pretty print the API response"""
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(f"Response: {response.text}")

def enable_abtest():
    """Enable A/B testing"""
    print("\n=== Enabling A/B Testing ===")
    url = f"{BASE_URL}/admin/abtest/toggle"
    headers = {
        "Content-Type": "application/json",
        "X-Admin-API-Key": ADMIN_KEY
    }
    data = {"enabled": True}
    
    response = requests.post(url, headers=headers, json=data)
    print_response(response)

def disable_abtest():
    """Disable A/B testing"""
    print("\n=== Disabling A/B Testing ===")
    url = f"{BASE_URL}/admin/abtest/toggle"
    headers = {
        "Content-Type": "application/json",
        "X-Admin-API-Key": ADMIN_KEY
    }
    data = {"enabled": False}
    
    response = requests.post(url, headers=headers, json=data)
    print_response(response)

def view_results():
    """View A/B testing results"""
    print("\n=== Viewing A/B Testing Results ===")
    url = f"{BASE_URL}/admin/abtest/results"
    headers = {
        "X-Admin-API-Key": ADMIN_KEY
    }
    
    response = requests.get(url, headers=headers)
    print_response(response)

if __name__ == "__main__":
    print("Admin A/B Testing API Examples")
    print(f"Using admin key: {ADMIN_KEY}")
    print("Note: Make sure Minerva server is running!")
    
    # Uncomment the functions you want to use
    # enable_abtest()
    # disable_abtest()
    # view_results()
    
    print("\nTo use these examples:")
    print("1. Make sure Minerva server is running")
    print("2. Set the MINERVA_ADMIN_KEY environment variable (optional)")
    print("3. Uncomment the function calls in this script")
    print("4. Run this script: python admin_abtest_examples.py")
