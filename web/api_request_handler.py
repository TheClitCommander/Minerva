"""
Centralized API Request Handler for Minerva

This module provides a robust API request handling system with:
- Automatic retries with exponential backoff
- Comprehensive error handling
- Fallback mechanisms to alternative models/endpoints
- Detailed logging for monitoring and debugging
- Support for both URL-based API calls and direct function calls

Usage:
    from web.api_request_handler import api_request
    
    # For URL-based API calls
    response = await api_request(
        url="https://api.example.com/v1/generate",
        method="POST",
        headers={"Authorization": "Bearer your-api-key"},
        data={"prompt": "Hello, world!"},
        max_retries=3,
        timeout=30,
        fallback_url="https://fallback-api.example.com/generate"
    )
    
    # For function-based calls
    response = await api_request(
        primary_config={
            "function": your_primary_function,
            "params": {"param1": "value1", "param2": "value2"}
        },
        fallback_config={
            "function": your_fallback_function,
            "params": {"param1": "value1", "param2": "value2"}
        },
        max_retries=3,
        retry_delay=1.0,
        timeout=30
    )
"""

import asyncio
import inspect
import json
import logging
import time
import traceback
import os
import threading
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_request_handler")

# Global tracking of errors by model/endpoint
ERROR_TRACKING = {}

# Rate limit configuration for different models
# Format: model_name: {max_requests: int, window: int (seconds), last_request: timestamp, count: int}
RATE_LIMITS = {
    # OpenAI models
    "gpt-4o": {"max_requests": 100, "window": 60, "last_request": 0, "count": 0},
    "gpt-4": {"max_requests": 80, "window": 60, "last_request": 0, "count": 0},
    "gpt-3.5-turbo": {"max_requests": 150, "window": 60, "last_request": 0, "count": 0},
    
    # Anthropic models
    "claude-3": {"max_requests": 80, "window": 60, "last_request": 0, "count": 0},
    "claude-3-opus": {"max_requests": 60, "window": 60, "last_request": 0, "count": 0},
    "claude-3-sonnet": {"max_requests": 70, "window": 60, "last_request": 0, "count": 0},
    "claude-3-haiku": {"max_requests": 90, "window": 60, "last_request": 0, "count": 0},
    
    # Mistral models
    "mistral-large-latest": {"max_requests": 80, "window": 60, "last_request": 0, "count": 0},
    "mistral-medium-latest": {"max_requests": 100, "window": 60, "last_request": 0, "count": 0},
    "mistral-small-latest": {"max_requests": 120, "window": 60, "last_request": 0, "count": 0},
    
    # Default for any other model
    "default": {"max_requests": 60, "window": 60, "last_request": 0, "count": 0}
}

# Circuit breaker configuration for tracking API failures and disabling failing models
# Format: model_name: {failures: int, disabled_until: timestamp, total_failures: int, last_success: timestamp}
CIRCUIT_BREAKERS = {}

# Configuration for circuit breaker
CIRCUIT_BREAKER_CONFIG = {
    "failure_threshold": 3,       # Number of consecutive failures before disabling
    "cooldown_period": 300,      # Period to disable model in seconds (5 minutes)
    "half_open_timeout": 60,     # Time before testing a disabled model again (1 minute)
    "health_check_interval": 60  # Time between health checks for disabled models (1 minute)
}

# Lock for thread-safe access to rate limits and circuit breakers
rate_limit_lock = threading.RLock()
circuit_breaker_lock = threading.RLock()

