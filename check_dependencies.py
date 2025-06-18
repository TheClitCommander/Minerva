#!/usr/bin/env python3
"""
Dependency Checker for Minerva

This script checks for necessary dependencies and attempts to resolve common issues.
It can be run independently to diagnose and fix problems.
"""

import os
import sys
import subprocess
import logging
import platform
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dependency_checker")

class DependencyChecker:
    """Class to check and fix dependencies for Minerva"""
    
    def __init__(self, auto_fix=True):
        """Initialize the dependency checker"""
        self.auto_fix = auto_fix
        self.system = platform.system()
        self.python_version = platform.python_version()
        self.venv_active = 'VIRTUAL_ENV' in os.environ
        
        # Core packages that must be available
        self.core_packages = [
            "flask",
            "flask_socketio",
            "eventlet",
        ]
        
        # AI-related packages
        self.ai_packages = [
            "torch",
            "transformers",
            "tokenizers",
        ]
        
        # Optional packages
        self.optional_packages = [
            "bitsandbytes",  # For quantization
            "psutil",        # For system monitoring
            "safetensors",   # For model loading
        ]
        
        # Tracked package versions
        self.package_versions = {}
        
        # Problems detected
        self.problems = []
        self.fixes_applied = []
        
    def check_all(self):
        """Perform all dependency checks"""
        logger.info("Starting dependency checks...")
        
        self.check_venv()
        self.check_python_version()
        self.check_core_packages()
        self.check_ai_packages()
        self.check_optional_packages()
        self.check_port_conflicts()
        
        if self.problems:
            logger.warning(f"Found {len(self.problems)} problems")
            for i, problem in enumerate(self.problems, 1):
                logger.warning(f"Problem {i}: {problem}")
                
            if self.fixes_applied:
                logger.info(f"Applied {len(self.fixes_applied)} fixes")
                for i, fix in enumerate(self.fixes_applied, 1):
                    logger.info(f"Fix {i}: {fix}")
            
            return False
        else:
            logger.info("All dependency checks passed!")
            return True
    
    def check_venv(self):
        """Check if running in a virtual environment"""
        if not self.venv_active:
            self.problems.append("Not running in a virtual environment")
            logger.warning("Not running in a virtual environment. This may cause conflicts.")
            
            if self.auto_fix:
                venv_path = Path("fresh_venv")
                if venv_path.exists():
                    logger.info("Virtual environment 'fresh_venv' exists but is not activated")
                    self.fixes_applied.append("Please activate the virtual environment with 'source fresh_venv/bin/activate'")
                else:
                    logger.info("Creating new virtual environment 'fresh_venv'")
                    try:
                        subprocess.check_call([sys.executable, "-m", "venv", "fresh_venv"])
                        self.fixes_applied.append("Created virtual environment 'fresh_venv'")
                        self.fixes_applied.append("Please activate it with 'source fresh_venv/bin/activate' and run this script again")
                    except subprocess.SubprocessError:
                        logger.error("Failed to create virtual environment")
    
    def check_python_version(self):
        """Check Python version compatibility"""
        major, minor, _ = map(int, self.python_version.split('.'))
        
        if major < 3 or (major == 3 and minor < 8):
            self.problems.append(f"Python version {self.python_version} is too old (minimum 3.8 required)")
        elif major > 3 or (major == 3 and minor > 12):
            logger.warning(f"Python version {self.python_version} is newer than officially supported (3.8-3.12 recommended)")
            
            # Known tokenizers compatibility issue with Python 3.13
            if major == 3 and minor >= 13:
                tokenizers_issue = self.check_package_available("tokenizers")
                if tokenizers_issue:
                    logger.warning("Potential compatibility issue with tokenizers on Python 3.13")
                    
                    if self.auto_fix:
                        logger.info("Attempting to work around tokenizers issues")
                        try:
                            subprocess.check_call([
                                sys.executable, "-m", "pip", "install", 
                                "git+https://github.com/huggingface/tokenizers.git"
                            ])
                            self.fixes_applied.append("Installed tokenizers from source")
                        except subprocess.SubprocessError:
                            logger.error("Failed to install tokenizers from source")
                            self.problems.append("Could not resolve tokenizers compatibility with Python 3.13")

    def check_package_available(self, package):
        """Check if a package is available and get its version"""
        try:
            spec = importlib.util.find_spec(package)
            if spec is None:
                return f"Package {package} not installed"
            
            if package == "tokenizers":
                # Special check for tokenizers functionality
                try:
                    import tokenizers
                    # More resilient version detection
                    try:
                        version = tokenizers.__version__
                    except AttributeError:
                        try:
                            version = tokenizers.version.__version__
                        except (AttributeError, ImportError):
                            version = "unknown"
                    
                    self.package_versions[package] = version
                    return None
                except ImportError as e:
                    return f"Package {package} cannot be imported: {e}"
            else:
                # Standard package
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    version = module.__version__
                elif hasattr(module, 'version'):
                    version = module.version
                else:
                    version = "unknown"
                
                self.package_versions[package] = version
                return None
            
        except ImportError as e:
            return f"Error importing {package}: {e}"

    def check_core_packages(self):
        """Check core packages required for Minerva to function"""
        for package in self.core_packages:
            issue = self.check_package_available(package)
            if issue:
                self.problems.append(issue)
                
                if self.auto_fix:
                    logger.info(f"Attempting to install missing core package: {package}")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                        self.fixes_applied.append(f"Installed {package}")
                    except subprocess.SubprocessError:
                        logger.error(f"Failed to install {package}")
    
    def check_ai_packages(self):
        """Check AI-related packages"""
        for package in self.ai_packages:
            issue = self.check_package_available(package)
            if issue:
                self.problems.append(issue)
                
                if self.auto_fix:
                    if package == "tokenizers":
                        logger.info("Attempting to fix tokenizers package")
                        try:
                            # Special handling for tokenizers
                            subprocess.check_call([
                                sys.executable, "-m", "pip", "uninstall", "-y", "tokenizers"
                            ])
                            
                            # Try different versions based on Python version
                            major, minor, _ = map(int, self.python_version.split('.'))
                            if major == 3 and minor >= 13:
                                # For Python 3.13+, try the latest version
                                subprocess.check_call([
                                    sys.executable, "-m", "pip", "install",
                                    "git+https://github.com/huggingface/tokenizers.git"
                                ])
                            else:
                                # For older Python versions, use a stable version
                                subprocess.check_call([
                                    sys.executable, "-m", "pip", "install", "tokenizers==0.13.3"
                                ])
                            
                            self.fixes_applied.append("Reinstalled tokenizers package")
                        except subprocess.SubprocessError:
                            logger.error("Failed to fix tokenizers package")
                    else:
                        # Standard installation
                        logger.info(f"Attempting to install missing AI package: {package}")
                        try:
                            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                            self.fixes_applied.append(f"Installed {package}")
                        except subprocess.SubprocessError:
                            logger.error(f"Failed to install {package}")
    
    def check_optional_packages(self):
        """Check optional packages"""
        for package in self.optional_packages:
            issue = self.check_package_available(package)
            if issue:
                logger.info(f"Optional package {package} not available: {issue}")
                
                if self.auto_fix:
                    logger.info(f"Attempting to install optional package: {package}")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                        self.fixes_applied.append(f"Installed optional package {package}")
                    except subprocess.SubprocessError:
                        logger.warning(f"Failed to install optional package {package}")
    
    def check_port_conflicts(self):
        """Check for port conflicts on the default Minerva port (5000)"""
        port = 5000  # Default Minerva port
        
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('localhost', port))
            # Port is available
            logger.info(f"Port {port} is available for use")
        except socket.error:
            self.problems.append(f"Port {port} is already in use")
            logger.warning(f"Port {port} is already in use")
            
            if self.auto_fix:
                if self.system == "Darwin" or self.system == "Linux":
                    logger.info(f"Checking processes using port {port}")
                    try:
                        result = subprocess.check_output(f"lsof -i :{port} -t", shell=True).decode('utf-8').strip()
                        if result:
                            pids = [int(pid) for pid in result.split('\n')]
                            logger.info(f"Found processes using port {port}: {pids}")
                            
                            # Try to identify Minerva processes
                            for pid in pids:
                                try:
                                    cmd_result = subprocess.check_output(f"ps -p {pid} -o command=", shell=True).decode('utf-8').strip()
                                    if "minerva" in cmd_result.lower() or "run_minerva.py" in cmd_result.lower():
                                        logger.info(f"Process {pid} appears to be a Minerva process: {cmd_result}")
                                        logger.info(f"You may want to kill it with: kill -9 {pid}")
                                    else:
                                        logger.info(f"Process {pid} using port {port}: {cmd_result}")
                                except subprocess.SubprocessError:
                                    logger.warning(f"Could not get command for PID {pid}")
                    except subprocess.SubprocessError:
                        logger.warning(f"Could not check processes using port {port}")
                
                self.fixes_applied.append(f"Try using a different port with --port option when starting Minerva")
        finally:
            s.close()
    
    def print_report(self):
        """Print dependency report"""
        print("\n==== Minerva Dependency Report ====")
        print(f"Python: {self.python_version}")
        print(f"System: {self.system}")
        print(f"Virtual Environment: {'Active' if self.venv_active else 'Not Active'}")
        
        print("\nPackage Versions:")
        for package, version in self.package_versions.items():
            print(f"  {package}: {version}")
        
        if self.problems:
            print("\nProblems Detected:")
            for i, problem in enumerate(self.problems, 1):
                print(f"  {i}. {problem}")
        else:
            print("\nNo problems detected!")
        
        if self.fixes_applied:
            print("\nFixes Applied:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")

def main():
    """Main function to run the dependency checker"""
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Check and fix dependencies for Minerva')
    parser.add_argument('--no-fix', action='store_true', help='Only check dependencies, do not attempt to fix issues')
    args = parser.parse_args()
    
    # Run checks
    checker = DependencyChecker(auto_fix=not args.no_fix)
    checker.check_all()
    checker.print_report()

if __name__ == "__main__":
    main()
