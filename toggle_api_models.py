#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script to toggle API models on or off for Think Tank mode.

This script provides a simple command-line interface to enable or disable
API-based models in the Think Tank system, avoiding API costs during development.
"""

import os
import sys
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_toggle")

# Import the free model configuration
try:
    from web.free_model_config import (
        toggle_api_models,
        get_available_models,
        ENABLE_API_MODELS,
        FREE_MODELS,
        API_MODELS
    )
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the Minerva project root.")
    sys.exit(1)

def main():
    """Process command line arguments and toggle API models."""
    parser = argparse.ArgumentParser(
        description="Toggle API models on/off for Think Tank mode",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Create a mutually exclusive group for enable/disable/status
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enable", 
        action="store_true", 
        help="Enable API models"
    )
    group.add_argument(
        "--disable", 
        action="store_true", 
        help="Disable API models (use free models only)"
    )
    group.add_argument(
        "--status", 
        action="store_true", 
        help="Show current API model status"
    )
    
    # Add an argument to test the configuration with a query
    parser.add_argument(
        "--test", 
        type=str, 
        help="Test the configuration with a sample query"
    )
    
    args = parser.parse_args()
    
    # Process the command
    if args.status:
        status = "enabled" if ENABLE_API_MODELS else "disabled"
        logger.info(f"API models are currently {status}")
        logger.info(f"Available models: {get_available_models()}")
        logger.info(f"Free models: {FREE_MODELS}")
        logger.info(f"API models: {API_MODELS}")
    
    elif args.enable:
        toggle_api_models(True)
        logger.info("API models have been ENABLED")
        logger.info(f"Available models: {get_available_models()}")
    
    elif args.disable:
        toggle_api_models(False)
        logger.info("API models have been DISABLED")
        logger.info(f"Available models: {get_available_models()}")
    
    # Test the configuration if requested
    if args.test:
        try:
            from web.think_tank_processor import process_with_think_tank
            
            logger.info(f"Testing Think Tank with query: '{args.test}'")
            response = process_with_think_tank(args.test)
            logger.info(f"Response: {response}")
        except Exception as e:
            logger.error(f"Error testing Think Tank: {e}")

if __name__ == "__main__":
    main()
