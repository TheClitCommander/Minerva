"""
Self-Learning System for Minerva

This module implements Minerva's ability to learn, optimize, and improve itself
over time without human intervention. It builds on the existing memory and
feedback systems to enable autonomous growth.

Features:
- Performance monitoring and optimization
- Error detection and self-debugging
- Knowledge expansion through automated learning
- Model selection optimization based on historical performance
"""

import os
import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import sqlite3
from collections import defaultdict, Counter
import statistics

# Set up logging first to avoid NameError
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Minerva's components with fallback for missing dependencies
# Define fallback functions that will be used if imports fail
def fallback_store_memory(*args, **kwargs):
    logger.warning("Memory system not available - memory will not be stored")
    return True

def fallback_retrieve_memory(*args, **kwargs):
    logger.warning("Memory system not available - no memories can be retrieved")
    return []

def fallback_add_knowledge(*args, **kwargs):
    logger.warning("Memory system not available - knowledge will not be stored")
    return 0

def fallback_record_feedback(*args, **kwargs):
    logger.warning("Feedback system not available - feedback will not be recorded")
    return "mock_feedback_id"

def fallback_get_model_performance(*args, **kwargs):
    logger.warning("Feedback system not available - using default model performance")
    return {"gpt-4": 0.9, "claude-3": 0.85, "mistral": 0.8, "llama2": 0.75}

# Fix import paths
import sys
web_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.dirname(web_dir)

