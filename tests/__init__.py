"""
Minerva AI - Test Suite

This package contains tests for various components of the Minerva AI system.

Includes tests for the refactored architecture:
- Core components (bin, core, models, memory, frameworks, server)
- Integration tests  
- Backward compatibility tests
"""

__version__ = "2.0.0"

# Import the main refactoring test suite
from .test_refactored_components import *
