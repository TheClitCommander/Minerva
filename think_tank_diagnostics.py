#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Think Tank Diagnostics

This script performs step-by-step diagnostics on the Think Tank mode
to identify exactly where response generation is failing.
"""

import os
import sys
import logging
import json
import time
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("think_tank_diagnostics")

# Add the Minerva directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create diagnostic wrapper functions that provide detailed logging
def diagnostic_wrapper(func_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"[DIAGNOSTIC] Starting {func_name}")
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"[DIAGNOSTIC] Successfully completed {func_name} in {elapsed:.4f}s")
                return result
            except Exception as e:
                logger.error(f"[DIAGNOSTIC] Error in {func_name}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator

def run_diagnostics():
    """Run comprehensive diagnostics on the Think Tank mode"""
    results = {
        "test_results": {},
        "errors": [],
        "suggestions": []
    }

    # Step 1: Test importing the necessary modules
    test_imports(results)
    
    # If imports failed, we can't proceed
    if results["errors"] and any("import" in error for error in results["errors"]):
        logger.error("Critical import errors detected, cannot proceed with further tests")
        write_results(results)
        return results

    # Step 2: Test the model registry
    test_model_registry(results)
    
    # Step 3: Test query analysis functions
    test_query_analysis(results)
    
    # Step 4: Test model processors
    test_model_processors(results)
    
    # Step 5: Test response evaluation
    test_response_evaluation(results)
    
    # Step 6: Test end-to-end processing
    test_end_to_end(results)

    # Write results to file
    write_results(results)
    
    return results

@diagnostic_wrapper("import_tests")
def test_imports(results):
    """Test importing the necessary modules"""
    try:
        # Import with minimal dependencies first
        from web.multi_model_processor_minimal import (
            route_request, 
            get_query_tags,
            calculate_query_complexity,
            classify_query_type
        )
        results["test_results"]["basic_imports"] = "SUCCESS"
        logger.info("Successfully imported basic functions from minimal processor")
    except ImportError as e:
        results["errors"].append(f"Failed to import basic functions: {str(e)}")
        results["test_results"]["basic_imports"] = "FAILURE"
        logger.error(f"Failed to import basic functions: {str(e)}")
    
    try:
        # Try to import from the actual processor
        from web.multi_model_processor import (
            route_request,
            get_query_tags,
            calculate_query_complexity,
            classify_query_type,
            simulated_gpt4_processor,
            simulated_claude3_processor,
            simulated_gemini_processor
        )
        results["test_results"]["processor_imports"] = "SUCCESS"
        logger.info("Successfully imported all functions from multi_model_processor")
    except ImportError as e:
        results["errors"].append(f"Failed to import all functions: {str(e)}")
        results["test_results"]["processor_imports"] = "FAILURE"
        logger.error(f"Failed to import all functions: {str(e)}")

@diagnostic_wrapper("model_registry_tests")
def test_model_registry(results):
    """Test the model registry functionality"""
    try:
        from web.model_registry import get_registry, list_models, get_model
        
        # Test basic registry operations
        registry = get_registry()
        models = list_models()
        
        logger.info(f"Available models: {models}")
        results["test_results"]["model_registry"] = "SUCCESS"
        results["test_results"]["available_models"] = models
        
        # Check if we have enough models for Think Tank mode
        if len(models) < 2:
            results["errors"].append("Insufficient models registered for effective Think Tank mode")
            results["suggestions"].append("Register at least 3 different models for Think Tank mode to function properly")
    
    except Exception as e:
        results["errors"].append(f"Model registry error: {str(e)}")
        results["test_results"]["model_registry"] = "FAILURE"
        logger.error(f"Model registry error: {str(e)}")

@diagnostic_wrapper("query_analysis_tests")
def test_query_analysis(results):
    """Test query analysis functions"""
    try:
        from web.multi_model_processor import get_query_tags, calculate_query_complexity, classify_query_type
        
        # Test queries
        test_queries = [
            "What is the capital of France?",
            "Write a poem about artificial intelligence",
            "Help me debug this Python code: for i in range(10): print(i]",
            "Compare and contrast solar and wind energy"
        ]
        
        query_results = []
        
        for query in test_queries:
            tags = get_query_tags(query)
            complexity = calculate_query_complexity(query)
            query_type = classify_query_type(query)
            
            query_results.append({
                "query": query,
                "tags": tags,
                "complexity": complexity,
                "query_type": query_type
            })
            
            logger.info(f"Query: '{query}' -> Type: {query_type}, Complexity: {complexity}, Tags: {tags}")
        
        results["test_results"]["query_analysis"] = "SUCCESS"
        results["test_results"]["query_samples"] = query_results
    
    except Exception as e:
        results["errors"].append(f"Query analysis error: {str(e)}")
        results["test_results"]["query_analysis"] = "FAILURE"
        logger.error(f"Query analysis error: {str(e)}")

@diagnostic_wrapper("model_processor_tests")
def test_model_processors(results):
    """Test model processors"""
    try:
        from web.multi_model_processor import (
            simulated_gpt4_processor,
            simulated_claude3_processor, 
            simulated_gemini_processor,
            simulated_mistral7b_processor,
            simulated_gpt4all_processor
        )
        
        test_query = "What is artificial intelligence?"
        
        processor_results = {}
        
        # Test each processor
        processor_results["gpt4"] = simulated_gpt4_processor(test_query)
        processor_results["claude3"] = simulated_claude3_processor(test_query)
        processor_results["gemini"] = simulated_gemini_processor(test_query)
        processor_results["mistral7b"] = simulated_mistral7b_processor(test_query)
        processor_results["gpt4all"] = simulated_gpt4all_processor(test_query)
        
        # Check if we got valid responses
        valid_responses = all(isinstance(resp, str) and len(resp) > 0 for resp in processor_results.values())
        
        if valid_responses:
            results["test_results"]["model_processors"] = "SUCCESS"
            logger.info("All model processors returned valid responses")
        else:
            results["test_results"]["model_processors"] = "PARTIAL"
            invalid_models = [model for model, resp in processor_results.items() 
                             if not (isinstance(resp, str) and len(resp) > 0)]
            logger.warning(f"Some model processors returned invalid responses: {invalid_models}")
            results["errors"].append(f"Invalid responses from models: {invalid_models}")
        
        results["test_results"]["processor_responses"] = processor_results
    
    except Exception as e:
        results["errors"].append(f"Model processor error: {str(e)}")
        results["test_results"]["model_processors"] = "FAILURE"
        logger.error(f"Model processor error: {str(e)}")

@diagnostic_wrapper("response_evaluation_tests")
def test_response_evaluation(results):
    """Test response evaluation"""
    try:
        from web.multi_model_processor import evaluate_response_quality
        
        # Mock responses
        responses = {
            "gpt4": "Artificial intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans.",
            "claude3": "AI is the field of computer science dedicated to creating systems capable of performing tasks that typically require human intelligence.",
            "gemini": "Artificial intelligence is the development of computer systems able to perform tasks normally requiring human intelligence."
        }
        
        evaluation_results = {}
        
        # Evaluate each response
        for model, response in responses.items():
            quality_score = evaluate_response_quality(response, "What is artificial intelligence?")
            evaluation_results[model] = quality_score
            logger.info(f"Quality score for {model}: {quality_score}")
        
        results["test_results"]["response_evaluation"] = "SUCCESS"
        results["test_results"]["evaluation_samples"] = evaluation_results
    
    except Exception as e:
        results["errors"].append(f"Response evaluation error: {str(e)}")
        results["test_results"]["response_evaluation"] = "FAILURE"
        logger.error(f"Response evaluation error: {str(e)}")

@diagnostic_wrapper("end_to_end_tests")
def test_end_to_end(results):
    """Test end-to-end processing with the Think Tank mode"""
    try:
        from web.think_tank_processor import process_with_think_tank
        
        test_queries = [
            "What is the capital of France?",
            "Write a poem about artificial intelligence",
            "Explain quantum computing in simple terms"
        ]
        
        e2e_results = []
        
        for query in test_queries:
            try:
                logger.info(f"Testing Think Tank with query: '{query}'")
                start_time = time.time()
                response = process_with_think_tank(query)
                elapsed = time.time() - start_time
                
                e2e_results.append({
                    "query": query,
                    "response": response,
                    "processing_time": elapsed,
                    "status": "SUCCESS" if response else "FAILURE"
                })
                
                if response:
                    logger.info(f"Think Tank responded in {elapsed:.4f}s")
                else:
                    logger.warning(f"Think Tank returned empty response after {elapsed:.4f}s")
            
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                e2e_results.append({
                    "query": query,
                    "error": str(e),
                    "status": "ERROR"
                })
                results["errors"].append(f"End-to-end processing error for query '{query}': {str(e)}")
        
        # Check overall results
        success_count = sum(1 for r in e2e_results if r["status"] == "SUCCESS")
        
        if success_count == len(test_queries):
            results["test_results"]["end_to_end"] = "SUCCESS"
        elif success_count > 0:
            results["test_results"]["end_to_end"] = "PARTIAL"
        else:
            results["test_results"]["end_to_end"] = "FAILURE"
        
        results["test_results"]["e2e_samples"] = e2e_results
    
    except Exception as e:
        results["errors"].append(f"End-to-end test error: {str(e)}")
        results["test_results"]["end_to_end"] = "FAILURE"
        logger.error(f"End-to-end test error: {str(e)}")

def write_results(results):
    """Write diagnostic results to a file"""
    output_file = "think_tank_diagnostics_results.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Diagnostic results written to {output_file}")

if __name__ == "__main__":
    logger.info("Starting Think Tank diagnostics...")
    try:
        results = run_diagnostics()
        
        # Print summary
        print("\n" + "="*80)
        print("THINK TANK DIAGNOSTICS SUMMARY")
        print("="*80)
        
        for test, result in results["test_results"].items():
            if isinstance(result, str):
                print(f"{test.replace('_', ' ').upper()}: {result}")
        
        if results["errors"]:
            print("\nERRORS DETECTED:")
            for i, error in enumerate(results["errors"], 1):
                print(f"{i}. {error}")
        
        if results["suggestions"]:
            print("\nSUGGESTIONS:")
            for i, suggestion in enumerate(results["suggestions"], 1):
                print(f"{i}. {suggestion}")
        
        print("\nDetailed results available in 'think_tank_diagnostics_results.json'")
        print("="*80)
    
    except Exception as e:
        logger.error(f"Diagnostic script error: {str(e)}", exc_info=True)
        print(f"Error running diagnostics: {str(e)}")
