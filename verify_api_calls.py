#!/usr/bin/env python3
"""
Direct API Call Verification Script for Minerva

This script directly tests the OpenAI and Anthropic APIs to verify they are working
properly and returning real responses instead of simulated ones.
"""
import os
import sys
import json
import logging
import asyncio
import time
import requests
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ApiVerification")

# Import dotenv for environment variables if available
try:
    import dotenv
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(dotenv_path):
        logger.info(f"Loading environment variables from {dotenv_path}")
        dotenv.load_dotenv(dotenv_path)
except ImportError:
    logger.warning("dotenv not available, skipping .env file loading")

# Set API keys if they are in the environment but not already set
if not os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_API_KEY_VALUE"):
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY_VALUE")
    logger.info("Set OPENAI_API_KEY from OPENAI_API_KEY_VALUE")
    
if not os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("ANTHROPIC_API_KEY_VALUE"):
    os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY_VALUE")
    logger.info("Set ANTHROPIC_API_KEY from ANTHROPIC_API_KEY_VALUE")

# Set default API keys for testing if needed
if not os.environ.get("OPENAI_API_KEY"):
    # Default key for testing
    DEFAULT_OPENAI_KEY = "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"
    os.environ["OPENAI_API_KEY"] = DEFAULT_OPENAI_KEY
    logger.warning("Using default OpenAI API key for testing. Replace with your own in production.")

def direct_openai_request(api_key, messages, model="gpt-4"):
    """Make a direct HTTP request to OpenAI API without using the client"""
    logger.info(f"Making direct API request to OpenAI API for {model}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 100,
        "temperature": 0.7,
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # 30 second timeout
        )
        
        # Check if request was successful
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        logger.info(f"Successfully received response from OpenAI API")
        return {
            "success": True,
            "data": result,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error in direct OpenAI request: {str(e)}")
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

async def test_openai_api():
    """Test direct API call to OpenAI without using the client"""
    logger.info("Testing OpenAI API using direct HTTP request...")
    
    try:
        # Get API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OpenAI API key found")
            return False, {"success": False, "error": "No API key"}
            
        # Log key format for debugging
        key_format = f"{api_key[:3]}...{api_key[-3:]} (length: {len(api_key)})"
        logger.info(f"Using OpenAI API key format: {key_format}")
        
        # Prepare messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain the concept of API integration in one sentence."}
        ]
        
        # Make test call using direct request
        start_time = time.time()
        result = direct_openai_request(api_key, messages, model="gpt-4")
        end_time = time.time()
        
        if not result["success"]:
            # API call failed
            error_msg = result["error"]
            logger.error(f"Error calling GPT-4 API: {error_msg}")
            return False, {"success": False, "error": error_msg}
            
        # Check if we got a real response
        api_response = result["data"]
        content = api_response["choices"][0]["message"]["content"]
        model = api_response["model"]
        
        logger.info(f"✅ OpenAI API test successful in {end_time - start_time:.2f}s")
        logger.info(f"Model: {model}")
        logger.info(f"Response: {content}")
        
        return True, {
            "success": True,
            "model": model,
            "content": content,
            "processing_time": end_time - start_time
        }
    
    except Exception as e:
        logger.error(f"❌ OpenAI API test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {
            "success": False,
            "error": str(e)
        }

async def test_anthropic_api():
    """Test direct API call to Anthropic"""
    logger.info("Testing Anthropic API...")
    
    try:
        # Check if API key exists
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("No Anthropic API key found, skipping test")
            return False, {
                "success": False,
                "error": "No API key"
            }
        
        # Import Anthropic
        from anthropic import AsyncAnthropic
        
        # Create client
        client = AsyncAnthropic(api_key=api_key)
        
        # Make test call
        start_time = time.time()
        response = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            system="You are a helpful assistant.",
            messages=[
                {"role": "user", "content": "Explain the concept of API integration in one sentence."}
            ]
        )
        end_time = time.time()
        
        # Check if we got a real response
        content = response.content[0].text
        model = response.model
        
        logger.info(f"✅ Anthropic API test successful in {end_time - start_time:.2f}s")
        logger.info(f"Model: {model}")
        logger.info(f"Response: {content}")
        
        return True, {
            "success": True,
            "model": model,
            "content": content,
            "processing_time": end_time - start_time
        }
    
    except Exception as e:
        logger.error(f"❌ Anthropic API test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {
            "success": False,
            "error": str(e)
        }

async def main():
    """Run all API tests"""
    print("\n" + "=" * 80)
    print("🧪 MINERVA API CALL VERIFICATION 🧪")
    print("=" * 80)
    print("Testing direct API calls to verify real model integration")
    print("=" * 80 + "\n")
    
    # Test OpenAI
    openai_success, openai_result = await test_openai_api()
    
    # Test Anthropic
    anthropic_success, anthropic_result = await test_anthropic_api()
    
    # Summarize results
    print("\n" + "=" * 80)
    print("API VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"OpenAI API:     {'✅ WORKING' if openai_success else '❌ FAILED'}")
    print(f"Anthropic API:  {'✅ WORKING' if anthropic_success else '❌ FAILED'}")
    print("=" * 80)
    
    if openai_success or anthropic_success:
        print("\n🎉 SUCCESS! At least one real AI API is working.")
        print("Minerva can now use real AI models for responses.")
    else:
        print("\n⚠️ WARNING: No real AI APIs are working.")
        print("Minerva will fall back to simulated responses.")
    
    print("\nNext steps:")
    print("1. Restart the Minerva WebSocket server")
    print("2. Test Minerva with real requests")
    print("=" * 80 + "\n")
    
    # Save results to file
    results = {
        "timestamp": datetime.now().isoformat(),
        "openai": openai_result,
        "anthropic": anthropic_result,
        "overall_success": openai_success or anthropic_success
    }
    
    with open("api_verification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved to api_verification_results.json")
    
    return 0 if (openai_success or anthropic_success) else 1

if __name__ == "__main__":
    asyncio.run(main())
