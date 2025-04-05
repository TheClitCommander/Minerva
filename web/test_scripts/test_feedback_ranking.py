#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback-Driven Model Ranking Test

This script directly tests the rank_responses function with and without feedback data
to validate the integration of user feedback into model selection.
"""

import os
import sys
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the web directory to the path
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, web_dir)

# Import directly - no package paths
from integrations.feedback import get_model_performance
from think_tank_processor import rank_responses

def test_model_ranking_with_feedback():
    """Test how feedback data influences model ranking"""
    logger.info("===== Testing Feedback Influence on Model Ranking =====")
    
    # Sample responses from different models
    test_responses = {
        "gpt-4": "GPT-4's response to the test query.",
        "claude-3": "Claude-3's response to the test query.",
        "gemini-pro": "Gemini Pro's response to the test query.",
        "mistral": "Mistral's response to the test query."
    }
    
    # Test with different query types
    test_queries = {
        "technical": "Explain how garbage collection works in Python.",
        "creative": "Write a haiku about artificial intelligence.",
        "reasoning": "Discuss the ethical implications of autonomous vehicles."
    }
    
    # First, rank without feedback
    logger.info("Ranking without feedback influence:")
    for query_type, query in test_queries.items():
        logger.info(f"\nTesting {query_type} query: {query}")
        
        # Get rankings without feedback
        ranked_without_feedback = rank_responses(test_responses, query, use_feedback=False)
        
        logger.info("Rankings WITHOUT feedback:")
        for i, (model, score) in enumerate(ranked_without_feedback):
            logger.info(f"  {i+1}. {model}: {score:.3f}")
    
    # Now, rank with feedback
    logger.info("\nRanking WITH feedback influence:")
    for query_type, query in test_queries.items():
        logger.info(f"\nTesting {query_type} query: {query}")
        
        # Get rankings with feedback
        ranked_with_feedback = rank_responses(test_responses, query, use_feedback=True)
        
        logger.info("Rankings WITH feedback:")
        for i, (model, score) in enumerate(ranked_with_feedback):
            logger.info(f"  {i+1}. {model}: {score:.3f}")
        
        # Check if feedback influenced rankings
        if ranked_with_feedback:
            # Compare top models
            top_model_without = ranked_without_feedback[0][0] if ranked_without_feedback else None
            top_model_with = ranked_with_feedback[0][0] if ranked_with_feedback else None
            
            if top_model_with != top_model_without:
                logger.info(f"✓ Feedback changed top model from {top_model_without} to {top_model_with}")
            else:
                # Check if scores changed
                models_dict_without = {model: score for model, score in ranked_without_feedback}
                models_dict_with = {model: score for model, score in ranked_with_feedback}
                
                score_changes = {}
                for model in models_dict_with.keys():
                    if model in models_dict_without:
                        score_change = models_dict_with[model] - models_dict_without[model]
                        score_changes[model] = score_change
                
                # Show score changes
                logger.info("Score changes due to feedback:")
                for model, change in score_changes.items():
                    if abs(change) > 0.001:  # Only show meaningful changes
                        direction = "↑" if change > 0 else "↓"
                        logger.info(f"  {model}: {change:.3f} {direction}")
    
    # Check model performance data
    logger.info("\nRetrieving model performance data:")
    performance = get_model_performance()
    
    if performance:
        logger.info(f"Found performance data for {len(performance)} models:")
        for model, data in performance.items():
            logger.info(f"  {model}:")
            logger.info(f"    Average score: {data.get('avg_score', 0):.3f}")
            logger.info(f"    Feedback count: {data.get('count', 0)}")
            
            # Show performance by query type
            if "query_types" in data and data["query_types"]:
                logger.info("    Performance by query type:")
                for qt, qt_data in data["query_types"].items():
                    logger.info(f"      {qt}: {qt_data.get('avg_score', 0):.3f} from {qt_data.get('count', 0)} entries")
    else:
        logger.warning("No model performance data found")
    
    logger.info("===== Test Completed =====")
    return

if __name__ == "__main__":
    try:
        test_model_ranking_with_feedback()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
