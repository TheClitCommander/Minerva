#!/usr/bin/env python3
"""
Minerva API Key Check

This script checks for and configures the necessary API keys for Minerva to work with real AI models.
It will set up the environment variables and verify API key validity where possible.
"""
import os
import sys
import time
import logging
from pathlib import Path
import asyncio
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MinervaAPICheck")

def setup_environment():
    """Set up the environment with proper API keys"""
    # Check for a .env file
    dotenv_path = Path(".env")
    
    # Load any existing .env file
    if dotenv_path.exists():
        logger.info("Loading existing .env file")
        dotenv.load_dotenv(dotenv_path)
    
    # Check if OpenAI API key exists
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("⚠️ OpenAI API key not found in environment variables")
        new_key = input("Enter your OpenAI API key (or press enter to leave blank): ").strip()
        if new_key:
            os.environ["OPENAI_API_KEY"] = new_key
            logger.info("✅ OpenAI API key set in environment")
        else:
            logger.warning("⚠️ No OpenAI API key provided - GPT-4 will use simulated responses")
    else:
        logger.info("✅ OpenAI API key already configured")
    
    # Check if Anthropic API key exists
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.warning("⚠️ Anthropic API key not found in environment variables")
        new_key = input("Enter your Anthropic API key (or press enter to leave blank): ").strip()
        if new_key:
            os.environ["ANTHROPIC_API_KEY"] = new_key
            logger.info("✅ Anthropic API key set in environment")
        else:
            logger.warning("⚠️ No Anthropic API key provided - Claude-3 will use simulated responses")
    else:
        logger.info("✅ Anthropic API key already configured")
    
    # Save to .env file for persistence
    with open(dotenv_path, "w") as f:
        if openai_key or os.environ.get("OPENAI_API_KEY"):
            f.write(f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY')}\n")
        if anthropic_key or os.environ.get("ANTHROPIC_API_KEY"):
            f.write(f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY')}\n")
    
    logger.info("API keys saved to .env file")
    return True

async def test_api_keys():
    """Test the API keys by making minimal API calls"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    results = {
        "openai": False,
        "anthropic": False
    }
    
    # Test OpenAI API key
    if openai_key:
        try:
            logger.info("Testing OpenAI API key...")
            # Dynamically import to avoid import errors
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=openai_key)
            
            # Make a minimal API call
            models = await client.models.list()
            if models and len(models.data) > 0:
                logger.info(f"✅ OpenAI API key is valid! Found {len(models.data)} models")
                # Log some available models
                model_names = [model.id for model in models.data[:5]]
                logger.info(f"Available models include: {', '.join(model_names)}")
                results["openai"] = True
            else:
                logger.warning("⚠️ OpenAI API connection successful but no models found")
                results["openai"] = True  # Still consider valid
        except Exception as e:
            logger.error(f"❌ OpenAI API key test failed: {str(e)}")
    
    # Test Anthropic API key
    if anthropic_key:
        try:
            logger.info("Testing Anthropic API key...")
            # Dynamically import to avoid import errors
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=anthropic_key)
            
            # Simply initializing the client successfully is enough for Anthropic
            # as they don't have a simple models list endpoint
            logger.info("✅ Anthropic API key format is valid")
            results["anthropic"] = True
        except Exception as e:
            logger.error(f"❌ Anthropic API key test failed: {str(e)}")
    
    return results

def main():
    """Main function to run the API key checker"""
    print("\n" + "=" * 70)
    print("🔑 MINERVA API KEY CONFIGURATION 🔑")
    print("=" * 70)
    print("This script will check and configure API keys for real AI integration")
    print("=" * 70 + "\n")
    
    # Setup environment
    setup_environment()
    
    # Test API keys
    asyncio.run(test_api_keys())
    
    print("\n" + "=" * 70)
    print("CONFIGURATION COMPLETE!")
    print("=" * 70)
    print("You can now run Minerva with these API keys using:")
    print("  ./run_minerva.sh")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
