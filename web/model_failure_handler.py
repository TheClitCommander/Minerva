"""
Model Failure Handler - Helps Minerva adapt when API models fail

This module provides utilities to detect API failures (especially payment-related issues)
and helps restructure model selection decisions to avoid repeatedly trying failing APIs.
"""

import os
import logging
import json
import time
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to store API failure status
FAILURE_CACHE_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "api_failure_status.json"

class ModelFailureHandler:
    """Handles API model failures and helps adapt model selection strategy"""
    
    def __init__(self):
        """Initialize the failure handler with cached failure statuses"""
        self.api_failure_status = self._load_failure_status()
        self._check_api_keys()
    
    def _load_failure_status(self) -> Dict[str, Any]:
        """Load cached API failure status if it exists"""
        default_status = {
            "openai": {
                "failing": False,
                "last_failure_reason": None,
                "failure_count": 0,
                "last_failure_time": None
            },
            "anthropic": {
                "failing": False,
                "last_failure_reason": None,
                "failure_count": 0,
                "last_failure_time": None
            },
            "mistral": {
                "failing": False,
                "last_failure_reason": None,
                "failure_count": 0,
                "last_failure_time": None
            }
        }
        
        try:
            if FAILURE_CACHE_PATH.exists():
                with open(FAILURE_CACHE_PATH, 'r') as f:
                    return json.load(f)
            return default_status
        except Exception as e:
            logger.warning(f"Error loading API failure status: {e}")
            return default_status
    
    def _save_failure_status(self):
        """Save current API failure status to cache file"""
        try:
            with open(FAILURE_CACHE_PATH, 'w') as f:
                json.dump(self.api_failure_status, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving API failure status: {e}")
    
    def _check_api_keys(self):
        """Check if API keys are available and valid"""
        # Check OpenAI API key
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key or len(openai_key) < 20:  # Basic validation
            logger.warning("OpenAI API key not found or appears invalid")
            self.api_failure_status["openai"]["failing"] = True
            self.api_failure_status["openai"]["last_failure_reason"] = "API key missing or invalid"
        
        # Check Anthropic/Claude API key
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key or len(anthropic_key) < 20:  # Basic validation
            logger.warning("Anthropic API key not found or appears invalid")
            self.api_failure_status["anthropic"]["failing"] = True
            self.api_failure_status["anthropic"]["last_failure_reason"] = "API key missing or invalid"
        
        # Check Mistral API key
        mistral_key = os.environ.get("MISTRAL_API_KEY")
        if not mistral_key or len(mistral_key) < 20:  # Basic validation
            logger.warning("Mistral API key not found or appears invalid")
            self.api_failure_status["mistral"]["failing"] = True
            self.api_failure_status["mistral"]["last_failure_reason"] = "API key missing or invalid"
        
        # Save updated status
        self._save_failure_status()
    
    def register_api_failure(self, api_name: str, error_message: str):
        """Register an API failure and update the failure status"""
        
        if api_name not in self.api_failure_status:
            self.api_failure_status[api_name] = {
                "failing": False,
                "last_failure_reason": None,
                "failure_count": 0,
                "last_failure_time": None,
                "payment_related": False
            }
        
        # Check if this is a payment-related issue
        payment_related = self._is_payment_related_error(error_message)
        
        self.api_failure_status[api_name]["failing"] = True
        self.api_failure_status[api_name]["last_failure_reason"] = error_message
        self.api_failure_status[api_name]["failure_count"] += 1
        self.api_failure_status[api_name]["last_failure_time"] = time.time()
        
        # Mark payment issues specifically
        if payment_related:
            self.api_failure_status[api_name]["payment_related"] = True
            logger.error(f"PAYMENT ISSUE DETECTED for {api_name}: {error_message}")
        
        # For OpenAI specifically, check for quota/billing issues
        if api_name == "openai" and self._is_openai_quota_error(error_message):
            self.api_failure_status[api_name]["payment_related"] = True
            logger.error(f"OPENAI QUOTA ISSUE DETECTED: {error_message}")
        
        # Save updated status
        self._save_failure_status()
        
        logger.warning(f"Registered API failure for {api_name}: {error_message}")
    
    def _is_payment_related_error(self, error_message: str) -> bool:
        """Check if an error is payment-related"""
        payment_keywords = [
            "billing", "payment", "credit", "quota", "limit", 
            "exceed", "insufficient", "upgrade", "account", "paid",
            "trial", "expired", "subscription", "rate limit"
        ]
        
        return any(keyword.lower() in error_message.lower() for keyword in payment_keywords)
    
    def _is_openai_quota_error(self, error_message: str) -> bool:
        """Check specifically for OpenAI quota errors"""
        openai_quota_patterns = [
            r"rate\s*limit",
            r"quota\s*exceed",
            r"insufficient\s*quota",
            r"billing\s*issues",
            r"maximum\s*monthly\s*spending",
            r"You exceeded your current quota",
            r"Your account is not active"
        ]
        
        return any(re.search(pattern, error_message, re.IGNORECASE) for pattern in openai_quota_patterns)
    
    def is_api_failing(self, api_name: str) -> bool:
        """Check if an API is currently failing"""
        if api_name not in self.api_failure_status:
            return False
        return self.api_failure_status[api_name]["failing"]
    
    def get_alternative_models(self, requested_models: List[str], 
                               available_models: List[str]) -> List[str]:
        """Get alternative models when requested models are failing"""
        # Define model categories
        openai_models = ["gpt-4", "gpt-4o", "gpt-3.5-turbo", "gpt4", "gpt-4-turbo", "gpt-4-0314", "gpt-4-32k"]
        anthropic_models = ["claude-3", "claude-3-opus", "claude-3-sonnet", "claude-instant", "claude-2"]
        mistral_models = ["mistral", "mistral-large", "mistral-medium", "mistral-small", "mistral-tiny"]
        local_models = ["huggingface", "llama", "falcon", "mpt", "gpt4all", "zephyr", "starling"]
        
        original_models = requested_models.copy()
        filtered_models = requested_models.copy()
        
        # Check if OpenAI is failing
        if self.is_api_failing("openai"):
            logger.warning("OpenAI API is failing - removing OpenAI models from selection")
            # Replace OpenAI models with alternatives
            filtered_models = [m for m in filtered_models if not any(oai in m.lower() for oai in openai_models)]
        
        # Check if Anthropic is failing
        if self.is_api_failing("anthropic"):
            logger.warning("Anthropic API is failing - removing Anthropic models from selection")
            # Replace Anthropic models with alternatives
            filtered_models = [m for m in filtered_models if not any(claude in m.lower() for claude in anthropic_models)]
        
        # Check if Mistral is failing
        if self.is_api_failing("mistral"):
            logger.warning("Mistral API is failing - removing Mistral models from selection")
            # Replace Mistral models with alternatives
            filtered_models = [m for m in filtered_models if not any(mistral in m.lower() for mistral in mistral_models)]
        
        # If our filtering removed all requested models OR if OpenAI has payment issues,
        # explicitly add local models that are available
        if not filtered_models or (self.is_api_failing("openai") and 
                                   self.api_failure_status["openai"].get("payment_related", False)):
            logger.warning("All requested models filtered out or OpenAI has payment issues - adding local models")
            
            # Find all available local models
            local_alternatives = []
            for model in available_models:
                if any(local_id in model.lower() for local_id in local_models):
                    local_alternatives.append(model)
            
            # Add local models to the filtered list
            filtered_models.extend(local_alternatives)
            
            # Log what happened for debugging
            if local_alternatives:
                logger.info(f"Added local alternatives: {local_alternatives}")
            else:
                logger.warning("No local alternatives found in available models")
        
        # Ensure we have at least one model
        if not filtered_models and available_models:
            # Default to first available model as last resort
            filtered_models.append(available_models[0])
            logger.warning(f"No models available after filtering - defaulting to {available_models[0]}")
        
        # Log the model selection process
        logger.info(f"Model selection: Original={original_models}, After filtering={filtered_models}")
        
        return filtered_models
    
    def check_openai_keys(self) -> Tuple[bool, str]:
        """Check all available OpenAI API keys and mark API as failing if none work"""
        import os
        
        # Get all potential OpenAI API keys
        main_key = os.environ.get("OPENAI_API_KEY", "")
        backup_key = os.environ.get("OPENAI_API_KEY_BACKUP", "")
        
        # If no keys available, mark as failing
        if not main_key and not backup_key:
            self.api_failure_status["openai"]["failing"] = True
            self.api_failure_status["openai"]["last_failure_reason"] = "No API keys available"
            self._save_failure_status()
            return False, "No OpenAI API keys available"
        
        # If keys exist but we already determined they're failing, maintain that state
        if self.is_api_failing("openai") and self.api_failure_status["openai"].get("payment_related", False):
            # Keys are available but we know they're failing due to payment issues
            logger.warning("OpenAI API keys are available but known to have payment issues")
            return False, "OpenAI API keys have payment issues"
            
        # We have keys but don't know their status - the caller should test them
        available_keys = []
        if main_key:
            available_keys.append("Main")
        if backup_key:
            available_keys.append("Backup")
            
        return True, f"OpenAI has {len(available_keys)} API key(s) available"
    
    def force_mark_api_failing(self, api_name: str, reason: str, payment_related: bool = True):
        """Explicitly mark an API as failing, useful for external verifications"""
        if api_name not in self.api_failure_status:
            self.api_failure_status[api_name] = {
                "failing": False,
                "last_failure_reason": None,
                "failure_count": 0,
                "last_failure_time": None,
                "payment_related": False
            }
        
        self.api_failure_status[api_name]["failing"] = True
        self.api_failure_status[api_name]["last_failure_reason"] = reason
        self.api_failure_status[api_name]["failure_count"] += 1
        self.api_failure_status[api_name]["last_failure_time"] = time.time()
        self.api_failure_status[api_name]["payment_related"] = payment_related
        
        # Add an explicit flag for external verification
        self.api_failure_status[api_name]["verified_failing"] = True
        self.api_failure_status[api_name]["verification_time"] = datetime.now().isoformat()
        
        logger.error(f"API {api_name} explicitly marked as failing: {reason}")
        self._save_failure_status()
    
    def detect_payment_issues(self, error_message: str) -> Optional[str]:
        """Detect payment issues in API error messages"""
        payment_keywords = [
            "billing", "payment", "credit", "quota", "limit", 
            "exceed", "insufficient", "upgrade", "account", "paid",
            "trial", "expired", "subscription", "rate limit",
            "maximum", "spending", "not active"
        ]
        
        # For better logging
        detected_keywords = []
        
        # Look for payment-related keywords in the error
        for keyword in payment_keywords:
            if keyword.lower() in error_message.lower():
                detected_keywords.append(keyword)
                
                if "openai" in error_message.lower():
                    logger.warning(f"OpenAI payment issue detected: {keyword} in '{error_message}'")
                    return "openai"
                elif "anthropic" in error_message.lower() or "claude" in error_message.lower():
                    logger.warning(f"Anthropic payment issue detected: {keyword} in '{error_message}'")
                    return "anthropic"
                elif "mistral" in error_message.lower():
                    logger.warning(f"Mistral payment issue detected: {keyword} in '{error_message}'")
                    return "mistral"
                else:
                    # Generic API with payment issues
                    logger.warning(f"Unknown API payment issue detected: {keyword} in '{error_message}'")
                    return "unknown_api"
        
        # Check for common OpenAI error patterns separately
        openai_patterns = [
            r"You exceeded your current quota",
            r"Your account is not active",
            r"No API key provided",
            r"Invalid API key provided",
            r"exceeded your current quota",
            r"Your access was terminated"
        ]
        
        for pattern in openai_patterns:
            if re.search(pattern, error_message, re.IGNORECASE):
                logger.error(f"OpenAI API issue detected with pattern '{pattern}' in '{error_message}'")
                return "openai"
                
        if detected_keywords:
            logger.info(f"Detected payment keywords {detected_keywords} but couldn't identify specific API")
            
        return None

# Create a singleton instance
failure_handler = ModelFailureHandler()

def get_failure_handler() -> ModelFailureHandler:
    """Get the singleton failure handler instance"""
    return failure_handler
