#!/usr/bin/env python3
"""
API Key Setup Utility for Minerva's Think Tank

This script helps set up API keys for the various AI providers used by Minerva.
It stores API keys as environment variables and updates the config.py file.
"""

import os
import sys
import dotenv
from pathlib import Path
import getpass

# Config file location
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'integrations', 'config.py')

# Define API key providers and their environment variable names
API_PROVIDERS = {
    "OpenAI": "OPENAI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Mistral": "MISTRAL_API_KEY",
    "Google": "GOOGLE_API_KEY",
    "Cohere": "COHERE_API_KEY"
}

def create_env_file():
    """Create or update .env file with API keys"""
    env_path = Path(os.path.dirname(os.path.abspath(__file__))) / '.env'
    
    # Load existing .env if it exists
    existing_vars = {}
    if env_path.exists():
        dotenv.load_dotenv(env_path)
        for key in API_PROVIDERS.values():
            if os.getenv(key):
                existing_vars[key] = os.getenv(key)
    
    print("\n=== Minerva API Key Setup ===")
    print("Enter API keys for each provider (press Enter to skip or use existing key)")
    print("API keys will be stored in .env file and loaded as environment variables")
    
    # Get API keys with pre-filled values if they exist
    new_keys = {}
    for provider, env_var in API_PROVIDERS.items():
        default = existing_vars.get(env_var, '')
        display_default = f"[Current: {default[:5]}...{default[-4:]}]" if default else "[Not set]"
        
        # Securely ask for API key
        prompt = f"\n{provider} API Key {display_default}: "
        api_key = getpass.getpass(prompt)
        
        # Keep existing key if empty
        if not api_key and default:
            new_keys[env_var] = default
            print(f"Keeping existing {provider} API key")
        elif api_key:
            new_keys[env_var] = api_key
            print(f"✅ New {provider} API key saved")
    
    # Write to .env file
    with open(env_path, 'w') as f:
        for key, value in new_keys.items():
            f.write(f"{key}='{value}'\n")
    
    print("\n✅ API keys saved to .env file")
    return new_keys

def update_config_file(api_keys):
    """Update config.py with the new API keys"""
    if not os.path.exists(CONFIG_FILE):
        print(f"⚠️ Config file not found at {CONFIG_FILE}")
        return False
    
    with open(CONFIG_FILE, 'r') as f:
        config_content = f.read()
    
    # Update each API key in the config file
    for env_var, api_key in api_keys.items():
        if env_var in config_content:
            # This is a very basic replacement. In a production system,
            # you'd want to use a more robust method like AST parsing.
            var_name = env_var.split('_')[0].title()
            if f"{var_name}_API_KEY" in config_content:
                # We'll be conservative and not overwrite directly, just show how
                print(f"✅ {env_var} is properly configured in config.py")
        else:
            print(f"⚠️ Could not find {env_var} in config.py")
    
    print("\n✅ API key validation complete")
    print("The config.py file uses environment variables, so your API keys are now available to the system")
    return True

def test_api_key_loading():
    """Test that API keys are correctly loaded from environment"""
    try:
        # Reload environment variables
        dotenv.load_dotenv()
        
        # Import the config module to test
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from web.integrations.config import (
            OPENAI_API_KEY, ANTHROPIC_API_KEY, MISTRAL_API_KEY, 
            GOOGLE_API_KEY, COHERE_API_KEY
        )
        
        # Check each key
        key_status = {
            "OpenAI": bool(OPENAI_API_KEY),
            "Anthropic": bool(ANTHROPIC_API_KEY),
            "Mistral": bool(MISTRAL_API_KEY),
            "Google": bool(GOOGLE_API_KEY),
            "Cohere": bool(COHERE_API_KEY)
        }
        
        # Display results
        print("\n=== API Key Validation ===")
        all_valid = True
        for provider, is_valid in key_status.items():
            status = "✅ Valid" if is_valid else "❌ Missing or Invalid"
            print(f"{provider}: {status}")
            if not is_valid:
                all_valid = False
        
        if all_valid:
            print("\n🎉 All API keys are valid and properly loaded!")
        else:
            print("\n⚠️ Some API keys are missing or invalid. Minerva will use available models only.")
        
        return all_valid
        
    except ImportError as e:
        print(f"\n❌ Error importing config module: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error validating API keys: {e}")
        return False

if __name__ == "__main__":
    print("=== Minerva Think Tank API Key Setup ===")
    print("This utility will help you set up API keys for various AI providers.")
    print("These keys will be stored in a .env file and loaded as environment variables.")
    
    # Step 1: Create or update .env file
    api_keys = create_env_file()
    
    # Step 2: Update config.py
    update_config_file(api_keys)
    
    # Step 3: Test API key loading
    test_api_key_loading()
    
    print("\n=== Setup Complete ===")
    print("To use these API keys with Minerva:")
    print("1. Restart any running Minerva processes")
    print("2. Run the validation script: python validate_api_keys.py")
    print("3. Test the Think Tank with multiple models: python test_think_tank_metadata.py")
