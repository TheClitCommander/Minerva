#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OpenAI Evals Integration for Minerva's Think Tank Mode

This module provides integration between OpenAI Evals and Minerva's Think Tank mode,
allowing for standardized evaluation of model responses using OpenAI's evaluation framework.
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI Evals
try:
    import evals
    from evals.api import CompletionFn, CompletionResult
    EVALS_AVAILABLE = True
    logger.info("Successfully imported OpenAI Evals")
except ImportError as e:
    logger.warning(f"OpenAI Evals import failed: {e}")
    EVALS_AVAILABLE = False
    # Define fallback types when evals is not available
    from typing import Callable, TypeVar, Dict
    T = TypeVar('T')
    CompletionFn = Callable[[str], Dict[str, str]]
    CompletionResult = Dict[str, Any]

# Define evaluation metrics and registry
DEFAULT_EVAL_METRICS = {
    "accuracy": {
        "weight": 1.0,
        "description": "Factual correctness of the response"
    },
    "relevance": {
        "weight": 0.8,
        "description": "How relevant the response is to the query"
    },
    "completeness": {
        "weight": 0.7, 
        "description": "How completely the response addresses all aspects of the query"
    },
    "coherence": {
        "weight": 0.6,
        "description": "Logical flow and structure of the response"
    },
    "harmlessness": {
        "weight": 1.0,
        "description": "Absence of harmful, biased, or inappropriate content"
    }
}

# Store evaluation results
EVAL_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "data", "evals_results.json")
os.makedirs(os.path.dirname(EVAL_RESULTS_PATH), exist_ok=True)

