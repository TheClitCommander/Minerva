#!/usr/bin/env python3
"""
Usage Tracking System for AI Model APIs

This module provides tools to track usage of various AI model APIs, 
including token counts, estimated costs, and analytics for optimization.
"""

import os
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any, Tuple
import sqlite3
from pathlib import Path
import threading

# Try to import pandas, but continue if it's not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("pandas not installed, advanced analytics features will be disabled")
    PANDAS_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for database and storage
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             '..', '..', 'data', 'usage_tracking.db')

# Model pricing information as of March 2025
# Format: (input_price_per_million_tokens, output_price_per_million_tokens)
MODEL_PRICING = {
    # OpenAI models
    'gpt-4': (10.0, 30.0),
    'gpt-4-turbo': (10.0, 30.0),
    'gpt-4o': (10.0, 30.0),
    'gpt-3.5-turbo': (0.5, 1.5),
    
    # Anthropic models
    'claude-3-opus': (15.0, 75.0),
    'claude-3-sonnet': (3.0, 15.0),
    'claude-3.5-sonnet': (3.0, 15.0),
    'claude-3.5-haiku': (0.8, 3.5),
    
    # Google models
    'gemini-pro': (1.25, 5.0),
    'gemini-flash': (0.1, 2.0),
    'gemini-1.5-pro': (2.5, 8.0),
    
    # Mistral models
    'mistral-small': (2.0, 6.0),
    'mistral-medium': (4.0, 12.0),
    'mistral-large': (8.0, 24.0),
    
    # Cohere models
    'cohere-command': (1.5, 7.0),
    'cohere-command-light': (0.6, 2.5),
    'cohere-command-r': (2.5, 10.0),
    
    # Default fallback pricing if model not found
    'default': (5.0, 15.0)
}

