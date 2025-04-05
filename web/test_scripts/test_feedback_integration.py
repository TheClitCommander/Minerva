#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Feedback Integration Test

This script tests the integration of feedback data with Minerva's Think Tank model selection.
"""

import os
import sys
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(web_dir)

# Add both directories to the path
sys.path.insert(0, parent_dir)
sys.path.insert(0, web_dir)

# Add 'web' to sys.modules to handle the circular imports
import sys

# Create a special import handler for the 'web' package
class WebModuleProxy:
    def __getattr__(self, name):
        # When something tries to import from 'web.X', redirect to a direct import of X
        try:
            return __import__(name)
        except ImportError:
            # If direct import fails, try as web.X for backward compatibility
            return __import__(f'web.{name}', fromlist=[name])

# Register our proxy for 'web' imports if it doesn't exist
if 'web' not in sys.modules:
    sys.modules['web'] = WebModuleProxy()

# Import Minerva modules with proper path handling
from integrations.feedback import record_user_feedback, get_model_performance

# Import think_tank_processor with a try/except to handle different import scenarios
try:
    import think_tank_processor
except ImportError:
    logger.warning("Could not import think_tank_processor directly, trying through web package")
    from web import think_tank_processor

# Test queries for different query types
TEST_QUERIES = {
    "technical": "Explain the difference between TCP and UDP protocols",
    "creative": "Write a short poem about artificial intelligence",
    "reasoning": "What are the ethical implications of autonomous vehicles?",
    "general": "How can I improve my public speaking skills?"
}

def test_feedback_influence():
    """Test how feedback data influences model ranking"""
    logger.info("===== Testing Feedback Influence on Model Ranking =====")
    
    # Create unique conversation ID for this test
    conversation_id = f"feedback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"Using conversation ID: {conversation_id}")
    
    # Step 1: Process queries without prior feedback
    logger.info("Step 1: Processing queries without prior feedback...")
    initial_results = {}
    
    for query_type, query in TEST_QUERIES.items():
        logger.info(f"Processing {query_type} query: {query[:50]}...")
        result = think_tank_processor.process_with_think_tank(query, conversation_id=conversation_id)
        
        if isinstance(result, dict) and "model_info" in result:
            model_info = result["model_info"]
            selected_model = model_info.get("selected_model")
            score = model_info.get("score", 0)
            logger.info(f"Selected model for {query_type}: {selected_model} (score: {score:.3f})")
            
            # Store result for comparison
            initial_results[query_type] = {
                "selected_model": selected_model,
                "score": score,
                "model_info": model_info
            }
            
            # Log rankings if available
            if "model_rankings" in model_info:
                logger.info("Model rankings:")
                for i, ranking in enumerate(model_info.get("model_rankings", [])):
                    if isinstance(ranking, dict):
                        model = ranking.get("model", "unknown")
                        score = ranking.get("score", 0)
                        logger.info(f"  {i+1}. {model}: {score:.3f}")
    
    # Step 2: Record synthetic feedback
    logger.info("\nStep 2: Recording synthetic feedback...")
    feedback_data = {
        "technical": {
            "gpt-4": "excellent",  # GPT-4 is excellent for technical
            "claude-3": "good",    # Claude is good for technical
            "gemini-pro": "adequate"  # Gemini is adequate for technical
        },
        "creative": {
            "gpt-4": "good",       # GPT-4 is good for creative
            "claude-3": "excellent",  # Claude is excellent for creative
            "gemini-pro": "good"      # Gemini is good for creative
        },
        "reasoning": {
            "gpt-4": "good",       # GPT-4 is good for reasoning
            "claude-3": "excellent",  # Claude is excellent for reasoning
            "gemini-pro": "adequate"  # Gemini is adequate for reasoning
        }
    }
    
    # Record feedback for each query type and model
    for query_type, model_feedback in feedback_data.items():
        query = TEST_QUERIES[query_type]
        for model, feedback_level in model_feedback.items():
            # Create a sample response
            response = f"This is a test response from {model} for a {query_type} query."
            
            # Create model info metadata
            model_info = {
                "selected_model": model,
                "is_api_model": model in ["gpt-4", "claude-3", "gemini-pro"],
                "query_type": query_type,
                "score": 0.8,
                "used_blending": False
            }
            
            # Record feedback multiple times to build up data
            for i in range(3):  # Record 3 entries for each model/query type
                feedback_id = record_user_feedback(
                    conversation_id=conversation_id,
                    query=query,
                    response=response,
                    feedback_level=feedback_level,
                    comments=f"Test feedback {i+1} for {model} on {query_type}",
                    metadata={"model_info": model_info}
                )
                logger.info(f"Recorded {feedback_level} feedback for {model} on {query_type} query")
    
    # Step 3: Check model performance data
    logger.info("\nStep 3: Checking model performance data...")
    performance = get_model_performance()
    
    if performance:
        logger.info(f"Retrieved performance data for {len(performance)} models")
        
        # Check performance by query type
        for query_type in ["technical", "creative", "reasoning"]:
            type_performance = get_model_performance(query_type=query_type)
            if type_performance:
                logger.info(f"\n{query_type.title()} query performance:")
                for model, data in type_performance.items():
                    logger.info(f"  {model}: avg score {data.get('avg_score', 0):.3f} ({data.get('count', 0)} entries)")
    else:
        logger.warning("No model performance data retrieved")
    
    # Step 4: Process the same queries again to see if feedback influences model selection
    logger.info("\nStep 4: Processing queries again after feedback...")
    final_results = {}
    
    for query_type, query in TEST_QUERIES.items():
        logger.info(f"Processing {query_type} query again: {query[:50]}...")
        result = think_tank_processor.process_with_think_tank(query, conversation_id=conversation_id)
        
        if isinstance(result, dict) and "model_info" in result:
            model_info = result["model_info"]
            selected_model = model_info.get("selected_model")
            score = model_info.get("score", 0)
            logger.info(f"Selected model for {query_type}: {selected_model} (score: {score:.3f})")
            
            # Store result for comparison
            final_results[query_type] = {
                "selected_model": selected_model,
                "score": score,
                "model_info": model_info
            }
            
            # Check for feedback influence in rankings
            if "model_rankings" in model_info:
                logger.info("Model rankings with feedback influence:")
                for i, ranking in enumerate(model_info.get("model_rankings", [])):
                    if isinstance(ranking, dict):
                        model = ranking.get("model", "unknown")
                        score = ranking.get("score", 0)
                        feedback_boost = ranking.get("feedback_boost", 0)
                        logger.info(f"  {i+1}. {model}: {score:.3f} (feedback boost: {feedback_boost:.3f})")
    
    # Step 5: Compare results to check for feedback influence
    logger.info("\nStep 5: Analyzing feedback influence...")
    
    for query_type in TEST_QUERIES.keys():
        if query_type in initial_results and query_type in final_results:
            initial = initial_results[query_type]
            final = final_results[query_type]
            
            logger.info(f"\n{query_type.title()} query comparison:")
            logger.info(f"  Initial model: {initial['selected_model']} (score: {initial['score']:.3f})")
            logger.info(f"  Final model: {final['selected_model']} (score: {final['score']:.3f})")
            
            # Check if model selection changed
            if initial["selected_model"] != final["selected_model"]:
                logger.info(f"  ✓ Model selection changed due to feedback!")
            else:
                # Check if score changed
                if final["score"] > initial["score"]:
                    logger.info(f"  ✓ Model score increased due to feedback!")
                else:
                    logger.info(f"  ⚠ No clear feedback influence detected")
                    
            # Look for feedback boosts in final rankings
            feedback_influenced = False
            if "model_info" in final and "model_rankings" in final["model_info"]:
                for ranking in final["model_info"]["model_rankings"]:
                    if isinstance(ranking, dict) and ranking.get("feedback_boost", 0) > 0:
                        feedback_influenced = True
                        logger.info(f"  ✓ Detected feedback boost of {ranking.get('feedback_boost', 0):.3f} for {ranking.get('model', 'unknown')}")
            
            if not feedback_influenced:
                logger.info("  ⚠ No feedback boosts detected in rankings")
    
    logger.info("\n===== Test Completed =====")
    return initial_results, final_results

if __name__ == "__main__":
    try:
        test_feedback_influence()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
