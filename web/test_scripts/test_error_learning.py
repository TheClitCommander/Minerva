#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Script for Error Learning System

This script tests Minerva's ability to learn from errors and automatically
improve its responses over time using the self-learning system.
"""

import os
import sys
import logging
import time
import uuid
import json
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("error_learning_test")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components for testing
try:
    from integrations.error_monitoring import (
        detect_response_errors,
        learn_from_errors,
        error_monitor,
        record_retry_outcome
    )
    error_monitoring_available = True
except ImportError as e:
    logger.warning(f"Error monitoring not available for testing: {e}")
    error_monitoring_available = False

try:
    from integrations.self_learning import (
        add_new_knowledge,
        verify_and_update_knowledge,
        get_all_knowledge_entries,
        track_model_performance
    )
    self_learning_available = True
except ImportError as e:
    logger.warning(f"Self-learning system not available for testing: {e}")
    self_learning_available = False


class TestData:
    """Test data for error learning scenarios"""
    
    # Common query types for testing
    QUERIES = {
        "factual": [
            "What is the capital of France?",
            "When was the first moon landing?",
            "Who wrote Pride and Prejudice?",
            "What is the population of Tokyo?",
            "What elements make up water?"
        ],
        "technical": [
            "How do I create a binary search tree in Python?",
            "Explain how HTTPS encryption works",
            "What's the difference between REST and GraphQL?",
            "How does garbage collection work in Java?",
            "Explain the time complexity of quicksort"
        ],
        "creative": [
            "Write a short poem about artificial intelligence",
            "Create a short story about time travel",
            "Imagine a world where humans can photosynthesize",
            "Write a haiku about the moon",
            "Describe an alien civilization unlike any in science fiction"
        ],
        "reasoning": [
            "How might quantum computing affect cybersecurity?",
            "What are the ethical implications of genetic engineering?",
            "How could cities be redesigned to be more sustainable?",
            "What might be the long-term effects of remote work?",
            "How could education systems better prepare students for the future?"
        ]
    }
    
    # Common error types for testing
    ERROR_RESPONSES = {
        "refusal": [
            "I'm sorry, but I cannot assist with that request.",
            "I apologize, but I'm not able to provide that information.",
            "I don't feel comfortable responding to that query.",
            "Sorry, I can't help with that specific request.",
            "I'm unable to provide the requested information."
        ],
        "self_reference": [
            "As an AI language model, I don't have access to that information.",
            "As an AI, I don't have the ability to browse the internet.",
            "I'm an AI assistant created by a team of engineers.",
            "As a language model, my knowledge has a cutoff date.",
            "I don't have personal experiences as I'm an AI."
        ],
        "hallucination": [
            "The city of Xanadu is the capital of France, known for its beautiful Eiffel Tower.",
            "The first moon landing occurred in 1962 when Neil Armstrong and Edwin Aldrin landed.",
            "Pride and Prejudice was written by Charlotte Dickens in 1832.",
            "Tokyo has a population of 72 million people as of the 2020 census.",
            "Water is composed of hydrogen, oxygen, and nitrogen atoms."
        ],
        "incomplete": [
            "The capital of France is",
            "The moon landing occurred",
            "Pride and Prejudice was",
            "Tokyo's population is approximately",
            "Water consists of"
        ],
        "uncertain": [
            "I think the capital of France might be Paris, but I'm not entirely sure.",
            "If I recall correctly, the moon landing was probably in the late 1960s.",
            "I believe Pride and Prejudice was written by Jane Austen, but I could be wrong.",
            "Tokyo's population is maybe around 10-30 million, I'm not certain.",
            "I'm pretty sure water has hydrogen and oxygen, but I might be missing something."
        ]
    }
    
    # Model names for testing
    MODELS = [
        "gpt4",
        "claude3",
        "gemini",
        "mistral7b",
        "llama2"
    ]
    
    @classmethod
    def get_random_query(cls, query_type=None):
        """Get a random query of the specified type"""
        import random
        
        if query_type is None:
            query_type = random.choice(list(cls.QUERIES.keys()))
            
        return random.choice(cls.QUERIES[query_type])
    
    @classmethod
    def get_random_error_response(cls, error_type=None):
        """Get a random error response of the specified type"""
        import random
        
        if error_type is None:
            error_type = random.choice(list(cls.ERROR_RESPONSES.keys()))
            
        return random.choice(cls.ERROR_RESPONSES[error_type])
    
    @classmethod
    def get_random_model(cls):
        """Get a random model name"""
        import random
        return random.choice(cls.MODELS)


def test_error_detection_accuracy():
    """Test the accuracy of error detection across different error types"""
    if not error_monitoring_available:
        logger.warning("Error monitoring not available, skipping test")
        return False
        
    logger.info("Testing error detection accuracy...")
    
    results = {
        "total": 0,
        "correct": 0,
        "by_type": {}
    }
    
    # Test each error type
    for error_type, responses in TestData.ERROR_RESPONSES.items():
        results["by_type"][error_type] = {"total": 0, "correct": 0}
        
        for response in responses:
            query = TestData.get_random_query()
            model = TestData.get_random_model()
            
            # Detect errors
            error_result = error_monitor.detect_errors(query, response, model)
            
            results["total"] += 1
            results["by_type"][error_type]["total"] += 1
            
            # Check if correctly identified
            has_error = error_result.get("has_error", False)
            detected_type = error_result.get("error_type", "")
            
            if has_error and (detected_type == error_type or detected_type in error_type):
                results["correct"] += 1
                results["by_type"][error_type]["correct"] += 1
                logger.info(f"Correctly identified {error_type} error in response")
            else:
                logger.warning(f"Failed to identify {error_type} error. Detected: {detected_type}")
                logger.warning(f"Response: {response[:50]}...")
                
    # Calculate accuracy
    overall_accuracy = results["correct"] / results["total"] if results["total"] > 0 else 0
    logger.info(f"Overall error detection accuracy: {overall_accuracy:.2f}")
    
    # Report by type
    for error_type, counts in results["by_type"].items():
        type_accuracy = counts["correct"] / counts["total"] if counts["total"] > 0 else 0
        logger.info(f"  {error_type} accuracy: {type_accuracy:.2f} ({counts['correct']}/{counts['total']})")
        
    return results


def test_learn_from_errors():
    """Test the system's ability to learn from errors"""
    if not error_monitoring_available or not hasattr(error_monitor, "learn_from_errors"):
        logger.warning("Error learning not available, skipping test")
        return False
        
    if not self_learning_available:
        logger.warning("Self-learning system not available, skipping test")
        return False
    
    logger.info("Testing learn from errors functionality...")
    
    results = {
        "attempted": 0,
        "successful": 0,
        "by_type": {}
    }
    
    # Test learning from different error types
    for error_type, responses in TestData.ERROR_RESPONSES.items():
        results["by_type"][error_type] = {"attempted": 0, "successful": 0}
        
        # Test with 2 samples of each error type
        for response in responses[:2]:
            query = TestData.get_random_query()
            model = TestData.get_random_model()
            
            results["attempted"] += 1
            results["by_type"][error_type]["attempted"] += 1
            
            # Try to learn from the error
            try:
                test_id = str(uuid.uuid4())[:8]  # Generate a unique test ID
                
                learning_result = learn_from_errors(
                    query=query,
                    response=response,
                    error_type=error_type,
                    model=model,
                    test_id=test_id
                )
                
                if learning_result.get("success", False):
                    knowledge_id = learning_result.get("knowledge_id")
                    results["successful"] += 1
                    results["by_type"][error_type]["successful"] += 1
                    logger.info(f"Successfully learned from {error_type} error: {knowledge_id}")
                else:
                    logger.warning(f"Failed to learn from {error_type} error: {learning_result.get('error')}")
            except Exception as e:
                logger.error(f"Error during learning process: {str(e)}")
                
    # Calculate success rate
    success_rate = results["successful"] / results["attempted"] if results["attempted"] > 0 else 0
    logger.info(f"Overall learning success rate: {success_rate:.2f} ({results['successful']}/{results['attempted']})")
    
    # Report by type
    for error_type, counts in results["by_type"].items():
        type_rate = counts["successful"] / counts["attempted"] if counts["attempted"] > 0 else 0
        logger.info(f"  {error_type} learning rate: {type_rate:.2f} ({counts['successful']}/{counts['attempted']})")
        
    return results


