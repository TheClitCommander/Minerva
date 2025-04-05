#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ensemble Validator for Minerva's Think Tank mode.

This module implements weighted voting, probabilistic consensus, and confidence scoring
to evaluate and rank responses from multiple AI models. It allows the Think Tank to
select the highest quality responses based on model consensus rather than arbitrary selection.
"""

import logging
import re
import json
from typing import Dict, List, Any, Tuple, Optional, Union
import numpy as np
from collections import defaultdict

# Import cost-related modules
try:
    from web.integrations.cost_optimizer import get_cost_per_1k_tokens
    from web.integrations.smart_model_selector import estimate_cost_savings
except ImportError:
    # Mock functions if the modules aren't available
    def get_cost_per_1k_tokens(model_name):
        return 0.01  # Default low cost
    def estimate_cost_savings(original_model, selected_model):
        return 0.0  # Default no savings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Common stopwords for text analysis
STOPWORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
             'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'against', 'between', 'into',
             'through', 'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down',
             'this', 'that', 'these', 'those', 'of', 'as', 'it', 'its', 'they', 'them', 'their'}

# Model capability profiles for different query types
MODEL_CAPABILITIES = {
    "gpt-4o": {
        "technical": 0.95,
        "coding": 0.95,
        "creative": 0.90,
        "reasoning": 0.95,
        "explanation": 0.95,
        "comparison": 0.90,
        "general": 0.95
    },
    "gpt-4": {
        "technical": 0.90,
        "coding": 0.90,
        "creative": 0.88,
        "reasoning": 0.92,
        "explanation": 0.90,
        "comparison": 0.88,
        "general": 0.90
    },
    "claude-3-opus": {
        "technical": 0.88,
        "coding": 0.85,
        "creative": 0.90,
        "reasoning": 0.90,
        "explanation": 0.95,
        "comparison": 0.95,
        "general": 0.90
    },
    "claude-3-sonnet": {
        "technical": 0.85,
        "coding": 0.80,
        "creative": 0.85,
        "reasoning": 0.85,
        "explanation": 0.90,
        "comparison": 0.90,
        "general": 0.85
    },
    "claude-3-haiku": {
        "technical": 0.75,
        "coding": 0.70,
        "creative": 0.80,
        "reasoning": 0.78,
        "explanation": 0.80,
        "comparison": 0.80,
        "general": 0.75
    },
    "gpt-3.5-turbo": {
        "technical": 0.75,
        "coding": 0.75,
        "creative": 0.80,
        "reasoning": 0.75,
        "explanation": 0.80,
        "comparison": 0.75,
        "general": 0.80
    },
    "gemini-pro": {
        "technical": 0.85,
        "coding": 0.85,
        "creative": 0.82,
        "reasoning": 0.80,
        "explanation": 0.85,
        "comparison": 0.80,
        "general": 0.82
    },
    "mistral-medium": {
        "technical": 0.80,
        "coding": 0.80,
        "creative": 0.75,
        "reasoning": 0.78,
        "explanation": 0.78,
        "comparison": 0.76,
        "general": 0.78
    },
    "cohere-command": {
        "technical": 0.75,
        "coding": 0.72,
        "creative": 0.75,
        "reasoning": 0.75,
        "explanation": 0.78,
        "comparison": 0.75,
        "general": 0.75
    },
}

# Legacy model capability weights (for backward compatibility)
DEFAULT_MODEL_WEIGHTS = {
    "gpt-4o": 1.0,       # GPT-4o is considered the BEST model (highest priority)
    "gpt-4": 0.95,       # Updated naming conventions
    "claude-3-opus": 0.9, # Slightly lower than GPT-4o
    "claude-3-sonnet": 0.85, # Added Claude 3 Sonnet
    "gpt-3.5-turbo": 0.8, # Added GPT-3.5-turbo
    "claude-3-haiku": 0.75, # Added Claude 3 Haiku
    "claude-3": 0.9,    # Generic Claude 3 
    "claude3": 0.9,     # Alternative name for Claude 3
    "mistral-7b": 0.8,  # Updated Mistral
    "mistral7b": 0.8,   # Alternative name for Mistral
    "mistral": 0.8,     # Generic Mistral
    "cohere": 0.75,      # Added Cohere
    "llama": 0.6,        # Generic Llama - LOWERED to prevent generic responses
    "llama2": 0.65,      # Llama 2 - LOWERED to prevent generic responses
    "gpt4": 0.95,        # For backward compatibility
    "gpt4all": 0.7,      # For backward compatibility
    "huggingface": 0.75  # Generic weight for huggingface models
}

# Default weight for unknown models
DEFAULT_MODEL_WEIGHT = 0.6

# Different weights for different query types
MODEL_TYPE_WEIGHTS = {
    "technical": {
        "gpt-4": 0.95,
        "gpt-4o": 1.0,
        "gpt4": 0.95,
        "gpt-3.5-turbo": 0.8,
        "claude-3-opus": 0.9,
        "claude-3-sonnet": 0.9,
        "claude-3-haiku": 0.8,
        "claude-3": 0.9,
        "claude3": 0.9,
        "mistral-7b": 0.85,
        "mistral7b": 0.85,
        "mistral": 0.85,
        "llama": 0.7,
        "llama2": 0.7,
        "cohere": 0.75
    },
    "creative": {
        "claude-3-opus": 1.0,
        "claude-3-sonnet": 0.95,
        "claude-3-haiku": 0.9,
        "claude-3": 0.95,
        "claude3": 0.95,
        "gpt-4o": 0.95,
        "gpt-4": 0.9,
        "gpt4": 0.9,
        "gpt-3.5-turbo": 0.85,
        "mistral-7b": 0.8,
        "mistral7b": 0.8,
        "mistral": 0.8,
        "llama": 0.75,
        "llama2": 0.75,
        "cohere": 0.7
    },
    "analytical": {
        "gpt-4o": 1.0,
        "gpt-4": 0.95,
        "gpt4": 0.95,
        "claude-3-opus": 0.95,
        "claude-3-sonnet": 0.9,
        "claude-3-haiku": 0.85,
        "claude-3": 0.9,
        "claude3": 0.9,
        "gpt-3.5-turbo": 0.8,
        "mistral-7b": 0.8,
        "mistral7b": 0.8,
        "mistral": 0.8,
        "llama": 0.7,
        "llama2": 0.7,
        "cohere": 0.7
    },
    "factual": {
        "gpt-4o": 1.0,  # 🚨 FORCEFULLY PRIORITIZE GPT-4o for factual queries
        "gpt-4": 0.9,
        "gpt4": 0.9,
        "claude-3-opus": 0.9,
        "gpt-3.5-turbo": 0.85,  # Downgraded from 1.0
        "claude-3-sonnet": 0.85,
        "claude-3-haiku": 0.8,
        "claude-3": 0.85,
        "claude3": 0.85,
        "mistral-7b": 0.5,  # 🚫 Significantly downgraded
        "mistral7b": 0.5,   # 🚫 Significantly downgraded
        "mistral": 0.5,     # 🚫 Significantly downgraded
        "llama": 0.3,       # 🚫 HEAVILY penalized for factual queries
        "llama2": 0.3,      # 🚫 HEAVILY penalized for factual queries
        "cohere": 0.65
    },
    "reasoning": {
        "gpt-4o": 1.0,
        "gpt-4": 0.95,
        "gpt4": 0.95,
        "claude-3-opus": 0.95,
        "claude-3-sonnet": 0.9,
        "claude-3-haiku": 0.85,
        "claude-3": 0.9,
        "claude3": 0.9,
        "gpt-3.5-turbo": 0.85,
        "mistral-7b": 0.8,
        "mistral7b": 0.8,
        "mistral": 0.8,
        "llama": 0.7,
        "llama2": 0.7,
        "cohere": 0.7
    },
    "code": {
        "gpt-4o": 1.0,
        "gpt-4": 0.95,
        "gpt4": 0.95,
        "claude-3-opus": 0.9,
        "claude-3-sonnet": 0.85,
        "claude-3-haiku": 0.8,
        "claude-3": 0.85,
        "claude3": 0.85,
        "gpt-3.5-turbo": 0.8,
        "mistral-7b": 0.75,
        "mistral7b": 0.75,
        "mistral": 0.75,
        "llama": 0.65,
        "llama2": 0.65,
        "cohere": 0.7
    },
    "multi-perspective": {
        "claude-3-opus": 1.0,
        "claude-3-sonnet": 0.95,
        "claude-3-haiku": 0.9,
        "claude-3": 0.95,
        "claude3": 0.95,
        "gpt-4o": 0.9,
        "gpt-4": 0.85,
        "gpt4": 0.85,
        "gpt-3.5-turbo": 0.8,
        "mistral-7b": 0.75,
        "mistral7b": 0.75,
        "mistral": 0.75,
        "llama": 0.7,
        "llama2": 0.7,
        "cohere": 0.65
    }
}

class EnsembleValidator:
    """
    Implements ensemble validation techniques for evaluating and ranking responses
    from multiple AI models in the Think Tank mode.
    """
    
    def __init__(self, model_weights: Dict[str, float] = None):
        """
        Initialize the ensemble validator with model weights.
        
        Args:
            model_weights: Dictionary mapping model names to their reliability weights
        """
        self.model_weights = model_weights or DEFAULT_MODEL_WEIGHTS.copy()
        logger.info(f"Ensemble Validator initialized with {len(self.model_weights)} model weights")
    
    def calculate_consensus_scores(self,
                             responses: Dict[str, str],
                             query: str = None) -> Dict[str, float]:
        """
        Calculate consensus scores for responses by comparing agreement across models.
        This is a wrapper around probabilistic_consensus for API compatibility.
        
        Args:
            responses: Dictionary mapping model names to their responses
            query: Optional original query for context (unused in this implementation)
            
        Returns:
            Dictionary mapping model names to consensus scores
        """
        # Generate simple quality scores if not provided externally
        quality_scores = {model: 0.8 for model in responses}
        
        # Call the underlying method
        return self.probabilistic_consensus(responses, quality_scores)
    
    def analyze_confidence(self, responses: Dict[str, str]) -> Dict[str, float]:
        """
        Analyze confidence levels in each response.
        This is a wrapper around confidence_analysis for API compatibility.
        
        Args:
            responses: Dictionary mapping model names to their responses
            
        Returns:
            Dictionary mapping model names to confidence scores
        """
        confidence_scores = {}
        for model_name, response in responses.items():
            confidence_scores[model_name] = self.confidence_analysis(response)
        return confidence_scores
    
    def evaluate_response_quality(self, response: str, query: str = None) -> Dict[str, float]:
        """
        Comprehensive evaluation of response quality across multiple dimensions.
        
        Args:
            response: Text response to evaluate
            query: Original query for context
            
        Returns:
            Dictionary with quality scores across different dimensions
        """
        if not response:
            return {
                "overall": 0.0,
                "relevance": 0.0,
                "coherence": 0.0,
                "correctness": 0.0,
                "helpfulness": 0.0,
                "structure": 0.0,
                "issues": ["empty_response"],
            }
        
        # Evaluate relevance if query is provided
        relevance_score = 0.5
        if query:
            # Check for query terms in response
            query_terms = set(re.findall(r'\b\w+\b', query.lower()))
            significant_terms = [term for term in query_terms if len(term) > 3 and term not in STOPWORDS]
            
            if significant_terms:
                response_lower = response.lower()
                matching_terms = sum(1 for term in significant_terms if term in response_lower)
                relevance_score = min(1.0, matching_terms / len(significant_terms))
        
        # Evaluate coherence
        coherence_score = 0.5
        sentences = re.split(r'(?<=[.!?])\s+', response)
        if len(sentences) > 1:
            # Check for logical transitions between sentences
            transition_words = ['therefore', 'however', 'additionally', 'furthermore', 'consequently', 
                               'meanwhile', 'nevertheless', 'thus', 'although', 'despite']
            has_transitions = any(word in response.lower() for word in transition_words)
            
            # Check for consistent tense
            tense_consistency = 0.8  # Default assumption of consistency
            
            # Combine factors
            coherence_score = 0.5 + (0.25 if has_transitions else 0) + (0.25 * tense_consistency)
        
        # Detect common issues
        issues = []
        
        # Check for AI self-references
        if re.search(r'\b(I am an AI|As an AI|as an AI language model)\b', response, re.IGNORECASE):
            issues.append("self_reference")
            coherence_score -= 0.2
        
        # Check for repetition
        if len(response) > 200:  # Only check longer responses
            paragraphs = re.split(r'\n\n+', response)
            repeated_content = False
            
            for i in range(len(paragraphs)):
                for j in range(i+1, len(paragraphs)):
                    similarity = self._calculate_text_similarity(paragraphs[i], paragraphs[j])
                    if similarity > 0.7:  # High similarity threshold
                        repeated_content = True
                        break
            
            if repeated_content:
                issues.append("excessive_repetition")
                coherence_score -= 0.2
        
        # Check for appropriate length
        word_count = len(response.split())
        length_score = 0.0
        
        if 50 <= word_count <= 1000:
            # Good length range
            length_score = 1.0
        elif word_count < 50:
            # Too short
            length_score = word_count / 50
            issues.append("too_short")
        elif word_count > 1000:
            # Very long - still acceptable but not optimal
            length_score = 1.0 - min(0.3, (word_count - 1000) / 2000)
            if word_count > 2000:
                issues.append("excessive_length")
        
        # Check for evidence of truncation
        if response.endswith(('...', '…')) or re.search(r'I will continue|to be continued|part \d+$', response):
            issues.append("truncated_response")
            length_score -= 0.3
        
        # Evaluate structure quality
        structure_score = 0.5  # Base score
        
        # Count paragraphs (text blocks separated by double newlines)
        paragraphs = re.split(r'\n\n+', response)
        num_paragraphs = len(paragraphs)
        
        # Count bullet points or numbered lists
        list_items = re.findall(r'^\s*[-*•]|\d+\.\s+', response, re.MULTILINE)
        num_list_items = len(list_items)
        
        # Count code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        num_code_blocks = len(code_blocks)
        
        # Bonus for appropriate paragraphing
        if 3 <= num_paragraphs <= 10:
            structure_score += 0.1
        
        # Bonus for including lists
        if num_list_items > 0:
            structure_score += 0.1
        
        # Bonus for code blocks
        if num_code_blocks > 0:
            structure_score += 0.1
        
        # Combine all scores for an overall quality score
        # Weight the different aspects of quality
        overall_score = (
            (relevance_score * 0.3) +      # Relevance 30%
            (coherence_score * 0.3) +      # Coherence 30%
            (length_score * 0.2) +         # Length appropriateness 20%
            (structure_score * 0.2)        # Structure quality 20%
        )
        
        # Ensure score is properly bounded
        overall_score = max(0.0, min(1.0, overall_score))
        
        # Return comprehensive quality assessment
        return {
            "overall": overall_score,
            "relevance": relevance_score,
            "coherence": coherence_score,
            "correctness": 0.5,  # Placeholder - hard to evaluate without ground truth
            "helpfulness": overall_score,  # Approximation based on overall quality
            "structure": structure_score,
            "length": length_score,
            "issues": issues,
        }

    def validate_response(self, response: str, query: str = None) -> Dict[str, Any]:
        """
        Validates if a response meets quality standards and checks for refusal patterns.
        
        Args:
            response: The response text to validate
            query: Original query for context
            
        Returns:
            Dictionary with validation result and details
        """
        if not response or len(response.strip()) < 10:
            return {
                "valid": False,
                "reason": "empty_or_too_short",
                "score": 0.0
            }
        
        # Evaluate overall quality
        quality = self.evaluate_response_quality(response, query)
        overall_score = quality["overall"]
        
        # Check for refusal patterns with contextual assessment
        refusal_patterns = [
            r"I'm (sorry|afraid) (but )?I (cannot|can't|am unable to|don't have the ability to)",
            r"I (don't|cannot|can't) (assist|help|provide|engage|generate|respond)",
            r"I (won't|will not|can't|cannot|am not able to) (create|provide|generate|produce|assist)",
            r"(cannot|can't|unable to|not able to) (fulfill|complete|perform|carry out) (this|your|such a) (request|task)",
            r"(against|violates) (my|the|OpenAI's|AI's|your assistant's) (ethical|moral|programming|use|content) (guidelines|principles|policy|policies)"
        ]
        
        refusal_detected = False
        refusal_context = ""
        
        for pattern in refusal_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                refusal_detected = True
                # Get surrounding context (100 chars before and after)
                start = max(0, match.start() - 100)
                end = min(len(response), match.end() + 100)
                refusal_context = response[start:end]
                break
        
        # If refusal detected, check if it's a contextual refusal vs. a full response refusal
        if refusal_detected:
            # Check if refusal is just a small part of a longer, otherwise helpful response
            refusal_ratio = len(refusal_context) / len(response)
            if refusal_ratio < 0.3 and overall_score > 0.6:
                # This is likely a contextual refusal within an otherwise good response
                refusal_detected = False
        
        # Determine appropriate threshold based on complexity
        query_complexity = 0.5  # Default medium complexity
        if query:
            # Estimate complexity from query
            word_count = len(query.split())
            if word_count > 30:
                query_complexity = 0.7  # Complex query
            elif word_count < 10:
                query_complexity = 0.3  # Simple query
        
        # Adjust quality threshold based on complexity
        # More complex queries get a slightly lower threshold
        quality_threshold = 0.5 - (query_complexity * 0.1)
        
        # Check against threshold
        below_quality_threshold = overall_score < quality_threshold
        
        # Determine validity with reason
        valid = True
        reason = "acceptable"
        
        if refusal_detected:
            valid = False
            reason = "refusal_pattern"
        elif below_quality_threshold:
            valid = False
            if quality["issues"]:
                reason = quality["issues"][0]  # Use the first detected issue
            else:
                reason = "low_quality"
        
        # Return validation result
        return {
            "valid": valid,
            "score": overall_score,
            "reason": reason,
            "refusal_detected": refusal_detected,
            "quality_details": quality
        }
        
    def get_model_weight(self, model_name: str, query_type: str = None) -> float:
        """
        Get the weight for a specific model, optionally adjusted for query type.
        Uses the new model capabilities system for more precise weighting.
        
        Args:
            model_name: The name of the model
            query_type: Optional query type (technical, creative, etc.)
            
        Returns:
            float: The model's weight (0.0-1.0)
        """
        # Clean up model name (handle common variations)
        clean_name = model_name.lower().strip()
        
        # Normalize model names to match our capability profiles
        if 'gpt-4' in clean_name or 'gpt4' in clean_name:
            if 'gpt-4o' in clean_name or 'gpt4o' in clean_name:
                clean_name = 'gpt-4o'
            else:    
                clean_name = 'gpt-4'
        elif 'gpt-3.5' in clean_name or 'gpt3.5' in clean_name:
            clean_name = 'gpt-3.5-turbo'
        elif 'claude-3-opus' in clean_name or 'claude3opus' in clean_name:
            clean_name = 'claude-3-opus'
        elif 'claude-3-sonnet' in clean_name or 'claude3sonnet' in clean_name:
            clean_name = 'claude-3-sonnet'
        elif 'claude-3-haiku' in clean_name or 'claude3haiku' in clean_name:
            clean_name = 'claude-3-haiku'
        elif 'claude-3' in clean_name or 'claude3' in clean_name:
            clean_name = 'claude-3-opus'  # Assume Opus if not specified
        elif 'claude' in clean_name:
            clean_name = 'claude-3-opus'  # Assume Opus if just "claude"
        elif 'gemini' in clean_name:
            clean_name = 'gemini-pro'
        elif 'mistral' in clean_name:
            clean_name = 'mistral-medium'
        elif 'cohere' in clean_name:
            clean_name = 'cohere-command'
            
        # First check if we have detailed capabilities for this model
        if clean_name in MODEL_CAPABILITIES:
            # If we have a query type, use the specific capability score
            if query_type:
                # Map query type variations to our standard categories
                effective_query_type = query_type.lower()
                
                # Map similar query types to our standard categories
                if any(term in effective_query_type for term in ['code', 'programming', 'algorithm', 'function']):  
                    effective_query_type = 'coding'
                elif any(term in effective_query_type for term in ['compare', 'versus', 'vs', 'difference']):  
                    effective_query_type = 'comparison'
                elif any(term in effective_query_type for term in ['explain', 'describe', 'what is', 'how does']):  
                    effective_query_type = 'explanation'
                elif any(term in effective_query_type for term in ['analyze', 'reason', 'logic', 'solve']):  
                    effective_query_type = 'reasoning'
                elif any(term in effective_query_type for term in ['create', 'imagine', 'story', 'design']):  
                    effective_query_type = 'creative'
                elif any(term in effective_query_type for term in ['tech', 'science', 'engineering', 'math']):  
                    effective_query_type = 'technical'
                
                # Get the specific capability score if available, otherwise default to general
                return MODEL_CAPABILITIES[clean_name].get(
                    effective_query_type, 
                    MODEL_CAPABILITIES[clean_name].get('general', 0.7)
                )
            else:
                # Return the general capability score if no query type provided
                return MODEL_CAPABILITIES[clean_name].get('general', 0.7)
        
        # Fall back to legacy weights if no capability data available
        base_weight = self.model_weights.get(clean_name, 0.7)  # Default to 0.7 if unknown
        
        # Legacy adjustments for backward compatibility
        if query_type:
            if 'gpt-4' in clean_name and query_type in ['technical', 'code']:
                return min(base_weight + 0.05, 1.0)  # Boost GPT-4 for technical questions
            elif 'claude' in clean_name and query_type in ['creative', 'writing']:
                return min(base_weight + 0.05, 1.0)  # Boost Claude for creative tasks
            elif 'gpt-3.5' in clean_name and query_type in ['simple', 'factual']:
                return min(base_weight + 0.05, 1.0)  # Boost GPT-3.5 for simple factual queries
        
        return base_weight
    
    def weighted_voting(self, 
                       responses: Dict[str, str], 
                       query_type: str = None,
                       quality_scores: Dict[str, float] = None) -> Dict[str, float]:
        """
        Performs weighted voting across model responses.
        
        Args:
            responses: Dictionary mapping model names to their responses
            query_type: Optional type of query for specialized weighting
            quality_scores: Optional pre-computed quality scores for each response
            
        Returns:
            Dictionary mapping model names to their weighted scores
        """
        if not responses:
            return {}
        
        # Calculate weights for each model
        weights = {model: self.get_model_weight(model, query_type) for model in responses.keys()}
        
        # If we have quality scores, multiply them by the model weights
        if quality_scores:
            weighted_scores = {
                model: weights[model] * quality_scores.get(model, 0.5) 
                for model in responses.keys()
            }
        else:
            weighted_scores = weights.copy()
        
        # Normalize scores to sum to 1.0
        total_score = sum(weighted_scores.values())
        if total_score > 0:
            weighted_scores = {model: score/total_score for model, score in weighted_scores.items()}
        
        return weighted_scores
    
    def calculate_agreement_score(self, 
                                 primary_response: str, 
                                 other_responses: List[str]) -> float:
        """
        Calculates how much other responses agree with the primary response.
        
        Args:
            primary_response: The main response being evaluated
            other_responses: List of responses to compare against
            
        Returns:
            float: Agreement score between 0.0 (no agreement) and 1.0 (perfect agreement)
        """
        if not other_responses:
            return 0.5  # Neutral score if no other responses
        
        # Extract key sentences from the primary response
        primary_sentences = self._extract_sentences(primary_response)
        if not primary_sentences:
            return 0.5
        
        # Track agreement scores for each sentence
        sentence_agreement_scores = []
        
        for sentence in primary_sentences:
            # Skip very short sentences as they're not informative
            if len(sentence.split()) < 3:
                continue
                
            # Calculate agreement for this sentence with other responses
            agreement_count = 0
            for other_response in other_responses:
                # Check if the sentence or a similar one appears in the other response
                if self._has_similar_statement(sentence, other_response):
                    agreement_count += 1
            
            # Calculate agreement ratio for this sentence
            agreement_ratio = agreement_count / len(other_responses)
            sentence_agreement_scores.append(agreement_ratio)
        
        # Return average agreement if we have scores, otherwise neutral
        if sentence_agreement_scores:
            return sum(sentence_agreement_scores) / len(sentence_agreement_scores)
        return 0.5
    
    def _extract_sentences(self, text: Union[str, Dict[str, Any]]) -> List[str]:
        """
        Extract sentences from text.
        
        Args:
            text: Input text to process (can be a string or dictionary)
            
        Returns:
            List of sentences
        """
        # Handle case where text is a dictionary with a 'response' field
        if isinstance(text, dict):
            if 'response' in text:
                text = text['response']
            else:
                # Try to convert dict to string as fallback
                text = str(text)
        
        # Ensure text is a string
        if not isinstance(text, str):
            text = str(text)
        
        # Basic sentence splitting (could be enhanced with nltk)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _has_similar_statement(self, statement: str, text: str) -> bool:
        """
        Check if a statement or a similar one appears in the text.
        
        Args:
            statement: The statement to look for
            text: The text to search in
            
        Returns:
            True if a similar statement is found
        """
        # Very basic similarity check - could be enhanced with embeddings
        # Extract key terms (nouns, verbs, adjectives) - simplified version
        words = statement.lower().split()
        important_words = [w for w in words if len(w) > 3]
        
        # If the statement is too short to extract meaningful words, use the whole statement
        if len(important_words) < 2:
            important_words = words
        
        # Check if most important words appear in the text
        text_lower = text.lower()
        matches = sum(1 for word in important_words if word in text_lower)
        match_ratio = matches / len(important_words) if important_words else 0
        
        return match_ratio > 0.7  # Consider similar if 70% of important words match
    
    def confidence_analysis(self, response: str) -> float:
        """
        Analyzes a response to detect confidence/certainty levels.
        
        Args:
            response: The model response text
            
        Returns:
            float: Confidence score between 0.0 (uncertain) and 1.0 (very confident)
        """
        # Keywords indicating uncertainty
        uncertainty_indicators = [
            "i'm not sure", "might be", "could be", "possibly", 
            "perhaps", "probably", "i think", "may", "may not",
            "uncertain", "unclear", "i don't know", "i don't think",
            "it's hard to say", "it's difficult to determine"
        ]
        
        # Keywords indicating confidence
        confidence_indicators = [
            "definitely", "certainly", "absolutely", "without doubt",
            "clearly", "is", "are", "was", "will", "must", "always",
            "never", "indeed", "proves", "demonstrates", "shows"
        ]
        
        response_lower = response.lower()
        
        # Count occurrences of indicators
        uncertainty_count = sum(response_lower.count(indicator) for indicator in uncertainty_indicators)
        confidence_count = sum(response_lower.count(indicator) for indicator in confidence_indicators)
        
        # Calculate basic confidence score
        total_indicators = uncertainty_count + confidence_count
        if total_indicators == 0:
            return 0.7  # Default to moderate confidence
        
        confidence_score = confidence_count / total_indicators
        
        # Adjust for response length
        words = response.split()
        length_factor = min(1.0, len(words) / 100)  # Longer answers tend to be more confident
        
        # Final score combines both factors
        final_score = (confidence_score * 0.7) + (length_factor * 0.3)
        
        return min(1.0, max(0.1, final_score))  # Ensure score is between 0.1 and 1.0
    
    def probabilistic_consensus(self, 
                               responses: Dict[str, str], 
                               quality_scores: Dict[str, float],
                               query_type: str = None) -> Dict[str, float]:
        """
        Calculate consensus scores for responses using probabilistic methods.
        
        Args:
            responses: Dictionary mapping model names to their responses
            quality_scores: Dictionary mapping model names to quality scores
            query_type: Optional query type for specialized weighting
            
        Returns:
            Dictionary mapping model names to consensus scores
        """
        if len(responses) <= 1:
            # No consensus possible with 0 or 1 response
            return {model: 0.5 for model in responses}
        
        # Calculate agreement scores for each response compared to others
        agreement_scores = {}
        for model_name, response in responses.items():
            other_responses = [r for m, r in responses.items() if m != model_name]
            agreement_scores[model_name] = self.calculate_agreement_score(response, other_responses)
        
        # Calculate confidence for each response
        confidence_scores = {model: self.confidence_analysis(response) 
                            for model, response in responses.items()}
        
        # Combine quality, confidence, and agreement with model weights
        consensus_scores = {}
        for model_name in responses:
            model_weight = self.get_model_weight(model_name, query_type)
            quality = quality_scores.get(model_name, 0.5)
            confidence = confidence_scores[model_name]
            agreement = agreement_scores[model_name]
            
            # Weighted combination
            consensus_scores[model_name] = (
                0.4 * quality +        # Quality score 
                0.3 * confidence +     # Confidence score
                0.3 * agreement        # Agreement with other models
            ) * model_weight           # Scaled by model reliability
        
        return consensus_scores
    
    def rank_responses(self, 
                      responses: Dict[str, str], 
                      task_info: Any = None,
                      quality_scores: Optional[Dict[str, float]] = None,
                      voting_results: Optional[Dict[str, float]] = None,
                      consensus_scores: Optional[Dict[str, float]] = None,
                      confidence_results: Optional[Dict[str, float]] = None,
                      query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Rank responses using ensemble techniques including weighted voting and consensus.
        
        Args:
            responses: Dictionary mapping model names to their responses
            task_info: Task information containing query type and other metadata
            quality_scores: Optional pre-computed quality scores
            voting_results: Optional pre-computed voting results
            consensus_scores: Optional pre-computed consensus scores
            confidence_results: Optional pre-computed confidence results
            query_type: Optional query type (technical, creative, etc.)
            
        Returns:
            Dictionary with scores, rankings, and best model information
        """
        if not responses:
            return {
                'scores': {},
                'ranked_models': [],
                'best_model': None,
                'capability_scores': {},
                'ranking_details': {},
                'quality_details': {}
            }
        
        # Extract query type from task_info
        extracted_query_type = None
        if isinstance(task_info, dict):
            extracted_query_type = task_info.get('query_type') or task_info.get('task_type')
        elif isinstance(task_info, str):
            try:
                task_dict = json.loads(task_info)
                if isinstance(task_dict, dict):
                    extracted_query_type = task_dict.get('query_type') or task_dict.get('task_type')
            except:
                pass
                
        effective_query_type = extracted_query_type or query_type or 'general'
        effective_query_type = effective_query_type.lower()
        
        # 🚀 Force GPT-4o for factual queries
        if effective_query_type in ["factual", "knowledge", "fact"]:
            preferred_model = "gpt-4o"
            if preferred_model in responses:
                logger.info(f"Forcing {preferred_model} for factual query type: {effective_query_type}")
                ranked_responses = [(preferred_model, 1.0)]
                return {
                    'scores': {preferred_model: 1.0},
                    'ranked_models': ranked_responses,
                    'best_model': preferred_model,
                    'capability_scores': {preferred_model: 1.0},
                    'query_type': effective_query_type,
                    'forced_selection': True
                }
        
        # Process task_info to extract query_type and hierarchical workflow information
        extracted_query_type = None
        lead_model = None
        hierarchical_mode = False
        response_weights = {}
        
        if isinstance(task_info, str):
            try:
                parsed_task_info = json.loads(task_info)
                if isinstance(parsed_task_info, dict):
                    extracted_query_type = parsed_task_info.get('query_type') or parsed_task_info.get('task_type')
                    # Extract hierarchical workflow information
                    lead_model = parsed_task_info.get('lead_model')
                    hierarchical_mode = parsed_task_info.get('hierarchical', False)
                    response_weights = parsed_task_info.get('response_weights', {})
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"Could not parse task_info as JSON: {task_info}")
        elif isinstance(task_info, dict):
            extracted_query_type = task_info.get('query_type') or task_info.get('task_type')
            # Also check for category/type in case those are used instead
            if not extracted_query_type:
                extracted_query_type = task_info.get('category') or task_info.get('type')
            # Extract hierarchical workflow information
            lead_model = task_info.get('lead_model')
            hierarchical_mode = task_info.get('hierarchical', False)
            response_weights = task_info.get('response_weights', {})
        
        # Use the best available query type or default to general
        effective_query_type = extracted_query_type or query_type or 'general'
        logger.info(f"Using query_type: {effective_query_type}")
        
        # Evaluate structure quality of each response
        structure_scores = {}
        for model, response in responses.items():
            # Skip if response is not a string or is too short
            if not isinstance(response, str) or len(response) < 20:
                structure_scores[model] = 0.0
                continue
                
            # Convert to string if it's a dict or other object
            if not isinstance(response, str):
                try:
                    response_text = str(response)
                except:
                    response_text = ""
            else:
                response_text = response
                
            structure_score = 0.5  # Start with a base score
            
            # PENALIZE GENERIC TEMPLATES - Check for generic template phrases with MUCH STRONGER penalty
            generic_phrases = [
                "here's what i know", 
                "a few important points", 
                "this information should help",
                "it's worth noting that",
                "provides a reasonable response",
                "here are the key points",
                "to address your question",
                "there are a few important points to consider",
                "covering the main aspects",
                "in response to your question",
                "let me address your query"
            ]
            
            # Enhanced detection for factual queries using regex patterns
            factual_patterns = [
                r'\bwhat is\b', r'\bwho is\b', r'\bwhen did\b', r'\bwhere is\b',
                r'\bhow many\b', r'\bcapital of\b', r'\blargest\b', r'\bsmallest\b',
                r'\bpopulation of\b', r'\bin what year\b', r'\bwho was\b'
            ]
            
            is_factual_query = False
            if query_type and query_type.lower() in ["fact_simple", "factual", "knowledge", "fact"]:
                is_factual_query = True
            elif isinstance(task_info, str) and any(re.search(pattern, task_info.lower()) for pattern in factual_patterns):
                is_factual_query = True
                logger.info(f"Detected factual query from pattern matching: '{task_info[:50]}...'")
            
            # 🚨 EXTREMELY AGGRESSIVE blocking for templated responses on factual queries
            if is_factual_query:
                logger.info(f"🚨 FACTUAL QUERY DETECTED - Applying strict template blocking")
                
                # Boost GPT-4o's score for factual queries
                if model.lower() in ["gpt-4o", "gpt-4o-mini", "gpt-4"]:
                    structure_score += 0.5
                    logger.info(f"🚀 BOOSTED {model} structure score for factual query by +0.5")
                
                # Penalize Llama models for factual queries regardless of template
                if model.lower() in ["llama", "llama2"]:
                    structure_score -= 1.0
                    logger.info(f"🚫 PENALIZED {model} for factual query by -1.0 (aggressive downgrade)")
                
                # Check for template phrases and heavily penalize
                if any(phrase in response_text.lower() for phrase in generic_phrases):
                    structure_score = min(structure_score, -2.0)  # 🚨 Extreme negative score for templated factual responses
                    logger.info(f"⛔ CRITICALLY BLOCKED {model} for using template phrases on factual query")
            # For non-factual queries, still apply strong penalty
            elif any(phrase in response_text.lower() for phrase in generic_phrases):
                structure_score -= 0.6  # Strong penalty for generic template responses
                logger.info(f"Model {model} HEAVILY penalized for generic template phrases")
                
                # Additional 0.2 penalty for llama models specifically when they use templates
                if model.lower() in ["llama", "llama2"]:
                    structure_score -= 0.2  # Extra penalty for llama models using templates
                    logger.info(f"Applied extra template penalty to {model} model")
            
            # Check for paragraphs (multiple line breaks)
            if '\n\n' in response_text:
                structure_score += 0.2
                
            # Check for lists (bullets, numbering)
            if any(marker in response_text for marker in ['•', '-', '*', '1.', '2.', '3.']):
                structure_score += 0.2
                
            # Check for headers or emphasis
            if any(header in response_text for header in ['# ', '## ', '**']):
                structure_score += 0.2
                
            # Check for code blocks in technical queries
            if '```' in response_text and effective_query_type in ['technical', 'code']:
                structure_score += 0.3
            
            # Assess appropriate length (not too short, not too verbose)
            word_count = len(response_text.split())
            if 100 <= word_count <= 500:  # Ideal length range
                structure_score += 0.1
            elif word_count > 1000:  # Too verbose
                structure_score -= 0.1
            elif word_count < 50:  # Too short
                structure_score -= 0.2
                
            # Normalize to 0-1 range
            structure_scores[model] = max(0.0, min(structure_score, 1.0))
            logger.info(f"Model {model} structure score: {structure_scores[model]:.2f}")
        
        # If quality scores aren't provided, use neutral values
        if not quality_scores:
            quality_scores = {model: 0.7 for model in responses}
        
        # Use provided scores or calculate them if not provided, with robust type checking
        # Handle case where voting_results might be a string or other non-dictionary type
        if isinstance(voting_results, dict):
            model_voting_scores = voting_results
        else:
            try:
                model_voting_scores = self.weighted_voting(responses, effective_query_type, quality_scores)
                # Safety check - ensure we got a dictionary
                if not isinstance(model_voting_scores, dict):
                    logger.warning(f"⚠️ weighted_voting returned non-dict type: {type(model_voting_scores).__name__}")
                    model_voting_scores = {model: 0.5 for model in responses}  # Fallback to neutral scores
            except Exception as e:
                logger.error(f"⚠️ Error in weighted_voting: {e}")
                model_voting_scores = {model: 0.5 for model in responses}  # Fallback to neutral scores
        
        # Handle case where consensus_scores might be a string or other non-dictionary type
        if isinstance(consensus_scores, dict):
            model_consensus_scores = consensus_scores
        else:
            try:
                model_consensus_scores = self.probabilistic_consensus(responses, quality_scores, effective_query_type)
                # Safety check - ensure we got a dictionary
                if not isinstance(model_consensus_scores, dict):
                    logger.warning(f"⚠️ probabilistic_consensus returned non-dict type: {type(model_consensus_scores).__name__}")
                    model_consensus_scores = {model: 0.5 for model in responses}  # Fallback to neutral scores
            except Exception as e:
                logger.error(f"⚠️ Error in probabilistic_consensus: {e}")
                model_consensus_scores = {model: 0.5 for model in responses}  # Fallback to neutral scores
        
        # Handle case where confidence_results might be a string or other non-dictionary type
        if isinstance(confidence_results, dict):
            model_confidence_scores = confidence_results
        else:
            try:
                # Create confidence scores dictionary safely
                model_confidence_scores = {}
                for model, text in responses.items():
                    try:
                        # Get confidence from response analysis
                        score = self.confidence_analysis(text)
                        # Boost confidence based on model capability for the query type
                        capability_boost = self.get_model_weight(model, effective_query_type)
                        # Combine confidence and capability (70% capability, 30% confidence)
                        adjusted_score = (score * 0.3) + (capability_boost * 0.7)
                        model_confidence_scores[model] = adjusted_score
                        logger.info(f"Model {model} confidence: {score:.2f}, capability: {capability_boost:.2f}, adjusted: {adjusted_score:.2f}")
                    except Exception as e:
                        logger.error(f"⚠️ Error analyzing confidence for {model}: {e}")
                        model_confidence_scores[model] = 0.5  # Fallback to neutral score
            except Exception as e:
                logger.error(f"⚠️ Error in confidence analysis: {e}")
                model_confidence_scores = {model: 0.5 for model in responses}  # Fallback to neutral scores
        
        # Combine all scores with appropriate weights, with additional error handling
        combined_scores = {}
        model_capabilities = {}
        capability_reasons = {}
        
        for model in responses:
            # Safely get scores with robust error handling
            try:
                voting_score = model_voting_scores.get(model, 0.5) if isinstance(model_voting_scores, dict) else 0.5
                consensus_score = model_consensus_scores.get(model, 0.5) if isinstance(model_consensus_scores, dict) else 0.5
                confidence_score = model_confidence_scores.get(model, 0.5) if isinstance(model_confidence_scores, dict) else 0.5
                
                # Get model capability for this query type
                capability_score = self.get_model_weight(model, effective_query_type)
                model_capabilities[model] = capability_score
                
                # Get structure score for this model
                structure_score = structure_scores.get(model, 0.0)
                
                # Get model cost for cost-efficiency scoring
                try:
                    # Lower cost = higher score (inverse relationship)
                    model_cost = get_cost_per_1k_tokens(model)
                    # Normalize cost to a 0-1 score (inverted so lower cost = higher score)
                    max_cost = 0.05  # Reference maximum cost per 1k tokens (for GPT-4)
                    cost_efficiency_score = 1.0 - min(model_cost / max_cost, 1.0)
                    
                    # Simple queries should prioritize cost efficiency more
                    is_simple_query = effective_query_type in ['general', 'simple', 'factual'] and \
                                     not any(tag in effective_query_type for tag in ['technical', 'complex', 'code'])
                    
                    if is_simple_query:
                        cost_weight = 0.25  # Increase cost weight for simple queries (25%)
                        logger.info(f"Applying higher cost weight ({cost_weight}) for simple query type: {effective_query_type}")
                    else:
                        cost_weight = 0.10  # Lower cost weight for complex queries (10%)
                        
                    logger.info(f"Model {model} cost: ${model_cost:.4f}/1k tokens, efficiency score: {cost_efficiency_score:.2f}")
                except Exception as e:
                    logger.warning(f"Error calculating cost efficiency for {model}: {e}")
                    cost_efficiency_score = 0.5  # Neutral score
                    cost_weight = 0.10  # Default weight
                
                # Weight the different scoring methods with emphasis on capability, confidence, structure AND cost
                score = (
                    (voting_score * 0.15) +                # Weighted voting (15%)
                    (consensus_score * 0.15) +            # Consensus (15%)
                    (confidence_score * 0.15) +           # Confidence (15%)
                    (capability_score * (0.30 - cost_weight)) +  # Model capability (adjusted down)
                    (structure_score * 0.15) +            # Structure quality (15%)
                    (cost_efficiency_score * cost_weight)  # Cost efficiency (10-25% based on query type)
                )
                
                # Apply hierarchical workflow boosting for lead model
                if hierarchical_mode and lead_model and model == lead_model:
                    lead_boost = 0.15  # 15% boost for lead model
                    score += lead_boost
                    logger.info(f"Applying lead model boost of {lead_boost} to {model} in hierarchical workflow")
                # Apply custom response weights from hierarchical workflow if available
                elif hierarchical_mode and model in response_weights:
                    weight_multiplier = response_weights.get(model, 1.0)
                    original_score = score
                    score *= weight_multiplier
                    logger.info(f"Applied custom weight {weight_multiplier} to {model}, adjusting score from {original_score:.3f} to {score:.3f}")
                
                combined_scores[model] = score
                
                logger.info(f"Model {model} final score: {combined_scores[model]:.3f} (voting={voting_score:.2f}, "
                          f"consensus={consensus_score:.2f}, confidence={confidence_score:.2f}, "
                          f"capability={capability_score:.2f}, structure={structure_score:.2f})")
                          
            except Exception as e:
                logger.error(f"⚠️ Error combining scores for {model}: {e}")
                combined_scores[model] = 0.5  # Fallback to neutral score
                model_capabilities[model] = 0.5  # Fallback capability score
        
        # Sort by score (descending)
        ranked_responses = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Generate detailed reasons for each model's ranking
        for model in responses:
            # We already calculated model capabilities above with the effective_query_type
            capability = model_capabilities.get(model, 0.5)
            
            # Generate reasons based on scores and capabilities with more specificity
            reasons = []
            try:
                voting_score = model_voting_scores.get(model, 0.5) if isinstance(model_voting_scores, dict) else 0.5
                consensus_score = model_consensus_scores.get(model, 0.5) if isinstance(model_consensus_scores, dict) else 0.5
                confidence_score = model_confidence_scores.get(model, 0.5) if isinstance(model_confidence_scores, dict) else 0.5
                
                # Add specific reasons based on scores
                if voting_score > 0.7:
                    reasons.append('high_relevance')
                if consensus_score > 0.7:
                    reasons.append('strong_coherence')
                if confidence_score > 0.7:
                    reasons.append('confident_response')
                if capability > 0.8:  # Higher threshold for expertise
                    reasons.append(f'{effective_query_type}_expertise')
                # Add structure-related reasons
                structure_score = structure_scores.get(model, 0.0)
                if structure_score > 0.7:
                    reasons.append('well_structured_response')
                elif structure_score < 0.3:
                    reasons.append('poorly_structured_response')
                    
                # Add more nuanced reasoning based on score patterns
                if capability > 0.9 and confidence_score > 0.8:
                    reasons.append('optimal_model_match')
                if voting_score > 0.8 and consensus_score > 0.8:
                    reasons.append('consensus_leader')
            except Exception as e:
                logger.warning(f"Error generating reasons for {model}: {e}")
            
            # Ensure we have at least one reason
            if not reasons:
                reasons = ['general_quality']
                
            capability_reasons[model] = reasons
        
        # Create detailed rankings with reasons and more information
        detailed_rankings = []
        for model, score in ranked_responses:
            detailed_rankings.append({
                'model': model,
                'score': score,
                'capability': model_capabilities.get(model, 0.5),
                'reasons': capability_reasons.get(model, ['general_quality']),
                'query_type': effective_query_type
            })
        
        # Prepare cost analysis information
        model_costs = {}
        cost_efficiency_scores = {}
        for model in responses:
            try:
                model_costs[model] = get_cost_per_1k_tokens(model)
                # Calculate normalized cost efficiency score
                max_cost = 0.05  # Reference maximum cost
                cost_efficiency_scores[model] = 1.0 - min(model_costs[model] / max_cost, 1.0)
            except Exception:
                model_costs[model] = None
                cost_efficiency_scores[model] = 0.5  # Neutral score
        
        # Estimate potential cost savings if a lower-cost model was selected
        if ranked_responses and len(ranked_responses) > 1:
            best_model = ranked_responses[0][0]
            # Find the best lower-cost model in the top 3
            lower_cost_models = []
            for model, score in ranked_responses[1:min(4, len(ranked_responses))]:
                try:
                    if model_costs.get(model, 0) < model_costs.get(best_model, 0) and score > 0.7 * ranked_responses[0][1]:
                        lower_cost_models.append((model, score, model_costs.get(model, 0)))
                except Exception:
                    pass
            
            # If we found any viable lower-cost models
            if lower_cost_models:
                # Sort by score (higher is better)
                lower_cost_models.sort(key=lambda x: x[1], reverse=True)
                best_alternative = lower_cost_models[0][0]
                savings_percent = estimate_cost_savings(best_model, best_alternative)
                cost_analysis = {
                    'best_model_cost': model_costs.get(best_model),
                    'alternative_model': best_alternative,
                    'alternative_model_cost': model_costs.get(best_alternative),
                    'potential_savings_percent': savings_percent,
                    'viable_cost_reduction': savings_percent > 20 and lower_cost_models[0][1] > 0.75
                }
            else:
                cost_analysis = {
                    'best_model_cost': model_costs.get(best_model),
                    'alternative_model': None,
                    'viable_cost_reduction': False
                }
        else:
            cost_analysis = {'viable_cost_reduction': False}
            
        # Create results dictionary with enhanced information and metadata
        result = {
            'scores': combined_scores,
            'ranked_models': ranked_responses,
            'detailed_rankings': detailed_rankings,  # More descriptive key name
            'best_model': ranked_responses[0][0] if ranked_responses else None,
            'query_type': effective_query_type,  # Include the query type used for scoring
            'voting_scores': model_voting_scores,
            'consensus_scores': model_consensus_scores,
            'confidence_scores': model_confidence_scores,
            'capability_scores': model_capabilities,
            'structure_scores': structure_scores,  # Add structure scores to output
            'hierarchical': hierarchical_mode,     # Indicate if hierarchical workflow was used
            'lead_model': lead_model,              # Include the lead model if applicable
            'cost_efficiency_scores': cost_efficiency_scores,  # Add cost efficiency scores
            'model_costs': model_costs,            # Add model costs information
            'cost_analysis': cost_analysis,        # Add cost analysis
            'ranking_explanation': f'Models ranked by combined scoring with emphasis on {effective_query_type} capability, response structure, and cost efficiency' +
                                (f', with hierarchical workflow lead model ({lead_model})' if hierarchical_mode and lead_model else '')
        }
        
        # Log the final selection for debugging
        if ranked_responses:
            best_model = ranked_responses[0][0]
            best_score = ranked_responses[0][1]
            best_reasons = capability_reasons.get(best_model, ['general_quality'])
            logger.info(f"Selected best model: {best_model} with score {best_score:.3f} for query type {effective_query_type}")
            logger.info(f"Selection reasons: {', '.join(best_reasons)}")
        
        return result
    
    def select_best_response(self, 
                            responses: Dict[str, str] = None, 
                            query: str = None,
                            quality_scores: Optional[Dict[str, float]] = None,
                            query_type: Optional[str] = None,
                            ranking_results: Optional[Dict[str, Any]] = None,
                            budget_constraints: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Select the best response using ensemble validation techniques.
        
        Args:
            responses: Dictionary mapping model names to their responses
            query: The original user query
            quality_scores: Optional pre-computed quality scores
            query_type: Optional query type (technical, creative, etc.)
            ranking_results: Optional pre-computed ranking results
            budget_constraints: Optional budget constraint information including:
                - budget_risk: Risk level ('low', 'medium', 'high', 'critical')
                - force_cost_efficiency: Whether to force cost-efficient model selection
            
        Returns:
            Tuple containing:
            - Selected model name
            - Result dictionary with scores and metadata
        """
        # Initialize budget-related variables
        budget_risk = "low"
        force_cost_efficiency = False
        auto_switching_active = False
        cost_savings_mode = False
        
        # Process budget constraints if provided
        if budget_constraints and isinstance(budget_constraints, dict):
            budget_risk = budget_constraints.get('budget_risk', 'low')
            force_cost_efficiency = budget_constraints.get('force_cost_efficiency', False)
            auto_switching_active = budget_risk in ['high', 'critical']
            cost_savings_mode = budget_risk in ['medium', 'high', 'critical'] or force_cost_efficiency
            
            logger.info(f"Budget risk level: {budget_risk}, cost savings mode: {cost_savings_mode}, "
                       f"auto-switching: {auto_switching_active}")
        
        # Use the provided ranking results or compute them
        if ranking_results is None:
            if responses is None:
                logger.warning("No responses provided for selecting best response")
                return None, {"error": "No responses provided"}
            
            ranking_results = self.rank_responses(responses, query, quality_scores, query_type)
        
        # Extract information from the ranking results
        if not ranking_results.get('ranked_models'):
            logger.warning("No valid responses to rank")
            return None, {"error": "No valid responses"}
        
        # Get the top-ranked model and its score
        best_model = ranking_results['best_model']
        best_score = ranking_results['scores'].get(best_model, 0.0) if best_model else 0.0
        
        # Apply cost efficiency analysis for budget constraint enforcement
        cost_analysis = ranking_results.get('cost_analysis', {})
        alternative_model = cost_analysis.get('alternative_model')
        potential_savings = cost_analysis.get('potential_savings_percent', 0)
        viable_cost_reduction = cost_analysis.get('viable_cost_reduction', False)
        
        # Check if we need to auto-switch to a cheaper model based on budget constraints
        auto_switched = False
        original_best_model = best_model
        
        if viable_cost_reduction and alternative_model:
            # Auto-switch if budget risk is high/critical, or if medium risk with significant savings,
            # or if forced to optimize costs
            should_auto_switch = (auto_switching_active) or \
                             (budget_risk == 'medium' and potential_savings > 40) or \
                             force_cost_efficiency
            
            if should_auto_switch:
                logger.warning(f"AUTO-SWITCHING from {best_model} to {alternative_model} due to budget constraints")
                logger.warning(f"Budget risk: {budget_risk}, Potential savings: {potential_savings}%")
                best_model = alternative_model
                auto_switched = True
        
        # Return the best model and metadata with cost information
        result = {
            "best_model": best_model,
            "score": best_score,
            "rankings": ranking_results['ranked_models'],
            "confidence": ranking_results.get('confidence_scores', {}).get(best_model, 0.0) if best_model and responses else 0.0,
            "agreement_level": "high" if best_score > 0.8 else "medium" if best_score > 0.6 else "low",
            "cost_optimization": {
                "auto_switched": auto_switched,
                "original_model": original_best_model if auto_switched else None,
                "budget_risk": budget_risk,
                "potential_savings": potential_savings if alternative_model else 0,
                "force_cost_efficiency": force_cost_efficiency
            },
            "cost_analysis": cost_analysis
        }
        
        if auto_switched:
            logger.info(f"Auto-switched from {original_best_model} to {best_model} (budget risk: {budget_risk})")
        else:
            logger.info(f"Selected best response from model {best_model} with score {best_score:.2f}")
            
        return best_model, result
    
    def blend_comparison_responses(self, responses, ranking_result):
        """
        Specialized blending for comparative queries that require balanced perspectives.
        
        Args:
            responses: Dictionary of model responses
            ranking_result: Result of ranking the responses
            
        Returns:
            Blended response emphasizing balanced comparison
        """
        logger.info("Using specialized comparison blending strategy")
        
        # Get top 3 models and their responses
        top_models = [item['model'] for item in ranking_result.get('detailed_rankings', [])[:3]]
        if len(top_models) < 2:
            return responses[top_models[0]] if top_models else "Insufficient responses for comparison"
        
        # Extract key comparison points from each response
        points_by_model = {}
        for model in top_models:
            if model in responses:
                # Extract sentences that contain comparison indicators
                text = responses[model]
                sentences = re.split(r'(?<=[.!?])\s+', text)
                comparison_sentences = [s for s in sentences if re.search(r'(compared|versus|vs\.|better|worse|different|similar|advantage|disadvantage)', s, re.IGNORECASE)]
                points_by_model[model] = comparison_sentences
        
        # Construct a balanced response
        blended = []
        
        # Start with intro from highest ranked model
        intro_sentences = re.split(r'(?<=[.!?])\s+', responses[top_models[0]])[:2]
        blended.extend(intro_sentences)
        blended.append("\n\n")
        
        # Add comparison points from all models
        for model in top_models:
            if model in points_by_model and points_by_model[model]:
                # Add 2-3 unique points from each model
                unique_points = []
                for point in points_by_model[model][:5]:  # Limit to 5 candidate points
                    if not any(self._has_similar_statement(point, p) for p in unique_points):
                        unique_points.append(point)
                    if len(unique_points) >= 3:  # Get up to 3 unique points
                        break
                blended.extend(unique_points)
                blended.append("\n")
        
        # Add conclusion from highest ranked model
        conclusion_sentences = re.split(r'(?<=[.!?])\s+', responses[top_models[0]])[-2:]
        blended.append("\n")
        blended.extend(conclusion_sentences)
        
        return " ".join(blended)

    def blend_technical_responses(self, responses, ranking_result):
        """
        Specialized blending for technical queries, emphasizing accuracy and code.
        
        Args:
            responses: Dictionary of model responses
            ranking_result: Result of ranking the responses
            
        Returns:
            Blended response optimized for technical accuracy
        """
        logger.info("Using specialized technical blending strategy")
        
        # Get top 3 models and their responses
        top_models = [item['model'] for item in ranking_result.get('detailed_rankings', [])[:3]]
        if len(top_models) < 2:
            return responses[top_models[0]] if top_models else "Insufficient responses for technical blending"
        
        # Primary response comes from the top-ranked model
        primary_response = responses[top_models[0]]
        
        # Extract code blocks from all responses
        code_blocks_by_model = {}
        for model in top_models:
            if model in responses:
                text = responses[model]
                # Find all code blocks
                blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
                if blocks:
                    code_blocks_by_model[model] = blocks
        
        # If the primary model has code blocks, use them
        if top_models[0] in code_blocks_by_model and code_blocks_by_model[top_models[0]]:
            # The primary model's response is sufficient
            return primary_response
        
        # If primary doesn't have code but others do, blend them in
        if code_blocks_by_model:
            # Use the primary response text but add code blocks from other models
            for model in top_models[1:]:
                if model in code_blocks_by_model and code_blocks_by_model[model]:
                    # Find a suitable insertion point (after a paragraph that mentions code or implementation)
                    lines = primary_response.split('\n')
                    insertion_point = 0
                    for i, line in enumerate(lines):
                        if re.search(r'(code|implementation|example|solution)', line, re.IGNORECASE):
                            insertion_point = i + 1
                            break
                    
                    # Insert the first code block from this model
                    code_insertion = f"\n\nHere's an implementation example:\n\n```\n{code_blocks_by_model[model][0]}\n```\n"
                    lines.insert(insertion_point, code_insertion)
                    primary_response = '\n'.join(lines)
                    break  # Only use one alternative model's code
        
        return primary_response

    def blend_explanation_responses(self, responses, ranking_result):
        """
        Specialized blending for explanatory queries requiring comprehensive information.
        
        Args:
            responses: Dictionary of model responses
            ranking_result: Result of ranking the responses
            
        Returns:
            Blended response with comprehensive explanation
        """
        logger.info("Using specialized explanation blending strategy")
        
        # Get top 3 models and their responses
        top_models = [item['model'] for item in ranking_result.get('detailed_rankings', [])[:3]]
        if len(top_models) < 2:
            return responses[top_models[0]] if top_models else "Insufficient responses for explanation blending"
        
        # Use the primary response as the base
        primary_response = responses[top_models[0]]
        
        # Extract unique sections/paragraphs from secondary responses
        all_paragraphs = []
        for model in top_models:
            if model in responses:
                text = responses[model]
                paragraphs = re.split(r'\n\n+', text)  # Split by double newlines
                for para in paragraphs:
                    if len(para.strip()) > 50:  # Only consider substantial paragraphs
                        all_paragraphs.append((model, para))
        
        # Find unique insights in secondary responses not covered in primary
        unique_insights = []
        primary_paragraphs = re.split(r'\n\n+', primary_response)
        
        for model, para in all_paragraphs:
            if model != top_models[0]:  # Skip primary model paragraphs
                # Check if this paragraph contains unique information
                is_unique = True
                for primary_para in primary_paragraphs:
                    similarity = self._calculate_text_similarity(para, primary_para)
                    if similarity > 0.7:  # High similarity threshold
                        is_unique = False
                        break
                if is_unique:
                    unique_insights.append(para)
        
        # Add unique insights to the primary response
        if unique_insights:
            additional_content = "\n\n## Additional Insights\n\n" + "\n\n".join(unique_insights[:2])
            primary_response += additional_content
        
        return primary_response

    def blend_general_responses(self, responses, ranking_result):
        """
        Fallback blending strategy for general queries.
        
        Args:
            responses: Dictionary of model responses
            ranking_result: Result of ranking the responses
            
        Returns:
            Blended response for general queries
        """
        logger.info("Using general blending strategy")
        
        # Get top 2 models and their responses
        top_models = [item['model'] for item in ranking_result.get('detailed_rankings', [])[:2]]
        if not top_models:
            return "No valid responses available"
        
        # If only one model available, return its response
        if len(top_models) == 1:
            return responses[top_models[0]]
        
        # Use the best response as base
        primary_response = responses[top_models[0]]
        secondary_response = responses[top_models[1]]
        
        # Check if secondary response contains unique information
        primary_sentences = set(re.split(r'(?<=[.!?])\s+', primary_response))
        secondary_sentences = set(re.split(r'(?<=[.!?])\s+', secondary_response))
        
        # Find unique sentences in secondary response
        unique_sentences = []
        for sentence in secondary_sentences:
            if len(sentence.split()) > 5:  # Skip very short sentences
                if not any(self._has_similar_statement(sentence, p) for p in primary_sentences):
                    unique_sentences.append(sentence)
        
        # If there are unique insights, append them
        if unique_sentences:
            additional_content = "\n\nAdditional information: " + " ".join(unique_sentences[:3])
            primary_response += additional_content
        
        return primary_response

    def _calculate_text_similarity(self, text1, text2):
        """
        Calculate similarity between two text snippets.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            float: Similarity score from 0.0 to 1.0
        """
        # Tokenize both texts
        tokens1 = set(re.findall(r'\b\w+\b', text1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Calculate Jaccard similarity
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union)
        
    def blend_responses(self, responses: Dict[str, Any], task_info: Any) -> Dict[str, Any]:
        """
        Blend responses from multiple models based on task type and quality.
        Returns a complete response object with model info and blending details.
        
        Args:
            responses: Dictionary mapping model names to their responses
            task_info: Task classification information
            
        Returns:
            Dictionary containing blended response and metadata
        """
        logger.info(f"Blending responses from {len(responses)} models")
        
        # Validate responses dict
        if not responses:
            logger.error("No responses provided for blending")
            return {"content": "Error: No model responses available", "model_info": {}}
        
        if not isinstance(responses, dict):
            logger.error(f"Expected dict for responses, got {type(responses).__name__}")
            try:
                # Try to convert to dict if possible
                responses = dict(responses)
            except:
                logger.error("Could not convert responses to dictionary")
                return {"content": "Error: Invalid response format", "model_info": {}}
        
        # Extract task information
        task_query = ''
        task_type = 'general'
        complexity = 5  # Default moderate complexity
        tags = []  # Default empty tags
        
        # Process task_info based on its type
        try:
            if isinstance(task_info, dict):
                task_query = task_info.get('query', '')
                task_type = task_info.get('task_type', 'general')
                complexity = task_info.get('complexity', 5)
                tags = task_info.get('tags', [])
            elif isinstance(task_info, str):
                task_query = task_info
            else:
                try:
                    task_query = str(task_info)
                except:
                    task_query = ""
        except Exception as e:
            logger.error(f"Error processing task_info: {e}")
        
        # Determine query type from task info or infer it
        query_type = task_type
        if not query_type or query_type == 'general':
            # Infer query type from content
            if task_query:
                if re.search(r'(code|program|function|class|algorithm|implementation)', task_query, re.IGNORECASE):
                    query_type = 'technical'
                elif re.search(r'(compare|versus|vs\.|difference between|similarities|pros and cons)', task_query, re.IGNORECASE):
                    query_type = 'comparison'
                elif re.search(r'(explain|how does|what is|concept|definition|theory)', task_query, re.IGNORECASE):
                    query_type = 'explanation'
        
        # Rank the responses to get quality metrics
        ranking_result = self.rank_responses(responses, task_info, query_type=query_type)
        
        # If we couldn't rank responses, return the first available response
        if not ranking_result or not ranking_result.get('detailed_rankings'):
            logger.warning("Could not rank responses for blending, using first available")
            first_response = list(responses.values())[0] if responses else "No valid responses available"
            return {
                "content": first_response,
                "model_info": {
                    "models_used": list(responses.keys()),
                    "blending_method": "none",
                    "error": "Could not rank responses"
                }
            }
        
        # Select blending strategy based on query type
        blended_content = ""
        blending_method = "general"
        
        try:
            if query_type == 'comparison':
                blended_content = self.blend_comparison_responses(responses, ranking_result)
                blending_method = "comparison"
            elif query_type == 'technical':
                blended_content = self.blend_technical_responses(responses, ranking_result)
                blending_method = "technical"
            elif query_type == 'explanation':
                blended_content = self.blend_explanation_responses(responses, ranking_result)
                blending_method = "explanation"
            else:
                blended_content = self.blend_general_responses(responses, ranking_result)
                blending_method = "general"
        except Exception as e:
            logger.error(f"Error in specialized blending: {e}")
            # Fallback to top response
            top_model = ranking_result['best_model']
            blended_content = responses[top_model] if top_model in responses else "Error in response blending"
            blending_method = "fallback"
        
        # Create detailed model info for response
        models_used = list(responses.keys())
        top_models = [item['model'] for item in ranking_result.get('detailed_rankings', [])[:3]]
        
        # Create sections information for transparency
        sections_info = []
        if blending_method != "fallback":
            primary_model = top_models[0] if top_models else None
            sections_info = [
                {"section": "primary_content", "model": primary_model, "contribution": "main_structure"},
            ]
            
            # Add secondary contributions based on blending method
            if blending_method == "comparison":
                for i, model in enumerate(top_models[1:3], 1):
                    sections_info.append({
                        "section": f"comparison_points_{i}", 
                        "model": model, 
                        "contribution": "alternative_perspective"
                    })
            elif blending_method == "technical" and len(top_models) > 1:
                sections_info.append({
                    "section": "code_examples", 
                    "model": top_models[1], 
                    "contribution": "implementation_examples"
                })
            elif blending_method == "explanation" and len(top_models) > 1:
                sections_info.append({
                    "section": "additional_insights", 
                    "model": top_models[1], 
                    "contribution": "supplementary_information"
                })
        
        # Create comprehensive model info structure
        model_info = {
            "models_used": models_used,
            "top_models": top_models,
            "rankings": ranking_result.get('detailed_rankings', []),
            "blending_method": blending_method,
            "query_type": query_type,
            "sections": sections_info
        }
        
        # Create the complete response structure
        response = {
            "content": blended_content,
            "model_info": model_info
        }
        
        return response


# Create a singleton instance for easy importing
ensemble_validator = EnsembleValidator()


def test_ensemble_validator():
    """
    Test the ensemble validator with sample responses.
    """
    # Sample responses from different models
    responses = {
        "gpt4": "The capital of France is Paris. It is known for the Eiffel Tower and the Louvre museum.",
        "claude3": "Paris is the capital city of France. Famous landmarks include the Eiffel Tower, Notre Dame, and the Louvre.",
        "mistral7b": "The capital of France is Paris. It's a major European city and a global center for art, fashion, and culture.",
        "gpt4all": "Paris is France's capital. It has many monuments like the Eiffel Tower."
    }
    
    # Sample quality scores (would normally come from evaluate_response_quality)
    quality_scores = {
        "gpt4": 0.9,
        "claude3": 0.85,
        "mistral7b": 0.75,
        "gpt4all": 0.65
    }
    
    # Create validator
    validator = EnsembleValidator()
    
    # Test ranking
    rankings = validator.rank_responses(responses, "What is the capital of France?", quality_scores, "factual")
    print("Rankings:", rankings)
    
    # Test best response selection
    best_model, result = validator.select_best_response(
        responses, "What is the capital of France?", quality_scores, "factual"
    )
    print(f"Best model: {best_model}")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test consensus analysis
    consensus_scores = validator.probabilistic_consensus(responses, quality_scores, "factual")
    print("Consensus scores:", consensus_scores)


if __name__ == "__main__":
    test_ensemble_validator()
