
# ===== START INSTRUMENTATION CODE =====
import time
import logging
from functools import wraps

# Get module-specific loggers
model_logger = logging.getLogger("minerva.models")
huggingface_logger = logging.getLogger("minerva.huggingface")
performance_logger = logging.getLogger("minerva.performance")

def log_function_call(logger):
    """Decorator to log function calls with timing information."""
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
