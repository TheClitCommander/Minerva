#!/usr/bin/env python3
"""
Enable Test API Keys for Minerva's Think Tank

This script enables test API keys for all providers to test the Think Tank's
ranking and blending functionality.
"""

import os
import sys
from pathlib import Path

# Directory and file paths
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = BASE_DIR / 'web' / 'integrations' / 'config.py'
ENV_FILE = BASE_DIR / '.env'

# Test API keys (these are non-functional placeholders that will allow the system to test)
TEST_API_KEYS = {
    "OPENAI_API_KEY": "sk-test-openai-key-for-ranking-test-minerva-thinktank",
    "ANTHROPIC_API_KEY": "sk-ant-test-key-minerva-thinktank",
    "MISTRAL_API_KEY": "mistral-test-key-minerva-thinktank",
    "GOOGLE_API_KEY": "google-test-key-minerva-thinktank",
    "COHERE_API_KEY": "cohere-test-key-minerva-thinktank"
}

def enable_test_api_keys():
    """Enable test API keys by updating the .env file"""
    # Create or update .env file
    with open(ENV_FILE, 'w') as f:
        for key, value in TEST_API_KEYS.items():
            f.write(f"{key}='{value}'\n")
    
    print("✅ Test API keys written to .env file")
    
    # Load them into the current environment
    for key, value in TEST_API_KEYS.items():
        os.environ[key] = value
    
    print("✅ Test API keys loaded into environment")
    return True

