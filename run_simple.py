#!/usr/bin/env python3
"""
Simplified run script for Minerva that doesn't rely on WebSockets.
"""
import os
import eventlet
# Monkey patch before importing Flask
eventlet.monkey_patch()

from web.app import app

if __name__ == '__main__':
    # Set Flask environment
    os.environ['FLASK_ENV'] = 'development'
    
    # Run the app
    print("Starting Minerva on http://localhost:8765")
    app.run(host='0.0.0.0', port=8765, debug=True)
