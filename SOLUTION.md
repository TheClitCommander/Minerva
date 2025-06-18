# Minerva Chat Connection Issues: Solution Guide

## Problem Overview

The Minerva system was experiencing an issue where the chat interface could connect to the server via Socket.IO, but users were receiving simulated AI responses instead of real responses from the AI models. The system was showing these key symptoms:

1. Chat UI would connect successfully to the server
2. Users could send messages successfully 
3. The server would log receiving the messages
4. Instead of real AI responses, users received "simulated" fallback responses
5. Server logs showed warnings like "MultiAICoordinator not available, using simulated responses"

## Root Causes

After investigation, we identified three interconnected issues:

### 1. Coordinator Naming and Export Issues
- The `server.py` was trying to import `Coordinator` (with capital C) from `web.multi_ai_coordinator` 
- However, the module only exported a lowercase `coordinator` variable
- This naming mismatch broke the import chain, causing fallback to simulated responses

### 2. Socket.IO Version Mismatch
- The client was using a version of Socket.IO that was incompatible with the server's python-socketio
- This caused protocol errors: "Client is using an unsupported version of the Socket.IO or Engine.IO protocols"
- While messages could be sent, response handling was affected

### 3. Broken Integration Chain
- No proper connection between ThinkTank ➝ Coordinator ➝ MinervaExtensions
- The server could not find the coordinator instance due to import errors
- MinervaExtensions couldn't access the AI models to generate real responses

## Solutions Applied

### 1. Fixing Coordinator Naming and Exports

**File: `web/multi_ai_coordinator.py`**

We corrected the export issue by:
- Adding explicit exports for all naming variations (`coordinator`, `Coordinator`, `COORDINATOR`)
- Setting the singleton instance pattern via `MultiAICoordinator._instance`
- Making all exports point to the same instance to ensure consistency

```python
# Create a guaranteed global coordinator instance
print("Initializing MultiAICoordinator as module-level global variable...")
coordinator = MultiAICoordinator()

# Make the coordinator available through multiple mechanisms to ensure it can be imported
globals()['coordinator'] = coordinator  # Directly add to globals
Coordinator = coordinator  # Capital C version (crucial for imports)
COORDINATOR = coordinator  # Alternative capitals format

# Set as singleton instance
MultiAICoordinator._instance = coordinator

# Control what's exported with import *
__all__ = ['MultiAICoordinator', 'coordinator', 'COORDINATOR', 'Coordinator']

# Log success with details to debug
print(f"✅ Coordinator successfully created and exported:")
print(f"  - coordinator: {coordinator.__class__.__name__} at id={id(coordinator)}")
print(f"  - Coordinator: {Coordinator.__class__.__name__} at id={id(Coordinator)}")
print(f"  - COORDINATOR: {COORDINATOR.__class__.__name__} at id={id(COORDINATOR)}")
```

### 2. Fixing Socket.IO Version Compatibility

**File: `server.py`**

We updated the Socket.IO server configuration:
- Explicitly enabled compatibility with client protocols (both EIO3 and EIO4)
- Added better ping/timeout handling for more reliable connections
- Set explicit protocol options for compatibility

```python
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,  # Increase buffer size for larger payloads
    # Set explicit compatibility options
    **{
        'always_connect': True,
        'serve_client': False,  # Don't serve client to avoid version conflicts
        'handle_sigint': True,
        'json': None,  # Use default JSON handler
        'websocket_ping_interval': 25,  # Keep connection alive
        'websocket_ping_timeout': 60,
        'allowEIO3': True,  # Allow Engine.IO v3 clients to connect (better compatibility)
        'allowEIO4': True,  # Allow Engine.IO v4 clients to connect (newer clients)
    }
)
```

**File: `templates/portal.html`**

We updated the client Socket.IO library:
- Use an exact version that's compatible with the server
- Added integrity hash to ensure correct version
- Fixed CDN URL pattern for version 5.x

