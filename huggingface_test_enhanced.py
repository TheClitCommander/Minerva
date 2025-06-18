#!/usr/bin/env python3
"""
Enhanced isolated test script for Minerva's Hugging Face processing.

This script tests the complete functionality of Minerva's Hugging Face processing,
including dynamic parameter optimization, response validation, and fallback handling.
"""

import os
import sys
import json
import time
import logging
import re
from typing import Dict, List, Any, Tuple, Optional
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("minerva.test")

# Mock Tokenizer and Model for testing without loading actual Hugging Face models
class MockTokenizer:
    def __init__(self, name="gpt2"):
        self.name = name
        self.stored_query = ""
        self.topic = "general topics"
        logger.info(f"Initialized mock tokenizer for {name}")
        
    def __call__(self, text, return_tensors=None):
        tokens = len(text.split())  # Simple approximation
        return MockTokenizerOutput(tokens)
    
    def decode(self, token_ids, skip_special_tokens=True):
        if isinstance(token_ids, list) and len(token_ids) > 0:
            return f"User: {self.stored_query}\n\nAssistant: Here is a response to your query about {self.topic}."
        return "Empty response due to no tokens"
    
    def set_query(self, query):
        self.stored_query = query
        words = query.split()
        self.topic = " ".join(words[:3]) if len(words) > 3 else query


class MockTokenizerOutput:
    def __init__(self, token_count):
        self.input_ids = MockTensor([1, token_count])

    def to(self, device):
        return self


class MockTensor:
    def __init__(self, shape):
        self.shape = shape


class MockModel:
    def __init__(self, name="gpt2"):
        self.name = name
        self.device = "cpu"
        logger.info(f"Initialized mock model for {name}")
        # Error simulation
        self.simulate_error = False
        self.error_type = None

    def __str__(self):
        return self.name

    def to(self, device):
        self.device = device
        logger.info(f"Mock model moved to {device}")
        return self

    def generate(self, **kwargs):
        # Check if we should simulate an error
        if self.simulate_error:
            if self.error_type == "timeout":
                raise TimeoutError("Simulated timeout error")
            elif self.error_type == "resource":
                raise RuntimeError("Simulated resource error")
            elif self.error_type == "token_limit":
                raise ValueError("Simulated token limit exceeded")
            
        max_new_tokens = kwargs.get('max_new_tokens', 50)
        temperature = kwargs.get('temperature', 0.7)
        do_sample = kwargs.get('do_sample', True)
        
        # Simulate different response qualities based on params
        response_length = int(max_new_tokens * (0.5 + temperature / 2))
        if do_sample and temperature > 0.9:
            # Simulate more random responses at high temperatures
            response_length = random.randint(10, response_length)
        
        return [list(range(response_length))]  # Simulated response tokens

    def set_error_simulation(self, error_type=None):
        if error_type:
            self.simulate_error = True
            self.error_type = error_type
        else:
            self.simulate_error = False
            self.error_type = None


# Mock Utility Functions
def mock_get_query_tags(message: str) -> List[str]:
    tags = []
    if re.search(r'\b(hi|hey|hello|greetings)\b', message.lower()):
        tags.append("greeting")
    if re.search(r'\b(what|where|when|who|which|how many|why)\b.*\?', message.lower()):
        tags.append("factual")
    if re.search(r'\b(analyze|compare|contrast|explain|discuss|evaluate|synthesize)\b', message.lower()):
        tags.append("complex_reasoning")
    if re.search(r'\b(code|function|program|algorithm|python|javascript|java|c\+\+)\b', message.lower()):
        tags.append("coding")
    if not tags:
        tags.append("general")
    return tags


def mock_route_request(message: str) -> Dict[str, Any]:
    tags = mock_get_query_tags(message)
    complexity_factors = {
        "greeting": 0.1, "factual": 0.4, "general": 0.5, "coding": 0.7, "complex_reasoning": 0.8
    }
    complexity = max(0.3, max(complexity_factors.get(tag, 0.3) for tag in tags))
    words = len(message.split())
    if words > 30:
        complexity = min(1.0, complexity + 0.2)
    elif words > 15:
        complexity = min(1.0, complexity + 0.1)
    elif words < 5:
        complexity = max(0.1, complexity - 0.2)
    models = ["gpt2"]
    if complexity > 0.5:
        models.append("gpt2-medium")
    return {"query_tags": tags, "complexity": complexity, "models": models}


