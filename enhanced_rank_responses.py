import json
import logging
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enhanced_rank_responses")

def rank_responses(responses, task_info, query_type=None):
    """Ranks responses based on multiple scoring factors: voting, consensus, confidence"""
    
    logger.info(f"Starting enhanced rank_responses with task_info type: {type(task_info).__name__}")
    
    # Initialize model type weights if not already defined
    MODEL_TYPE_WEIGHTS = {
        "factual": {
            "gpt-3.5-turbo": 1.0,
            "gpt-4o": 0.9,
            "gpt-4": 0.9,
            "gpt4": 0.9,
            "claude-3-opus": 0.9,
            "claude-3-sonnet": 0.85
        },
        "technical": {
            "gpt-4": 0.95,
            "gpt-4o": 1.0,
            "gpt4": 0.95
        },
        "code": {
            "gpt-4": 0.95,
            "gpt-4o": 1.0,
            "gpt4": 0.95
        },
        "creative": {
            "claude-3-opus": 1.0,
            "claude-3": 0.95,
            "claude3": 0.95
        },
        "reasoning": {
            "gpt-4": 0.95,
            "gpt-4o": 1.0,
            "gpt4": 0.95
        },
        "multi-perspective": {
            "claude-3-opus": 1.0,
            "claude-3": 0.95,
            "claude3": 0.95
        }
    }
    
    # Default weight for unknown models
    DEFAULT_MODEL_WEIGHT = 0.6
    
    # Ensure task_info is properly formatted
    if isinstance(task_info, str):
        try:
            task_info = json.loads(task_info)
            logger.info(f"Converted task_info from string to dict: {task_info}")
        except json.JSONDecodeError:
            logger.warning(f"Could not parse task_info as JSON: {task_info}")
            task_info = {}
    elif task_info is None:
        task_info = {}
        
    # Extract query type from task_info or use provided query_type
    extracted_query_type = None
    if isinstance(task_info, dict):
        extracted_query_type = task_info.get("query_type") or task_info.get("task_type")
        # Also check for category/type in case those are used instead
        if not extracted_query_type:
            extracted_query_type = task_info.get("category") or task_info.get("type")
    
    # Use the best available query type
    effective_query_type = extracted_query_type or query_type or "general"
    logger.info(f"Using query_type: {effective_query_type}")
    
    # Map common query types to our standardized types
    type_mapping = {
        "fact": "factual",
        "fact_simple": "factual",
        "facts": "factual",
        "tech": "technical",
        "programming": "code",
        "software": "code",
        "creative_writing": "creative",
        "analytical": "reasoning",
        "comparison": "multi-perspective",
        "debate": "multi-perspective"
    }
    
    # Standardize the query type
    standardized_type = type_mapping.get(effective_query_type.lower(), effective_query_type.lower())
    logger.info(f"Standardized query_type: {standardized_type}")
    
    # If we don't have weights for this query type, use general weights
    if standardized_type not in MODEL_TYPE_WEIGHTS:
        standardized_type = "general"
        logger.info(f"Using general weights since {effective_query_type} is not recognized")
    
    # Compute capability scores based on model type
    model_capability_scores = {}
    for model in responses.keys():
        if standardized_type in MODEL_TYPE_WEIGHTS and model in MODEL_TYPE_WEIGHTS[standardized_type]:
            model_capability_scores[model] = MODEL_TYPE_WEIGHTS[standardized_type][model]
        else:
            # Default score for models not in our capability mapping
            model_capability_scores[model] = DEFAULT_MODEL_WEIGHT
    
    logger.info(f"Model capability scores: {model_capability_scores}")
    
    # Compute final ranking scores (weighted heavily toward capabilities for accuracy)
    final_scores = {}
    for model, response in responses.items():
        # Get model capability score (this is the most important factor)
        capability = model_capability_scores.get(model, DEFAULT_MODEL_WEIGHT)
        
        # For now, use placeholder values for consensus and content quality
        # In a real implementation, these would be calculated based on response content
        consensus = 0.7  # Placeholder
        content_quality = 0.7  # Placeholder
        
        # Weight factors: Capability (70%), Content Quality (20%), Consensus (10%)
        # This heavily weights model selection based on known capabilities
        final_score = (capability * 0.7) + (content_quality * 0.2) + (consensus * 0.1)
        final_scores[model] = final_score
        
        logger.info(f"Model {model} final score: {final_score} (capability={capability})")
    
    # Rank models based on final computed scores
    ranked_models = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"Final ranking: {ranked_models}")
    
    # Create detailed output in the expected format
    result = {
        'scores': final_scores,
        'ranked_models': ranked_models,
        'best_model': ranked_models[0][0] if ranked_models else None,
        'capability_scores': model_capability_scores
    }
    
    return result
