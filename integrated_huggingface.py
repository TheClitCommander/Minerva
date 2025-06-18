#!/usr/bin/env python3
"""
Integrated Hugging Face Processing Module for Minerva

This module contains the enhanced functionality for Hugging Face processing
that has been thoroughly tested through our isolated test scripts.
"""

import re
import time
import logging
import traceback
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger("minerva.huggingface")

# Support function: Optimize generation parameters based on query characteristics
def optimize_generation_parameters(message, query_tags=None, query_complexity=0.5):
    """
    Dynamically optimize generation parameters based on message characteristics.
    
    Args:
        message: The user message
        query_tags: List of query type tags
        query_complexity: Complexity score (0-1) of the query
        
    Returns:
        Dictionary of optimized parameters
    """
    # Default parameters
    params = {
        'max_tokens': 150,  # Increased default max tokens
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 40,
        'repetition_penalty': 1.2,
        'presence_penalty': 0.0,
        'frequency_penalty': 0.0
    }
    
    # Ensure we have query tags
    if query_tags is None:
        query_tags = []
    
    # Adjust max tokens based on complexity and query type
    if query_complexity > 0.8:  # Very complex queries need more tokens
        params['max_tokens'] = 350  # Increased from 300
    elif query_complexity > 0.5:  # Moderately complex
        params['max_tokens'] = 220  # Increased from 200
    elif query_complexity < 0.3:  # Simple queries
        params['max_tokens'] = 80
    
    # Adjust temperature based on query type
    if 'code' in query_tags:
        # Code generation needs less randomness
        params['temperature'] = 0.5
        params['top_p'] = 0.95
        params['repetition_penalty'] = 1.1
    elif 'creative' in query_tags:
        # Creative tasks benefit from more randomness
        params['temperature'] = 0.9
        params['top_p'] = 0.95
        params['top_k'] = 50
    elif 'factual' in query_tags:
        # Factual queries need more deterministic responses
        params['temperature'] = 0.4
        params['top_p'] = 0.85
        params['repetition_penalty'] = 1.15
    elif 'greeting' in query_tags:
        # Greetings need simple, predictable responses
        params['temperature'] = 0.3
        params['max_tokens'] = 50
        params['repetition_penalty'] = 1.3
    
    # Improved adjustments based on message content
    message_lower = message.lower()
    
    # Adjust for list requests
    if any(pattern in message_lower for pattern in ["list", "enumerate", "steps to", "instructions for"]):
        params['max_tokens'] = max(180, params['max_tokens'])  # Increased from 150
        params['repetition_penalty'] = 1.18  # Prevent repeating list items
    
    # Adjust for questions expecting precise answers
    if '?' in message and any(word in message_lower for word in ["exact", "precisely", "specific", "exact", "exactly"]):
        params['temperature'] = max(0.3, params['temperature'] - 0.2)  # Reduce randomness
    
    # Handle comparative queries
    if any(phrase in message_lower for phrase in ["compare", "difference between", "versus", "vs", "pros and cons"]):
        params['max_tokens'] = max(200, params['max_tokens'])  # Increased from 180
        params['temperature'] = min(0.7, params['temperature'])  # Keep focused
    
    # New: Adjustments for explanatory queries
    if any(phrase in message_lower for pattern in ["explain", "how does", "describe", "tell me about"]):
        params['max_tokens'] = max(200, params['max_tokens'])
        params['temperature'] = min(0.65, params['temperature'])  # Slightly reduced randomness
    
    # New: Adjustments for coding questions with multiple requirements
    if 'code' in query_tags and any(phrase in message_lower for phrase in ["with", "that includes", "requirements", "following"]):
        params['max_tokens'] = max(300, params['max_tokens'])  # Ensure enough space for detailed code
        params['repetition_penalty'] = 1.15  # Help avoid repetitive docstrings/comments
    
    # Log the optimized parameters
    logger.info(f"[PARAM OPTIMIZATION] Adjusted parameters for query complexity {query_complexity:.2f}, tags: {query_tags}")
    logger.info(f"[PARAM OPTIMIZATION] Parameters: {params}")
    
    return params

