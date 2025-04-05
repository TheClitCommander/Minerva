#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized Logging Configuration for Minerva

This module provides a unified logging configuration for the entire application,
with different log levels for production and development environments.
"""

import os
import logging
import logging.handlers
import time
from functools import wraps

# Get environment setting
ENV = os.environ.get('MINERVA_ENV', 'development').lower()

# Configure log levels based on environment
if ENV == 'production':
    DEFAULT_LOG_LEVEL = logging.WARNING  # Less verbose in production
    PERFORMANCE_CRITICAL_LOG_LEVEL = logging.ERROR  # Only log errors for performance-critical components
else:
    DEFAULT_LOG_LEVEL = logging.INFO  # More verbose in development
    PERFORMANCE_CRITICAL_LOG_LEVEL = logging.INFO

# These modules are performance-critical and should log less in production
PERFORMANCE_CRITICAL_MODULES = [
    'web.model_processors',
    'web.multi_ai_coordinator',
    'web.ensemble_validator',
    'web.response_generator',
    'web.think_tank_processor',
    'web.model_insights_manager'
]

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)

# Common log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Setup rotating file handler
file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(log_dir, 'minerva.log'), 
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

# Setup console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

def configure_logger(logger_name=None):
    """
    Configure a logger with the appropriate log level and handlers.
    
    Args:
        logger_name: Name of the logger to configure
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Set appropriate log level
    if logger_name in PERFORMANCE_CRITICAL_MODULES:
        logger.setLevel(PERFORMANCE_CRITICAL_LOG_LEVEL)
    else:
        logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def log_execution_time(logger=None):
    """
    Decorator to log function execution time for performance monitoring.
    Only logs if logger level is DEBUG or lower.
    
    Args:
        logger: Logger to use for logging, defaults to module logger
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided logger or get one for the function's module
            log = logger or logging.getLogger(func.__module__)
            
            # Only time the function if we're actually going to log it
            if log.isEnabledFor(logging.DEBUG):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                log.debug(f"Function '{func.__name__}' executed in {(end_time - start_time)*1000:.2f}ms")
                return result
            else:
                # Don't time the function if we're not going to log it
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Initialize root logger
root_logger = logging.getLogger()
root_logger.setLevel(DEFAULT_LOG_LEVEL)

# Clear any existing handlers
if root_logger.handlers:
    root_logger.handlers.clear()

# Add handlers to root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Configure basic logging
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[file_handler, console_handler]
)

print(f"[SYSTEM] Logging configured: Environment={ENV}, Default Level={logging.getLevelName(DEFAULT_LOG_LEVEL)}")
print(f"[SYSTEM] Performance-critical modules logging at {logging.getLevelName(PERFORMANCE_CRITICAL_LOG_LEVEL)}")