class APIRequestError(Exception):
    """Custom exception for API request errors with detailed context."""
    def __init__(self, message, status_code=None, response=None, model=None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.model = model
        super().__init__(self.message)
        
    def __str__(self):
        details = []
        if self.model:
            details.append(f"Model: {self.model}")
        if self.status_code:
            details.append(f"Status: {self.status_code}")
        if self.response:
            # Limit response length to avoid huge error messages
            resp_str = str(self.response)
            if len(resp_str) > 500:
                resp_str = resp_str[:500] + "..."
            details.append(f"Response: {resp_str}")
            
        if details:
            return f"{self.message} ({', '.join(details)})"
        return self.message

def track_error(model_or_url: str, error_type: str) -> None:
    """
    Track errors by model/endpoint and error type to identify patterns
    
    Args:
        model_or_url: The model or URL that encountered an error
        error_type: The type of error encountered
    """
    if model_or_url not in ERROR_TRACKING:
        ERROR_TRACKING[model_or_url] = {}
    
    if error_type not in ERROR_TRACKING[model_or_url]:
        ERROR_TRACKING[model_or_url][error_type] = 1
    else:
        ERROR_TRACKING[model_or_url][error_type] += 1
    
    # Log the error
    logger.warning(f"Error type '{error_type}' recorded for model '{model_or_url}'")


def enforce_rate_limit(model_name: str) -> bool:
    """
    Check if the API request is within the rate limit for the specified model
    
    Args:
        model_name: The name of the AI model to check rate limits for
    
    Returns:
        bool: True if the request is allowed, False if it exceeds rate limits
    """
    # Use default limits if model not specifically configured
    with rate_limit_lock:
        limit_config = RATE_LIMITS.get(model_name, RATE_LIMITS["default"])
        now = time.time()
        
        # Reset counter if the time window has passed
        if now - limit_config["last_request"] > limit_config["window"]:
            limit_config["count"] = 0
            limit_config["last_request"] = now
        
        # Check if we've hit the rate limit
        if limit_config["count"] >= limit_config["max_requests"]:
            cooldown = limit_config["window"] - (now - limit_config["last_request"])
            cooldown = max(0.1, cooldown)  # Ensure positive cooldown time
            logger.warning(f"Rate limit hit for {model_name}. Cooling down for {cooldown:.2f} seconds.")
            # Don't increment the counter, just report the rate limit hit
            return False
        
        # Increment the request counter
        limit_config["count"] += 1
        return True


async def wait_for_rate_limit(model_name: str) -> None:
    """
    Wait until the rate limit cooldown expires for the specified model
    
    Args:
        model_name: The name of the AI model to wait for
    """
    with rate_limit_lock:
        limit_config = RATE_LIMITS.get(model_name, RATE_LIMITS["default"])
        now = time.time()
        
        # Calculate time to wait if rate limit is exceeded
        if limit_config["count"] >= limit_config["max_requests"]:
            cooldown = limit_config["window"] - (now - limit_config["last_request"])
            cooldown = max(0.1, cooldown)  # Ensure positive cooldown time
            logger.info(f"Waiting for rate limit cooldown on {model_name}: {cooldown:.2f} seconds")
            await asyncio.sleep(cooldown)
            
            # Reset the counter after waiting
            limit_config["count"] = 0
            limit_config["last_request"] = time.time()


def check_circuit_breaker(model_name: str) -> bool:
    """
    Check if a model is available or if the circuit breaker has been triggered
    
    Args:
        model_name: The name of the AI model to check
    
    Returns:
        bool: True if the model is available, False if it's been disabled by the circuit breaker
    """
    with circuit_breaker_lock:
        if model_name not in CIRCUIT_BREAKERS:
            return True  # Model is available if not in circuit breakers list
            
        breaker_status = CIRCUIT_BREAKERS[model_name]
        now = time.time()
        
        # If the model is disabled and the cooldown period hasn't expired
        if now < breaker_status.get("disabled_until", 0):
            # Check if it's time for a trial request (half-open state)
            time_since_disable = now - (breaker_status.get("disabled_until", 0) - CIRCUIT_BREAKER_CONFIG["cooldown_period"])
            
            if time_since_disable >= CIRCUIT_BREAKER_CONFIG["half_open_timeout"]:
                # Allow a test request in half-open state
                logger.info(f"Circuit breaker for {model_name} in half-open state, allowing test request")
                return True
                
            logger.warning(f"Circuit breaker triggered for {model_name}. Model disabled until {time.ctime(breaker_status.get('disabled_until', 0))}")
            return False
            
        return True  # Available if cooldown period has expired


def update_circuit_breaker(model_name: str, success: bool) -> None:
    """
    Update the circuit breaker status after an API request
    
    Args:
        model_name: The name of the AI model
        success: Whether the API request was successful
    """
    with circuit_breaker_lock:
        now = time.time()
        
        # Initialize circuit breaker for this model if not exists
        if model_name not in CIRCUIT_BREAKERS:
            CIRCUIT_BREAKERS[model_name] = {
                "failures": 0,
                "disabled_until": 0,
                "total_failures": 0,
                "last_success": now if success else 0
            }
        
        breaker = CIRCUIT_BREAKERS[model_name]
        
        if success:
            # Reset failure count on success
            breaker["failures"] = 0
            breaker["last_success"] = now
            
            # If the model was in a disabled state and is now successful, log recovery
            if breaker["disabled_until"] > 0 and now >= breaker["disabled_until"]:
                logger.info(f"Circuit breaker for {model_name} has reset. Model is now available.")
                breaker["disabled_until"] = 0
        else:
            # Increment failure counters
            breaker["failures"] += 1
            breaker["total_failures"] += 1
            
            # Check if we've hit the failure threshold
            if breaker["failures"] >= CIRCUIT_BREAKER_CONFIG["failure_threshold"]:
                # Disable the model for the configured cooldown period
                breaker["disabled_until"] = now + CIRCUIT_BREAKER_CONFIG["cooldown_period"]
                logger.warning(f"Circuit breaker triggered for {model_name} after {breaker['failures']} consecutive failures. Disabled until {time.ctime(breaker['disabled_until'])}")


async def health_check_models() -> None:
    """
    Periodically check the health of disabled models by sending a test request
    This runs in a background task to automatically recover models when they're back online
    """
    while True:
        try:
            disabled_models = []
            
            # Get a list of currently disabled models
            with circuit_breaker_lock:
                now = time.time()
                for model_name, breaker in CIRCUIT_BREAKERS.items():
                    if breaker.get("disabled_until", 0) > now:
                        disabled_models.append(model_name)
            
            # Attempt health checks for disabled models
            for model_name in disabled_models:
                # This would actually call the API with a simple test request
                # For now, we'll just log that we would do a health check
                logger.info(f"Performing health check for disabled model: {model_name}")
                
                # TODO: In a real implementation, send a very small test request to the API
                # If successful, update the circuit breaker to re-enable the model
            
            # Wait before the next health check cycle
            await asyncio.sleep(CIRCUIT_BREAKER_CONFIG["health_check_interval"])
            
        except Exception as e:
            logger.error(f"Error in health check background task: {str(e)}")
            await asyncio.sleep(CIRCUIT_BREAKER_CONFIG["health_check_interval"])

async def _execute_function(config: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """
    Executes a function with the given parameters within a timeout
    
    Args:
        config: Dictionary containing the function and its parameters
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary with execution results
    """
    function = config["function"]
    params = config.get("params", {})
    
    try:
        # Check if the function is async
        if inspect.iscoroutinefunction(function):
            # Execute async function with timeout
            result = await asyncio.wait_for(function(**params), timeout=timeout)
        else:
            # Execute sync function in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: function(**params)
            )
        
        # Handle different return formats
        if isinstance(result, dict) and "success" in result:
            return result
        else:
            return {"success": True, "data": result}
            
    except asyncio.TimeoutError:
        return {
            "success": False, 
            "error": f"Function execution timed out after {timeout} seconds"
        }
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in function execution: {str(e)}\n{error_trace}")
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace
        }

