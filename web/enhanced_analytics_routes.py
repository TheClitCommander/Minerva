"""
Enhanced Analytics Routes for Minerva
------------------------------------
These routes provide improved analytics capabilities with clear separation 
between real and simulated API calls.
"""

from flask import render_template, jsonify
import json
import time
from enhanced_analytics import process_analytics_data, prepare_chart_data, get_response_quality_metrics

def register_enhanced_analytics_routes(app):
    """Register enhanced analytics routes with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    
    @app.route('/enhanced-analytics')
    def enhanced_analytics():
        """Display the enhanced analytics dashboard page.
        
        This page provides clear separation between real and simulated API calls,
        with improved visualization and filtering options.
        """
        # Process analytics data
        real_models, simulated_models, summary_metrics = process_analytics_data()
        
        # Prepare chart data
        chart_data = prepare_chart_data(real_models, simulated_models)
        
        # Get quality metrics
        quality_metrics = get_response_quality_metrics()
        
        # Update response time in summary metrics
        summary_metrics['avg_response_time'] = quality_metrics.get('avg_response_time', 0)
        
        return render_template(
            'enhanced_analytics.html',
            real_models=real_models,
            simulated_models=simulated_models,
            summary_metrics=summary_metrics,
            quality_metrics=quality_metrics,
            chart_data_json=json.dumps(chart_data)
        )
    
    @app.route('/api/enhanced-analytics')
    def api_enhanced_analytics():
        """API endpoint for enhanced analytics data.
        
        Returns:
            JSON: Structured analytics data with clear separation of real and simulated API calls
        """
        # Process analytics data
        real_models, simulated_models, summary_metrics = process_analytics_data()
        
        # Prepare chart data
        chart_data = prepare_chart_data(real_models, simulated_models)
        
        # Get quality metrics
        quality_metrics = get_response_quality_metrics()
        
        return jsonify({
            'real_models': real_models,
            'simulated_models': simulated_models,
            'summary': summary_metrics,
            'quality': quality_metrics,
            'chart_data': chart_data
        })
