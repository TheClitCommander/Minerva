#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Router for Minerva

This module implements query analysis and intelligent model routing for Minerva AI.
It determines the most appropriate AI models for a given query based on content analysis.
"""

import re
import logging
from typing import Dict, List, Any, Optional
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Available model options (models that can be selected by the router)
AVAILABLE_MODELS = [
    "gpt4", 
    "claude3", 
    "mistral7b", 
    "llama2", 
    "gpt4all", 
    "falcon"
]

def get_query_tags(query: str) -> List[str]:
    """
    Extract content domain tags from a query using pattern matching.
    
    Args:
        query: The user query to analyze
        
    Returns:
        List of relevant content domain tags
    """
    query = query.lower()
    tags = []
    
    # Content domain detection
    if re.search(r'(code|function|program|algorithm|script|bug|error|exception)', query):
        tags.append('code')
    
    if re.search(r'(math|equation|formula|calculate|solve|computation|numerical)', query):
        tags.append('math')
    
    if re.search(r'(science|scientific|physics|chemistry|biology|experiment)', query):
        tags.append('science')
    
    if re.search(r'(write|essay|story|creative|poem|narrative|dialogue)', query):
        tags.append('creative_writing')
    
    if re.search(r'(explain|how|why|what is|definition|meaning)', query):
        tags.append('explanation')
    
    if re.search(r'(compare|difference|versus|contrast|similarities|better)', query):
        tags.append('comparison')
    
    if re.search(r'(step by step|procedure|how to|tutorial|guide|instructions)', query):
        tags.append('procedure')
    
    if re.search(r'(evaluate|assess|review|analyze|critique|good|bad)', query):
        tags.append('evaluation')
    
    # Default tag if no specific domain detected
    if not tags:
        tags.append('general')
    
    logger.info(f"[QUERY_TAGS] Identified tags: {', '.join(tags)}")
    return tags

def estimate_query_complexity(query: str) -> int:
    """
    Estimate query complexity on a scale of 1-10.
    
    Args:
        query: The user query to analyze
        
    Returns:
        Complexity score (1-10)
    """
    # Base complexity starts at 3
    complexity = 3
    
    # Length-based complexity (longer queries are typically more complex)
    words = len(query.split())
    if words > 30:
        complexity += 2
    elif words > 15:
        complexity += 1
    
    # Multi-part questions increase complexity
    question_marks = query.count('?')
    if question_marks > 1:
        complexity += min(question_marks, 3)  # Cap at 3 additional points
    
    # Technical vocabulary indicates complexity
    technical_terms = [
        'algorithm', 'optimize', 'complexity', 'architecture', 'framework',
        'implementation', 'design pattern', 'mathematical', 'theoretical',
        'recursive', 'quantum', 'neural network', 'machine learning'
    ]
    
    for term in technical_terms:
        if term in query.lower():
            complexity += 1
            if complexity >= 10:  # Cap at 10
                break
    
    logger.info(f"[QUERY_COMPLEXITY] Estimated complexity: {complexity}/10")
    return min(complexity, 10)  # Ensure we don't exceed 10

def route_request(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze a query and determine the most appropriate models to process it,
    leveraging learned user preferences and patterns when available.
    
    Args:
        query: The user query to route
        context: Optional context data from the learning system including user preferences and patterns
        
    Returns:
        Dictionary containing routing information with intelligent model selection
    """
    # Start with query analysis
    query_tags = get_query_tags(query)
    complexity = estimate_query_complexity(query)
    logger.info(f"[MODEL_ROUTING] Processing query with complexity {complexity}/10 and tags: {', '.join(query_tags)}")
    
    # Default model order - will be adjusted based on query characteristics
    priority_models = ["gpt4", "claude3", "mistral7b"]
    routing_reason = "default configuration"
    
    # Extract relevant context data if provided
    user_preferences = {}
    topic_matches = []
    pattern_matches = []
    high_satisfaction_models = []
    previous_successful_models = []
    behavior_preferences = []
    
    if context:
        # Extract user model preferences
        if isinstance(context.get('model_preferences'), dict):
            user_preferences = context.get('model_preferences', {})
            logger.info(f"[MODEL_ROUTING] Found user model preferences: {user_preferences}")
        
        # Extract additional context elements
        topic_matches = context.get('topic_matches', [])
        pattern_matches = context.get('pattern_matches', [])
        high_satisfaction_models = context.get('high_satisfaction_models', [])
        previous_successful_models = context.get('previous_models', [])
        behavior_preferences = context.get('behavior_preferences', [])
        
        # Get tags from context if available and merge with query tags
        context_tags = context.get('tags', [])
        if context_tags:
            for tag in context_tags:
                if tag not in query_tags:
                    query_tags.append(tag)
            logger.info(f"[MODEL_ROUTING] Added context tags: {context_tags}")
    
    # Apply context-based enhancements to complexity score if available
    if context and 'complexity' in context:
        context_complexity = context.get('complexity', complexity)
        if context.get('complexity_boosted') or context.get('complexity_reduced'):
            # If context has specifically modified complexity, use that value
            old_complexity = complexity
            complexity = context_complexity
            logger.info(f"[MODEL_ROUTING] Adjusted complexity from {old_complexity} to {complexity} based on user context")
    
    # Determine optimal model priority based on query and context
    if 'code' in query_tags:
        priority_models = ["gpt4", "claude3", "mistral7b"]
        routing_reason = "code-related query"
    elif 'math' in query_tags:
        priority_models = ["gpt4", "claude3", "llama2"]
        routing_reason = "math-related query"
    elif 'creative_writing' in query_tags:
        priority_models = ["claude3", "gpt4", "llama2"]
        routing_reason = "creative writing query"
    elif 'science' in query_tags:
        priority_models = ["gpt4", "claude3", "mistral7b"]
        routing_reason = "science-related query"
    
    # Apply user preferences if available (override tag-based selection)
    if user_preferences:
        # Sort models by confidence score from user preferences
        preferred_models = sorted(
            user_preferences.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # If preferences are strong (confidence > 0.8), prioritize them
        strong_preferences = [m for m, conf in preferred_models if conf > 0.8]
        if strong_preferences:
            # Start with strong user preferences, then add default models
            new_priority = strong_preferences.copy()
            for model in priority_models:
                if model not in new_priority:
                    new_priority.append(model)
            
            priority_models = new_priority
            routing_reason = "strong user model preferences"
            logger.info(f"[MODEL_ROUTING] Prioritizing models based on user preferences: {strong_preferences}")
    
    # Apply historical model success data if available
    if high_satisfaction_models:
        # If we have models that performed well for similar queries in the past, prioritize them
        high_sat_not_in_priority = [m for m in high_satisfaction_models if m not in priority_models]
        if high_sat_not_in_priority:
            # Insert high satisfaction models at the beginning, maintaining original order for others
            new_priority = high_satisfaction_models.copy()
            for model in priority_models:
                if model not in new_priority:
                    new_priority.append(model)
                    
            priority_models = new_priority
            routing_reason = "models with high satisfaction on similar queries"
            logger.info(f"[MODEL_ROUTING] Prioritizing models with historical high satisfaction: {high_satisfaction_models}")
    elif previous_successful_models and not high_satisfaction_models:
        # If no high satisfaction models but we have previous models that were used
        previous_not_in_priority = [m for m in previous_successful_models if m not in priority_models[:2]]
        if previous_not_in_priority:
            # Insert at position 2 (after our top picks) if not already in top positions
            for model in reversed(previous_not_in_priority):
                priority_models.insert(2, model)
                # Remove duplicate if it exists further down the list
                if model in priority_models[3:]:
                    priority_models.remove(model)
            
            routing_reason += " with influence from historically used models"
            logger.info(f"[MODEL_ROUTING] Incorporating previously successful models: {previous_successful_models}")
    
    # Filter priority models to only include available models
    priority_models = [m for m in priority_models if m in AVAILABLE_MODELS]
    
    # Add fallback models if we have fewer than 3 models
    while len(priority_models) < 3 and len(AVAILABLE_MODELS) > len(priority_models):
        for model in AVAILABLE_MODELS:
            if model not in priority_models:
                priority_models.append(model)
                break
    
    # Set confidence thresholds based on complexity and context
    if complexity >= 8:
        confidence_threshold = 0.8
    elif complexity >= 5:
        confidence_threshold = 0.7
    else:
        confidence_threshold = 0.6
    
    # Adjust confidence for behavior preferences
    for behavior in behavior_preferences:
        behavior_type = behavior.get('type', '')
        # If user expects step-by-step or tutorial content, increase confidence threshold
        if behavior_type in ['step-by-step', 'explanatory', 'tutorial-like'] and behavior.get('confidence', 0) > 0.8:
            confidence_threshold = min(0.9, confidence_threshold + 0.1)
            logger.info(f"[MODEL_ROUTING] Increased confidence threshold to {confidence_threshold} for {behavior_type} content")
    
    # Add redundancy for complex queries
    if complexity >= 8:
        logger.info("[MODEL_ROUTING] Complex query detected, adding redundancy")
        redundancy_reason = "complex query requiring redundancy"
        # Add fallback models to handle difficult queries
        for model in AVAILABLE_MODELS:
            if model not in priority_models:
                priority_models.append(model)
                if len(priority_models) >= 4:  # Cap at 4 models for very complex queries
                    break
        
        # Add complexity reason to routing reason if not already mentioned
        if "complex" not in routing_reason:
            routing_reason = f"{routing_reason} with additional models for complex query"
    
    # Create detailed routing info object
    routing_info = {
        "priority_models": priority_models,
        "query_complexity": complexity,
        "query_tags": query_tags,
        "confidence_threshold": confidence_threshold,
        "routing_explanation": f"Routed to {', '.join(priority_models)} based on {routing_reason}"
    }
    
    logger.info(f"[MODEL_ROUTING] Final routing decision: {routing_info['routing_explanation']}")
    return routing_info

def evaluate_responses(responses: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Evaluate and rank a list of model responses based on quality metrics.
    
    Args:
        responses: List of response objects with model outputs
        query: The original user query
    
    Returns:
        Ranked list of responses with quality scores
    """
    for response in responses:
        # Start with model confidence as base score
        quality_score = response.get('confidence', 0.5)
        
        # Adjust score based on response length (penalize extremely short responses)
        response_text = response.get('response', '')
        if len(response_text) < 50:
            quality_score *= 0.7
        
        # Check for repetition (reduce score for repetitive responses)
        words = response_text.split()
        unique_words = set(words)
        if len(words) > 0:
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.6:  # High repetition
                quality_score *= 0.8
        
        # Relevance check - make sure response mentions key terms from query
        query_words = set(query.lower().split())
        important_words = {word for word in query_words if len(word) > 4}  # Only longer words
        if important_words:
            response_lower = response_text.lower()
            matches = sum(1 for word in important_words if word in response_lower)
            relevance_score = min(1.0, matches / len(important_words))
            quality_score *= (0.7 + 0.3 * relevance_score)  # Weighted adjustment
        
        # Add quality score to response object
        response['quality_score'] = round(quality_score, 2)
        logger.info(f"[RESPONSE_EVALUATION] {response.get('model', 'unknown')} quality score: {quality_score:.2f}")
    
    # Sort responses by quality score (descending)
    ranked_responses = sorted(responses, key=lambda x: x.get('quality_score', 0), reverse=True)
    
    # Log the ranking results
    logger.info(f"[RESPONSE_RANKING] Best response from: {ranked_responses[0].get('model', 'unknown')}")
    
    return ranked_responses