def modify_think_tank_consolidated():
    """Modify the think_tank_consolidated.py file to use test API keys"""
    file_path = BASE_DIR / 'web' / 'think_tank_consolidated.py'
    
    if not file_path.exists():
        print(f"❌ Cannot find {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if we need to add the test API keys logic
    if "# Test mode detection" not in content:
        # Find a suitable location to insert the code (after imports)
        import_section_end = content.find("def process_think_tank_request")
        
        if import_section_end == -1:
            print("❌ Could not find a suitable location to insert test code")
            return False
        
        # Code to insert
        test_code = """
# Test mode detection
TEST_MODE = os.environ.get("MINERVA_TEST_MODE", "false").lower() == "true"

# Use test API keys if in test mode
if TEST_MODE:
    os.environ["OPENAI_API_KEY"] = "sk-test-openai-key-for-ranking-test-minerva-thinktank"
    os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-minerva-thinktank"
    os.environ["MISTRAL_API_KEY"] = "mistral-test-key-minerva-thinktank"
    os.environ["GOOGLE_API_KEY"] = "google-test-key-minerva-thinktank"
    os.environ["COHERE_API_KEY"] = "cohere-test-key-minerva-thinktank"
    logger.info("🧪 Running in TEST MODE with test API keys")

"""
        
        # Insert the code
        new_content = content[:import_section_end] + test_code + content[import_section_end:]
        
        # Write the modified content back
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Added test mode detection to {file_path}")
        return True
    else:
        print(f"✅ Test mode detection already in {file_path}")
        return True

def modify_model_processors():
    """Modify model_processors.py to handle test API keys"""
    file_path = BASE_DIR / 'web' / 'model_processors.py'
    
    if not file_path.exists():
        print(f"❌ Cannot find {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if we need to add test mode logic
    if "def is_test_api_key(" not in content:
        # Find suitable locations to insert helper functions
        import_section_end = content.find("import re")
        if import_section_end == -1:
            import_section_end = content.find("import os")
        
        if import_section_end == -1:
            print("❌ Could not find a suitable location to insert test code")
            return False
        
        # Add the test mode variable after imports
        test_mode_code = """
# Test mode detection
TEST_MODE = os.environ.get("MINERVA_TEST_MODE", "false").lower() == "true"

def is_test_api_key(api_key):
    \"\"\"Check if an API key is a test key\"\"\"
    test_patterns = ["test-key", "test-openai", "test-ant", "minerva-thinktank"]
    if api_key and isinstance(api_key, str):
        return any(pattern in api_key.lower() for pattern in test_patterns)
    return False

"""
        
        # Insert the test mode code
        new_content = content[:import_section_end] + test_mode_code + content[import_section_end:]
        
        # Write the modified content back
        with open(file_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Added test mode detection to {file_path}")
        return True
    else:
        print(f"✅ Test mode detection already in {file_path}")
        return True

def create_test_runner():
    """Create or update the test runner script"""
    test_runner_path = BASE_DIR / "run_think_tank_test.py"
    
    test_runner_code = """#!/usr/bin/env python3
\"\"\"
Think Tank Test Runner

This script runs a comprehensive test of the Think Tank with various query types
to validate model selection, response quality, ranking, and blending.
\"\"\"

import os
import sys
import subprocess
import time

def main():
    # Set the test mode environment variable
    os.environ["MINERVA_TEST_MODE"] = "true"
    
    # Activate the Python environment
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "minerva_env")
    activate_script = os.path.join(env_path, "bin", "activate")
    
    # Run the comprehensive test
    cmd = f"cd {os.path.dirname(os.path.abspath(__file__))} && source {activate_script} && python test_think_tank_full.py"
    
    print("🚀 Running Think Tank test in TEST MODE...")
    print("📝 This will use simulated API responses to test model ranking and blending.")
    print(f"⏱️ Starting test at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the command
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Stream the output
    for line in iter(process.stdout.readline, b''):
        print(line.decode('utf-8'), end='')
    
    # Wait for completion
    process.wait()
    
    if process.returncode == 0:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed with error code:", process.returncode)
        for line in iter(process.stderr.readline, b''):
            print(line.decode('utf-8'), end='')

if __name__ == "__main__":
    main()
"""
    
    with open(test_runner_path, 'w') as f:
        f.write(test_runner_code)
    
    # Make it executable
    test_runner_path.chmod(test_runner_path.stat().st_mode | 0o111)
    
    print(f"✅ Created test runner script at {test_runner_path}")
    return True

def update_model_capabilities():
    """Update model capabilities for better ranking and blending"""
    model_capabilities_path = BASE_DIR / "processor" / "think_tank.py"
    
    if not model_capabilities_path.exists():
        print(f"❌ Cannot find {model_capabilities_path}")
        return False
    
    # Read the file
    with open(model_capabilities_path, 'r') as f:
        content = f.read()
    
    # Find the MODEL_CAPABILITIES dictionary
    capabilities_start = content.find("MODEL_CAPABILITIES = {")
    
    if capabilities_start == -1:
        print("❌ Could not find MODEL_CAPABILITIES dictionary")
        return False
    
    # Check if our local models are already defined
    if "Llama-3.2-1B-Instruct-Q4_0.gguf" in content:
        print("✅ Model capabilities for local models already defined")
        return True
    
    # Find where to insert our local model capabilities
    capabilities_end = content.find("}", capabilities_start)
    if capabilities_end == -1:
        print("❌ Could not find end of MODEL_CAPABILITIES dictionary")
        return False
    
    # Capabilities to add
    new_capabilities = """
    # Local model capabilities
    "Llama-3.2-1B-Instruct-Q4_0.gguf": {
        'technical': 0.70,
        'creative': 0.65,
        'reasoning': 0.70,
        'factual': 0.60,
        'structured': 0.65,
        'max_tokens': 2048,
        'context_window': 4096
    },
    "gpt4all-llama-3": {
        'technical': 0.70,
        'creative': 0.65,
        'reasoning': 0.70,
        'factual': 0.60,
        'structured': 0.65,
        'max_tokens': 2048,
        'context_window': 4096
    },
"""
    
    # Insert our capabilities
    new_content = content[:capabilities_end] + new_capabilities + content[capabilities_end:]
    
    # Write the modified content back
    with open(model_capabilities_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated model capabilities in {model_capabilities_path}")
    return True

def main():
    print("=== Minerva Think Tank Test API Key Setup ===")
    
    # Step 1: Enable test API keys
    enable_test_api_keys()
    
    # Step 2: Modify think_tank_consolidated.py
    modify_think_tank_consolidated()
    
    # Step 3: Modify model_processors.py
    modify_model_processors()
    
    # Step 4: Update model capabilities
    update_model_capabilities()
    
    # Step 5: Create test runner
    create_test_runner()
    
    print("\n===== Setup Complete =====")
    print("You can now test Minerva's Think Tank with the following commands:")
    print("\n1. Run the comprehensive test:")
    print("   python run_think_tank_test.py")
    print("\n2. Or run with real API keys (if available):")
    print("   MINERVA_TEST_MODE=false python test_think_tank_full.py")
    print("\nThese tests will show the full capabilities of your Think Tank's:")
    print("- Multi-model response generation")
    print("- Sophisticated response ranking system")
    print("- Intelligent response blending strategies")

if __name__ == "__main__":
    main()