def mock_validate_response(response: str, message: str) -> Tuple[bool, Dict[str, Any]]:
    validation_results = {"quality_score": 0.0, "checks": [], "primary_reason": None}
    if not response or len(response.strip()) < 5:
        validation_results["primary_reason"] = "empty"
        return False, validation_results
    if len(response.strip()) < 20:
        validation_results["primary_reason"] = "too_short"
        return False, validation_results
    if re.search(r'(I am an AI|As an AI|I\'m an AI|As an artificial intelligence)', response, re.IGNORECASE):
        validation_results["primary_reason"] = "self_reference"
        return False, validation_results
    sentences = re.split(r'[.!?]\s+', response)
    seen_sentences = []
    repetition_count = sum(1 for s in sentences if s.strip() in seen_sentences)
    if repetition_count > 1:
        validation_results["primary_reason"] = "repetitive"
        return False, validation_results
    validation_results["quality_score"] = 0.7
    return True, validation_results


def mock_evaluate_response_quality(response: str) -> Dict[str, float]:
    metrics = {"relevance_score": 0.8, "coherence_score": 0.8, "length_score": 0.7}
    words = len(response.split())
    if words < 10:
        metrics["length_score"] = 0.3
    elif words < 20:
        metrics["length_score"] = 0.5
    elif words > 100:
        metrics["length_score"] = 0.9
    sentences = re.split(r'[.!?]\s+', response)
    if len(sentences) < 2:
        metrics["coherence_score"] = 0.6
    metrics["overall_score"] = (
        metrics["relevance_score"] * 0.4 + metrics["coherence_score"] * 0.4 + metrics["length_score"] * 0.2
    )
    return metrics


def optimize_generation_parameters(query: str, query_complexity: float = 0.5, query_tags: List[str] = None) -> Dict[str, Any]:
    """
    Optimize Hugging Face generation parameters based on query characteristics.
    
    Args:
        query: The user query
        query_complexity: Complexity score from 0.0 to 1.0
        query_tags: List of tags for the query
        
    Returns:
        Dict of optimized parameters
    """
    if query_tags is None:
        query_tags = []
    
    # Default parameters
    params = {
        "max_new_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.1,
        "do_sample": True
    }
    
    # Adjust based on complexity
    if query_complexity > 0.7:  # High complexity
        params["max_new_tokens"] = 512
        params["temperature"] = 0.8
        params["top_p"] = 0.92
        params["repetition_penalty"] = 1.2
    elif query_complexity < 0.3:  # Low complexity
        params["max_new_tokens"] = 128
        params["temperature"] = 0.6
        params["top_p"] = 0.85
        params["repetition_penalty"] = 1.05
    
    # Tag-specific adjustments
    if "greeting" in query_tags:
        params["max_new_tokens"] = 64
        params["temperature"] = 0.5
    
    if "coding" in query_tags:
        params["repetition_penalty"] = 1.3
        params["temperature"] = 0.3
    
    if "factual" in query_tags:
        params["temperature"] = 0.4
        params["repetition_penalty"] = 1.15
    
    # Log the parameters for debugging
    logger.info(f"Optimized parameters for query: {query[:30]}...")
    logger.info(f"Query complexity: {query_complexity}, Tags: {query_tags}")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    
    return params


