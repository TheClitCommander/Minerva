#!/usr/bin/env python3
"""
API Status Verification Utility

This script verifies the status of all API models and explicitly marks failing APIs 
in the model failure handler. It should be run regularly to ensure the system correctly
prioritizes working models.
"""

import os
import logging
import time
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_verification.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_paths():
    """Make sure the script can import from the web directory"""
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # If the script is in the web directory, add its parent to the path
    if current_dir.name == "web":
        parent_dir = current_dir.parent
        sys.path.insert(0, str(parent_dir))
    
    # If we're in the main Minerva directory, add the current directory
    else:
        sys.path.insert(0, str(current_dir))
        
    # Also explicitly add the web directory to handle both cases
    web_dir = current_dir / "web" if current_dir.name != "web" else current_dir
    if web_dir.exists():
        sys.path.insert(0, str(web_dir))
        
    logger.info(f"Python path: {sys.path}")

def verify_openai_status():
    """Check OpenAI API status and mark as failing if needed"""
    logger.info("Verifying OpenAI API status...")
    
    try:
        # Import the OpenAI key checker
        from openai_key_check import test_all_openai_keys
        
        # Test all OpenAI keys
        success = test_all_openai_keys()
        return success
        
    except Exception as e:
        logger.error(f"Error verifying OpenAI API status: {e}", exc_info=True)
        return False

def verify_local_models():
    """Verify that local models are available and working"""
    logger.info("Verifying local model availability...")
    
    try:
        # Import the model failure handler
        from model_failure_handler import get_failure_handler
        
        # Check if torch and transformers are available
        try:
            import torch
            import transformers
            logger.info("PyTorch and Transformers are available")
            
            # Check if GPU is available
            if torch.cuda.is_available():
                logger.info(f"GPU is available: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("Running on CPU mode")
                
            return True
            
        except ImportError as e:
            logger.error(f"Missing required packages for local models: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying local model availability: {e}", exc_info=True)
        return False

def update_model_router_config():
    """Update the model router configuration to prioritize local models if OpenAI is failing"""
    logger.info("Updating model router configuration...")
    
    try:
        # Import the model failure handler
        from model_failure_handler import get_failure_handler
        
        # Get the failure handler instance
        failure_handler = get_failure_handler()
        
        # Check if OpenAI is failing
        openai_failing = failure_handler.is_api_failing("openai")
        
        if openai_failing:
            logger.warning("OpenAI API is failing - model router will prioritize local models")
            
            # Set an environment variable to prioritize local models
            os.environ["MINERVA_PRIORITIZE_LOCAL"] = "1"
            
            # Log the status for analysis
            payment_related = failure_handler.api_failure_status.get("openai", {}).get("payment_related", False)
            if payment_related:
                logger.warning("OpenAI failure appears to be payment-related")
            
            # Get the failure reason for logging
            reason = failure_handler.api_failure_status.get("openai", {}).get("last_failure_reason", "Unknown reason")
            logger.info(f"Failure reason: {reason}")
        else:
            logger.info("OpenAI API appears to be working")
            os.environ.pop("MINERVA_PRIORITIZE_LOCAL", None)
            
        return True
        
    except Exception as e:
        logger.error(f"Error updating model router configuration: {e}", exc_info=True)
        return False

def run_verification():
    """Run all verification steps"""
    logger.info("=" * 50)
    logger.info("Starting API status verification")
    logger.info("=" * 50)
    
    # Setup paths for imports
    setup_paths()
    
    # Verify OpenAI status
    openai_working = verify_openai_status()
    
    # Verify local models
    local_working = verify_local_models()
    
    # Update model router configuration
    update_model_router_config()
    
    # Print summary
    logger.info("=" * 50)
    logger.info("API Status Verification Summary")
    logger.info("=" * 50)
    logger.info(f"OpenAI API Status: {'WORKING' if openai_working else 'FAILING'}")
    logger.info(f"Local Models Status: {'AVAILABLE' if local_working else 'UNAVAILABLE'}")
    
    # Final recommendation
    if not openai_working and local_working:
        logger.info("RECOMMENDATION: Use local-only API endpoint for processing")
    elif openai_working:
        logger.info("RECOMMENDATION: Continue using regular API endpoints")
    else:
        logger.error("CRITICAL: Both OpenAI API and local models appear to be unavailable")
        
    logger.info("=" * 50)
    logger.info("Verification complete")
    
    return openai_working, local_working

if __name__ == "__main__":
    run_verification()
