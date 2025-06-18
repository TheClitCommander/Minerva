"""
A patching module for the response handler and ensemble validator in Minerva.
This script provides functions to ensure responses are properly formatted before validation.
"""

import logging
import json
from typing import Dict, Any, Union, List

logger = logging.getLogger(__name__)

def ensure_string_response(response: Union[str, Dict, Any]) -> str:
    """
    Ensures that a response is a properly formatted string.
    
    Args:
        response: The response object, which could be a string, dictionary, or other type
        
    Returns:
        A properly formatted string version of the response
    """
    if isinstance(response, str):
        return response
    
    if isinstance(response, dict):
        # Check if there's a 'content', 'text', or 'message' field in the dictionary
        if 'content' in response:
            return str(response['content'])
        elif 'text' in response:
            return str(response['text'])
        elif 'message' in response:
            return str(response['message'])
        else:
            # Return the entire dictionary as a formatted string
            try:
                return json.dumps(response, indent=2)
            except:
                return str(response)
    
    # For any other type, convert to string
    return str(response)

def patch_ensemble_validator():
    """
    Applies a runtime patch to the ensemble validator to handle dictionary responses.
    """
    try:
        from web.ensemble_validator import EnsembleValidator
        
        # Patch confidence_analysis to handle dictionary responses
        original_confidence_analysis = EnsembleValidator.confidence_analysis
        
        def patched_confidence_analysis(self, response):
            # Ensure response is a string
            response_str = ensure_string_response(response)
            return original_confidence_analysis(self, response_str)
        
        EnsembleValidator.confidence_analysis = patched_confidence_analysis
        logger.info("✅ Successfully patched EnsembleValidator.confidence_analysis")
        
        # Patch _has_similar_statement to handle dictionary responses
        original_has_similar = EnsembleValidator._has_similar_statement
        
        def patched_has_similar(self, statement, text):
            # Ensure both are strings
            statement_str = ensure_string_response(statement)
            text_str = ensure_string_response(text)
            return original_has_similar(self, statement_str, text_str)
        
        EnsembleValidator._has_similar_statement = patched_has_similar
        logger.info("✅ Successfully patched EnsembleValidator._has_similar_statement")
        
        # Patch rank_responses to handle dictionary responses
        original_rank_responses = EnsembleValidator.rank_responses
        
        def patched_rank_responses(self, responses, query=None, quality_scores=None, query_type=None):
            # Convert all responses to strings
            string_responses = {}
            for model, response in responses.items():
                string_responses[model] = ensure_string_response(response)
            return original_rank_responses(self, string_responses, query, quality_scores, query_type)
        
        EnsembleValidator.rank_responses = patched_rank_responses
        logger.info("✅ Successfully patched EnsembleValidator.rank_responses")
        
        # Also patch the probabilistic_consensus method
        original_probabilistic_consensus = EnsembleValidator.probabilistic_consensus
        
        def patched_probabilistic_consensus(self, responses, quality_scores=None, query_type=None):
            # Convert any dictionary responses to strings
            string_responses = {}
            for model, response in responses.items():
                string_responses[model] = ensure_string_response(response)
            return original_probabilistic_consensus(self, string_responses, quality_scores, query_type)
        
        EnsembleValidator.probabilistic_consensus = patched_probabilistic_consensus
        logger.info("✅ Successfully patched EnsembleValidator.probabilistic_consensus")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to patch ensemble validator: {e}")
        return False

if __name__ == "__main__":
    # Apply patches when run directly
    patch_ensemble_validator()
