#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Feedback-Driven Model Selection Test

This script tests the integration of Minerva's feedback system with the
Think Tank model selection logic, validating that past user feedback
influences future model selection decisions.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pprint import pprint

# Add parent directory to path for importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from integrations.feedback import record_user_feedback, get_model_performance
from think_tank_processor import process_with_think_tank, determine_query_type, rank_responses

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test data
TEST_CONVERSATION_ID = f"feedback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_QUERIES = {
    "technical": [
        "How do I implement a binary search tree in Python?",
        "Explain the difference between TCP and UDP protocols",
        "Write a function to find prime numbers using the Sieve of Eratosthenes"
    ],
    "creative": [
        "Write a short poem about artificial intelligence",
        "Describe a futuristic city in the year 2150",
        "Create a story about a robot that gains consciousness"
    ],
    "reasoning": [
        "What are the ethical implications of autonomous vehicles?",
        "Analyze the pros and cons of universal basic income",
        "Explain how quantum computing might impact cybersecurity"
    ],
    "general": [
        "What are some good books to read?",
        "How can I improve my public speaking skills?",
        "Tell me about the history of jazz music"
    ]
}

def test_feedback_recording():
    """Test recording feedback for different models and query types"""
    logger.info("Testing feedback recording...")
    
    # Record synthetic feedback data for testing
    feedback_data = [
        # GPT-4 performs well on technical questions
        {"model": "gpt-4", "query_type": "technical", "feedback": "excellent", "count": 3},
        {"model": "gpt-4", "query_type": "creative", "feedback": "good", "count": 2},
        {"model": "gpt-4", "query_type": "reasoning", "feedback": "good", "count": 2},
        
        # Claude performs well on creative and reasoning
        {"model": "claude-3", "query_type": "technical", "feedback": "good", "count": 2},
        {"model": "claude-3", "query_type": "creative", "feedback": "excellent", "count": 3},
        {"model": "claude-3", "query_type": "reasoning", "feedback": "excellent", "count": 3},
        
        # Mistral is decent at technical but not as good at creative
        {"model": "mistral", "query_type": "technical", "feedback": "good", "count": 2},
        {"model": "mistral", "query_type": "creative", "feedback": "adequate", "count": 2},
        {"model": "mistral", "query_type": "reasoning", "feedback": "adequate", "count": 2}
    ]
    
    # Record multiple feedback entries for each model and query type
    for entry in feedback_data:
        for i in range(entry["count"]):
            query = TEST_QUERIES[entry["query_type"]][i % len(TEST_QUERIES[entry["query_type"]])]
            response = f"Test response from {entry['model']} for query type {entry['query_type']}"
            
            # Create model info metadata
            model_info = {
                "selected_model": entry["model"],
                "is_api_model": entry["model"] in ["gpt-4", "claude-3", "gemini"],
                "query_type": entry["query_type"],
                "score": 0.8,
                "used_blending": False
            }
            
            # Record feedback with model metadata
            feedback_id = record_user_feedback(
                conversation_id=TEST_CONVERSATION_ID,
                query=query,
                response=response,
                feedback_level=entry["feedback"],
                comments=f"Test feedback for {entry['model']}",
                metadata={"model_info": model_info}
            )
            
            logger.info(f"Recorded {entry['feedback']} feedback for {entry['model']} on {entry['query_type']} query: {feedback_id}")
    
    logger.info("Completed feedback recording test")
    return True

def test_model_performance_analysis():
    """Test retrieving and analyzing model performance based on feedback"""
    logger.info("Testing model performance analysis...")
    
    # Get overall model performance
    performance = get_model_performance(min_feedback_entries=5)
    logger.info(f"Retrieved performance data for {len(performance)} models")
    
    # Check if we have data for our test models
    expected_models = ["gpt-4", "claude-3", "mistral"]
    for model in expected_models:
        if model.lower() in performance:
            logger.info(f"Model {model} analysis:")
            logger.info(f"  Average score: {performance[model.lower()]['avg_score']:.2f}")
            logger.info(f"  Sample count: {performance[model.lower()]['count']}")
            logger.info(f"  Query types: {list(performance[model.lower()]['query_types'].keys())}")
        else:
            logger.warning(f"No performance data found for {model}")
    
    # Get performance for specific query types
    for query_type in ["technical", "creative", "reasoning"]:
        type_performance = get_model_performance(query_type=query_type, min_feedback_entries=2)
        logger.info(f"{query_type.title()} query performance: {len(type_performance)} models available")
        
        # Display top model for this query type
        if type_performance:
            top_model = max(type_performance.items(), key=lambda x: x[1]["avg_score"])[0]
            logger.info(f"  Top model for {query_type}: {top_model} with avg score {type_performance[top_model]['avg_score']:.2f}")
    
    logger.info("Completed model performance analysis test")
    return performance

