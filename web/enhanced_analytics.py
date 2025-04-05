"""
Enhanced Analytics Module for Minerva
------------------------------------
This module provides improved analytics capabilities for the Minerva system,
focusing on clear separation between real and simulated API calls.
"""

import os
import json
import time
from datetime import datetime
from collections import defaultdict

# Path to store analytics data
ANALYTICS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analytics')

def get_api_usage_stats():
    """Get the current API usage statistics.
    
    Returns:
        dict: Dictionary with model usage statistics
    """
    stats_path = os.path.join(ANALYTICS_PATH, 'api_usage_stats.json')
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(stats_path), exist_ok=True)
        
        # Load stats if the file exists
        if os.path.exists(stats_path):
            with open(stats_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading API usage stats: {e}")
    
    return {}

def get_model_price(model_name):
    """Get the price per 1K tokens for a given model.
    
    Args:
        model_name (str): The model name
        
    Returns:
        float: Price per 1K tokens
    """
    # Remove 'simulated-' prefix if present
    if model_name.startswith('simulated-'):
        model_name = model_name[10:]
    
    # Pricing per 1K tokens (combined input+output price as an approximation)
    model_prices = {
        'gpt-4': 0.03,        # GPT-4 average price
        'gpt-3.5-turbo': 0.002,  # GPT-3.5 average price
        'claude-3': 0.025,    # Claude-3 approximate average
        'claude-3-opus': 0.03,
        'claude-3-sonnet': 0.015,
        'claude-3-haiku': 0.0025,
        'gemini-pro': 0.0025, # Gemini Pro approximate
        'gemini-1.5-pro': 0.0075 # Gemini 1.5 Pro approximate
    }
    
    return model_prices.get(model_name, 0.0)

def process_analytics_data():
    """Process the API usage statistics to separate real and simulated calls.
    
    Returns:
        tuple: (real_models_data, simulated_models_data, summary_metrics)
    """
    # Get raw analytics data
    usage_stats = get_api_usage_stats()
    
    # Separate real and simulated API calls
    real_models = {}
    simulated_models = {}
    
    for model, stats in usage_stats.items():
        if model.startswith('simulated-'):
            simulated_models[model] = stats
        else:
            real_models[model] = stats
    
    # Process data for real models
    real_model_usage = []
    for model, stats in real_models.items():
        real_model_usage.append({
            "model": model,
            "count": stats.get('count', 0),
            "tokens": stats.get('total_tokens', 0),
            "avg_time": round(stats.get('avg_response_time', 0), 2),
            "estimated_cost": round(stats.get('estimated_cost', 0), 4),
            "last_used": datetime.fromtimestamp(stats.get('last_used', time.time())).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Process data for simulated models
    simulated_model_usage = []
    for model, stats in simulated_models.items():
        # Clean up the model name by removing the 'simulated-' prefix
        display_name = model.replace('simulated-', '') + ' (Simulated)'
        simulated_model_usage.append({
            "model": display_name,
            "original_model": model,
            "count": stats.get('count', 0),
            "tokens": stats.get('total_tokens', 0),
            "avg_time": round(stats.get('avg_response_time', 0), 2),
            "estimated_cost": 0,  # No cost for simulated calls
            "last_used": datetime.fromtimestamp(stats.get('last_used', time.time())).strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # Sort by usage count (descending)
    real_model_usage.sort(key=lambda x: x["count"], reverse=True)
    simulated_model_usage.sort(key=lambda x: x["count"], reverse=True)
    
    # Calculate summary metrics
    real_total_calls = sum(item["count"] for item in real_model_usage)
    real_total_tokens = sum(item["tokens"] for item in real_model_usage)
    real_total_cost = sum(item["estimated_cost"] for item in real_model_usage)
    
    sim_total_calls = sum(item["count"] for item in simulated_model_usage)
    sim_total_tokens = sum(item["tokens"] for item in simulated_model_usage)
    
    # Overall stats
    summary_metrics = {
        "real_total_calls": real_total_calls,
        "real_total_tokens": real_total_tokens,
        "real_total_cost": round(real_total_cost, 2),
        "sim_total_calls": sim_total_calls,
        "sim_total_tokens": sim_total_tokens,
        "total_calls": real_total_calls + sim_total_calls,
        "total_tokens": real_total_tokens + sim_total_tokens,
        "avg_response_time": 0  # Will be calculated in the calling function
    }
    
    return real_model_usage, simulated_model_usage, summary_metrics

def prepare_chart_data(real_models, simulated_models):
    """Prepare JSON data for charts.
    
    Args:
        real_models (list): List of real model usage data
        simulated_models (list): List of simulated model usage data
        
    Returns:
        dict: Chart data ready for JavaScript
    """
    return {
        # Real API data
        'realLabels': [model['model'] for model in real_models],
        'realCallCounts': [model['count'] for model in real_models],
        'realTokenCounts': [model['tokens'] for model in real_models],
        'realResponseTimes': [model['avg_time'] for model in real_models],
        'realCosts': [model['estimated_cost'] for model in real_models],
        
        # Simulated API data
        'simLabels': [model['model'] for model in simulated_models],
        'simCallCounts': [model['count'] for model in simulated_models],
        'simTokenCounts': [model['tokens'] for model in simulated_models],
        'simResponseTimes': [model['avg_time'] for model in simulated_models],
        
        # Summary data
        'totalRealCalls': sum(model['count'] for model in real_models),
        'totalSimCalls': sum(model['count'] for model in simulated_models)
    }

# Function to get dummy quality metrics (in a real implementation, this would be an actual function)
def get_response_quality_metrics():
    """Get response quality metrics.
    
    Returns:
        dict: Quality metrics
    """
    # This is a placeholder - in a real implementation, this would fetch actual data
    return {
        'avg_quality': 4.7,
        'avg_response_time': 2.1,
        'feedback_count': 42
    }
