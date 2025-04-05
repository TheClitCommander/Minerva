#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Free Model Configuration for Think Tank Mode

This module provides configuration for using only free and open-source models
in Think Tank mode, avoiding API costs during development.
"""

import logging
from typing import Dict, List, Any, Optional
import os

# Configure logging
logger = logging.getLogger(__name__)

# Configuration flag to disable API-based models
# In production, this should always be True for real models
ENABLE_API_MODELS = True  # Production mode requires real API models

# Free/open-source models to prioritize
FREE_MODELS = [
    "mistral7b",
    "gpt4all",
    "llama2",
    "distilgpt",
    "falcon",
    "bloom"
]

# Paid API models (disabled by default)
API_MODELS = [
    "gpt-4",
    "gpt-3.5-turbo",
    "claude-3",
    "claude-instant",
    "gemini",
    "palm2",
    "bard"
]

# Model capability profiles for free models
FREE_MODEL_CAPABILITIES = {
    "mistral7b": {
        "technical_expertise": 0.75,
        "creative_writing": 0.70,
        "reasoning": 0.72,
        "mathematical_reasoning": 0.68,
        "long_context": 0.65,
        "instruction_following": 0.76,
        "factual_accuracy": 0.72
    },
    "gpt4all": {
        "technical_expertise": 0.70,
        "creative_writing": 0.65,
        "reasoning": 0.68,
        "mathematical_reasoning": 0.65,
        "long_context": 0.60,
        "instruction_following": 0.72,
        "factual_accuracy": 0.68
    },
    "llama2": {
        "technical_expertise": 0.78,
        "creative_writing": 0.75,
        "reasoning": 0.76,
        "mathematical_reasoning": 0.70,
        "long_context": 0.65,
        "instruction_following": 0.74,
        "factual_accuracy": 0.73
    },
    "distilgpt": {
        "technical_expertise": 0.65,
        "creative_writing": 0.60,
        "reasoning": 0.62,
        "mathematical_reasoning": 0.58,
        "long_context": 0.50,
        "instruction_following": 0.65,
        "factual_accuracy": 0.64
    },
    "falcon": {
        "technical_expertise": 0.72,
        "creative_writing": 0.68,
        "reasoning": 0.70,
        "mathematical_reasoning": 0.65,
        "long_context": 0.60,
        "instruction_following": 0.70,
        "factual_accuracy": 0.68
    },
    "bloom": {
        "technical_expertise": 0.68,
        "creative_writing": 0.65,
        "reasoning": 0.66,
        "mathematical_reasoning": 0.62,
        "long_context": 0.55,
        "instruction_following": 0.67,
        "factual_accuracy": 0.66
    }
}

def get_available_models() -> List[str]:
    """Get the list of available models based on the API model toggle.
    
    Returns:
        List of available model names
    """
    if ENABLE_API_MODELS:
        logger.info("Using both free and API models in Think Tank mode")
        return FREE_MODELS + API_MODELS
    else:
        logger.info("Using only free/open-source models in Think Tank mode (API models disabled)")
        return FREE_MODELS

def toggle_api_models(enable: bool) -> None:
    """Toggle API models on or off.
    
    Args:
        enable: Whether to enable API models
    """
    global ENABLE_API_MODELS
    ENABLE_API_MODELS = enable
    status = "enabled" if enable else "disabled"
    logger.info(f"API models are now {status}")

def get_model_capabilities(model_name: str) -> Dict[str, float]:
    """Get capability scores for a model.
    
    Args:
        model_name: The model name
        
    Returns:
        Dictionary of capability scores or default if not found
    """
    # Normalize model name (remove version numbers, etc.)
    normalized_name = model_name.lower().split('-')[0].replace(' ', '')
    
    # Try to find in free models first
    if normalized_name in FREE_MODEL_CAPABILITIES:
        return FREE_MODEL_CAPABILITIES[normalized_name]
    
    # Default capabilities for unknown models
    return {
        "technical_expertise": 0.65,
        "creative_writing": 0.65,
        "reasoning": 0.65,
        "mathematical_reasoning": 0.60,
        "long_context": 0.55,
        "instruction_following": 0.65,
        "factual_accuracy": 0.65
    }

def should_use_think_tank(query: str) -> bool:
    """
    Determine if a query should use Think Tank mode (multiple models) or
    just a simple free model based on complexity.
    
    Args:
        query: The user query
        
    Returns:
        True if the query should use Think Tank mode, False if a single free model should be used
    """
    # Simple greeting check
    greetings = ['hi', 'hello', 'hey', 'greetings', 'howdy', 'good morning', 'good afternoon', 'good evening']
    query_lower = query.lower().strip()
    
    if query_lower in greetings or (query_lower.endswith('?') and any(query_lower.startswith(g) for g in greetings)):
        logger.info(f"Query '{query[:30]}...' identified as simple greeting, using free model")
        return False
    
    # Length-based heuristics (short queries are often simpler)
    if len(query) < 15:
        logger.info(f"Query '{query}' is very short, using free model")
        return False
    
    # Check for complex query indicators
    complex_indicators = [
        "explain", "analyze", "compare", "contrast", "evaluate", 
        "summarize", "synthesize", "interpret", "code", "write", "debug",
        "create", "generate", "optimize", "solve", "design", "predict",
        "what would happen if", "how would you", "please help me"
    ]
    
    # If query contains complex indicators, use Think Tank
    if any(indicator in query_lower for indicator in complex_indicators):
        logger.info(f"Query '{query[:30]}...' identified as complex, using Think Tank mode")
        return True
    
    # By default, use Think Tank for queries longer than 25 characters
    should_use_tt = len(query) > 25
    logger.info(f"Default decision for query '{query[:30]}...': use Think Tank = {should_use_tt}")
    return should_use_tt

def is_api_model(model_name: str) -> bool:
    """Check if a model is an API-based model.
    
    Args:
        model_name: The model name
        
    Returns:
        True if it's an API model, False otherwise
    """
    normalized_name = model_name.lower()
    return any(api_model.lower() in normalized_name for api_model in API_MODELS)

def log_model_usage(model_name: str, query: str, score: float = None) -> None:
    """Log model usage for tracking.
    
    Args:
        model_name: The model name
        query: The query that was processed
        score: Optional quality score for the response
    """
    model_type = "API" if is_api_model(model_name) else "Free/Open-Source"
    log_message = f"MODEL USAGE: {model_name} ({model_type}) processed query: {query[:50]}..."
    
    if score is not None:
        log_message += f" Score: {score:.2f}"
    
    if is_api_model(model_name) and not ENABLE_API_MODELS:
        log_message += " [WARNING: API model used while API models are disabled!]"
    
    logger.info(log_message)
