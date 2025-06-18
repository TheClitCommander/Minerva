#!/usr/bin/env python3
"""
Fix script for Minerva's dependencies issues.
This will reinstall and verify the required packages for Hugging Face integration.
"""

import os
import sys
import subprocess
import importlib.util
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required packages to check and reinstall if needed
REQUIRED_PACKAGES = [
    "transformers==4.49.0",  # Specify exact version for consistency
    "tokenizers>=0.13.3",    # Ensure compatible tokenizers version
    "bitsandbytes>=0.39.0",  # For 8-bit quantization
    "torch>=2.0.0",          # PyTorch for model operations
    "einops>=0.6.1",         # Required by some models
    "safetensors>=0.3.1"     # For model weight loading
]

def run_command(cmd, cwd=None):
    """Run a shell command and return its output."""
    try:
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            text=True, 
            capture_output=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return None

def is_package_installed(package_name):
    """Check if a package is installed."""
    # Extract just the package name without version
    package_base = package_name.split("==")[0].split(">=")[0].split("<=")[0]
    return importlib.util.find_spec(package_base) is not None

def fix_dependencies():
    """Fix Minerva's dependencies."""
    logger.info("Starting Minerva dependency fix...")
    
    # Create a pip constraints file to ensure compatible versions
    constraints_file = "minerva_constraints.txt"
    with open(constraints_file, "w") as f:
        f.write("\n".join(REQUIRED_PACKAGES))
    
    logger.info(f"Created constraints file with required packages: {constraints_file}")
    
    # Upgrade pip first
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    logger.info("Upgraded pip to latest version")
    
    # Install/upgrade required packages with constraints
    installation_cmd = [
        sys.executable, 
        "-m", 
        "pip", 
        "install", 
        "--upgrade",
        "-c", 
        constraints_file
    ] + REQUIRED_PACKAGES
    
    result = run_command(installation_cmd)
    if result is not None:
        logger.info("Successfully reinstalled all required packages")
    else:
        logger.error("Failed to install required packages")
        return False
    
    # Verify installations
    logger.info("Verifying package installations...")
    all_installed = True
    for package in REQUIRED_PACKAGES:
        package_base = package.split("==")[0].split(">=")[0].split("<=")[0]
        if is_package_installed(package_base):
            logger.info(f"✅ {package_base} is installed")
            # Try importing to verify deeper issues
            try:
                if package_base == "transformers":
                    from transformers import AutoModelForCausalLM, AutoTokenizer
                    logger.info("✅ transformers core classes can be imported")
                elif package_base == "tokenizers":
                    from tokenizers import Tokenizer
                    logger.info("✅ tokenizers core classes can be imported")
                elif package_base == "bitsandbytes":
                    import bitsandbytes as bnb
                    logger.info("✅ bitsandbytes can be imported")
                elif package_base == "torch":
                    import torch
                    logger.info(f"✅ PyTorch {torch.__version__} is working. CUDA available: {torch.cuda.is_available()}")
            except ImportError as e:
                logger.error(f"❌ {package_base} installed but has import issues: {e}")
                all_installed = False
        else:
            logger.error(f"❌ {package_base} is NOT installed")
            all_installed = False
    
    # Clean up
    if os.path.exists(constraints_file):
        os.remove(constraints_file)
    
    if all_installed:
        logger.info("✅ All dependencies verified successfully!")
        return True
    else:
        logger.error("❌ Some dependencies have issues. Please check the logs.")
        return False

if __name__ == "__main__":
    success = fix_dependencies()
    if success:
        print("\n====================================")
        print("✅ Minerva dependencies fixed successfully!")
        print("You can now run Minerva with:")
        print("python run_minerva.py")
        print("====================================\n")
        sys.exit(0)
    else:
        print("\n====================================")
        print("❌ Some issues remain with Minerva dependencies.")
        print("See the logs above for details on what needs fixing.")
        print("====================================\n")
        sys.exit(1)