def test_retry_outcome_recording():
    """Test recording retry outcomes for learning"""
    if not error_monitoring_available or not hasattr(error_monitor, "record_retry_outcome"):
        logger.warning("Retry outcome recording not available, skipping test")
        return False
        
    logger.info("Testing retry outcome recording...")
    
    # Generate test data
    queries = [TestData.get_random_query() for _ in range(5)]
    models = [TestData.get_random_model() for _ in range(5)]
    error_types = list(TestData.ERROR_RESPONSES.keys())
    
    results = {
        "recorded": 0,
        "successful": 0
    }
    
    # Record some successful retries
    for i in range(5):
        query = queries[i]
        original_model = models[i]
        error_type = error_types[i % len(error_types)]
        retry_model = models[(i + 2) % len(models)]
        
        # 60% success rate for test
        success = (i % 5) < 3
        strategy = "model_switch" if i % 2 == 0 else "query_reformulation"
        
        try:
            record_result = record_retry_outcome(
                query=query,
                original_model=original_model,
                error_type=error_type,
                retry_model=retry_model,
                success=success,
                strategy=strategy,
                test_id=f"test-{i}"
            )
            
            results["recorded"] += 1
            
            if record_result.get("success", False):
                results["successful"] += 1
                logger.info(f"Successfully recorded retry outcome {i+1}/5")
            else:
                logger.warning(f"Failed to record retry outcome: {record_result.get('error')}")
        except Exception as e:
            logger.error(f"Error recording retry outcome: {str(e)}")
    
    # Calculate success rate
    success_rate = results["successful"] / results["recorded"] if results["recorded"] > 0 else 0
    logger.info(f"Retry recording success rate: {success_rate:.2f} ({results['successful']}/{results['recorded']})")
    
    return results


