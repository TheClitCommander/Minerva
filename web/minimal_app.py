#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Minimal Flask application for testing API endpoints
This is a standalone app that doesn't rely on the complex setup in app.py
"""

from flask import Flask, jsonify, request
import json
import uuid
from datetime import datetime

# Create a minimal Flask app
app = Flask(__name__)

@app.route('/')
def index():
    """Home page"""
    return jsonify({
        'status': 'OK',
        'message': 'Minerva minimal test server is running',
        'timestamp': str(datetime.now())
    })

@app.route('/api/simple_test', methods=['GET', 'POST'])
def simple_test():
    """A very simple test endpoint that provides template responses"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            message = data.get('message', 'No message in POST')
        except Exception as e:
            message = f"Error parsing JSON: {str(e)}"
    else:  # GET
        message = request.args.get('message', 'No message in GET')
        
    # Generate a more substantive response based on the input
    if "machine learning" in message.lower():
        response = "Machine learning is a subset of artificial intelligence that focuses on developing systems that learn from data without being explicitly programmed. Common applications include recommendation systems, image recognition, and natural language processing."
    elif "python" in message.lower():
        response = "Python is a high-level, interpreted programming language known for its readability and versatility. It's widely used in data science, web development, artificial intelligence, and automation."
    elif "minerva" in message.lower():
        response = "Minerva is an AI assistant system designed to provide helpful responses to a wide range of queries. It can use multiple AI models and advanced routing to provide the most appropriate answers."
    else:
        response = f"This is a template response to your query: '{message}'. This minimal server is for testing API connectivity only."
    
    return jsonify({
        'success': True,
        'message_id': str(uuid.uuid4()),
        'message': message,
        'response': response,
        'processing_method': 'minimal_template',
        'timestamp': str(datetime.now())
    })

@app.route('/api/direct', methods=['GET', 'POST'])
def direct_api():
    """Minimal direct API endpoint for testing"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            message = data.get('message', 'No message in POST')
            max_tokens = data.get('max_tokens', 500)
            temperature = data.get('temperature', 0.7)
        except Exception as e:
            message = f"Error parsing JSON: {str(e)}"
            max_tokens = 500
            temperature = 0.7
    else:  # GET
        message = request.args.get('message', 'No message in GET')
        max_tokens = int(request.args.get('max_tokens', 500))
        temperature = float(request.args.get('temperature', 0.7))
    
    # For testing, generate a response based on the message and parameters
    response = f"[TEST MODE] Response to: '{message}'\n\n"
    
    if "machine learning" in message.lower():
        response += "Machine learning is a field of artificial intelligence that uses statistical techniques to give computer systems the ability to 'learn' from data, without being explicitly programmed."
        response += "\n\nKey machine learning paradigms include:\n1. Supervised learning\n2. Unsupervised learning\n3. Reinforcement learning"
    elif "python" in message.lower():
        response += "Python is a high-level, interpreted programming language known for its readability and versatility."
        response += "\n\nPython features:\n- Easy to learn syntax\n- Dynamic typing\n- Memory management\n- Extensive standard library\n- Large ecosystem of third-party packages"
    else:
        response += "This is a simulated response from the direct API endpoint. In a real implementation, this would come from an AI model."
        response += f"\n\nParameters used:\n- max_tokens: {max_tokens}\n- temperature: {temperature}"
    
    return jsonify({
        'success': True,
        'message_id': str(uuid.uuid4()),
        'message': message,
        'response': response,
        'processing_time': 0.05,  # Simulated processing time
        'timestamp': str(datetime.now())
    })

if __name__ == '__main__':
    # Run the minimal app on port 9877 to avoid conflicts with the main app
    print("Starting minimal Flask app for API testing...")
    print("Access the API at: http://localhost:9877/api/simple_test")
    app.run(debug=True, host='0.0.0.0', port=9877)
