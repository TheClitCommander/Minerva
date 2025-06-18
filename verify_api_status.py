#!/usr/bin/env python3
"""
API Status Verification Tool for Minerva

This script verifies the status and connectivity of various AI model APIs
used by Minerva's Think Tank mode.

It tests:
1. OpenAI API (GPT-4, GPT-3.5)
2. Anthropic API (Claude-3)
3. Mistral API
4. Cohere API
"""

import os
import sys
import json
import time
import logging
import requests
from typing import Dict, List, Tuple, Optional
import colorama
from colorama import Fore, Style
from dotenv import load_dotenv

# Initialize colorama
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("api_status_verifier")

# Load environment variables
load_dotenv()

def print_header(text: str):
    """Print a formatted header."""
    width = 80
    print("\n" + "="*width)
    print(f"{text.center(width)}")
    print("="*width + "\n")

def print_status(api_name: str, status: bool, message: str = "", time_ms: Optional[int] = None):
    """Print the status of an API check."""
    status_color = Fore.GREEN if status else Fore.RED
    status_icon = "✅" if status else "❌"
    status_text = "AVAILABLE" if status else "UNAVAILABLE"
    
    time_text = f" ({time_ms}ms)" if time_ms is not None else ""
    
    print(f"{status_color}{status_icon} {api_name.ljust(15)}: {status_text}{time_text}{Style.RESET_ALL}")
    if message:
        print(f"   {message}")

def verify_openai_api() -> Tuple[bool, str, Optional[int]]:
    """Verify OpenAI API connectivity."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "API key not found in environment variables", None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    try:
        # Just check models endpoint as a lightweight test
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers=headers,
            timeout=10
        )
        
        elapsed_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_names = [model.get("id") for model in models]
            
            # Check if key GPT models are available
            gpt4_available = any("gpt-4" in model.lower() for model in model_names)
            gpt35_available = any("gpt-3.5" in model.lower() for model in model_names)
            
            if gpt4_available and gpt35_available:
                return True, f"Found {len(models)} models including GPT-4 and GPT-3.5", elapsed_time
            elif gpt4_available:
                return True, f"Found {len(models)} models including GPT-4", elapsed_time
            elif gpt35_available:
                return True, f"Found {len(models)} models including GPT-3.5", elapsed_time
            else:
                return True, f"Found {len(models)} models", elapsed_time
        
        return False, f"API responded with status code: {response.status_code}", elapsed_time
    
    except Exception as e:
        logger.error(f"Error verifying OpenAI API: {str(e)}")
        return False, f"Error: {str(e)}", None

def verify_anthropic_api() -> Tuple[bool, str, Optional[int]]:
    """Verify Anthropic (Claude) API connectivity."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return False, "API key not found in environment variables", None
    
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    # Minimal message to test API
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 10,
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    start_time = time.time()
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=10
        )
        
        elapsed_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        if response.status_code == 200:
            return True, "Successfully connected to Claude API", elapsed_time
        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            return False, f"API responded with status code: {response.status_code}, {error_msg}", elapsed_time
    
    except Exception as e:
        logger.error(f"Error verifying Anthropic API: {str(e)}")
        return False, f"Error: {str(e)}", None

def verify_mistral_api() -> Tuple[bool, str, Optional[int]]:
    """Verify Mistral API connectivity."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return False, "API key not found in environment variables", None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    try:
        # Check models endpoint
        response = requests.get(
            "https://api.mistral.ai/v1/models",
            headers=headers,
            timeout=10
        )
        
        elapsed_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        if response.status_code == 200:
            models = response.json().get("data", [])
            model_names = [model.get("id") for model in models]
            return True, f"Found {len(models)} models: {', '.join(model_names)}", elapsed_time
        
        return False, f"API responded with status code: {response.status_code}", elapsed_time
    
    except Exception as e:
        logger.error(f"Error verifying Mistral API: {str(e)}")
        return False, f"Error: {str(e)}", None

def verify_cohere_api() -> Tuple[bool, str, Optional[int]]:
    """Verify Cohere API connectivity."""
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return False, "API key not found in environment variables", None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    start_time = time.time()
    try:
        # Minimal request to test API availability
        data = {
            "model": "command",
            "message": "Hello",
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.cohere.ai/v1/chat",
            headers=headers,
            json=data,
            timeout=10
        )
        
        elapsed_time = int((time.time() - start_time) * 1000)  # Convert to ms
        
        if response.status_code == 200:
            return True, "Successfully connected to Cohere API", elapsed_time
        else:
            error_msg = response.json().get("message", "Unknown error")
            return False, f"API responded with status code: {response.status_code}, {error_msg}", elapsed_time
    
    except Exception as e:
        logger.error(f"Error verifying Cohere API: {str(e)}")
        return False, f"Error: {str(e)}", None

def check_minerva_connection() -> bool:
    """Verify if Minerva's local server is running."""
    try:
        response = requests.get("http://localhost:9876/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print_header("MINERVA API STATUS VERIFICATION")
    
    # Check if Minerva server is running
    minerva_running = check_minerva_connection()
    print_status("Minerva Server", minerva_running, 
                "Local server is running and ready" if minerva_running else "Local server is not running")
    
    # Verify OpenAI API
    print("\n📊 Checking API Statuses...")
    openai_status, openai_message, openai_time = verify_openai_api()
    print_status("OpenAI API", openai_status, openai_message, openai_time)
    
    # Verify Anthropic API
    anthropic_status, anthropic_message, anthropic_time = verify_anthropic_api()
    print_status("Claude API", anthropic_status, anthropic_message, anthropic_time)
    
    # Verify Mistral API
    mistral_status, mistral_message, mistral_time = verify_mistral_api()
    print_status("Mistral API", mistral_status, mistral_message, mistral_time)
    
    # Verify Cohere API
    cohere_status, cohere_message, cohere_time = verify_cohere_api()
    print_status("Cohere API", cohere_status, cohere_message, cohere_time)
    
    # Summary
    print("\n📊 API Status Summary:")
    print(f"OpenAI API: {'✅ Ready' if openai_status else '❌ Unavailable'}")
    print(f"Claude API: {'✅ Ready' if anthropic_status else '❌ Unavailable'}")
    print(f"Mistral API: {'✅ Ready' if mistral_status else '❌ Unavailable'}")
    print(f"Cohere API: {'✅ Ready' if cohere_status else '❌ Unavailable'}")
    
    # Overall recommendation
    print("\n📋 Recommendations:")
    if all([openai_status, anthropic_status, mistral_status, cohere_status]):
        print(f"{Fore.GREEN}✅ All APIs are available. Minerva's Think Tank Mode should function optimally with all models.{Style.RESET_ALL}")
    elif openai_status and (anthropic_status or mistral_status):
        print(f"{Fore.YELLOW}⚠️ Most critical APIs are available. Minerva's Think Tank Mode should function with some model options.{Style.RESET_ALL}")
    elif openai_status:
        print(f"{Fore.YELLOW}⚠️ Only OpenAI API is available. Minerva's Think Tank Mode will function with limited model diversity.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ No critical APIs are available. Minerva's Think Tank Mode will fall back to simulated mode.{Style.RESET_ALL}")
    
    if not minerva_running:
        print(f"{Fore.YELLOW}⚠️ Minerva's local server is not running. Start the server with 'python web/app.py' before testing.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