def test_feedback_influenced_ranking():
    """Test that feedback influences model ranking and selection"""
    logger.info("Testing feedback-influenced ranking...")
    
    # Simulate ranking with feedback for different query types
    for query_type, queries in TEST_QUERIES.items():
        test_query = queries[0]
        logger.info(f"Testing ranking for {query_type} query: {test_query}")
        
        # Create sample responses
        test_responses = {
            "gpt-4": f"GPT-4 response for {query_type} query",
            "claude-3": f"Claude-3 response for {query_type} query",
            "mistral": f"Mistral response for {query_type} query"
        }
        
        # Rank with and without feedback
        ranked_with_feedback = rank_responses(test_responses, test_query, use_feedback=True)
        ranked_without_feedback = rank_responses(test_responses, test_query, use_feedback=False)
        
        # Compare rankings
        logger.info("Rankings WITH feedback:")
        for i, (model, score) in enumerate(ranked_with_feedback):
            logger.info(f"  {i+1}. {model}: {score:.3f}")
            
        logger.info("Rankings WITHOUT feedback:")
        for i, (model, score) in enumerate(ranked_without_feedback):
            logger.info(f"  {i+1}. {model}: {score:.3f}")
        
        # Check if rankings differ
        if [m for m, s in ranked_with_feedback] != [m for m, s in ranked_without_feedback]:
            logger.info("✓ Feedback successfully influenced model ranking order")
        else:
            logger.info("⚠ Feedback did not change ranking order, but scores might still be affected")
            
        # Compare scores
        if ranked_with_feedback and ranked_without_feedback:
            top_model_with_feedback = ranked_with_feedback[0][0]
            top_model_without_feedback = ranked_without_feedback[0][0]
            
            if top_model_with_feedback != top_model_without_feedback:
                logger.info(f"✓ Feedback changed top model from {top_model_without_feedback} to {top_model_with_feedback}")
    
    logger.info("Completed feedback influence test")
    return True

def test_end_to_end_think_tank():
    """Test the end-to-end Think Tank processing with feedback integration"""
    logger.info("Testing Think Tank end-to-end with feedback...")
    
    # Process a query for each query type
    for query_type, queries in TEST_QUERIES.items():
        test_query = queries[0]
        logger.info(f"Testing Think Tank for {query_type} query: {test_query}")
        
        # Process with Think Tank
        result = process_with_think_tank(
            message=test_query,
            conversation_id=TEST_CONVERSATION_ID
        )
        
        # Check result structure
        if isinstance(result, dict) and "text" in result and "model_info" in result:
            logger.info("✓ Think Tank returned structured result with model info")
            
            # Display selected model and scores
            model_info = result["model_info"]
            logger.info(f"Selected model: {model_info['selected_model']}")
            logger.info(f"Model score: {model_info.get('score', 'N/A')}")
            logger.info(f"Query type detected: {model_info.get('query_type', 'N/A')}")
            
            # Check if blending was used
            if model_info.get("used_blending", False):
                logger.info("Response was created by blending multiple models")
            
            # Check if there was a feedback boost
            if "model_rankings" in model_info:
                for ranking in model_info["model_rankings"]:
                    if "feedback_boost" in ranking and ranking["feedback_boost"] != 0:
                        logger.info(f"✓ Model {ranking['model']} had a feedback boost of {ranking['feedback_boost']}")
        else:
            logger.warning("⚠ Think Tank did not return structured result with model info")
    
    logger.info("Completed end-to-end Think Tank test")
    return True

def run_all_tests():
    """Run all feedback integration tests"""
    logger.info("=" * 50)
    logger.info("STARTING FEEDBACK INTEGRATION TESTS")
    logger.info("=" * 50)
    
    # Step 1: Record test feedback data
    test_feedback_recording()
    
    # Step 2: Test model performance analysis
    performance = test_model_performance_analysis()
    
    # Step 3: Test feedback influence on ranking
    test_feedback_influenced_ranking()
    
    # Step 4: Test end-to-end Think Tank
    test_end_to_end_think_tank()
    
    logger.info("=" * 50)
    logger.info("ALL TESTS COMPLETED")
    logger.info("=" * 50)

if __name__ == "__main__":
    run_all_tests()
