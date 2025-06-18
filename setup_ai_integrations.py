#!/usr/bin/env python
"""
Setup script to configure AI integrations for Minerva

This script automatically configures integrations between Minerva and 
various AI implementations found in the Minerva/GPT AI Codes folder.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

# Constants
DESKTOP_PATH = os.path.expanduser("~/Desktop")
AI_CODES_PATH = os.path.join(MINERVA_PATH, "GPT AI Codes")
MINERVA_PATH = os.path.join(DESKTOP_PATH, "Minerva")
INTEGRATIONS_CONFIG_PATH = os.path.join(MINERVA_PATH, "config/integrations.json")

# Ensure output directories exist
os.makedirs(os.path.dirname(INTEGRATIONS_CONFIG_PATH), exist_ok=True)

# Map of AI implementation directories to Minerva integration modules
AI_TO_INTEGRATION_MAP = {
    # Enhanced GPT implementations
    "GPT AI Codes": "huggingface_integration.py",
    
    # AutoGPT implementations
    "Auto-GPT": "autogpt_integration.py",
    "Auto-GPT-Turbo": "autogpt_integration.py",
    "AgentGPT": "autogpt_integration.py",
    "autogpt": "autogpt_integration.py",
    "autogpt-server-api": "autogpt_integration.py",
    "mini-agi": "autogpt_integration.py",
    "SuperAGI": "autogpt_integration.py",
    "babyagi": "autogpt_integration.py",
    
    # GPT4All implementations
    "gpt4all": "gpt4all_integration.py",
    "gpt4all-backend": "gpt4all_integration.py",
    "gpt4all-bindings": "gpt4all_integration.py",
    "gpt4all-chat": "gpt4all_integration.py",
    "gpt4all-training": "gpt4all_integration.py",
    "gpt4all_api_server": "gpt4all_integration.py",
    "gpt4all_python": "gpt4all_integration.py",
    
    # Hugging Face implementations
    "starcoder": "huggingface_integration.py",
    "starcoder2": "huggingface_integration.py",
    "mlc-llm": "huggingface_integration.py",
    
    # LangChain and related
    "localGPT": "langchain_integration.py",
    "localGPTUI": "langchain_integration.py",
    "pdfGPT": "langchain_integration.py",
    
    # Chroma DB (vector store)
    "chroma": "langchain_integration.py",
    "chromadb": "langchain_integration.py",
    "chroma-server": "langchain_integration.py",
    "distributed-chroma": "langchain_integration.py",
    "run-chroma": "langchain_integration.py",
}


def create_gpt4all_integration():
    """Create GPT4All integration file if it doesn't exist"""
    gpt4all_integration_path = os.path.join(MINERVA_PATH, "integrations/gpt4all_integration.py")
    
    if os.path.exists(gpt4all_integration_path):
        print(f"GPT4All integration already exists at {gpt4all_integration_path}")
        return
    
    print(f"Creating GPT4All integration at {gpt4all_integration_path}")
    
    integration_code = """\"\"\"
GPT4All Integration for Minerva AI Assistant

This module provides integration with the GPT4All framework.
\"\"\"

import os
import sys
import json
from typing import Dict, List, Optional, Any
from loguru import logger

from .base_integration import BaseIntegration

class GPT4AllIntegration(BaseIntegration):
    \"\"\"Integration with GPT4All framework.\"\"\"
    
    def __init__(self, framework_path: str):
        \"\"\"
        Initialize the GPT4All integration.
        
        Args:
            framework_path: Path to the GPT4All installation
        \"\"\"
        super().__init__("GPT4All", framework_path)
        
        self.api_available = False
        self.models_path = os.path.join(os.path.expanduser("~"), ".cache", "gpt4all")
        
        # Add these capabilities
        self.capabilities = ["text_generation", "chat", "local_execution"]
        
        try:
            # Check if GPT4All is installed via pip
            try:
                import gpt4all
                self.api_available = True
                self.gpt4all_module = gpt4all
                self.model = None
                logger.info("GPT4All package is installed")
            except ImportError:
                logger.warning("GPT4All package is not installed, attempting to install...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "gpt4all"])
                    import gpt4all
                    self.api_available = True
                    self.gpt4all_module = gpt4all
                    self.model = None
                    logger.info("Successfully installed GPT4All package")
                except Exception as e:
                    logger.error(f"Failed to install GPT4All: {str(e)}")
            
            logger.info(f"GPT4All API available: {self.api_available}")
            
        except Exception as e:
            logger.error(f"Error initializing GPT4All integration: {str(e)}")
    
    def load_model(self, model_name="gpt4all-j-v1.3-groovy"):
        \"\"\"
        Load a GPT4All model.
        
        Args:
            model_name: Name of the model to load
        
        Returns:
            True if model was loaded successfully, False otherwise
        \"\"\"
        if not self.api_available:
            logger.error("GPT4All API is not available")
            return False
        
        try:
            logger.info(f"Loading GPT4All model: {model_name}")
            self.model = self.gpt4all_module.GPT4All(model_name, model_path=self.models_path)
            logger.info(f"Successfully loaded model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error loading GPT4All model: {str(e)}")
            return False
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> str:
        \"\"\"
        Process a message using GPT4All.
        
        Args:
            message: The message to process
            context: Optional context for processing
        
        Returns:
            Response from GPT4All
        \"\"\"
        if not self.api_available:
            return "GPT4All is not available"
        
        if not self.model:
            logger.info("Model not loaded, attempting to load default model")
            if not self.load_model():
                return "Failed to load GPT4All model"
        
        try:
            logger.info(f"Sending message to GPT4All: {message[:50]}...")
            
            # Process system prompt if provided in context
            system_prompt = ""
            if context and "system_prompt" in context:
                system_prompt = context["system_prompt"]
            
            # Generate response
            response = self.model.generate(
                message, 
                max_tokens=200,
                temp=0.7,
                system_prompt=system_prompt
            )
            
            logger.info(f"GPT4All response: {response[:50]}...")
            return response
        except Exception as e:
            logger.error(f"Error processing message with GPT4All: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_response(self, message: str) -> str:
        \"\"\"
        Generate a response to a message.
        
        Args:
            message: The message to respond to
        
        Returns:
            Response from GPT4All
        \"\"\"
        return self.process_message(message)
"""
    
    with open(gpt4all_integration_path, "w") as f:
        f.write(integration_code)
    
    print(f"Created GPT4All integration at {gpt4all_integration_path}")


