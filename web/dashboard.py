"""
Minerva Analytics Dashboard

This module provides a real-time analytics dashboard for monitoring API stability:
- Model request/response metrics
- Rate limiting status
- Circuit breaker status
- Error tracking
- Response time analytics
"""

import os
import json
import time
import datetime
import logging
import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

import httpx
from flask import Flask, render_template, jsonify, request, Response
from flask_cors import CORS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("minerva_dashboard")

# Import API request handler data structures
from web.api_request_handler import (
    RATE_LIMITS,
    CIRCUIT_BREAKERS,
    CIRCUIT_BREAKER_CONFIG,
    ERROR_TRACKING
)

# For storing metrics
model_request_counts = {}
model_failure_counts = {}
model_cooldowns = {}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure static files path
static_folder = os.path.join(os.path.dirname(__file__), 'static')
if not os.path.exists(static_folder):
    os.makedirs(static_folder)

# In-memory metrics storage (will be backed up periodically)
metrics_history = {
    "requests": defaultdict(lambda: deque(maxlen=1000)),  # Request counts by model
    "errors": defaultdict(lambda: deque(maxlen=1000)),    # Error counts by model
    "response_times": defaultdict(lambda: deque(maxlen=1000)),  # Response times by model
    "rate_limits": defaultdict(lambda: deque(maxlen=100)),  # Rate limit events
    "circuit_breaks": defaultdict(lambda: deque(maxlen=100)),  # Circuit breaker events
}

# Time series data is stored as (timestamp, value) tuples
performance_metrics = {
    "total_requests": deque(maxlen=1000),  # Total requests across all models
    "success_rate": deque(maxlen=1000),    # Success rate percentage
    "avg_response_time": deque(maxlen=1000),  # Average response time in ms
}

# Dashboard configuration
dashboard_config = {
    "refresh_interval": 5,  # Dashboard refresh interval in seconds
    "metrics_retention": 24,  # Hours to keep metrics data
    "alert_threshold_errors": 5,  # Number of errors to trigger alert
    "alert_threshold_response_time": 5000,  # Response time in ms to trigger alert
}

# Helper functions for data formatting
def get_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.datetime.now().isoformat()

