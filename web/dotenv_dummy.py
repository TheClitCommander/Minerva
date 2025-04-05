#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dummy dotenv module to handle environment variables without requiring the python-dotenv package.
This file serves as a fallback implementation that mimics the basic functionality of dotenv.
"""

import os
import logging

logger = logging.getLogger('dotenv')

def load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False, **kwargs):
    """
    Load environment variables from .env file.
    This is a simplified version that doesn't actually load from a file
    but simply returns True to satisfy import requirements.
    """
    logger.info("Using dummy dotenv.load_dotenv() implementation")
    return True

def find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=False):
    """
    Search for a .env file in parent directories.
    This is a simplified version that doesn't actually search for a file
    but returns a placeholder path to satisfy import requirements.
    """
    logger.info("Using dummy dotenv.find_dotenv() implementation")
    return os.path.join(os.getcwd(), '.env')

def set_key(dotenv_path, key_to_set, value_to_set, quote_mode="always"):
    """
    Set a key in a .env file.
    This is a simplified version that doesn't actually set a key
    but returns True to satisfy import requirements.
    """
    logger.info(f"Using dummy dotenv.set_key() implementation (would set {key_to_set}={value_to_set})")
    return True

# Only log which environment variables are available, don't set placeholder values
api_keys = {
    'OPENAI_API_KEY': 'OpenAI',
    'ANTHROPIC_API_KEY': 'Anthropic',
    'MISTRAL_API_KEY': 'Mistral',
    'GOOGLE_API_KEY': 'Google',
    'COHERE_API_KEY': 'Cohere'
}

for key, provider in api_keys.items():
    if key in os.environ and os.environ[key]:
        logger.info(f"✅ {provider} API key is available")
    else:
        logger.warning(f"⚠️ {provider} API key is not available")

# Log that dummy module is being used
logger.warning("Using dummy dotenv module - set real API keys in environment variables for production use")