def find_ai_implementations():
    """Find AI implementations in the specified directory"""
    available_implementations = {}
    
    if not os.path.exists(AI_CODES_PATH):
        print(f"AI codes directory not found: {AI_CODES_PATH}")
        return available_implementations
    
    for item in os.listdir(AI_CODES_PATH):
        item_path = os.path.join(AI_CODES_PATH, item)
        if os.path.isdir(item_path) and item in AI_TO_INTEGRATION_MAP:
            integration_type = AI_TO_INTEGRATION_MAP[item].split(".")[0]  # Remove .py extension
            
            if integration_type not in available_implementations:
                available_implementations[integration_type] = []
            
            available_implementations[integration_type].append(item_path)
    
    return available_implementations


def create_integration_config(implementations):
    """Create or update the integration configuration file"""
    config = {
        "integrations": {}
    }
    
    for integration_type, paths in implementations.items():
        config["integrations"][integration_type] = {
            "enabled": True,
            "paths": paths
        }
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(INTEGRATIONS_CONFIG_PATH), exist_ok=True)
    
    # Save configuration
    with open(INTEGRATIONS_CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Integration configuration saved to {INTEGRATIONS_CONFIG_PATH}")


def update_app_to_use_integrations():
    """Update app.py to properly load integrations"""
    app_path = os.path.join(MINERVA_PATH, "web/app.py")
    
    if not os.path.exists(app_path):
        print(f"App file not found: {app_path}")
        return
    
    # Read the existing app.py file
    with open(app_path, "r") as f:
        app_code = f.read()
    
    # Check if integration code already exists
    if "load_integrations_from_config" in app_code:
        print("Integration loading code already exists in app.py")
        return
    
    # Add code to load integrations from config
    init_app_function = """
def load_integrations_from_config():
    \"\"\"Load AI integrations from the configuration file.\"\"\"
    from integrations.framework_manager import FrameworkManager
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config/integrations.json")
    if not os.path.exists(config_path):
        print(f"Integration configuration not found: {config_path}")
        return
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        manager = FrameworkManager()
        
        # Load configured integrations
        for integration_type, settings in config.get("integrations", {}).items():
            if settings.get("enabled", False):
                for path in settings.get("paths", []):
                    if os.path.exists(path):
                        manager.register_framework(integration_type, path)
        
        print(f"Loaded {len(manager.loaded_frameworks)} AI integrations")
    except Exception as e:
        print(f"Error loading integrations: {str(e)}")
"""
    
    # Find the right spot to insert (after the imports)
    import_end_idx = app_code.find("def init_app")
    if import_end_idx == -1:
        print("Could not find an appropriate location to add integration code")
        return
    
    # Insert integration loading code
    updated_app_code = (
        app_code[:import_end_idx] + 
        init_app_function + 
        app_code[import_end_idx:]
    )
    
    # Add call to load_integrations_from_config in init_app
    init_app_function_body = "def init_app(flask_app=None, socketio_instance=None):"
    init_app_function_call = "    # Load AI integrations\n    load_integrations_from_config()\n"
    
    if init_app_function_body in updated_app_code and init_app_function_call not in updated_app_code:
        updated_app_code = updated_app_code.replace(
            init_app_function_body,
            init_app_function_body + "\n" + init_app_function_call
        )
    
    # Update app.py
    with open(app_path, "w") as f:
        f.write(updated_app_code)
    
    print("Updated app.py to load integrations from configuration")


def main():
    """Main function to setup AI integrations"""
    print("Setting up AI integrations for Minerva...")
    
    # Create GPT4All integration
    create_gpt4all_integration()
    
    # Find available AI implementations
    implementations = find_ai_implementations()
    
    if not implementations:
        print("No compatible AI implementations found")
        return
    
    print(f"Found {sum(len(paths) for paths in implementations.values())} AI implementations across {len(implementations)} integration types")
    
    # Create or update integration configuration
    create_integration_config(implementations)
    
    # Update app.py to use integrations
    update_app_to_use_integrations()
    
    print("AI integration setup complete!")
    print("\nRestart Minerva for changes to take effect:")
    print("cd ~/Desktop/Minerva && source fresh_venv/bin/activate && python run_minerva.py --port 5001 --debug")


if __name__ == "__main__":
    main()
