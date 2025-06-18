#!/usr/bin/env python3
"""
API Key Validation Script for Minerva

This script checks the status of API keys for all cloud models and tests
their functionality by sending a simple test query to each one.
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger("api_validation")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test prompt for all models
TEST_PROMPT = "What are three key benefits of quantum computing?"

def validate_api_keys():
    """Check all API keys and their status"""
    
    from web.integrations.config import (
        OPENAI_API_KEY, 
        ANTHROPIC_API_KEY, 
        MISTRAL_API_KEY, 
        GOOGLE_API_KEY, 
        COHERE_API_KEY
    )
    
    # Check keys and report status
    results = []
    
    # OpenAI
    openai_status = _check_key(OPENAI_API_KEY, "OpenAI", "sk-")
    results.append({"provider": "OpenAI", "status": openai_status})
    
    # Anthropic
    anthropic_status = _check_key(ANTHROPIC_API_KEY, "Anthropic", "sk-ant-")
    results.append({"provider": "Anthropic", "status": anthropic_status})
    
    # Mistral
    mistral_status = _check_key(MISTRAL_API_KEY, "Mistral")
    results.append({"provider": "Mistral", "status": mistral_status})
    
    # Google
    google_status = _check_key(GOOGLE_API_KEY, "Google")
    results.append({"provider": "Google", "status": google_status})
    
    # Cohere
    cohere_status = _check_key(COHERE_API_KEY, "Cohere")
    results.append({"provider": "Cohere", "status": cohere_status})
    
    # GPT4All (local model)
    gpt4all_status = _check_gpt4all()
    results.append({"provider": "GPT4All (Local)", "status": gpt4all_status})
    
    return results

def _check_key(key: str, provider: str, expected_prefix: str = None) -> str:
    """Check if an API key is properly configured"""
    if not key or key in ["yourkeyhere", "sk-yourkeyhere", "your-key-here"]:
        return "❌ Missing or placeholder"
    
    if expected_prefix and not key.startswith(expected_prefix):
        return f"⚠️ Wrong format (should start with {expected_prefix})"
    
    return "✅ Configured"

def _check_gpt4all() -> str:
    """Check if GPT4All is properly configured"""
    try:
        # Check if model directory exists
        default_path = str(Path.home() / ".cache" / "gpt4all")
        if not os.path.exists(default_path):
            return "❌ Model directory not found"
        
        # Check for model files
        model_files = [f for f in os.listdir(default_path) if f.endswith(".gguf")]
        if not model_files:
            return "❌ No model files found"
        
        return f"✅ Available ({', '.join(model_files)})"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def test_models():
    """Test each model with a simple query"""
    results = []
    
    # Test OpenAI models
    results.append(_test_model("gpt-4", "OpenAI"))
    results.append(_test_model("gpt-4o", "OpenAI"))
    
    # Test Anthropic models
    results.append(_test_model("claude-3", "Anthropic"))
    
    # Test Mistral models
    results.append(_test_model("mistral-large", "Mistral"))
    
    # Test Google models
    results.append(_test_model("gemini-pro", "Google"))
    
    # Test Cohere models
    results.append(_test_model("cohere-command", "Cohere"))
    
    # Test GPT4All
    results.append(_test_model("gpt4all", "Local"))
    
    return results

def _test_model(model_name: str, provider: str) -> Dict[str, Any]:
    """Test a specific model with the test prompt"""
    result = {
        "model": model_name,
        "provider": provider,
        "status": "Not tested",
        "latency": None,
        "response": None,
        "error": None
    }
    
    try:
        logger.info(f"Testing {model_name} from {provider}...")
        
        # Import necessary modules based on provider
        if provider == "OpenAI":
            from web.integrations.openai_integration import generate_response
            processor = generate_response
        elif provider == "Anthropic":
            from web.integrations.anthropic_integration import generate_response
            processor = generate_response
        elif provider == "Mistral":
            from web.integrations.mistral_integration import generate_response
            processor = generate_response
        elif provider == "Google":
            from web.integrations.google_integration import generate_response
            processor = generate_response
        elif provider == "Cohere":
            from web.integrations.cohere_integration import generate_response
            processor = generate_response
        elif provider == "Local":
            from web.model_processors import process_with_gpt4all
            processor = process_with_gpt4all
        else:
            result["status"] = "❌ Unknown provider"
            return result
        
        # Measure response time
        start_time = time.time()
        
        if provider == "Local":
            # Local GPT4All has a different interface
            response = processor(TEST_PROMPT)
        else:
            # Cloud models
            response = processor(model_name, TEST_PROMPT)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Update result
        result["status"] = "✅ Working"
        result["latency"] = f"{latency:.2f}s"
        result["response"] = response[:100] + "..." if len(response) > 100 else response
        
    except Exception as e:
        result["status"] = "❌ Error"
        result["error"] = str(e)
    
    return result

def print_results(api_results, model_results):
    """Display validation results in a readable format"""
    print("\n" + "=" * 80)
    print(" MINERVA API KEY VALIDATION RESULTS ".center(80, "="))
    print("=" * 80)
    
    # API Key Status
    print("\n📋 API KEY STATUS:")
    print("-" * 80)
    for result in api_results:
        print(f"{result['provider']:<15} | {result['status']}")
    
    # Model Test Results
    print("\n🧪 MODEL TEST RESULTS:")
    print("-" * 80)
    print(f"{'MODEL':<20} | {'PROVIDER':<12} | {'STATUS':<10} | {'LATENCY':<8} | {'RESPONSE/ERROR'}")
    print("-" * 80)
    for result in model_results:
        status = result["status"]
        latency = result["latency"] if result["latency"] else "N/A"
        response = result["response"] if result["response"] else result.get("error", "N/A")
        print(f"{result['model']:<20} | {result['provider']:<12} | {status:<10} | {latency:<8} | {response[:50]}...")
    
    print("\n" + "=" * 80)
    print(" RECOMMENDATIONS ".center(80, "="))
    
    # Count working models
    working_models = sum(1 for r in model_results if r["status"] == "✅ Working")
    total_models = len(model_results)
    
    print(f"\n✓ {working_models}/{total_models} models are operational")
    
    if working_models == 0:
        print("\n❗ CRITICAL: No models are working. Please check your API keys and configurations.")
    elif working_models < total_models / 2:
        print("\n⚠️ WARNING: Less than half of the models are working. The Think Tank's model ensemble")
        print("  will be limited, affecting response quality and ranking.")
    elif working_models < total_models:
        print("\n🔶 NOTE: Some models are not working. The Think Tank will still function,")
        print("  but with a reduced model selection.")
    else:
        print("\n🟢 All models are operational! The Think Tank will have full model selection capability.")
    
    # Specific recommendations based on results
    missing_providers = [r["provider"] for r in api_results if "❌" in r["status"]]
    if missing_providers:
        print(f"\n📝 RECOMMENDATION: Add API keys for: {', '.join(missing_providers)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    logger.info("Starting API key and model validation...")
    
    # Validate API keys
    logger.info("Checking API key configurations...")
    api_results = validate_api_keys()
    
    # Test models
    logger.info("Testing models with sample query...")
    model_results = test_models()
    
    # Print results
    print_results(api_results, model_results)
