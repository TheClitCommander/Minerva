#!/usr/bin/env python
# Debug script to identify OpenAI client initialization issues

import os
import sys
import logging
import inspect
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    logger.error("OpenAI API key not found in .env file")
    sys.exit(1)

try:
    # Import OpenAI
    import openai
    from openai import AsyncOpenAI
    
    # Print out the OpenAI module info
    logger.info(f"OpenAI SDK version: {openai.__version__}")
    logger.info(f"OpenAI module path: {openai.__file__}")
    
    # Inspect the AsyncOpenAI.__init__ method
    logger.info("\nInspecting AsyncOpenAI.__init__ method:")
    sig = inspect.signature(AsyncOpenAI.__init__)
    logger.info(f"Parameters: {sig}")
    
    # Try to create client directly
    logger.info("\nTrying to create client directly:")
    direct_client = AsyncOpenAI(api_key=api_key)
    logger.info("✅ Direct client creation successful")
    
    # Try to create client using our model_processors function
    logger.info("\nTrying to create client with model_processors create_openai_client function:")
    sys.path.insert(0, os.path.dirname(__file__))
    from web.model_processors import create_openai_client
    
    # Inspect the create_openai_client function
    logger.info("\nInspecting create_openai_client function:")
    sig = inspect.signature(create_openai_client)
    logger.info(f"Parameters: {sig}")
    
    # Create client through our function
    client = create_openai_client(api_key)
    logger.info("✅ Client creation through model_processors successful")
    
    logger.info("\nTest completed successfully!")
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
    
    # Get more detailed exception information
    import traceback
    logger.error("Detailed exception information:")
    logger.error(traceback.format_exc())
