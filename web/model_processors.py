#!/usr/bin/env python3
"""
Model Processors for Minerva AI

This module provides implementations of model processors that the MultiAICoordinator
can use to process messages with various AI models.
"""

import os
import json
import logging
import random
import asyncio
import time

# Test mode detection
TEST_MODE = os.environ.get("MINERVA_TEST_MODE", "false").lower() == "true"

def is_test_api_key(api_key):
    """Check if an API key is a test key"""
    test_patterns = ["test-key", "test-openai", "test-ant", "minerva-thinktank"]
    if api_key and isinstance(api_key, str):
        return any(pattern in api_key.lower() for pattern in test_patterns)
    return False

import re
from typing import Dict, Any, List, Optional, Tuple, Callable

# Import actual API clients
import openai
import httpx
try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

# For proper timeout handling
try:
    from asyncio import timeout as asyncio_timeout
except ImportError:
    # For older Python versions
    asyncio_timeout = None

# Model usage tracking
model_usage_counts = {}

def update_model_usage(model_name: str):
    """Update usage counter for a specific model"""
    if model_name not in model_usage_counts:
        model_usage_counts[model_name] = 0
    model_usage_counts[model_name] += 1

# Import synchronous OpenAI client for direct API access
import os
import json
import requests
from datetime import datetime
from requests.exceptions import RequestException

def create_openai_client(api_key):
    """
    Create an OpenAI API client with the provided API key.
    
    Args:
        api_key: The OpenAI API key to use for authentication
        
    Returns:
        An OpenAI AsyncOpenAI object
    """
    try:
        from openai import AsyncOpenAI
        # Create client with minimal required parameters to avoid compatibility issues with newer SDK versions
        client = AsyncOpenAI(api_key=api_key)
        logger.info("Created OpenAI AsyncOpenAI client with minimal parameters")
        return client
    except ImportError as e:
        logger.error(f"Failed to import OpenAI AsyncClient: {e}")
        raise ImportError(f"OpenAI client library not installed properly: {e}")
    except Exception as e:
        logger.error(f"Failed to create OpenAI client: {e}")
        # Fall back to using requests for API calls if client creation fails
        logger.info("Will use direct API requests instead of client")
        return None

