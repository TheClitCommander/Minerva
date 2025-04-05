#!/usr/bin/env python3
"""
AI Models Usage Dashboard

This module provides Flask routes for visualizing AI model usage statistics
and cost optimization suggestions.
"""

import os
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from flask import Blueprint, render_template, request, jsonify, send_file
from io import BytesIO

from .usage_tracking import get_tracker, get_usage_summary, get_cost_saving_suggestions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for usage dashboard
usage_dashboard = Blueprint('usage_dashboard', __name__, url_prefix='/usage',
                           template_folder='../templates/usage')

@usage_dashboard.route('/')
def dashboard_home():
    """Render the main usage dashboard page"""
    return render_template('usage_dashboard.html')

@usage_dashboard.route('/api/summary')
def api_usage_summary():
    """API endpoint to get usage summary data"""
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    model = request.args.get('model')
    query_type = request.args.get('query_type')
    
    # Get usage summary
    summary = get_usage_summary(
        start_date=start_date,
        end_date=end_date,
        model=model,
        query_type=query_type
    )
    
    return jsonify(summary)

@usage_dashboard.route('/api/suggestions')
def api_optimization_suggestions():
    """API endpoint to get cost optimization suggestions"""
    suggestions = get_cost_saving_suggestions()
    return jsonify({
        'suggestions': suggestions,
        'suggestion_count': len(suggestions)
    })

@usage_dashboard.route('/api/charts/model_distribution')
def api_model_distribution_chart():
    """API endpoint for model distribution pie chart"""
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get usage summary
    summary = get_usage_summary(start_date=start_date, end_date=end_date)
    
    # Create DataFrame for the chart
    if not summary.get('model_breakdown'):
        return jsonify({'error': 'No data available'})
    
    df = pd.DataFrame(summary['model_breakdown'])
    
    # Create pie chart
    fig = px.pie(
        df, 
        values='total_cost', 
        names='model', 
        title='Cost Distribution by Model',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    # Convert to JSON
    chart_json = fig.to_json()
    
    return jsonify({
        'chart': json.loads(chart_json),
        'data': df.to_dict(orient='records')
    })

@usage_dashboard.route('/api/charts/daily_trend')
def api_daily_trend_chart():
    """API endpoint for daily cost trend chart"""
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get usage summary
    summary = get_usage_summary(start_date=start_date, end_date=end_date)
    
    # Create DataFrame for the chart
    if not summary.get('daily_trend'):
        return jsonify({'error': 'No data available'})
    
    df = pd.DataFrame(summary['daily_trend'])
    
    # Create line chart
    fig = px.line(
        df, 
        x='date', 
        y='daily_cost', 
        title='Daily API Cost Trend',
        labels={'daily_cost': 'Cost ($)', 'date': 'Date'},
        markers=True
    )
    
    # Convert to JSON
    chart_json = fig.to_json()
    
    return jsonify({
        'chart': json.loads(chart_json),
        'data': df.to_dict(orient='records')
    })

@usage_dashboard.route('/api/export/csv')
def api_export_csv():
    """API endpoint to export usage data as CSV"""
    # Parse date parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Get tracker instance
    tracker = get_tracker()
    
    try:
        conn = tracker._get_db_connection()
        
        # Build query
        if not start_date:
            # Default to last 30 days
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        start_timestamp = f"{start_date}T00:00:00"
        end_timestamp = f"{end_date}T23:59:59"
        
        query = '''
        SELECT * FROM model_usage
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp DESC
        '''
        
        # Use pandas to create CSV
        df = pd.read_sql_query(query, conn, params=[start_timestamp, end_timestamp])
        
        # Create BytesIO object to store CSV
        csv_data = BytesIO()
        df.to_csv(csv_data, index=False)
        csv_data.seek(0)
        
        # Generate filename with current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"minerva_api_usage_{timestamp}.csv"
        
        return send_file(
            csv_data,
            mimetype='text/csv',
            download_name=filename,
            as_attachment=True
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@usage_dashboard.route('/update_daily_summary', methods=['POST'])
def trigger_daily_summary_update():
    """Manually trigger daily summary update"""
    date = request.form.get('date')
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        # Get tracker and update summary
        tracker = get_tracker()
        tracker.update_daily_summary(date)
        
        return jsonify({
            'status': 'success',
            'message': f'Updated daily summary for {date}'
        })
        
    except Exception as e:
        logger.error(f"Error updating daily summary: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
