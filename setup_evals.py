#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for installing OpenAI Evals and related dependencies.

This script helps users install the necessary packages to use the OpenAI Evals
integration with Minerva's Think Tank mode.

Usage:
    python setup_evals.py [--install-only]
"""

import sys
import subprocess
import argparse
import logging
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define dependencies
DEPENDENCIES = [
    "openai",
    "evals @ git+https://github.com/openai/evals.git",
    "blobfile",
    "numpy",
    "pandas",
    "tqdm",
    "matplotlib",
    "pydantic"
]

def check_python_version():
    """Check if Python version is compatible."""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        logger.error(f"Python version {major}.{minor} is not supported. Please use Python 3.8 or later.")
        return False
    logger.info(f"Python version {major}.{minor} is compatible.")
    return True

def check_pip():
    """Check if pip is available."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.PIPE)
        logger.info("Pip is available.")
        return True
    except subprocess.CalledProcessError:
        logger.error("Pip is not available. Please install pip first.")
        return False

def install_dependencies():
    """Install required dependencies."""
    logger.info("Installing dependencies...")
    
    # Install each dependency
    for dependency in DEPENDENCIES:
        try:
            logger.info(f"Installing {dependency}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", dependency],
                stdout=subprocess.PIPE
            )
            logger.info(f"Successfully installed {dependency}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {dependency}: {e}")
            return False
    
    logger.info("All dependencies installed successfully.")
    return True

def verify_installation():
    """Verify that OpenAI Evals is properly installed."""
    logger.info("Verifying installation...")
    
    try:
        # Try importing evals
        import importlib
        evals = importlib.import_module("evals")
        logger.info(f"OpenAI Evals version: {getattr(evals, '__version__', 'unknown')}")
        
        # Try importing specific modules
        from evals.api import CompletionFn
        logger.info("Successfully imported CompletionFn from evals.api")
        
        # Check if blobfile is available
        import blobfile
        logger.info("Successfully imported blobfile")
        
        logger.info("Verification successful! OpenAI Evals is properly installed.")
        return True
    except ImportError as e:
        logger.error(f"Verification failed: {e}")
        return False

def test_integration():
    """Test the OpenAI Evals integration with Minerva."""
    logger.info("Testing OpenAI Evals integration...")
    
    # Ensure we're in the correct directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Try to import our integration module
    try:
        sys.path.append(str(script_dir))
        from web.evals_integration import evaluate_model_response, run_comprehensive_evaluation
        
        logger.info("Successfully imported integration modules")
        
        # Test with a sample query and response
        query = "What is machine learning?"
        response = "Machine learning is a branch of artificial intelligence that enables systems to learn from data without explicit programming."
        
        # Evaluate the response
        try:
            result = evaluate_model_response("test_model", query, response)
            logger.info(f"Evaluation result: {result}")
            return True
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return False
    except ImportError as e:
        logger.error(f"Could not import integration modules: {e}")
        return False

def main():
    """Main function to run the setup process."""
    parser = argparse.ArgumentParser(description="Setup script for OpenAI Evals integration")
    parser.add_argument("--install-only", action="store_true", help="Only install dependencies without testing")
    args = parser.parse_args()
    
    logger.info("Starting OpenAI Evals setup...")
    
    # Check prerequisites
    if not check_python_version() or not check_pip():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        logger.error("Failed to install all dependencies. Please try again.")
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        logger.error("Verification failed. Please check the error messages above.")
        sys.exit(1)
    
    # Test integration if not install-only
    if not args.install_only:
        if not test_integration():
            logger.error("Integration test failed. Please check the error messages above.")
            sys.exit(1)
    
    logger.info("Setup completed successfully!")
    
    # Print instructions
    print("\n" + "-" * 60)
    print("OpenAI Evals Integration Setup Complete!")
    print("-" * 60)
    print("\nYou can now use the OpenAI Evals integration with Minerva.")
    print("\nTo test the integration, run:")
    print("  python test_evals_integration.py")
    print("\nFor more information, see:")
    print("  docs/openai_evals_integration.md")
    print("-" * 60 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
