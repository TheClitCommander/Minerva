#!/usr/bin/env python3
"""
AI Usage Alerts System

This module provides functionality to track AI usage costs and send alerts
when predefined thresholds are exceeded.
"""

import logging
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import threading
import time

from .cost_optimizer import get_budget_status, BUDGET_THRESHOLDS
from .usage_tracking import get_usage_stats

# Set up logging
logger = logging.getLogger(__name__)

# Alert configuration path
ALERT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              '..', '..', 'data', 'alert_config.json')

# Default alert configuration
DEFAULT_ALERT_CONFIG = {
    "enabled": True,
    "alert_channels": {
        "email": {
            "enabled": False,
            "recipients": [],
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "from_address": ""
        },
        "slack": {
            "enabled": False,
            "webhook_url": ""
        },
        "webhook": {
            "enabled": False,
            "url": "",
            "method": "POST",
            "headers": {}
        },
        "log": {
            "enabled": True
        }
    },
    "alert_thresholds": {
        "daily_pct": 80,  # Alert at 80% of daily budget
        "weekly_pct": 80,  # Alert at 80% of weekly budget
        "monthly_pct": 80,  # Alert at 80% of monthly budget
        "emergency_alert": True  # Send high-priority alert in emergency mode
    },
    "cooldown_minutes": 60  # Don't send repeat alerts for the same threshold for this many minutes
}

def load_alert_config() -> Dict[str, Any]:
    """Load alert configuration from file or use defaults"""
    if os.path.exists(ALERT_CONFIG_PATH):
        try:
            with open(ALERT_CONFIG_PATH, 'r') as f:
                custom_config = json.load(f)
                return custom_config
        except Exception as e:
            logger.error(f"Error loading alert config: {str(e)}")
    
    return DEFAULT_ALERT_CONFIG