class UsageTracker:
    """Class for tracking API usage and costs for AI models"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """Initialize the usage tracker with database connection"""
        self.db_path = db_path
        self._init_database()
        self._lock = threading.Lock()
        
    def _init_database(self):
        """Initialize the SQLite database if it doesn't exist"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            model TEXT,
            request_id TEXT,
            query_type TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            latency_ms INTEGER,
            estimated_cost REAL,
            success INTEGER,
            error_message TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            model TEXT,
            total_requests INTEGER,
            total_input_tokens INTEGER,
            total_output_tokens INTEGER,
            total_cost REAL,
            avg_latency_ms INTEGER
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def track_usage(self, 
                   model: str,
                   input_tokens: int,
                   output_tokens: int,
                   query_type: str = 'general',
                   request_id: Optional[str] = None,
                   latency_ms: Optional[int] = None,
                   success: bool = True,
                   error_message: str = '') -> float:
        """
        Track usage of a model API call
        
        Args:
            model: Name of the model used
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            query_type: Type of query (code, general, etc.)
            request_id: Unique ID for the request
            latency_ms: Latency in milliseconds
            success: Whether the request was successful
            error_message: Error message if request failed
            
        Returns:
            Estimated cost of the API call
        """
        timestamp = datetime.now().isoformat()
        
        # Calculate cost based on token usage
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Generate a request ID if not provided
        if not request_id:
            request_id = f"req_{int(time.time())}_{hash(timestamp) % 10000}"
        
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO model_usage (
                    timestamp, model, request_id, query_type,
                    input_tokens, output_tokens, latency_ms,
                    estimated_cost, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp, model, request_id, query_type,
                    input_tokens, output_tokens, latency_ms,
                    cost, int(success), error_message
                ))
                
                conn.commit()
                conn.close()
                
                # Log the usage
                status = "successful" if success else "failed"
                logger.debug(f"Tracked {status} API call: {model}, {input_tokens}in/{output_tokens}out tokens, ${cost:.6f}")
                
                return cost
                
            except Exception as e:
                logger.error(f"Error tracking usage: {str(e)}")
                return cost
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the estimated cost based on token usage"""
        # Get pricing for the model, or use default if not found
        input_price, output_price = MODEL_PRICING.get(model.lower(), MODEL_PRICING['default'])
        
        # Calculate cost (convert from per million to per token)
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price
        
        return input_cost + output_cost
    
    def update_daily_summary(self, date: Optional[str] = None):
        """Update the daily usage summary for the given date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        start_timestamp = f"{date}T00:00:00"
        end_timestamp = f"{date}T23:59:59"
        
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Delete existing summary for this date to avoid duplicates
                cursor.execute("DELETE FROM daily_summary WHERE date = ?", (date,))
                
                # Get summarized data grouped by model
                cursor.execute('''
                SELECT 
                    model,
                    COUNT(*) as total_requests,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(estimated_cost) as total_cost,
                    AVG(latency_ms) as avg_latency_ms
                FROM model_usage
                WHERE timestamp >= ? AND timestamp <= ? AND success = 1
                GROUP BY model
                ''', (start_timestamp, end_timestamp))
                
                summaries = cursor.fetchall()
                
                # Insert new summaries
                for summary in summaries:
                    model, total_requests, total_input, total_output, total_cost, avg_latency = summary
                    
                    cursor.execute('''
                    INSERT INTO daily_summary (
                        date, model, total_requests, total_input_tokens,
                        total_output_tokens, total_cost, avg_latency_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date, model, total_requests, total_input,
                        total_output, total_cost, avg_latency
                    ))
                
                conn.commit()
                conn.close()
                logger.info(f"Updated daily summary for {date}")
                
            except Exception as e:
                logger.error(f"Error updating daily summary: {str(e)}")
    
    def get_usage_report(self, 
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        model: Optional[str] = None,
                        query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a usage report for the specified time period
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            model: Filter by specific model
            query_type: Filter by query type
            
        Returns:
            Dictionary with usage statistics
        """
        if not start_date:
            # Default to last 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        start_timestamp = f"{start_date}T00:00:00"
        end_timestamp = f"{end_date}T23:59:59"
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query with optional filters
            query = '''
            SELECT 
                model,
                COUNT(*) as total_requests,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(latency_ms) as avg_latency_ms
            FROM model_usage
            WHERE timestamp >= ? AND timestamp <= ? AND success = 1
            '''
            
            params = [start_timestamp, end_timestamp]
            
            if model:
                query += " AND model = ?"
                params.append(model)
                
            if query_type:
                query += " AND query_type = ?"
                params.append(query_type)
                
            query += " GROUP BY model"
            
            # Use pandas for easier data manipulation
            df = pd.read_sql_query(query, conn, params=params)
            
            # Total across all models
            total_cost = df['total_cost'].sum()
            total_requests = df['total_requests'].sum()
            total_input_tokens = df['total_input_tokens'].sum()
            total_output_tokens = df['total_output_tokens'].sum()
            
            # Convert DataFrame to records for JSON serialization
            model_breakdown = df.to_dict(orient='records')
            
            # Get daily trend
            daily_query = '''
            SELECT date, SUM(total_cost) as daily_cost
            FROM daily_summary
            WHERE date >= ? AND date <= ?
            '''
            
            daily_params = [start_date, end_date]
            
            if model:
                daily_query += " AND model = ?"
                daily_params.append(model)
                
            daily_query += " GROUP BY date ORDER BY date"
            
            daily_df = pd.read_sql_query(daily_query, conn, params=daily_params)
            daily_trend = daily_df.to_dict(orient='records')
            
            conn.close()
            
            return {
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_statistics': {
                    'total_cost': float(total_cost),
                    'total_requests': int(total_requests),
                    'total_input_tokens': int(total_input_tokens),
                    'total_output_tokens': int(total_output_tokens),
                    'cost_per_request': float(total_cost / total_requests) if total_requests > 0 else 0
                },
                'model_breakdown': model_breakdown,
                'daily_trend': daily_trend
            }
            
        except Exception as e:
            logger.error(f"Error generating usage report: {str(e)}")
            return {
                'error': str(e),
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_statistics': {
                    'total_cost': 0,
                    'total_requests': 0,
                    'total_input_tokens': 0,
                    'total_output_tokens': 0,
                    'cost_per_request': 0
                },
                'model_breakdown': [],
                'daily_trend': []
            }
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """
        Analyze usage data and provide optimization suggestions
        
        Returns:
            List of suggestions for optimizing API usage costs
        """
        suggestions = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Identify expensive models that could be replaced
            model_costs = pd.read_sql_query('''
                SELECT 
                    model,
                    COUNT(*) as request_count,
                    SUM(estimated_cost) as total_cost,
                    AVG(input_tokens) as avg_input_tokens,
                    AVG(output_tokens) as avg_output_tokens,
                    AVG(estimated_cost) as avg_cost_per_request
                FROM model_usage
                WHERE success = 1
                GROUP BY model
                ORDER BY avg_cost_per_request DESC
            ''', conn)
            
            # Get query types that might be optimizable
            query_type_costs = pd.read_sql_query('''
                SELECT 
                    query_type,
                    COUNT(*) as request_count,
                    SUM(estimated_cost) as total_cost,
                    AVG(input_tokens) as avg_input_tokens,
                    AVG(output_tokens) as avg_output_tokens
                FROM model_usage
                WHERE success = 1
                GROUP BY query_type
                ORDER BY total_cost DESC
            ''', conn)
            
            conn.close()
            
            # Find expensive models that could be optimized
            for _, row in model_costs.iterrows():
                model = row['model']
                avg_cost = row['avg_cost_per_request']
                request_count = row['request_count']
                total_cost = row['total_cost']
                
                # Suggest cheaper alternatives for expensive models
                if 'gpt-4' in model and avg_cost > 0.05:
                    suggestions.append({
                        'type': 'model_substitution',
                        'model': model,
                        'impact': f"${total_cost:.2f} from {request_count} requests",
                        'suggestion': "Consider using GPT-3.5 Turbo for simpler queries to reduce costs.",
                        'estimated_savings': f"${total_cost * 0.7:.2f} (70% reduction)",
                        'priority': 'high' if total_cost > 10 else 'medium'
                    })
                
                elif 'claude-3-opus' in model and avg_cost > 0.1:
                    suggestions.append({
                        'type': 'model_substitution',
                        'model': model,
                        'impact': f"${total_cost:.2f} from {request_count} requests",
                        'suggestion': "Consider using Claude-3 Sonnet for most queries, reserving Opus for complex tasks.",
                        'estimated_savings': f"${total_cost * 0.6:.2f} (60% reduction)",
                        'priority': 'high' if total_cost > 15 else 'medium'
                    })
            
            # Analyze query types
            for _, row in query_type_costs.iterrows():
                query_type = row['query_type']
                total_cost = row['total_cost']
                avg_input = row['avg_input_tokens']
                avg_output = row['avg_output_tokens']
                
                # Identify query types with large outputs
                if avg_output > 2000 and total_cost > 5:
                    suggestions.append({
                        'type': 'token_optimization',
                        'query_type': query_type,
                        'impact': f"${total_cost:.2f} with avg {avg_output:.0f} output tokens",
                        'suggestion': "Consider limiting output tokens or breaking into smaller requests.",
                        'estimated_savings': f"${total_cost * 0.4:.2f} (40% reduction)",
                        'priority': 'medium'
                    })
                
                # Identify query types with large inputs
                if avg_input > 4000 and total_cost > 5:
                    suggestions.append({
                        'type': 'token_optimization',
                        'query_type': query_type,
                        'impact': f"${total_cost:.2f} with avg {avg_input:.0f} input tokens",
                        'suggestion': "Consider trimming input context or using embedding search to reduce tokens.",
                        'estimated_savings': f"${total_cost * 0.3:.2f} (30% reduction)",
                        'priority': 'medium'
                    })
            
            # Add general suggestions if we don't have enough specific ones
            if len(suggestions) < 2:
                suggestions.append({
                    'type': 'general',
                    'suggestion': "Implement model fallback strategy: start with cheaper models and only escalate to expensive ones when necessary.",
                    'priority': 'medium'
                })
                
                suggestions.append({
                    'type': 'general',
                    'suggestion': "Use caching for common queries to reduce duplicate API calls.",
                    'priority': 'medium'
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return [
                {
                    'type': 'error',
                    'suggestion': f"Error analyzing usage data: {str(e)}",
                    'priority': 'high'
                }
            ]


# Singleton instance
_tracker_instance = None

def get_tracker(db_path: str = DEFAULT_DB_PATH) -> UsageTracker:
    """Get the singleton tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = UsageTracker(db_path)
    return _tracker_instance


# Convenience functions for tracking usage
def track_model_usage(model: str, 
                     input_tokens: int, 
                     output_tokens: int,
                     **kwargs) -> float:
    """Track usage of a model API call"""
    return get_tracker().track_usage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        **kwargs
    )


def get_usage_summary(start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     **kwargs) -> Dict[str, Any]:
    """Get a summary of API usage"""
    return get_tracker().get_usage_report(
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )


def get_cost_saving_suggestions() -> List[Dict[str, Any]]:
    """Get suggestions for optimizing API costs"""
    return get_tracker().get_optimization_suggestions()


def get_usage_stats(period: str = 'week', model: Optional[str] = None, query_type: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive usage statistics for the dashboard
    
    Args:
        period: Time period to filter by ('today', 'week', 'month', 'all')
        model: Filter by specific model name (optional)
        query_type: Filter by specific query type (optional)
        
    Returns:
        Dict containing usage statistics including:
        - summary: Overall usage summary
        - models: Per-model statistics
        - daily_usage: Usage broken down by day
        - query_types: Usage broken down by query type
        - cost_trends: Cost trends over time
        - optimization_suggestions: Cost saving suggestions
    """
    tracker = get_tracker()
    
    # Calculate date range based on period
    today = datetime.now().date()
    if period == 'today':
        start_date = str(today)
        end_date = str(today)
    elif period == 'week':
        start_date = str(today - timedelta(days=7))
        end_date = str(today)
    elif period == 'month':
        start_date = str(today - timedelta(days=30))
        end_date = str(today)
    else:  # 'all'
        start_date = None
        end_date = None
        
    # Get basic usage summary
    summary = tracker.get_usage_report(start_date=start_date, end_date=end_date, model=model, query_type=query_type)
    
    # Add per-model statistics - use the get_model_breakdown method if available, or create a simple version
    try:
        models_data = tracker.get_model_breakdown(start_date=start_date, end_date=end_date, query_type=query_type)
    except AttributeError:
        # Simple fallback implementation if method doesn't exist
        conn = sqlite3.connect(tracker.db_path)
        query = "SELECT model, COUNT(*) as count, SUM(input_tokens) as input_tokens, "
        query += "SUM(output_tokens) as output_tokens, SUM(estimated_cost) as cost "
        query += "FROM model_usage WHERE 1=1 "
        
        params = []
        if start_date:
            query += "AND date(timestamp) >= date(?) "
            params.append(start_date)
        if end_date:
            query += "AND date(timestamp) <= date(?) "
            params.append(end_date)
        if query_type:
            query += "AND query_type = ? "
            params.append(query_type)
            
        query += "GROUP BY model"
        
        df = pd.read_sql_query(query, conn, params=params)
        models_data = df.set_index('model').to_dict(orient='index')
        conn.close()
    
    # Get daily usage data for charts
    try:
        daily_usage = tracker.get_daily_usage(start_date=start_date, end_date=end_date, model=model, query_type=query_type)
    except AttributeError:
        # Simple fallback implementation
        conn = sqlite3.connect(tracker.db_path)
        query = "SELECT date(timestamp) as date, COUNT(*) as count, "
        query += "SUM(input_tokens) as input_tokens, SUM(output_tokens) as output_tokens, "
        query += "SUM(estimated_cost) as cost FROM model_usage WHERE 1=1 "
        
        params = []
        if start_date:
            query += "AND date(timestamp) >= date(?) "
            params.append(start_date)
        if end_date:
            query += "AND date(timestamp) <= date(?) "
            params.append(end_date)
        if model:
            query += "AND model = ? "
            params.append(model)
        if query_type:
            query += "AND query_type = ? "
            params.append(query_type)
            
        query += "GROUP BY date(timestamp) ORDER BY date(timestamp)"
        
        df = pd.read_sql_query(query, conn, params=params)
        daily_usage = df.set_index('date').to_dict(orient='index')
        conn.close()
    
    # Get query type distribution
    try:
        query_types = tracker.get_query_type_distribution(start_date=start_date, end_date=end_date, model=model)
    except AttributeError:
        # Simple fallback implementation
        conn = sqlite3.connect(tracker.db_path)
        query = "SELECT query_type, COUNT(*) as count, SUM(input_tokens) as input_tokens, "
        query += "SUM(output_tokens) as output_tokens, SUM(estimated_cost) as cost "
        query += "FROM model_usage WHERE query_type IS NOT NULL AND query_type != '' "
        
        params = []
        if start_date:
            query += "AND date(timestamp) >= date(?) "
            params.append(start_date)
        if end_date:
            query += "AND date(timestamp) <= date(?) "
            params.append(end_date)
        if model:
            query += "AND model = ? "
            params.append(model)
            
        query += "GROUP BY query_type"
        
        df = pd.read_sql_query(query, conn, params=params)
        query_types = df.set_index('query_type').to_dict(orient='index')
        conn.close()
    
    # Get optimization suggestions
    try:
        optimization = tracker.get_optimization_suggestions()
    except AttributeError:
        optimization = [
            {
                'suggestion': 'Consider using lower-cost models for simple queries',
                'impact': 'medium',
                'estimated_savings': 'Up to 40% reduction in costs',
                'details': 'For general queries, models like GPT-3.5 Turbo often provide sufficient quality at a fraction of the cost.'
            }
        ]
    
    # Format available models
    available_models = list(models_data.keys()) if models_data else []
    
    # Format available query types
    query_types_list = list(query_types.keys()) if query_types else []
    
    return {
        'summary': summary,
        'models': models_data,
        'daily_usage': daily_usage,
        'query_types': query_types,
        'optimization_suggestions': optimization,
        'available_models': available_models,
        'available_query_types': query_types_list,
        'period': period
    }
