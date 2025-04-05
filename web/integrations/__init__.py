"""
AI Model Integration Package

This package contains modules for integrating with various AI model providers
and self-learning capabilities for Minerva's autonomous improvement system.

The package includes:
- Self-learning core functionality
- Error monitoring and detection
- Automatic retry and correction
- Memory and feedback systems
"""

import logging
logger = logging.getLogger(__name__)

# Import key functions from self_learning for external use
try:
    from .self_learning import (
        # Error detection and tracking
        log_error,
        get_common_errors,
        get_error_prone_models,
        
        # Self-optimization
        track_model_performance,
        analyze_model_performance,
        get_model_performance,
        optimize_model_selection,
        
        # Knowledge expansion
        add_new_knowledge,
        verify_and_update_knowledge,
        get_all_knowledge_entries,
        increment_knowledge_usage,
        
        # Integration with Think Tank
        adaptive_model_selection,
        generate_improvement_suggestions
    )
    logger.info("Self-learning core functions imported successfully")
except ImportError as e:
    logger.warning(f"Could not import some functions from self_learning: {str(e)}")

# Import enhanced error monitoring system
try:
    from .error_monitoring import (
        # Advanced error detection
        detect_response_errors,
        suggest_retry_strategy,
        reformulate_query,
        record_retry_outcome,
        learn_from_errors,
        
        # Error monitoring class
        error_monitor
    )
    logger.info("Error monitoring system imported successfully")
except ImportError as e:
    logger.warning(f"Could not import error monitoring system: {str(e)}")
    # Use original error detection if available
    try:
        from .self_learning import detect_response_errors
    except ImportError:
        pass

# Import retry and correction system
try:
    from .retry_correction import (
        # Automatic retry processing
        process_with_retry,
        
        # Correction utilities
        retry_correction
    )
    logger.info("Retry & correction system imported successfully")
except ImportError as e:
    logger.warning(f"Could not import retry correction system: {str(e)}")
    
    # Define fallback function if import fails
    def process_with_retry(query, model, available_models, query_processor, **kwargs):
        """Fallback function when retry system is unavailable"""
        logger.warning("Retry system not available - using direct processing")
        return {
            "response": query_processor(query, model),
            "model": model,
            "retry_performed": False
        }