# Add the proper paths to sys.path
if web_dir not in sys.path:
    sys.path.insert(0, web_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Import memory system with absolute imports
try:
    from web.integrations.memory import (
        memory_system, 
        store_memory, 
        retrieve_memory, 
        add_knowledge
    )
    memory_available = True
    logger.info("Memory system successfully connected")
except ImportError as e:
    logger.warning(f"Memory system not available - some functionality will be limited: {e}")
    memory_available = False
    # Set fallback functions
    memory_system = None
    store_memory = fallback_store_memory
    retrieve_memory = fallback_retrieve_memory
    add_knowledge = fallback_add_knowledge

# Import feedback system with absolute imports
try:
    from web.integrations.feedback import (
        record_user_feedback,
        get_model_performance
    )
    feedback_available = True
    logger.info("Feedback system successfully connected")
except ImportError as e:
    logger.warning(f"Feedback system not available - some functionality will be limited: {e}")
    feedback_available = False
    # Set fallback functions
    record_user_feedback = fallback_record_feedback
    get_model_performance = fallback_get_model_performance

# Logging already set up at the top of the file

# Database setup for error tracking and self-optimization
DB_PATH = "./data/self_learning.db"

def ensure_db_setup():
    """Set up SQLite database for self-learning system if it doesn't exist."""
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

# Error detection and tracking
def log_error(error_type: str, query: str, model: str, response: str, error_message: str) -> int:
    """
    Log an error for future analysis and self-improvement.
    
    Args:
        error_type: Type of error (e.g., 'refusal', 'hallucination', 'timeout')
        query: User query that triggered the error
        model: Model that produced the error
        response: Model response
        error_message: Detailed error message or description
        
    Returns:
        error_id: ID of the logged error
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO error_logs (error_type, query, model, response, error_message) VALUES (?, ?, ?, ?, ?)",
            (error_type, query, model, response, error_message)
        )
        
        error_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Logged error (ID: {error_id}) of type '{error_type}' from model '{model}'")
        
        # Store this error in memory system too if available
        if memory_available:
            error_memory = {
                "type": "error_log",
                "error_type": error_type,
                "model": model,
                "error_message": error_message
            }
            
            try:
                store_memory(
                    conversation_id=f"error_{error_id}",
                    user_message=query,
                    ai_response=response,
                    metadata=error_memory
                )
                logger.info(f"Error also stored in memory system with ID: error_{error_id}")
            except Exception as e:
                logger.warning(f"Failed to store error in memory system: {str(e)}")
        
        return error_id
    except Exception as e:
        logger.error(f"Failed to log error: {str(e)}")
        return 0

def detect_response_errors(query: str, response: str, model: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Detect common errors in model responses.
    
    Args:
        query: User query
        response: Model response
        model: Model that generated the response
        
    Returns:
        Tuple of (has_error, error_type, error_description)
    """
    # Check for refusal patterns
    refusal_phrases = [
        "I'm sorry, I can't",
        "I cannot assist",
        "I can't provide",
        "I'm not able to",
        "I am unable to",
        "I don't have the ability",
        "I apologize, but I cannot"
    ]
    
    for phrase in refusal_phrases:
        if phrase.lower() in response.lower():
            return True, "refusal", "Model refused to provide an answer"
    
    # Check for hallucination indicators
    hallucination_indicators = [
        "As an AI",
        "As a language model",
        "I don't have access to",
        "I don't have the ability to browse",
        "I cannot browse",
        "my knowledge cutoff",
        "my training data",
        "my training cutoff"
    ]
    
    for indicator in hallucination_indicators:
        if indicator.lower() in response.lower():
            return True, "self_reference", "Model referenced itself as an AI"
    
    # Check for empty or extremely short responses
    if not response or len(response.strip()) < 10:
        return True, "empty_response", "Response is empty or too short"
    
    # No errors detected
    return False, None, None

# Self-optimization
def track_model_performance(
    model: str, 
    query_type: str,
    query: str,
    response: str,
    feedback_score: float,
    processing_time: float
) -> int:
    """
    Track model performance for a specific query type.
    
    Args:
        model: Name of the model
        query_type: Type of query (technical, creative, reasoning)
        query: The actual query
        response: Model's response
        feedback_score: Quality score (0-1)
        processing_time: Time taken to process
        
    Returns:
        entry_id: ID of the tracked entry or 0 if tracking failed
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO model_performance 
               (model, query_type, query, response, feedback_score, processing_time) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (model, query_type, query, response, feedback_score, processing_time)
        )
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Optionally record this performance data for feedback if available
        if feedback_available:
            try:
                record_user_feedback(
                    conversation_id=f"perf_{model}_{int(time.time())}",
                    query=query,
                    response=response,
                    feedback_level="excellent" if feedback_score > 0.8 else 
                                 "good" if feedback_score > 0.6 else 
                                 "adequate" if feedback_score > 0.4 else "poor",
                    metadata={
                        "model": model,
                        "query_type": query_type, 
                        "processing_time": processing_time,
                        "auto_generated": True
                    }
                )
                logger.debug(f"Recorded performance feedback for model {model}")
            except Exception as e:
                logger.warning(f"Failed to record feedback for model performance: {str(e)}")
        
        logger.info(f"Tracked performance for model '{model}' on {query_type} query (score: {feedback_score:.2f})")
        return entry_id
    except Exception as e:
        logger.error(f"Failed to track model performance: {str(e)}")
        return 0

def analyze_model_performance() -> Dict[str, Any]:
    """
    Analyze model performance across query types to optimize selection.
    
    Returns:
        Dictionary of analysis results including best models per query type
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get performance data
    cursor.execute(
        """SELECT model, query_type, AVG(feedback_score) as avg_score, 
           COUNT(*) as count, AVG(processing_time) as avg_time
           FROM model_performance 
           GROUP BY model, query_type
           HAVING count >= 5"""
    )
    
    results = cursor.fetchall()
    conn.close()
    
    # Process the results
    performance_by_type = defaultdict(list)
    model_stats = defaultdict(lambda: defaultdict(dict))
    
    for model, query_type, avg_score, count, avg_time in results:
        performance_by_type[query_type].append((model, avg_score, count, avg_time))
        model_stats[model][query_type] = {
            "avg_score": avg_score,
            "count": count,
            "avg_time": avg_time
        }
    
    # Find best model for each query type
    best_models = {}
    for query_type, models in performance_by_type.items():
        # Sort by score (higher is better)
        models.sort(key=lambda x: x[1], reverse=True)
        best_models[query_type] = models[0][0] if models else None
    
    return {
        "best_models_by_type": best_models,
        "model_stats": dict(model_stats),
        "analysis_time": datetime.now().isoformat()
    }

def log_optimization(
    optimization_type: str,
    description: str,
    before_state: Dict,
    after_state: Dict,
    improvement_metric: float
) -> int:
    """
    Log a self-optimization action.
    
    Args:
        optimization_type: Type of optimization
        description: Description of what was optimized
        before_state: State before optimization
        after_state: State after optimization
        improvement_metric: Quantitative measure of improvement
        
    Returns:
        log_id: ID of the optimization log
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO optimization_log 
           (optimization_type, description, before_state, after_state, improvement_metric) 
           VALUES (?, ?, ?, ?, ?)""",
        (
            optimization_type, 
            description, 
            json.dumps(before_state), 
            json.dumps(after_state), 
            improvement_metric
        )
    )
    
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return log_id

