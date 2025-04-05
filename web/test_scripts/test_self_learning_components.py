#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minerva Self-Learning Component Tests

This script tests each component of Minerva's self-learning system independently,
handling optional dependencies gracefully and providing detailed validation results.
"""

import os
import sys
import json
import time
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the correct paths to system path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.abspath(os.path.join(script_dir, ".."))
root_dir = os.path.abspath(os.path.join(web_dir, ".."))

# Add both web and root directories to path
sys.path.insert(0, web_dir)
sys.path.insert(0, root_dir)

# Ensure we can import from the integrations directory
import sys
web_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
integrations_dir = os.path.join(web_dir, 'integrations')
if integrations_dir not in sys.path:
    sys.path.insert(0, integrations_dir)

# Import directly from integrations package
try:
    from integrations.self_learning import (
        # Error detection and tracking
        detect_response_errors,
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
        adaptive_model_selection
    )
    from integrations.memory import (
        store_memory,
        retrieve_memory,
        add_knowledge as memory_add_knowledge,
        memory_system
    )
    from integrations.feedback import (
        record_user_feedback,
        get_model_performance as feedback_get_model_performance
    )
    
    logger.info("Successfully imported all required modules and functions")
except ImportError as e:
    logger.warning(f"Could not import some functions: {str(e)}")
except AttributeError as e:
    logger.warning(f"Some functions are missing: {str(e)}")

# Paths
DB_PATH = "./data/self_learning.db"

# Test data
TEST_MODELS = ["gpt-4", "claude-3", "mistral", "llama2"]
TEST_QUERY_TYPES = ["technical", "creative", "reasoning", "factual", "general"]

# Make sure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class TestResult:
    """Simple class to track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details = []
    
    def add_pass(self, test_name, message=None):
        self.passed += 1
        self.details.append({
            "test": test_name,
            "result": "PASS",
            "message": message
        })
        logger.info(f"✅ PASS: {test_name}" + (f" - {message}" if message else ""))
    
    def add_fail(self, test_name, message=None):
        self.failed += 1
        self.details.append({
            "test": test_name,
            "result": "FAIL",
            "message": message
        })
        logger.error(f"❌ FAIL: {test_name}" + (f" - {message}" if message else ""))
    
    def add_skip(self, test_name, message=None):
        self.skipped += 1
        self.details.append({
            "test": test_name,
            "result": "SKIP",
            "message": message
        })
        logger.warning(f"⚠️ SKIP: {test_name}" + (f" - {message}" if message else ""))
    
    def summary(self):
        total = self.passed + self.failed + self.skipped
        logger.info(f"\n===== TEST SUMMARY =====")
        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        logger.info(f"Skipped: {self.skipped}")
        return self.failed == 0

def test_db_setup():
    """Test the database setup for the self-learning system"""
    results = TestResult()
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if required tables exist
        tables = [
            "error_logs",
            "model_performance",
            "optimization_log",
            "knowledge_entries"
        ]
        
        for table in tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                results.add_pass(f"Database table '{table}' exists")
            else:
                results.add_fail(f"Database table '{table}' does not exist")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(error_logs)")
        columns = cursor.fetchall()
        required_columns = ["id", "error_type", "query", "model", "response", "error_message", "timestamp"]
        column_names = [col[1] for col in columns]
        
        for col in required_columns:
            if col in column_names:
                results.add_pass(f"Error logs table has '{col}' column")
            else:
                results.add_fail(f"Error logs table missing '{col}' column")
        
        conn.close()
        
    except Exception as e:
        results.add_fail("Database setup test", f"Exception: {str(e)}")
    
    return results

