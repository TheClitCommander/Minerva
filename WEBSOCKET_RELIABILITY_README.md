# WebSocket Reliability Enhancements for Minerva

This package provides comprehensive reliability improvements for Minerva's WebSocket connections, particularly focused on addressing authentication issues, timeout handling, and ensuring responses do not get stuck in Think Tank mode.

## 📋 Overview

The WebSocket reliability enhancements consist of three main components:

1. **Minimal WebSocket Fix (`minimal_websocket_fix.py`)** - Core implementation with:
   - Connection timeout management
   - Request tracking with automatic detection of stalled requests
   - Authentication header support
   - Automatic reconnection handling

2. **Patching Script (`apply_minimal_websocket_fix.py`)** - Applies the fix to the Minerva system:
   - Automatically locates WebSocket handling code in the codebase
   - Updates Flask-SocketIO timeout settings
   - Patches the WebSocket handler with request tracking
   - Provides detailed diagnostics during application

3. **Enhanced Verification (`enhanced_websocket_verification.py`)** - Validates the fixes:
   - Progressive testing - checks server, authentication, and WebSocket
   - Detailed diagnostics - captures and logs all connection issues
   - Authentication support - handles session cookies and tokens
   - Think Tank verification - ensures model routing and quality validation work

## 🛠️ Implementation Details

### 1. Request Tracking

The `RequestTracker` class monitors active WebSocket requests and their timeouts:

- Tracks each request with a unique ID and timestamp
- Periodically checks for stalled requests
- Executes custom timeout handlers when requests exceed their timeout
- Automatically cleans up completed requests to prevent memory leaks

### 2. WebSocket Client Enhancements

The `WebSocketClient` class provides a more robust connection:

- Supports authentication headers and cookies
- Handles socket.io protocol details automatically
- Implements automatic reconnection with exponential backoff
- Manages request callbacks and response routing

### 3. Integration with Minerva

The patching script:

- Updates Flask-SocketIO ping timeouts and intervals
- Patches the WebSocket message handler to track requests
- Adds fallback responses for timed-out requests
- Preserves compatibility with Minerva's existing authentication system

## 🚀 How to Apply the Fix

1. Ensure all three files are in the Minerva directory:
   - `minimal_websocket_fix.py`
   - `apply_minimal_websocket_fix.py`
   - `enhanced_websocket_verification.py`

2. Run the patching script:
   ```bash
   python apply_minimal_websocket_fix.py
   ```

3. Restart the Minerva server to apply the changes.

4. Verify the fix with the verification script:
   ```bash
   python enhanced_websocket_verification.py
   ```

## 🔍 Verification Options

The verification script supports multiple options:

```bash
# Basic verification
python enhanced_websocket_verification.py --test-mode basic

# Test Think Tank mode specifically
python enhanced_websocket_verification.py --test-mode think_tank

# Test timeout handling
python enhanced_websocket_verification.py --test-mode timeout

# Run all tests
python enhanced_websocket_verification.py --test-mode all

# With authentication
python enhanced_websocket_verification.py --auth

# Custom server URL
python enhanced_websocket_verification.py --server http://yourserver:port

# Custom timeout
python enhanced_websocket_verification.py --timeout 60
```

## 🔄 Integration with Existing Features

These WebSocket reliability enhancements have been designed to work seamlessly with Minerva's existing features:

1. **Response Validation System** - Timeout handling works alongside the quality assessment system to ensure valid responses
2. **Enhanced Logging** - The WebSocket client adds detailed transaction tracing that complements Minerva's existing logging
3. **Intelligent Model Selection** - Think Tank mode reliability is improved without modifying the core model selection logic

## 📊 Logging and Diagnostics

All components use consistent logging to the `logs/` directory:

- `logs/minimal_websocket_fix.log` - Core WebSocket operations
- `logs/websocket_fix_application.log` - Patching script diagnostics
- `logs/enhanced_verification.log` - Verification test results

## 🛡️ Security Considerations

- Authentication headers and cookies are securely transmitted
- Session management is preserved during WebSocket operations
- All timeout handlers are executed in a secure context

## ⚠️ Troubleshooting

If you encounter issues:

1. Check the logs in the `logs/` directory for detailed error messages
2. Verify the Minerva server is running and accessible
3. Ensure you have the correct authentication credentials if required
4. Run the verification script with `--test-mode basic` to isolate basic connectivity issues
5. Check the WebSocket URL configuration if connections are failing

## 📝 Future Enhancements

Potential future improvements:

1. Add monitoring dashboard for WebSocket performance metrics
2. Implement more advanced retry strategies for different types of failures
3. Add support for message compression to improve performance
4. Enhance security with additional authentication options
