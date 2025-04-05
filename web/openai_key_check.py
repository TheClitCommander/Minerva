"""
Enhanced script to test OpenAI API keys and update the model failure handler.

This script checks all available OpenAI API keys and updates the model failure handler
to ensure Minerva falls back to local models when OpenAI API payment issues are detected.
"""

import os
import sys
import logging
import openai
import time
import json
import re
from pathlib import Path
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("openai_key_check.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_openai_key(api_key, key_name=""):
    """Test if the OpenAI API key works by making a simple request"""
    if not key_name:
        key_name = f"{api_key[:5]}...{api_key[-4:]}"
        
    try:
        # Set the API key for this test
        client = OpenAI(api_key=api_key)
        
        # Make a simple request that shouldn't cost much
        logger.info(f"Testing OpenAI API key {key_name}...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test message to check API key validity."}],
            max_tokens=10
        )
        
        # If we get here, the key is working
        logger.info(f"✅ SUCCESS: API key {key_name} works! Response: {response.choices[0].message.content}")
        return True, "Key is working correctly", None
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ ERROR with key {key_name}: {error_msg}")
        
        # Check for payment-related errors with more detailed patterns
        payment_patterns = [
            r"billing", r"payment", r"credit", r"quota", r"limit", 
            r"exceed", r"insufficient", r"upgrade", r"account", r"paid",
            r"trial", r"expired", r"subscription", r"rate limit"
        ]
        
        # Common OpenAI error patterns
        openai_quota_patterns = [
            r"rate\s*limit",
            r"quota\s*exceed",
            r"insufficient\s*quota",
            r"billing\s*issues",
            r"maximum\s*monthly\s*spending",
            r"You exceeded your current quota",
            r"Your account is not active"
        ]
        
        # Check for payment issues
        is_payment_issue = False
        for pattern in payment_patterns:
            if re.search(pattern, error_msg, re.IGNORECASE):
                is_payment_issue = True
                break
                
        # Check for OpenAI quota issues specifically
        is_quota_issue = False
        for pattern in openai_quota_patterns:
            if re.search(pattern, error_msg, re.IGNORECASE):
                is_quota_issue = True
                break
        
        # Categorize the error
        if is_payment_issue or is_quota_issue:
            logger.warning(f"⚠️ PAYMENT ISSUE DETECTED with key {key_name}: {error_msg}")
            return False, "Payment or quota issue detected", error_msg
        elif "invalid" in error_msg.lower() and "api key" in error_msg.lower():
            logger.warning(f"⚠️ INVALID API KEY {key_name}: {error_msg}")
            return False, "Invalid API key format", error_msg
        elif "exceeded" in error_msg.lower() or "limit" in error_msg.lower():
            logger.warning(f"⚠️ RATE LIMIT EXCEEDED for key {key_name}: {error_msg}")
            return False, "Rate limit or quota exceeded", error_msg
        else:
            logger.warning(f"⚠️ UNKNOWN ERROR with key {key_name}: {error_msg}")
            return False, "Unknown error", error_msg

def update_model_failure_handler(all_keys_failing=False, payment_related=False, error_message=""):
    """Update the model failure handler to mark OpenAI as failing"""
    try:
        # First try to import with direct module path
        try:
            from model_failure_handler import get_failure_handler
            logger.info("Imported model_failure_handler directly")
        except ImportError:
            # Then try with web package prefix
            try:
                from web.model_failure_handler import get_failure_handler
                logger.info("Imported web.model_failure_handler")
            except ImportError:
                logger.error("Could not import model_failure_handler module")
                return False
                
        # Get the failure handler instance
        failure_handler = get_failure_handler()
        
        if all_keys_failing:
            # Mark OpenAI as failing with appropriate error message
            reason = "All OpenAI API keys failed due to payment issues" if payment_related else "All OpenAI API keys failed"
            if error_message:
                reason += f": {error_message}"
                
            logger.warning(f"⚠️ {reason}")
            failure_handler.force_mark_api_failing("openai", reason, payment_related)
            
            # Log the update
            logger.info("✅ Updated model failure handler to mark OpenAI as failing")
            return True
        else:
            logger.info("📊 Not all keys are failing, not updating failure handler")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update model failure handler: {str(e)}")
        return False
            
