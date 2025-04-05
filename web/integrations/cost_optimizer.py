#!/usr/bin/env python3
"""
AI Cost Optimizer System

This module provides tools to optimize AI model selection based on cost efficiency
and implements smart model switching logic to reduce unnecessary expenses.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
import os
from datetime import datetime, timedelta
import json

from .usage_tracking import MODEL_PRICING, get_usage_stats, get_tracker
from .config import OPENAI_API_KEY, ANTHROPIC_API_KEY, MISTRAL_API_KEY, GOOGLE_API_KEY, COHERE_API_KEY

# Set up logging
logger = logging.getLogger(__name__)

# Model complexity tiers
MODEL_COMPLEXITY_TIERS = {
    'low': {
        'openai': ['gpt-3.5-turbo'],
        'anthropic': ['claude-3.5-haiku'],
        'mistral': ['mistral-small'],
        'google': ['gemini-flash'],
        'cohere': ['cohere-command-light'],
    },
    'medium': {
        'openai': ['gpt-4o-mini'],
        'anthropic': ['claude-3.5-sonnet'],
        'mistral': ['mistral-medium'],
        'google': ['gemini-pro'],
        'cohere': ['cohere-command'],
    },
    'high': {
        'openai': ['gpt-4o', 'gpt-4'],
        'anthropic': ['claude-3-opus'],
        'mistral': ['mistral-large'],
        'google': ['gemini-1.5-pro'],
        'cohere': ['cohere-command-r'],
    }
}

# Query complexity indicators
COMPLEXITY_INDICATORS = {
    'low': [
        'simple question', 'quick answer', 'basic information',
        'definition', 'synonym', 'antonym', 'short explanation',
        'common knowledge', 'general question', 'straightforward',
    ],
    'high': [
        'complex', 'detailed analysis', 'comprehensive',
        'in-depth', 'technical', 'advanced', 'specialized',
        'nuanced', 'elaborate', 'explain thoroughly',
        'compare and contrast', 'step-by-step explanation',
        'multifaceted', 'complicated', 'intricate',
    ],
}

# Default budget thresholds by period (in USD) - Increased significantly for reliability
DEFAULT_BUDGET_THRESHOLDS = {
    'daily': 250.0,     # Increased 10x
    'weekly': 1500.0,   # Increased 10x
    'monthly': 5000.0,  # Increased 10x
    'emergency': 10000.0,  # Increased 10x - Absolute emergency threshold that triggers cost-cutting
}

# Load custom budget settings if they exist
BUDGET_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                '..', '..', 'data', 'budget_config.json')

def load_budget_config() -> Dict[str, float]:
    """Load budget configuration from file or use defaults"""
    if os.path.exists(BUDGET_CONFIG_PATH):
        try:
            with open(BUDGET_CONFIG_PATH, 'r') as f:
                custom_config = json.load(f)
                # Validate the loaded config
                for key in DEFAULT_BUDGET_THRESHOLDS:
                    if key not in custom_config or not isinstance(custom_config[key], (int, float)):
                        custom_config[key] = DEFAULT_BUDGET_THRESHOLDS[key]
                return custom_config
        except Exception as e:
            logger.error(f"Error loading budget config: {str(e)}")
    
    return DEFAULT_BUDGET_THRESHOLDS

def save_budget_config(config: Dict[str, float]) -> bool:
    """Save budget configuration to file"""
    try:
        os.makedirs(os.path.dirname(BUDGET_CONFIG_PATH), exist_ok=True)
        with open(BUDGET_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving budget config: {str(e)}")
        return False

# Initialize budget thresholds
BUDGET_THRESHOLDS = load_budget_config()

def estimate_query_complexity(message: str, system_prompt: str) -> str:
    """
    Estimate the complexity of a query based on content analysis.
    
    Args:
        message: User message
        system_prompt: System prompt
        
    Returns:
        Complexity level: 'low', 'medium', or 'high'
    """
    # Combine message and system prompt for analysis
    combined_text = (message + " " + system_prompt).lower()
    
    # Check for high complexity indicators
    for indicator in COMPLEXITY_INDICATORS['high']:
        if indicator.lower() in combined_text:
            return 'high'
    
    # Check for low complexity indicators
    low_complexity_count = 0
    for indicator in COMPLEXITY_INDICATORS['low']:
        if indicator.lower() in combined_text:
            low_complexity_count += 1
    
    # If multiple low complexity indicators are found, likely a simple query
    if low_complexity_count >= 2:
        return 'low'
    
    # Default to medium complexity if no clear indicators
    # Message length can also be an indicator
    if len(message) < 100:
        return 'low'
    elif len(message) > 500:
        return 'high'
    
    return 'medium'

def get_provider_from_model(model_name: str) -> str:
    """Determine the provider from a model name"""
    model_name = model_name.lower()
    
    if any(x in model_name for x in ['gpt', 'openai']):
        return 'openai'
    elif 'claude' in model_name:
        return 'anthropic'
    elif any(x in model_name for x in ['mistral', 'llama']):
        return 'mistral'
    elif 'gemini' in model_name:
        return 'google'
    elif 'cohere' in model_name:
        return 'cohere'
    elif 'gpt4all' in model_name:
        return 'local'
    
    return 'unknown'

def get_available_providers() -> Set[str]:
    """Get the set of available model providers based on API keys"""
    providers = set()
    
    if OPENAI_API_KEY:
        providers.add('openai')
    if ANTHROPIC_API_KEY:
        providers.add('anthropic')
    if MISTRAL_API_KEY:
        providers.add('mistral')
    if GOOGLE_API_KEY:
        providers.add('google')
    if COHERE_API_KEY:
        providers.add('cohere')
    
    # Always add local providers
    providers.add('local')
    
    return providers

def get_cost_optimized_model(
    requested_model: str,
    message: str,
    system_prompt: str,
    available_models: List[str],
    force_requested: bool = False
) -> str:
    """
    Get the most cost-effective model for a given query.
    
    Args:
        requested_model: The model originally requested
        message: User message
        system_prompt: System prompt
        available_models: List of available models
        force_requested: If True, always use the requested model
    
    Returns:
        The model name to use (may be different from requested)
    """
    # If forcing the requested model, don't perform optimization
    if force_requested:
        return requested_model
    
    # Get query complexity
    complexity = estimate_query_complexity(message, system_prompt)
    
    # Get the provider for the requested model
    requested_provider = get_provider_from_model(requested_model)
    
    # If it's a local model, always use it
    if requested_provider == 'local':
        return requested_model
    
    # If it's an unknown provider, fall back to the requested model
    if requested_provider == 'unknown':
        return requested_model
    
    # Get all available providers
    available_providers = get_available_providers()
    
    # Filter providers to those that are available
    if requested_provider not in available_providers:
        # Find an alternative provider
        if len(available_providers) == 0:
            return requested_model  # No alternatives available
        
        # Pick the first available provider
        requested_provider = next(iter(available_providers))
    
    # Get models in the appropriate complexity tier
    if complexity == 'low':
        # For low complexity, use the cheapest model from the provider
        target_models = MODEL_COMPLEXITY_TIERS['low'].get(requested_provider, [])
    elif complexity == 'medium':
        # For medium complexity, use a mid-tier model
        target_models = MODEL_COMPLEXITY_TIERS['medium'].get(requested_provider, [])
    else:
        # For high complexity, use the requested model
        return requested_model
    
    # Filter to models that are actually available
    available_tier_models = [m for m in target_models if m in available_models]
    
    # If no models in the appropriate tier are available, fall back to the requested model
    if not available_tier_models:
        return requested_model
    
    # Return the first available model in the appropriate tier
    return available_tier_models[0]

def get_cost_per_1k_tokens(model_name: str, token_type: str = None) -> Tuple[float, float]:
    """
    Get the cost per 1k tokens for a given model.
    
    Args:
        model_name: The model name
        token_type: Optional, type of tokens to get cost for ('input' or 'output')
        
    Returns:
        Tuple of (input_cost_per_1k, output_cost_per_1k) in USD
    """
    # Normalize model name to match pricing keys
    normalized_name = model_name.lower()
    
    # Try to match the model with our pricing data
    for pricing_model, prices in MODEL_PRICING.items():
        if pricing_model.lower() in normalized_name:
            try:
                # Handle both tuple and dictionary formats for backward compatibility
                if isinstance(prices, (list, tuple)) and len(prices) == 2:
                    input_price, output_price = prices
                elif isinstance(prices, dict):
                    input_price = prices.get('input', 5.0)
                    output_price = prices.get('output', 15.0)
                else:
                    input_price, output_price = 5.0, 15.0
                
                # Convert from price per million to price per 1k
                input_cost = input_price / 1000
                output_cost = output_price / 1000
                
                # If token_type is specified, return just that cost
                if token_type == "input":
                    return (input_cost, 0.0)
                elif token_type == "output":
                    return (0.0, output_cost)
                else:
                    return (input_cost, output_cost)
            except Exception as e:
                logger.error(f"Error processing pricing for {model_name}: {e}")
                break
    
    # If no match found, use default pricing
    default_input, default_output = 5.0, 15.0
    try:
        default_pricing = MODEL_PRICING.get('default')
        if isinstance(default_pricing, (list, tuple)) and len(default_pricing) == 2:
            default_input, default_output = default_pricing
        elif isinstance(default_pricing, dict):
            default_input = default_pricing.get('input', 5.0)
            default_output = default_pricing.get('output', 15.0)
    except Exception as e:
        logger.error(f"Error getting default pricing: {e}")
    
    input_cost = default_input / 1000
    output_cost = default_output / 1000
    
    # Handle token type for default case
    if token_type == "input":
        return (input_cost, 0.0)
    elif token_type == "output":
        return (0.0, output_cost)
    else:
        return (input_cost, output_cost)

def rank_models_by_cost_efficiency(
    available_models: List[str], 
    query_type: str = 'general'
) -> List[Tuple[str, float]]:
    """
    Rank available models by their cost efficiency based on historical usage.
    
    Args:
        available_models: List of available models
        query_type: Type of query (optional)
        
    Returns:
        List of (model_name, efficiency_score) tuples, sorted by efficiency
    """
    # Get usage stats for the past month
    stats = get_usage_stats(period='month', query_type=query_type)
    
    model_efficiency = []
    
    for model in available_models:
        # Get base cost per token
        input_cost, output_cost = get_cost_per_1k_tokens(model)
        
        # Calculate efficiency score (lower is better)
        # Default to just the raw costs if no historical data
        efficiency_score = input_cost + (output_cost * 2)  # Output tokens are generally more expensive
        
        # If we have historical data for this model, factor that in
        if model in stats['models']:
            model_stats = stats['models'][model]
            
            # Success rate is important for efficiency
            success_rate = model_stats.get('success_rate', 0.95)
            
            # Factor in success rate (failed requests waste money)
            efficiency_score = efficiency_score / max(success_rate, 0.5)
            
            # Factor in average response quality if available
            if 'avg_quality_score' in model_stats and model_stats['avg_quality_score'] > 0:
                quality_score = model_stats['avg_quality_score'] / 10.0  # Normalize to 0-1 range
                efficiency_score = efficiency_score / max(quality_score, 0.5)
        
        model_efficiency.append((model, efficiency_score))
    
    # Sort by efficiency score (lower is better)
    return sorted(model_efficiency, key=lambda x: x[1])

def is_budget_exceeded(threshold_type: str = 'daily') -> bool:
    """
    Check if the budget for a given period has been exceeded.
    
    Args:
        threshold_type: Type of threshold to check ('daily', 'weekly', 'monthly', 'emergency')
        
    Returns:
        True if budget is exceeded, False otherwise
    """
    # Get the appropriate time period for the threshold
    if threshold_type == 'daily':
        period = 'today'
    elif threshold_type == 'weekly':
        period = 'week'
    elif threshold_type == 'monthly' or threshold_type == 'emergency':
        period = 'month'
    else:
        period = 'month'  # Default to monthly
    
    # Get usage stats for the period
    stats = get_usage_stats(period=period)
    
    # Get total cost
    total_cost = stats['summary'].get('total_cost', 0.0)
    
    # Get the threshold for this period
    threshold = BUDGET_THRESHOLDS.get(threshold_type, DEFAULT_BUDGET_THRESHOLDS[threshold_type])
    
    # Check if the budget is exceeded
    return total_cost > threshold

def get_budget_status() -> Dict[str, Any]:
    """
    Get the current budget status for all periods.
    
    Returns:
        Dict containing budget status information
    """
    # Get usage stats for different periods
    today_stats = get_usage_stats(period='today')
    week_stats = get_usage_stats(period='week')
    month_stats = get_usage_stats(period='month')
    
    # Get daily, weekly, and monthly costs
    daily_cost = today_stats['summary'].get('total_cost', 0.0)
    weekly_cost = week_stats['summary'].get('total_cost', 0.0)
    monthly_cost = month_stats['summary'].get('total_cost', 0.0)
    
    # Calculate percentage of budget used
    daily_pct = (daily_cost / BUDGET_THRESHOLDS['daily']) * 100 if BUDGET_THRESHOLDS['daily'] > 0 else 0
    weekly_pct = (weekly_cost / BUDGET_THRESHOLDS['weekly']) * 100 if BUDGET_THRESHOLDS['weekly'] > 0 else 0
    monthly_pct = (monthly_cost / BUDGET_THRESHOLDS['monthly']) * 100 if BUDGET_THRESHOLDS['monthly'] > 0 else 0
    
    # Determine status levels
    daily_status = 'critical' if daily_pct >= 100 else 'warning' if daily_pct >= 80 else 'normal'
    weekly_status = 'critical' if weekly_pct >= 100 else 'warning' if weekly_pct >= 80 else 'normal'
    monthly_status = 'critical' if monthly_pct >= 100 else 'warning' if monthly_pct >= 80 else 'normal'
    
    # Check if emergency threshold is reached
    emergency_mode = monthly_cost > BUDGET_THRESHOLDS['emergency']
    
    return {
        'daily': {
            'cost': daily_cost,
            'budget': BUDGET_THRESHOLDS['daily'],
            'percentage': daily_pct,
            'status': daily_status,
        },
        'weekly': {
            'cost': weekly_cost,
            'budget': BUDGET_THRESHOLDS['weekly'],
            'percentage': weekly_pct,
            'status': weekly_status,
        },
        'monthly': {
            'cost': monthly_cost,
            'budget': BUDGET_THRESHOLDS['monthly'],
            'percentage': monthly_pct,
            'status': monthly_status,
        },
        'emergency_mode': emergency_mode,
        'thresholds': BUDGET_THRESHOLDS,
    }

def update_budget_thresholds(new_thresholds: Dict[str, float]) -> bool:
    """
    Update budget thresholds with new values.
    
    Args:
        new_thresholds: Dict containing new threshold values
        
    Returns:
        True if update was successful, False otherwise
    """
    global BUDGET_THRESHOLDS
    
    # Validate the new thresholds
    for key in DEFAULT_BUDGET_THRESHOLDS:
        if key in new_thresholds and isinstance(new_thresholds[key], (int, float)) and new_thresholds[key] >= 0:
            BUDGET_THRESHOLDS[key] = new_thresholds[key]
    
    # Save the updated thresholds
    return save_budget_config(BUDGET_THRESHOLDS)


def get_cost_analysis_data(period: str = 'month') -> Dict[str, Any]:
    """
    Get comprehensive cost analysis data for the AI models.
    
    Args:
        period: Time period for analysis ('today', 'week', 'month', 'quarter', 'year')
        
    Returns:
        Dictionary with cost analysis data including total costs, savings, and model distribution
    """    
    from .usage_tracking import get_usage_stats
    
    # Get usage statistics
    usage_stats = get_usage_stats(period=period)
    
    # Calculate cost savings
    savings = calculate_cost_savings(period=period)
    
    # Get model distribution
    model_distribution = get_model_cost_distribution(period=period)
    
    # Prepare response data
    return {
        'total_cost': usage_stats.get('total_cost', 0),
        'total_requests': usage_stats.get('total_requests', 0),
        'cost_savings': savings.get('amount', 0),
        'savings_percentage': savings.get('percentage', 0),
        'potential_cost': savings.get('potential_cost', 0),
        'model_distribution': model_distribution,
        'period': period
    }

def calculate_cost_savings(period: str = 'month') -> Dict[str, float]:
    """
    Calculate cost savings based on model selection optimization.
    
    Args:
        period: Time period for calculation ('today', 'week', 'month', 'quarter', 'year')
        
    Returns:
        Dictionary with savings amount, percentage, and potential cost
    """
    from .usage_tracking import get_usage_stats
    
    # Get usage statistics
    usage_stats = get_usage_stats(period=period)
    
    # Calculate actual cost
    actual_cost = usage_stats.get('total_cost', 0)
    
    # Calculate potential cost if all queries used the most expensive model
    models_data = usage_stats.get('models', {})
    total_queries = usage_stats.get('total_requests', 0)
    
    if not models_data or total_queries == 0:
        return {
            'amount': 0,
            'percentage': 0,
            'potential_cost': 0
        }
    
    # Find the most expensive model
    most_expensive_model = max(models_data.items(), key=lambda x: x[1].get('avg_cost_per_request', 0))
    max_cost_per_request = most_expensive_model[1].get('avg_cost_per_request', 0)
    
    # Calculate potential cost
    potential_cost = max_cost_per_request * total_queries
    
    # Calculate savings
    savings_amount = max(0, potential_cost - actual_cost)
    savings_percentage = (savings_amount / potential_cost * 100) if potential_cost > 0 else 0
    
    return {
        'amount': savings_amount,
        'percentage': savings_percentage,
        'potential_cost': potential_cost
    }

def get_model_cost_distribution(period: str = 'month') -> Dict[str, Dict[str, float]]:
    """
    Get the cost distribution across different models.
    
    Args:
        period: Time period for analysis ('today', 'week', 'month', 'quarter', 'year')
        
    Returns:
        Dictionary with model distribution data
    """
    from .usage_tracking import get_usage_stats
    
    # Get usage statistics
    usage_stats = get_usage_stats(period=period)
    models_data = usage_stats.get('models', {})
    
    # Format model distribution data
    distribution = {}
    for model, data in models_data.items():
        distribution[model] = {
            'cost': data.get('total_cost', 0),
            'requests': data.get('requests', 0),
            'avg_cost_per_request': data.get('avg_cost_per_request', 0),
            'percentage': (data.get('total_cost', 0) / usage_stats.get('total_cost', 1)) * 100 if usage_stats.get('total_cost', 0) > 0 else 0
        }
    
    return distribution

def predict_costs(days: int = 30) -> List[Dict[str, Any]]:
    """
    Predict future costs based on historical usage patterns.
    
    Args:
        days: Number of days to predict
        
    Returns:
        List of daily cost predictions
    """
    import numpy as np
    from datetime import datetime, timedelta
    from .usage_tracking import get_daily_usage_stats
    
    # Get daily usage stats for the last 30 days
    daily_stats = [get_daily_usage_stats(datetime.now() - timedelta(days=i)) for i in range(30, 0, -1)]
    
    # Extract daily costs
    daily_costs = [stats.get('total_cost', 0) for stats in daily_stats]
    
    # Calculate average daily cost and standard deviation
    avg_daily_cost = np.mean(daily_costs) if daily_costs else 0
    std_daily_cost = np.std(daily_costs) if daily_costs else 0
    
    # Generate predictions
    predictions = []
    for i in range(1, days + 1):
        # Simple linear projection with some randomness
        projected_cost = avg_daily_cost * (1 + (i * 0.01))  # Assume 1% growth per day
        upper_bound = projected_cost + (std_daily_cost * 1.5)
        lower_bound = max(0, projected_cost - (std_daily_cost * 1.5))
        
        predictions.append({
            'day': i,
            'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
            'projected_cost': projected_cost,
            'upper_bound': upper_bound,
            'lower_bound': lower_bound
        })
    
    return predictions


def simulate_cost_scenario(current_monthly_cost: float, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a cost scenario based on provided parameters.
    
    Args:
        current_monthly_cost: Current monthly cost as baseline
        params: Dictionary with scenario parameters:
            - usage_change: Percentage change in usage volume (-100 to +100)
            - model_mix_change: Percentage shift to cheaper models (-100 to +100)
            - efficiency_gains: Percentage efficiency improvements (0 to 100)
            - time_horizon: Number of months to project (1 to 12)
            - budget_cap: Monthly budget cap (optional)
            
    Returns:
        Dictionary with projected costs and savings
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # Extract parameters with defaults
    usage_change = params.get('usage_change', 0)  # Percentage
    model_mix_change = params.get('model_mix_change', 0)  # Percentage
    efficiency_gains = params.get('efficiency_gains', 0)  # Percentage
    time_horizon = min(max(1, params.get('time_horizon', 3)), 12)  # Cap at 12 months
    budget_cap = params.get('budget_cap')  # Optional cap
    
    # Validate input parameters
    if usage_change < -100 or usage_change > 100:
        usage_change = max(-100, min(100, usage_change))
    
    if model_mix_change < -100 or model_mix_change > 100:
        model_mix_change = max(-100, min(100, model_mix_change))
    
    if efficiency_gains < 0 or efficiency_gains > 100:
        efficiency_gains = max(0, min(100, efficiency_gains))
    
    # Calculate impact of usage change
    # A positive usage_change means more usage, increasing cost
    usage_factor = 1 + (usage_change / 100)
    
    # Calculate impact of model mix change
    # A positive model_mix_change means shifting to cheaper models, decreasing cost
    # A 100% shift would give a 0.5x factor (50% cost reduction)
    mix_factor = 1 - ((model_mix_change / 100) * 0.5)
    
    # Calculate impact of efficiency gains
    # Efficiency gains directly reduce costs
    efficiency_factor = 1 - (efficiency_gains / 100)
    
    # Calculate base monthly projected cost
    base_monthly_cost = current_monthly_cost * usage_factor * mix_factor * efficiency_factor
    
    # Apply budget cap if specified
    capped_monthly_cost = min(base_monthly_cost, budget_cap) if budget_cap is not None else base_monthly_cost
    
    # Generate monthly projections
    monthly_projections = []
    for month in range(1, time_horizon + 1):
        # Add slight growth over time (0.5% monthly growth)
        growth_factor = 1 + (0.005 * (month - 1))
        monthly_cost = base_monthly_cost * growth_factor
        
        # Apply budget cap
        if budget_cap is not None:
            monthly_cost = min(monthly_cost, budget_cap)
        
        # Calculate monthly savings from baseline (if any)
        baseline = current_monthly_cost * growth_factor
        savings = max(0, baseline - monthly_cost)
        
        monthly_projections.append({
            'month': month,
            'date': (datetime.now() + timedelta(days=30 * month)).strftime('%Y-%m'),
            'projected_cost': monthly_cost,
            'baseline_cost': baseline,
            'savings': savings,
            'is_capped': budget_cap is not None and monthly_cost >= budget_cap
        })
    
    # Calculate cumulative costs and savings
    cumulative_baseline = sum(m['baseline_cost'] for m in monthly_projections)
    cumulative_projected = sum(m['projected_cost'] for m in monthly_projections)
    cumulative_savings = sum(m['savings'] for m in monthly_projections)
    
    # Generate recommendations based on scenario
    recommendations = []
    
    if model_mix_change > 0:
        recommendations.append({
            'text': f"Shifting {model_mix_change:.0f}% to cheaper models could save ${cumulative_savings:.2f} over {time_horizon} months.",
            'type': 'model_mix'
        })
    
    if efficiency_gains > 0:
        recommendations.append({
            'text': f"Implementing {efficiency_gains:.0f}% efficiency improvements through prompt optimization.",
            'type': 'efficiency'
        })
    
    if budget_cap is not None and any(m['is_capped'] for m in monthly_projections):
        recommendations.append({
            'text': f"Budget cap of ${budget_cap:.2f} will be reached and may limit AI capabilities.",
            'type': 'warning'
        })
    
    # Default recommendation if none apply
    if not recommendations:
        if cumulative_projected > cumulative_baseline:
            recommendations.append({
                'text': f"This scenario will increase costs by ${cumulative_projected - cumulative_baseline:.2f} over {time_horizon} months.",
                'type': 'cost_increase'
            })
        else:
            recommendations.append({
                'text': f"This scenario appears sustainable within current budget parameters.",
                'type': 'sustainable'
            })
    
    return {
        'scenario_name': params.get('scenario_name', 'Untitled Scenario'),
        'time_horizon': time_horizon,
        'parameters': {
            'usage_change': usage_change,
            'model_mix_change': model_mix_change,
            'efficiency_gains': efficiency_gains,
            'budget_cap': budget_cap
        },
        'current_monthly_cost': current_monthly_cost,
        'projected_monthly_cost': monthly_projections[0]['projected_cost'],
        'total_projected_cost': cumulative_projected,
        'total_baseline_cost': cumulative_baseline,
        'total_savings': cumulative_savings,
        'monthly_projections': monthly_projections,
        'recommendations': recommendations
    }

def identify_optimization_opportunities() -> List[Dict[str, Any]]:
    """
    Identify cost optimization opportunities based on usage patterns.
    
    Returns:
        List of optimization opportunities with descriptions and potential savings
    """
    from .usage_tracking import get_usage_stats
    
    opportunities = []
    
    # Get monthly usage stats
    monthly_stats = get_usage_stats(period='month')
    models_data = monthly_stats.get('models', {})
    
    # Check if we're using expensive models for simple queries
    model_efficiency = rank_models_by_cost_efficiency(list(models_data.keys()))
    
    expensive_models_usage = []
    for model, data in models_data.items():
        if model in model_efficiency[-3:]:  # Check the bottom 3 in efficiency
            expensive_models_usage.append({
                'model': model,
                'requests': data.get('requests', 0),
                'cost': data.get('total_cost', 0)
            })
    
    if expensive_models_usage:
        total_expensive_cost = sum(m['cost'] for m in expensive_models_usage)
        potential_savings = total_expensive_cost * 0.4  # Assume 40% could be saved
        
        opportunities.append({
            'id': 'expensive_models',
            'title': 'Optimize High-Cost Model Usage',
            'description': f"You're using expensive models like {', '.join([m['model'] for m in expensive_models_usage])} for {sum([m['requests'] for m in expensive_models_usage])} requests this month. Consider using more cost-effective models for appropriate tasks.",
            'potential_savings': potential_savings,
            'difficulty': 'medium',
            'priority': 'high' if potential_savings > 100 else 'medium',
            'implementation': 'Adjust model selection criteria in ensemble_manager.py to prioritize cost efficiency for appropriate query types.'
        })
    
    # Check for underutilized caching
    cache_hit_rate = monthly_stats.get('cache_hit_rate', 0)
    if cache_hit_rate < 0.5:  # Less than 50% cache hit rate
        cache_opportunity_savings = monthly_stats.get('total_cost', 0) * 0.2  # Assume 20% savings
        
        opportunities.append({
            'id': 'improve_caching',
            'title': 'Enhance Response Caching',
            'description': f"Your cache hit rate is only {cache_hit_rate*100:.1f}%. Improving caching strategies could reduce redundant API calls.",
            'potential_savings': cache_opportunity_savings,
            'difficulty': 'easy',
            'priority': 'high' if cache_opportunity_savings > 50 else 'medium',
            'implementation': 'Adjust cache TTL in cache_manager.py and expand semantic caching to cover more query types.'
        })
    
    # Check for low-value queries
    if monthly_stats.get('low_value_queries_percentage', 0) > 0.1:  # More than 10%
        low_value_savings = monthly_stats.get('total_cost', 0) * 0.15  # Assume 15% savings
        
        opportunities.append({
            'id': 'reduce_low_value',
            'title': 'Reduce Low-Value Queries',
            'description': f"About {monthly_stats.get('low_value_queries_percentage', 0)*100:.1f}% of queries generate minimal user engagement. Consider pre-filtering these queries.",
            'potential_savings': low_value_savings,
            'difficulty': 'hard',
            'priority': 'medium',
            'implementation': 'Implement user engagement tracking and use it to identify and filter out low-value query patterns.'
        })
    
    # Check for budget alert optimization
    budget_status = get_budget_status()
    if not budget_status.get('alerts_enabled', False):
        opportunities.append({
            'id': 'enable_budget_alerts',
            'title': 'Enable Budget Alerts',
            'description': "You haven't set up budget alerts. Configure alerts to prevent unexpected cost overruns.",
            'potential_savings': monthly_stats.get('total_cost', 0) * 0.1,  # Assume 10% savings
            'difficulty': 'easy',
            'priority': 'high',
            'implementation': 'Configure budget thresholds and enable email/Slack notifications in the dashboard.'
        })
    
    return opportunities

def simulate_cost_scenario(current_monthly_cost: float, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate a cost scenario based on provided parameters.
    
    Args:
        current_monthly_cost: Current monthly cost as baseline
        params: Dictionary with scenario parameters:
            - usage_change: Percentage change in usage volume (-100 to +100)
            - model_mix_change: Percentage shift to cheaper models (-100 to +100)
            - efficiency_gains: Percentage efficiency improvements (0 to 100)
            - time_horizon: Number of months to project (1 to 12)
            - budget_cap: Monthly budget cap (optional)
            
    Returns:
        Dictionary with projected costs and savings
    """
    # Validate inputs
    usage_change = max(-100, min(100, params.get('usage_change', 0)))
    model_mix_change = max(-100, min(100, params.get('model_mix_change', 0)))
    efficiency_gains = max(0, min(100, params.get('efficiency_gains', 0)))
    time_horizon = max(1, min(12, params.get('time_horizon', 3)))
    budget_cap = params.get('budget_cap', None)
    
    # Calculate monthly impact of each factor
    usage_factor = 1 + (usage_change / 100)
    model_mix_factor = 1 - (model_mix_change / 100) * 0.3  # Assume max 30% impact from model mix
    efficiency_factor = 1 - (efficiency_gains / 100)
    
    # Calculate baseline projection without optimizations
    baseline_projection = [current_monthly_cost * (1 + (i * 0.03)) for i in range(time_horizon)]  # Assume 3% monthly growth
    
    # Calculate optimized projection
    optimized_projection = []
    for i in range(time_horizon):
        month_projection = baseline_projection[i] * usage_factor * model_mix_factor * efficiency_factor
        
        # Apply budget cap if specified
        if budget_cap is not None and month_projection > budget_cap:
            month_projection = budget_cap
            
        optimized_projection.append(month_projection)
    
    # Calculate total baseline and optimized costs
    total_baseline = sum(baseline_projection)
    total_optimized = sum(optimized_projection)
    total_savings = total_baseline - total_optimized
    
    return {
        'baseline_projection': baseline_projection,
        'optimized_projection': optimized_projection,
        'total_baseline_cost': total_baseline,
        'total_optimized_cost': total_optimized,
        'total_savings': total_savings,
        'savings_percentage': (total_savings / total_baseline * 100) if total_baseline > 0 else 0,
        'months': list(range(1, time_horizon + 1))
    }