class ModelEvaluator:
    """Class to evaluate AI model outputs using OpenAI Evals."""
    
    def __init__(self):
        """Initialize the model evaluator."""
        self.results_cache = {}
        self._load_cached_results()
    
    def _load_cached_results(self):
        """Load cached evaluation results from disk."""
        if os.path.exists(EVAL_RESULTS_PATH):
            try:
                with open(EVAL_RESULTS_PATH, 'r') as f:
                    self.results_cache = json.load(f)
                logger.info(f"Loaded {len(self.results_cache)} cached evaluation results")
            except Exception as e:
                logger.error(f"Error loading cached evaluation results: {e}")
                self.results_cache = {}
    
    def _save_cached_results(self):
        """Save evaluation results to disk."""
        try:
            with open(EVAL_RESULTS_PATH, 'w') as f:
                json.dump(self.results_cache, f, indent=2)
            logger.info(f"Saved {len(self.results_cache)} evaluation results to cache")
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")
    
    def make_completion_fn(self, response: str) -> CompletionFn:
        """Create a CompletionFn wrapper for a static response.
        
        Args:
            response: The model response string
            
        Returns:
            A CompletionFn object that returns the static response
        """
        if not EVALS_AVAILABLE:
            logger.warning("OpenAI Evals not available, using mock implementation")
            # Return a mock function since evals isn't available
            mock_fn = lambda prompt: {"response": response}
            return mock_fn
        
        class StaticCompletionFn(CompletionFn):
            def __init__(self, static_response):
                self.static_response = static_response
                
            def __call__(self, prompt: str, **kwargs):
                return CompletionResult(response=self.static_response)
        
        return StaticCompletionFn(response)
    
    def evaluate_response(self, prompt: str, response: str, eval_name: str = "accuracy") -> Dict[str, Any]:
        """Evaluate a model response using OpenAI Evals.
        
        Args:
            prompt: The user prompt/query
            response: The model's response
            eval_name: Name of the evaluation to run
            
        Returns:
            Dictionary containing evaluation results
        """
        # Create a unique identifier for this evaluation
        eval_id = f"{hash(prompt)}_{hash(response)}_{eval_name}"
        
        # Check if we've already evaluated this exact prompt-response pair
        if eval_id in self.results_cache:
            logger.info(f"Using cached evaluation result for {eval_id}")
            return self.results_cache[eval_id]
        
        # If OpenAI Evals is not available, use our fallback evaluation
        if not EVALS_AVAILABLE:
            logger.warning("Using fallback evaluation since OpenAI Evals is not available")
            result = self._fallback_evaluate(prompt, response, eval_name)
            self.results_cache[eval_id] = result
            self._save_cached_results()
            return result
        
        try:
            # Create a completion function that returns our static response
            completion_fn = self.make_completion_fn(response)
            
            # Run the evaluation
            logger.info(f"Running OpenAI Eval '{eval_name}' on response")
            eval_result = evals.run(eval_name, completion_fn)
            
            # Format the result
            result = {
                "score": eval_result.get("accuracy", 0.0),
                "timestamp": datetime.datetime.now().isoformat(),
                "eval_name": eval_name,
                "details": eval_result,
            }
            
            # Cache the result
            self.results_cache[eval_id] = result
            self._save_cached_results()
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating response with OpenAI Evals: {e}")
            # Fall back to our own evaluation
            result = self._fallback_evaluate(prompt, response, eval_name)
            self.results_cache[eval_id] = result
            self._save_cached_results()
            return result
    
    def _fallback_evaluate(self, prompt: str, response: str, eval_name: str) -> Dict[str, Any]:
        """Fallback evaluation when OpenAI Evals is not available.
        
        Args:
            prompt: The user prompt/query
            response: The model's response
            eval_name: Name of the evaluation to run
            
        Returns:
            Dictionary containing evaluation results
        """
        # Basic length-based and keyword-based heuristics
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())
        
        # Calculate word overlap as a basic relevance metric
        overlap = len(prompt_words.intersection(response_words))
        overlap_ratio = overlap / max(1, len(prompt_words))
        
        # Completeness heuristic based on response length relative to prompt
        completeness = min(1.0, len(response) / (len(prompt) * 3))
        
        # Response structure heuristics (paragraphs, sentences)
        paragraphs = response.count('\n\n') + 1
        sentences = response.count('.') + response.count('!') + response.count('?')
        structure_score = min(1.0, (paragraphs / 3) * 0.5 + (sentences / 5) * 0.5)
        
        # Combine metrics based on evaluation type
        if eval_name == "accuracy":
            # Without ground truth, accuracy is hard to estimate - use a moderate default
            score = 0.7
        elif eval_name == "relevance":
            score = overlap_ratio * 0.9  # Scale to 0.9 max (perfect relevance is unlikely)
        elif eval_name == "completeness":
            score = completeness
        elif eval_name == "coherence":
            score = structure_score
        else:
            # Default moderate score for unknown eval types
            score = 0.7
        
        return {
            "score": score,
            "timestamp": datetime.datetime.now().isoformat(),
            "eval_name": eval_name,
            "details": {
                "word_overlap": overlap,
                "overlap_ratio": overlap_ratio,
                "completeness": completeness,
                "structure_score": structure_score,
                "is_fallback": True
            }
        }
    
    def run_comprehensive_evaluation(self, prompt: str, response: str) -> Dict[str, Any]:
        """Run a comprehensive evaluation using multiple metrics.
        
        Args:
            prompt: The user prompt/query
            response: The model's response
            
        Returns:
            Dictionary containing comprehensive evaluation results
        """
        results = {}
        total_score = 0.0
        total_weight = 0.0
        
        # Run each evaluation metric
        for metric, config in DEFAULT_EVAL_METRICS.items():
            weight = config["weight"]
            result = self.evaluate_response(prompt, response, metric)
            score = result.get("score", 0.0)
            
            results[metric] = {
                "score": score,
                "weight": weight,
                "description": config["description"],
                "details": result.get("details", {})
            }
            
            total_score += score * weight
            total_weight += weight
        
        # Calculate weighted average
        weighted_average = total_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "overall_score": weighted_average,
            "timestamp": datetime.datetime.now().isoformat(),
            "metrics": results
        }

# Singleton instance for easy access
evaluator = ModelEvaluator()

def evaluate_model_response(prompt: str, response: str, eval_name: str = "accuracy") -> Dict[str, Any]:
    """Convenience function to evaluate a model response using the singleton evaluator.
    
    Args:
        prompt: The user prompt/query
        response: The model's response
        eval_name: Name of the evaluation to run
        
    Returns:
        Dictionary containing evaluation results
    """
    return evaluator.evaluate_response(prompt, response, eval_name)

def run_comprehensive_evaluation(prompt: str, response: str) -> Dict[str, Any]:
    """Convenience function to run a comprehensive evaluation using the singleton evaluator.
    
    Args:
        prompt: The user prompt/query
        response: The model's response
        
    Returns:
        Dictionary containing comprehensive evaluation results
    """
    return evaluator.run_comprehensive_evaluation(prompt, response)


# Test the evaluator functionality
if __name__ == "__main__":
    test_prompt = "What is the capital of France?"
    test_response = "The capital of France is Paris."
    
    print("Testing basic evaluation:")
    result = evaluate_model_response(test_prompt, test_response)
    print(json.dumps(result, indent=2))
    
    print("\nTesting comprehensive evaluation:")
    comp_result = run_comprehensive_evaluation(test_prompt, test_response)
    print(json.dumps(comp_result, indent=2))
