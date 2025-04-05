#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scheduled Feedback Processor

This script is designed to be run periodically (e.g., daily via cron) to:
1. Analyze collected user feedback
2. Update model weights based on performance
3. Generate feedback reports for administrators
"""

import os
import sys
import argparse
import logging
import json
import datetime
from pathlib import Path

# Add parent directory to path so we can import our modules
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(parent_dir, 'logs', 'feedback_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feedback_processor')

def process_feedback(args):
    """Process feedback data and update model weights.
    
    Args:
        args: Command-line arguments
    """
    try:
        # Import our feedback modules
        from web.feedback_handler import FeedbackHandler
        from web.feedback_analyzer import FeedbackAnalyzer
        
        logger.info("Starting feedback processing job")
        
        # Initialize the feedback handler
        feedback_handler = FeedbackHandler()
        
        # Initialize the analyzer with our feedback handler
        analyzer = FeedbackAnalyzer(feedback_handler=feedback_handler)
        
        # Get current feedback stats
        stats = feedback_handler.get_feedback_stats()
        logger.info(f"Processing {stats['total_feedback']} feedback items")
        
        # If we don't have enough feedback, we might want to skip processing
        if stats['total_feedback'] < args.min_feedback_count:
            logger.info(f"Not enough feedback to process (minimum: {args.min_feedback_count})")
            return
        
        # Update model weights based on feedback with query-type specialization
        update_result = analyzer.analyze_and_update_models(query_type_boost=True)
        
        if update_result['success']:
            logger.info(f"Successfully updated model weights: {update_result['updated_weights']}")
            
            # Log adjustments by query type if available
            if 'query_type_adjustments' in update_result:
                for query_type, model in update_result['query_type_adjustments'].items():
                    logger.info(f"Specialized {model} for {query_type} queries based on feedback")
        else:
            logger.error("Failed to update model weights: " + update_result.get('error', 'Unknown error'))
        
        # Generate and save a feedback report if requested
        if args.generate_report:
            # Try to get admin stats with new method if available
            try:
                admin_stats = feedback_handler.get_admin_stats()
                logger.info(f"Using enhanced statistics for report generation")
                # Log some key insights from the admin stats
                if admin_stats and 'by_query_type' in admin_stats:
                    query_types = admin_stats['by_query_type']
                    for query_type, data in query_types.items():
                        total = data.get('helpful', 0) + data.get('not_helpful', 0)
                        if total >= 10:  # Only log if we have enough data
                            helpful_pct = (data.get('helpful', 0) / total * 100) if total > 0 else 0
                            logger.info(f"Query type '{query_type}': {helpful_pct:.1f}% helpful ({total} samples)")
            except (AttributeError, TypeError) as e:
                logger.warning(f"Using basic statistics for report generation: {e}")
            
            report_path = analyzer.export_report_to_json()
            logger.info(f"Generated feedback report at: {report_path}")
            
            # If email notification is enabled, send report
            if args.email_report and args.email_recipient:
                send_email_report(args.email_recipient, report_path)
                
            # Archive old reports if we're keeping too many
            if args.max_reports > 0:
                try:
                    cleanup_old_reports(args.max_reports)
                except Exception as e:
                    logger.warning(f"Error cleaning up old reports: {e}")
        
        logger.info("Feedback processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)

def cleanup_old_reports(max_reports=10):
    """Clean up old feedback reports, keeping only the most recent ones.
    
    Args:
        max_reports: Number of most recent reports to keep
    """
    try:
        # Find the reports directory
        base_dir = Path(__file__).resolve().parent.parent
        reports_dir = os.path.join(base_dir, "data", "reports")
        
        if not os.path.exists(reports_dir):
            logger.warning(f"Reports directory does not exist: {reports_dir}")
            return
        
        # Get all JSON report files
        report_files = [f for f in os.listdir(reports_dir) if f.startswith('feedback_report_') and f.endswith('.json')]
        
        # If we have more than max_reports, delete the oldest ones
        if len(report_files) > max_reports:
            # Sort by filename (which includes timestamp) - oldest first
            report_files.sort()
            
            # Calculate how many to delete
            to_delete = len(report_files) - max_reports
            
            # Delete oldest reports
            for i in range(to_delete):
                file_path = os.path.join(reports_dir, report_files[i])
                os.remove(file_path)
                logger.info(f"Archived old report: {report_files[i]}")
    
    except Exception as e:
        logger.error(f"Error cleaning up old reports: {e}")
        raise

def send_email_report(recipient, report_path):
    """Send email with feedback report.
    
    Args:
        recipient: Email address to send the report to
        report_path: Path to the feedback report file
    """
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        
        # Load report data
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        
        # Create a summary of the report
        helpful_pct = report_data['overall_statistics']['helpful_percentage']
        recent_pct = report_data['overall_statistics'].get('recent_helpful_percentage', helpful_pct)
        total_feedback = report_data['overall_statistics']['total_feedback']
        
        # Create the email
        msg = MIMEMultipart()
        msg['Subject'] = f'Minerva Feedback Report - {datetime.datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = 'minerva-noreply@example.com'
        msg['To'] = recipient
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>Minerva AI Feedback Report</h2>
            <p>This is an automated report from the Minerva feedback system.</p>
            
            <h3>Summary</h3>
            <ul>
                <li>Total Feedback: {total_feedback}</li>
                <li>Overall Helpful Rating: {helpful_pct:.1f}%</li>
                <li>Recent Helpful Rating: {recent_pct:.1f}%</li>
            </ul>
            
            <h3>Model Performance</h3>
            <table border="1" cellpadding="5">
                <tr>
                    <th>Model</th>
                    <th>Helpful %</th>
                    <th>Total Feedback</th>
                </tr>
        """
        
        # Add model performance data
        for model, stats in report_data['model_performance'].items():
            body += f"""
                <tr>
                    <td>{model}</td>
                    <td>{stats['helpful_percentage']:.1f}%</td>
                    <td>{stats['total_feedback']}</td>
                </tr>
            """
        
        body += """
            </table>
            
            <p>The full report is attached to this email.</p>
            
            <p>Regards,<br>
            Minerva AI Team</p>
        </body>
        </html>
        """
        
        # Attach the HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach the report file
        with open(report_path, 'rb') as f:
            attachment = MIMEApplication(f.read(), _subtype='json')
            attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(report_path))
            msg.attach(attachment)
        
        # Send the email using local SMTP server
        # Note: In a production environment, you would use your actual SMTP configuration
        logger.info(f"Would send email report to {recipient}")
        # Uncomment the following code when ready to send actual emails
        '''
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()
        '''
        
    except Exception as e:
        logger.error(f"Error sending email report: {str(e)}", exc_info=True)

if __name__ == '__main__':
    # Create the logs directory if it doesn't exist
    log_dir = os.path.join(parent_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create data and reports directories if they don't exist
    data_dir = os.path.join(parent_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    reports_dir = os.path.join(data_dir, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process feedback and update model weights')
    parser.add_argument('--min-feedback-count', type=int, default=10, 
                        help='Minimum number of feedback items required to process')
    parser.add_argument('--generate-report', action='store_true', 
                        help='Generate a feedback analysis report')
    parser.add_argument('--email-report', action='store_true',
                        help='Send the report via email')
    parser.add_argument('--email-recipient', type=str,
                        help='Email address to send the report to')
    parser.add_argument('--max-reports', type=int, default=10,
                       help='Maximum number of historical reports to keep')
    parser.add_argument('--query-type-analysis', action='store_true', default=True,
                       help='Include query type analysis when adjusting model weights')
    
    args = parser.parse_args()
    
    # Process feedback
    process_feedback(args)
