# Minerva Chat Implementation Guide

This document explains the hybrid chat implementation that provides both WebSocket and REST API chat functionality.

## Overview

Minerva's chat system now employs a hybrid approach:

1. **WebSocket-based Chat (Primary)**: Real-time communication using Flask-SocketIO with eventlet
2. **REST API-based Chat (Fallback)**: Standard HTTP API for environments where WebSockets might not work

## Starting the Server

Use the provided script to start the server:

```bash
./start_minerva.sh
```

Options:
- `-p, --port PORT`: Specify port (default: 9876)
- `-d, --debug`: Enable debug mode
- `-v, --venv PATH`: Virtual environment path (default: fresh_venv)
- `-h, --help`: Show help message

## WebSocket Chat API

The WebSocket chat API is implemented using Flask-SocketIO and provides real-time communication.

### Client-side Implementation

```javascript
// Connect to the WebSocket server
const socket = io();

// Listen for connection events
socket.on('connect', () => {
    console.log('Connected to Minerva chat server');
});

// Listen for incoming messages
socket.on('message_received', (data) => {
    console.log('Received message:', data);
    // Display message in UI
});

// Send a message
socket.emit('chat_message', {
    message: 'Hello, Minerva!',
    conversation_id: 'your_conversation_id'
});
```

### Server-side Implementation

The server handles WebSocket connections through event handlers:

- `@socketio.on('connect')`: Handles new connections
- `@socketio.on('disconnect')`: Handles client disconnections
- `@socketio.on('chat_message')`: Processes incoming chat messages
- `emit('message_received')`: Sends responses back to clients

## REST API Chat Endpoints

For environments where WebSockets are not available, a RESTful API provides chat functionality.

### POST /api/chat/message

Send a message to Minerva and get a response.

**Request:**
```json
{
    "message": "Hello, Minerva!",
    "conversation_id": "optional_conversation_id"
}
```

**Response:**
```json
{
    "status": "success",
    "conversation_id": "conversation_id",
    "user_message": "Hello, Minerva!",
    "response": "Hello! How can I help you today?",
    "timestamp": "2025-02-27T19:45:00.000Z"
}
```

## Troubleshooting

### WebSocket Connection Issues

If WebSocket connections fail:
1. Check if eventlet is properly installed: `pip install eventlet`
2. Ensure the server is running with the eventlet worker
3. Verify there are no port conflicts
4. Try the REST API fallback

### Port Conflicts

If you encounter "Address already in use" errors:
1. Find processes using the port: `lsof -i -P | grep LISTEN | grep 9876`
2. Terminate those processes: `kill -9 PID`
3. Alternatively, use a different port: `./start_minerva.sh -p 8765`

## Technical Implementation Details

The hybrid approach ensures reliability through:

1. **WebSocket Context Preservation**: Request SID is stored and passed explicitly to threads
2. **Eventlet Monkey Patching**: Applied before imports to ensure compatibility
3. **SocketIO Configuration**: Using `async_mode='eventlet'` and `cors_allowed_origins="*"`
4. **REST API Fallback**: Standard HTTP endpoints that don't rely on WebSocket functionality