def direct_openai_request(api_key, messages, model="gpt-4"):
    """
    Make a direct HTTP request to OpenAI API without using the official client
    to avoid compatibility issues.
    
    Args:
        api_key: OpenAI API key
        messages: List of message objects with role and content
        model: Model to use
    
    Returns:
        Dict with API response or error
    """
    logger.info(f"Making direct API request to OpenAI API for {model}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 1000,
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
        
    except RequestException as e:
        logger.error(f"Error in direct OpenAI request: {str(e)}")
        return {
            "success": False,
            "data": None,
            "error": str(e)
        }

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dictionary to track model usage
models_used = {}

def update_model_usage(model_name):
    """
    Update the global models_used dictionary to track model usage.
    
    Args:
        model_name: The name of the model that was used
    """
    global models_used
    
    # Initialize if needed
    if not models_used:
        models_used = {}
    
    # Update usage stats
    if model_name not in models_used:
        models_used[model_name] = {
            'model_used': model_name,
            'last_used': datetime.now().isoformat(),
            'count': 1
        }
    else:
        models_used[model_name]['last_used'] = datetime.now().isoformat()
        models_used[model_name]['count'] += 1
    
    logger.info(f"Updated usage statistics for model: {model_name}, total uses: {models_used[model_name]['count']}")

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# Model response quality factors (for simulated responses)
QUALITY_FACTORS = {
    "gpt4": 0.95,
    "claude3": 0.93,
    "mistral7b": 0.88,
    "llama2": 0.85,
    "gpt4all": 0.78,
    "falcon": 0.83
}

# Simulated response templates for different query types
RESPONSE_TEMPLATES = {
    "code": [
        "Here's the code implementation you requested:\n\n```python\n{details}\n```\n\nThis implementation {explanation}",
        "I've created the following code solution:\n\n```python\n{details}\n```\n\nThe approach works by {explanation}",
        "Here's how you can implement this:\n\n```python\n{details}\n```\n\nThis solution {explanation}"
    ],
    "math": [
        "The mathematical solution is:\n\n{details}\n\nTo explain further, {explanation}",
        "To solve this problem, we need to:\n\n{details}\n\nThis works because {explanation}",
        "The solution can be derived as follows:\n\n{details}\n\nThe key insight is that {explanation}"
    ],
    "general": [
        "Based on your query, I can provide the following information:\n\n{details}\n\nFurthermore, {explanation}",
        "Here's what you need to know:\n\n{details}\n\nAdditionally, {explanation}",
        "In response to your question:\n\n{details}\n\nIt's worth noting that {explanation}"
    ]
}

# Explanation generators for different models
MODEL_EXPLANATIONS = {
    "gpt4": lambda query: f"provides a comprehensive and nuanced understanding that addresses all aspects of '{query[:50]}...'",
    "claude3": lambda query: f"offers a detailed and balanced perspective on '{query[:50]}...' with careful consideration of context",
    "mistral7b": lambda query: f"gives a solid answer to '{query[:50]}...' with good attention to the key points",
    "llama2": lambda query: f"provides a reasonable response to '{query[:50]}...' covering the main aspects",
    "gpt4all": lambda query: f"addresses the basic elements of '{query[:50]}...' in a straightforward manner",
    "falcon": lambda query: f"analyzes '{query[:50]}...' with focus on the creative and conceptual dimensions"
}

# Simulated code samples for code-related queries
CODE_SAMPLES = {
    "fibonacci": """def fibonacci(n):
    # Calculate the nth Fibonacci number.
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b""",
    
    "sort": """def quick_sort(arr):
    # Implement quick sort algorithm.
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)""",
    
    "neural": """class SimpleNeuralNetwork:
    # A simple neural network implementation.
    def __init__(self, input_size, hidden_size, output_size):
        self.weights1 = np.random.randn(input_size, hidden_size)
        self.weights2 = np.random.randn(hidden_size, output_size)
        
    def forward(self, X):
        self.hidden = np.tanh(np.dot(X, self.weights1))
        self.output = np.dot(self.hidden, self.weights2)
        return self.output"""
}

def evaluate_response_quality(response: str, query: str = None) -> Dict[str, Any]:
    """
    Evaluate the quality of an AI response based on multiple factors.
    
    Args:
        response: The AI response to evaluate
        query: The original query that prompted the response
        
    Returns:
        Dict containing quality scores and analysis
    """
    # Initialize results structure
    results = {
        "overall_score": 0.0,
        "structure_score": 0.0,
        "content_score": 0.0,
        "relevance_score": 0.8,  # Default assuming somewhat relevant
        "issues": [],
        "details": {}
    }
    
    # Check for empty response
    if not response or len(response.strip()) < 10:
        results["overall_score"] = 0.1
        results["issues"].append("empty_or_too_short")
        return results
    
    # Check length - penalize extremely short or long responses
    word_count = len(response.split())
    results["details"]["word_count"] = word_count
    
    if word_count < 20:
        results["content_score"] = 0.3
        results["issues"].append("too_short")
    elif word_count > 2000:
        results["content_score"] = 0.6  # Long but might be comprehensive
        results["issues"].append("very_long")
    else:
        # Ideal range
        results["content_score"] = 0.8
    
    # Check structure - paragraphs, formatting, etc.
    paragraphs = response.split('\n\n')
    has_lists = bool(re.search(r'\n[-*•] ', response))
    has_headers = bool(re.search(r'\n#{1,3} ', response))
    has_code_blocks = '```' in response
    
    structure_points = 0.5  # Base score
    if len(paragraphs) > 1:
        structure_points += 0.1
    if has_lists:
        structure_points += 0.1
    if has_headers:
        structure_points += 0.1
    if has_code_blocks and query and any(kw in query.lower() for kw in ['code', 'script', 'program', 'function']):
        structure_points += 0.2
    
    results["structure_score"] = min(1.0, structure_points)
    results["details"]["structure"] = {
        "paragraphs": len(paragraphs),
        "has_lists": has_lists,
        "has_headers": has_headers,
        "has_code": has_code_blocks
    }
    
    # Check for common issues
    if "as an ai" in response.lower() or "as an assistant" in response.lower():
        results["issues"].append("self_reference")
        results["content_score"] -= 0.1
    
    if response.lower().startswith("i'm sorry") and ("cannot" in response.lower() or "unable" in response.lower()):
        results["issues"].append("refusal")
        results["content_score"] -= 0.2
    
    # Calculate overall score
    results["overall_score"] = (results["content_score"] * 0.4 + 
                               results["structure_score"] * 0.3 + 
                               results["relevance_score"] * 0.3)
    
    # Ensure scores are within valid range
    for key in ["overall_score", "structure_score", "content_score", "relevance_score"]:
        results[key] = max(0.0, min(1.0, results[key]))
    
    return results

def validate_response(response: str, query: str = None) -> Dict[str, Any]:
    """
    Validate if a response is acceptable based on quality and content.
    
    Args:
        response: The AI response to validate
        query: The original query
        
    Returns:
        Dict with validation results
    """
    # Get quality evaluation
    quality = evaluate_response_quality(response, query)
    
    # Initialize validation results
    validation = {
        "is_valid": True,
        "score": quality["overall_score"],
        "reasons": [],
        "details": quality
    }
    
    # Check for rejection criteria
    if quality["overall_score"] < 0.4:
        validation["is_valid"] = False
        validation["reasons"].append(f"Low quality score: {quality['overall_score']:.2f}")
    
    if "refusal" in quality["issues"]:
        validation["is_valid"] = False
        validation["reasons"].append("Response contains a refusal")
        
    if "empty_or_too_short" in quality["issues"]:
        validation["is_valid"] = False
        validation["reasons"].append("Response is empty or too short")
    
    # Check for common placeholder templates
    placeholder_patterns = [
        r"\{\{.*?\}\}",  # {{placeholder}}
        r"\[.*?\]",      # [placeholder]
        r"\(insert .*?\)"  # (insert text)
    ]
    
    for pattern in placeholder_patterns:
        if re.search(pattern, response):
            validation["is_valid"] = False
            validation["reasons"].append("Response contains placeholder text")
            break
    
    return validation

def format_enhanced_prompt(message: str, model: str = None) -> str:
    """
    Format a user message with model-specific enhancements.
    
    Args:
        message: The original user message
        model: Target model name for customization
        
    Returns:
        Enhanced prompt string
    """
    # Base prompt with no enhancement
    enhanced_prompt = message
    
    # Apply model-specific enhancements
    if model and model.lower() in ['gpt4', 'gpt-4']:
        # For GPT-4, add a reminder to be detailed and accurate
        enhanced_prompt = f"{message}\n\nPlease provide a detailed and well-structured response."
    
    elif model and 'claude' in model.lower():
        # For Claude models, add a reminder about formatting
        enhanced_prompt = f"{message}\n\nPlease format your response with clear sections and examples where helpful."
    
    return enhanced_prompt

def get_model_processors():
    """
    Get available model processor functions.
    
    Returns:
        Dict of model processor functions
    """
    processors = {}
    
    # Try to import and add real model processors
    try:
        processors['gpt4'] = process_with_gpt4
    except NameError:
        pass
        
    try:
        processors['claude3'] = process_with_claude3
    except NameError:
        pass
        
    try:
        processors['mistral7b'] = process_with_mistral7b
    except NameError:
        pass
    
    try:
        processors['huggingface'] = process_with_huggingface
    except NameError:
        pass
    
    # Add simulated processors
    processors['simulated_gpt4'] = simulated_gpt4_processor
    processors['simulated_claude3'] = simulated_claude3_processor
    processors['simulated_mistral7b'] = simulated_mistral7b_processor
    processors['simulated_gpt4all'] = simulated_gpt4all_processor
    
    return processors

def attempt_salvage_response(response: str, message: str, model_name: str, issue: str = None) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Attempt to salvage a problematic response.
    
    Args:
        response: The original problematic response
        message: The user's message
        model_name: The model that generated the response
        issue: The specific issue type if known
        
    Returns:
        Tuple containing (success flag, salvaged response, debug info)
    """
    debug_info = {
        "original_response": response[:100] + "..." if len(response) > 100 else response,
        "issue": issue,
        "action_taken": "none"
    }
    
    # If empty response, return a generic response
    if not response or len(response.strip()) < 10:
        salvaged = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question or providing more details."
        debug_info["action_taken"] = "replaced_empty_response"
        return True, salvaged, debug_info
    
    # If response is a refusal, try to provide a partial answer
    if issue == "refusal" or response.lower().startswith("i'm sorry") and ("cannot" in response.lower() or "unable" in response.lower()):
        # Extract any useful information from the refusal
        parts = response.split('\n\n')
        if len(parts) > 1:
            # Use any additional paragraphs that might contain partial information
            salvaged = "While I can't provide a complete answer, here's what I can share:\n\n" + "\n\n".join(parts[1:])
            debug_info["action_taken"] = "extracted_partial_info_from_refusal"
            return True, salvaged, debug_info
    
    # If response has self-references, remove them
    if issue == "self_reference" or "as an ai" in response.lower() or "as an assistant" in response.lower():
        # Remove self-references
        cleaned = re.sub(r"(?i)as an AI(.*?)\.|(?i)as an assistant(.*?)\.", "", response)
        if cleaned and len(cleaned.strip()) > len(response) * 0.7:
            debug_info["action_taken"] = "removed_self_references"
            return True, cleaned, debug_info
    
    # If we get here, we couldn't salvage effectively
    debug_info["action_taken"] = "no_effective_salvage_possible"
    return False, response, debug_info

# Simulated processors for each model type
def simulated_gpt4_processor(message: str) -> Dict[str, Any]:
    """Simulate GPT-4 responses with high quality and technical accuracy."""
    update_model_usage('simulated_gpt4')
    return {
        "response": "This is a simulated GPT-4 response that demonstrates technical expertise and detailed explanations with accurate information. The response includes code examples when appropriate, clear structure, and comprehensive coverage of the topic.\n\n## Technical Analysis\n\nHere is a detailed breakdown of the concept:\n\n1. First, we examine the core principles\n2. Then, we explore practical applications\n3. Finally, we consider limitations and future directions\n\n```python\n# Example code implementation\ndef example_function(param):\n    return processed_result\n```\n\nThis approach ensures optimal performance while maintaining flexibility.",
        "model": "gpt4",
        "quality_score": 0.95,
        "is_error": False
    }

def simulated_claude3_processor(message: str) -> Dict[str, Any]:
    """Simulate Claude-3 responses with natural language and good reasoning."""
    update_model_usage('simulated_claude3')
    return {
        "response": "This is a simulated Claude-3 response showcasing natural language understanding and nuanced reasoning. The response maintains a conversational tone while delivering substantive content.\n\nI'll approach this from multiple perspectives:\n\n* Historical context provides important background\n* Current frameworks help us understand the present state\n* Emerging trends point to future developments\n\nThis balanced approach gives us a comprehensive view of the subject matter while acknowledging complexity and avoiding oversimplification.",
        "model": "claude3",
        "quality_score": 0.92,
        "is_error": False
    }

def simulated_mistral7b_processor(message: str) -> Dict[str, Any]:
    """Simulate Mistral-7B responses with concise but accurate content."""
    update_model_usage('simulated_mistral7b')
    return {
        "response": "This is a simulated Mistral-7B response providing concise and practical information. The response is direct and focuses on key points without unnecessary elaboration.\n\nKey points:\n- Main concept explained simply\n- Practical application outlined\n- Common pitfalls identified\n\nThis straightforward approach gives you actionable insights quickly.",
        "model": "mistral7b",
        "quality_score": 0.85,
        "is_error": False
    }

def simulated_gpt4all_processor(message: str) -> Dict[str, Any]:
    """Simulate GPT4All responses with basic information but occasional inaccuracies."""
    update_model_usage('simulated_gpt4all')
    return {
        "response": "This is a simulated GPT4All response that provides basic information on the topic. The response covers fundamental aspects but may not include advanced details.\n\nBasic explanation:\nThe concept involves several components working together to achieve the desired outcome. Applications range from everyday use to specialized contexts.\n\nRemember that these principles apply broadly but specific implementations may vary.",
        "model": "gpt4all",
        "quality_score": 0.75,
        "is_error": False
    }

async def process_with_huggingface(message: str) -> Dict[str, Any]:
    """
    Process a message with HuggingFace models using their Inference API.
    
    Args:
        message: The message to process
        
    Returns:
        Dict containing response, model name, and error status
    """
    api_token = os.environ.get("HUGGINGFACE_API_TOKEN") or os.environ.get("HF_API_TOKEN")
    
    # Default model - can be modified based on preferences or message content
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"  
    
    logger.info(f"Processing message with HuggingFace model: {model_id}")
    update_model_usage('huggingface')
    
    # Prepare the API request
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload
    payload = {
        "inputs": message,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True
        }
    }
    
    try:
        # Make the async API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=30.0  # 30 second timeout
            )
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                # Extract the generated text
                generated_text = result[0].get('generated_text', '')
                if not generated_text and 'summary_text' in result[0]:
                    generated_text = result[0]['summary_text']
                    
                return {
                    "response": generated_text,
                    "model": "huggingface",
                    "quality_score": 0.85,
                    "is_error": False
                }
            else:
                logger.warning(f"Unexpected response format from HuggingFace: {result}")
                return {
                    "response": "I'm sorry, but I couldn't generate a proper response for your query.",
                    "model": "huggingface",
                    "quality_score": 0.5,
                    "is_error": True,
                    "error": "Unexpected response format"
                }
    except Exception as e:
        logger.error(f"Error with HuggingFace API: {str(e)}")
        return {
            "response": f"Error with HuggingFace model: {str(e)}",
            "model": "huggingface",
            "is_error": True,
            "error": str(e)
        }

async def process_with_claude3(message: str) -> Dict[str, Any]:
    """
    Process a message with Claude-3 model using the Anthropic API.
    This implementation uses the centralized API request handler for improved
    error handling, automatic retries, and fallback capabilities.
    
    Args:
        message: The message to process
        
    Returns:
        Dict containing response, model name, and error status
    """
    logger.info(f"Processing message with Claude 3: {message[:50]}...")
    start_time = time.time()
    
    # Update usage counter
    update_model_usage('claude3')
    
    try:
        # Import the API request handler
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from api_request_handler import anthropic_request, model_request_with_fallback
        
        # Format the message into the expected structure
        formatted_messages = [{"role": "user", "content": message}]
        
        # Determine if this is a technical query for better fallback model selection
        is_technical = any(keyword in message.lower() for keyword in [
            "code", "python", "javascript", "programming", "function", "algorithm", "data structure",
            "api", "database", "sql", "json", "xml", "html", "css", "http", "request"
        ])
        query_type = "technical" if is_technical else "general"
        
        # Process with Claude with automatic fallback if it fails
        # The api_request_handler will automatically handle retries and fallbacks
        result = await model_request_with_fallback(
            primary_model="claude-3-haiku-20240307",
            request_function=anthropic_request,
            request_params={
                "messages": formatted_messages,
                "max_tokens": 800
            },
            query_type=query_type
        )
        
        # Check if the request was successful
        if result.get("status") == "success":
            response_text = result.get("content")
            model_used = result.get("model", "claude-3-haiku-20240307")
            
            # If a fallback model was used, note this in the response
            fallback_info = ""
            if result.get("model_info", {}).get("fallback_used"):
                primary = result["model_info"]["primary_model"]
                final = result["model_info"]["final_model"]
                fallback_info = f" (Fallback from {primary} to {final})"
            
            return {
                "response": response_text,
                "model": "claude3",
                "model_used": model_used + fallback_info,
                "quality_score": 0.85,
                "is_error": False,
                "processing_time": time.time() - start_time,
                "is_valid": True,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time(),
                "api_metadata": result.get("model_info", {})
            }
        else:
            # Handle empty or invalid response
            logger.error("Received empty or invalid response from Claude 3 API")
            return {
                "response": "I apologize, but I received an empty or invalid response from the Claude-3 model.",
                "model": "claude3",
                "model_used": "claude3-error",
                "is_error": True,
                "error": "Empty or invalid API response",
                "processing_time": time.time() - start_time,
                "is_valid": False,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time()
            }
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing message with Claude 3: {error_message}")
        
        # Check for specific error types to provide better responses
        if "credit balance is too low" in error_message.lower():
            response_text += " The API account has reached its usage limit. Please try again later."
        elif "rate limit" in error_message.lower():
            response_text += " The service is currently experiencing high demand. Please try again in a few moments."
        elif "api_key" in error_message.lower() or "apikey" in error_message.lower():
            response_text = "Error: Anthropic API key appears to be invalid or missing. Please check your API key configuration."
        
        return {
            "response": response_text,
            "model": "claude3",
            "model_used": "claude3-error",
            "is_error": True,
            "error": error_message,
            "processing_time": time.time() - start_time,
            "is_valid": False,
            "was_salvaged": False,
            "response_length": len(response_text),
            "timestamp": time.time()
        }

async def process_with_mistral7b(message: str) -> Dict[str, Any]:
    """
    Process a message with Mistral-7B model using the Mistral API.
    
    Args:
        message: The message to process
        
    Returns:
        Dict containing response, model name, and error status
    """
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logger.warning("No Mistral API key found when trying to process with Mistral-7B")
        return {
            "response": "Error: Mistral API key not found",
            "model": "mistral7b",
            "is_error": True,
            "error": "API key missing"
        }
    
    # Update usage counter
    update_model_usage('mistral7b')
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "mistral-large-latest",  # Use the latest large model
        "messages": [
            {"role": "user", "content": message}
        ],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.95
    }
    
    try:
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            # Extract the message content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return {
                    "response": content,
                    "model": "mistral7b",
                    "quality_score": 0.85,
                    "is_error": False
                }
            else:
                logger.warning(f"Unexpected response format from Mistral API: {result}")
                return {
                    "response": "Error: Unexpected response format from Mistral API",
                    "model": "mistral7b",
                    "is_error": True,
                    "error": "Unexpected response format"
                }
    except Exception as e:
        logger.error(f"Error processing message with Mistral-7B: {str(e)}")
        return {
            "response": f"Error processing with Mistral-7B: {str(e)}",
            "model": "mistral7b",
            "is_error": True,
            "error": str(e)
        }

async def process_with_cohere(message: str) -> Dict[str, Any]:
    """
    Process a message with Cohere's models using their API.
    
    Args:
        message: The message to process
        
    Returns:
        Dict containing response, model name, and error status
    """
    api_key = os.environ.get("COHERE_API_KEY") or os.environ.get("COHERE_TRIAL_KEY")
    if not api_key:
        logger.warning("No Cohere API key found when trying to process with Cohere")
        return {
            "response": "Error: Cohere API key not found",
            "model": "cohere",
            "is_error": True,
            "error": "API key missing"
        }
    
    # Update usage counter
    update_model_usage('cohere')
    
    url = "https://api.cohere.ai/v1/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": message,
        "model": "command",  # Using the Command model
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            
            # Extract the response text
            if 'text' in result:
                return {
                    "response": result['text'],
                    "model": "cohere",
                    "quality_score": 0.82,
                    "is_error": False
                }
            else:
                logger.warning(f"Unexpected response format from Cohere API: {result}")
                return {
                    "response": "Error: Unexpected response format from Cohere API",
                    "model": "cohere",
                    "is_error": True,
                    "error": "Unexpected response format"
                }
    except Exception as e:
        logger.error(f"Error processing message with Cohere: {str(e)}")
        return {
            "response": f"Error processing with Cohere: {str(e)}",
            "model": "cohere",
            "is_error": True,
            "error": str(e)
        }

async def process_with_gpt4(message: str) -> Dict[str, Any]:
    """
    Process a message with the best available OpenAI model, starting with GPT-4o.
    
    The function implements a fallback chain: gpt-4o → gpt-4o-mini → gpt-3.5-turbo
    to ensure the highest quality response is returned, with graceful degradation
    if higher-capability models are unavailable or have quota limitations.
    
    Args:
        message: The user message to process
        
    Returns:
        Dict containing the model's response and metadata
    """
    logger.info(f"Processing message with GPT-4: {message[:50]}...")
    
    start_time = time.time()
    
    # Update usage counter
    update_model_usage('gpt4')
    
    try:
        # Import the API request handler
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from api_request_handler import openai_request, model_request_with_fallback
        
        # Set up message format with system instruction
        messages = [{
            "role": "system",
            "content": "You are a helpful, accurate, and thoughtful assistant that provides detailed, factual information. Answer in a comprehensive but direct manner."
        }, {
            "role": "user",
            "content": message
        }]
        
        # Determine query type for better fallback model selection
        is_technical = any(keyword in message.lower() for keyword in [
            "code", "python", "javascript", "programming", "function", "algorithm", "data structure",
            "api", "database", "sql", "json", "xml", "html", "css", "http", "request"
        ])
        is_creative = any(keyword in message.lower() for keyword in [
            "creative", "story", "write", "poem", "fiction", "imagine", "design", "art", "music"
        ])
        is_analytical = any(keyword in message.lower() for keyword in [
            "analyze", "compare", "contrast", "evaluate", "assess", "examine", "review", "study"
        ])
        
        # Determine the query type based on keywords
        if is_technical:
            query_type = "technical"
        elif is_creative:
            query_type = "creative"
        elif is_analytical:
            query_type = "analytical"
        else:
            query_type = "general"
        
        # Log query type for debugging
        logger.info(f"Query type determined as: {query_type}")
        
        # Process with GPT-4 with automatic fallback if it fails
        # The api_request_handler will handle retries and fallbacks
        result = await model_request_with_fallback(
            primary_model="gpt-4o",  # Start with the best model
            request_function=openai_request,
            request_params={
                "messages": messages,
                "max_tokens": 3000,
                "temperature": 0.7
            },
            fallback_models=["gpt-4", "gpt-3.5-turbo"],  # Explicit fallback chain
            query_type=query_type
        )
        
        # Check if the request was successful
        if result.get("status") == "success":
            response_text = result.get("content")
            model_used = result.get("model", "gpt-4o")
            
            # If a fallback model was used, note this in the response
            fallback_info = ""
            if result.get("model_info", {}).get("fallback_used"):
                primary = result["model_info"]["primary_model"]
                final = result["model_info"]["final_model"]
                fallback_info = f" (Fallback from {primary} to {final})"
            
            # Evaluate the quality of the response
            quality_evaluation = evaluate_response_quality(response_text, message)
            quality_score = quality_evaluation.get("overall_score", 0.9)
            
            # Return the successful response with metadata
            return {
                "response": response_text,
                "model": "gpt4",
                "model_used": model_used + fallback_info,
                "confidence": 0.95,
                "processing_time": time.time() - start_time,
                "quality_score": quality_score,
                "is_valid": True,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time(),
                "api_metadata": result.get("model_info", {})
            }
        # If we got here, there was an error with the request
        error_info = result.get("error", "Unknown error with API request")
        logger.error(f"Error processing with GPT-4: {error_info}")
        
        return {
            "response": f"I apologize, but I encountered an issue while processing your request. {error_info}",
            "model": "gpt4",
            "model_used": "none",
            "confidence": 0.0,
            "error": error_info,
            "is_error": True,
            "processing_time": time.time() - start_time,
            "quality_score": 0.0,
            "is_valid": False,
            "was_salvaged": False,
            "response_length": 0,
            "timestamp": time.time()
        }
    except Exception as e:
        # Handle any unexpected errors that weren't caught by the API handler
        error_msg = str(e)
        logger.error(f"Unexpected error in process_with_gpt4: {error_msg}")
        return {
            "response": f"I apologize, but I encountered an unexpected error: {error_msg}",
            "model": "gpt4",
            "model_used": "none",
            "is_error": True,
            "error": error_msg,
            "processing_time": time.time() - start_time,
            "is_valid": False,
            "was_salvaged": False,
            "response_length": 0,
            "timestamp": time.time()
        }

async def process_with_claude3(message: str) -> Dict[str, Any]:
    """
    Process a message with the Claude 3 model using the Anthropic API.
    
    Args:
        message: The user message to process
        
    Returns:
        Dict containing the model's response and metadata
    """
    logger.info(f"Processing message with Claude 3: {message[:50]}...")
    
    start_time = time.time()
    
    # Initialize response variables to avoid UnboundLocalError
    response = None
    response_text = "I apologize, but there was an issue connecting to the Claude-3 model."
    
    try:
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("Anthropic API key not found in environment variables")
            return {
                "response": "I'm sorry, but I cannot process your request at this time due to configuration issues. Please ensure the Anthropic API key is properly set.",
                "model": "claude3",
                "model_used": "none",
                "error": "API key not configured",
                "is_error": True,
                "is_valid": False,
                "was_salvaged": False,
                "timestamp": time.time()
            }
        
        # Initialize Anthropic client with API key
        # Use minimal configuration to avoid compatibility issues
        # Check if proxies are defined in environment variables
        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        
        # If proxies are configured, use httpx client with proxies
        if http_proxy or https_proxy:
            proxies = {}
            if http_proxy:
                proxies['http://'] = http_proxy
            if https_proxy:
                proxies['https://'] = https_proxy
            
            # Create HTTP client with proxies
            http_client = httpx.AsyncClient(proxies=proxies)
            client = AsyncAnthropic(api_key=api_key, http_client=http_client)
        else:
            # Simple initialization without proxies
            client = AsyncAnthropic(api_key=api_key)
        
        # Call the Anthropic API
        response = await client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            system="You are a helpful, accurate, and thoughtful assistant that provides detailed, factual information. Answer in a comprehensive but direct manner.",
            messages=[
                {"role": "user", "content": message}
            ]
        )
        
        # Check if response exists and has the expected structure
        if response and hasattr(response, 'content') and response.content and len(response.content) > 0:
            # Extract the response content
            response_text = response.content[0].text
            
            processing_time = time.time() - start_time
            
            return {
                "response": response_text,
                "model": "claude3",
                "model_used": "claude-3-opus-20240229",
                "confidence": 0.95,
                "processing_time": processing_time,
                "quality_score": QUALITY_FACTORS["claude3"] * 0.95,
                "is_valid": True,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time()
            }
        else:
            # Handle empty or invalid response
            logger.error("Received empty or invalid response from Claude 3 API")
            processing_time = time.time() - start_time
            
            return {
                "response": "I apologize, but I received an empty or invalid response from the Claude-3 model.",
                "model": "claude3",
                "model_used": "claude3-error",
                "is_error": True,
                "error": "Empty or invalid API response",
                "processing_time": processing_time,
                "is_valid": False,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time()
            }
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing message with Claude 3: {error_message}")
        processing_time = time.time() - start_time
        
        # Provide more specific error messages based on exception content
        if "credit balance is too low" in error_message.lower():
            response_text += " The API account has reached its usage limit. Please try again later."
        elif "rate limit" in error_message.lower():
            response_text += " The service is currently experiencing high demand. Please try again in a few moments."
        elif "api_key" in error_message.lower() or "apikey" in error_message.lower():
            response_text = "Error: Anthropic API key appears to be invalid or missing. Please check your API key configuration."
        else:
            response_text = f"Error processing Claude-3 request: {error_message}"
        
        return {
            "response": response_text,
            "model": "claude3",
            "model_used": "claude3-error",
            "error": error_message,
            "is_error": True,
            "is_valid": False,
            "was_salvaged": False,
            "confidence": 0.0,
            "processing_time": processing_time,
            "quality_score": 0.0,
            "response_length": len(response_text),
            "timestamp": time.time()
        }

async def process_with_mistral(message: str) -> Dict[str, Any]:
    """
    Process a message with the Mistral AI model using the Mistral API.
    
    This function handles communication with Mistral's La-Platforme API
    to generate responses using their large language models.
    
    Args:
        message: The user message to process
        
    Returns:
        Dict containing the model's response and metadata
    """
    logger.info(f"Processing message with Mistral: {message[:50]}...")
    
    start_time = time.time()
    
    # Update usage counter
    update_model_usage('mistral7b')
    
    try:
        # Import the API request handler
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from api_request_handler import mistral_request, model_request_with_fallback
        
        # Prepare messages with system instruction
        formatted_messages = [
            {"role": "system", "content": "You are a helpful, honest, and precise AI assistant called Minerva."},
            {"role": "user", "content": message}
        ]
        
        # Determine query type for better fallback model selection
        is_technical = any(keyword in message.lower() for keyword in [
            "code", "python", "javascript", "programming", "function", "algorithm", "data structure",
            "api", "database", "sql", "json", "xml", "html", "css", "http", "request"
        ])
        is_creative = any(keyword in message.lower() for keyword in [
            "creative", "story", "write", "poem", "fiction", "imagine", "design", "art", "music"
        ])
        is_mathematical = any(keyword in message.lower() for keyword in [
            "math", "equation", "calculation", "formula", "solve", "compute", "calculus", "algebra", "geometry"
        ])
        
        # Determine the query type based on keywords
        if is_technical:
            query_type = "technical"
        elif is_creative:
            query_type = "creative"
        elif is_mathematical:
            query_type = "mathematical"
        else:
            query_type = "general"
        
        # Process with Mistral with automatic fallback if it fails
        # The api_request_handler will handle retries and fallbacks
        result = await model_request_with_fallback(
            primary_model="mistral-large-latest",
            request_function=mistral_request,
            request_params={
                "messages": formatted_messages,
                "max_tokens": 1000,
                "temperature": 0.7
            },
            query_type=query_type
        )
        
        # Check if the request was successful
        if result.get("status") == "success":
            response_text = result.get("content")
            model_used = result.get("model", "mistral-large-latest")
            
            # If a fallback model was used, note this in the response
            fallback_info = ""
            if result.get("model_info", {}).get("fallback_used"):
                primary = result["model_info"]["primary_model"]
                final = result["model_info"]["final_model"]
                fallback_info = f" (Fallback from {primary} to {final})"
            
            # Return the successful response with metadata
            return {
                "response": response_text,
                "model": "mistral7b",
                "model_used": model_used + fallback_info,
                "confidence": 0.9,
                "processing_time": time.time() - start_time,
                "quality_score": 0.85,
                "is_valid": True,
                "was_salvaged": False,
                "response_length": len(response_text),
                "timestamp": time.time(),
                "api_metadata": result.get("model_info", {})
            }
        
        # If we got here, there was an error with the request
        if not result.get("content"):
            logger.error("Empty response from Mistral API")
            return {
                "response": "Error: Received empty response from Mistral API.",
                "model": "mistral7b",
                "error": "Empty response",
                "is_error": True,
                "is_valid": False,
                "processing_time": time.time() - start_time
            }
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Extract token usage if available
        usage = response_data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", len(message) // 4)  # Fallback to estimate
        completion_tokens = usage.get("completion_tokens", len(response_text) // 4)  # Fallback to estimate
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        
        return {
            "response": response_text,
            "model": "mistral7b",
            "model_used": "mistral-large-latest",
            "confidence": 0.9,  # Mistral large models are quite capable
            "processing_time": processing_time,
            "quality_score": 0.9,  # Assumed high quality
            "is_valid": True,
            "was_salvaged": False,
            "tokens": {"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens}
        }
        
    except Exception as e:
        logger.error(f"Error processing message with Mistral: {str(e)}")
        processing_time = time.time() - start_time
        
        return {
            "response": f"Error: Failed to process message with Mistral: {str(e)}",
            "model": "mistral7b",
            "model_used": "mistral-error",
            "error": str(e),
            "is_error": True,
            "is_valid": False,
            "was_salvaged": False,
            "processing_time": processing_time,
            "quality_score": 0.0
        }

async def process_with_llama2(message: str) -> Dict[str, Any]:
    """Process a message with the Llama 2 model."""
    logger.info(f"Processing message with Llama 2: {message[:50]}...")
    await asyncio.sleep(0.5 + (random.random() * 0.7))
    
    query_type = "general"
    if any(term in message.lower() for term in ["code", "function", "programming"]):
        query_type = "code"
    elif any(term in message.lower() for term in ["math", "calculate", "equation"]):
        query_type = "math"
    
    template = random.choice(RESPONSE_TEMPLATES[query_type])
    
    if query_type == "code":
        code_key = next((k for k in CODE_SAMPLES.keys() if k in message.lower()), random.choice(list(CODE_SAMPLES.keys())))
        details = CODE_SAMPLES[code_key]
    else:
        sentences = [
            f"Here's what I know about {' '.join(message.split()[:3])}:",
            f"There are a few important points to consider.",
            f"This information should help address your question."
        ]
        details = "\n\n".join(sentences)
    
    explanation = MODEL_EXPLANATIONS["llama2"](message)
    response = template.format(details=details, explanation=explanation)
    
    return {
        "response": response,
        "model": "llama2",
        "confidence": 0.78 + (random.random() * 0.15),
        "processing_time": 0.5 + (random.random() * 0.7),
        "quality_score": QUALITY_FACTORS["llama2"] * (0.9 + (random.random() * 0.2))
    }

def check_gpt4all_availability() -> bool:
    """
    Check if GPT4All is available by verifying model files exist.
    
    Returns:
        True if the model is available and can be loaded, False otherwise
    """
    try:
        # Check if the GPT4All library is installed
        import importlib
        gpt4all_spec = importlib.util.find_spec('gpt4all')
        if gpt4all_spec is None:
            logger.warning("GPT4All Python library not installed")
            return False
            
        # Modern GPT4All uses ~/.cache/gpt4all directory
        from pathlib import Path
        model_dir = str(Path.home() / ".cache" / "gpt4all")
        if not os.path.exists(model_dir):
            logger.warning(f"GPT4All model directory not found: {model_dir}")
            return False
            
        # Modern GPT4All uses .gguf files, not .bin files
        model_files = [f for f in os.listdir(model_dir) if f.endswith(".gguf")]
        if not model_files:
            logger.warning("No GPT4All model files found")
            return False
            
        logger.info(f"GPT4All is available with models: {', '.join(model_files)}")
        return True
    except Exception as e:
        logger.error(f"Error checking GPT4All availability: {str(e)}")
        return False

def process_with_gpt4all_with_usage(message: str, system_prompt: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Process a message with the GPT4All model using a real local LLM with usage tracking.
    
    Args:
        message: The message to process
        system_prompt: Optional system prompt to guide the model
        
    Returns:
        Tuple containing:
            - The model's response text
            - Usage information dict with estimated input_tokens and output_tokens
    """
    try:
        logger.info(f"Processing message with GPT4All: {message[:50]}...")
        
        # Try to import and use the actual GPT4All library
        try:
            import gpt4all
            
            # GPT4All now downloads models to ~/.cache/gpt4all/ by default
            from pathlib import Path
            default_path = str(Path.home() / ".cache" / "gpt4all")
            model_path = os.environ.get('GPT4ALL_MODEL_PATH', default_path)
            # Updated to use the newer GGUF model format that's available
            model_name = os.environ.get('GPT4ALL_MODEL', 'Llama-3.2-1B-Instruct-Q4_0.gguf')
            
            # Log the model path so we can debug
            logger.info(f"Looking for GPT4All model at: {model_path}/{model_name}")
            
            # Create model instance with appropriate settings
            gpt = gpt4all.GPT4All(model_name=model_name, model_path=model_path)
            
            # Format the prompt with system instructions if provided
            full_prompt = message
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser query: {message}"
                
            # Generate response with appropriate parameters
            response = gpt.generate(full_prompt, 
                                   max_tokens=512,
                                   temp=0.7,
                                   top_k=40,
                                   top_p=0.9)
            
            # Update usage statistics
            update_model_usage("gpt4all")
            
            # For local models like GPT4All, we need to estimate token counts
            # since they don't provide this information directly
            # Estimate based on input and output text length (roughly 3/4 tokens per word)
            input_tokens = len(full_prompt.split()) if full_prompt else 0
            output_tokens = len(response.split()) if response else 0
            
            # Apply a multiplier to convert words to tokens (approximation)
            estimated_input_tokens = int(input_tokens * 1.33)
            estimated_output_tokens = int(output_tokens * 1.33)
            
            # Create usage info dictionary
            usage_info = {
                'input_tokens': estimated_input_tokens,
                'output_tokens': estimated_output_tokens,
                'total_tokens': estimated_input_tokens + estimated_output_tokens,
                'model': 'gpt4all',
                'estimated': True  # Flag to indicate these are estimates
            }
            
            logger.info(f"GPT4All usage (estimated): {estimated_input_tokens} input / {estimated_output_tokens} output tokens")
            
            return response, usage_info
            
        except ImportError as e:
            logger.error(f"GPT4All library not available: {str(e)}")
            raise ImportError(f"GPT4All library not installed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error processing with GPT4All: {str(e)}")
            raise Exception(f"GPT4All processing error: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to process with GPT4All: {str(e)}")
        raise Exception(f"GPT4All processing failed: {str(e)}")


# Backward compatibility wrapper
def process_with_gpt4all(message: str, system_prompt: str = None) -> str:
    """Legacy wrapper for process_with_gpt4all_with_usage
    
    Returns just the response text for backward compatibility
    """
    response_text, _ = process_with_gpt4all_with_usage(message, system_prompt)
    return response_text


async def process_with_falcon(message: str) -> Dict[str, Any]:
    """Process a message with the Falcon model."""
    logger.info(f"Processing message with Falcon: {message[:50]}...")
    await asyncio.sleep(0.6 + (random.random() * 0.7))
    
    query_type = "general"
    if any(term in message.lower() for term in ["code", "function", "programming"]):
        query_type = "code"
    elif any(term in message.lower() for term in ["math", "calculate", "equation"]):
        query_type = "math"
    
    template = random.choice(RESPONSE_TEMPLATES[query_type])
    
    if query_type == "code":
        code_key = next((k for k in CODE_SAMPLES.keys() if k in message.lower()), random.choice(list(CODE_SAMPLES.keys())))
        details = CODE_SAMPLES[code_key]
    else:
        sentences = [
            f"In considering {' '.join(message.split()[:3])}, I'd like to offer a creative perspective:",
            f"There are several interesting dimensions to explore here.",
            f"This approach reveals unique insights that might be valuable.",
            f"Looking at this from multiple angles enhances our understanding."
        ]
        details = "\n\n".join(sentences)
    
    explanation = MODEL_EXPLANATIONS["falcon"](message)
    response = template.format(details=details, explanation=explanation)
    
    return {
        "response": response,
        "model": "falcon",
        "confidence": 0.75 + (random.random() * 0.15),
        "processing_time": 0.6 + (random.random() * 0.7),
        "quality_score": QUALITY_FACTORS["falcon"] * (0.85 + (random.random() * 0.25))
    }

async def process_with_gpt4o(message: str) -> Dict[str, Any]:
    """
    Process a message with GPT-4o model using the OpenAI API.
    
    This function handles communication with OpenAI's high-capability GPT-4o model,
    which offers improved reasoning, coding, and multimodal capabilities.
    
    Args:
        message: The user message to process
        
    Returns:
        Dict containing the model's response and metadata
    """
    logger.info(f"Processing with GPT-4o: {message[:50]}...")
    await asyncio.sleep(0.5 + (random.random() * 0.3))  # Simulate API latency
    
    try:
        # Get OpenAI API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found in environment variables")
            return {
                "response": "Error: OpenAI API key not configured.",
                "model": "gpt-4o",
                "error": True
            }
        
        # Create OpenAI client and make a real API call
        client = create_openai_client(api_key)
        logger.info("Created OpenAI client, making API call to GPT-4o...")
        
        start_time = time.time()
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are Minerva, an AI assistant that is helpful, harmless, and honest."},
                {"role": "user", "content": message}
            ],
            max_tokens=1500,
            temperature=0.7
        )
        elapsed_time = time.time() - start_time
        
        # Extract the response text
        if not response or not response.choices or len(response.choices) == 0:
            logger.error("Empty response from GPT-4o API")
            return {
                "response": "Error: Received empty response from GPT-4o API.",
                "model": "gpt-4o",
                "error": True
            }
        
        response_text = response.choices[0].message.content
        
        # Calculate API response time 
        processing_time = elapsed_time
        
        # Log successful API call
        logger.info(f"Successfully received GPT-4o response of {len(response_text)} characters")
        
        # Extract token usage if available in the response
        try:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            logger.info(f"GPT-4o usage: {prompt_tokens} prompt tokens, {completion_tokens} completion tokens")
        except (AttributeError, TypeError):
            # Fallback if usage stats aren't available
            prompt_tokens = len(message) // 4  # Rough estimate
            completion_tokens = len(response_text) // 4  # Rough estimate
            total_tokens = prompt_tokens + completion_tokens
        
        return {
            "response": response_text,
            "model": "gpt-4o",
            "confidence": 0.95,  # GPT-4o typically has high confidence
            "processing_time": processing_time,
            "quality_score": 0.95,  # GPT-4o typically produces high quality responses
            "tokens": {"prompt": prompt_tokens, "completion": completion_tokens, "total": total_tokens}
        }
        
    except Exception as e:
        logger.error(f"Error in process_with_gpt4o: {str(e)}")
        # Fall back to simulated response in case of error
        return {
            "response": f"I encountered an error while processing your request. Please try again or rephrase your question. (Error: {str(e)})",
            "model": "gpt-4o",
            "error": True,
            "error_message": str(e)
        }