def test_integrate_with_self_learning():
    """Test integration with the self-learning system"""
    if not self_learning_available or not error_monitoring_available:
        logger.warning("Required components not available, skipping integration test")
        return False
        
    logger.info("Testing integration with self-learning system...")
    
    # Check if we can add knowledge from error detection
    query = "What is the capital of France?"
    erroneous_response = "The capital of France is London, a beautiful city on the Seine River."
    model = "test_model"
    
    # 1. Detect error
    error_result = error_monitor.detect_errors(query, erroneous_response, model)
    
    if error_result.get("has_error", False):
        error_type = error_result.get("error_type")
        logger.info(f"Detected error: {error_type}")
        
        # 2. Learn from error
        try:
            learning_result = learn_from_errors(
                query=query,
                response=erroneous_response,
                error_type=error_type,
                model=model,
                test_id="integration-test"
            )
            
            if learning_result.get("success", False):
                knowledge_id = learning_result.get("knowledge_id")
                logger.info(f"Successfully created knowledge entry: {knowledge_id}")
                
                # 3. Verify knowledge was added
                knowledge_entries = get_all_knowledge_entries()
                found = False
                
                for entry in knowledge_entries:
                    if entry.get("id") == knowledge_id:
                        found = True
                        logger.info(f"Verified knowledge entry exists: {json.dumps(entry, indent=2)}")
                        break
                
                if found:
                    logger.info("✅ Integration test successful!")
                    return True
                else:
                    logger.warning("Knowledge entry not found in database")
            else:
                logger.warning(f"Failed to learn from error: {learning_result.get('error')}")
        except Exception as e:
            logger.error(f"Error during integration test: {str(e)}")
    else:
        logger.warning("Failed to detect error in test response")
    
    logger.warning("❌ Integration test failed")
    return False


def run_all_tests():
    """Run all tests and return results"""
    results = {}
    
    print("=" * 80)
    print("TESTING ERROR LEARNING SYSTEM")
    print("=" * 80)
    
    # Check system status
    print(f"Error monitoring available: {error_monitoring_available}")
    print(f"Self-learning system available: {self_learning_available}")
    print("-" * 80)
    
    # Run tests if components available
    if error_monitoring_available:
        print("\nTEST 1: Error Detection Accuracy")
        results["error_detection"] = test_error_detection_accuracy()
        
        print("\nTEST 2: Learning From Errors")
        results["error_learning"] = test_learn_from_errors()
        
        print("\nTEST 3: Retry Outcome Recording")
        results["retry_recording"] = test_retry_outcome_recording()
        
        if self_learning_available:
            print("\nTEST 4: Integration With Self-Learning")
            results["integration"] = test_integrate_with_self_learning()
    else:
        print("Error monitoring system not available. Tests skipped.")
    
    # Summarize results
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if "error_detection" in results:
        detection_results = results["error_detection"]
        if isinstance(detection_results, dict) and "correct" in detection_results and "total" in detection_results:
            accuracy = detection_results["correct"] / detection_results["total"] if detection_results["total"] > 0 else 0
            print(f"Error Detection:      {'✅' if accuracy > 0.7 else '❌'} ({accuracy:.2f} accuracy)")
        else:
            print(f"Error Detection:      ❌ (Test failed)")
    else:
        print(f"Error Detection:      ⚠️ (Skipped)")
        
    if "error_learning" in results:
        learning_results = results["error_learning"]
        if isinstance(learning_results, dict) and "successful" in learning_results and "attempted" in learning_results:
            success_rate = learning_results["successful"] / learning_results["attempted"] if learning_results["attempted"] > 0 else 0
            print(f"Error Learning:       {'✅' if success_rate > 0.5 else '❌'} ({success_rate:.2f} success rate)")
        else:
            print(f"Error Learning:       ❌ (Test failed)")
    else:
        print(f"Error Learning:       ⚠️ (Skipped)")
        
    if "retry_recording" in results:
        retry_results = results["retry_recording"]
        if isinstance(retry_results, dict) and "successful" in retry_results and "recorded" in retry_results:
            success_rate = retry_results["successful"] / retry_results["recorded"] if retry_results["recorded"] > 0 else 0
            print(f"Retry Recording:      {'✅' if success_rate > 0.5 else '❌'} ({success_rate:.2f} success rate)")
        else:
            print(f"Retry Recording:      ❌ (Test failed)")
    else:
        print(f"Retry Recording:      ⚠️ (Skipped)")
        
    if "integration" in results:
        integration_success = results["integration"]
        print(f"Self-Learning Integration: {'✅' if integration_success else '❌'}")
    else:
        print(f"Self-Learning Integration: ⚠️ (Skipped)")
        
    print("=" * 80)
    

if __name__ == "__main__":
    run_all_tests()