def test_all_openai_keys():
    """Test all OpenAI API keys from environment variables"""
    main_key = os.environ.get("OPENAI_API_KEY", "")
    backup_key = os.environ.get("OPENAI_API_KEY_BACKUP", "")
    
    # Track results
    results = []
    success_count = 0
    payment_issues = 0
    last_error = ""
    
    # Test main key if available
    if main_key:
        logger.info("======= Testing Main OpenAI API Key =======")
        success, message, error = check_openai_key(main_key, "Main")
        results.append({"key": "Main", "success": success, "message": message})
        
        if success:
            success_count += 1
        elif "payment" in message.lower() or "quota" in message.lower():
            payment_issues += 1
            last_error = error
    else:
        logger.warning("Main OpenAI API key not found in environment variables")
        results.append({"key": "Main", "success": False, "message": "Key not found"})
    
    # Test backup key if available
    if backup_key:
        logger.info("======= Testing Backup OpenAI API Key =======")
        success, message, error = check_openai_key(backup_key, "Backup")
        results.append({"key": "Backup", "success": success, "message": message})
        
        if success:
            success_count += 1
        elif "payment" in message.lower() or "quota" in message.lower():
            payment_issues += 1
            last_error = error
    else:
        logger.warning("Backup OpenAI API key not found in environment variables")
        results.append({"key": "Backup", "success": False, "message": "Key not found"})
    
    # Generate summary
    log_section_header("SUMMARY")
    for result in results:
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        logger.info(f"{status}: {result['key']} - {result['message']}")
    
    # Update model failure handler if all keys failed due to payment issues
    keys_tested = len([r for r in results if r["key"] in ["Main", "Backup"]])
    if keys_tested > 0 and success_count == 0:
        log_section_header("API FAILURE STATUS UPDATE")
        
        # Check if payment issues were the cause
        payment_related = payment_issues > 0
        update_model_failure_handler(True, payment_related, last_error)
        
        if payment_related:
            logger.warning("⚠️ ALL KEYS HAVE PAYMENT ISSUES - Minerva will prioritize local models")
        else:
            logger.warning("⚠️ ALL KEYS FAILED - Minerva will prioritize local models")
    
    return success_count > 0

def log_section_header(title):
    """Print a section header to the log"""
    logger.info("="*50)
    logger.info(f" {title} ".center(50, "="))
    logger.info("="*50)

if __name__ == "__main__":
    log_section_header("OpenAI API KEY CHECKER")
    
    # Check if specific keys were provided as command line arguments
    if len(sys.argv) > 1:
        logger.info("Testing keys provided via command line...")
        
        for i, key in enumerate(sys.argv[1:], 1):
            key_name = f"Command line key #{i}"
            logger.info(f"Testing {key_name}: {key[:5]}...{key[-4:]}")
            success, message, _ = check_openai_key(key, key_name)
            
            if success:
                logger.info(f"✅ {key_name} WORKS! You can use this key in your application.")
                # Save the working key to a file for easy reference
                with open("working_openai_key.txt", "w") as f:
                    f.write(key)
                break
            else:
                logger.info(f"❌ {key_name} FAILED: {message}")
    
    # Otherwise test keys from environment variables
    else:
        logger.info("No keys provided via command line. Testing keys from environment variables...")
        any_working = test_all_openai_keys()
        
        if any_working:
            logger.info("✅ At least one key is working! Minerva can use OpenAI API.")
        else:
            logger.warning("❌ No working keys found! Minerva will fallback to local models.")
    
    logger.info("Testing complete!")
