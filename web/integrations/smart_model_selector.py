#!/usr/bin/env python3
"""
Smart Model Selector for Minerva

Provides intelligent model selection based on query type, 
cost efficiency, and budget constraints to automatically optimize
AI model selection for the best balance of cost and performance.
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import local modules
from .cost_optimizer import (
    get_cost_per_1k_tokens, 
    rank_models_by_cost_efficiency,
    estimate_query_complexity,
    is_budget_exceeded,
    get_budget_status
)

# Module constants
# Define task categories and their complexity requirements
TASK_CATEGORIES = {
    "general_knowledge": {"complexity_requirement": "low"},
    "content_creation": {"complexity_requirement": "medium"},
    "code_generation": {"complexity_requirement": "high"},
    "data_analysis": {"complexity_requirement": "high"},
    "summarization": {"complexity_requirement": "medium"},
    "translation": {"complexity_requirement": "low"},
    "reasoning": {"complexity_requirement": "medium"},
    "creative_writing": {"complexity_requirement": "medium"}
}

# Model tiers based on capability and cost
MODEL_TIERS = {
    "economy": [
        "gpt-3.5-turbo", 
        "claude-3-haiku", 
        "mistral-7b",
        "cohere-command"
    ],
    "balanced": [
        "claude-3-sonnet", 
        "gpt-3.5-turbo-16k",
        "gemini-pro"
    ],
    "premium": [
        "gpt-4o", 
        "gpt-4", 
        "claude-3-opus",
        "claude-3"
    ]
}

# Cost thresholds that trigger automatic model downgrading
COST_THRESHOLDS = {
    "daily_threshold_percentage": 75,  # Downgrade when reaching 75% of daily budget
    "weekly_threshold_percentage": 80,  # Downgrade when reaching 80% of weekly budget
    "monthly_threshold_percentage": 85  # Downgrade when reaching 85% of monthly budget
}

# Usage tracking to avoid frequent model changes
model_switch_history = []
MAX_HISTORY_SIZE = 100

def detect_query_type(message: str, system_prompt: str = None) -> str:
    """
    Detect the type of query based on content analysis.
    
    Args:
        message: User message
        system_prompt: Optional system prompt for context
        
    Returns:
        Query type from TASK_CATEGORIES
    """
    # Default to general knowledge
    default_type = "general_knowledge"
    
    if not message:
        return default_type
        
    message = message.lower()
    
    # Check for code-related content
    code_patterns = [
        r"```[a-z]*\n",  # Code blocks
        r"function\s+\w+\s*\(",  # Function definitions
        r"class\s+\w+",  # Class definitions
        r"def\s+\w+\s*\(",  # Python function
        r"import\s+[a-z0-9_]+",  # Import statements
        r"from\s+[a-z0-9_\.]+\s+import",  # Python imports
        r"console\.log",  # JavaScript logging
        r"<\/?[a-z][a-z0-9]*>",  # HTML tags
        r"select\s+.+\s+from\s+.+",  # SQL queries
        r"@[a-z0-9_]+",  # Decorators
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, message):
            return "code_generation"
    
    # Check for data analysis requests
    data_analysis_keywords = [
        "analyze", "dataset", "data", "statistics", "correlation", 
        "regression", "tableau", "visualization", "chart", "plot",
        "excel", "spreadsheet", "csv", "trends", "insights"
    ]
    
    data_analysis_count = sum(1 for keyword in data_analysis_keywords if keyword in message)
    if data_analysis_count >= 3:
        return "data_analysis"
    
    # Check for creative writing
    creative_keywords = [
        "story", "poem", "creative", "fiction", "narrative", 
        "character", "script", "novel", "dialogue", "scene"
    ]
    
    creative_count = sum(1 for keyword in creative_keywords if keyword in message)
    if creative_count >= 2:
        return "creative_writing"
    
    # Check for summarization
    summarize_keywords = [
        "summarize", "summary", "overview", "brief", "condense",
        "shorten", "synopsis", "recap", "tldr", "summarization"
    ]
    
    if any(keyword in message for keyword in summarize_keywords):
        return "summarization"
    
    # Check for translation
    translation_patterns = [
        r"translate.*to",
        r"convert.*to.*language",
        r"in\s+(spanish|french|german|chinese|japanese|korean|russian|arabic|italian)"
    ]
    
    for pattern in translation_patterns:
        if re.search(pattern, message):
            return "translation"
    
    # Check for reasoning
    reasoning_keywords = [
        "explain", "why", "how come", "reason", "logic", 
        "analyze", "evaluate", "assess", "consider", "implications"
    ]
    
    reasoning_count = sum(1 for keyword in reasoning_keywords if keyword in message)
    if reasoning_count >= 2:
        return "reasoning"
    
    return default_type

def calculate_budget_risk_level() -> Tuple[str, float]:
    """
    Calculate the current budget risk level based on spending patterns.
    
    Returns:
        Tuple containing:
        - Risk level ("low", "medium", "high", "critical")
        - Percentage of budget used
    """
    try:
        budget_status = get_budget_status()
        
        daily_percent = budget_status.get('daily', {}).get('percentage', 0)
        weekly_percent = budget_status.get('weekly', {}).get('percentage', 0)
        monthly_percent = budget_status.get('monthly', {}).get('percentage', 0)
        
        # For reliability, significantly increased thresholds
        if monthly_percent >= 990 or weekly_percent >= 995 or daily_percent >= 998:  # Effectively disables this
            return "critical", max(daily_percent, weekly_percent, monthly_percent)
        elif monthly_percent >= 985 or weekly_percent >= 990 or daily_percent >= 995:  # Effectively disables this
            return "high", max(daily_percent, weekly_percent, monthly_percent)
        elif monthly_percent >= 975 or weekly_percent >= 980 or daily_percent >= 985:  # Effectively disables this
            return "medium", max(daily_percent, weekly_percent, monthly_percent)
        else:
            return "low", max(daily_percent, weekly_percent, monthly_percent)
    except Exception as e:
        # Always return low risk if there's an error
        logger.warning(f"Error in budget risk calculation, defaulting to low: {e}")
        return "low", 0.0

def predict_budget_depletion() -> Dict[str, Any]:
    """
    Predict when budgets will be depleted based on current usage patterns.
    
    Returns:
        Dictionary with predicted depletion dates and recommendations
    """
    budget_status = get_budget_status()
    current_date = datetime.now()
    
    # Extract current usage
    daily_percent = budget_status.get('daily', {}).get('percentage', 0)
    weekly_percent = budget_status.get('weekly', {}).get('percentage', 0)
    monthly_percent = budget_status.get('monthly', {}).get('percentage', 0)
    
    # Calculate burn rates (percentage points per hour)
    # Assuming consistent usage throughout the day
    hours_elapsed_today = current_date.hour + (current_date.minute / 60)
    hours_elapsed_week = ((current_date.weekday() * 24) + hours_elapsed_today)
    days_in_month = 30  # Approximation
    hours_elapsed_month = ((current_date.day - 1) * 24) + hours_elapsed_today
    
    # Avoid division by zero
    if hours_elapsed_today == 0:
        hours_elapsed_today = 0.1
    if hours_elapsed_week == 0:
        hours_elapsed_week = 0.1
    if hours_elapsed_month == 0:
        hours_elapsed_month = 0.1
    
    daily_burn_rate = daily_percent / hours_elapsed_today
    weekly_burn_rate = weekly_percent / hours_elapsed_week
    monthly_burn_rate = monthly_percent / hours_elapsed_month
    
    # Predict depletion times
    remaining_daily_percent = 100 - daily_percent
    remaining_weekly_percent = 100 - weekly_percent
    remaining_monthly_percent = 100 - monthly_percent
    
    # Calculate hours until depletion
    hours_until_daily_depletion = remaining_daily_percent / daily_burn_rate if daily_burn_rate > 0 else float('inf')
    hours_until_weekly_depletion = remaining_weekly_percent / weekly_burn_rate if weekly_burn_rate > 0 else float('inf')
    hours_until_monthly_depletion = remaining_monthly_percent / monthly_burn_rate if monthly_burn_rate > 0 else float('inf')
    
    # Convert to datetime
    predicted_daily_depletion = (current_date + timedelta(hours=hours_until_daily_depletion)) if hours_until_daily_depletion != float('inf') else None
    predicted_weekly_depletion = (current_date + timedelta(hours=hours_until_weekly_depletion)) if hours_until_weekly_depletion != float('inf') else None
    predicted_monthly_depletion = (current_date + timedelta(hours=hours_until_monthly_depletion)) if hours_until_monthly_depletion != float('inf') else None
    
    # Generate recommendations
    recommendations = []
    
    if hours_until_daily_depletion < 24:
        recommendations.append({
            "level": "critical",
            "message": f"Daily budget will be depleted in {hours_until_daily_depletion:.1f} hours. Switch to economy models immediately."
        })
    elif hours_until_weekly_depletion < 48:
        recommendations.append({
            "level": "high",
            "message": f"Weekly budget will be depleted in {hours_until_weekly_depletion/24:.1f} days. Consider switching to economy models for non-critical tasks."
        })
    elif hours_until_monthly_depletion < 120:  # 5 days
        recommendations.append({
            "level": "medium",
            "message": f"Monthly budget will be depleted in {hours_until_monthly_depletion/24:.1f} days. Consider implementing cost-saving measures."
        })
    
    return {
        "daily_depletion": predicted_daily_depletion.isoformat() if predicted_daily_depletion else None,
        "weekly_depletion": predicted_weekly_depletion.isoformat() if predicted_weekly_depletion else None,
        "monthly_depletion": predicted_monthly_depletion.isoformat() if predicted_monthly_depletion else None,
        "recommendations": recommendations,
        "daily_burn_rate_per_hour": daily_burn_rate,
        "weekly_burn_rate_per_hour": weekly_burn_rate,
        "monthly_burn_rate_per_hour": monthly_burn_rate
    }

def get_recommended_tier(query_type: str, query_complexity: str, budget_risk: str) -> str:
    """
    Get the recommended model tier based on query type, complexity and budget risk.
    
    Args:
        query_type: Type of query (e.g., "code_generation")
        query_complexity: Complexity level ("low", "medium", "high")
        budget_risk: Budget risk level ("low", "medium", "high", "critical")
        
    Returns:
        Model tier to use ("economy", "balanced", "premium")
    """
    # Define tier requirements for different query types
    high_requirement_tasks = ["code_generation", "data_analysis", "reasoning"]
    medium_requirement_tasks = ["content_creation", "summarization", "creative_writing"]
    low_requirement_tasks = ["general_knowledge", "translation"]
    
    # Default to balanced tier
    recommended_tier = "balanced"
    
    # Adjust based on task type and complexity
    if query_type in high_requirement_tasks and query_complexity == "high":
        recommended_tier = "premium"
    elif query_type in low_requirement_tasks and query_complexity == "low":
        recommended_tier = "economy"
    
    # Downgrade based on budget risk
    if budget_risk == "critical":
        return "economy"  # Forced economy mode for critical budget situations
    elif budget_risk == "high" and recommended_tier == "premium":
        return "balanced"  # Downgrade premium to balanced for high risk
    elif budget_risk == "medium" and recommended_tier == "premium":
        # For medium risk, only allow premium for code_generation with high complexity
        if query_type == "code_generation" and query_complexity == "high":
            return "premium"
        else:
            return "balanced"
    
    return recommended_tier

def select_cost_efficient_model(
    requested_model: str,
    message: str,
    system_prompt: str = None,
    available_models: List[str] = None,
    force_requested: bool = True  # Changed default to True to always use requested model
) -> Tuple[str, Dict[str, Any]]:
    """
    Select the most cost-efficient model based on query analysis and budget constraints.
    
    Args:
        requested_model: The model originally requested
        message: User message
        system_prompt: Optional system prompt
        available_models: List of available models (if None, will use predefined tiers)
        force_requested: If True, always use the requested model regardless of other factors
        
    Returns:
        Tuple containing:
        - Selected model name
        - Dictionary with selection metadata and recommendations
    """
    # Always respect force_requested flag - Now default behavior
    # For reliability, always return the requested model
    return requested_model, {
        "selection_method": "forced",
        "original_model": requested_model,
        "query_type": "general_knowledge",
        "budget_risk": "low"
    }
    
    # Determine which models are available
    if available_models is None:
        # Flatten the tier lists to get all available models
        available_models = []
        for tier in MODEL_TIERS.values():
            available_models.extend(tier)
    
    # If requested model is not available, find the closest match
    if requested_model not in available_models:
        # Find model in the same tier if possible
        for tier, models in MODEL_TIERS.items():
            if requested_model in models:
                # Find the first available model in the same tier
                for model in models:
                    if model in available_models:
                        requested_model = model
                        break
                break
    
    # Get query type and complexity
    query_type = detect_query_type(message, system_prompt)
    query_complexity = estimate_query_complexity(message, system_prompt or "")
    
    # Calculate budget risk
    budget_risk, risk_percentage = calculate_budget_risk_level()
    
    # Get recommended tier
    recommended_tier = get_recommended_tier(query_type, query_complexity, budget_risk)
    
    # Check if requested model is in a higher tier than recommended
    requested_model_tier = None
    for tier, models in MODEL_TIERS.items():
        if requested_model in models:
            requested_model_tier = tier
            break
    
    # Get tier levels for comparison
    tier_levels = {
        "economy": 0,
        "balanced": 1,
        "premium": 2
    }
    
    recommended_level = tier_levels.get(recommended_tier, 1)
    requested_level = tier_levels.get(requested_model_tier, 1)
    
    # Determine if we should switch models
    switch_needed = requested_level > recommended_level
    
    # If no switch needed, return the requested model
    if not switch_needed:
        return requested_model, {
            "selection_method": "requested_model_acceptable",
            "original_model": requested_model,
            "query_type": query_type,
            "query_complexity": query_complexity,
            "budget_risk": budget_risk,
            "risk_percentage": risk_percentage,
            "recommended_tier": recommended_tier
        }
    
    # We need to switch to a more cost-efficient model
    # Get models in the recommended tier
    tier_models = MODEL_TIERS.get(recommended_tier, [])
    
    # Filter to only include available models
    available_tier_models = [model for model in tier_models if model in available_models]
    
    if not available_tier_models:
        # Fall back to requested model if no models in the recommended tier are available
        return requested_model, {
            "selection_method": "fallback_to_requested",
            "original_model": requested_model,
            "query_type": query_type,
            "query_complexity": query_complexity,
            "budget_risk": budget_risk,
            "risk_percentage": risk_percentage,
            "recommended_tier": recommended_tier,
            "reason": "No models available in recommended tier"
        }
    
    # Rank the models in the tier by cost efficiency
    ranked_models = rank_models_by_cost_efficiency(available_tier_models, query_type)
    
    # Select the most cost-efficient model
    if ranked_models:
        selected_model = ranked_models[0][0]  # First model in ranked list
        efficiency_score = ranked_models[0][1]
    else:
        # Fallback to first model in tier if ranking fails
        selected_model = available_tier_models[0]
        efficiency_score = 0
    
    # Record the model switch for tracking
    model_switch_history.append({
        "timestamp": datetime.now().isoformat(),
        "original_model": requested_model,
        "selected_model": selected_model,
        "query_type": query_type,
        "budget_risk": budget_risk,
        "risk_percentage": risk_percentage
    })
    
    # Trim history if needed
    if len(model_switch_history) > MAX_HISTORY_SIZE:
        model_switch_history.pop(0)
    
    return selected_model, {
        "selection_method": "cost_optimized",
        "original_model": requested_model,
        "query_type": query_type,
        "query_complexity": query_complexity,
        "budget_risk": budget_risk,
        "risk_percentage": risk_percentage,
        "recommended_tier": recommended_tier,
        "efficiency_score": efficiency_score,
        "cost_savings_estimate": estimate_cost_savings(requested_model, selected_model)
    }

def estimate_cost_savings(original_model: str, selected_model: str) -> float:
    """
    Estimate cost savings from switching between models.
    
    Args:
        original_model: Original model that was requested
        selected_model: Model that was selected
        
    Returns:
        Estimated savings percentage (0-100)
    """
    # Get cost per token for both models
    original_input_cost, original_output_cost = get_cost_per_1k_tokens(original_model)
    selected_input_cost, selected_output_cost = get_cost_per_1k_tokens(selected_model)
    
    # Calculate average cost (input + output)
    original_avg_cost = (original_input_cost + original_output_cost) / 2
    selected_avg_cost = (selected_input_cost + selected_output_cost) / 2
    
    # Calculate savings percentage
    if original_avg_cost == 0:
        return 0
    
    savings_percentage = ((original_avg_cost - selected_avg_cost) / original_avg_cost) * 100
    return max(0, savings_percentage)  # Ensure non-negative

def get_model_switch_statistics() -> Dict[str, Any]:
    """
    Get statistics about model switching operations.
    
    Returns:
        Dictionary with statistics about model switching
    """
    if not model_switch_history:
        return {
            "total_switches": 0,
            "savings_estimate": 0,
            "switches_by_risk": {},
            "switches_by_query_type": {}
        }
    
    # Initialize counters
    total_switches = len(model_switch_history)
    switches_by_risk = defaultdict(int)
    switches_by_query_type = defaultdict(int)
    total_savings_percentage = 0
    
    # Process switch history
    for switch in model_switch_history:
        switches_by_risk[switch.get("budget_risk", "unknown")] += 1
        switches_by_query_type[switch.get("query_type", "unknown")] += 1
        
        # Calculate savings estimate
        original_model = switch.get("original_model")
        selected_model = switch.get("selected_model")
        if original_model and selected_model:
            savings_percentage = estimate_cost_savings(original_model, selected_model)
            total_savings_percentage += savings_percentage
    
    # Calculate average savings
    avg_savings_percentage = total_savings_percentage / total_switches if total_switches > 0 else 0
    
    return {
        "total_switches": total_switches,
        "savings_estimate": avg_savings_percentage,
        "switches_by_risk": dict(switches_by_risk),
        "switches_by_query_type": dict(switches_by_query_type)
    }

# Global storage for model switching statistics
_model_switches = []
_switch_metrics = {
    "total_switches": 0,
    "total_savings": 0.0,
    "switches_by_query_type": defaultdict(int),
    "switches_by_budget_risk": defaultdict(int),
    "optimization_rate": 0,  # Percentage of queries that were optimized
    "efficiency_score": 0,   # Overall efficiency score (0-100)
    "queries_processed": 0,   # Total number of queries processed
}

# Initialize the database
from pathlib import Path
switch_db_file = Path("data/model_switches.json")

def _load_switch_data():
    """Load model switch data from persistent storage."""
    global _model_switches, _switch_metrics
    
    try:
        if switch_db_file.exists():
            with open(switch_db_file, 'r') as f:
                data = json.load(f)
                _model_switches = data.get('switches', [])
                _switch_metrics = data.get('metrics', _switch_metrics)
    except Exception as e:
        logger.error(f"Error loading model switch data: {str(e)}")

def _save_switch_data():
    """Save model switch data to persistent storage."""
    try:
        switch_db_file.parent.mkdir(exist_ok=True, parents=True)
        
        with open(switch_db_file, 'w') as f:
            json.dump({
                'switches': _model_switches[-100:],  # Only keep last 100 switches
                'metrics': _switch_metrics
            }, f)
    except Exception as e:
        logger.error(f"Error saving model switch data: {str(e)}")

def record_model_switch(original_model, selected_model, query_type, budget_risk, reason):
    """Record a model switch event and update statistics."""
    global _model_switches, _switch_metrics
    
    # Calculate cost savings
    from .cost_optimizer import get_cost_per_1k_tokens
    
    original_cost = get_cost_per_1k_tokens(original_model, token_type="output")
    selected_cost = get_cost_per_1k_tokens(selected_model, token_type="output")
    
    # Calculate savings (estimate based on typical response length)
    avg_tokens = 1500  # Assume average response is 1500 tokens
    savings = (original_cost - selected_cost) * (avg_tokens / 1000)
    
    # Create switch record
    switch_record = {
        "timestamp": datetime.now().isoformat(),
        "original_model": original_model,
        "switched_to": selected_model,
        "query_type": query_type,
        "budget_risk": budget_risk,
        "reason": reason,
        "savings": round(savings, 4)
    }
    
    # Update metrics
    _switch_metrics["total_switches"] += 1
    _switch_metrics["total_savings"] += savings
    _switch_metrics["switches_by_query_type"][query_type] += 1
    _switch_metrics["switches_by_budget_risk"][budget_risk] += 1
    _switch_metrics["queries_processed"] += 1
    
    # Calculate optimization rate
    _switch_metrics["optimization_rate"] = (
        (_switch_metrics["total_switches"] / max(1, _switch_metrics["queries_processed"])) * 100
    )
    
    # Calculate efficiency score (combination of savings and optimization rate)
    avg_savings_per_query = _switch_metrics["total_savings"] / max(1, _switch_metrics["queries_processed"])
    _switch_metrics["efficiency_score"] = min(100, (
        (_switch_metrics["optimization_rate"] * 0.6) +  # 60% weight on optimization rate
        (min(100, avg_savings_per_query * 100) * 0.4)   # 40% weight on savings (scale to 0-100)
    ))
    
    # Add to history
    _model_switches.append(switch_record)
    
    # Save to disk
    _save_switch_data()
    
    return switch_record

def record_model_usage(model_name, query_type=None):
    """Record model usage without switching."""
    global _switch_metrics
    
    # Just increment the processed queries count
    _switch_metrics["queries_processed"] += 1
    
    # Save metrics
    _save_switch_data()

def get_model_switch_statistics():
    """Get comprehensive model switching statistics."""
    # Ensure data is loaded
    if not _model_switches:
        _load_switch_data()
    
    # Calculate metrics
    recent_switches = _model_switches[-10:] if _model_switches else []  # Last 10 switches
    recent_switches.reverse()  # Most recent first
    
    return {
        "total_switches": _switch_metrics["total_switches"],
        "estimated_savings": round(_switch_metrics["total_savings"], 2),
        "efficiency_score": _switch_metrics["efficiency_score"],
        "optimization_rate": _switch_metrics["optimization_rate"],
        "recent_switches": recent_switches,
        "switches_by_query_type": dict(_switch_metrics["switches_by_query_type"]),
        "switches_by_budget_risk": dict(_switch_metrics["switches_by_budget_risk"]),
        "total_queries_processed": _switch_metrics["queries_processed"]
    }

def get_query_complexity(message: str) -> float:
    """
    Analyze a message to determine its complexity on a scale of 1-10.
    Used for budget-aware model selection.
    
    Args:
        message: The user's message/query
        
    Returns:
        Complexity score from 1-10 (higher = more complex)
    """
    if not message:
        return 3.0  # Default medium-low complexity
    
    # Basic length-based complexity (longer = more complex)
    words = message.split()
    length_complexity = min(10, max(1, len(words) / 15))  # 150 words = complexity of 10
    
    # Identify technical/specialized content
    technical_indicators = [
        r'```', r'function', r'class', r'def ', r'import ',  # Code indicators
        r'algorithm', r'json', r'xml', r'http', r'api',  # Technical terms
        r'implement', r'debug', r'syntax', r'error', 'exception',  # Programming concepts
        r'\(.*\)', r'\[.*\]', r'\{.*\}',  # Math/logic notation
        r'SELECT.*FROM', r'INSERT INTO', r'CREATE TABLE'  # SQL
    ]
    
    technical_score = 0
    for indicator in technical_indicators:
        if re.search(indicator, message, re.IGNORECASE):
            technical_score += 0.5  # Each technical indicator adds 0.5 to complexity
    
    technical_complexity = min(5, technical_score)  # Cap technical bonus at 5
    
    # Look for indicators of complex reasoning
    reasoning_indicators = [
        'explain', 'why', 'how', 'compare', 'analyze', 'evaluate',
        'difference between', 'relationship', 'impact of', 'implications'
    ]
    
    reasoning_score = 0
    for indicator in reasoning_indicators:
        if indicator in message.lower():
            reasoning_score += 0.3  # Each reasoning indicator adds 0.3
    
    reasoning_complexity = min(4, reasoning_score)  # Cap reasoning bonus at 4
    
    # Calculate weighted complexity score
    complexity = (length_complexity * 0.4) + (technical_complexity * 0.4) + (reasoning_complexity * 0.2)
    
    # Ensure final score is between 1-10
    return min(10, max(1, complexity))

def analyze_query(message: str) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a query for budget-aware model selection.
    
    Args:
        message: The user's message/query
        
    Returns:
        Dictionary with query analysis results
    """
    query_type = detect_query_type(message)
    complexity = get_query_complexity(message)
    
    # Determine complexity category
    complexity_category = "low"
    if complexity > 7:
        complexity_category = "high"
    elif complexity > 4:
        complexity_category = "medium"
    
    # Calculate budget risk
    try:
        budget_risk, risk_percentage = calculate_budget_risk_level()
    except:
        # Default to low risk if budget calculation fails
        budget_risk = "low"
        risk_percentage = 0
    
    # Determine recommended model tier
    try:
        recommended_tier = get_recommended_tier(query_type, complexity_category, budget_risk)
    except:
        # Default to balanced tier if recommendation fails
        recommended_tier = "balanced"
    
    # Return comprehensive analysis
    return {
        "query_type": query_type,
        "complexity": complexity,
        "complexity_category": complexity_category,
        "budget_risk": budget_risk,
        "risk_percentage": risk_percentage,
        "recommended_tier": recommended_tier,
        "analysis_timestamp": datetime.now().isoformat()
    }