def get_readable_timestamp():
    """Get human-readable timestamp"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def format_model_status():
    """Format model status data for the dashboard"""
    models_data = []
    
    # Combine all models that have appeared in our tracking
    all_model_names = set()
    all_model_names.update([k for k in RATE_LIMITS.keys() if k != 'default'])
    all_model_names.update(model_request_counts.keys())
    all_model_names.update(CIRCUIT_BREAKERS.keys())
    all_model_names.update(model_failure_counts.keys())
    
    for model in all_model_names:
        # Get rate limit info
        rate_limit_info = RATE_LIMITS.get(model, RATE_LIMITS.get('default', {}))
        max_requests = rate_limit_info.get('max_requests', 0) if rate_limit_info else 0
        count = rate_limit_info.get('count', 0) if rate_limit_info else 0
        
        # Get circuit breaker info
        breaker_info = CIRCUIT_BREAKERS.get(model, {})
        is_disabled = time.time() < breaker_info.get('disabled_until', 0) if breaker_info else False
        failures = breaker_info.get('failures', 0) if breaker_info else 0
        
        # Determine status
        status = "ONLINE"
        if is_disabled:
            status = "OFFLINE"
        elif count >= max_requests:
            status = "RATE_LIMITED"
        
        model_data = {
            "name": model,
            "request_count": model_request_counts.get(model, 0),
            "rate_limit": max_requests,
            "current_usage": count,
            "circuit_status": "OPEN" if is_disabled else "CLOSED",
            "failure_count": failures,
            "failure_threshold": CIRCUIT_BREAKER_CONFIG['failure_threshold'],
            "status": status
        }
        models_data.append(model_data)
        
    return models_data

def format_error_tracking():
    """Format error tracking data for the dashboard"""
    error_data = []
    
    for model, error_types in ERROR_TRACKING.items():
        for error_type, count in error_types.items():
            error_data.append({
                "model": model,
                "error_type": error_type,
                "count": count,
                "last_seen": get_readable_timestamp()  # This would ideally come from error tracking
            })
            
    return error_data

# Dashboard routes
@app.route('/')
def dashboard_home():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics():
    """API endpoint for analytics data expected by dashboard.html"""
    # Calculate average latency (simulated for now)
    avg_latency = 0
    response_count = 0
    
    # Get active models
    active_models = []
    for model, breaker_data in CIRCUIT_BREAKERS.items():
        # Model is active if it's not disabled or cooldown period has expired
        if time.time() >= breaker_data.get('disabled_until', 0):
            active_models.append(model)
    
    # Add all models from RATE_LIMITS that aren't in circuit breakers
    for model in RATE_LIMITS.keys():
        if model != 'default' and model not in CIRCUIT_BREAKERS:
            active_models.append(model)
    
    # Get rate limited models
    rate_limited_models = []
    for model, limit_data in RATE_LIMITS.items():
        if model != 'default' and limit_data['count'] >= limit_data['max_requests']:
            rate_limited_models.append(model)
    
    stats = {
        "timestamp": get_timestamp(),
        "requests": sum(model_request_counts.values()),
        "failures": sum(model_failure_counts.values()),
        "average_latency": avg_latency,
        "active_models": active_models,
        "rate_limited_models": rate_limited_models
    }
    return jsonify(stats)

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        "timestamp": get_timestamp(),
        "models": format_model_status(),
        "errors": format_error_tracking(),
        "performance": {
            "total_requests": sum(model_request_counts.values()),
            "total_failures": sum(model_failure_counts.values()),
            "circuit_breaks": sum(1 for status in circuit_breaker_status.values() if status),
            "rate_limited_models": sum(1 for model, cooldown in model_cooldowns.items() 
                                      if time.time() < cooldown)
        }
    }
    return jsonify(stats)

@app.route('/api/model/<model_name>')
def model_details(model_name):
    """API endpoint for detailed model statistics"""
    if model_name not in model_request_counts:
        return jsonify({"error": "Model not found"}), 404
        
    # Get historical metrics for this model
    requests_history = list(metrics_history["requests"].get(model_name, []))
    errors_history = list(metrics_history["errors"].get(model_name, []))
    response_times = list(metrics_history["response_times"].get(model_name, []))
    
    details = {
        "model": model_name,
        "status": "OFFLINE" if circuit_breaker_status.get(model_name, False) else 
                 "RATE_LIMITED" if time.time() < model_cooldowns.get(model_name, 0) else 
                 "ONLINE",
        "metrics": {
            "request_count": model_request_counts.get(model_name, 0),
            "failure_count": model_failure_counts.get(model_name, 0),
            "success_rate": (1 - (model_failure_counts.get(model_name, 0) / 
                               max(model_request_counts.get(model_name, 1), 1))) * 100,
            "circuit_breaker_status": "OPEN" if circuit_breaker_status.get(model_name, False) else "CLOSED",
            "cooldown_remaining": max(0, model_cooldowns.get(model_name, 0) - time.time()),
        },
        "history": {
            "requests": requests_history,
            "errors": errors_history,
            "response_times": response_times
        }
    }
    return jsonify(details)

@app.route('/api/recent-activity')
def recent_activity():
    """API endpoint for recent activity stream"""
    # We would ideally have an activity log, but for now we'll generate it from current state
    activities = []
    
    # Check for currently rate-limited models
    for model, cooldown in model_cooldowns.items():
        if time.time() < cooldown:
            activities.append({
                "timestamp": get_readable_timestamp(),
                "model": model,
                "action": "RATE_LIMITED",
                "message": f"Model {model} rate limited, cooling down for {int(cooldown - time.time())} more seconds"
            })
    
    # Check for circuit breaker status
    for model, status in circuit_breaker_status.items():
        if status:
            activities.append({
                "timestamp": get_readable_timestamp(),
                "model": model,
                "action": "CIRCUIT_OPENED",
                "message": f"Circuit breaker opened for model {model} due to excessive failures"
            })
    
    # Check for high failure counts
    for model, failures in model_failure_counts.items():
        if failures > 0:
            activities.append({
                "timestamp": get_readable_timestamp(),
                "model": model,
                "action": "FAILURES",
                "message": f"Model {model} has encountered {failures} failures"
            })
            
    return jsonify(activities)

# Add a simple health check endpoint
@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok", 
        "timestamp": get_timestamp(),
        "version": "1.0.0"
    })

# Admin control endpoints - these would need authentication in production
@app.route('/api/admin/reset-circuit/<model_name>', methods=['POST'])
def reset_circuit(model_name):
    """Manually reset circuit breaker for a model"""
    if model_name in circuit_breaker_status:
        circuit_breaker_status[model_name] = False
        model_failure_counts[model_name] = 0
        return jsonify({"success": True, "message": f"Circuit breaker reset for {model_name}"})
    return jsonify({"success": False, "message": "Model not found"}), 404

@app.route('/api/admin/reset-rate-limit/<model_name>', methods=['POST'])
def reset_rate_limit(model_name):
    """Manually reset rate limit cooldown for a model"""
    if model_name in model_cooldowns:
        model_cooldowns[model_name] = 0
        model_request_counts[model_name] = 0
        return jsonify({"success": True, "message": f"Rate limit reset for {model_name}"})
    return jsonify({"success": False, "message": "Model not found"}), 404

# Background task to update metrics
async def update_metrics():
    """Background task to update metrics periodically"""
    while True:
        try:
            # Record current timestamp for all metrics
            timestamp = get_timestamp()
            
            # Update total requests metric
            total_requests = sum(model_request_counts.values())
            performance_metrics["total_requests"].append((timestamp, total_requests))
            
            # Calculate success rate
            total_failures = sum(model_failure_counts.values())
            success_rate = (1 - (total_failures / max(total_requests, 1))) * 100
            performance_metrics["success_rate"].append((timestamp, success_rate))
            
            # Update metrics for each model
            for model in model_request_counts.keys():
                # Record request count
                metrics_history["requests"][model].append(
                    (timestamp, model_request_counts.get(model, 0))
                )
                
                # Record error count
                metrics_history["errors"][model].append(
                    (timestamp, model_failure_counts.get(model, 0))
                )
                
                # Record rate limit events if currently rate limited
                if time.time() < model_cooldowns.get(model, 0):
                    metrics_history["rate_limits"][model].append(
                        (timestamp, model_cooldowns.get(model, 0) - time.time())
                    )
                
                # Record circuit breaker events
                if circuit_breaker_status.get(model, False):
                    metrics_history["circuit_breaks"][model].append(
                        (timestamp, 1)  # 1 indicates circuit is open
                    )
            
            logger.debug(f"Updated metrics at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
            
        # Wait for next update interval
        await asyncio.sleep(dashboard_config["refresh_interval"])

# Background task runner
def start_background_tasks():
    """Start background tasks for dashboard"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.create_task(update_metrics())
        loop.run_forever()
    finally:
        loop.close()

# Start the dashboard
def start_dashboard(host="0.0.0.0", port=5005, debug=False):
    """Start the dashboard server"""
    # Start background metrics update in a separate thread
    import threading
    background_thread = threading.Thread(target=start_background_tasks)
    background_thread.daemon = True
    background_thread.start()
    
    # Start Flask app
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    start_dashboard(debug=True)
