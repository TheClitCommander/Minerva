#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Minerva prompt formatting.
This script tests the enhanced prompt formatter with different types of queries.
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
    from web.multi_model_processor import format_enhanced_prompt, validate_response, get_query_tags, route_request
    logger.info("Successfully imported Minerva modules")
except ImportError as e:
    logger.error(f"Error importing Minerva modules: {e}")
    sys.exit(1)

def test_prompt_formats():
    """Test prompt formatting for different message types."""
    logger.info("Testing prompt formatting...")
    
    test_messages = [
        "Hello",
        "Hi there, how are you?",
        "What is the capital of France?",
        "Can you explain how machine learning works?",
        "Write a short poem about the ocean.",
        "How do I fix a Python TypeError?",
        "Tell me about the history of the Roman Empire in great detail."
    ]
    
    for message in test_messages:
        logger.info(f"\n=== Testing message: '{message}' ===")
        
        # Get query tags
        tags = get_query_tags(message)
        logger.info(f"Query tags: {tags}")
        
        # Get routing decision
        routing = route_request(message)
        logger.info(f"Routing complexity: {routing['complexity']:.2f}")
        logger.info(f"Selected models: {routing['selected_models'][:2]}")
        
        # Get prompt formats for different model types
        basic_prompt = format_enhanced_prompt(message, model_type="basic")
        advanced_prompt = format_enhanced_prompt(message, model_type="zephyr")
        
        logger.info("\n--- Basic Model Prompt ---")
        logger.info(basic_prompt)
        
        logger.info("\n--- Advanced Model Prompt ---")
        logger.info(advanced_prompt)
        
        logger.info("=" * 50)

def main():
    """Run the test suite."""
    logger.info("Starting Minerva prompt format tests...")
    
    # Test prompt formats
    test_prompt_formats()
    
    logger.info("Test complete!")

if __name__ == "__main__":
    main()
