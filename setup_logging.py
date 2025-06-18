#!/usr/bin/env python3
"""
Minerva Enhanced Logging Setup

This script sets up comprehensive logging for monitoring the performance and behavior
of the enhanced Hugging Face functions in production.
"""

import os
import sys
import json
import logging
import logging.config
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# Define the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Define log directory paths
LOG_DIR = os.path.join(project_root, "logs")
CONFIG_DIR = os.path.join(project_root, "config")

# Ensure these directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Default logging configuration
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
        },
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(pathname)s:%(lineno)d %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file_standard": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": os.path.join(LOG_DIR, "minerva.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf8"
        },
        "file_errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": os.path.join(LOG_DIR, "errors.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf8"
        },
        "file_models": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": os.path.join(LOG_DIR, "models.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf8"
        },
        "file_performance": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": os.path.join(LOG_DIR, "performance.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file_standard", "file_errors"],
            "level": "INFO",
            "propagate": True
        },
        "minerva.models": {  # Logger for model-related operations
            "handlers": ["console", "file_models"],
            "level": "INFO",
            "propagate": False
        },
        "minerva.huggingface": {  # Logger for Hugging Face operations
            "handlers": ["console", "file_models"],
            "level": "INFO",
            "propagate": False
        },
        "minerva.performance": {  # Logger for performance metrics
            "handlers": ["console", "file_performance"],
            "level": "INFO",
            "propagate": False
        }
    }
}

def setup_logging(config: Optional[Dict[str, Any]] = None, verbose: bool = False) -> Dict[str, Any]:
    """
    Set up logging configuration for Minerva.

    Args:
        config: Optional logging configuration dictionary.
        verbose: Whether to enable verbose (DEBUG) logging.

    Returns:
        The active logging configuration.
    """
    if config is None:
        config = DEFAULT_LOGGING_CONFIG
    
    # Modify log levels if verbose mode is enabled
    if verbose:
        config["handlers"]["console"]["level"] = "DEBUG"
        config["loggers"][""]["level"] = "DEBUG"
        config["loggers"]["minerva.models"]["level"] = "DEBUG"
        config["loggers"]["minerva.huggingface"]["level"] = "DEBUG"
        config["loggers"]["minerva.performance"]["level"] = "DEBUG"
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Log the startup information
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    if verbose:
        logger.debug("Verbose logging enabled")
    
    return config

def create_instrumentation_functions():
    """
    Create and inject instrumentation functions into the Minerva codebase.
    """
    # Get loggers for different components
    model_logger = logging.getLogger("minerva.models")
    huggingface_logger = logging.getLogger("minerva.huggingface")
    performance_logger = logging.getLogger("minerva.performance")
    
    # Define function to patch into web.app.py
    patch_code = """
# ===== START INSTRUMENTATION CODE =====
import time
import logging
from functools import wraps

# Get module-specific loggers
model_logger = logging.getLogger("minerva.models")
huggingface_logger = logging.getLogger("minerva.huggingface")
performance_logger = logging.getLogger("minerva.performance")

def log_function_call(logger):
    \"\"\"Decorator to log function calls with timing information.\"\"\"
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Log the function call
            logger.info(f"CALL {func.__name__} - Started")
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                
                # Log the successful completion
                logger.info(f"CALL {func.__name__} - Completed in {elapsed_time:.4f}s")
                
                # Log more detailed performance metrics for specific functions
                if func.__name__ == "process_huggingface_only":
                    # Extract the query from args or kwargs
                    query = args[0] if args else kwargs.get("message", "Unknown query")
                    query_length = len(query) if isinstance(query, str) else 0
                    
                    # Log detailed performance data
                    performance_logger.info(
                        f"PERF {func.__name__} - "
                        f"Query: '{query[:50]}{'...' if len(query) > 50 else ''}', "
                        f"Length: {query_length}, "
                        f"Time: {elapsed_time:.4f}s"
                    )
                
                return result
            except Exception as e:
                # Calculate elapsed time
                elapsed_time = time.time() - start_time
                
                # Log the error
                logger.error(
                    f"CALL {func.__name__} - Failed after {elapsed_time:.4f}s: {str(e)}",
                    exc_info=True
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator

# Apply the decorator to key functions
original_process_huggingface_only = process_huggingface_only
process_huggingface_only = log_function_call(huggingface_logger)(original_process_huggingface_only)

original_optimize_generation_parameters = optimize_generation_parameters
optimize_generation_parameters = log_function_call(model_logger)(original_optimize_generation_parameters)

original_clean_ai_response = clean_ai_response
clean_ai_response = log_function_call(model_logger)(original_clean_ai_response)

original_generate_fallback_response = generate_fallback_response
generate_fallback_response = log_function_call(model_logger)(original_generate_fallback_response)

# ===== END INSTRUMENTATION CODE =====
"""
    
    # Create the instrumentation script
    instrumentation_script = os.path.join(project_root, "instrumentation.py")
    with open(instrumentation_script, "w") as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Minerva Instrumentation Module

This module contains functions for instrumenting the Minerva codebase with logging.
\"\"\"

import os
import sys
import inspect
import importlib.util
import logging

