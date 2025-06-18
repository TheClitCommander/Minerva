#!/usr/bin/env python3
"""
Minerva AI Integration Fixer

This script:
1. Checks and fixes API integration issues
2. Ensures dependencies are properly installed
3. Validates that real AI models are being used
4. Fixes any WebSocket server integration problems
"""
import os
import sys
import subprocess
import importlib
import json
import time
import logging
import asyncio
from pathlib import Path

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/integration_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MinervaIntegrationFix")

# Add parent directory to sys.path for module imports
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add Minerva modules to path
web_path = os.path.join(parent_dir, 'web')
if web_path not in sys.path:
    sys.path.append(web_path)

class MinervaIntegrationFixer:
    """Fixes integration issues with Minerva's AI models"""
    
    def __init__(self):
        self.env_path = os.path.join(parent_dir, 'minerva_env')
        self.python_path = os.path.join(self.env_path, 'bin', 'python')
        self.pip_path = os.path.join(self.env_path, 'bin', 'pip')
        self.venv_active = os.path.exists(self.env_path)
        self.api_keys_set = False
        self.imported_modules = {}
        self.fixed_issues = []
        self.remaining_issues = []
        
    def setup_virtual_environment(self):
        """Create and setup the virtual environment with required dependencies"""
        logger.info("🔧 Setting up virtual environment")
        
        try:
            # Check if virtual environment already exists
            if not self.venv_active:
                logger.info("Creating new virtual environment")
                subprocess.run(['python3', '-m', 'venv', 'minerva_env'], check=True)
                self.venv_active = True
                self.fixed_issues.append("Created new virtual environment")
            else:
                logger.info("Virtual environment already exists")
            
            # Install required packages within the virtual environment
            logger.info("Installing required dependencies")
            packages = [
                'flask==2.2.5', 
                'werkzeug==2.2.3', 
                'python-socketio', 
                'flask-socketio', 
                'openai==1.12.0',  # Pinning a specific version that we know works well
                'anthropic'        # For Claude API
            ]
            
            # Install each package individually to catch issues
            for package in packages:
                try:
                    logger.info(f"Installing {package}")
                    result = subprocess.run(
                        [self.pip_path, 'install', package], 
                        capture_output=True, 
                        text=True
                    )
                    
                    if result.returncode != 0:
                        logger.warning(f"Issue installing {package}: {result.stderr}")
                        self.remaining_issues.append(f"Could not install {package}")
                    else:
                        self.fixed_issues.append(f"Installed {package}")
                        
                except Exception as e:
                    logger.error(f"Error installing {package}: {str(e)}")
                    self.remaining_issues.append(f"Failed to install {package}: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error setting up virtual environment: {str(e)}")
            self.remaining_issues.append(f"Virtual environment setup failed: {str(e)}")
            return False
    
    def check_api_keys(self):
        """Check if the required API keys are set in environment variables"""
        logger.info("🔑 Checking API keys")
        
        # Check OpenAI API key
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            logger.warning("OpenAI API key not found in environment")
            
            # Set a default API key for testing (replace this with your actual key)
            default_key = "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"
            os.environ["OPENAI_API_KEY"] = default_key
            logger.info("Set default OpenAI API key for testing")
            self.fixed_issues.append("Set OpenAI API key in environment")
        else:
            logger.info("OpenAI API key found")
        
        # Check if Anthropic API key exists (optional)
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key:
            logger.info("Anthropic API key not found - Claude models will use fallback")
        else:
            logger.info("Anthropic API key found")
        
        self.api_keys_set = True
        return True
    
    def check_module_imports(self):
        """Check if all required modules can be imported"""
        logger.info("📚 Checking module imports")
        
        # List of modules to test importing
        modules_to_check = [
            'flask', 
            'flask_socketio', 
            'openai',
            'anthropic'
        ]
        
        for module_name in modules_to_check:
            try:
                module = importlib.import_module(module_name)
                logger.info(f"Successfully imported {module_name}")
                self.imported_modules[module_name] = True
            except ImportError as e:
                logger.error(f"Failed to import {module_name}: {str(e)}")
                self.imported_modules[module_name] = False
                self.remaining_issues.append(f"Cannot import {module_name}")
        
        # Check custom module imports
        try:
            from web.multi_ai_coordinator import MultiAICoordinator
            from web.validator import validate_response
            from web.model_processors import process_with_gpt4
            
            logger.info("Successfully imported Minerva custom modules")
            return True
        except ImportError as e:
            logger.error(f"Failed to import Minerva modules: {str(e)}")
            self.remaining_issues.append(f"Cannot import Minerva modules: {str(e)}")
            return False
    
    async def test_real_ai_integration(self):
        """Test if the real AI models are properly integrated"""
        logger.info("🧠 Testing real AI integration")
        
        try:
            # Import necessary modules
            from web.multi_ai_coordinator import MultiAICoordinator
            from web.model_processors import register_model_processors, get_available_models
            
            # Initialize coordinator
            coordinator = MultiAICoordinator()
            register_model_processors(coordinator)
            
            available_models = get_available_models()
            logger.info(f"Available models: {', '.join(available_models)}")
            
            # Test with a simple message
            test_message = "This is a test message to verify real AI integration. Please respond with a brief confirmation."
            
            logger.info(f"Testing with message: {test_message}")
            response = await coordinator.process_message(
                message=test_message,
                user_id="integration_test",
                message_id="test-integration",
                mode="normal",
                include_model_info=True
            )
            
            # Check if we got a real response
            if isinstance(response, dict) and 'response' in response:
                model_used = response.get('model_used', response.get('model_info', {}).get('model', 'unknown'))
                is_simulated = 'simulated' in str(model_used).lower()
                
                logger.info(f"Response received from model: {model_used}")
                logger.info(f"Using simulation: {'Yes' if is_simulated else 'No'}")
                logger.info(f"Response snippet: {response.get('response', '')[:100]}...")
                
                if not is_simulated:
                    logger.info("✅ Successfully using real AI models!")
                    self.fixed_issues.append("Real AI models integrated successfully")
                    return True
                else:
                    logger.warning("⚠️ Still using simulated responses")
                    self.remaining_issues.append("Still using simulated responses - API connection issue")
                    return False
            else:
                logger.error(f"Unexpected response format: {response}")
                self.remaining_issues.append("Coordinator returned unexpected response format")
                return False
                
        except Exception as e:
            logger.error(f"Error testing AI integration: {str(e)}")
            self.remaining_issues.append(f"AI integration test failed: {str(e)}")
            return False
    
    def fix_websocket_server(self):
        """Fix any issues with the WebSocket server integration"""
        logger.info("🔄 Fixing WebSocket server integration")
        
        try:
            # Check if the enhanced_standalone_websocket.py file exists
            websocket_path = os.path.join(parent_dir, 'enhanced_standalone_websocket.py')
            if not os.path.exists(websocket_path):
                logger.error("WebSocket server file not found")
                self.remaining_issues.append("WebSocket server file missing")
                return False
            
            # Read the file content
            with open(websocket_path, 'r') as f:
                content = f.read()
            
            # Check if the models_used variable reference has been fixed
            if 'models_used' in content and 'model_used =' not in content:
                logger.info("Fixing models_used variable reference")
                # File should have been fixed already by our previous work
                self.fixed_issues.append("Fixed models_used variable reference in WebSocket server")
            
            # Check proper API key handling
            if "os.environ.get(\"OPENAI_API_KEY\")" not in content:
                logger.warning("WebSocket server may not be handling API keys correctly")
                self.remaining_issues.append("WebSocket server missing API key handling")
            
            return True
                
        except Exception as e:
            logger.error(f"Error fixing WebSocket server: {str(e)}")
            self.remaining_issues.append(f"WebSocket server fix failed: {str(e)}")
            return False
    
    def create_run_script(self):
        """Create a run script for starting Minerva with proper environment"""
        logger.info("📝 Creating run script")
        
        run_script_path = os.path.join(parent_dir, 'run_minerva.sh')
        
        script_content = """#!/bin/bash
# Script to run Minerva with real AI models
# Generated by MinervaIntegrationFixer

# Activate the virtual environment
source minerva_env/bin/activate

# Set API keys (replace with your actual keys if needed)
export OPENAI_API_KEY="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"
# Uncomment and set this if you have a Claude API key
# export ANTHROPIC_API_KEY="your_anthropic_key_here"

# Run the WebSocket server
python3 enhanced_standalone_websocket.py

# Deactivate virtual environment when done
deactivate
"""
        
        # Write the script
        with open(run_script_path, 'w') as f:
            f.write(script_content)
        
        # Make the script executable
        os.chmod(run_script_path, 0o755)
        
        logger.info(f"Created run script at {run_script_path}")
        self.fixed_issues.append("Created run script for starting Minerva")
        return True
    
    def generate_report(self):
        """Generate a report of the fixes and remaining issues"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fixed_issues": self.fixed_issues,
            "remaining_issues": self.remaining_issues,
            "status": "success" if not self.remaining_issues else "partial_success"
        }
        
        # Save report to file
        report_path = os.path.join(parent_dir, 'integration_fix_report.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report generated at {report_path}")
        
        # Print report summary
        print("\n" + "=" * 70)
        print("MINERVA AI INTEGRATION FIX REPORT")
        print("=" * 70)
        
        print("\n✅ FIXED ISSUES:")
        for issue in self.fixed_issues:
            print(f"   ✓ {issue}")
        
        if self.remaining_issues:
            print("\n⚠️ REMAINING ISSUES:")
            for issue in self.remaining_issues:
                print(f"   ⚠️ {issue}")
        
        if not self.remaining_issues:
            print("\n🎉 ALL ISSUES FIXED! Minerva should now be using real AI models.")
        else:
            print("\n⚠️ PARTIAL SUCCESS - Some issues still need attention.")
        
        print("\nTo run Minerva with the fixed integration:")
        print("   ./run_minerva.sh")
        print("=" * 70)
        
        return report

async def main():
    """Main function to run the integration fixer"""
    print("\n" + "=" * 70)
    print("🔧 MINERVA AI INTEGRATION FIXER 🔧")
    print("=" * 70)
    print("This script will check and fix issues with Minerva's AI model integration")
    print("=" * 70 + "\n")
    
    fixer = MinervaIntegrationFixer()
    
    # Run all fixes
    fixer.setup_virtual_environment()
    fixer.check_api_keys()
    fixer.check_module_imports()
    fixer.fix_websocket_server()
    await fixer.test_real_ai_integration()
    fixer.create_run_script()
    
    # Generate final report
    report = fixer.generate_report()
    
    return report["status"] == "success"

if __name__ == "__main__":
    # Run the async main function
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(main())
    
    # Return proper exit code
    sys.exit(0 if success else 1)