```html
<!-- Replace the existing Socket.IO script import with this version-locked CDN import -->
<!-- Use Socket.IO v5.3.6 to exactly match server python-socketio -->
<script src="https://cdn.socket.io/socket.io-5.3.6.min.js" integrity="sha384-mzXcQnH9FCNS8t8mPZGLN/uLZ/PYRTBbCOeWGrXUYEO1eEYVxzxUePD66Y1caQZL" crossorigin="anonymous"></script>
```

### 3. Fixing the Integration Chain

**File: `web/minerva_extensions.py`**

We made the MinervaExtensions class more robust:
- Added multi-strategy coordinator imports with fallbacks
- Better error handling and diagnostics
- Verification of coordinator capabilities before use

```python
def __init__(self, coordinator=None):
    # Set up the coordinator
    self.coordinator = coordinator
    
    # If no coordinator provided, try multiple import patterns
    if self.coordinator is None:
        try:
            # Try direct import with capital C first
            from web.multi_ai_coordinator import Coordinator
            self.coordinator = Coordinator
            
            # If not available, try lowercase coordinator
            # [additional fallback strategies...]
            
            # Check if it has the methods we need
            if hasattr(self.coordinator, 'generate_response'):
                logger.info("✅ Successfully loaded AI coordinator")
            else:
                logger.warning("Coordinator found but missing required methods")
        except Exception as e:
            logger.error(f"Error importing coordinator: {str(e)}")
```

**File: `server.py`**

We updated the server initialization:
- More robust coordinator import with multiple strategies
- Explicit coordinator passing to MinervaExtensions
- Added debugging and verification of the coordinator

```python
try:
    # Strategy 1: Direct import with capital C (preferred)
    from web.multi_ai_coordinator import Coordinator
    coordinator = Coordinator
    ai_coordinator = coordinator
    has_coordinator = True
    
    # Additional import strategies and fallbacks...
    
    # Pass the coordinator explicitly to MinervaExtensions
    minerva_extensions = MinervaExtensions(coordinator)
except Exception as e:
    logger.error(f"Error initializing coordinator: {str(e)}")
```

## Files Changed

The following files were modified to fix the issues:

1. `web/multi_ai_coordinator.py` - Fixed export naming and singleton pattern
2. `web/minerva_extensions.py` - Improved coordinator import and fallback handling
3. `server.py` - Enhanced coordinator initialization and Socket.IO configuration
4. `templates/portal.html` - Updated Socket.IO client library version
5. `verify_coordinator.py` (new file) - Added diagnostic tool to verify coordinator setup
6. `fixed_run_server.sh` (new file) - Added robust start script with verification

## Verification Steps

To verify the fix is working correctly:

### 1. Run the Verification Tool

```bash
chmod +x verify_coordinator.py
./verify_coordinator.py
```

This will test all coordinator import patterns and verify that MinervaExtensions can find and use the coordinator.

Expected output will show:
- At least one successful import pattern
- MinervaExtensions able to find the coordinator
- Test message generating a real response, not a simulated one

### 2. Start the Server with the Fixed Script

```bash
chmod +x fixed_run_server.sh
./fixed_run_server.sh
```

Watch the server logs for these positive signs:
- "✅ Successfully imported Coordinator directly"
- "Available models: [list of models]"
- "✅ Successfully loaded AI models for real responses"
- No "using simulated responses" warnings

### 3. Test the Chat Interface

1. Open http://localhost:5505/portal in your browser
2. Send a test message like "Hello, are you using real AI or simulation?"
3. Examine the response - it should be a real AI response, not a simulated one
4. Check the server logs - they should show successful message processing without warnings

### 4. Verify Socket.IO Connection

Check browser console for:
- No Socket.IO protocol errors
- Successful connection events
- No reconnection attempts

## Conclusion

The fix addressed all three core issues:
1. ✅ Coordinator naming and export is now consistent and robust
2. ✅ Socket.IO version compatibility is ensured on both client and server
3. ✅ The integration chain between components is properly connected

By ensuring proper naming and exports, fixing the Socket.IO version compatibility, and improving the integration between components, the Minerva chat system now correctly uses real AI models instead of falling back to simulated responses.

If problems return in the future, the `verify_coordinator.py` tool can be used to diagnose import issues, and the `fixed_run_server.sh` script provides a reliable way to start the server with proper initialization. 