def test_error_detection_system():
    """Test the error detection system"""
    results = TestResult()
    
    try:
        # Check if the error detection function is available
        if 'detect_response_errors' not in globals():
            raise ImportError("detect_response_errors function not available")
        
        # Test cases
        test_cases = [
            {
                "name": "Refusal detection",
                "query": "How can I hack into a computer?",
                "response": "I'm sorry, I cannot assist with that request as it goes against ethical guidelines.",
                "expected_error": True,
                "expected_type": "refusal"
            },
            {
                "name": "Self-reference detection",
                "query": "What's happening in the world right now?",
                "response": "As an AI language model, I don't have access to real-time data beyond my training cutoff.",
                "expected_error": True,
                "expected_type": "self_reference"
            },
            {
                "name": "Empty response detection",
                "query": "Tell me about quantum computing",
                "response": "",
                "expected_error": True,
                "expected_type": "empty_response"
            },
            {
                "name": "Valid response passes",
                "query": "What is TCP/IP?",
                "response": "TCP/IP is a suite of communication protocols used to interconnect network devices on the internet.",
                "expected_error": False,
                "expected_type": None
            }
        ]
        
        for case in test_cases:
            has_error, error_type, _ = detect_response_errors(
                case["query"], 
                case["response"], 
                "test-model"
            )
            
            if has_error == case["expected_error"]:
                if has_error:
                    if error_type == case["expected_type"]:
                        results.add_pass(case["name"], f"Correctly detected {error_type}")
                    else:
                        results.add_fail(case["name"], f"Detected error but wrong type: {error_type} vs {case['expected_type']}")
                else:
                    results.add_pass(case["name"], "Correctly identified as valid response")
            else:
                results.add_fail(case["name"], 
                                f"Expected error={case['expected_error']}, got {has_error}")
                
    except ImportError:
        results.add_skip("Error detection tests", "detect_response_errors function not available")
    except Exception as e:
        results.add_fail("Error detection tests", f"Exception: {str(e)}")
    
    return results

def test_error_logging():
    """Test the error logging functionality"""
    results = TestResult()
    
    try:
        # Check if the error logging function is available
        if 'log_error' not in globals():
            raise ImportError("log_error function not available")
        
        # Test error logging
        error_id = log_error(
            error_type="test_error",
            query="Test query",
            model="test-model",
            response="Test response",
            error_message="This is a test error"
        )
        
        if error_id and isinstance(error_id, int):
            results.add_pass("Error logging", f"Error logged with ID: {error_id}")
            
            # Verify the error was logged in the database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM error_logs WHERE id = ?", (error_id,))
            logged_error = cursor.fetchone()
            conn.close()
            
            if logged_error:
                results.add_pass("Error database verification", "Error found in database")
            else:
                results.add_fail("Error database verification", "Error not found in database")
        else:
            results.add_fail("Error logging", "Failed to log error or invalid ID returned")
            
    except ImportError:
        results.add_skip("Error logging tests", "log_error function not available")
    except Exception as e:
        results.add_fail("Error logging tests", f"Exception: {str(e)}")
    
    return results

def test_model_performance_tracking():
    """Test the model performance tracking functionality"""
    results = TestResult()
    
    try:
        # Check if the performance tracking function is available
        if 'track_model_performance' not in globals():
            raise ImportError("track_model_performance function not available")
        
        # Test tracking for different models and query types
        for model in TEST_MODELS[:2]:  # Just test a couple models to keep it quick
            for query_type in TEST_QUERY_TYPES[:2]:  # Just test a couple query types
                entry_id = track_model_performance(
                    model=model,
                    query_type=query_type,
                    query=f"Sample {query_type} query",
                    response=f"Sample {model} response for {query_type} query",
                    feedback_score=0.85,
                    processing_time=1.2
                )
                
                if entry_id and isinstance(entry_id, int):
                    results.add_pass(
                        f"Performance tracking: {model}/{query_type}", 
                        f"Entry logged with ID: {entry_id}"
                    )
                    
                    # Verify the entry was logged in the database
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM model_performance WHERE id = ?", (entry_id,))
                    logged_entry = cursor.fetchone()
                    conn.close()
                    
                    if logged_entry:
                        results.add_pass(
                            f"Performance DB verification: {model}/{query_type}", 
                            "Entry found in database"
                        )
                    else:
                        results.add_fail(
                            f"Performance DB verification: {model}/{query_type}", 
                            "Entry not found in database"
                        )
                else:
                    results.add_fail(
                        f"Performance tracking: {model}/{query_type}", 
                        "Failed to log entry or invalid ID returned"
                    )
                    
    except ImportError:
        results.add_skip("Performance tracking tests", "track_model_performance function not available")
    except Exception as e:
        results.add_fail("Performance tracking tests", f"Exception: {str(e)}")
    
    return results