def optimize_model_selection(threshold: float = 0.1) -> Dict[str, Any]:
    """
    Optimize model selection based on performance data.
    Only makes changes if the improvement exceeds the threshold.
    
    Args:
        threshold: Minimum improvement threshold to trigger optimization
        
    Returns:
        Optimization results
    """
    # Get current performance data from feedback system
    current_performance = get_model_performance()
    
    # Get self-tracked performance data
    analysis = analyze_model_performance()
    best_models = analysis["best_models_by_type"]
    
    optimizations = []
    
    # Check if we can improve model selection for each query type
    for query_type, best_model in best_models.items():
        if not best_model:
            continue
            
        # Get current best model for this query type
        type_performance = get_model_performance(query_type=query_type)
        if not type_performance:
            continue
            
        current_models = [(model, data.get("avg_score", 0)) 
                          for model, data in type_performance.items()]
        
        # Sort by score
        current_models.sort(key=lambda x: x[1], reverse=True)
        current_best = current_models[0][0] if current_models else None
        
        if current_best and current_best != best_model:
            # Get scores for comparison
            best_model_score = 0
            for model, score in current_models:
                if model == best_model:
                    best_model_score = score
                    break
            
            current_best_score = current_models[0][1] if current_models else 0
            
            # Check if the improvement exceeds threshold
            if best_model_score > current_best_score + threshold:
                optimizations.append({
                    "query_type": query_type,
                    "old_best": current_best,
                    "new_best": best_model,
                    "improvement": best_model_score - current_best_score
                })
    
    # Log the optimization if any were made
    if optimizations:
        log_optimization(
            optimization_type="model_selection",
            description=f"Optimized model selection for {len(optimizations)} query types",
            before_state={"current_performance": current_performance},
            after_state={"optimized_performance": analysis},
            improvement_metric=sum(opt["improvement"] for opt in optimizations)
        )
    
    return {
        "optimizations": optimizations,
        "analysis": analysis
    }

# Knowledge expansion
def add_new_knowledge(
    title: str,
    content: str,
    source: str,
    confidence: float = 0.7,
    verified: bool = False
) -> int:
    """
    Add new knowledge to Minerva's knowledge base.
    
    Args:
        title: Knowledge title
        content: Knowledge content
        source: Source of knowledge
        confidence: Confidence in the knowledge (0-1)
        verified: Whether the knowledge is verified
        
    Returns:
        knowledge_id: ID of the added knowledge
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO knowledge_entries 
               (title, content, source, confidence, verified) 
               VALUES (?, ?, ?, ?, ?)""",
            (title, content, source, confidence, verified)
        )
        
        knowledge_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Also add to memory system for semantic search if available
        if memory_available:
            try:
                add_knowledge(
                    title=title,
                    content=content,
                    source=source,
                    metadata={
                        "confidence": confidence,
                        "verified": verified,
                        "knowledge_id": knowledge_id
                    }
                )
                logger.info(f"Knowledge also added to memory system for semantic search")
            except Exception as e:
                logger.warning(f"Failed to add knowledge to memory system: {str(e)}")
        
        logger.info(f"Added new knowledge: '{title}' (ID: {knowledge_id})")
        return knowledge_id
    except Exception as e:
        logger.error(f"Failed to add new knowledge: {str(e)}")
        return 0

