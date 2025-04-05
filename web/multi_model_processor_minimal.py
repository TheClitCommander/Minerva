#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Multi-model processor for handling different AI model integrations.
This module coordinates different model types, validates responses,
and provides routing functionality for optimal model selection.
'''

import logging
import random
import re
from typing import Dict, List, Tuple, Any, Optional

# Import the text corrector module
try:
    from web.text_corrector import correct_text, should_attempt_correction
    TEXT_CORRECTION_ENABLED = True
except ImportError:
    TEXT_CORRECTION_ENABLED = False

# Configure logging
logger = logging.getLogger(__name__)

# Model capability profiles
MODEL_CAPABILITIES = {
    "gpt-4": {
        "technical_expertise": 9.5,
        "creative_writing": 9.0,
        "reasoning": 9.5,
        "math": 9.0,
        "long_context": 8.5,
        "instruction_following": 9.5
    },
    "claude-3": {
        "technical_expertise": 9.0,
        "creative_writing": 9.5,
        "reasoning": 9.0,
        "math": 8.5,
        "long_context": 9.5,
        "instruction_following": 9.0
    },
    "gemini": {
        "technical_expertise": 8.5,
        "creative_writing": 8.5,
        "reasoning": 8.5,
        "math": 9.0,
        "long_context": 8.0,
        "instruction_following": 8.5
    },
    "mistral": {
        "technical_expertise": 8.0,
        "creative_writing": 7.5,
        "reasoning": 8.0,
        "math": 7.5,
        "long_context": 7.0,
        "instruction_following": 8.0
    },
    "default": {
        "technical_expertise": 7.0,
        "creative_writing": 7.0,
        "reasoning": 7.0,
        "math": 7.0,
        "long_context": 7.0,
        "instruction_following": 7.0
    }
}

def route_request(message: str, available_models: List[str] = None) -> Dict[str, Any]:
    '''
    Analyzes a user message to determine the best-suited model for response generation.
    
    Args:
        message: The user's message
        available_models: List of available model names
        
    Returns:
        Dictionary containing routing decision with selected models and metadata
    '''
    # Default models list if none provided
    if not available_models:
        available_models = ["gpt-4", "claude-3", "gemini", "mistral"]
    
    # Get query tags for routing
    tags = get_query_tags(message)
    
    # Determine query complexity (1-10 scale)
    complexity = calculate_query_complexity(message)
    
    # Categorize the query type
    query_type = classify_query_type(message)
    
    # Prioritize models based on query characteristics
    priority_models = prioritize_models_for_query(query_type, complexity, available_models)
    
    # Determine confidence scores for each model
    confidence_scores = {}
    for model in available_models:
        # Base score from model capabilities
        capability_score = get_model_capability_score(model, query_type)
        
        # Adjust based on query complexity
        complexity_match = get_complexity_match_score(model, complexity)
        
        # Final confidence score
        confidence_scores[model] = (capability_score * 0.7) + (complexity_match * 0.3)
    
    # Return routing decision with metadata
    return {
        "selected_models": priority_models[:3],  # Top 3 models
        "all_models_scored": confidence_scores,
        "query_metadata": {
            "tags": tags,
            "complexity": complexity,
            "type": query_type
        }
    }

def get_query_tags(message: str) -> List[str]:
    '''
    Analyze a message to extract relevant tags that help with routing.
    
    Args:
        message: The user's message
        
    Returns:
        List of tags relevant to the message
    '''
    tags = []
    message_lower = message.lower()
    
    # Check for greeting
    if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
        tags.append("greeting")
    
    # Check for code
    if any(marker in message_lower for marker in ["code", "function", "bug", "error", "programming"]):
        tags.append("code")
        
        # Detect specific languages
        if any(lang in message_lower for lang in ["python", "java", "javascript", "c++", "ruby", "go"]):
            tags.append("specific_language")
    
    # Check for creative request
    if any(word in message_lower for word in ["story", "poem", "creative", "write", "imagine"]):
        tags.append("creative")
    
    # Check for math/analysis
    if any(word in message_lower for word in ["calculate", "solve", "equation", "math", "formula"]):
        tags.append("mathematical")
    
    return tags

def calculate_query_complexity(message: str) -> int:
    '''
    Calculate the complexity of a query on a scale of 1-10.
    
    Args:
        message: The user's message
        
    Returns:
        Complexity score (1-10)
    '''
    # Base complexity starts at 3
    complexity = 3
    
    # Length factor
    words = message.split()
    if len(words) > 100:
        complexity += 3
    elif len(words) > 50:
        complexity += 2
    elif len(words) > 20:
        complexity += 1
    
    # Technical terms factor
    technical_terms = ["algorithm", "function", "variable", "framework", "implementation", 
                       "parameter", "optimization", "complexity", "architecture"]
    tech_count = sum(1 for term in technical_terms if term in message.lower())
    complexity += min(2, tech_count)
    
    # Question complexity
    if "?" in message:
        question_count = message.count("?")
        if question_count > 3:
            complexity += 2
        elif question_count > 1:
            complexity += 1
            
    # Cap at 10
    return min(10, complexity)

def classify_query_type(message: str) -> str:
    '''
    Classify the type of query based on its content.
    
    Args:
        message: The user query
        
    Returns:
        Query type classification
    '''
    message_lower = message.lower()
    
    # Technical query check
    technical_indicators = ["code", "function", "algorithm", "debug", "error", 
                           "implement", "fix", "programming", "software", "develop"]
    
    # Creative query check
    creative_indicators = ["story", "poem", "creative", "imagine", "write", 
                         "generate", "fiction", "narrative", "character"]
    
    # Analytical query check
    analytical_indicators = ["analyze", "compare", "evaluate", "assess", "critique",
                           "review", "pros and cons", "strengths and weaknesses"]
    
    # Count matches for each type
    technical_count = sum(1 for word in technical_indicators if word in message_lower)
    creative_count = sum(1 for word in creative_indicators if word in message_lower)
    analytical_count = sum(1 for word in analytical_indicators if word in message_lower)
    
    # Determine the dominant type
    if technical_count > creative_count and technical_count > analytical_count:
        return "technical"
    elif creative_count > technical_count and creative_count > analytical_count:
        return "creative"
    elif analytical_count > technical_count and analytical_count > creative_count:
        return "analytical"
    else:
        # Default type for general factual queries
        return "factual"

def prioritize_models_for_query(query_type: str, complexity: int, available_models: List[str]) -> List[str]:
    '''
    Prioritize models based on query type and complexity.
    
    Args:
        query_type: Type of the query (technical, creative, analytical, factual)
        complexity: Complexity score of the query (1-10)
        available_models: List of available models
        
    Returns:
        Prioritized list of models
    '''
    # Define priority models for each query type
    priority_mapping = {
        "technical": ["gpt-4", "claude-3", "gemini", "mistral"],
        "creative": ["claude-3", "gpt-4", "gemini", "mistral"],
        "analytical": ["gpt-4", "claude-3", "gemini", "mistral"],
        "factual": ["gemini", "gpt-4", "claude-3", "mistral"]
    }
    
    # For high complexity queries, adjust priority
    if complexity >= 8:
        high_complexity_order = ["gpt-4", "claude-3", "gemini", "mistral"]
        
        # Get the base priority list for the query type
        base_priority = priority_mapping.get(query_type, ["gpt-4", "claude-3", "gemini", "mistral"])
        
        # Blend the two lists, with high complexity having more weight
        priority_models = []
        for model in high_complexity_order:
            if model in available_models:
                priority_models.append(model)
        
        # Add any remaining models from the base priority if not already added
        for model in base_priority:
            if model in available_models and model not in priority_models:
                priority_models.append(model)
    else:
        # Use the standard priority for this query type
        standard_priority = priority_mapping.get(query_type, ["gpt-4", "claude-3", "gemini", "mistral"])
        priority_models = [model for model in standard_priority if model in available_models]
    
    # Ensure all available models are included
    for model in available_models:
        if model not in priority_models:
            priority_models.append(model)
    
    return priority_models

def get_model_capability_score(model: str, query_type: str) -> float:
    '''
    Get a capability score for a model based on the query type.
    
    Args:
        model: Model name
        query_type: Type of the query
        
    Returns:
        Capability score for the model (0-10)
    '''
    # Get the model's capability profile
    capability_profile = MODEL_CAPABILITIES.get(model, MODEL_CAPABILITIES["default"])
    
    # Determine which capabilities matter most for this query type
    if query_type == "technical":
        score = (capability_profile["technical_expertise"] * 0.5 + 
                 capability_profile["reasoning"] * 0.3 + 
                 capability_profile["instruction_following"] * 0.2)
    elif query_type == "creative":
        score = (capability_profile["creative_writing"] * 0.6 + 
                 capability_profile["reasoning"] * 0.2 + 
                 capability_profile["instruction_following"] * 0.2)
    elif query_type == "analytical":
        score = (capability_profile["reasoning"] * 0.5 + 
                 capability_profile["technical_expertise"] * 0.3 + 
                 capability_profile["instruction_following"] * 0.2)
    else:  # factual
        score = (capability_profile["technical_expertise"] * 0.4 + 
                 capability_profile["reasoning"] * 0.4 + 
                 capability_profile["instruction_following"] * 0.2)
    
    return score

def get_complexity_match_score(model: str, complexity: int) -> float:
    '''
    Calculate how well a model matches a given query complexity.
    
    Args:
        model: Model name
        complexity: Query complexity score (1-10)
        
    Returns:
        Match score (0-10)
    '''
    # Define complexity thresholds for each model
    model_complexity_thresholds = {
        "gpt-4": 9.5,         # Best for very complex queries
        "claude-3": 9.0,      # Also excellent for complex queries
        "gemini": 8.0,        # Good for moderately complex queries
        "mistral": 7.0,       # Better for simpler queries
        "default": 5.0        # Default for unknown models
    }
    
    # Get the model's complexity threshold
    model_threshold = model_complexity_thresholds.get(model, model_complexity_thresholds["default"])
    
    # Calculate match score based on how close the query complexity is to the model's sweet spot
    # Models perform best when complexity is at or below their threshold
    if complexity <= model_threshold:
        # Perfect match if complexity is within the model's capabilities
        return 10.0
    else:
        # Reduced score for queries that exceed the model's optimal complexity
        difference = complexity - model_threshold
        return max(0, 10.0 - (difference * 2.0))

def simulated_gpt4_processor(message: str) -> str:
    '''GPT-4 simulated processor'''
    return f"GPT-4 response to: {message}"

def simulated_claude_processor(message: str) -> str:
    '''Claude 3 simulated processor'''
    return f"Claude 3 response to: {message}"

def simulated_mistral_processor(message: str) -> str:
    '''Mistral simulated processor'''
    return f"Mistral response to: {message}"

def simulated_mistral7b_processor(message: str) -> str:
    '''Mistral 7B simulated processor (alias for simulated_mistral_processor)'''
    return simulated_mistral_processor(message)

def simulated_gpt4all_processor(message: str) -> str:
    '''GPT4All simulated processor'''
    return f"GPT4All response to: {message}"

# Main execution for testing
if __name__ == "__main__":
    test_queries = [
        "Hi there, how are you doing today?",
        "Can you write a short poem about the sea?",
        "Explain the concept of recursion in programming with an example",
        "What are the current major AI models and their strengths?"
    ]
    
    for query in test_queries:
        result = route_request(query)
        print(f"Query: {query}")
        print(f"Routing: {result}")
        print("-----")