async def _execute_url_request(url: str, method: str, headers: Dict[str, str], 
                              data: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """
    Executes an HTTP request to the specified URL
    
    Args:
        url: The URL to send the request to
        method: The HTTP method to use
        headers: The HTTP headers to include
        data: The data payload to send
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary with execution results
    """
    try:
        # Import httpx here to avoid dependency issues
        try:
            import httpx
        except ImportError:
            logger.error("httpx library not installed. Install with: pip install httpx")
            return {"success": False, "error": "httpx library not installed"}
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=data)
            else:  # Default to POST
                response = await client.post(url, headers=headers, json=data)
            
            # Check if the request was successful
            if response.status_code < 400:
                try:
                    # Try to parse as JSON first
                    return {"success": True, "data": response.json()}
                except:
                    # If not JSON, return text
                    return {"success": True, "data": response.text}
            else:
                error_message = f"Error code: {response.status_code}"
                try:
                    error_content = response.json()
                    error_message += f" - {error_content}"
                except:
                    error_content = response.text
                    error_message += f" - {error_content}"
                    
                return {
                    "success": False,
                    "error": error_message,
                    "status_code": response.status_code,
                    "response": error_content
                }
                
    except httpx.RequestError as e:
        logger.error(f"HTTP Request error: {str(e)}")
        return {"success": False, "error": f"HTTP Request error: {str(e)}"}
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Error in URL request execution: {str(e)}\n{error_trace}")
        return {
            "success": False,
            "error": str(e),
            "traceback": error_trace
        }