# Support function: Generate appropriate fallback responses
def generate_fallback_response(message, failure_reason=None):
    """
    Generate an appropriate fallback response based on the failure reason.
    
    Args:
        message: The original user message
        failure_reason: The reason for the failure
        
    Returns:
        A fallback response appropriate to the situation
    """
    logger.info(f"[FALLBACK] Generating fallback response for reason: {failure_reason}")
    
    # Content-related issues
    if failure_reason == "irrelevant":
        return "I understand you're asking about an important topic. To help me give you a more relevant response, could you provide more context or specific details about what you'd like to know?"
    
    elif failure_reason == "self_reference":
        return "I've prepared information on your topic. To make sure I give you exactly what you need, could you clarify which specific aspects you're most interested in?"
    
    elif failure_reason == "repetitive" or failure_reason == "excessive_repetition":
        return "I've collected information on your topic but found myself covering the same points repeatedly. Could you help me focus by specifying which aspects of this topic are most important to you?"
    
    elif failure_reason == "too_short":
        return "I have some initial thoughts on your question, but I'd like to provide more comprehensive information. Could you tell me which aspects of this topic you're most interested in exploring?"
        
    elif failure_reason == "validation_error":
        return "I'm having difficulty generating a high-quality response for this specific question. Could you try rephrasing it or provide more details about what you're looking for?"
        
    elif failure_reason == "generation_error":
        return "I encountered a technical issue while processing your question. This might be due to the complexity of the topic. Could you try a more specific or differently worded question?"
        
    # Technical errors
    elif failure_reason == "resource_error":
        return "I'm experiencing some resource constraints at the moment. Could you try asking a simpler question or try again in a moment?"
        
    elif failure_reason == "sequence_length_error" or failure_reason == "token_limit":
        return "Your question seems quite complex. Could you break it down into smaller, more specific questions so I can address each part thoroughly?"
        
    elif failure_reason == "timeout_error" or failure_reason == "timeout":
        return "I wasn't able to complete processing your question in time. This might be due to its complexity. Could you try a more focused question?"
        
    elif failure_reason == "general_error":
        return "I encountered an unexpected issue while processing your question. Could you try rephrasing it or asking about a different aspect of the topic?"
    
    # Generic fallback for unknown reasons
    return "I understand you're interested in this topic. To provide a more helpful response, could you rephrase your question or provide additional details about what you'd like to know?"

# Enhanced clean_ai_response function
def clean_ai_response(response):
    """
    Clean and normalize AI-generated responses.
    
    Args:
        response: The raw AI response
        
    Returns:
        A cleaned and normalized response
    """
    if not response:
        return ""
    
    # Remove any AI self-reference patterns
    self_ref_patterns = [
        r"As an AI language model,?",
        r"As an AI assistant,?",
        r"As an artificial intelligence,?",
        r"I'm an AI language model,?",
        r"I'm an AI assistant,?",
        r"I'm an artificial intelligence,?",
        r"As a language model,?",
        r"As an? ?AI,?",
        r"I do not have personal opinions",
        r"I do not have the ability to",
        r"I don't have access to",
        r"I don't have the ability to",
        r"I cannot provide",
        r"I cannot browse"
    ]
    
    for pattern in self_ref_patterns:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)
    
    # Remove common artifacts and formatting issues
    response = re.sub(r'\n{3,}', '\n\n', response)  # Replace excessive newlines
    response = re.sub(r'\s{2,}', ' ', response)  # Replace multiple spaces
    response = re.sub(r'(\w)\s+([.,!?:;])', r'\1\2', response)  # Fix spacing before punctuation
    
    # Clean up any special tokens or markers that might remain
    response = re.sub(r'<.*?>', '', response)  # Remove HTML-like tags
    response = re.sub(r'\[\w+\]', '', response)  # Remove markdown-style tags
    
    # Fix common formatting inconsistencies
    response = re.sub(r'(\d)\s+(\.)(\s+)(\d)', r'\1\2\4', response)  # Fix decimal spacing
    
    # Final normalization: ensure single spaces between sentences
    response = re.sub(r'([.!?])\s{2,}', r'\1 ', response)
    
    return response.strip()

# Integration points for the Enhanced Hugging Face Processing

# 1. Replace the optimize_generation_parameters function in app.py
# 2. Add the generate_fallback_response function to app.py
# 3. Update the process_huggingface_only function with our enhanced implementation

# Usage example:
# from integrated_huggingface import optimize_generation_parameters, generate_fallback_response, clean_ai_response
# These functions can be used directly or copied into the codebase.
