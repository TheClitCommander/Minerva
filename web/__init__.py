"""
Minerva web package initialization.
This file makes the web directory a proper Python package.
"""

import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the current directory to the path for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import key components to expose at package level
coordinator = None
MultiAICoordinator = None

try:
    from .multi_ai_coordinator import MultiAICoordinator, coordinator
    logger.info("Successfully imported MultiAICoordinator and coordinator in web package __init__")
except ImportError as e:
    # Log warning but don't fail on import
    logger.warning(f"Could not import MultiAICoordinator in web package __init__: {e}")

# Expose components at package level
__all__ = ['MultiAICoordinator', 'coordinator']