def update_budget_settings(daily_budget: Optional[float] = None,
                          weekly_budget: Optional[float] = None,
                          monthly_budget: Optional[float] = None,
                          emergency_threshold: Optional[float] = None,
                          notification_channels: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update budget settings and notification preferences.
    
    Args:
        daily_budget: Daily budget threshold
        weekly_budget: Weekly budget threshold
        monthly_budget: Monthly budget threshold
        emergency_threshold: Emergency threshold percentage
        notification_channels: Configuration for notification channels
        
    Returns:
        True if update was successful, False otherwise
    """
    new_thresholds = {}
    
    # Update budget thresholds
    if daily_budget is not None:
        new_thresholds['daily'] = max(0, daily_budget)
    
    if weekly_budget is not None:
        new_thresholds['weekly'] = max(0, weekly_budget)
    
    if monthly_budget is not None:
        new_thresholds['monthly'] = max(0, monthly_budget)
    
    if emergency_threshold is not None:
        new_thresholds['emergency_threshold'] = max(0, min(100, emergency_threshold))
    
    # Update budget thresholds
    update_budget_thresholds(new_thresholds)
    
    # Update notification channels if provided
    if notification_channels is not None:
        # Example implementation - would need to be expanded based on notification system
        # Example: notification_channels = {'email': True, 'slack': True, 'email_addresses': ['admin@example.com']}
        # This would be saved to a notification configuration
        pass
    
    return True

def analyze_cost_patterns(period: str = 'month') -> Dict[str, Any]:
    # This function computes cost metrics, savings, projections, and optimization opportunities
    from datetime import datetime, timedelta
    import pandas as pd
    import numpy as np
    
    # Get usage statistics
    usage_stats = get_usage_stats(period=period)
    tracker = get_tracker()
    
    # Get raw data for model predictions
    raw_data = tracker.get_raw_usage_data(days=90)  # Get 90 days of data for forecasting
    df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
    
    # Convert timestamp to datetime
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    
    # Calculate cost metrics
    total_cost = usage_stats['summary']['total_cost']
    total_requests = usage_stats['summary']['total_requests']
    
    # Determine the time window based on period
    if period == 'today':
        days_in_period = 1
    elif period == 'week':
        days_in_period = 7
    elif period == 'month':
        days_in_period = 30
    elif period == 'quarter':
        days_in_period = 90
    elif period == 'year':
        days_in_period = 365
    else:
        days_in_period = 30  # Default to month
    
    # Calculate projected costs using time series forecasting if enough data
    projected_cost = total_cost
    r_value = 0
    if not df.empty and len(df) > 7:  # Need at least a week of data
        try:
            # Group by date and calculate daily costs
            daily_costs = df.groupby('date')['estimated_cost'].sum().reset_index()
            
            # Create a complete date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_in_period-1)
            date_range = pd.date_range(start=start_date, end=end_date)
            
            # Ensure we have data for all dates by reindexing
            daily_costs = daily_costs.set_index('date')
            daily_costs = daily_costs.reindex(date_range.date, fill_value=0)
            
            # Simple linear regression for forecasting
            if len(daily_costs) >= 7:  # Need at least a week of data for forecasting
                x = np.arange(len(daily_costs))
                y = daily_costs['estimated_cost'].values
                
                # Linear regression
                from scipy import stats
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # Project forward based on the trend
                days_to_project = days_in_period  # Project forward for one period
                additional_cost = sum([(slope * (len(daily_costs) + i) + intercept) for i in range(1, days_to_project + 1)])
                projected_cost = max(total_cost * 1.1, total_cost + additional_cost)  # At least 10% increase
            else:
                # If not enough data, use a simple scaling factor
                projected_cost = total_cost * (days_in_period / max(1, len(daily_costs)))
        except Exception as e:
            logger.error(f"Error calculating cost projections: {str(e)}")
            # Fallback to simple projection
            projected_cost = total_cost * 1.2  # 20% increase as fallback
    
    # Calculate cost savings from model switching
    # This calculates how much would have been spent if always using the most expensive model
    savings_data = calculate_cost_savings(period=period)
    cost_savings = savings_data['total_savings']
    potential_cost = total_cost + cost_savings
    
    # Check if emergency mode should be activated based on spending
    emergency_mode = is_budget_exceeded('emergency') or is_budget_exceeded('monthly')
    
    return {
        'total_cost': total_cost,
        'projected_cost': projected_cost,
        'cost_savings': cost_savings,
        'potential_cost': potential_cost,
        'savings_by_model': savings_data['savings_by_model'],
        'total_requests': total_requests,
        'emergency_mode': emergency_mode,
        'cost_optimization_opportunities': identify_optimization_opportunities(),
        'prediction_confidence': min(0.95, max(0.6, r_value ** 2)) if r_value else 0.7,
    }


def calculate_cost_savings_enhanced(period: str = 'month') -> Dict[str, Any]:
    # Calculate cost savings from intelligent model selection
    tracker = get_tracker()
    raw_data = tracker.get_raw_usage_data(period=period)
    
    total_savings = 0.0
    savings_by_model = {}
    
    for entry in raw_data:
        model = entry.get('model', '')
        input_tokens = entry.get('input_tokens', 0)
        output_tokens = entry.get('output_tokens', 0)
        query_type = entry.get('query_type', 'general')
        
        # Skip entries with missing data
        if not model or not input_tokens:
            continue
        
        # Get the current model's cost
        current_cost = entry.get('estimated_cost', 0.0)
        
        # Determine what would have been the most expensive model for this query
        provider = get_provider_from_model(model)
        expensive_models = {
            'openai': 'gpt-4o',
            'anthropic': 'claude-3-opus',
            'mistral': 'mistral-large',
            'google': 'gemini-1.5-pro',
            'cohere': 'cohere-command-r',
            'local': 'gpt4all'  # Local models are already the cheapest
        }
        
        expensive_model = expensive_models.get(provider, model)
        
        # Skip if already using the most expensive model
        if model == expensive_model:
            continue
        
        # Calculate what it would have cost with the expensive model
        expensive_input_cost, expensive_output_cost = get_cost_per_1k_tokens(expensive_model)
        expensive_cost = (input_tokens / 1000.0 * expensive_input_cost) + \
                         (output_tokens / 1000.0 * expensive_output_cost)
        
        # Calculate savings
        savings = max(0, expensive_cost - current_cost)
        total_savings += savings
        
        # Track savings by model
        if model not in savings_by_model:
            savings_by_model[model] = 0.0
        savings_by_model[model] += savings
    
    return {
        'total_savings': total_savings,
        'savings_by_model': savings_by_model
    }


def identify_optimization_opportunities() -> List[Dict[str, Any]]:
    # Identify opportunities to optimize AI model usage and reduce costs
    tracker = get_tracker()
    recent_data = tracker.get_raw_usage_data(days=14)  # Look at last 2 weeks
    
    # Group data by query_type
    query_type_data = {}
    for entry in recent_data:
        query_type = entry.get('query_type', 'general')
        model = entry.get('model', '')
        cost = entry.get('estimated_cost', 0.0)
        
        if query_type not in query_type_data:
            query_type_data[query_type] = {'models': {}, 'total_cost': 0.0, 'count': 0}
            
        if model not in query_type_data[query_type]['models']:
            query_type_data[query_type]['models'][model] = {'cost': 0.0, 'count': 0}
            
        query_type_data[query_type]['models'][model]['cost'] += cost
        query_type_data[query_type]['models'][model]['count'] += 1
        query_type_data[query_type]['total_cost'] += cost
        query_type_data[query_type]['count'] += 1
    
    # Identify optimization opportunities
    opportunities = []
    
    for query_type, data in query_type_data.items():
        # Only consider query types with significant cost
        if data['total_cost'] < 5.0 or data['count'] < 10:
            continue
            
        model_costs = []
        for model, model_data in data['models'].items():
            avg_cost = model_data['cost'] / max(1, model_data['count'])
            model_costs.append((model, avg_cost, model_data['count']))
            
        # Sort by average cost
        model_costs.sort(key=lambda x: x[1], reverse=True)
        
        # If we have multiple models and the most expensive one is used often
        if len(model_costs) > 1 and model_costs[0][2] >= 5:
            expensive_model, expensive_avg, expensive_count = model_costs[0]
            cheaper_model, cheaper_avg, cheaper_count = model_costs[-1]
            
            # If the cost difference is significant
            if expensive_avg > (cheaper_avg * 2) and expensive_avg - cheaper_avg > 0.01:
                savings_per_query = expensive_avg - cheaper_avg
                potential_monthly_savings = savings_per_query * expensive_count * (30 / 14)  # Extrapolate to monthly
                
                opportunities.append({
                    'query_type': query_type,
                    'current_model': expensive_model,
                    'recommended_model': cheaper_model,
                    'average_cost_difference': savings_per_query,
                    'estimated_monthly_savings': potential_monthly_savings,
                    'confidence': min(0.9, max(0.6, expensive_count / 20.0)),  # Higher count = higher confidence
                    'priority': 'high' if potential_monthly_savings > 50 else 
                               'medium' if potential_monthly_savings > 20 else 'low'
                })
    
    # Sort by estimated savings potential
    opportunities.sort(key=lambda x: x['estimated_monthly_savings'], reverse=True)
    
    return opportunities


def export_cost_data(period: str = 'month'):
    # Export cost data as a DataFrame for reporting
    import pandas as pd
    from datetime import datetime
    
    # Get raw data
    tracker = get_tracker()
    raw_data = tracker.get_raw_usage_data(period=period)
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
    
    if df.empty:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['timestamp', 'model', 'query_type', 'input_tokens', 
                                    'output_tokens', 'estimated_cost'])
    
    # Process timestamps
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
    
    # Get cost analysis data
    cost_analysis = get_cost_analysis_data(period=period)
    
    # Add summary row
    summary = pd.DataFrame({
        'timestamp': datetime.now(),
        'model': 'SUMMARY',
        'query_type': 'all',
        'input_tokens': df['input_tokens'].sum(),
        'output_tokens': df['output_tokens'].sum(),
        'estimated_cost': df['estimated_cost'].sum(),
        'total_requests': len(df),
        'projected_monthly_cost': cost_analysis['projected_cost'],
        'cost_savings': cost_analysis['cost_savings']
    }, index=[0])
    
    # Calculate model-specific aggregations
    model_summary = df.groupby('model').agg({
        'estimated_cost': 'sum',
        'input_tokens': 'sum',
        'output_tokens': 'sum',
        'model': 'count'
    }).reset_index()
    
    model_summary.rename(columns={'model': 'model', 'model_count': 'request_count'}, inplace=True)
    
    # Return the processed DataFrame
    return pd.concat([summary, df], ignore_index=True)


def predict_ai_costs(days_ahead: int = 30) -> Dict[str, Any]:
    # Predict future AI costs based on historical usage patterns
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Get historical data
    tracker = get_tracker()
    raw_data = tracker.get_raw_usage_data(days=90)  # Use up to 90 days of historical data
    
    # Prepare data frame
    df = pd.DataFrame(raw_data) if raw_data else pd.DataFrame()
    
    if df.empty:
        return {
            'predicted_costs': [0.0] * days_ahead,
            'prediction_dates': [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_ahead)],
            'confidence': 0.0,
            'total_predicted': 0.0
        }
    
    # Process timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    # Group by date
    daily_costs = df.groupby('date')['estimated_cost'].sum().reset_index()
    
    # Create a complete date range including dates with no usage
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=len(daily_costs.index))
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Reindex to include all dates
    daily_costs = daily_costs.set_index('date')
    daily_costs = daily_costs.reindex(date_range.date, fill_value=0).reset_index()
    daily_costs.rename(columns={'index': 'date'}, inplace=True)
    
    # Simple linear regression for forecasting
    x = np.arange(len(daily_costs))
    y = daily_costs['estimated_cost'].values
    
    # Calculate linear regression
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Predict future costs
    future_dates = [end_date + timedelta(days=i+1) for i in range(days_ahead)]
    future_x = np.arange(len(daily_costs), len(daily_costs) + days_ahead)
    
    # Generate predictions
    predictions = slope * future_x + intercept
    predictions = np.maximum(predictions, 0)  # Ensure no negative costs
    
    # Calculate confidence based on R^2 value and data size
    confidence = min(0.95, max(0.5, r_value**2))  # R^2 is a measure of fit quality
    
    # Adjust confidence based on amount of data
    confidence *= min(1.0, len(daily_costs) / 30.0)  # Full confidence with at least 30 days of data
    
    return {
        'predicted_costs': predictions.tolist(),
        'prediction_dates': [d.strftime('%Y-%m-%d') for d in future_dates],
        'confidence': confidence,
        'total_predicted': float(np.sum(predictions)),
        'trend': 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable',
        'avg_daily_predicted': float(np.mean(predictions))
    }

def get_budget_prediction_data():
    # Generate comprehensive budget prediction data for the dashboard
    # Get current budget status
    budget_status = get_budget_status()
    
    # Predict budget depletion
    depletion_prediction = predict_budget_depletion()
    
    # Get cost recommendations
    recommendations = get_cost_recommendations(
        budget_percentage=budget_status.get('percentage_used', 0),
        days_until_depletion=depletion_prediction.get('days_until_depletion'),
        model_usage_patterns=budget_status.get('model_usage', {})
    )
    
    # Combine all data
    return {
        'current_spend': budget_status.get('current_spend', 0.0),
        'monthly_budget': budget_status.get('monthly_budget', 0.0),
        'percentage_used': budget_status.get('percentage_used', 0.0),
        'days_until_depletion': depletion_prediction.get('days_until_depletion'),
        'predicted_depletion_date': depletion_prediction.get('depletion_date'),
        'trend': depletion_prediction.get('trend', 'stable'),
        'recommendations': recommendations
    }

def get_cost_recommendations(budget_percentage, days_until_depletion=None, model_usage_patterns=None):
    # Simple implementation to avoid docstring issues
    recommendations = []
    
    # Default if no model usage patterns provided
    if model_usage_patterns is None:
        model_usage_patterns = {}
    
    # High priority recommendations for critical budget situations
    if budget_percentage > 90 or (days_until_depletion is not None and days_until_depletion < 7):
        recommendations.append({
            "title": "Switch to Economy Models",
            "description": "Your budget is nearly depleted. Consider switching to economy models for all non-critical queries.",
            "priority": "high"
        })
    # Medium priority recommendations
    elif budget_percentage > 70:
        recommendations.append({
            "title": "Optimize Premium Model Usage",
            "description": "Restrict premium models to complex queries only.",
            "priority": "medium"
        })
    # Low priority recommendations
    else:
        recommendations.append({
            "title": "Regular Usage Review",
            "description": "Monitor your usage patterns weekly.",
            "priority": "low"
        })
    
    return recommendations