# Map of model names to processor functions
MODEL_PROCESSORS = {
    "gpt4": process_with_gpt4,
    "gpt4o": process_with_gpt4o,  # Add the new GPT-4o processor
    "claude3": process_with_claude3,
    "mistral7b": process_with_mistral,
    "llama2": process_with_llama2,
    "gpt4all": process_with_gpt4all,
    "falcon": process_with_falcon
}

def register_model_processors(coordinator):
    """
    Register all model processors with the MultiAICoordinator.
    
    Args:
        coordinator: The MultiAICoordinator instance
        
    Returns:
        None
    """
    for model_name, processor_func in MODEL_PROCESSORS.items():
        model_config = CONFIG.get("models", {}).get(model_name, {})
        capabilities = model_config.get("capabilities", {})
        
        # Only register if the model is marked as active in config
        is_active = model_config.get("is_active", True)
        if is_active:
            logger.info(f"Registering {model_name} processor with coordinator")
            coordinator.register_model_processor(model_name, processor_func, capabilities)
        else:
            logger.info(f"Skipping registration of inactive model: {model_name}")
    
    logger.info(f"Successfully registered active model processors")

def get_available_models():
    """
    Get the list of available model names.
    
    Returns:
        List of model names
    """
    return list(MODEL_PROCESSORS.keys())

