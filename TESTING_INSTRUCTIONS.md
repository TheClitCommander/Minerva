# Minerva Testing Instructions

This document provides detailed instructions for testing Minerva's WebSocket connectivity and REST API fallback functionality.

## Prerequisites

- Minerva server running on port 5001
- Web browser with developer console (Chrome recommended)
- `curl` for REST API testing (optional)
- Python 3.6+ for running the test scripts

## Starting Minerva Server

First, ensure the Minerva server is running:

```bash
cd ~/Desktop/Minerva
source fresh_venv/bin/activate
python run_minerva.py --port 5001
```

Verify that the server starts without errors. Look for these log messages:

```
[STARTUP] SocketIO async_mode: eventlet
[STARTUP] Starting SocketIO server...
```

## Testing WebSocket Connectivity

### Method 1: Using the JavaScript Test UI

1. Navigate to any web page in Chrome
2. Open Chrome DevTools (F12 or Right-click > Inspect)
3. Go to the Console tab
4. Paste the entire contents of `manual_websocket_test.js` into the console and press Enter
5. A test UI should appear in the top-right corner of the web page
6. Click "Connect" and observe the connection status
7. Type a message and click "Send Message"
8. Check the console for response messages

Expected result: You should see "CONNECTED" status and receive responses to your messages.

### Method 2: Using Raw JavaScript in Console

If the test UI doesn't work, you can try direct JavaScript commands:

```javascript
// Connect to server
var socket = io("http://localhost:5001");

// Log connection
socket.on("connect", function() {
  console.log("Connected to Minerva WebSocket!");
});

// Listen for responses
socket.on("response", function(data) {
  console.log("Response received:", data);
});

// Send a test message
socket.emit("message", "Hello Minerva");

// Send a structured message
socket.emit("chat_message", {
  message: "Testing chat message",
  conversation_id: "test-" + Date.now()
});
```

### Troubleshooting WebSocket Issues

If WebSocket connections fail:

1. Check the browser console for error messages
2. Verify that the server is running and accessible
3. Check for CORS issues in the browser console
4. Ensure that port 5001 is not blocked by firewall
5. Kill any existing processes using port 5001:
   ```bash
   # Mac/Linux
   lsof -i :5001
   kill -9 <PID>
   
   # Windows
   netstat -ano | findstr :5001
   taskkill /PID <PID> /F
   ```

## Testing REST API Fallback

### Method 1: Using the Python Test Script

Run the Python test script with various options:

```bash
# Basic test
python test_rest_api.py

# Test with custom message
python test_rest_api.py --message "Custom test message"

# Test basic endpoints
python test_rest_api.py --test-basic

# Full test with options
python test_rest_api.py --host localhost --port 5001 --message "Test with options" --test-basic
```

Expected result: The script should show successful responses from the server.

### Method 2: Using curl

Test the REST API directly with curl:

```bash
# Basic message test
curl -X POST http://localhost:5001/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from curl"}'

# Test with conversation ID
curl -X POST http://localhost:5001/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello with conversation", "conversation_id": "curl-test-1"}'

# Test other endpoints
curl http://localhost:5001/api/test
```

## Verifying GPT Model Integration

After confirming basic connectivity, test GPT model integration:

1. Try sending a complex question that would require AI processing
2. Check the server logs for lines like `[GPT] Sending request to ...`
3. Verify that responses contain AI-generated content
4. If multiple models are available, check that responses include output from each model

## Monitoring Logs

Monitor both client-side and server-side logs:

1. Client-side: Browser console messages from Socket.IO
2. Server-side: Terminal output from Minerva process
3. Look for error messages, warnings, or unexpected behavior

## Additional Notes

- WebSocket connections may take a moment to establish
- AI model responses may take several seconds to generate
- REST API is generally more reliable for testing as it doesn't require persistent connections
- If one method fails, try the other to isolate the issue

## Common Issues and Solutions

| Issue | Possible Solution |
|-------|------------------|
| Connection refused | Ensure server is running and port is accessible |
| CORS errors | Check SocketIO cors_allowed_origins parameter |
| No response from AI | Verify AI models are properly loaded |
| Timeout errors | Increase timeouts for AI processing |
| "Working outside of request context" | Ensure request.sid is captured before threading |