# Get the root logger
logger = logging.getLogger(__name__)

def instrument_module(module_path, instrumentation_code):
    \"\"\"
    Instrument a module with the provided code.
    
    Args:
        module_path: Path to the module file.
        instrumentation_code: Code to inject into the module.
    
    Returns:
        bool: Whether the instrumentation was successful.
    \"\"\"
    try:
        # Read the module content
        with open(module_path, 'r') as f:
            content = f.read()
        
        # Check if the module is already instrumented
        if "# ===== START INSTRUMENTATION CODE =====" in content:
            logger.info(f"Module {module_path} is already instrumented.")
            return True
        
        # Find a suitable location to insert the instrumentation code
        # Here we look for import statements and add our code after them
        import_end = 0
        lines = content.split('\\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_end = i
        
        # Insert the instrumentation code after the imports
        modified_lines = lines[:import_end+1] + ['', instrumentation_code] + lines[import_end+1:]
        modified_content = '\\n'.join(modified_lines)
        
        # Write the modified content back to the file
        with open(module_path, 'w') as f:
            f.write(modified_content)
        
        logger.info(f"Successfully instrumented module {module_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument module {module_path}: {str(e)}")
        return False

def main():
    \"\"\"Main function to instrument the Minerva codebase.\"\"\"
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to key modules
    app_module = os.path.join(project_root, 'web', 'app.py')
    
    # Instrumentation code (normally imported from a string in setup_logging.py)
    with open(os.path.join(project_root, 'config', 'instrumentation_code.py')) as f:
        instrumentation_code = f.read()
    
    # Instrument the main application module
    success = instrument_module(app_module, instrumentation_code)
    
    if success:
        logger.info("Instrumentation completed successfully.")
    else:
        logger.error("Instrumentation failed.")

if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    main()
""")
    
    # Create the instrumentation code file
    os.makedirs(os.path.join(project_root, "config"), exist_ok=True)
    with open(os.path.join(project_root, "config", "instrumentation_code.py"), "w") as f:
        f.write(patch_code)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Created instrumentation script at {instrumentation_script}")
    logger.info(f"Created instrumentation code at {os.path.join(project_root, 'config', 'instrumentation_code.py')}")

def create_logging_config_file(config: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Create a logging configuration file.

    Args:
        config: The logging configuration.
        output_path: Optional path to write the configuration file.

    Returns:
        The path to the created configuration file.
    """
    if output_path is None:
        output_path = os.path.join(CONFIG_DIR, "logging_config.json")
    
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return output_path

def print_summary():
    """Print a summary of the logging setup."""
    print("\n\n")
    print("="*80)
    print("MINERVA ENHANCED LOGGING SETUP")
    print("="*80)
    print("The following logging components have been set up:")
    print("\n1. Log Files:")
    print(f"   - Main Log: {os.path.join(LOG_DIR, 'minerva.log')}")
    print(f"   - Error Log: {os.path.join(LOG_DIR, 'errors.log')}")
    print(f"   - Model Operations Log: {os.path.join(LOG_DIR, 'models.log')}")
    print(f"   - Performance Metrics Log: {os.path.join(LOG_DIR, 'performance.log')}")
    
    print("\n2. Loggers:")
    print("   - Root Logger: General application logging")
    print("   - minerva.models: Model-specific operations")
    print("   - minerva.huggingface: Hugging Face operations")
    print("   - minerva.performance: Performance metrics")
    
    print("\n3. Instrumentation:")
    print(f"   - Instrumentation Script: {os.path.join(project_root, 'instrumentation.py')}")
    print(f"   - Instrumentation Code: {os.path.join(project_root, 'config', 'instrumentation_code.py')}")
    
    print("\n4. Configuration:")
    print(f"   - Logging Config: {os.path.join(CONFIG_DIR, 'logging_config.json')}")
    
    print("\nTo apply instrumentation to the codebase, run:")
    print(f"   python {os.path.join(project_root, 'instrumentation.py')}")
    
    print("\nTo view logs in real-time, run:")
    print(f"   tail -f {os.path.join(LOG_DIR, 'minerva.log')}")
    print(f"   tail -f {os.path.join(LOG_DIR, 'performance.log')}")
    
    print("\nFor detailed error tracking, run:")
    print(f"   tail -f {os.path.join(LOG_DIR, 'errors.log')}")
    
    print("\n" + "="*80)

def main():
    """Set up enhanced logging for Minerva."""
    print("="*80)
    print("MINERVA ENHANCED LOGGING SETUP")
    print("="*80)
    print("Setting up comprehensive logging for monitoring Hugging Face functions")
    print("="*80)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up enhanced logging for Minerva")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--apply-instrumentation", action="store_true", help="Apply instrumentation to the codebase")
    args = parser.parse_args()
    
    # Set up logging
    config = setup_logging(verbose=args.verbose)
    
    # Create the logging configuration file
    config_path = create_logging_config_file(config)
    
    # Create instrumentation functions
    create_instrumentation_functions()
    
    # Apply instrumentation if requested
    if args.apply_instrumentation:
        instrumentation_script = os.path.join(project_root, "instrumentation.py")
        os.system(f"python {instrumentation_script}")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()
