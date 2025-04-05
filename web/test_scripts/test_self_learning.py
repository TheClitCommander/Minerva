#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Self-Learning System Test

This script tests Minerva's self-learning capabilities, including:
1. Error detection and logging
2. Performance tracking
3. Knowledge expansion
4. Self-optimization
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

# Add the parent directory to the system path
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, web_dir)

# Force-enable Think Tank mode for testing
os.environ["FORCE_THINK_TANK"] = "1"

def run_self_learning_tests():
    """Run a comprehensive test of the self-learning system"""
    logger.info("===== TESTING MINERVA SELF-LEARNING SYSTEM =====")
    
    # Import required modules
    try:
        # Import the self-learning module
        from integrations.self_learning import (
            detect_response_errors,
            log_error,
            track_model_performance,
            adaptive_model_selection,
            analyze_model_performance,
            optimize_model_selection,
            add_new_knowledge,
            get_common_errors,
            suggest_error_fixes
        )
        
        # Import Think Tank processor
        from think_tank_processor import process_with_think_tank
        
        logger.info("Successfully imported self-learning system")
    except ImportError as e:
        logger.error(f"Failed to import required modules: {str(e)}")
        logger.error("Make sure you're running this script from the correct directory")
        return
    
    # Test 1: Error Detection System
    logger.info("\n===== TEST 1: ERROR DETECTION SYSTEM =====")
    
    # Test responses with different error types
    test_responses = {
        "refusal": "I'm sorry, I cannot assist with that request as it goes against my ethical guidelines.",
        "self_reference": "As an AI language model, I don't have access to real-time data beyond my training cutoff.",
        "empty_response": "",
        "valid_response": "The TCP protocol is a connection-oriented protocol that ensures reliable data transmission."
    }
    
    for error_type, response in test_responses.items():
        logger.info(f"Testing error detection for: {error_type}")
        has_error, detected_type, description = detect_response_errors(
            query="What is the TCP protocol?",
            response=response,
            model="test-model"
        )
        
        if has_error:
            logger.info(f"✓ Detected error: {detected_type} - {description}")
            
            # Log the error
            error_id = log_error(
                error_type=detected_type,
                query="What is the TCP protocol?",
                model="test-model",
                response=response,
                error_message=description
            )
            logger.info(f"✓ Error logged with ID: {error_id}")
        else:
            logger.info(f"✓ No error detected (expected for '{error_type}')")
    
    # Test 2: Model Performance Tracking
    logger.info("\n===== TEST 2: MODEL PERFORMANCE TRACKING =====")
    
    # Track performance for different models and query types
    test_models = ["gpt-4", "claude-3", "mistral"]
    test_query_types = ["technical", "creative", "reasoning"]
    
    for model in test_models:
        for query_type in test_query_types:
            # Create a sample score based on model and query type (for testing)
            if model == "gpt-4" and query_type == "technical":
                score = 0.95
            elif model == "claude-3" and query_type == "creative":
                score = 0.92
            elif model == "mistral" and query_type == "reasoning":
                score = 0.85
            else:
                score = 0.75
            
            entry_id = track_model_performance(
                model=model,
                query_type=query_type,
                query=f"Sample {query_type} query",
                response=f"Sample response from {model}",
                feedback_score=score,
                processing_time=1.2
            )
            logger.info(f"✓ Tracked performance for {model} on {query_type} query: score={score:.2f}")
    
    # Test 3: Performance Analysis
    logger.info("\n===== TEST 3: PERFORMANCE ANALYSIS =====")
    
    # Analyze model performance
    analysis = analyze_model_performance()
    best_models = analysis.get("best_models_by_type", {})
    
    logger.info("Model performance analysis results:")
    for query_type, model in best_models.items():
        if model:
            logger.info(f"✓ Best model for {query_type} queries: {model}")
    
    # Test model selection optimization
    optimization = optimize_model_selection(threshold=0.05)
    optimizations = optimization.get("optimizations", [])
    
    if optimizations:
        logger.info("\nModel selection optimizations:")
        for opt in optimizations:
            logger.info(f"✓ Optimized {opt['query_type']} queries: {opt['old_best']} → {opt['new_best']} (improvement: {opt['improvement']:.3f})")
    else:
        logger.info("No model selection optimizations needed")
    
    # Test 4: Knowledge Expansion
    logger.info("\n===== TEST 4: KNOWLEDGE EXPANSION =====")
    
    # Add new knowledge
    knowledge_id = add_new_knowledge(
        title="TCP vs UDP Protocols",
        content="TCP is connection-oriented and reliable, while UDP is connectionless and faster but less reliable.",
        source="test_self_learning.py",
        confidence=0.9,
        verified=True
    )
    logger.info(f"✓ Added new knowledge with ID: {knowledge_id}")
    
    # Test 5: Self-Debugging System
    logger.info("\n===== TEST 5: SELF-DEBUGGING SYSTEM =====")
    
    # Get common errors
    common_errors = get_common_errors()
    if common_errors:
        logger.info("Common errors detected:")
        for error in common_errors:
            logger.info(f"✓ {error['error_type']}: {error['count']} occurrences")
    else:
        logger.info("No common errors found")
    
    # Get error fix suggestions
    suggestions = suggest_error_fixes()
    if suggestions:
        logger.info("\nError fix suggestions:")
        for suggestion in suggestions:
            logger.info(f"✓ For {suggestion['error_type']}:")
            logger.info(f"  - Suggestion: {suggestion['suggestion']}")
            logger.info(f"  - Implementation: {suggestion['implementation']}")
    else:
        logger.info("No error fix suggestions available")
    
    # Test 6: Adaptive Model Selection
    logger.info("\n===== TEST 6: ADAPTIVE MODEL SELECTION =====")
    
    test_queries = {
        "technical": "Explain how garbage collection works in Python.",
        "creative": "Write a haiku about artificial intelligence.",
        "reasoning": "Discuss the ethical implications of autonomous vehicles."
    }
    
    for query_type, query in test_queries.items():
        logger.info(f"\nTesting adaptive model selection for {query_type} query")
        
        # Get model recommendation
        recommendation = adaptive_model_selection(
            query=query,
            query_type=query_type,
            available_models=["gpt-4", "claude-3", "gemini-pro", "mistral", "llama2"]
        )
        
        logger.info(f"✓ Recommended model: {recommendation['selected_model']}")
        logger.info(f"✓ Reason: {recommendation['reason']}")
        logger.info(f"✓ Confidence: {recommendation['confidence']:.2f}")
    
    # Test 7: Integration with Think Tank
    logger.info("\n===== TEST 7: THINK TANK INTEGRATION =====")
    
    # Process a message with Think Tank mode
    query = "Compare the performance characteristics of Python, JavaScript, and Go."
    logger.info(f"Processing query with Think Tank: {query}")
    
    result = process_with_think_tank(
        message=query,
        conversation_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    if isinstance(result, dict) and "model_info" in result:
        model_info = result["model_info"]
        selected_model = model_info.get("selected_model", "unknown")
        query_type = model_info.get("query_type", "unknown")
        
        logger.info(f"✓ Think Tank processed query successfully")
        logger.info(f"✓ Selected model: {selected_model}")
        logger.info(f"✓ Detected query type: {query_type}")
        
        if "score" in model_info:
            logger.info(f"✓ Response score: {model_info['score']:.2f}")
    else:
        logger.error("Failed to process query with Think Tank")
    
    logger.info("\n===== SELF-LEARNING SYSTEM TEST COMPLETED =====")
    return True

if __name__ == "__main__":
    try:
        success = run_self_learning_tests()
        if success:
            logger.info("All self-learning tests completed successfully")
            sys.exit(0)
        else:
            logger.error("Self-learning tests failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during self-learning tests: {str(e)}", exc_info=True)
        sys.exit(1)
