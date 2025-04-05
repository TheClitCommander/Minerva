#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Admin Routes for Minerva Dashboard

This module contains admin-only routes for the Minerva dashboard, including
feedback statistics and management features.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user

# Set up logger
logger = logging.getLogger(__name__)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard view."""
    if not current_user.is_admin:
        return render_template('error.html', error="Unauthorized", 
                              message="You don't have permission to access this resource"), 403
    
    return render_template('admin/dashboard.html')

@admin_bp.route('/feedback')
@login_required
def admin_feedback():
    """Admin feedback view."""
    if not current_user.is_admin:
        return render_template('error.html', error="Unauthorized", 
                              message="You don't have permission to access this resource"), 403
    
    return render_template('admin/feedback.html')

@admin_bp.route('/api/feedback_stats', methods=["GET"])
@login_required
def get_admin_feedback_stats():
    """API endpoint for admin dashboard to get feedback statistics.
    
    Returns aggregated statistics about user feedback including:
    - Overall feedback (helpful vs not helpful)
    - Feedback by model
    - Feedback over time
    - Feedback by query type
    - Common feedback reasons
    
    Returns:
        JSON: Feedback statistics
    """
    try:
        # Check if user has admin permissions
        if not current_user.is_admin:
            return jsonify({
                "error": "Unauthorized",
                "message": "You don't have permission to access this resource"
            }), 403
        
        # Get time range from query parameter (default to last 30 days)
        time_range = request.args.get('timeRange', 'last30days')
        
        # Import feedback handler
        try:
            from web.feedback_handler import FeedbackHandler
            feedback_handler = FeedbackHandler()
        except ImportError:
            logger.error("Failed to import FeedbackHandler")
            return jsonify({
                "error": "Feedback system is not available"
            }), 500
        
        # Set the date range based on the requested time period
        end_date = datetime.now()
        
        if time_range == 'last7days':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'last30days':
            start_date = end_date - timedelta(days=30)
        elif time_range == 'last90days':
            start_date = end_date - timedelta(days=90)
        else:  # all time
            start_date = None
        
        # Get feedback statistics
        stats = feedback_handler.get_admin_stats(start_date=start_date, end_date=end_date)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting admin feedback stats: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@admin_bp.route('/api/recent_feedback', methods=["GET"])
@login_required
def get_recent_feedback():
    """API endpoint to retrieve recent feedback entries.
    
    Returns the most recent feedback entries for review in admin dashboard.
    
    Returns:
        JSON: List of recent feedback entries
    """
    try:
        # Check if user has admin permissions
        if not current_user.is_admin:
            return jsonify({
                "error": "Unauthorized",
                "message": "You don't have permission to access this resource"
            }), 403
        
        # Get limit parameter (default to 50 entries)
        limit = request.args.get('limit', 50, type=int)
        if limit > 100:  # Cap at 100 for performance
            limit = 100
            
        # Get time range from query parameter (default to last 30 days)
        time_range = request.args.get('timeRange', 'last30days')
        
        # Import feedback handler
        try:
            from web.feedback_handler import FeedbackHandler
            feedback_handler = FeedbackHandler()
        except ImportError:
            logger.error("Failed to import FeedbackHandler")
            return jsonify({
                "error": "Feedback system is not available"
            }), 500
        
        # Set the date range based on the requested time period
        end_date = datetime.now()
        
        if time_range == 'last7days':
            start_date = end_date - timedelta(days=7)
        elif time_range == 'last30days':
            start_date = end_date - timedelta(days=30)
        elif time_range == 'last90days':
            start_date = end_date - timedelta(days=90)
        else:  # all time
            start_date = None
            
        # Get feedback entries
        feedback_entries = feedback_handler.get_feedback_by_date_range(
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )
        
        # Sort by timestamp (newest first) and limit
        feedback_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        limited_entries = feedback_entries[:limit]
        
        # Prepare response
        response = {
            "total": len(feedback_entries),
            "count": len(limited_entries),
            "items": limited_entries
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting recent feedback: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@admin_bp.route('/api/feedback_report', methods=["GET"])
@login_required
def generate_feedback_report():
    """Generate and return a comprehensive feedback analysis report.
    
    This endpoint generates an analysis report based on feedback data,
    including model performance insights and recommendations.
    
    Returns:
        JSON: Feedback analysis report
    """
    try:
        # Check if user has admin permissions
        if not current_user.is_admin:
            return jsonify({
                "error": "Unauthorized",
                "message": "You don't have permission to access this resource"
            }), 403
            
        # Import feedback analyzer
        try:
            from web.feedback_analyzer import FeedbackAnalyzer
            analyzer = FeedbackAnalyzer()
        except ImportError:
            logger.error("Failed to import FeedbackAnalyzer")
            return jsonify({
                "error": "Feedback analysis system is not available"
            }), 500
            
        # Generate in-memory report without writing to file
        # We'll extract the report data directly instead of using export_report_to_json
        # This requires implementing a method in FeedbackAnalyzer to generate the report data
        # without writing to a file
        try:
            # Try to get report from newer method first
            report_data = analyzer.generate_report_data()
        except AttributeError:
            # Fall back to exporting to temp file
            import tempfile
            import os
            import json
            
            # Create temp file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"feedback_report_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            # Generate report
            report_path = analyzer.export_report_to_json(temp_file)
            
            if not report_path or not os.path.exists(report_path):
                return jsonify({
                    "error": "Failed to generate report"
                }), 500
                
            # Read report from file
            with open(report_path, 'r') as f:
                report_data = json.load(f)
                
            # Clean up temp file
            try:
                os.remove(report_path)
            except:
                pass
        
        return jsonify(report_data)
        
    except Exception as e:
        logger.error(f"Error generating feedback report: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

# Register the blueprint in app.py using:
# from web.routes.admin_routes import admin_bp
# app.register_blueprint(admin_bp)
