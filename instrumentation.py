#!/usr/bin/env python3
"""
Minerva Instrumentation Module

This module contains functions for instrumenting the Minerva codebase with logging.
"""

import os
import sys
import inspect
import importlib.util
import logging

# Get the root logger
logger = logging.getLogger(__name__)

def instrument_module(module_path, instrumentation_code):
    """
    Instrument a module with the provided code.
    
    Args:
        module_path: Path to the module file.
        instrumentation_code: Code to inject into the module.
    
    Returns:
        bool: Whether the instrumentation was successful.
    """
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
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_end = i
        
        # Insert the instrumentation code after the imports
        modified_lines = lines[:import_end+1] + ['', instrumentation_code] + lines[import_end+1:]
        modified_content = '\n'.join(modified_lines)
        
        # Write the modified content back to the file
        with open(module_path, 'w') as f:
            f.write(modified_content)
        
        logger.info(f"Successfully instrumented module {module_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to instrument module {module_path}: {str(e)}")
        return False

def main():
    """Main function to instrument the Minerva codebase."""
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
