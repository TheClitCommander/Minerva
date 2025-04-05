#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback Data Test

This script tests the feedback data storage and retrieval functionality,
which is a core part of the feedback-driven model selection system.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the web directory to the path
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, web_dir)

# Import feedback module directly - this should work regardless of package structure
from integrations.feedback import record_user_feedback, get_model_performance, get_feedback_entry

def test_feedback_storage_and_retrieval():
    """Test basic feedback storage and retrieval"""
    logger.info("===== Testing Feedback Storage and Retrieval =====")
    
    # Create a unique conversation ID for this test
    conversation_id = f"feedback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Test conversation ID: {conversation_id}")
    
    # Create test feedback entries for different model types and query types
    test_models = {
        "gpt-4": {"is_api": True, "query_types": ["technical", "creative", "reasoning"]},
        "claude-3": {"is_api": True, "query_types": ["creative", "reasoning"]},
        "gemini-pro": {"is_api": True, "query_types": ["technical"]},
        "mistral": {"is_api": False, "query_types": ["technical", "general"]}
    }
    
    # Record feedback for each model and query type
    feedback_ids = []
    for model, info in test_models.items():
        for query_type in info["query_types"]:
            # Create a sample query for this type
            if query_type == "technical":
                query = "Explain how garbage collection works in Python."
            elif query_type == "creative":
                query = "Write a haiku about artificial intelligence."
            elif query_type == "reasoning":
                query = "Discuss the ethical implications of autonomous vehicles."
            else:  # general
                query = "What are some good books to read?"
                
            # Create a sample response
            response = f"This is a test response from {model} for a {query_type} query."
            
            # Create model info for metadata
            model_info = {
                "selected_model": model,
                "is_api_model": info["is_api"],
                "query_type": query_type,
                "score": 0.85,
                "processing_time": 1.2,
                "used_blending": False
            }
            
            # Determine feedback level based on model and query type combinations
            if model == "gpt-4" and query_type == "technical":
                feedback_level = "excellent"
            elif model == "claude-3" and query_type == "creative":
                feedback_level = "excellent"
            elif model == "mistral" and query_type == "technical":
                feedback_level = "good"
            else:
                feedback_level = "adequate"
            
            # Record the feedback
            feedback_id = record_user_feedback(
                conversation_id=conversation_id,
                query=query,
                response=response,
                feedback_level=feedback_level,
                comments=f"Test feedback for {model} on {query_type} query",
                metadata={"model_info": model_info}
            )
            
            logger.info(f"Recorded {feedback_level} feedback for {model} on {query_type} query: {feedback_id}")
            feedback_ids.append(feedback_id)
    
    # Verify feedback was stored by retrieving entries
    logger.info("\nVerifying feedback storage by retrieving entries:")
    for feedback_id in feedback_ids:
        entry = get_feedback_entry(feedback_id)
        if entry:
            model = entry.get("metadata", {}).get("model_info", {}).get("selected_model", "unknown")
            query_type = entry.get("metadata", {}).get("model_info", {}).get("query_type", "unknown")
            feedback_level = entry.get("feedback_level", "unknown")
            
            logger.info(f"Retrieved feedback {feedback_id}: {model} ({query_type}) - {feedback_level}")
        else:
            logger.warning(f"Failed to retrieve feedback entry {feedback_id}")
    
    # Test model performance analysis
    logger.info("\nTesting model performance analysis:")
    
    # Get overall performance
    performance = get_model_performance()
    if performance:
        logger.info(f"Retrieved overall performance for {len(performance)} models:")
        for model, data in performance.items():
            logger.info(f"  {model}: avg_score={data.get('avg_score', 0):.3f}, count={data.get('count', 0)}")
    else:
        logger.warning("No overall performance data found")
    
    # Get performance by query type
    for query_type in ["technical", "creative", "reasoning", "general"]:
        query_performance = get_model_performance(query_type=query_type)
        if query_performance:
            logger.info(f"\nPerformance for {query_type} queries:")
            for model, data in query_performance.items():
                logger.info(f"  {model}: avg_score={data.get('avg_score', 0):.3f}, count={data.get('count', 0)}")
        else:
            logger.info(f"No performance data found for {query_type} queries")
    
    # Get performance for a specific model
    for model in test_models.keys():
        model_performance = get_model_performance(model_name=model)
        if model_performance and model in model_performance:
            data = model_performance[model]
            logger.info(f"\nPerformance for {model}:")
            logger.info(f"  Overall: avg_score={data.get('avg_score', 0):.3f}, count={data.get('count', 0)}")
            
            # Show performance by query type
            if "query_types" in data:
                for qt, qt_data in data.get("query_types", {}).items():
                    logger.info(f"  {qt}: avg_score={qt_data.get('avg_score', 0):.3f}, count={qt_data.get('count', 0)}")
        else:
            logger.info(f"No performance data found for {model}")
    
    logger.info("\n===== Feedback Test Completed =====")
    return feedback_ids

if __name__ == "__main__":
    try:
        test_feedback_storage_and_retrieval()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
