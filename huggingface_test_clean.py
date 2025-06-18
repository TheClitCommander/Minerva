#!/usr/bin/env python3
"""
Isolated test script for Minerva's enhanced Hugging Face processing.

This script allows testing the Hugging Face processing functions in isolation
without requiring the full Flask application context or dependencies.
"""

import os
import sys
import json
import time
import logging
import re
from typing import Dict, List, Any, Tuple, Optional

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

    def __str__(self):
        return self.name

    def to(self, device):
        self.device = device
        logger.info(f"Mock model moved to {device}")
        return self

    def generate(self, **kwargs):
        max_new_tokens = kwargs.get('max_new_tokens', 50)
        temperature = kwargs.get('temperature', 0.7)
        response_length = int(max_new_tokens * (0.5 + temperature / 2))
        return [list(range(response_length))]  # Simulated response tokens


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


def run_mock_test():
    test_message = "Explain quantum computing in simple terms."
    logger.info(f"Testing message: {test_message}")
    model = MockModel()
    tokenizer = MockTokenizer()
    tokenizer.set_query(test_message)
    tokenized_input = tokenizer(test_message)
    response_tokens = model.generate(max_new_tokens=100)
    generated_response = tokenizer.decode(response_tokens)
    logger.info(f"Generated Response: {generated_response}")
    valid, validation_details = mock_validate_response(generated_response, test_message)
    logger.info(f"Validation Result: {valid}, Details: {validation_details}")
    quality_scores = mock_evaluate_response_quality(generated_response)
    logger.info(f"Quality Scores: {quality_scores}")


if __name__ == "__main__":
    run_mock_test()