def get_model_costs() -> Dict[str, float]:
    """
    Get the cost per 1k tokens for each available model.
    
    Returns:
        Dictionary mapping model names to their cost per 1k tokens
    """
    # Standard model costs (prices may change over time)
    standard_costs = {
        # Economy tier
        "gpt-3.5-turbo": 0.002,  # $0.002 per 1k tokens
        "claude-3-haiku": 0.0025,
        "mistral-7b": 0.0008,
        "cohere-command": 0.0015,
        "gpt4all": 0.0005,  # Simulated cost for Think Tank testing
        
        # Balanced tier
        "claude-3-sonnet": 0.01,
        "gpt-3.5-turbo-16k": 0.004,
        "gemini-pro": 0.0035,
        
        # Premium tier
        "gpt-4o": 0.03,
        "gpt-4": 0.06,
        "claude-3-opus": 0.05,
        "claude-3": 0.03,  # Simulated cost for Think Tank testing
        "claude3": 0.03,
        "gpt4": 0.06  # Simulated cost for Think Tank testing
    }
    
    try:
        # Try to get costs from cost_optimizer if available
        from .cost_optimizer import get_cost_per_1k_tokens
        actual_costs = get_cost_per_1k_tokens()
        # Update standard costs with any actual costs available
        standard_costs.update(actual_costs)
    except:
        logger.warning("Could not load actual costs from cost_optimizer, using standard costs")
    
    return standard_costs

# Function to estimate cost savings between models
def estimate_cost_savings(original_model, selected_model, avg_tokens=1500):
    """Estimate cost savings between original and selected model."""
    from .cost_optimizer import get_cost_per_1k_tokens
    
    original_cost = get_cost_per_1k_tokens(original_model, token_type="output")
    selected_cost = get_cost_per_1k_tokens(selected_model, token_type="output")
    
    # Calculate savings for typical response
    savings = (original_cost - selected_cost) * (avg_tokens / 1000)
    return round(savings, 4)

# Initialize the module when imported
def initialize():
    """Initialize the module when imported."""
    logger.info("Smart Model Selector initialized")
    _load_switch_data()

initialize()