def verify_and_update_knowledge(knowledge_id: int, verified: bool, updated_content: Optional[str] = None) -> bool:
    """
    Verify or update existing knowledge.
    
    Args:
        knowledge_id: ID of the knowledge to update
        verified: Verification status
        updated_content: Updated content if any
        
    Returns:
        success: Whether the update was successful
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    update_sql = "UPDATE knowledge_entries SET verified = ?"
    params = [verified]
    
    if updated_content:
        update_sql += ", content = ?"
        params.append(updated_content)
    
    update_sql += " WHERE id = ?"
    params.append(knowledge_id)
    
    cursor.execute(update_sql, params)
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    if success:
        logger.info(f"Updated knowledge ID {knowledge_id}, verified: {verified}")
    else:
        logger.warning(f"Failed to update knowledge ID {knowledge_id}")
    
    return success

def get_all_knowledge_entries(verified_only: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get all knowledge entries.
    
    Args:
        verified_only: Whether to return only verified entries
        limit: Maximum number of entries to return
        
    Returns:
        List of knowledge entries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM knowledge_entries"
    if verified_only:
        query += " WHERE verified = TRUE"
    query += " ORDER BY usage_count DESC, timestamp DESC LIMIT ?"
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    # Convert to list of dicts
    result = [dict(row) for row in rows]
    conn.close()
    
    return result

def increment_knowledge_usage(knowledge_id: int) -> bool:
    """
    Increment the usage count for a knowledge entry.
    
    Args:
        knowledge_id: ID of the knowledge entry
        
    Returns:
        success: Whether the update was successful
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE knowledge_entries SET usage_count = usage_count + 1 WHERE id = ?",
        (knowledge_id,)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# Self-debugging functions
def get_common_errors(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get the most common errors for self-debugging.
    
    Args:
        limit: Maximum number of error types to return
        
    Returns:
        List of common error types and counts
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT error_type, COUNT(*) as count 
           FROM error_logs 
           WHERE resolved = FALSE
           GROUP BY error_type 
           ORDER BY count DESC 
           LIMIT ?""",
        (limit,)
    )
    
    results = cursor.fetchall()
    conn.close()
    
    return [{"error_type": err_type, "count": count} for err_type, count in results]

def get_error_prone_models() -> List[Dict[str, Any]]:
    """
    Identify models that frequently produce errors.
    
    Returns:
        List of models and their error counts
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """SELECT model, error_type, COUNT(*) as error_count
           FROM error_logs
           WHERE resolved = FALSE
           GROUP BY model, error_type
           ORDER BY error_count DESC"""
    )
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {"model": model, "error_type": err_type, "count": count}
        for model, err_type, count in results
    ]

def suggest_error_fixes() -> List[Dict[str, Any]]:
    """
    Suggest fixes for common errors based on historical data.
    
    Returns:
        List of suggested fixes for different error types
    """
    # Get common errors
    common_errors = get_common_errors()
    error_prone_models = get_error_prone_models()
    
    suggestions = []
    
    # Generate suggestions based on error patterns
    for error in common_errors:
        error_type = error["error_type"]
        
        # Find models that have this error type
        affected_models = [
            model_error["model"]
            for model_error in error_prone_models
            if model_error["error_type"] == error_type
        ]
        
        if error_type == "refusal":
            suggestions.append({
                "error_type": error_type,
                "affected_models": affected_models,
                "suggestion": "Try reformulating queries to avoid triggering refusal responses",
                "implementation": "Implement query reformulation module"
            })
        elif error_type == "self_reference":
            suggestions.append({
                "error_type": error_type,
                "affected_models": affected_models,
                "suggestion": "Add post-processing to remove AI self-references",
                "implementation": "Implement response filter for AI self-references"
            })
        elif error_type == "empty_response":
            suggestions.append({
                "error_type": error_type,
                "affected_models": affected_models,
                "suggestion": "Add fallback mechanism for empty responses",
                "implementation": "Implement automatic retry with different model"
            })
    
    return suggestions