def test_knowledge_expansion():
    """Test the knowledge expansion functionality"""
    results = TestResult()
    
    try:
        # Check if the knowledge expansion functions are available
        for func_name in ['add_new_knowledge', 'verify_and_update_knowledge', 'get_all_knowledge_entries', 'increment_knowledge_usage']:
            if func_name not in globals():
                raise ImportError(f"{func_name} function not available")
        
        # Test adding new knowledge
        knowledge_id = add_new_knowledge(
            title="Test Knowledge Entry",
            content="This is a test knowledge entry for unit testing.",
            source="unit_test",
            confidence=0.9,
            verified=True
        )
        
        if knowledge_id and isinstance(knowledge_id, int):
            results.add_pass("Knowledge addition", f"Knowledge added with ID: {knowledge_id}")
            
            # Verify the knowledge was added in the database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_entries WHERE id = ?", (knowledge_id,))
            knowledge_entry = cursor.fetchone()
            conn.close()
            
            if knowledge_entry:
                results.add_pass("Knowledge DB verification", "Entry found in database")
            else:
                results.add_fail("Knowledge DB verification", "Entry not found in database")
            
            # Test updating knowledge
            success = verify_and_update_knowledge(
                knowledge_id=knowledge_id,
                verified=True,
                updated_content="This is an updated test knowledge entry."
            )
            
            if success:
                results.add_pass("Knowledge update", "Successfully updated knowledge entry")
            else:
                results.add_fail("Knowledge update", "Failed to update knowledge entry")
            
            # Test incrementing usage count
            success = increment_knowledge_usage(knowledge_id)
            
            if success:
                results.add_pass("Knowledge usage increment", "Successfully incremented usage count")
            else:
                results.add_fail("Knowledge usage increment", "Failed to increment usage count")
            
            # Test retrieving knowledge entries
            entries = get_all_knowledge_entries(verified_only=False)
            
            if entries and len(entries) > 0:
                results.add_pass("Knowledge retrieval", f"Retrieved {len(entries)} knowledge entries")
            else:
                results.add_fail("Knowledge retrieval", "No knowledge entries found")
                
        else:
            results.add_fail("Knowledge addition", "Failed to add knowledge or invalid ID returned")
            
    except ImportError:
        results.add_skip("Knowledge expansion tests", "Knowledge functions not available")
    except Exception as e:
        results.add_fail("Knowledge expansion tests", f"Exception: {str(e)}")
    
    return results

def test_model_analysis_and_optimization():
    """Test the model analysis and optimization functionality"""
    results = TestResult()
    
    try:
        # Check if the analysis and optimization functions are available
        for func_name in ['analyze_model_performance', 'optimize_model_selection']:
            if func_name not in globals():
                raise ImportError(f"{func_name} function not available")
        
        # Test analyzing model performance
        analysis = analyze_model_performance()
        
        if isinstance(analysis, dict) and "best_models_by_type" in analysis:
            results.add_pass("Model performance analysis", "Analysis returned expected structure")
            
            best_models = analysis.get("best_models_by_type", {})
            for query_type, model in best_models.items():
                results.add_pass(
                    f"Performance analysis detail: {query_type}", 
                    f"Best model: {model if model else 'None'}"
                )
        else:
            results.add_fail("Model performance analysis", "Analysis returned unexpected structure")
        
        # Test optimizing model selection
        optimization = optimize_model_selection(threshold=0.05)
        
        if isinstance(optimization, dict) and "optimizations" in optimization:
            results.add_pass("Model selection optimization", "Optimization returned expected structure")
            
            optimizations = optimization.get("optimizations", [])
            if optimizations:
                results.add_pass("Optimization details", f"Found {len(optimizations)} optimizations")
            else:
                results.add_pass("Optimization details", "No optimizations needed (expected if data is limited)")
        else:
            results.add_fail("Model selection optimization", "Optimization returned unexpected structure")
            
    except ImportError:
        results.add_skip("Model analysis tests", "Analysis functions not available")
    except Exception as e:
        results.add_fail("Model analysis tests", f"Exception: {str(e)}")
    
    return results

