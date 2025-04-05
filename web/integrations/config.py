"""
AI Model Integration Configuration

This module provides a centralized location for AI service configuration and API keys.
"""

import os
import logging
import pathlib

# Set up logging
logger = logging.getLogger(__name__)

# Try to load environment variables from .env file if dotenv is available
try:
    from dotenv import load_dotenv
    env_path = pathlib.Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / '.env'
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.warning(f"No .env file found at {env_path}")
except ImportError:
    logger.warning("dotenv package not found, continuing without loading .env file")

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-yourkeyhere")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")  # Optional

# Anthropic API configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "sk-ant-yourkeyhere") or os.getenv("CLAUDE_API_KEY")

# Mistral API configuration
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "yourkeyhere")

# Google AI (Gemini) API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "yourkeyhere")

# Cohere API configuration 
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "yourkeyhere")

# For testing purposes, uncomment and replace with your actual API keys
# OPENAI_API_KEY = "your-actual-openai-key"
# ANTHROPIC_API_KEY = "your-actual-anthropic-key"
# MISTRAL_API_KEY = "your-actual-mistral-key"
# GOOGLE_API_KEY = "your-actual-google-key"
# COHERE_API_KEY = "your-actual-cohere-key"

# Configuration validation
def validate_api_keys():
    """Validate which API keys are available and log their status"""
    available_models = []
    
    if OPENAI_API_KEY:
        available_models.extend(['gpt-4', 'gpt-4o', 'gpt-4o-mini'])
        logger.info("✅ OpenAI API key is available")
    else:
        logger.warning("⚠️ OpenAI API key is not available - OpenAI models will be unavailable")
    
    if ANTHROPIC_API_KEY:
        available_models.extend(['claude-3', 'claude-3-opus', 'claude-3-haiku'])
        logger.info("✅ Anthropic API key is available")
    else:
        logger.warning("⚠️ Anthropic API key is not available - Claude models will be unavailable")
    
    if MISTRAL_API_KEY:
        available_models.extend(['mistral', 'mistral-large', 'mistral-small'])
        logger.info("✅ Mistral API key is available")
    else:
        logger.warning("⚠️ Mistral API key is not available - Mistral models will be unavailable")
    
    if GOOGLE_API_KEY:
        available_models.append('gemini')
        logger.info("✅ Google API key is available")
    else:
        logger.warning("⚠️ Google API key is not available - Gemini models will be unavailable")
    
    if COHERE_API_KEY:
        available_models.append('cohere')
        logger.info("✅ Cohere API key is available")
    else:
        logger.warning("⚠️ Cohere API key is not available - Cohere models will be unavailable")
    
    return available_models

# Export available models based on API keys
AVAILABLE_EXTERNAL_MODELS = validate_api_keys()