if __name__ == "__main__":
    # Simple test
    import asyncio
    
    async def test_models():
        test_message = "Write a Python function to calculate Fibonacci numbers"
        # Test just a few models for demonstration
        test_models = ["gpt4", "claude3", "mistral7b"]
        
        for model_name in test_models:
            if model_name in MODEL_PROCESSORS:
                processor = MODEL_PROCESSORS[model_name]
                try:
                    print(f"\n===== TESTING {model_name.upper()} =====")
                    result = await processor(test_message)
                    
                    # Print model information
                    model_used = result.get("model_used", "Unknown")
                    print(f"Model used: {model_used}")
                    
                    # Print confidence (default to 0.0 if not present)
                    confidence = result.get("confidence", 0.0)
                    if isinstance(confidence, (int, float)):
                        print(f"Confidence: {confidence:.2f}")
                    else:
                        print(f"Confidence: {confidence}")
                    
                    # Print quality score (default to 0.0 if not present)
                    quality = result.get("quality_score", 0.0)
                    if isinstance(quality, (int, float)):
                        print(f"Quality: {quality:.2f}")
                    else:
                        print(f"Quality: {quality}")
                    
                    # Print whether there was an error
                    is_error = result.get("is_error", False)
                    print(f"Error: {is_error}")
                    
                    # Print API metadata if available
                    if "api_metadata" in result:
                        print(f"API Metadata: {result['api_metadata']}")
                    
                    # Print response (truncated to 200 chars)
                    response_text = result.get("response", "No response text")
                    print(f"Response:\n{response_text[:200]}..." if len(response_text) > 200 else f"Response:\n{response_text}")
                    
                except Exception as e:
                    print(f"Error testing {model_name}: {str(e)}")
    
    asyncio.run(test_models())
