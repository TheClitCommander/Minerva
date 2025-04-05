"""
Minerva AI - Error Handlers

This module provides error handling functionality for the web interface.
"""

import sys
import traceback
import logging
from functools import wraps
from flask import jsonify, render_template, current_app, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('minerva_errors.log')
    ]
)
logger = logging.getLogger('minerva.errors')


class MinervaError(Exception):
    """Base exception class for Minerva errors."""
    
    def __init__(self, message, status_code=500, details=None):
        """
        Initialize a new MinervaError.
        
        Args:
            message (str): Human-readable error message
            status_code (int, optional): HTTP status code. Defaults to 500.
            details (dict, optional): Additional error details. Defaults to None.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self):
        """
        Convert error to a dictionary representation.
        
        Returns:
            dict: Dictionary representation of the error
        """
        error_dict = {
            "error": self.message,
            "success": False,
            "status_code": self.status_code,
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class DocumentProcessingError(MinervaError):
    """Raised when document processing fails."""
    
    def __init__(self, message, document_path=None, details=None):
        """
        Initialize a new DocumentProcessingError.
        
        Args:
            message (str): Human-readable error message
            document_path (str, optional): Path to the document that failed processing
            details (dict, optional): Additional error details
        """
        super().__init__(message, status_code=500, details=details)
        if document_path:
            self.details["document_path"] = document_path


class DocumentNotFoundError(MinervaError):
    """Raised when a requested document is not found."""
    
    def __init__(self, document_id):
        """
        Initialize a new DocumentNotFoundError.
        
        Args:
            document_id (str): ID of the document that was not found
        """
        super().__init__(
            f"Document not found: {document_id}",
            status_code=404,
            details={"document_id": document_id}
        )


class InvalidRequestError(MinervaError):
    """Raised when a request is invalid."""
    
    def __init__(self, message, validation_errors=None):
        """
        Initialize a new InvalidRequestError.
        
        Args:
            message (str): Human-readable error message
            validation_errors (dict, optional): Dictionary of validation errors
        """
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
        super().__init__(message, status_code=400, details=details)


def handle_api_error(func):
    """
    Decorator for API routes to handle exceptions consistently.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MinervaError as e:
            logger.error(f"API Error: {str(e)}", exc_info=True)
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error in API: {str(e)}", exc_info=True)
            error = MinervaError(
                "An unexpected error occurred",
                details={"exception": str(e)}
            )
            return jsonify(error.to_dict()), 500
    return wrapper


def register_error_handlers(app):
    """
    Register error handlers with the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Resource not found",
                "success": False,
                "status_code": 404
            }), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        logger.error(f"Server error: {str(error)}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({
                "error": "Internal server error",
                "success": False,
                "status_code": 500
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(MinervaError)
    def handle_minerva_error(error):
        """Handle Minerva-specific errors."""
        logger.error(f"Minerva error: {str(error)}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify(error.to_dict()), error.status_code
        return render_template(
            'errors/generic.html', 
            error_message=error.message,
            status_code=error.status_code
        ), error.status_code


def log_error(error, context=None):
    """
    Log an error with optional context.
    
    Args:
        error (Exception): The exception to log
        context (dict, optional): Additional context information
    """
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc()
    }
    
    if context:
        error_info.update(context)
    
    logger.error(f"Error: {error_info['error_message']}", extra=error_info, exc_info=True)
