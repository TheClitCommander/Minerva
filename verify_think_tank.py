#!/usr/bin/env python3
"""
Verify the Minerva Think Tank setup

This script checks if all AI models are properly configured and available.
It helps diagnose issues with the API keys and connectivity.
"""

import os
import sys
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('think_tank_verifier')

# Add the current directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

def check_api_keys():
    """Check if all required API keys are set."""
    keys = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
        'MISTRAL_API_KEY': os.environ.get('MISTRAL_API_KEY'),
        'HUGGINGFACE_API_KEY': os.environ.get('HUGGINGFACE_API_KEY'),
        'COHERE_API_KEY': os.environ.get('COHERE_API_KEY'),
        'GEMINI_API_KEY': os.environ.get('GEMINI_API_KEY'),
    }
    
    print("\n=== API Key Status ===")
    for key_name, key_value in keys.items():
        status = "✅ Set" if key_value else "❌ Not set"
        masked_value = "None" if not key_value else f"{key_value[:5]}...{key_value[-4:]}" if len(key_value) > 9 else "[too short]"
        print(f"{key_name}: {status} ({masked_value})")
    
    return all(key for key in [keys['OPENAI_API_KEY'], keys['ANTHROPIC_API_KEY'], keys['MISTRAL_API_KEY']])

def check_coordinator():
    """Check if the coordinator can be initialized."""
    print("\n=== Coordinator Status ===")
    try:
        # First import the module
        print("Importing MultiAICoordinator module...")
        import web.multi_ai_coordinator as multi_ai_mod
        print("✅ Import successful")
        
        # Check if coordinator is accessible
        if hasattr(multi_ai_mod, 'coordinator'):
            coordinator = multi_ai_mod.coordinator
            print(f"✅ Found coordinator attribute")
        elif hasattr(multi_ai_mod, 'COORDINATOR'):
            coordinator = multi_ai_mod.COORDINATOR
            print(f"✅ Found COORDINATOR attribute")
        elif hasattr(multi_ai_mod, 'MultiAICoordinator') and hasattr(multi_ai_mod.MultiAICoordinator, 'instance'):
            coordinator = multi_ai_mod.MultiAICoordinator.instance
            print(f"✅ Found MultiAICoordinator.instance")
        else:
            # Try to create a new instance
            if hasattr(multi_ai_mod, 'MultiAICoordinator'):
                coordinator = multi_ai_mod.MultiAICoordinator()
                print(f"✅ Created new coordinator instance")
            else:
                print("❌ MultiAICoordinator class not found")
                return False
        
        # Check available models
        available_models = coordinator.available_models
        print(f"Models available: {len(available_models)}")
        
        # Print model details
        for model_name, model_info in available_models.items():
            status_icon = "✅" if model_info['status'] == 'active' else "⚠️"
            print(f"{status_icon} {model_name} ({model_info['type']}): {model_info['description']}")
        
        # Check for real (non-fallback) models
        real_models = [m for m in available_models if available_models[m]['type'] not in 
                      ['simulation', 'enhanced_simulation', 'advanced_simulation', 'fallback']]
        
        if real_models:
            print(f"\n✅ {len(real_models)} real AI models available:")
            for model in real_models:
                print(f"  - {model}")
            return True
        else:
            print("\n⚠️ No real AI models found, only fallback/simulation available")
            return False
            
    except Exception as e:
        print(f"❌ Error checking coordinator: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_response():
    """Test generating a response using the coordinator."""
    print("\n=== Response Test ===")
    try:
        from web.multi_ai_coordinator import coordinator
        
        # Test with a simple prompt
        test_prompt = "Hello, can you explain what Minerva is in one short sentence?"
        print(f"Sending test prompt: '{test_prompt}'")
        
        response = coordinator.generate_response(test_prompt)
        print(f"\nResponse: '{response}'")
        
        if len(response) > 20:
            print("✅ Received valid response")
            return True
        else:
            print("⚠️ Response seems too short")
            return False
            
    except Exception as e:
        print(f"❌ Error testing response: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function."""
    print("==================================")
    print("  Minerva Think Tank Verifier")
    print("==================================")
    
    # Check API keys
    keys_ok = check_api_keys()
    if not keys_ok:
        print("\n⚠️ Some essential API keys are missing")
    
    # Check coordinator
    coordinator_ok = check_coordinator()
    
    # Test response generation
    if coordinator_ok:
        response_ok = test_response()
    else:
        response_ok = False
        print("\n⚠️ Skipping response test due to coordinator issues")
    
    # Overall status
    print("\n==================================")
    if keys_ok and coordinator_ok and response_ok:
        print("✅ Think Tank verified successfully!")
        print("==================================")
        return 0
    else:
        print("⚠️ Think Tank verification found issues")
        print("==================================")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 