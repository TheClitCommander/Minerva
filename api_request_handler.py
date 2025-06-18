"""
Universal API Request Handler for Minerva

This module provides a centralized system for handling API requests to various AI providers
with automatic retries, fallback mechanisms, and comprehensive logging.
"""

import os
import time
import uuid
import logging
import httpx
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api_requests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_request_handler")

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Define a universal API request function with error handling
async def api_request(
    url: str, 
    method: str = "POST", 
    headers: Optional[Dict[str, str]] = None, 
    data: Optional[Dict[str, Any]] = None, 
    max_retries: int = 3, 
    timeout: int = 30, 
    fallback_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an HTTP request to an API with built-in retry and fallback logic.

    Args:
        url (str): The primary API endpoint URL.
        method (str): HTTP method ("GET" or "POST").
        headers (dict): Headers for the request.
        data (dict): Payload data for the request.
        max_retries (int): Maximum number of retries if request fails.
        timeout (int): Request timeout in seconds.
        fallback_url (str): Optional fallback API URL in case of failure.

    Returns:
        dict: API response data or error message.
    """
    retries = 0
    last_error = None
    start_time = time.time()
    
    while retries < max_retries:
        try:
            logger.info(f"🔄 Attempt {retries+1}/{max_retries}: API Request to {url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method, 
                    url, 
                    headers=headers, 
                    json=data, 
                    timeout=timeout
                )
            
            end_time = time.time()
            request_time = end_time - start_time
            
            # Log the response time
            logger.info(f"⏱️ API Request to {url} took {request_time:.2f} seconds")

            # Check if response is valid
            if response.status_code == 200:
                logger.info(f"✅ API Request Successful: {url} | Status: {response.status_code}")
                return response.json()
            else:
                error_msg = f"⚠️ API Request Failed: {url} | Status: {response.status_code} | Response: {response.text}"
                logger.warning(error_msg)
                last_error = error_msg
        
        except httpx.RequestError as e:
            error_msg = f"❌ Request Error for {url}: {str(e)}"
            logger.error(error_msg)
            last_error = error_msg
        
        except Exception as e:
            error_msg = f"❌ Unexpected Error for {url}: {str(e)}"
            logger.error(error_msg)
            last_error = error_msg
        
        # Increment retry count and wait before retrying using exponential backoff
        retries += 1
        if retries < max_retries:
            backoff_time = 2 ** retries  # Exponential backoff
            logger.info(f"⏳ Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
            start_time = time.time()  # Reset start time for accurate measurement

    # If all retries failed, attempt fallback if provided
    if fallback_url and fallback_url != url:
        logger.info(f"🔄 Attempting Fallback API: {fallback_url}")
        return await api_request(fallback_url, method, headers, data, max_retries=1)

    # If everything failed, return error
    return {
        "error": f"API request failed after {max_retries} retries",
        "last_error": last_error,
        "status": "failed",
        "url": url
    }

async def api_request_with_context(
    model_name: str, 
    url: str, 
    method: str = "POST", 
    headers: Optional[Dict[str, str]] = None, 
    data: Optional[Dict[str, Any]] = None, 
    **kwargs
) -> Dict[str, Any]:
    """
    Enhanced API request that preserves model context information.
    
    Args:
        model_name (str): Name of the AI model being called.
        url (str): The API endpoint URL.
        method (str): HTTP method.
        headers (dict): Headers for the request.
        data (dict): Payload data for the request.
        **kwargs: Additional arguments for api_request.
        
    Returns:
        dict: API response with added context information.
    """
    # Create request context
    context = {
        "original_model": model_name,
        "timestamp": time.time(),
        "request_id": str(uuid.uuid4())
    }
    
    # Make the API request
    result = await api_request(url, method, headers, data, **kwargs)
    
    # Add context to the result
    if isinstance(result, dict):
        result["context"] = context
    else:
        logger.warning(f"⚠️ Could not add context to non-dict result: {result}")
        result = {
            "raw_result": result,
            "context": context
        }
    
    return result

# Tracking for model statistics
model_stats = {}

def update_model_stats(model_name: str, success: bool, response_time: float) -> None:
    """
    Update statistics for a specific model.
    
    Args:
        model_name (str): Name of the AI model.
        success (bool): Whether the request was successful.
        response_time (float): Time taken for the API request.
    """
    if model_name not in model_stats:
        model_stats[model_name] = {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_time": 0,
            "avg_time": 0,
            "error_types": {}
        }
    
    stats = model_stats[model_name]
    stats["requests"] += 1
    
    if success:
        stats["successes"] += 1
    else:
        stats["failures"] += 1
    
    stats["total_time"] += response_time
    stats["avg_time"] = stats["total_time"] / stats["requests"]

def update_error_stats(model_name: str, error_type: str) -> None:
    """
    Track specific error types for each model.
    
    Args:
        model_name (str): Name of the AI model.
        error_type (str): Type of error encountered.
    """
    if model_name not in model_stats:
        update_model_stats(model_name, False, 0)  # Initialize if not exists
        
    if error_type not in model_stats[model_name]["error_types"]:
        model_stats[model_name]["error_types"][error_type] = 0
        
    model_stats[model_name]["error_types"][error_type] += 1
    logger.warning(f"Error type '{error_type}' recorded for model '{model_name}'")

def get_model_stats() -> Dict[str, Dict[str, Any]]:
    """
    Get statistics for all models.
    
    Returns:
        dict: Statistics for all models.
    """
    return model_stats

def get_fastest_model(query_type: Optional[str] = None, min_successes: int = 5) -> Optional[str]:
    """
    Get the fastest model based on average response time.
    
    Args:
        query_type (str, optional): Type of query to consider.
        min_successes (int): Minimum number of successful requests required to consider a model.
        
    Returns:
        str: Name of the fastest model or None if no models meet criteria.
    """
    candidates = {}
    
    for model_name, stats in model_stats.items():
        # Only consider models with sufficient successful requests
        if stats["successes"] >= min_successes:
            candidates[model_name] = stats["avg_time"]
    
    if not candidates:
        return None
        
    # Return model with lowest average time
    return min(candidates.items(), key=lambda x: x[1])[0]

def get_most_reliable_model(query_type: Optional[str] = None, min_requests: int = 5) -> Optional[str]:
    """
    Get the most reliable model based on success rate.
    
    Args:
        query_type (str, optional): Type of query to consider.
        min_requests (int): Minimum number of total requests required to consider a model.
        
    Returns:
        str: Name of the most reliable model or None if no models meet criteria.
    """
    candidates = {}
    
    for model_name, stats in model_stats.items():
        # Only consider models with sufficient total requests
        if stats["requests"] >= min_requests:
            success_rate = stats["successes"] / stats["requests"]
            candidates[model_name] = success_rate
    
    if not candidates:
        return None
        
    # Return model with highest success rate
    return max(candidates.items(), key=lambda x: x[1])[0]

async def model_request_with_fallback(
    primary_model: str,
    request_function: callable,
    request_params: Dict[str, Any],
    fallback_models: Optional[List[str]] = None,
    query_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Make an API request to the primary model with automatic fallback to alternative models.
    
    Args:
        primary_model (str): Primary model to attempt first.
        request_function (callable): Function that makes the actual API request.
        request_params (dict): Parameters to pass to the request function.
        fallback_models (list): List of models to try if primary fails, in order of preference.
        query_type (str): Type of query being made (technical, creative, etc.)
        
    Returns:
        dict: API response data with metadata.
    """
    start_time = time.time()
    error_info = None
    models_tried = []
    
    # Try primary model first
    try:
        logger.info(f"Attempting request with primary model: {primary_model}")
        result = await request_function(model=primary_model, **request_params)
        
        # Check if the result indicates an error
        if not isinstance(result, dict) or result.get("status") == "failed" or "error" in result:
            error_info = result.get("error") if isinstance(result, dict) else "Unknown error"
            logger.warning(f"Primary model {primary_model} request failed: {error_info}")
            raise Exception(f"Primary model failed: {error_info}")
            
        # Success with primary model
        end_time = time.time()
        update_model_stats(primary_model, True, end_time - start_time)
        
        result["model_info"] = {
            "primary_model": primary_model,
            "models_tried": [primary_model],
            "final_model": primary_model,
            "response_time": end_time - start_time
        }
        
        return result
        
    except Exception as e:
        # Primary model failed, try fallbacks
        logger.error(f"Error with primary model {primary_model}: {str(e)}")
        update_model_stats(primary_model, False, time.time() - start_time)
        update_error_stats(primary_model, type(e).__name__)
        models_tried.append(primary_model)
    
    # If no fallback models specified, try to get them from the model selection system
    if not fallback_models:
        try:
            from web.multi_ai_coordinator import MultiAICoordinator
            coordinator = MultiAICoordinator.get_instance()
            fallback_models = [
                model for model in coordinator.model_processors.keys() 
                if model != primary_model
            ]
            
            # If we have a query type, use the enhanced fallback selection
            if query_type:
                # Estimate complexity based on request params
                complexity = 5  # Default medium complexity
                if "messages" in request_params:
                    # Estimate complexity based on message length if available
                    content = ""
                    for msg in request_params["messages"]:
                        if isinstance(msg, dict) and "content" in msg:
                            content += msg["content"]
                    complexity = min(10, max(1, len(content) // 500))
                
                best_fallback = coordinator.get_best_fallback_model(
                    primary_model, query_type, complexity
                )
                
                if best_fallback:
                    # Put the best fallback at the front of the list
                    fallback_models = [
                        model for model in fallback_models if model != best_fallback
                    ]
                    fallback_models.insert(0, best_fallback)
        except ImportError:
            logger.warning("Could not import MultiAICoordinator for fallback selection")
    
    # Try each fallback model
    for model in (fallback_models or []):
        if model in models_tried:
            continue
            
        models_tried.append(model)
        model_start_time = time.time()
        
        try:
            logger.info(f"Attempting request with fallback model: {model}")
            result = await request_function(model=model, **request_params)
            
            # Check if the result indicates an error
            if not isinstance(result, dict) or result.get("status") == "failed" or "error" in result:
                error_info = result.get("error") if isinstance(result, dict) else "Unknown error"
                logger.warning(f"Fallback model {model} request failed: {error_info}")
                update_model_stats(model, False, time.time() - model_start_time)
                update_error_stats(model, "API_Error")
                continue
                
            # Success with fallback model
            model_end_time = time.time()
            update_model_stats(model, True, model_end_time - model_start_time)
            
            result["model_info"] = {
                "primary_model": primary_model,
                "models_tried": models_tried,
                "final_model": model,
                "response_time": model_end_time - model_start_time,
                "total_time": time.time() - start_time,
                "fallback_used": True
            }
            
            # Log successful fallback
            logger.info(f"✅ Successfully used fallback model {model} after primary model {primary_model} failed")
            return result
            
        except Exception as e:
            # Fallback model also failed
            logger.error(f"Error with fallback model {model}: {str(e)}")
            update_model_stats(model, False, time.time() - model_start_time)
            update_error_stats(model, type(e).__name__)
    
    # All models failed
    error_response = {
        "error": "All models failed to process the request",
        "primary_error": error_info,
        "models_tried": models_tried,
        "status": "failed"
    }
    
    logger.error(f"❌ All models failed for request: {models_tried}")
    return error_response

# Model-specific API handlers

async def anthropic_request(messages: List[Dict[str, Any]], model: str = "claude-3-opus", max_tokens: int = 4000, **kwargs) -> Dict[str, Any]:
    """
    Send a request to Anthropic Claude API with standardized error handling and retries.
    
    Args:
        messages: List of message objects with role and content
        model: Claude model to use (default: "claude-3-opus")
        max_tokens: Maximum number of tokens to generate
        **kwargs: Additional parameters for the API
        
    Returns:
        dict: Standardized response with model output and metadata
    """
    try:
        from anthropic import AsyncAnthropic
        
        # Get API key from environment or config
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "Anthropic API key not found", "status": "failed"}
        
        # Determine model-specific URL (though Anthropic client handles this internally)
        model_endpoint = "api.anthropic.com/v1/messages"
        
        # Initialize client
        client = AsyncAnthropic(api_key=api_key)
        
        # Record start time for performance monitoring
        start_time = time.time()
        
        # Process Minerva's message format to Anthropic's format if needed
        anthropic_messages = messages
        if messages and isinstance(messages[0], dict) and "role" in messages[0]:
            # Already in the right format, but ensure compatibility
            anthropic_messages = []
            for msg in messages:
                role = msg["role"]
                # Convert OpenAI format to Anthropic if needed
                if role == "assistant":
                    anthropic_messages.append({"role": "assistant", "content": msg["content"]})
                elif role == "user":
                    anthropic_messages.append({"role": "user", "content": msg["content"]})
                elif role == "system":
                    # Anthropic handles system message differently, prepend to first user message
                    # Find the first user message
                    for i, m in enumerate(anthropic_messages):
                        if m["role"] == "user":
                            anthropic_messages[i]["content"] = f"System: {msg['content']}\n\nUser: {anthropic_messages[i]['content']}"
                            break
        
        # Make the API call
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=anthropic_messages,
            **kwargs
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Update statistics
        update_model_stats(model, True, response_time)
        
        # Format response in a standardized way
        result = {
            "content": response.content[0].text,
            "model": model,
            "response_time": response_time,
            "status": "success",
            "model_id": response.id,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Anthropic API request: {str(e)}")
        update_error_stats(model, type(e).__name__)
        return {
            "error": str(e),
            "status": "failed",
            "model": model
        }

async def openai_request(messages: List[Dict[str, Any]], model: str = "gpt-4o", max_tokens: int = 4000, **kwargs) -> Dict[str, Any]:
    """
    Send a request to OpenAI API with standardized error handling and retries.
    
    Args:
        messages: List of message objects with role and content
        model: OpenAI model to use (default: "gpt-4o")
        max_tokens: Maximum number of tokens to generate
        **kwargs: Additional parameters for the API
        
    Returns:
        dict: Standardized response with model output and metadata
    """
    try:
        from openai import AsyncOpenAI
        
        # Get API key from environment or config
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OpenAI API key not found", "status": "failed"}
        
        # Initialize client
        client = AsyncOpenAI(api_key=api_key)
        
        # Record start time for performance monitoring
        start_time = time.time()
        
        # Make the API call
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Update statistics
        update_model_stats(model, True, response_time)
        
        # Format response in a standardized way
        result = {
            "content": response.choices[0].message.content,
            "model": model,
            "response_time": response_time,
            "status": "success",
            "model_id": response.id,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in OpenAI API request: {str(e)}")
        update_error_stats(model, type(e).__name__)
        return {
            "error": str(e),
            "status": "failed",
            "model": model
        }

async def mistral_request(messages: List[Dict[str, Any]], model: str = "mistral-large-latest", max_tokens: int = 4000, **kwargs) -> Dict[str, Any]:
    """
    Send a request to Mistral API with standardized error handling and retries.
    
    Args:
        messages: List of message objects with role and content
        model: Mistral model to use (default: "mistral-large-latest")
        max_tokens: Maximum number of tokens to generate
        **kwargs: Additional parameters for the API
        
    Returns:
        dict: Standardized response with model output and metadata
    """
    try:
        from mistralai.client import MistralAsyncClient
        from mistralai.models.chat_completion import ChatMessage
        
        # Get API key from environment or config
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            return {"error": "Mistral API key not found", "status": "failed"}
        
        # Initialize client
        client = MistralAsyncClient(api_key=api_key)
        
        # Format messages for Mistral
        mistral_messages = []
        for msg in messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                mistral_messages.append(ChatMessage(role=msg["role"], content=msg["content"]))
        
        # Record start time for performance monitoring
        start_time = time.time()
        
        # Make the API call
        response = await client.chat(
            model=model,
            messages=mistral_messages,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Update statistics
        update_model_stats(model, True, response_time)
        
        # Format response in a standardized way
        result = {
            "content": response.choices[0].message.content,
            "model": model,
            "response_time": response_time,
            "status": "success",
            "model_id": response.id,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Mistral API request: {str(e)}")
        update_error_stats(model, type(e).__name__)
        return {
            "error": str(e),
            "status": "failed",
            "model": model
        }

async def process_with_best_model(messages: List[Dict[str, Any]], query_type: str = "general", preferred_model: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a request with the best available model based on query type and performance metrics.
    Uses the model selection system from MultiAICoordinator if available.
    
    Args:
        messages: List of message objects to send to the model
        query_type: Type of query (technical, creative, analytical, etc.)
        preferred_model: Optional preferred model to try first
        
    Returns:
        dict: Standardized response with model output and metadata
    """
    # Get models based on priority
    primary_model = preferred_model
    
    # If no preferred model specified, try to use the model selection system
    if not primary_model:
        try:
            # Try to use the model selection system
            from web.multi_ai_coordinator import MultiAICoordinator
            
            coordinator = MultiAICoordinator.get_instance()
            # Extract the actual query from messages
            query = ""
            for msg in messages:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    query += msg["content"]
                    
            # Get model selection decision
            decision = coordinator._model_selection_decision("default_user", query)
            models_to_use = decision.get("models_to_use", [])
            
            if models_to_use:
                primary_model = models_to_use[0]  # Use the highest priority model
        except ImportError:
            logger.warning("Could not import model selection system, using fallbacks")
    
    # If still no primary model, use performance metrics
    if not primary_model:
        # Choose based on reliability for technical queries, speed for other types
        if query_type == "technical":
            primary_model = get_most_reliable_model() or "gpt-4o"
        else:
            primary_model = get_fastest_model() or "claude-3-haiku"
    
    # Select appropriate request function based on model
    if primary_model.startswith("claude"):
        request_function = anthropic_request
    elif primary_model.startswith("gpt") or primary_model.startswith("text-davinci"):
        request_function = openai_request
    elif primary_model.startswith("mistral"):
        request_function = mistral_request
    else:
        # Default to OpenAI for unknown models
        request_function = openai_request
        primary_model = "gpt-4o"
    
    # Request with fallback logic
    return await model_request_with_fallback(
        primary_model=primary_model,
        request_function=request_function,
        request_params={"messages": messages, "max_tokens": 4000},
        query_type=query_type
    )

def get_most_reliable_model(query_type: Optional[str] = None) -> str:
    """
    Get the most reliable model based on success rate.
    
    Args:
        query_type (str, optional): Type of query to consider.
        
    Returns:
        str: Name of the most reliable model.
    """
    if not model_stats:
        return "unknown"
    
    # If we have performance data by query type in the future,
    # we can use that for more granular selection
    
    # For now, just return the model with the highest success rate
    best_model = max(
        model_stats.items(),
        key=lambda x: x[1]["successes"] / max(x[1]["requests"], 1)
    )[0]
    
    return best_model

def get_fastest_model(query_type: Optional[str] = None) -> str:
    """
    Get the fastest model based on average response time.
    
    Args:
        query_type (str, optional): Type of query to consider.
        
    Returns:
        str: Name of the fastest model.
    """
    if not model_stats:
        return "unknown"
    
    # Return the model with the lowest average response time
    # that has had at least 5 successful requests
    candidates = {
        name: stats for name, stats in model_stats.items() 
        if stats["successes"] >= 5
    }
    
    if not candidates:
        return "unknown"
    
    fastest_model = min(
        candidates.items(),
        key=lambda x: x[1]["avg_time"]
    )[0]
    
    return fastest_model