def mark_errors_resolved(error_type: str) -> int:
    """
    Mark all errors of a specific type as resolved.
    
    Args:
        error_type: Type of error to mark as resolved
        
    Returns:
        Number of errors marked as resolved
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE error_logs SET resolved = TRUE WHERE error_type = ?",
        (error_type,)
    )
    
    count = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Marked {count} errors of type '{error_type}' as resolved")
    return count

# Integration with the Think Tank system
def adaptive_model_selection(
    query: str, 
    query_type: str, 
    available_models: List[str]
) -> Dict[str, Any]:
    """
    Adaptively select the best model for a query based on historical performance.
    
    Args:
        query: User query
        query_type: Type of query
        available_models: List of available models
        
    Returns:
        Dictionary with selected model and reasoning
    """
    try:
        if not available_models:
            logger.warning("No available models provided for selection!")
            return {
                "selected_model": None,
                "reason": "No models available for selection",
                "confidence": 0.0
            }
            
        # Define model capabilities for better selection when no data is available
        model_capabilities = {
            "gpt-4": {"technical": 0.95, "creative": 0.90, "reasoning": 0.95, "factual": 0.90, "general": 0.92},
            "claude-3": {"technical": 0.88, "creative": 0.92, "reasoning": 0.90, "factual": 0.85, "general": 0.90},
            "gemini": {"technical": 0.85, "creative": 0.82, "reasoning": 0.87, "factual": 0.88, "general": 0.85},
            "gpt-3.5-turbo": {"technical": 0.80, "creative": 0.85, "reasoning": 0.80, "factual": 0.75, "general": 0.82},
            "mistral": {"technical": 0.78, "creative": 0.80, "reasoning": 0.75, "factual": 0.70, "general": 0.75},
            "llama2": {"technical": 0.75, "creative": 0.78, "reasoning": 0.73, "factual": 0.68, "general": 0.73},
        }
        
        # Try to get performance data if feedback system is available
        performance = {}
        if feedback_available:
            try:
                performance = get_model_performance(query_type=query_type)
            except Exception as e:
                logger.warning(f"Error getting model performance data: {str(e)}")
        
        # Try to get self-tracked performance data
        try:
            analysis = analyze_model_performance()
            best_models = analysis.get("best_models_by_type", {})
        except Exception as e:
            logger.warning(f"Error analyzing model performance: {str(e)}")
            best_models = {}
        
        # If no performance data, use model capabilities mapping
        if not performance or not any(model in available_models for model in performance):
            # Check if we have a best model for this query type from history
            best_model = best_models.get(query_type)
            if best_model and best_model in available_models:
                return {
                    "selected_model": best_model,
                    "reason": f"Selected based on historical performance for {query_type} queries",
                    "confidence": 0.7
                }
            else:
                # Use capability scoring when no historical data
                scored_models = []
                for model in available_models:
                    # Get capability score or default score
                    if model in model_capabilities and query_type in model_capabilities[model]:
                        score = model_capabilities[model][query_type]
                    else:
                        # If model not in capabilities, assign conservative score
                        score = 0.65
                    scored_models.append((model, score))
                
                # Sort by capability score
                scored_models.sort(key=lambda x: x[1], reverse=True)
                
                return {
                    "selected_model": scored_models[0][0],
                    "reason": f"Selected based on capability profile for {query_type} queries",
                    "confidence": scored_models[0][1],
                    "capability_based": True
                }
        
        # Filter to available models
        filtered_performance = {
            model: data
            for model, data in performance.items()
            if model in available_models
        }
        
        if not filtered_performance:
            # Fall back to capabilities
            scored_models = []
            for model in available_models:
                if model in model_capabilities and query_type in model_capabilities[model]:
                    score = model_capabilities[model][query_type]
                else:
                    score = 0.65  # Default score
                scored_models.append((model, score))
            
            # Sort by capability score
            scored_models.sort(key=lambda x: x[1], reverse=True)
            
            return {
                "selected_model": scored_models[0][0],
                "reason": "Using capability profile since no performance data exists",
                "confidence": scored_models[0][1],
                "capability_based": True
            }
        
        # Sort by average score
        ranked_models = sorted(
            filtered_performance.items(),
            key=lambda x: x[1].get("avg_score", 0),
            reverse=True
        )
        
        selected_model = ranked_models[0][0]
        confidence = ranked_models[0][1].get("avg_score", 0.5)
        
        return {
            "selected_model": selected_model,
            "reason": f"Selected based on highest average score for {query_type} queries",
            "confidence": confidence,
            "historical_data": True,
            "all_rankings": [
                {"model": model, "score": data.get("avg_score", 0), "count": data.get("count", 0)}
                for model, data in ranked_models
            ]
        }
    except Exception as e:
        logger.error(f"Error in adaptive model selection: {str(e)}")
        # Fallback to first available model
        if available_models:
            return {
                "selected_model": available_models[0],
                "reason": "Selected as fallback due to error in adaptive selection",
                "confidence": 0.5,
                "error": str(e)
            }
        else:
            return {
                "selected_model": None,
                "reason": "No models available and error in selection process",
                "confidence": 0.0,
                "error": str(e)
            }

# Initialize the self-learning system
ensure_db_setup()

logger.info("Self-learning system initialized")
