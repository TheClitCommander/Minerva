#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Evaluation Manager for Minerva's Think Tank Mode

This module provides an interface between OpenAI Evals and Minerva's Think Tank mode,
allowing for standardized evaluation of model responses and performance tracking.
"""

import os
import sys
import logging
import json
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import OpenAI Evals integration
try:
    from web.evals_integration import run_comprehensive_evaluation, evaluate_model_response
    EVALS_AVAILABLE = True
    logger.info("Successfully imported OpenAI Evals integration")
except ImportError as e:
    logger.warning(f"OpenAI Evals integration import failed: {e}")
    EVALS_AVAILABLE = False

# Import model registry
try:
    from web.model_registry import update_model_performance, get_registry
    MODEL_REGISTRY_AVAILABLE = True
    logger.info("Successfully imported model registry")
except ImportError as e:
    logger.warning(f"Model registry import failed: {e}")
    MODEL_REGISTRY_AVAILABLE = False

# Define storage for evaluation results
EVALUATION_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "data", "evaluation_results.json")
os.makedirs(os.path.dirname(EVALUATION_RESULTS_PATH), exist_ok=True)


class ModelEvaluationManager:
    """
    Manager for evaluating and tracking model performance using OpenAI Evals.
    This class provides a centralized interface for evaluating model responses,
    tracking performance over time, and updating the model registry.
    """
    
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of ModelEvaluationManager exists."""
        if cls._instance is None:
            cls._instance = super(ModelEvaluationManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        """Initialize the evaluation manager."""
        self.evaluation_results = self._load_results()
        logger.info("Model Evaluation Manager initialized")
        
    def _load_results(self) -> Dict[str, Any]:
        """Load evaluation results from disk."""
        if os.path.exists(EVALUATION_RESULTS_PATH):
            try:
                with open(EVALUATION_RESULTS_PATH, 'r') as f:
                    results = json.load(f)
                logger.info(f"Loaded {len(results)} evaluation results")
                return results
            except Exception as e:
                logger.error(f"Error loading evaluation results: {e}")
        return {}
        
    def _save_results(self) -> bool:
        """Save evaluation results to disk."""
        try:
            with open(EVALUATION_RESULTS_PATH, 'w') as f:
                json.dump(self.evaluation_results, f, indent=2)
            logger.info(f"Saved evaluation results")
            return True
        except Exception as e:
            logger.error(f"Error saving evaluation results: {e}")
            return False
    
    def evaluate_response(self, model_name: str, prompt: str, response: str) -> Dict[str, Any]:
        """
        Evaluate a model's response using OpenAI Evals or fallback methods.
        
        Args:
            model_name: The name of the model that generated the response
            prompt: The original user prompt/query
            response: The model's response
            
        Returns:
            Dictionary containing evaluation results
        """
        # Create a unique identifier for this evaluation
        eval_id = f"{model_name}_{hash(prompt)}_{hash(response)}_{datetime.now().isoformat()}"
        
        # Check if OpenAI Evals is available
        if not EVALS_AVAILABLE:
            logger.warning("Using fallback evaluation since OpenAI Evals is not available")
            # Use basic heuristics for evaluation
            prompt_words = set(prompt.lower().split())
            response_words = set(response.lower().split())
            overlap = len(prompt_words.intersection(response_words))
            overlap_ratio = overlap / max(1, len(prompt_words))
            
            result = {
                "overall_score": min(0.8, overlap_ratio * 1.2),  # Simple relevance heuristic, capped at 0.8
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "relevance": {"score": min(1.0, overlap_ratio * 1.2)},
                    "accuracy": {"score": 0.7},  # Default moderate score since we can't verify accuracy
                    "coherence": {"score": 0.75},  # Default moderate score
                    "is_fallback": True
                }
            }
        else:
            # Use OpenAI Evals for comprehensive evaluation
            logger.info(f"Evaluating response from {model_name} using OpenAI Evals")
            result = run_comprehensive_evaluation(prompt, response)
            result["model"] = model_name
        
        # Store the evaluation result
        self.evaluation_results[eval_id] = result
        self._save_results()
        
        # Update model registry if available
        if MODEL_REGISTRY_AVAILABLE:
            metrics = {
                "last_eval_score": result.get("overall_score", 0.5),
                "last_eval_timestamp": datetime.now().isoformat()
            }
            
            # Add individual metric scores if available
            if "metrics" in result:
                for metric_name, metric_data in result["metrics"].items():
                    if isinstance(metric_data, dict) and "score" in metric_data:
                        metrics[f"eval_{metric_name}"] = metric_data["score"]
            
            # Update the model registry
            update_model_performance(model_name, metrics)
            logger.info(f"Updated model registry with evaluation results for {model_name}")
        
        return result
    
    def get_model_evaluation_history(self, model_name: str = None, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get evaluation history for one or all models.
        
        Args:
            model_name: Optional model name to filter results
            limit: Maximum number of results per model
            
        Returns:
            Dictionary mapping model names to their evaluation histories
        """
        history = {}
        
        for eval_id, result in self.evaluation_results.items():
            result_model = result.get("model")
            
            if model_name and result_model != model_name:
                continue
                
            if result_model not in history:
                history[result_model] = []
                
            if len(history[result_model]) < limit:
                history[result_model].append(result)
        
        return history
    
    def get_model_performance_over_time(self, model_name: str, metric: str = "overall_score") -> List[Dict[str, Any]]:
        """
        Get performance trend for a specific model and metric.
        
        Args:
            model_name: The model name to get performance for
            metric: The metric to track (overall_score, accuracy, etc.)
            
        Returns:
            List of timestamp and score pairs, sorted by timestamp
        """
        performance = []
        
        for eval_id, result in self.evaluation_results.items():
            if result.get("model") != model_name:
                continue
                
            timestamp = result.get("timestamp")
            
            if metric == "overall_score":
                score = result.get("overall_score", 0)
            elif "metrics" in result and metric in result["metrics"]:
                score = result["metrics"][metric].get("score", 0)
            else:
                continue
                
            performance.append({
                "timestamp": timestamp,
                "score": score
            })
        
        # Sort by timestamp
        performance.sort(key=lambda x: x["timestamp"])
        
        return performance
    
    def compare_models(self, model_names: List[str], metric: str = "overall_score") -> Dict[str, float]:
        """
        Compare multiple models based on a specific metric.
        
        Args:
            model_names: List of model names to compare
            metric: The metric to compare on
            
        Returns:
            Dictionary mapping model names to their average score on the metric
        """
        comparison = {}
        
        for model_name in model_names:
            scores = []
            
            for eval_id, result in self.evaluation_results.items():
                if result.get("model") != model_name:
                    continue
                    
                if metric == "overall_score":
                    score = result.get("overall_score", 0)
                elif "metrics" in result and metric in result["metrics"]:
                    score = result["metrics"][metric].get("score", 0)
                else:
                    continue
                    
                scores.append(score)
            
            if scores:
                comparison[model_name] = sum(scores) / len(scores)
            else:
                comparison[model_name] = 0
        
        return comparison
    
    def rank_models(self, model_names: List[str] = None, metric: str = "overall_score") -> List[Dict[str, Any]]:
        """
        Rank models based on their performance on a specific metric.
        
        Args:
            model_names: Optional list of model names to rank, or None for all models
            metric: The metric to rank on
            
        Returns:
            List of model rankings with names and scores, sorted by score (descending)
        """
        if model_names is None:
            # Get all unique model names from evaluation results
            model_names = set()
            for result in self.evaluation_results.values():
                model = result.get("model")
                if model:
                    model_names.add(model)
            model_names = list(model_names)
        
        comparison = self.compare_models(model_names, metric)
        
        # Convert to list and sort by score (descending)
        rankings = [{"model": name, "score": score} for name, score in comparison.items()]
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        return rankings
    
    def clear_evaluation_history(self, model_name: str = None) -> int:
        """
        Clear evaluation history for a specific model or all models.
        
        Args:
            model_name: Optional model name to clear results for
            
        Returns:
            Number of evaluation results cleared
        """
        if model_name is None:
            # Clear all results
            count = len(self.evaluation_results)
            self.evaluation_results = {}
        else:
            # Clear results for specific model
            count = 0
            new_results = {}
            
            for eval_id, result in self.evaluation_results.items():
                if result.get("model") != model_name:
                    new_results[eval_id] = result
                else:
                    count += 1
            
            self.evaluation_results = new_results
        
        self._save_results()
        logger.info(f"Cleared {count} evaluation results")
        
        return count


# Singleton instance for easy access
_evaluation_manager_instance = None

def get_evaluation_manager() -> ModelEvaluationManager:
    """Get the singleton instance of the evaluation manager."""
    global _evaluation_manager_instance
    if _evaluation_manager_instance is None:
        _evaluation_manager_instance = ModelEvaluationManager()
    return _evaluation_manager_instance

# Convenience functions
def evaluate_model_response(model_name: str, prompt: str, response: str) -> Dict[str, Any]:
    """Evaluate a model response using the singleton evaluation manager."""
    manager = get_evaluation_manager()
    return manager.evaluate_response(model_name, prompt, response)

def get_model_rankings(model_names: List[str] = None, metric: str = "overall_score") -> List[Dict[str, Any]]:
    """Get model rankings using the singleton evaluation manager."""
    manager = get_evaluation_manager()
    return manager.rank_models(model_names, metric)

def get_model_performance_history(model_name: str) -> List[Dict[str, Any]]:
    """Get a model's performance history using the singleton evaluation manager."""
    manager = get_evaluation_manager()
    return manager.get_model_performance_over_time(model_name)

# For testing
if __name__ == "__main__":
    # Sample test
    test_prompt = "What is the capital of France?"
    test_responses = {
        "gpt4": "The capital of France is Paris, which is located in the north-central part of the country.",
        "claude": "Paris is the capital city of France. It's located in north-central France along the Seine River.",
        "mistral": "Paris is the capital of France."
    }
    
    manager = get_evaluation_manager()
    
    print("Testing model evaluation:")
    for model, response in test_responses.items():
        result = manager.evaluate_response(model, test_prompt, response)
        print(f"\n{model} evaluation result:")
        print(f"  Overall score: {result.get('overall_score', 0):.2f}")
        for metric_name, metric_data in result.get("metrics", {}).items():
            if isinstance(metric_data, dict) and "score" in metric_data:
                print(f"  {metric_name}: {metric_data['score']:.2f}")
    
    print("\nModel rankings:")
    rankings = manager.rank_models(list(test_responses.keys()))
    for rank, model_data in enumerate(rankings, 1):
        print(f"  {rank}. {model_data['model']}: {model_data['score']:.2f}")
