#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Error Handling and Retry Systems

This script tests Minerva's new error detection, monitoring, and automatic 
retry systems to ensure they properly handle problematic model responses.
"""

import os
import sys
import logging
import time
import unittest
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("error_handling_test")

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
# Make sure the web directory is in the path
web_dir = os.path.join(parent_dir, 'web')
if web_dir not in sys.path:
    sys.path.append(web_dir)

# Import components for testing
try:
    from web.integrations.error_monitoring import (
        detect_response_errors,
        error_monitor
    )
    error_monitoring_available = True
except ImportError as e:
    logger.warning(f"Error monitoring not available for testing: {e}")
    error_monitoring_available = False

try:
    from web.integrations.retry_correction import (
        process_with_retry,
        retry_correction,
        RetryCorrection
    )
    retry_system_available = True
except ImportError as e:
    logger.warning(f"Retry correction system not available for testing: {e}")
    retry_system_available = False


class ErrorDetectionTests(unittest.TestCase):
    """Tests for the enhanced error detection capabilities"""
    
    def setUp(self):
        self.test_queries = [
            "What is the capital of France?",
            "How do I implement a binary search tree in Python?",
            "Can you help me debug this code?",
            "Write a poem about artificial intelligence",
            "Explain quantum computing"
        ]
        
        # Example problematic responses for testing error detection
        self.error_responses = {
            "empty": "",
            "too_short": "Yes.",
            "refusal": "I'm sorry, but I cannot assist with that request.",
            "self_reference": "As an AI language model, I don't have access to that information.",
            "hallucination": "The city of Atlantis is located at coordinates 34.56° N, 12.78° W and was discovered in 1986 by Dr. James Smith.",
            "repetitive": "This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test. This is a test.",
            "truncated": "The main principles of quantum computing are based on quantum mechanics and include superposition and entanglement. Superposition allows quantum bits (qubits) to exist in multiple states simultaneously, while entanglement allows qubits to be correlated in ways that",
            "good": "Paris is the capital of France. It's known as the 'City of Light' and is famous for landmarks such as the Eiffel Tower, the Louvre Museum, and Notre-Dame Cathedral. Paris is located in the north-central part of France on the Seine River."
        }
        
    def test_basic_error_detection(self):
        """Test basic error detection capabilities"""
        if not error_monitoring_available:
            self.skipTest("Error monitoring system not available")
            
        # Test each error response type
        query = "What is the capital of France?"
        model = "test_model"
        
        for error_type, response in self.error_responses.items():
            with self.subTest(error_type=error_type):
                result = detect_response_errors(query, response, model)
                
                if error_type == "good":
                    self.assertFalse(result.get("has_error", False), 
                                    f"Good response wrongly flagged as error: {result}")
                else:
                    self.assertTrue(result.get("has_error", False), 
                                   f"Failed to detect {error_type} error")
                    logger.info(f"Detected {error_type} error: {result}")
    
    def test_error_monitor_object(self):
        """Test the error monitor object for more advanced detection"""
        if not error_monitoring_available or not hasattr(error_monitor, "detect_errors"):
            self.skipTest("Advanced error monitoring not available")
            
        # Test with a few error types
        for error_type in ["refusal", "self_reference", "good"]:
            response = self.error_responses[error_type]
            result = error_monitor.detect_errors(
                "What is the capital of France?", 
                response, 
                "test_model"
            )
            
            if error_type == "good":
                self.assertFalse(result.get("has_error", False),
                                f"Good response wrongly flagged: {result}")
            else:
                self.assertTrue(result.get("has_error", False),
                               f"Failed to detect {error_type}")
                self.assertIn("confidence", result, 
                             "Error detection missing confidence score")
                self.assertGreater(result["confidence"], 0.5,
                                  "Low confidence in error detection")


class RetrySystemTests(unittest.TestCase):
    """Tests for the new automatic retry and correction system"""
    
    def setUp(self):
        # Create a mock query processor for testing
        def mock_processor(query, model):
            # Simulate different model behaviors
            if model == "error_model":
                return "I'm sorry, but I cannot assist with that request."
            elif model == "short_model":
                return "Yes."
            elif model == "hallucination_model":
                return "The population of France is 2.7 billion people."
            elif model == "good_model":
                return "Paris is the capital of France. It's located in the north-central part of the country."
            else:
                return "Test response from " + model
                
        self.mock_processor = mock_processor
        self.test_query = "What is the capital of France?"
        self.available_models = ["error_model", "short_model", "hallucination_model", "good_model", "backup_model"]
        
    def test_retry_correction_instance(self):
        """Test that the RetryCorrection class works properly"""
        if not retry_system_available:
            self.skipTest("Retry system not available")
            
        retry = RetryCorrection(max_retries=2)
        self.assertEqual(retry.max_retries, 2, "Failed to set max retries")
        
        # Test should_retry method
        self.assertTrue(
            retry.should_retry({"has_error": True, "confidence": 0.2}),
            "Should retry low confidence error"
        )
        
        self.assertTrue(
            retry.should_retry({"has_error": True, "error_type": "refusal", "confidence": 0.9}),
            "Should retry critical error types regardless of confidence"
        )
        
        self.assertFalse(
            retry.should_retry({"has_error": False}),
            "Should not retry when no error detected"
        )
        
    def test_process_with_retry(self):
        """Test the main process_with_retry function"""
        if not retry_system_available:
            self.skipTest("Retry system not available")
            
        # First test with an error model that should trigger retry
        result = process_with_retry(
            query=self.test_query,
            model="error_model",
            available_models=self.available_models,
            query_processor=self.mock_processor
        )
        
        # Should have performed retry and gotten a good response
        self.assertTrue(result.get("retry_performed", False),
                       "Retry was not performed for error model")
        
        if result.get("retry_success", False):
            # If retry succeeded, should have a good response and different model
            self.assertNotEqual(result.get("model"), "error_model",
                               "Still using error model after retry")
            logger.info(f"Successfully retried with model: {result.get('model')}")
        
        # Test with direct good model (should not retry)
        result = process_with_retry(
            query=self.test_query,
            model="good_model",
            available_models=self.available_models,
            query_processor=self.mock_processor
        )
        
        self.assertFalse(result.get("retry_performed", False),
                        "Performed unnecessary retry for good model")
        self.assertEqual(result.get("model"), "good_model",
                        "Model changed despite no retry")
        
    def test_automatic_correction(self):
        """Test automatic minor corrections without full retry"""
        if not retry_system_available:
            self.skipTest("Retry system not available")
            
        # Create response with self-reference
        self_ref_response = "As an AI language model, I don't have access to real-time data. However, based on my knowledge, Paris is the capital of France."
        
        # Create error result for self-reference
        error_result = {
            "has_error": True,
            "error_type": "self_reference",
            "description": "Response contains AI self-reference"
        }
        
        # Test correction
        corrected = retry_correction.correct_response(self_ref_response, error_result)
        
        # Should have removed the self-reference
        self.assertNotEqual(corrected, self_ref_response, 
                           "No correction was applied")
        self.assertNotIn("As an AI language model", corrected,
                        "Self-reference was not removed")
        logger.info(f"Corrected response: {corrected}")


class IntegrationTests(unittest.TestCase):
    """Integration tests for the error handling pipeline"""
    
    def setUp(self):
        # Define a mock model processor
        def mock_think_tank_processor(model_name, message):
            # Simulate different model failures based on message prefixes
            if message.startswith("EMPTY:"):
                return ""
            elif message.startswith("REFUSE:"):
                return "I'm sorry, but I cannot assist with that request."
            elif message.startswith("NONSENSE:"):
                return "Colorless green ideas sleep furiously in the quantum field."
            elif message.startswith("REFERENCE:"):
                return "As an AI, I don't have access to that information."
            else:
                # Generate a reasonable response
                return f"Response from {model_name}: This is a test response to demonstrate the error handling system."
                
        self.mock_processor = mock_think_tank_processor
        
    def test_end_to_end_error_handling(self):
        """Test the full error handling pipeline"""
        if not error_monitoring_available or not retry_system_available:
            self.skipTest("Full error handling pipeline not available")
            
        # Test with a query that should trigger error handling
        query = "REFUSE: What is the meaning of life?"
        
        # Mock function for process_with_retry to use
        def query_processor(query, model):
            return self.mock_processor(model, query)
            
        # Test the full process
        result = process_with_retry(
            query=query,
            model="test_model",
            available_models=["test_model", "backup_model1", "backup_model2"],
            query_processor=query_processor
        )
        
        # Verify the result
        self.assertTrue(result.get("retry_performed", False),
                       "Retry not performed for error case")
        logger.info(f"Full pipeline test result: {result}")


def run_tests():
    """Run all tests"""
    # Set up test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(ErrorDetectionTests))
    suite.addTests(loader.loadTestsFromTestCase(RetrySystemTests))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTING ERROR HANDLING AND RETRY SYSTEMS")
    print("=" * 80)
    
    # Check system status
    print(f"Error monitoring available: {error_monitoring_available}")
    print(f"Retry system available: {retry_system_available}")
    print("-" * 80)
    
    # Run tests
    result = run_tests()
    
    # Summarize results
    print("\n" + "=" * 80)
    print(f"SUMMARY: Ran {result.testsRun} tests")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 80)
