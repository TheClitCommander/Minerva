#!/usr/bin/env python3
"""
Utility functions for the enhanced AI model scoring and selection system.
This module provides helper functions for complexity estimation, model capability
matching, and score adjustment based on query characteristics.
"""

import re
from typing import Dict, Any, List, Tuple, Optional, Set


def estimate_query_complexity(query: str) -> float:
    """
    Estimate the complexity of a query based on length, technical terms, and structure.
    
    Args:
        query: The user query text
        
    Returns:
        Float between 1.0 and 10.0 representing complexity (higher is more complex)
    """
    if not query:
        return 1.0
        
    # Base complexity on length
    query_length = len(query)
    complexity = min(5.0, query_length / 100)
    
    # Check for technical terms
    technical_terms = [
        r'algorithm', r'function', r'code', r'implement', r'technical', 
        r'optimize', r'parameter', r'variable', r'async', r'database', 
        r'api', r'framework', r'neural', r'quantum', r'machine learning',
        r'performance', r'efficiency', r'complexity', r'architecture'
    ]
    
    # Count technical terms
    term_count = 0
    for term in technical_terms:
        if re.search(r'\b' + term + r'\b', query.lower()):
            term_count += 1
    
    # Add complexity based on technical terms
    if term_count > 0:
        complexity += min(3.0, term_count * 0.75)
    
    # Check for code-like elements
    code_indicators = [
        r'```', r'def ', r'class ', r'function', r'return', r'import',
        r'for\s+\w+\s+in\s', r'if\s+\w+.*:', r'while\s+\w+.*:'
    ]
    
    for indicator in code_indicators:
        if re.search(indicator, query):
            complexity += 1.0
            break
    
    # Check for complex questions
    complex_question_indicators = [
        r'how would you', r'what is the best way to', r'explain in detail',
        r'compare and contrast', r'what are the implications', r'analyze'
    ]
    
    for indicator in complex_question_indicators:
        if re.search(indicator, query.lower()):
            complexity += 0.5
            break
    
    return min(10.0, max(1.0, complexity))


def calculate_confidence_threshold(complexity: float) -> float:
    """
    Calculate an appropriate confidence threshold based on query complexity.
    
    Args:
        complexity: The estimated query complexity (1.0-10.0)
        
    Returns:
        Confidence threshold between 0.6 and 0.8
    """
    # Higher threshold for simpler queries (require more certainty)
    # Lower threshold for complex queries (accept more experimentation)
    return max(0.6, 0.8 - (complexity / 40))


def get_model_capabilities(model_name: str) -> Dict[str, Any]:
    """
    Get the capabilities and strengths of a specific model.
    
    Args:
        model_name: Name of the AI model
        
    Returns:
        Dictionary of model capabilities and strengths
    """
    capabilities = {
        'technical_expertise': False,
        'creative': False,
        'concise': False,
        'depth': 0.0,  # 0.0-1.0 scale
        'speed': 0.0,  # 0.0-1.0 scale
        'domains': []  # List of specialized domains
    }
    
    # OpenAI models
    if model_name.startswith('openai') or model_name == 'gpt':
        capabilities.update({
            'technical_expertise': True,
            'depth': 0.9,
            'speed': 0.7,
            'domains': ['general', 'technical', 'code']
        })
        
    # Claude models
    elif model_name.startswith('claude'):
        capabilities.update({
            'technical_expertise': True,
            'creative': True,
            'depth': 0.8,
            'speed': 0.6,
            'domains': ['general', 'creative', 'reasoning']
        })
        
    # Hugging Face models
    elif model_name.startswith('huggingface'):
        capabilities.update({
            'concise': True,
            'speed': 0.9,
            'domains': ['general']
        })
        
    # Add more models as needed
    
    return capabilities


def model_matches_query_complexity(model_name: str, complexity: float) -> float:
    """
    Calculate how well a model matches a given query complexity.
    
    Args:
        model_name: Name of the AI model
        complexity: The estimated query complexity (1.0-10.0)
        
    Returns:
        Match score between 0.0 and 1.0
    """
    capabilities = get_model_capabilities(model_name)
    
    # For simple queries, prefer faster models
    if complexity < 3.0:
        return min(1.0, capabilities['speed'] * 1.5)
        
    # For highly complex queries, prefer models with technical expertise and depth
    elif complexity > 7.0:
        technical_score = 1.0 if capabilities['technical_expertise'] else 0.3
        return min(1.0, (technical_score + capabilities['depth']) / 2)
        
    # For medium complexity, balance is key
    else:
        return min(1.0, (capabilities['speed'] + capabilities['depth']) / 2)


def model_matches_user_preferences(model_name: str, preferences: Dict[str, Any]) -> float:
    """
    Calculate how well a model matches the user's preferences.
    
    Args:
        model_name: Name of the AI model
        preferences: Dictionary of user preferences
        
    Returns:
        Match score between 0.0 and 1.0
    """
    if not preferences:
        return 0.5  # Neutral score if no preferences
        
    capabilities = get_model_capabilities(model_name)
    match_score = 0.5  # Start with neutral score
    
    # Match response length preference
    if 'length' in preferences:
        if preferences['length'] == 'short' and capabilities['concise']:
            match_score += 0.2
        elif preferences['length'] == 'long' and capabilities['depth'] > 0.7:
            match_score += 0.2
    
    # Match tone preference
    if 'tone' in preferences:
        if preferences['tone'] == 'formal' and capabilities['technical_expertise']:
            match_score += 0.1
        elif preferences['tone'] == 'casual' and capabilities['creative']:
            match_score += 0.1
    
    # Match priority preference
    if 'priority' in preferences:
        if preferences['priority'] == 'speed' and capabilities['speed'] > 0.7:
            match_score += 0.2
        elif preferences['priority'] == 'quality' and capabilities['depth'] > 0.7:
            match_score += 0.2
    
    return min(1.0, match_score)


def adjust_score_by_recency(base_score: float, days_ago: int) -> float:
    """
    Adjust a model score based on how recent the insight is.
    
    Args:
        base_score: The initial score
        days_ago: Number of days since the insight was created
        
    Returns:
        Adjusted score
    """
    if days_ago <= 1:
        return base_score  # No adjustment for very recent insights
        
    # Gradually reduce score based on age, with diminishing effect
    recency_factor = max(0.5, 1.0 - (days_ago / 30))
    return base_score * recency_factor


def get_default_models_for_complexity(complexity: float) -> List[str]:
    """
    Get a list of recommended models based on query complexity.
    
    Args:
        complexity: The estimated query complexity (1.0-10.0)
        
    Returns:
        List of model names recommended for this complexity
    """
    if complexity < 3.0:
        # Simple queries - use fast models
        return ['openai']
    elif complexity < 7.0:
        # Medium complexity - balance speed and quality
        return ['openai']
    else:
        # High complexity - prioritize depth and technical expertise
        return ['openai', 'claude']
