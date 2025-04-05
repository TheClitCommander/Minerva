#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ultra simple test server for Minerva chat
"""

import sys
import os
import time
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-test-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('chat_test_simple.html')

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'message': 'API working!',
        'time': time.time()
    })

@socketio.on('connect')
def connect_handler():
    print(f"[SOCKET] Client connected: {request.sid}")
    emit('message', 'You are now connected to the server')

@socketio.on('disconnect')
def disconnect_handler():
    print(f"[SOCKET] Client disconnected: {request.sid}")

@socketio.on('message')
def message_handler(message):
    print(f"[SOCKET] Received basic message: {message}")
    emit('message', f"Echo: {message}")

@socketio.on('chat_message')
def chat_message_handler(data):
    print(f"[SOCKET] Received chat message: {data}")
    
    if isinstance(data, dict):
        message = data.get('message', '')
    else:
        message = str(data)
        
    # Send back an immediate response
    response = {
        'response': f"This is a simple response to: {message}",
        'message_id': '12345',
        'timestamp': time.time()
    }
    
    emit('response', response)

if __name__ == '__main__':
    port = 5555  # Different port than the main server
    print(f"[INFO] Starting simple test server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
