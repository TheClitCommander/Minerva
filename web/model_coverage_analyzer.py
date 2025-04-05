"""
Model Coverage Analyzer for Minerva's Think Tank mode

This module provides tools to ensure comprehensive model coverage and intelligent 
model selection in Think Tank mode, ensuring all AI models are utilized effectively.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ModelCoverageAnalyzer:
    """
    Analyzes and optimizes model coverage to ensure Think Tank mode uses a diverse
    set of high-quality models for the best possible response comparison.
    """
    
    # Model quality tiers for proper selection
    HIGH_QUALITY_MODELS = ['gpt4', 'claude3', 'palm2', 'gemini']
    MID_QUALITY_MODELS = ['mistral7b', 'autogpt', 'huggingface', 'llama2']
    BASIC_MODELS = ['gpt4all', 'distilgpt2', 'gpt3', 'simple_fallback']
    
    @staticmethod
    def analyze_and_enhance_model_coverage(
        models_to_use: List[str], 
        available_models: List[str],
        requested_models: Optional[List[str]] = None
    ) -> List[str]:
        """
        Analyzes model coverage and enhances model selection to ensure optimal
        diversity and quality for Think Tank response comparison.
        
        Args:
            models_to_use: Current list of models selected for use
            available_models: All available model processors
            requested_models: Specifically requested models to prioritize
            
        Returns:
            Enhanced list of models to ensure good coverage
        """
        logger.info(f"[THINK TANK] Model coverage analysis - Available: {available_models}")
        logger.info(f"[THINK TANK] Model coverage analysis - Current: {models_to_use}")
        
        # Count how many from each tier we have
        high_count = sum(1 for m in models_to_use if m in ModelCoverageAnalyzer.HIGH_QUALITY_MODELS)
        mid_count = sum(1 for m in models_to_use if m in ModelCoverageAnalyzer.MID_QUALITY_MODELS)
        basic_count = sum(1 for m in models_to_use if m in ModelCoverageAnalyzer.BASIC_MODELS)
        
        # Minimum requirements for a good mix
        need_more_high = high_count < 1 and any(m in available_models for m in ModelCoverageAnalyzer.HIGH_QUALITY_MODELS)
        need_more_mid = mid_count < 1 and any(m in available_models for m in ModelCoverageAnalyzer.MID_QUALITY_MODELS)
        need_diversity = len(models_to_use) < 2
        
        logger.info(f"[THINK TANK] Model counts - High: {high_count}, Mid: {mid_count}, Basic: {basic_count}")
        logger.info(f"[THINK TANK] Need more high-quality models: {need_more_high}")
        logger.info(f"[THINK TANK] Need more mid-tier models: {need_more_mid}")
        logger.info(f"[THINK TANK] Need more model diversity: {need_diversity}")
        
        # Add models if needed to ensure a good mix
        enhanced_models = list(models_to_use)  # Start with current models
        
        # Add specific requested models first (retry case)
        if requested_models:
            for model in requested_models:
                if model in available_models and model not in enhanced_models:
                    enhanced_models.append(model)
                    logger.info(f"[THINK TANK] Added specifically requested model: {model}")
        
        # Add missing high-quality models
        if need_more_high:
            for model in ModelCoverageAnalyzer.HIGH_QUALITY_MODELS:
                if model in available_models and model not in enhanced_models:
                    enhanced_models.append(model)
                    logger.info(f"[THINK TANK] Added high-quality model: {model}")
                    high_count += 1
                    if high_count >= 1:  # We've satisfied our requirement
                        break
        
        # Add missing mid-tier models
        if need_more_mid:
            for model in ModelCoverageAnalyzer.MID_QUALITY_MODELS:
                if model in available_models and model not in enhanced_models:
                    enhanced_models.append(model)
                    logger.info(f"[THINK TANK] Added mid-tier model: {model}")
                    mid_count += 1
                    if mid_count >= 1:  # We've satisfied our requirement
                        break
        
        # Ensure we have at least 2 models total for comparison
        if need_diversity and len(enhanced_models) < 2:
            for model in available_models:
                if model not in enhanced_models:
                    enhanced_models.append(model)
                    logger.info(f"[THINK TANK] Added model for diversity: {model}")
                    if len(enhanced_models) >= 2:  # We have enough models now
                        break
        
        # Check if we made any changes
        if enhanced_models != models_to_use:
            logger.info(f"[THINK TANK] Enhanced model selection: {enhanced_models}")
        
        return enhanced_models

    @staticmethod
    def generate_model_capabilities_dict(available_models: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Generates a capabilities dictionary for models to assist in evaluation and ranking.
        
        Args:
            available_models: List of available model processors
            
        Returns:
            Dictionary mapping model names to their capability scores
        """
        # Default capabilities for models in a standardized format
        model_capabilities = {
            # High-quality models
            'gpt4': {
                'knowledge': 0.95,
                'reasoning': 0.95,
                'creativity': 0.90,
                'coding': 0.92,
                'coherence': 0.95
            },
            'claude3': {
                'knowledge': 0.93,
                'reasoning': 0.94,
                'creativity': 0.92,
                'coding': 0.88,
                'coherence': 0.96
            },
            
            # Mid-tier models
            'mistral7b': {
                'knowledge': 0.85,
                'reasoning': 0.82,
                'creativity': 0.84,
                'coding': 0.80,
                'coherence': 0.83
            },
            'huggingface': {
                'knowledge': 0.82,
                'reasoning': 0.78,
                'creativity': 0.80,
                'coding': 0.75,
                'coherence': 0.80
            },
            'autogpt': {
                'knowledge': 0.80,
                'reasoning': 0.80,
                'creativity': 0.82,
                'coding': 0.85,
                'coherence': 0.78
            },
            
            # Basic models
            'gpt4all': {
                'knowledge': 0.75,
                'reasoning': 0.70,
                'creativity': 0.75,
                'coding': 0.65,
                'coherence': 0.72
            },
            'distilgpt2': {
                'knowledge': 0.65,
                'reasoning': 0.60,
                'creativity': 0.70,
                'coding': 0.50,
                'coherence': 0.65
            }
        }
        
        # Filter to only include available models
        result = {model: capabilities 
                 for model, capabilities in model_capabilities.items() 
                 if model in available_models}
        
        # Provide basic defaults for any model not in our predefined list
        for model in available_models:
            if model not in result:
                result[model] = {
                    'knowledge': 0.70,
                    'reasoning': 0.70,
                    'creativity': 0.70,
                    'coding': 0.70,
                    'coherence': 0.70
                }
                
        return result