async def api_request(
    url: Optional[str] = None,
    method: str = "POST",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Dict[str, Any]] = None,
    primary_config: Optional[Dict[str, Any]] = None,
    fallback_config: Optional[Dict[str, Any]] = None,
    max_retries: int = 3,
    retry_delay: float = 0.5,
    timeout: int = 30,
    fallback_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Universal API request handler with error handling, retries, and fallback logic
    
    This function handles both URL-based API requests and direct function calls with
    consistent error handling and fallback mechanisms.
    
    Args:
        url: The URL to send the request to (for URL-based requests)
        method: The HTTP method to use (for URL-based requests)
        headers: The HTTP headers to include (for URL-based requests)
        data: The data payload to send (for URL-based requests)
        primary_config: Dictionary with function and parameters for primary processing
        fallback_config: Dictionary with function and parameters for fallback processing
        max_retries: Maximum number of retry attempts
        retry_delay: Initial delay between retries (increases exponentially)
        timeout: Maximum execution time in seconds
        fallback_url: URL to use as fallback if primary URL fails
        metadata: Additional metadata to include in the response
    
    Returns:
        Dictionary with the API response or error details
    """
    # Determine if we're using URL-based or function-based execution
    is_url_based = url is not None
    is_function_based = primary_config is not None
    
    if not is_url_based and not is_function_based:
        raise ValueError("Either url or primary_config must be provided")
    
    # Initialize model name for rate limiting and circuit breaker
    primary_model = model_name if model_name else (url if is_url_based else "primary_function")
    
    # If no explicit model name was provided, try to extract it from URL or function
    if not model_name:
        if is_url_based and url:
            # Try to extract a model name from the URL for better logging
            if "anthropic" in url:
                primary_model = "claude"
                if "claude-3" in url:
                    primary_model = "claude-3"
                    if "claude-3-opus" in url:
                        primary_model = "claude-3-opus"
                    elif "claude-3-sonnet" in url:
                        primary_model = "claude-3-sonnet"
                    elif "claude-3-haiku" in url:
                        primary_model = "claude-3-haiku"
            elif "openai" in url:
                primary_model = "gpt"
                if "gpt-4" in url:
                    primary_model = "gpt-4"
                    if "gpt-4o" in url:
                        primary_model = "gpt-4o"
                elif "gpt-3.5" in url:
                    primary_model = "gpt-3.5-turbo"
            elif "mistral" in url:
                primary_model = "mistral"
                if "mistral-large" in url:
                    primary_model = "mistral-large-latest"
                elif "mistral-medium" in url:
                    primary_model = "mistral-medium-latest"
                elif "mistral-small" in url:
                    primary_model = "mistral-small-latest"
        elif is_function_based and isinstance(primary_config, dict):
            # Try to get a better name from the function
            func = primary_config.get("function")
            if func:
                primary_model = func.__name__
    
    # Try primary execution with retries
    current_retry = 0
    current_delay = retry_delay
    
    while current_retry <= max_retries:
        try:
            # Check if this model is available (circuit breaker)
            if not check_circuit_breaker(primary_model):
                logger.warning(f"Circuit breaker active for {primary_model}. Skipping request.")
                
                # If this is the last retry, attempt fallback
                if current_retry == max_retries:
                    break
                
                # Otherwise increment retry counter and delay
                current_retry += 1
                await asyncio.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
                continue
                
            # Check rate limits before making the request
            if not enforce_rate_limit(primary_model):
                logger.warning(f"Rate limit exceeded for {primary_model}. Waiting before retry.")
                await wait_for_rate_limit(primary_model)
            
            logger.info(f"Attempting request with primary model: {primary_model}")
            
            # Execute the request
            if is_url_based:
                result = await _execute_url_request(url, method, headers, data, timeout)
            else:
                result = await _execute_function(primary_config, timeout)
            
            # If successful, update circuit breaker and return the result
            if result.get("success", False):
                # Mark the model as successful in circuit breaker
                update_circuit_breaker(primary_model, success=True)
                
                # Include metadata if provided
                if metadata:
                    result["api_metadata"] = metadata
                    
                # Add rate limit and circuit breaker status to metadata
                if "api_metadata" not in result:
                    result["api_metadata"] = {}
                result["api_metadata"]["stability_info"] = {
                    "model": primary_model,
                    "rate_limited": False,
                    "circuit_open": False
                }
                
                return result
            
            # Log the error and retry
            error_msg = result.get("error", "Unknown error")
            logger.warning(f"Primary model {primary_model} request failed: {error_msg}")
            
            # Track the error and update circuit breaker
            error_type = "API_Error"
            track_error(primary_model, error_type)
            update_circuit_breaker(primary_model, success=False)
            
            # Increment retry counter
            current_retry += 1
            
            # If we've exhausted retries, break out of the loop
            if current_retry > max_retries:
                break
                
            # Exponential backoff with jitter
            jitter = random.uniform(0, 0.1 * current_delay)
            sleep_time = current_delay + jitter
            current_delay *= 2
            
            # Sleep before retry
            await asyncio.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error with primary model {primary_model}: {str(e)}")
            
            # Track the error
            error_type = type(e).__name__
            track_error(primary_model, error_type)
            
            # Increment retry counter
            current_retry += 1
            
            # If we've exhausted retries, break out of the loop
            if current_retry > max_retries:
                break
                
            # Exponential backoff with jitter
            jitter = random.uniform(0, 0.1 * current_delay)
            sleep_time = current_delay + jitter
            current_delay *= 2
            
            # Sleep before retry
            await asyncio.sleep(sleep_time)
    
    # Primary execution failed, try fallback if available
    if is_url_based and fallback_url:
        # Extract model name from fallback URL for better tracking
        fallback_model = fallback_url
        if "anthropic" in fallback_url:
            fallback_model = "claude"
            if "claude-3" in fallback_url:
                fallback_model = "claude-3"
                if "claude-3-opus" in fallback_url:
                    fallback_model = "claude-3-opus"
                elif "claude-3-sonnet" in fallback_url:
                    fallback_model = "claude-3-sonnet"
                elif "claude-3-haiku" in fallback_url:
                    fallback_model = "claude-3-haiku"
        elif "openai" in fallback_url:
            fallback_model = "gpt"
            if "gpt-4" in fallback_url:
                fallback_model = "gpt-4"
                if "gpt-4o" in fallback_url:
                    fallback_model = "gpt-4o"
            elif "gpt-3.5" in fallback_url:
                fallback_model = "gpt-3.5-turbo"
        elif "mistral" in fallback_url:
            fallback_model = "mistral"
            if "mistral-large" in fallback_url:
                fallback_model = "mistral-large-latest"
            elif "mistral-medium" in fallback_url:
                fallback_model = "mistral-medium-latest"
            elif "mistral-small" in fallback_url:
                fallback_model = "mistral-small-latest"
                
        # Check if fallback model is available (circuit breaker)
        if not check_circuit_breaker(fallback_model):
            logger.warning(f"Circuit breaker active for fallback model {fallback_model}. Cannot proceed.")
            
            # Return a circuit breaker error response
            error_response = {
                "success": False,
                "error": f"All models unavailable. Primary and fallback circuit breakers active.",
                "fallback_used": True,
                "fallback_failed": True
            }
            
            # Add metadata
            if metadata:
                error_response["api_metadata"] = metadata
            error_response["api_metadata"] = error_response.get("api_metadata", {})
            error_response["api_metadata"]["stability_info"] = {
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "primary_circuit_open": True,
                "fallback_circuit_open": True
            }
            
            return error_response
        
        # Check rate limits for the fallback model
        if not enforce_rate_limit(fallback_model):
            logger.warning(f"Rate limit exceeded for fallback model {fallback_model}. Waiting.")
            await wait_for_rate_limit(fallback_model)
        
        logger.info(f"Attempting request with fallback model: {fallback_model}")
        try:
            result = await _execute_url_request(fallback_url, method, headers, data, timeout)
            if result.get("success", False):
                # Mark the fallback model as successful in circuit breaker
                update_circuit_breaker(fallback_model, success=True)
                
                # Update response with fallback info
                if "api_metadata" not in result:
                    result["api_metadata"] = {}
                result["fallback_used"] = True
                result["api_metadata"]["fallback_used"] = True
                result["api_metadata"]["stability_info"] = {
                    "primary_model": primary_model,
                    "fallback_model": fallback_model,
                    "primary_circuit_open": not check_circuit_breaker(primary_model),
                    "fallback_circuit_open": False
                }
                
                # Include user-provided metadata if any
                if metadata:
                    result["api_metadata"].update(metadata)
                    
                return result
            else:
                error_msg = result.get("error", "Unknown error")
                logger.warning(f"Fallback URL request failed: {error_msg}")
                
                # Track error and update circuit breaker
                track_error(fallback_model, "API_Error")
                update_circuit_breaker(fallback_model, success=False)
        except Exception as e:
            logger.error(f"Error with fallback URL: {str(e)}")
            
            # Track error and update circuit breaker
            track_error(fallback_model, type(e).__name__)
            update_circuit_breaker(fallback_model, success=False)
    
    elif is_function_based and fallback_config:
        fallback_model = "fallback_function"
        func = fallback_config.get("function")
        if func:
            fallback_model = func.__name__
        
        # Check if fallback model is available (circuit breaker)
        if not check_circuit_breaker(fallback_model):
            logger.warning(f"Circuit breaker active for fallback function {fallback_model}. Cannot proceed.")
            
            # Return a circuit breaker error response
            error_response = {
                "success": False,
                "error": f"All models unavailable. Primary and fallback circuit breakers active.",
                "fallback_used": True,
                "fallback_failed": True
            }
            
            # Add metadata
            if metadata:
                error_response["api_metadata"] = metadata
            error_response["api_metadata"] = error_response.get("api_metadata", {})
            error_response["api_metadata"]["stability_info"] = {
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "primary_circuit_open": True,
                "fallback_circuit_open": True
            }
            
            return error_response
            
        # Check rate limits for the fallback model
        if not enforce_rate_limit(fallback_model):
            logger.warning(f"Rate limit exceeded for fallback function {fallback_model}. Waiting.")
            await wait_for_rate_limit(fallback_model)
            
        logger.info(f"Attempting request with fallback model: {fallback_model}")
        try:
            result = await _execute_function(fallback_config, timeout)
            if result.get("success", False):
                # Mark the fallback model as successful in circuit breaker
                update_circuit_breaker(fallback_model, success=True)
                
                # Update response with fallback info
                if "api_metadata" not in result:
                    result["api_metadata"] = {}
                result["fallback_used"] = True
                result["api_metadata"]["fallback_used"] = True
                result["api_metadata"]["stability_info"] = {
                    "primary_model": primary_model,
                    "fallback_model": fallback_model,
                    "primary_circuit_open": not check_circuit_breaker(primary_model),
                    "fallback_circuit_open": False
                }
                
                # Include user-provided metadata if any
                if metadata:
                    result["api_metadata"].update(metadata)
                    
                return result
            else:
                error_msg = result.get("error", "Unknown error")
                logger.warning(f"Fallback model {fallback_model} request failed: {error_msg}")
                
                # Track error and update circuit breaker
                track_error(fallback_model, "API_Error")
                update_circuit_breaker(fallback_model, success=False)
        except Exception as e:
            logger.error(f"Error with fallback model {fallback_model}: {str(e)}")
            
            # Track error and update circuit breaker
            track_error(fallback_model, type(e).__name__)
            update_circuit_breaker(fallback_model, success=False)
    
    # If primary and fallback both failed, return error
    failed_models = [primary_model]
    fallback_model = None
    
    # Construct comprehensive error response with stability info
    error_response = {
        "success": False,
        "error": "All models failed to process the request",
        "retry_count": current_retry,
        "failed_models": failed_models,
        "api_metadata": {
            "stability_info": {
                "primary_model": primary_model,
                "primary_circuit_open": not check_circuit_breaker(primary_model),
                "max_retries_exceeded": True
            }
        }
    }
    
    # Add fallback model information if applicable
    if is_url_based and fallback_url:
        # Extract fallback model name from URL for reporting
        fallback_model = fallback_url
        if "anthropic" in str(fallback_url):
            fallback_model = "claude"
            if "claude-3" in str(fallback_url):
                fallback_model = "claude-3"
                if "claude-3-opus" in str(fallback_url):
                    fallback_model = "claude-3-opus"
                elif "claude-3-sonnet" in str(fallback_url):
                    fallback_model = "claude-3-sonnet"
                elif "claude-3-haiku" in str(fallback_url):
                    fallback_model = "claude-3-haiku"
        elif "openai" in str(fallback_url):
            fallback_model = "gpt"
            if "gpt-4" in str(fallback_url):
                fallback_model = "gpt-4"
                if "gpt-4o" in str(fallback_url):
                    fallback_model = "gpt-4o"
            elif "gpt-3.5" in str(fallback_url):
                fallback_model = "gpt-3.5-turbo"
        elif "mistral" in str(fallback_url):
            fallback_model = "mistral"
            
        failed_models.append(fallback_model)
        error_response["fallback_used"] = True
        error_response["fallback_failed"] = True
        error_response["api_metadata"]["stability_info"]["fallback_model"] = fallback_model
        error_response["api_metadata"]["stability_info"]["fallback_circuit_open"] = not check_circuit_breaker(fallback_model)
        
    elif is_function_based and fallback_config:
        fallback_model = "fallback_function"
        func = fallback_config.get("function")
        if func:
            fallback_model = func.__name__
            
        failed_models.append(fallback_model)
        error_response["fallback_used"] = True
        error_response["fallback_failed"] = True
        error_response["api_metadata"]["stability_info"]["fallback_model"] = fallback_model
        error_response["api_metadata"]["stability_info"]["fallback_circuit_open"] = not check_circuit_breaker(fallback_model)
    
    # Include user-provided metadata if any
    if metadata:
        error_response["api_metadata"].update(metadata)
        
    logger.error(f"❌ All models failed for request: {failed_models}")
    return error_response

# Test functions for the API request handler
async def test_load():
    """Stress test for API stability features - testing rate limiting and circuit breakers"""
    import argparse
    import random
    
    logger.info("===== RUNNING API STABILITY STRESS TEST =====")
    logger.info("This test will simulate heavy API usage to test rate limiting and circuit breakers")
    
    # List of test models to use
    test_models = [
        "gpt-4", "gpt-4o", "gpt-3.5-turbo", 
        "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
        "mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"
    ]
    
    # Track the test results
    test_results = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "rate_limited_requests": 0,
        "circuit_opened": [],
    }
    
    # Simulate 200 random API requests
    for i in range(200):
        # Pick a random model
        model = random.choice(test_models)
        
        # Check if model is rate limited
        if not enforce_rate_limit(model):
            logger.warning(f"Rate limit hit for {model} - waiting cooldown period")
            test_results["rate_limited_requests"] += 1
            # Wait for rate limit to expire in stress test
            await wait_for_rate_limit(model)
            
        # Check if circuit breaker is open
        if not check_circuit_breaker(model):
            logger.warning(f"Circuit breaker triggered for {model} - model unavailable")
            if model not in test_results["circuit_opened"]:
                test_results["circuit_opened"].append(model)
            
            # Skip request for this model since circuit breaker is open
            test_results["failed_requests"] += 1
            continue
            
        # Simulate API request success/failure
        # For test purposes, we'll have a 20% chance of failure for each request
        success = random.random() > 0.2
        
        # Update metrics
        test_results["total_requests"] += 1
        if success:
            test_results["successful_requests"] += 1
            update_circuit_breaker(model, success=True)
        else:
            test_results["failed_requests"] += 1
            update_circuit_breaker(model, success=False)
            logger.error(f"Simulated API failure for {model}")
        
        # Random delay between requests (100-500ms)
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Log progress every 20 requests
        if i % 20 == 0:
            logger.info(f"Test progress: {i}/200 requests completed")
            logger.info(f"Current results: {test_results}")
            
    # Log final test results
    logger.info("===== API STABILITY STRESS TEST COMPLETE =====")
    logger.info(f"Total requests: {test_results['total_requests']}")
    logger.info(f"Successful requests: {test_results['successful_requests']}")
    logger.info(f"Failed requests: {test_results['failed_requests']}")
    logger.info(f"Rate limited requests: {test_results['rate_limited_requests']}")
    logger.info(f"Models with circuit breakers opened: {test_results['circuit_opened']}")
    
    # Print stability status of all models
    logger.info("===== CURRENT MODEL STATUS =====")
    for model in test_models:
        # Get circuit breaker status
        breaker_info = CIRCUIT_BREAKERS.get(model, {})
        is_disabled = time.time() < breaker_info.get('disabled_until', 0) if breaker_info else False
        circuit_status = "OPEN" if is_disabled else "CLOSED"
        
        # Get failure count
        failures = breaker_info.get('failures', 0) if breaker_info else 0
        
        # Get rate limit status
        rate_limit_info = RATE_LIMITS.get(model, RATE_LIMITS.get('default', {}))
        count = rate_limit_info.get('count', 0) if rate_limit_info else 0
        max_requests = rate_limit_info.get('max_requests', 0) if rate_limit_info else 0
        rate_limited = "YES" if count >= max_requests else "NO"
        
        logger.info(f"Model: {model} | Circuit: {circuit_status} | Failures: {failures} | Rate Limited: {rate_limited}")

# Test URL-based request function
async def test_url_request():
    # OpenAI test
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_api_key:
        print("===== TESTING OPENAI =====")
        result = await api_request(
            url="https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            data={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "max_tokens": 50
            }
        )
        print(json.dumps(result, indent=2))
    else:
        print("Skipping OpenAI test: No API key")
        
    # Anthropic test
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_api_key:
        print("\n===== TESTING ANTHROPIC =====")
        result = await api_request(
            url="https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": anthropic_api_key,
                "anthropic-version": "2023-06-01"
            },
            data={
                "model": "claude-3-haiku-20240307",
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": "Hello, world!"}
                ]
            }
        )
        print(json.dumps(result, indent=2))
    else:
        print("Skipping Anthropic test: No API key")

# Test function-based request
async def test_function_request():
    print("\n===== TESTING FUNCTION-BASED =====")
    
    # Define test functions
    async def primary_function(text: str):
        await asyncio.sleep(0.5)  # Simulate processing
        return f"Primary response: {text}"
        
    async def fallback_function(text: str):
        await asyncio.sleep(0.3)  # Simulate processing
        return f"Fallback response: {text}"
        
    # Test successful primary
    print("Test with successful primary:")
    result = await api_request(
        primary_config={
            "function": primary_function,
            "params": {"text": "Hello, world!"}
        },
        fallback_config={
            "function": fallback_function,
            "params": {"text": "Hello, world!"}
        }
    )
    print(json.dumps(result, indent=2))
    
    # Test failing primary
    print("\nTest with failing primary:")
    async def failing_function(text: str):
        raise Exception("Simulated failure")
        
    result = await api_request(
        primary_config={
            "function": failing_function,
            "params": {"text": "Hello, world!"}
        },
        fallback_config={
            "function": fallback_function,
            "params": {"text": "Hello, world!"}
        }
    )
    print(json.dumps(result, indent=2))

# Simple test function for the API request handler
if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="API Request Handler with stability features")
    parser.add_argument("--test-load", action="store_true", help="Run a stress test to verify rate limiting and circuit breakers")
    args = parser.parse_args()
    
    if args.test_load:
        asyncio.run(test_load())
    else:
        # Run the regular tests
        async def run_tests():
            await test_url_request()
            await test_function_request()
        
        asyncio.run(run_tests())
