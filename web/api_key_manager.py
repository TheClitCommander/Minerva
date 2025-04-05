"""
API Key Manager for Minerva

This module provides a robust system for managing multiple API keys,
rotating between them if one fails, and handling authentication issues gracefully.
"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path for storing key status
KEY_STATUS_PATH = Path(os.path.dirname(os.path.abspath(__file__))) / "key_status.json"

class ApiKeyManager:
    """Manages multiple API keys for various services with automatic rotation on failure"""
    
    def __init__(self):
        """Initialize the key manager with keys from environment and status tracking"""
        self.key_status = self._load_key_status()
        self._load_keys_from_env()
        self._update_key_statuses()
    
    def _load_key_status(self) -> Dict[str, Any]:
        """Load the key status file if it exists"""
        default_status = {
            "openai": {
                "active_key_index": 0,
                "keys": []
            },
            "anthropic": {
                "active_key_index": 0,
                "keys": []
            },
            "mistral": {
                "active_key_index": 0,
                "keys": []
            }
        }
        
        try:
            if KEY_STATUS_PATH.exists():
                with open(KEY_STATUS_PATH, 'r') as f:
                    return json.load(f)
            return default_status
        except Exception as e:
            logger.warning(f"Error loading key status: {e}")
            return default_status
    
    def _save_key_status(self):
        """Save the current key status to file"""
        try:
            # Remove actual key values before saving
            status_to_save = self.key_status.copy()
            for service in status_to_save:
                for key_entry in status_to_save[service]["keys"]:
                    if "key_value" in key_entry:
                        # Only store the first and last 3 chars for identification
                        key_val = key_entry["key_value"]
                        mask = f"{key_val[:3]}...{key_val[-3:]}" if len(key_val) > 6 else "***"
                        key_entry["key_value"] = mask
            
            with open(KEY_STATUS_PATH, 'w') as f:
                json.dump(status_to_save, f, indent=2)
        except Exception as e:
            logger.warning(f"Error saving key status: {e}")
    
    def _load_keys_from_env(self):
        """Load API keys from environment variables"""
        # OpenAI keys - check multiple possible environment variables
        openai_keys = []
        
        # Primary key
        primary_key = os.environ.get("OPENAI_API_KEY")
        if primary_key and len(primary_key) > 20:
            openai_keys.append(primary_key)
        
        # Secondary keys with numbered suffixes
        for i in range(1, 5):  # Check for OPENAI_API_KEY_1 through OPENAI_API_KEY_4
            key = os.environ.get(f"OPENAI_API_KEY_{i}")
            if key and len(key) > 20 and key not in openai_keys:
                openai_keys.append(key)
        
        # Check if any keys exist in the status file that aren't in environment
        if "openai" in self.key_status:
            for key_entry in self.key_status["openai"]["keys"]:
                if "key_value" in key_entry and key_entry["key_value"] not in openai_keys:
                    # Only add if it's a full key (not a masked one)
                    if len(key_entry["key_value"]) > 20 and "..." not in key_entry["key_value"]:
                        openai_keys.append(key_entry["key_value"])
        
        # Update key statuses
        self._update_openai_keys(openai_keys)
        
        # Similar approach for other APIs
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key and len(anthropic_key) > 20:
            self._update_anthropic_keys([anthropic_key])
        
        mistral_key = os.environ.get("MISTRAL_API_KEY")
        if mistral_key and len(mistral_key) > 20:
            self._update_mistral_keys([mistral_key])
    
    def _update_openai_keys(self, keys: List[str]):
        """Update the OpenAI key list with new keys"""
        if not "openai" in self.key_status:
            self.key_status["openai"] = {
                "active_key_index": 0,
                "keys": []
            }
        
        current_keys = [entry["key_value"] for entry in self.key_status["openai"]["keys"] 
                        if "key_value" in entry and len(entry["key_value"]) > 20 and "..." not in entry["key_value"]]
        
        # Add new keys
        for key in keys:
            if key not in current_keys:
                self.key_status["openai"]["keys"].append({
                    "key_value": key,
                    "status": "untested",
                    "last_failure": None,
                    "failure_count": 0,
                    "last_success": None,
                    "success_count": 0
                })
                logger.info(f"Added new OpenAI key: {key[:3]}...{key[-3:]}")
        
        # Make sure we have a valid active key index
        if self.key_status["openai"]["keys"] and self.key_status["openai"]["active_key_index"] >= len(self.key_status["openai"]["keys"]):
            self.key_status["openai"]["active_key_index"] = 0
    
    def _update_anthropic_keys(self, keys: List[str]):
        """Update the Anthropic key list with new keys"""
        if not "anthropic" in self.key_status:
            self.key_status["anthropic"] = {
                "active_key_index": 0,
                "keys": []
            }
        
        current_keys = [entry["key_value"] for entry in self.key_status["anthropic"]["keys"] 
                        if "key_value" in entry and len(entry["key_value"]) > 20]
        
        # Add new keys
        for key in keys:
            if key not in current_keys:
                self.key_status["anthropic"]["keys"].append({
                    "key_value": key,
                    "status": "untested",
                    "last_failure": None,
                    "failure_count": 0,
                    "last_success": None,
                    "success_count": 0
                })
                logger.info(f"Added new Anthropic key: {key[:3]}...{key[-3:]}")
    
    def _update_mistral_keys(self, keys: List[str]):
        """Update the Mistral key list with new keys"""
        if not "mistral" in self.key_status:
            self.key_status["mistral"] = {
                "active_key_index": 0,
                "keys": []
            }
        
        current_keys = [entry["key_value"] for entry in self.key_status["mistral"]["keys"] 
                        if "key_value" in entry and len(entry["key_value"]) > 20]
        
        # Add new keys
        for key in keys:
            if key not in current_keys:
                self.key_status["mistral"]["keys"].append({
                    "key_value": key,
                    "status": "untested",
                    "last_failure": None,
                    "failure_count": 0,
                    "last_success": None,
                    "success_count": 0
                })
                logger.info(f"Added new Mistral key: {key[:3]}...{key[-3:]}")
    
    def _update_key_statuses(self):
        """Update statuses of all keys"""
        for service in self.key_status:
            if not self.key_status[service]["keys"]:
                logger.warning(f"No {service} API keys available")
                continue
            
            # Reset keys that have been failing but haven't been tried in a while
            for key_entry in self.key_status[service]["keys"]:
                if key_entry.get("status") == "failing" and key_entry.get("last_failure"):
                    # Convert string timestamp to datetime if needed
                    last_failure = key_entry["last_failure"]
                    if isinstance(last_failure, str):
                        try:
                            last_failure = datetime.fromisoformat(last_failure)
                        except ValueError:
                            last_failure = datetime.now() - timedelta(days=1)
                    else:
                        # If it's a timestamp
                        last_failure = datetime.fromtimestamp(last_failure)
                    
                    # Reset keys that haven't been tried in the last hour
                    if datetime.now() - last_failure > timedelta(hours=1):
                        key_entry["status"] = "untested"
                        logger.info(f"Reset {service} key status to untested after cooling period")
    
    def add_key(self, service: str, key: str):
        """Add a new API key for a specific service"""
        if service not in self.key_status:
            self.key_status[service] = {
                "active_key_index": 0,
                "keys": []
            }
        
        # Check if key already exists
        current_keys = [entry["key_value"] for entry in self.key_status[service]["keys"] 
                        if "key_value" in entry]
        
        if key not in current_keys:
            self.key_status[service]["keys"].append({
                "key_value": key,
                "status": "untested",
                "last_failure": None,
                "failure_count": 0,
                "last_success": None,
                "success_count": 0
            })
            logger.info(f"Added new {service} key: {key[:3]}...{key[-3:]}")
            self._save_key_status()
            return True
        return False
    
    def get_active_key(self, service: str) -> Optional[str]:
        """Get the currently active API key for a service"""
        if service not in self.key_status or not self.key_status[service]["keys"]:
            return None
        
        active_idx = self.key_status[service]["active_key_index"]
        keys = self.key_status[service]["keys"]
        
        if active_idx >= len(keys):
            active_idx = 0
            self.key_status[service]["active_key_index"] = 0
        
        # Ensure we're using a working key if possible
        if keys[active_idx].get("status") == "failing":
            # Try to find a non-failing key
            for i, key_entry in enumerate(keys):
                if key_entry.get("status") != "failing":
                    active_idx = i
                    self.key_status[service]["active_key_index"] = i
                    logger.info(f"Switched to non-failing {service} key at index {i}")
                    break
        
        return keys[active_idx].get("key_value")
    
    def report_key_success(self, service: str, key: str):
        """Report a successful API call with a specific key"""
        if service not in self.key_status:
            return
        
        for i, key_entry in enumerate(self.key_status[service]["keys"]):
            if key_entry.get("key_value") == key:
                key_entry["status"] = "working"
                key_entry["last_success"] = datetime.now().isoformat()
                key_entry["success_count"] = key_entry.get("success_count", 0) + 1
                # Make this the active key since it's working
                self.key_status[service]["active_key_index"] = i
                break
        
        self._save_key_status()
    
    def report_key_failure(self, service: str, key: str, error_message: str):
        """Report a failed API call with a specific key and rotate to the next key"""
        if service not in self.key_status:
            return
        
        keys = self.key_status[service]["keys"]
        active_idx = self.key_status[service]["active_key_index"]
        
        # Record failure for the specific key
        for i, key_entry in enumerate(keys):
            if key_entry.get("key_value") == key:
                key_entry["status"] = "failing"
                key_entry["last_failure"] = datetime.now().isoformat()
                key_entry["failure_count"] = key_entry.get("failure_count", 0) + 1
                key_entry["last_error"] = error_message
                
                # Rotate to the next key if this was the active one
                if i == active_idx and len(keys) > 1:
                    next_idx = (i + 1) % len(keys)
                    self.key_status[service]["active_key_index"] = next_idx
                    logger.info(f"Rotated {service} key from index {i} to {next_idx} due to failure")
                break
        
        self._save_key_status()
    
    def all_keys_failing(self, service: str) -> bool:
        """Check if all keys for a service are failing"""
        if service not in self.key_status or not self.key_status[service]["keys"]:
            return True
        
        return all(key_entry.get("status") == "failing" for key_entry in self.key_status[service]["keys"])

# Create a singleton instance
_key_manager = ApiKeyManager()

def get_key_manager() -> ApiKeyManager:
    """Get the singleton key manager instance"""
    return _key_manager