def generate_fallback_response(query: str, validation_result: Dict[str, Any] = None, error_type: str = None) -> str:
    """
    Generate a fallback response when the primary response fails validation or generation.
    
    Args:
        query: The original user query
        validation_result: Result from validation if available
        error_type: Type of error that occurred, if any
        
    Returns:
        A fallback response string
    """
    # Default fallback message
    fallback_response = "I apologize, but I'm having trouble generating a good response to your query."
    
    if validation_result and "primary_reason" in validation_result:
        reason = validation_result["primary_reason"]
        
        if reason == "empty":
            fallback_response = "I apologize, but I couldn't generate a response to your query. Could you please rephrase your question?"
        elif reason == "too_short":
            fallback_response = "I need to provide more details on this topic. Let me elaborate further to properly address your query."
        elif reason == "self_reference":
            fallback_response = "To answer your question directly: " + query.strip()
        elif reason == "repetitive":
            fallback_response = "Let me provide a clearer and more concise answer to your question without repetition."
        elif reason == "irrelevant":
            fallback_response = "I'd like to address your question more directly. Could you please rephrase your query or provide additional context?"
        elif reason == "inappropriate":
            fallback_response = "I'm unable to provide a response to this query as it appears to request information that may not be appropriate or helpful."
    elif error_type:
        if error_type == "timeout":
            fallback_response = "I apologize for the delay. Your query is complex and requires more processing time than is currently available."
        elif error_type == "resource":
            fallback_response = "I'm currently experiencing high demand and limited resources. Please try again in a moment with a simpler query."
        elif error_type == "token_limit":
            fallback_response = "Your query would result in a response that exceeds my current capacity. Could you break it down into smaller parts?"
    
    # Log the fallback generation
    logger.info(f"Generated fallback response for query: {query[:30]}...")
    if validation_result:
        logger.info(f"Validation failure: {validation_result.get('primary_reason', 'unknown')}")
    if error_type:
        logger.info(f"Error type: {error_type}")
    
    return fallback_response


def process_huggingface_only_test(message: str) -> str:
    """
    Test implementation of the process_huggingface_only function.
    
    Args:
        message: The user message to process
        
    Returns:
        Generated response
    """
    logger.info(f"Processing message: {message}")
    
    # 1. Analyze query and optimize parameters
    route_info = mock_route_request(message)
    query_complexity = route_info.get("complexity", 0.5)
    query_tags = route_info.get("query_tags", ["general"])
    
    # 2. Optimize generation parameters
    params = optimize_generation_parameters(message, query_complexity, query_tags)
    
    # 3. Initialize tokenizer and model
    model = MockModel()
    tokenizer = MockTokenizer()
    tokenizer.set_query(message)
    
    # 4. Generate response
    try:
        # Randomly simulate errors in 20% of cases to test error handling
        if random.random() < 0.2:
            error_types = ["timeout", "resource", "token_limit"]
            model.set_error_simulation(random.choice(error_types))
        
        response_tokens = model.generate(**params)
        generated_response = tokenizer.decode(response_tokens)
        
        # 5. Validate response
        is_valid, validation_results = mock_validate_response(generated_response, message)
        
        if not is_valid:
            # 6. Generate fallback if validation fails
            logger.info(f"Response validation failed: {validation_results.get('primary_reason', 'unknown')}")
            return generate_fallback_response(message, validation_result=validation_results)
        
        # 7. Evaluate quality
        quality_metrics = mock_evaluate_response_quality(generated_response)
        logger.info(f"Response quality: {quality_metrics['overall_score']:.2f}")
        
        return generated_response
    
    except Exception as e:
        # Handle errors in generation
        error_type = "unknown"
        if isinstance(e, TimeoutError):
            error_type = "timeout"
        elif "resource" in str(e).lower():
            error_type = "resource"
        elif "token" in str(e).lower():
            error_type = "token_limit"
        
        logger.error(f"Error during generation: {str(e)}")
        return generate_fallback_response(message, error_type=error_type)


def run_comprehensive_test():
    """Run a comprehensive test suite for Hugging Face processing."""
    # Test cases covering different scenarios
    test_cases = [
        {"name": "Simple greeting", "query": "Hello, how are you?"},
        {"name": "Factual query", "query": "What is the capital of France?"},
        {"name": "Complex reasoning", "query": "Analyze the impact of climate change on global economics."},
        {"name": "Coding query", "query": "How to implement a quicksort algorithm in Python?"},
        {"name": "Long multi-part query", "query": "Explain quantum computing principles and then compare quantum computers with classical computers in terms of computational capabilities."}
    ]
    
    print("\n=== COMPREHENSIVE HUGGING FACE PROCESSING TEST ===\n")
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i+1}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print("-" * 50)
        
        # Process the query and get response
        response = process_huggingface_only_test(test_case["query"])
        
        print(f"Response: {response}")
        print("-" * 50)
    
    print("\nCompleted all test cases.")


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    run_comprehensive_test()
