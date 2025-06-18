#!/usr/bin/env python3
"""
Minimal API Server for Minerva UI
Provides just the essential API endpoints to fix the UI's "Initializing..." issue
"""

from flask import Flask, jsonify, request
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', template_folder='.')
app.config['JSON_SORT_KEYS'] = False

@app.route("/")
def index():
    return "Minerva Minimal API Server is running. Access the UI at /web/minerva_central.html"

@app.route("/web/<path:path>")
def serve_web(path):
    return app.send_static_file(f"../web/{path}")

@app.route("/api/status", methods=["GET"])
def api_status():
    """Status endpoint to check if API is available"""
    return jsonify({
        "status": "success",
        "message": "Minerva API is online",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chat endpoint to handle user messages"""
    try:
        data = request.json
        user_message = data.get("message", "")
        
        # Log the incoming message
        print(f"Received chat message: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        
        # Return a simple response to confirm connectivity
        return jsonify({
            "status": "success",
            "response": f"Hello from the Minerva API! I received your message: '{user_message[:30]}...'" if len(user_message) > 30 else f"Hello from the Minerva API! I received your message: '{user_message}'",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error processing chat request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error processing your request: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5505))
    print(f"Starting Minerva Minimal API Server on port {port}")
    print(f"Access the UI at: http://localhost:{port}/web/minerva_central.html")
    app.run(host="0.0.0.0", port=port, debug=True)
