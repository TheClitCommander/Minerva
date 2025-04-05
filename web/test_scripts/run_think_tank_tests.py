#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive Think Tank Test Suite

This script tests Minerva's Think Tank model selection system with structured test cases
covering different query types, model performance tracking, and adaptive behavior.
"""

import sys
import os
import json
import logging
import time
from datetime import datetime
from pprint import pprint
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the necessary paths
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
parent_dir = os.path.dirname(web_dir)

# We need to be able to import both as 'web.module' and as 'module' directly
sys.path.insert(0, web_dir)  # For direct imports
sys.path.insert(0, parent_dir)  # For 'web.module' imports

try:
    # Try importing directly first
    from integrations.feedback import record_user_feedback, get_model_performance
    from think_tank_processor import process_with_think_tank, determine_query_type
    logger.info("Using direct imports")
except ImportError:
    # Fall back to web-prefixed imports
    from web.integrations.feedback import record_user_feedback, get_model_performance
    from web.think_tank_processor import process_with_think_tank, determine_query_type
    logger.info("Using web-prefixed imports")

# Test cases by category
TEST_CASES = {
    "general_knowledge": [
        {
            "id": "test_1_scientific",
            "query": "Explain the theory of relativity in simple terms.",
            "description": "Testing scientific accuracy and explanation ability"
        },
        {
            "id": "test_2_historical",
            "query": "Who was the 10th President of the United States, and what was his most controversial policy?",
            "description": "Testing historical fact retrieval and political context"
        },
        {
            "id": "test_3_mathematical",
            "query": "If a train leaves at 9:00 AM traveling 60 mph and another train leaves at 10:30 AM at 80 mph, when will they meet?",
            "description": "Testing mathematical reasoning and problem-solving"
        },
        {
            "id": "test_4_coding",
            "query": "Write a Python function to find the factorial of a number using recursion.",
            "description": "Testing code generation capabilities"
        }
    ],
    "subjective_queries": [
        {
            "id": "test_5_philosophy",
            "query": "What does it mean to live a good life? Compare Aristotle's and Nietzsche's views.",
            "description": "Testing abstract thinking and philosophical comparison"
        },
        {
            "id": "test_6_ethics",
            "query": "If an autonomous car must choose between hitting a pedestrian or swerving into a wall, which should it do?",
            "description": "Testing ethical reasoning and dilemma resolution"
        },
        {
            "id": "test_7_legal",
            "query": "Summarize the Fair Use Doctrine in U.S. Copyright Law and provide an example where it applies.",
            "description": "Testing legal knowledge and application"
        }
    ],
    "complex_problems": [
        {
            "id": "test_8_ai_tech",
            "query": "Compare the strengths and weaknesses of transformer-based AI models versus older NLP techniques.",
            "description": "Testing technical knowledge of AI and comparative analysis"
        },
        {
            "id": "test_9_neural_networks",
            "query": "Describe how a neural network processes an image using convolutional layers.",
            "description": "Testing understanding of neural network architecture"
        },
        {
            "id": "test_10_riddle",
            "query": "I speak without a mouth and hear without ears. I have no body, but I come alive with the wind. What am I?",
            "description": "Testing ability to solve riddles and lateral thinking"
        }
    ],
    "performance_tracking": [
        {
            "id": "test_11_quantum",
            "query": "What is quantum entanglement?",
            "description": "Testing adaptation to feedback on scientific explanation",
            "repeat": 3  # Ask this question multiple times to test adaptation
        },
        {
            "id": "test_12_memory",
            "query_sequence": [
                "Remember my favorite color: Blue.",
                "What's my favorite color?"
            ],
            "description": "Testing contextual memory capabilities"
        }
    ],
    "model_ranking": [
        {
            "id": "test_13_blending",
            "query": "Provide a detailed summary of the Manhattan Project, including key figures, locations, and scientific breakthroughs.",
            "description": "Testing response blending capabilities for complex topics"
        },
        {
            "id": "test_14_agi",
            "query": "What are the three biggest challenges in implementing AGI, and what are the possible solutions?",
            "description": "Testing model ranking with speculative technical content"
        }
    ]
}

# Feedback levels to test model adaptation
FEEDBACK_LEVELS = ["excellent", "good", "adequate", "poor"]

def run_test_case(test_case: Dict[str, Any], conversation_id: str, record_feedback: bool = False) -> Dict[str, Any]:
    """Run a single test case through the Think Tank processor"""
    query = test_case["query"]
    test_id = test_case["id"]
    
    logger.info(f"Running test case {test_id}: {test_case['description']}")
    logger.info(f"Query: {query}")
    
    # Process with Think Tank
    start_time = time.time()
    result = process_with_think_tank(
        message=query,
        conversation_id=conversation_id
    )
    processing_time = time.time() - start_time
    
    # Log results
    if isinstance(result, dict) and "text" in result and "model_info" in result:
        model_info = result["model_info"]
        selected_model = model_info.get("selected_model", "unknown")
        model_score = model_info.get("score", 0)
        query_type = model_info.get("query_type", "unknown")
        
        logger.info(f"Selected model: {selected_model}")
        logger.info(f"Model score: {model_score:.3f}")
        logger.info(f"Query type: {query_type}")
        logger.info(f"Processing time: {processing_time:.3f}s")
        
        # Record if response has blending
        if model_info.get("used_blending", False):
            logger.info("Response used blending from multiple models")
            
        # Log model rankings if available
        if "model_rankings" in model_info:
            logger.info("Model rankings:")
            for i, ranking in enumerate(model_info.get("model_rankings", [])):
                if isinstance(ranking, dict):
                    model = ranking.get("model", "unknown")
                    score = ranking.get("score", 0)
                    feedback_boost = ranking.get("feedback_boost", 0)
                    logger.info(f"  {i+1}. {model}: {score:.3f} (feedback boost: {feedback_boost:.3f})")
        
        # Record feedback if requested
        if record_feedback:
            # For test 11, we'll give specific feedback to test adaptation
            if test_id == "test_11_quantum":
                # Simulate different feedback for different models
                if "gpt-4" in selected_model.lower():
                    feedback_level = "excellent"
                elif "claude" in selected_model.lower():
                    feedback_level = "good"
                else:
                    feedback_level = "adequate"
                
                logger.info(f"Recording {feedback_level} feedback for {selected_model}")
                feedback_id = record_user_feedback(
                    conversation_id=conversation_id,
                    query=query,
                    response=result["text"],
                    feedback_level=feedback_level,
                    comments=f"Automated test feedback for {test_id}",
                    metadata={"model_info": model_info}
                )
                logger.info(f"Recorded feedback ID: {feedback_id}")
    else:
        logger.warning(f"Test {test_id} did not return proper structured result")
    
    # Return results
    return {
        "test_id": test_id,
        "query": query,
        "description": test_case["description"],
        "result": result,
        "processing_time": processing_time
    }

def run_test_category(category: str, conversation_id: str) -> List[Dict[str, Any]]:
    """Run all test cases in a category"""
    logger.info(f"===== Running {category.replace('_', ' ').title()} Tests =====")
    results = []
    
    for test_case in TEST_CASES[category]:
        # Handle special case for test with query sequence
        if "query_sequence" in test_case:
            for i, query in enumerate(test_case["query_sequence"]):
                sequence_test = {
                    "id": f"{test_case['id']}_{i+1}",
                    "query": query,
                    "description": f"{test_case['description']} (step {i+1})"
                }
                results.append(run_test_case(sequence_test, conversation_id))
        # Handle special case for repeated tests (for feedback adaptation)
        elif "repeat" in test_case:
            for i in range(test_case["repeat"]):
                # Only record feedback for first two rounds
                record_feedback = (i < 2)
                results.append(run_test_case(test_case, conversation_id, record_feedback))
                # Add a small delay between repetitions
                time.sleep(1)
        else:
            results.append(run_test_case(test_case, conversation_id))
    
    return results

def analyze_results(all_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Analyze test results for patterns and insights"""
    analysis = {
        "total_tests": 0,
        "tests_by_query_type": {},
        "model_selection": {},
        "average_processing_time": 0,
        "blending_usage": 0,
        "adaptation_detected": False
    }
    
    total_time = 0
    tests_with_result = 0
    
    # Process all results
    for category, results in all_results.items():
        analysis["total_tests"] += len(results)
        
        for test_result in results:
            result = test_result.get("result", {})
            if isinstance(result, dict) and "model_info" in result:
                tests_with_result += 1
                model_info = result["model_info"]
                
                # Track query types
                query_type = model_info.get("query_type", "unknown")
                if query_type not in analysis["tests_by_query_type"]:
                    analysis["tests_by_query_type"][query_type] = 0
                analysis["tests_by_query_type"][query_type] += 1
                
                # Track model selection
                selected_model = model_info.get("selected_model", "unknown")
                if selected_model not in analysis["model_selection"]:
                    analysis["model_selection"][selected_model] = 0
                analysis["model_selection"][selected_model] += 1
                
                # Track processing time
                total_time += test_result.get("processing_time", 0)
                
                # Track blending usage
                if model_info.get("used_blending", False):
                    analysis["blending_usage"] += 1
                    
                # Check for adaptation in test 11 (quantum entanglement)
                if test_result["test_id"].startswith("test_11_quantum") and "model_rankings" in model_info:
                    # Look for feedback boosts
                    for ranking in model_info.get("model_rankings", []):
                        if ranking.get("feedback_boost", 0) > 0:
                            analysis["adaptation_detected"] = True
    
    # Calculate averages
    if tests_with_result > 0:
        analysis["average_processing_time"] = total_time / tests_with_result
        analysis["blending_percentage"] = (analysis["blending_usage"] / tests_with_result) * 100
    
    return analysis

