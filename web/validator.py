#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Response Validation System for Minerva

This module implements comprehensive validation and quality assessment
for AI model responses to ensure they meet Minerva's quality standards.
"""

import re
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_response(response: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate an AI response to ensure it meets quality standards.
    
    Args:
        response: The AI response object to validate
        query: The original user query for context
        
    Returns:
        Dictionary with validation results
    """
    # Extract response text
    if isinstance(response, str):
        response_text = response
        response_obj = {"response": response_text}
    else:
        response_text = response.get("response", "")
        response_obj = response.copy()
    
    if not response_text:
        logger.warning("[RESPONSE_VALIDATION] ❌ Empty response received")
        response_obj["is_valid"] = False
        response_obj["quality_score"] = 0.0
        response_obj["reason"] = "Empty response"
        return response_obj
    
    # Initialize validation result
    is_valid = True
    reason = "Response passes all validation checks"
    quality_score = response_obj.get("confidence", 0.7)  # Start with model confidence
    
    # Check for excessive repetition
    words = response_text.split()
    unique_words = set(words)
    if len(words) > 20:  # Only check longer responses
        repetition_ratio = len(unique_words) / len(words)
        if repetition_ratio < 0.5:  # High repetition
            is_valid = False
            reason = "Excessive repetition detected"
            quality_score *= 0.6
            logger.warning(f"[RESPONSE_VALIDATION] ❌ Excessive repetition: {repetition_ratio:.2f} ratio")
    
    # Check for AI self-references
    ai_references = re.findall(r'(as an AI|language model|AI assistant|AI model|OpenAI|trained by)', response_text, re.IGNORECASE)
    if ai_references and len(ai_references) > 1:
        is_valid = False
        reason = "Contains multiple AI self-references"
        quality_score *= 0.7
        logger.warning(f"[RESPONSE_VALIDATION] ❌ AI self-references detected: {len(ai_references)}")
    
    # Check for incomplete sentences or abrupt endings
    last_sentence = response_text.split('.')[-1].strip()
    if last_sentence and len(last_sentence) > 3 and not last_sentence.endswith(('!', '?', ':', ';')):
        quality_score *= 0.9  # Small penalty
        logger.warning("[RESPONSE_VALIDATION] ⚠️ Response may end abruptly")
    
    # Check for appropriate response length relative to query complexity
    if query:
        expected_length = len(query) * 2  # Simple heuristic
        if len(response_text) < expected_length * 0.5:
            quality_score *= 0.8
            logger.warning(f"[RESPONSE_VALIDATION] ⚠️ Response too short: {len(response_text)} chars vs expected {expected_length}")
        elif len(response_text) < 50:  # Absolute minimum for any response
            is_valid = False
            reason = "Response too short"
            quality_score *= 0.5
            logger.warning(f"[RESPONSE_VALIDATION] ❌ Response critically short: {len(response_text)} chars")
    
    # Check for hallucination markers (usually uncertain language)
    hallucination_markers = re.findall(r'(I think|I believe|probably|possibly|might be|could be|I\'m not sure|uncertain)', response_text, re.IGNORECASE)
    if hallucination_markers and len(hallucination_markers) > 3:
        quality_score *= 0.85
        logger.warning(f"[RESPONSE_VALIDATION] ⚠️ Potential hallucination markers: {len(hallucination_markers)}")
    
    # Check for nonsensical content (random character patterns)
    if re.search(r'([a-zA-Z]{1,2}\s+){5,}', response_text):
        is_valid = False
        reason = "Contains nonsensical character patterns"
        quality_score *= 0.3
        logger.warning("[RESPONSE_VALIDATION] ❌ Nonsensical content detected")
    
    # Check for structure quality (has paragraphs, etc.)
    has_paragraphs = response_text.count('\n\n') > 0
    has_lists = re.search(r'(\n[0-9]+\.|[-*]\s)', response_text) is not None
    if len(response_text) > 200 and not (has_paragraphs or has_lists):
        quality_score *= 0.9  # Minor penalty for lack of structure in longer responses
        logger.warning("[RESPONSE_VALIDATION] ⚠️ Long response lacks structure")
    
    # Add structured quality assessment if not already present
    quality_assessment = evaluate_response_quality(response_text, query)
    response_obj["quality_score"] = quality_score * quality_assessment
    response_obj["is_valid"] = is_valid
    response_obj["reason"] = reason
    response_obj["structure_quality"] = has_paragraphs or has_lists
    
    # Log validation result
    if is_valid:
        logger.info(f"[RESPONSE_VALIDATION] ✅ Response validated with score: {response_obj['quality_score']:.2f}")
    else:
        logger.warning(f"[RESPONSE_VALIDATION] ❌ Response rejected: {reason}")
    
    return response_obj

def evaluate_response_quality(response: str, query: Optional[str] = None) -> float:
    """
    Evaluate the overall quality of a response on a scale from 0.0 to 1.0.
    This function applies complexity-aware metrics and adaptive expectations.
    
    Args:
        response: The response text to evaluate
        query: The original query for context
        
    Returns:
        Quality score from 0.0 to 1.0
    """
    if not response:
        return 0.0
    
    # Base quality metrics
    base_score = 0.7  # Default starting score
    
    # Length-appropriate scoring
    response_length = len(response)
    if response_length < 50:
        base_score *= 0.6  # Severe penalty for very short responses
    elif response_length < 100:
        base_score *= 0.8  # Moderate penalty for short responses
    elif response_length > 2000:
        # Check if extremely long response is justified
        if query and (len(query) > 100 or "detailed" in query.lower()):
            base_score *= 0.95  # Slight penalty for very long response
        else:
            base_score *= 0.85  # Moderate penalty for unjustified verbosity
    
    # Structure and formatting quality
    structure_score = 0.0
    
    # Check for paragraphs
    paragraphs = response.split('\n\n')
    if len(paragraphs) > 1:
        structure_score += 0.2
    
    # Check for lists
    if re.search(r'(\n[0-9]+\.|[-*]\s)', response):
        structure_score += 0.15
    
    # Check for section headers
    if re.search(r'\n##? [A-Z]', response):
        structure_score += 0.15
    
    # Check for code blocks or examples
    if re.search(r'```|`.*`|\n    ', response):
        structure_score += 0.1
    
    # Cap structure score at 0.3 (30% of total quality)
    structure_score = min(structure_score, 0.3)
    
    # Content relevance score (if query is provided)
    relevance_score = 0.0
    if query:
        # Extract important words from query (length > 4 chars)
        query_words = {word.lower() for word in query.split() if len(word) > 4}
        if query_words:
            # Count matches in response
            response_lower = response.lower()
            matches = sum(1 for word in query_words if word in response_lower)
            relevance_ratio = matches / len(query_words)
            relevance_score = min(0.3, relevance_ratio * 0.3)  # Max 30% impact
    else:
        relevance_score = 0.2  # Default relevance score without query context
    
    # Combine scores
    final_score = base_score + structure_score + relevance_score
    
    # Cap at 1.0
    final_score = min(final_score, 1.0)
    
    logger.info(f"[QUALITY_EVALUATION] Score: {final_score:.2f} (base: {base_score:.2f}, structure: {structure_score:.2f}, relevance: {relevance_score:.2f})")
    return final_score
