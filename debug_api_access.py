#!/usr/bin/env python3
"""
Minerva API Access Debugging Tool

This script tests your API keys and connections to various AI providers.
It helps diagnose issues that might prevent Minerva from accessing AI models.

Usage:
  python debug_api_access.py

This will load your environment variables or .env file and test all configured API keys.
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime

# API Key handling utilities
def validate_key_format(key_name, value):
    """Check if the API key has the correct format"""
    if not value:
        return False
        
    # Define expected prefixes for different API keys
    expected_prefixes = {
        "OPENAI_API_KEY": "sk-",
        "ANTHROPIC_API_KEY": "sk-ant-",
        "HUGGINGFACE_API_KEY": "hf_",
        # Mistral doesn't have a required prefix pattern
        "MISTRAL_API_KEY": ""
    }
    
    prefix = expected_prefixes.get(key_name, "")
    if prefix and not value.startswith(prefix):
        return False
    
    # Basic length check
    if len(value) < 8:  # Most API keys are significantly longer
        return False
        
    return True

def mask_key(value):
    """Mask an API key for safe logging"""
    if not value or len(value) < 8:
        return "INVALID_KEY"
    
    # Show prefix and last 4 chars
    return value[:7] + "..." + value[-4:]

# Banner
print("\n" + "="*60)
print("  Minerva API Access Debugging Tool")
print("="*60)

# Load environment variables 
try:
    from dotenv import load_dotenv
    if os.path.exists('.env'):
        print("✅ Loading environment from .env file")
        load_dotenv()
    else:
        print("⚠️ No .env file found, using environment variables only")
except ImportError:
    print("⚠️ python-dotenv not installed. Using environment variables only.")

# Get API keys
openai_key = os.environ.get("OPENAI_API_KEY", "")
anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
mistral_key = os.environ.get("MISTRAL_API_KEY", "")
huggingface_key = os.environ.get("HUGGINGFACE_API_KEY", "")

# Check keys and print status with validation and masking
print("\n📋 API Key Status:")
print("------------------")

# OpenAI
openai_valid = validate_key_format("OPENAI_API_KEY", openai_key)
print(f"OpenAI API Key: {'✅ CONFIGURED' if openai_key else '❌ NOT CONFIGURED'}")
if openai_key:
    print(f"   Format: {'✅ VALID' if openai_valid else '❌ INVALID FORMAT'}")
    print(f"   Value: {mask_key(openai_key)}")
    if not openai_valid:
        print("   Error: OpenAI keys should start with 'sk-'")

# Anthropic
anthropic_valid = validate_key_format("ANTHROPIC_API_KEY", anthropic_key)
print(f"Anthropic API Key: {'✅ CONFIGURED' if anthropic_key else '❌ NOT CONFIGURED'}")
if anthropic_key:
    print(f"   Format: {'✅ VALID' if anthropic_valid else '❌ INVALID FORMAT'}")
    print(f"   Value: {mask_key(anthropic_key)}")
    if not anthropic_valid:
        print("   Error: Anthropic keys should start with 'sk-ant-'")

# Mistral
mistral_valid = validate_key_format("MISTRAL_API_KEY", mistral_key)
print(f"Mistral API Key: {'✅ CONFIGURED' if mistral_key else '❌ NOT CONFIGURED'}")
if mistral_key:
    print(f"   Format: {'✅ VALID' if mistral_valid else '❌ INVALID FORMAT'}")
    print(f"   Value: {mask_key(mistral_key)}")
    if not mistral_valid:
        print("   Error: Mistral key appears to be malformed (too short or invalid)")

# HuggingFace
huggingface_valid = validate_key_format("HUGGINGFACE_API_KEY", huggingface_key)
print(f"HuggingFace API Key: {'✅ CONFIGURED' if huggingface_key else '❌ NOT CONFIGURED'}")
if huggingface_key:
    print(f"   Format: {'✅ VALID' if huggingface_valid else '❌ INVALID FORMAT'}")
    print(f"   Value: {mask_key(huggingface_key)}")
    if not huggingface_valid:
        print("   Error: HuggingFace keys should start with 'hf_'")

# Count how many API keys we have and how many have valid format
keys_configured = sum([bool(k) for k in [openai_key, anthropic_key, mistral_key, huggingface_key]])
keys_valid = sum([k for k in [openai_valid and bool(openai_key), 
                             anthropic_valid and bool(anthropic_key), 
                             mistral_valid and bool(mistral_key), 
                             huggingface_valid and bool(huggingface_key)]])

print(f"\n🔑 {keys_configured} of 4 API keys configured")
print(f"🔑 {keys_valid} of {keys_configured} configured keys have valid format")

if keys_configured == 0:
    print("\n❗ No API keys configured. Minerva will run in SIMULATION MODE only.")
    print("See .env.example for how to configure your keys.")
    print("\nYou can still run the server, but only simulated AI will be available.")
    sys.exit(1)
elif keys_valid < keys_configured:
    print("\n⚠️ Some API keys have invalid format. This may cause connection issues.")

# Test functionality of each API
print("\n🧪 Testing API connections...")
print("-------------------------")

test_message = "Hello, this is a test message from Minerva debugging tool. Please reply with a short response."

# Test OpenAI
if openai_key and openai_valid:
    print("\n🔄 Testing OpenAI API connection...")
    try:
        import openai
        from openai import OpenAI
        
        client = OpenAI(api_key=openai_key)
        
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": test_message}
            ],
            max_tokens=50
        )
        elapsed = time.time() - start_time
        
        print(f"✅ OpenAI API connection successful! ({elapsed:.2f}s)")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        print(traceback.format_exc())
elif openai_key and not openai_valid:
    print("\n❌ Skipping OpenAI API test due to invalid key format.")

# Test Anthropic
if anthropic_key and anthropic_valid:
    print("\n🔄 Testing Anthropic API connection...")
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        start_time = time.time()
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": test_message}],
            max_tokens=50
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Anthropic API connection successful! ({elapsed:.2f}s)")
        print(f"Response: {response.content[0].text}")
    except Exception as e:
        print(f"❌ Anthropic API error: {str(e)}")
        print(traceback.format_exc())
elif anthropic_key and not anthropic_valid:
    print("\n❌ Skipping Anthropic API test due to invalid key format.")

# Test Mistral
if mistral_key and mistral_valid:
    print("\n🔄 Testing Mistral API connection...")
    try:
        from mistralai.client import MistralClient
        from mistralai.models.chat_completion import ChatMessage
        
        client = MistralClient(api_key=mistral_key)
        
        start_time = time.time()
        response = client.chat(
            model="mistral-small-latest",
            messages=[ChatMessage(role="user", content=test_message)],
        )
        elapsed = time.time() - start_time
        
        print(f"✅ Mistral API connection successful! ({elapsed:.2f}s)")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Mistral API error: {str(e)}")
        print(traceback.format_exc())
elif mistral_key and not mistral_valid:
    print("\n❌ Skipping Mistral API test due to invalid key format.")

# Test HuggingFace
if huggingface_key and huggingface_valid:
    print("\n🔄 Testing HuggingFace API connection...")
    try:
        import requests
        
        API_URL = "https://api-inference.huggingface.co/models/gpt2"
        headers = {"Authorization": f"Bearer {huggingface_key}"}
        
        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.json()
            
        start_time = time.time()
        output = query({
            "inputs": test_message,
            "parameters": {"max_length": 50}
        })
        elapsed = time.time() - start_time
        
        print(f"✅ HuggingFace API connection successful! ({elapsed:.2f}s)")
        print(f"Response: {output[0]['generated_text']}")
    except Exception as e:
        print(f"❌ HuggingFace API error: {str(e)}")
        print(traceback.format_exc())
elif huggingface_key and not huggingface_valid:
    print("\n❌ Skipping HuggingFace API test due to invalid key format.")

# Summary
print("\n📊 Test Summary:")
print("--------------")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"API Keys Configured: {keys_configured}/4")
print(f"API Keys with Valid Format: {keys_valid}/{keys_configured}")

# Next steps
print("\n📋 Next Steps:")
print("------------")
if keys_valid > 0:
    print("✅ You have API keys with valid formats - Minerva should be able to use real AI models.")
    print("🚀 Run './run_minerva_app.sh' to start the server with your configured keys.")
else:
    print("❌ No valid API keys configured. Minerva will run in simulation mode only.")
    print("📝 To add API keys:")
    print("   1. Create a '.env' file based on '.env.example'")
    print("   2. Add your API keys to the .env file using the correct formats:")
    print("      - OpenAI: sk-xxxxxxxxxxxx...")
    print("      - Anthropic: sk-ant-xxxxxxxxxxxx...")
    print("      - HuggingFace: hf_xxxxxxxxxxxx...")
    print("   3. Run 'source set_api_keys.sh' to set keys interactively")

print("\n" + "="*60) 