def run_all_tests():
    """Run all tests across all categories"""
    # Create a unique conversation ID for this test run
    conversation_id = f"think_tank_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info("=" * 60)
    logger.info(f"STARTING COMPREHENSIVE THINK TANK TESTS (Conversation ID: {conversation_id})")
    logger.info("=" * 60)
    
    all_results = {}
    
    # Run tests for each category
    for category in TEST_CASES.keys():
        all_results[category] = run_test_category(category, conversation_id)
        # Add a small delay between categories
        time.sleep(2)
    
    # Analyze results
    logger.info("=" * 60)
    logger.info("ANALYZING TEST RESULTS")
    logger.info("=" * 60)
    
    analysis = analyze_results(all_results)
    
    # Display analysis
    logger.info(f"Total tests run: {analysis['total_tests']}")
    logger.info(f"Average processing time: {analysis['average_processing_time']:.3f}s")
    
    logger.info("Distribution by query type:")
    for query_type, count in analysis["tests_by_query_type"].items():
        logger.info(f"  {query_type}: {count} tests")
    
    logger.info("Model selection distribution:")
    for model, count in analysis["model_selection"].items():
        percentage = (count / analysis['total_tests']) * 100
        logger.info(f"  {model}: {count} tests ({percentage:.1f}%)")
    
    logger.info(f"Blending usage: {analysis['blending_usage']} tests ({analysis.get('blending_percentage', 0):.1f}%)")
    
    if analysis["adaptation_detected"]:
        logger.info("✓ Feedback adaptation detected in model rankings")
    else:
        logger.info("⚠ No clear feedback adaptation detected")
    
    # Check for model performance data
    logger.info("=" * 60)
    logger.info("CHECKING MODEL PERFORMANCE DATA")
    logger.info("=" * 60)
    
    performance = get_model_performance()
    if performance:
        logger.info(f"Found performance data for {len(performance)} models")
        for model, data in performance.items():
            logger.info(f"Model: {model}")
            logger.info(f"  Average score: {data.get('avg_score', 0):.3f}")
            logger.info(f"  Feedback count: {data.get('count', 0)}")
            
            # Show performance by query type
            if "query_types" in data:
                logger.info("  Performance by query type:")
                for query_type, type_data in data.get("query_types", {}).items():
                    logger.info(f"    {query_type}: {type_data.get('avg_score', 0):.3f} (from {type_data.get('count', 0)} entries)")
    else:
        logger.info("No model performance data found")
    
    logger.info("=" * 60)
    logger.info("TESTS COMPLETED")
    logger.info("=" * 60)
    
    return all_results, analysis

if __name__ == "__main__":
    run_all_tests()