def save_alert_config(config: Dict[str, Any]) -> bool:
    """Save alert configuration to file"""
    try:
        os.makedirs(os.path.dirname(ALERT_CONFIG_PATH), exist_ok=True)
        with open(ALERT_CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving alert config: {str(e)}")
        return False

# Initialize alert configuration
ALERT_CONFIG = load_alert_config()

# Last alert timestamps to implement cooldown
last_alerts = {
    "daily": datetime.min,
    "weekly": datetime.min,
    "monthly": datetime.min,
    "emergency": datetime.min
}

def update_alert_config(new_config: Dict[str, Any]) -> bool:
    """
    Update alert configuration with new values.
    
    Args:
        new_config: Dict containing new configuration values
        
    Returns:
        True if update was successful, False otherwise
    """
    global ALERT_CONFIG
    
    # Merge the new config with the existing one
    for key, value in new_config.items():
        if key in ALERT_CONFIG:
            if isinstance(value, dict) and isinstance(ALERT_CONFIG[key], dict):
                # Recursively merge nested dictionaries
                for sub_key, sub_value in value.items():
                    if sub_key in ALERT_CONFIG[key]:
                        ALERT_CONFIG[key][sub_key] = sub_value
            else:
                ALERT_CONFIG[key] = value
    
    # Save the updated configuration
    return save_alert_config(ALERT_CONFIG)

def format_alert_message(
    alert_type: str,
    budget_status: Dict[str, Any],
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a consistent alert message for all notification channels.
    
    Args:
        alert_type: Type of alert ('daily', 'weekly', 'monthly', 'emergency')
        budget_status: Current budget status
        additional_info: Additional information to include
        
    Returns:
        Dict containing formatted alert message
    """
    period_status = budget_status.get(alert_type, {})
    cost = period_status.get('cost', 0.0)
    budget = period_status.get('budget', 0.0)
    percentage = period_status.get('percentage', 0.0)
    
    # Convert alert type to readable period
    period_name = alert_type.capitalize()
    
    # Build title
    if alert_type == 'emergency':
        title = "🚨 CRITICAL - AI API Emergency Cost Threshold Exceeded!"
    else:
        title = f"⚠️ {period_name} AI API Budget Alert - {percentage:.1f}% Used"
    
    # Build message body
    message = f"""
{title}

Minerva AI Usage Alert for {period_name} Budget
----------------------------------------------
• Current {period_name} Cost: ${cost:.2f}
• {period_name} Budget: ${budget:.2f}
• Percentage Used: {percentage:.1f}%
• Status: {period_status.get('status', 'unknown').upper()}
"""

    # Add additional info if provided
    if additional_info:
        message += "\nAdditional Information:\n"
        for key, value in additional_info.items():
            message += f"• {key}: {value}\n"
    
    # Add timestamp
    message += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Add cost-saving recommendation if we're over threshold
    if percentage >= 80:
        message += """

Recommended Actions:
1. Review the AI Usage Dashboard for optimization opportunities
2. Consider switching to more cost-efficient models for non-critical tasks
3. Implement stricter cost limits for high-volume projects
"""
    
    # Add link to dashboard
    message += "\nView detailed usage statistics: http://localhost:5000/usage"
    
    return {
        "title": title,
        "message": message,
        "alert_type": alert_type,
        "severity": "critical" if percentage >= 100 else "warning" if percentage >= 80 else "info",
        "timestamp": datetime.now().isoformat(),
        "cost": cost,
        "budget": budget,
        "percentage": percentage
    }

def send_email_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Send an alert via email.
    
    Args:
        alert_data: Formatted alert data
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    email_config = ALERT_CONFIG['alert_channels']['email']
    
    if not email_config['enabled'] or not email_config['recipients']:
        logger.warning("Email alerts are disabled or no recipients configured")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_config['from_address']
        msg['To'] = ', '.join(email_config['recipients'])
        msg['Subject'] = alert_data['title']
        
        # Attach message body
        msg.attach(MIMEText(alert_data['message'], 'plain'))
        
        # Connect to server and send
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()
        server.login(email_config['smtp_username'], email_config['smtp_password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Sent email alert to {len(email_config['recipients'])} recipients")
        return True
    
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
        return False

def send_slack_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Send an alert to Slack.
    
    Args:
        alert_data: Formatted alert data
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    slack_config = ALERT_CONFIG['alert_channels']['slack']
    
    if not slack_config['enabled'] or not slack_config['webhook_url']:
        logger.warning("Slack alerts are disabled or webhook URL not configured")
        return False
    
    try:
        # Format message for Slack
        color = "#FF0000" if alert_data['severity'] == "critical" else "#FFA500" if alert_data['severity'] == "warning" else "#36A64F"
        
        payload = {
            "attachments": [
                {
                    "title": alert_data['title'],
                    "text": alert_data['message'],
                    "color": color,
                    "fields": [
                        {
                            "title": "Cost",
                            "value": f"${alert_data['cost']:.2f}",
                            "short": True
                        },
                        {
                            "title": "Budget",
                            "value": f"${alert_data['budget']:.2f}",
                            "short": True
                        },
                        {
                            "title": "Percentage Used",
                            "value": f"{alert_data['percentage']:.1f}%",
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": alert_data['severity'].upper(),
                            "short": True
                        }
                    ],
                    "footer": f"Minerva AI • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        }
        
        # Send to Slack
        response = requests.post(
            slack_config['webhook_url'],
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info("Sent alert to Slack successfully")
            return True
        else:
            logger.error(f"Error sending Slack alert: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending Slack alert: {str(e)}")
        return False

def send_webhook_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Send an alert to a custom webhook.
    
    Args:
        alert_data: Formatted alert data
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    webhook_config = ALERT_CONFIG['alert_channels']['webhook']
    
    if not webhook_config['enabled'] or not webhook_config['url']:
        logger.warning("Webhook alerts are disabled or URL not configured")
        return False
    
    try:
        # Set method (default to POST)
        method = webhook_config.get('method', 'POST').upper()
        
        # Prepare headers
        headers = webhook_config.get('headers', {})
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        
        # Send request
        if method == 'GET':
            response = requests.get(
                webhook_config['url'],
                params=alert_data,
                headers=headers
            )
        else:  # POST, PUT, etc.
            response = requests.request(
                method,
                webhook_config['url'],
                json=alert_data,
                headers=headers
            )
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Sent alert to webhook successfully: {response.status_code}")
            return True
        else:
            logger.error(f"Error sending webhook alert: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending webhook alert: {str(e)}")
        return False

def log_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Log an alert message.
    
    Args:
        alert_data: Formatted alert data
        
    Returns:
        True always (logging doesn't fail)
    """
    log_config = ALERT_CONFIG['alert_channels']['log']
    
    if not log_config['enabled']:
        return False
    
    if alert_data['severity'] == 'critical':
        logger.critical(f"AI COST ALERT: {alert_data['title']}\n{alert_data['message']}")
    elif alert_data['severity'] == 'warning':
        logger.warning(f"AI COST ALERT: {alert_data['title']}\n{alert_data['message']}")
    else:
        logger.info(f"AI COST ALERT: {alert_data['title']}\n{alert_data['message']}")
    
    return True

def send_alert(
    alert_type: str,
    budget_status: Dict[str, Any],
    additional_info: Optional[Dict[str, Any]] = None,
    force: bool = False
) -> bool:
    """
    Send an alert through all enabled channels.
    
    Args:
        alert_type: Type of alert ('daily', 'weekly', 'monthly', 'emergency')
        budget_status: Current budget status
        additional_info: Additional information to include
        force: If True, bypass cooldown check
        
    Returns:
        True if at least one alert was sent successfully, False otherwise
    """
    global last_alerts
    
    # Skip if alerts are disabled
    if not ALERT_CONFIG['enabled']:
        logger.debug("Alerts are disabled, skipping")
        return False
    
    # Check cooldown unless forcing
    if not force:
        cooldown_minutes = ALERT_CONFIG.get('cooldown_minutes', 60)
        cooldown_delta = timedelta(minutes=cooldown_minutes)
        
        if alert_type in last_alerts:
            time_since_last = datetime.now() - last_alerts[alert_type]
            if time_since_last < cooldown_delta:
                logger.debug(f"Skipping {alert_type} alert due to cooldown ({time_since_last.total_seconds() / 60:.1f} minutes since last)")
                return False
    
    # Format alert message
    alert_data = format_alert_message(alert_type, budget_status, additional_info)
    
    # Send through each enabled channel
    success = False
    
    # Email
    if ALERT_CONFIG['alert_channels']['email']['enabled']:
        if send_email_alert(alert_data):
            success = True
    
    # Slack
    if ALERT_CONFIG['alert_channels']['slack']['enabled']:
        if send_slack_alert(alert_data):
            success = True
    
    # Webhook
    if ALERT_CONFIG['alert_channels']['webhook']['enabled']:
        if send_webhook_alert(alert_data):
            success = True
    
    # Logging (always enabled)
    if ALERT_CONFIG['alert_channels']['log']['enabled']:
        if log_alert(alert_data):
            success = True
    
    # Update last alert timestamp if any alert was sent
    if success:
        last_alerts[alert_type] = datetime.now()
    
    return success

def check_budget_and_alert() -> Dict[str, bool]:
    """
    Check all budget thresholds and send alerts if any are exceeded.
    
    Returns:
        Dict of alert types and whether an alert was sent
    """
    # Get current budget status
    budget_status = get_budget_status()
    
    # Get alert thresholds
    alert_thresholds = ALERT_CONFIG.get('alert_thresholds', {
        'daily_pct': 80,
        'weekly_pct': 80,
        'monthly_pct': 80,
        'emergency_alert': True
    })
    
    # Track which alerts were sent
    alerts_sent = {}
    
    # Check daily threshold
    daily_pct = budget_status['daily']['percentage']
    if daily_pct >= alert_thresholds.get('daily_pct', 80):
        alerts_sent['daily'] = send_alert('daily', budget_status)
    
    # Check weekly threshold
    weekly_pct = budget_status['weekly']['percentage']
    if weekly_pct >= alert_thresholds.get('weekly_pct', 80):
        alerts_sent['weekly'] = send_alert('weekly', budget_status)
    
    # Check monthly threshold
    monthly_pct = budget_status['monthly']['percentage']
    if monthly_pct >= alert_thresholds.get('monthly_pct', 80):
        alerts_sent['monthly'] = send_alert('monthly', budget_status)
    
    # Check emergency mode
    if budget_status['emergency_mode'] and alert_thresholds.get('emergency_alert', True):
        alerts_sent['emergency'] = send_alert('emergency', budget_status)
    
    return alerts_sent

# Monitoring thread
monitor_thread = None
should_monitor = False

def monitor_budget_loop():
    """Background thread for monitoring budget and sending alerts"""
    global should_monitor
    
    logger.info("Budget monitoring thread started")
    
    while should_monitor:
        try:
            check_budget_and_alert()
        except Exception as e:
            logger.error(f"Error in budget monitoring thread: {str(e)}")
        
        # Sleep for a while before checking again
        time.sleep(60 * 15)  # Check every 15 minutes
    
    logger.info("Budget monitoring thread stopped")

def start_budget_monitoring():
    """Start the background budget monitoring thread"""
    global monitor_thread, should_monitor
    
    if monitor_thread is not None and monitor_thread.is_alive():
        logger.warning("Budget monitoring thread is already running")
        return False
    
    should_monitor = True
    monitor_thread = threading.Thread(target=monitor_budget_loop, daemon=True)
    monitor_thread.start()
    
    logger.info("Budget monitoring started")
    return True

def stop_budget_monitoring():
    """Stop the background budget monitoring thread"""
    global should_monitor
    
    should_monitor = False
    logger.info("Budget monitoring stopping (may take up to 15 minutes to fully stop)")
    return True
