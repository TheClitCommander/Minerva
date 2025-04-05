#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Minerva response quality.
This script tests different types of queries to ensure response quality is consistent.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary functions
try:
    from web.app import process_huggingface_only
    from web.multi_model_processor import format_enhanced_prompt, validate_response
    logger.info("Successfully imported Minerva modules")
except ImportError as e:
    logger.error(f"Error importing Minerva modules: {e}")
    sys.exit(1)

def test_greeting_responses():
    """Test simple greeting responses."""
    logger.info("Testing greeting responses...")
    
    greeting_messages = [
        "Hello",
        "Hi there",
        "Hey Minerva",
        "Good morning"
    ]
    
    results = {}
    for message in greeting_messages:
        logger.info(f"Testing greeting: '{message}'")
        try:
            response = process_huggingface_only(message)
            is_valid, validation_results = validate_response(response, message)
            
            results[message] = {
                "response": response,
                "is_valid": is_valid,
                "validation_results": validation_results
            }
            
            logger.info(f"Response: '{response[:50]}...' Valid: {is_valid}")
        except Exception as e:
            logger.error(f"Error processing '{message}': {e}")
            results[message] = {"error": str(e)}
    
    return results

def test_factual_queries():
    """Test simple factual queries."""
    logger.info("Testing factual queries...")
    
    factual_messages = [
        "What is the capital of France?",
        "Tell me about the solar system",
        "How many planets are there?",
        "What's the tallest mountain?"
    ]
    
    results = {}
    for message in factual_messages:
        logger.info(f"Testing factual query: '{message}'")
        try:
            response = process_huggingface_only(message)
            is_valid, validation_results = validate_response(response, message)
            
            results[message] = {
                "response": response,
                "is_valid": is_valid,
                "validation_results": validation_results
            }
            
            logger.info(f"Response: '{response[:50]}...' Valid: {is_valid}")
        except Exception as e:
            logger.error(f"Error processing '{message}': {e}")
            results[message] = {"error": str(e)}
    
    return results

def main():
    """Run the test suite."""
    logger.info("Starting Minerva response quality tests...")
    
    # Test greeting responses
    greeting_results = test_greeting_responses()
    
    # Test factual queries
    factual_results = test_factual_queries()
    
    # Report results
    logger.info("\n\n===== TEST RESULTS =====")
    
    valid_greetings = sum(1 for result in greeting_results.values() if isinstance(result, dict) and result.get("is_valid", False))
    logger.info(f"Greeting Responses: {valid_greetings}/{len(greeting_results)} valid")
    
    valid_factual = sum(1 for result in factual_results.values() if isinstance(result, dict) and result.get("is_valid", False))
    logger.info(f"Factual Responses: {valid_factual}/{len(factual_results)} valid")
    
    total_valid = valid_greetings + valid_factual
    total_tests = len(greeting_results) + len(factual_results)
    
    logger.info(f"Overall Success Rate: {total_valid}/{total_tests} ({(total_valid/total_tests)*100:.1f}%)")
    logger.info("Test complete!")

if __name__ == "__main__":
    main()