def test_adaptive_model_selection():
    """Test the adaptive model selection functionality"""
    results = TestResult()
    
    try:
        # Check if the adaptive model selection function is available
        if 'adaptive_model_selection' not in globals():
            raise ImportError("adaptive_model_selection function not available")
        
        # Test cases for different query types
        test_cases = [
            {
                "name": "Technical query selection",
                "query": "Explain how garbage collection works in Python.",
                "query_type": "technical",
            },
            {
                "name": "Creative query selection",
                "query": "Write a haiku about artificial intelligence.",
                "query_type": "creative",
            },
            {
                "name": "Reasoning query selection",
                "query": "Discuss the ethical implications of autonomous vehicles.",
                "query_type": "reasoning",
            }
        ]
        
        for case in test_cases:
            # Get model recommendation
            recommendation = adaptive_model_selection(
                query=case["query"],
                query_type=case["query_type"],
                available_models=TEST_MODELS
            )
            
            if isinstance(recommendation, dict) and "selected_model" in recommendation:
                selected_model = recommendation.get("selected_model")
                confidence = recommendation.get("confidence", 0)
                reason = recommendation.get("reason", "")
                
                if selected_model in TEST_MODELS:
                    results.add_pass(
                        case["name"], 
                        f"Selected {selected_model} with confidence {confidence:.2f}: {reason}"
                    )
                else:
                    results.add_fail(
                        case["name"],
                        f"Selected invalid model: {selected_model}"
                    )
            else:
                results.add_fail(
                    case["name"],
                    "Recommendation returned unexpected structure"
                )
                
    except ImportError:
        results.add_skip("Adaptive model selection tests", "adaptive_model_selection function not available")
    except Exception as e:
        results.add_fail("Adaptive model selection tests", f"Exception: {str(e)}")
    
    return results

def test_think_tank_integration():
    """Test the integration with the Think Tank processor"""
    results = TestResult()
    
    try:
        # Import the Think Tank processor
        from think_tank_processor import process_with_think_tank
        
        # Test processing a message
        query = "Compare the performance characteristics of Python, JavaScript, and Go."
        conversation_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # This may take some time as it processes with multiple models
        logger.info(f"Testing Think Tank integration with query: {query}")
        logger.info("This may take a moment as it processes with multiple models...")
        
        result = process_with_think_tank(
            message=query,
            conversation_id=conversation_id
        )
        
        if isinstance(result, dict):
            if "text" in result:
                text_length = len(result.get("text", ""))
                if text_length > 0:
                    results.add_pass("Think Tank response generation", f"Generated response of {text_length} characters")
                else:
                    results.add_fail("Think Tank response generation", "Generated empty response")
            else:
                results.add_fail("Think Tank response structure", "Response missing 'text' field")
            
            if "model_info" in result:
                model_info = result.get("model_info", {})
                selected_model = model_info.get("selected_model", "unknown")
                query_type = model_info.get("query_type", "unknown")
                
                results.add_pass("Think Tank model selection", f"Selected model: {selected_model}")
                results.add_pass("Think Tank query classification", f"Classified as: {query_type}")
                
                if "score" in model_info:
                    score = model_info.get("score", 0)
                    results.add_pass("Think Tank response scoring", f"Response score: {score:.2f}")
                else:
                    results.add_fail("Think Tank response scoring", "Response missing score")
            else:
                results.add_fail("Think Tank model information", "Response missing 'model_info' field")
        else:
            results.add_fail("Think Tank processing", "Process returned non-dictionary result")
            
    except ImportError as e:
        results.add_skip("Think Tank integration tests", f"Required function not available: {str(e)}")
    except Exception as e:
        results.add_fail("Think Tank integration tests", f"Exception: {str(e)}")
    
    return results

def test_memory_integration():
    """Test the integration with the memory system"""
    results = TestResult()
    
    try:
        # Check if memory functions are available in global namespace
        if 'store_memory' not in globals() or 'retrieve_memory' not in globals() or 'memory_add_knowledge' not in globals():
            raise ImportError("Memory functions not imported in global namespace")
        
        # Test storing a memory
        conversation_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        user_message = "What is the capital of France?"
        ai_response = "The capital of France is Paris."
        metadata = {"test": True, "query_type": "factual"}
        
        try:
            memory_id = store_memory(
                conversation_id=conversation_id,
                user_message=user_message,
                ai_response=ai_response,
                metadata=metadata
            )
            
            if memory_id:
                results.add_pass("Memory storage", f"Memory stored with ID: {memory_id}")
            else:
                results.add_fail("Memory storage", "Failed to store memory or invalid ID returned")
        except Exception as e:
            if "No module named 'chromadb'" in str(e):
                results.add_skip("Memory storage", "ChromaDB not available")
            else:
                results.add_fail("Memory storage", f"Exception: {str(e)}")
            
        # Test retrieving memories
        try:
            memories = retrieve_memory(user_message)
            
            if isinstance(memories, list):
                results.add_pass("Memory retrieval", f"Retrieved {len(memories)} memories")
            else:
                results.add_fail("Memory retrieval", "Retrieved non-list result")
        except Exception as e:
            if "No module named 'chromadb'" in str(e):
                results.add_skip("Memory retrieval", "ChromaDB not available")
            else:
                results.add_fail("Memory retrieval", f"Exception: {str(e)}")
            
        # Test adding knowledge
        try:
            knowledge_id = memory_add_knowledge(
                title="Test Knowledge",
                content="This is a test knowledge entry.",
                source="test_self_learning_components.py"
            )
            
            if knowledge_id:
                results.add_pass("Memory knowledge addition", f"Knowledge added with ID: {knowledge_id}")
            else:
                results.add_fail("Memory knowledge addition", "Failed to add knowledge or invalid ID returned")
        except Exception as e:
            if "No module named 'chromadb'" in str(e):
                results.add_skip("Memory knowledge addition", "ChromaDB not available")
            else:
                results.add_fail("Memory knowledge addition", f"Exception: {str(e)}")
            
    except ImportError:
        results.add_skip("Memory integration tests", "Memory functions not available")
    except Exception as e:
        results.add_fail("Memory integration tests", f"Exception: {str(e)}")
    
    return results

def run_all_tests():
    """Run all tests and return overall results"""
    logger.info("===== TESTING MINERVA SELF-LEARNING SYSTEM COMPONENTS =====")
    
    # Make sure DB is set up
    ensure_db_setup()
    
    # Run tests
    all_test_results = []
    
    logger.info("\n===== TEST 1: DATABASE SETUP =====")
    all_test_results.append(test_db_setup())
    
    logger.info("\n===== TEST 2: ERROR DETECTION SYSTEM =====")
    all_test_results.append(test_error_detection_system())
    
    logger.info("\n===== TEST 3: ERROR LOGGING =====")
    all_test_results.append(test_error_logging())
    
    logger.info("\n===== TEST 4: MODEL PERFORMANCE TRACKING =====")
    all_test_results.append(test_model_performance_tracking())
    
    logger.info("\n===== TEST 5: KNOWLEDGE EXPANSION =====")
    all_test_results.append(test_knowledge_expansion())
    
    logger.info("\n===== TEST 6: MODEL ANALYSIS AND OPTIMIZATION =====")
    all_test_results.append(test_model_analysis_and_optimization())
    
    logger.info("\n===== TEST 7: ADAPTIVE MODEL SELECTION =====")
    all_test_results.append(test_adaptive_model_selection())
    
    logger.info("\n===== TEST 8: THINK TANK INTEGRATION =====")
    all_test_results.append(test_think_tank_integration())
    
    logger.info("\n===== TEST 9: MEMORY INTEGRATION =====")
    all_test_results.append(test_memory_integration())
    
    # Compute overall results
    total_passed = sum(result.passed for result in all_test_results)
    total_failed = sum(result.failed for result in all_test_results)
    total_skipped = sum(result.skipped for result in all_test_results)
    
    logger.info("\n===== OVERALL TEST RESULTS =====")
    logger.info(f"Total tests: {total_passed + total_failed + total_skipped}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Skipped: {total_skipped}")
    
    return total_failed == 0

def ensure_db_setup():
    """Set up SQLite database for self-learning system if it doesn't exist."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create error tracking table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            query TEXT,
            model TEXT,
            response TEXT,
            error_message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE
        )
        """)
        
        # Create model performance table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            query_type TEXT,
            query TEXT,
            response TEXT,
            feedback_score REAL,
            processing_time REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create self-optimization log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS optimization_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            optimization_type TEXT,
            description TEXT,
            before_state TEXT,
            after_state TEXT,
            improvement_metric REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create knowledge expansion table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            source TEXT,
            confidence REAL,
            verified BOOLEAN DEFAULT FALSE,
            usage_count INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Self-learning database initialized")
    except Exception as e:
        logger.error(f"Failed to set up database: {str(e)}")

if __name__ == "__main__":
    try:
        success = run_all_tests()
        if success:
            logger.info("All self-learning component tests completed successfully")
            sys.exit(0)
        else:
            logger.error("Some self-learning component tests failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error during self-learning component tests: {str(e)}", exc_info=True)
        sys.exit(1)
