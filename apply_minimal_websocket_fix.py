#!/usr/bin/env python3
"""
Apply Minimal WebSocket Fix to Minerva

This script applies the minimal WebSocket fix to enhance reliability:
1. Integrates request tracking with timeout handling
2. Adds monitoring for stuck requests
3. Provides fallback responses for timed-out requests
4. Works with existing authentication mechanisms

The script attempts multiple integration approaches and provides
detailed diagnostics for troubleshooting.
"""
import os
import sys
import time
import logging
import importlib.util
import traceback
from pathlib import Path

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket_fix_application.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('apply_websocket_fix')

# Add Minerva paths to sys.path
minerva_path = Path('/Users/bendickinson/Desktop/Minerva')
sys.path.append(str(minerva_path))
sys.path.append(str(minerva_path / 'web'))

# Import the minimal WebSocket fix
try:
    from minimal_websocket_fix import RequestTracker
    logger.info("✅ Successfully imported minimal_websocket_fix")
except ImportError as e:
    logger.error(f"❌ Failed to import minimal_websocket_fix: {e}")
    print(f"Error: Could not import minimal_websocket_fix module. Make sure it exists in the current directory.")
    sys.exit(1)

def check_minerva_running():
    """Check if the Minerva server is running"""
    try:
        import requests
        response = requests.get("http://localhost:5000/")
        
        if response.status_code == 200:
            logger.info("✅ Minerva server is running")
            return True
        else:
            logger.warning(f"⚠️ Minerva server returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to connect to Minerva server: {e}")
        return False

def find_socketio_module():
    """Find the Flask-SocketIO module in the Minerva codebase"""
    try:
        # Try direct import first
        try:
            from web import socketio
            logger.info("✅ Found socketio in web module")
            return socketio
        except ImportError:
            logger.warning("⚠️ Could not import socketio from web module directly")
        
        # Try to find app.py and import from there
        try:
            from web.app import socketio
            logger.info("✅ Found socketio in web.app module")
            return socketio
        except ImportError:
            logger.warning("⚠️ Could not import socketio from web.app")
        
        # Try to find the module by looking at the file system
        app_file = minerva_path / 'web' / 'app.py'
        if app_file.exists():
            logger.info(f"Found app.py at {app_file}")
            
            spec = importlib.util.spec_from_file_location("app", app_file)
            app_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(app_module)
            
            if hasattr(app_module, 'socketio'):
                logger.info("✅ Found socketio in app.py module")
                return app_module.socketio
        
        logger.error("❌ Could not find socketio module")
        return None
    
    except Exception as e:
        logger.error(f"❌ Error finding socketio module: {e}")
        traceback.print_exc()
        return None

def find_websocket_handler():
    """Find the WebSocket handler function in the Minerva codebase"""
    try:
        # Try different import paths to find the WebSocket handler
        import_paths = [
            "web.sockets.handle_chat_message",
            "web.app.handle_chat_message",
            "sockets.handle_chat_message"
        ]
        
        for path in import_paths:
            try:
                parts = path.split('.')
                module_path = '.'.join(parts[:-1])
                function_name = parts[-1]
                
                module = importlib.import_module(module_path)
                if hasattr(module, function_name):
                    handler = getattr(module, function_name)
                    logger.info(f"✅ Found WebSocket handler at {path}")
                    return module, function_name, handler
            except ImportError:
                logger.warning(f"⚠️ Could not import {path}")
            except Exception as e:
                logger.error(f"❌ Error importing {path}: {e}")
        
        # If we couldn't find it through imports, try to search for it
        logger.warning("⚠️ Could not find WebSocket handler through imports, searching files...")
        
        # Common locations for WebSocket handlers
        possible_files = [
            minerva_path / 'web' / 'sockets.py',
            minerva_path / 'web' / 'app.py',
            minerva_path / 'web' / 'websocket_handlers.py'
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                logger.info(f"Found potential handler file: {file_path}")
                
                # Try to parse the file to find the handler
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Look for common handler patterns
                if 'def handle_chat_message' in content:
                    logger.info(f"✅ Found handle_chat_message in {file_path}")
                    
                    # Load the module
                    module_name = file_path.stem
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'handle_chat_message'):
                        handler = getattr(module, 'handle_chat_message')
                        return module, 'handle_chat_message', handler
        
        logger.error("❌ Could not find WebSocket handler")
        return None, None, None
    
    except Exception as e:
        logger.error(f"❌ Error finding WebSocket handler: {e}")
        traceback.print_exc()
        return None, None, None

def patch_websocket_handler(module, function_name, original_handler):
    """Patch the WebSocket handler with request tracking and timeout handling"""
    if not module or not function_name or not original_handler:
        logger.error("❌ Cannot patch WebSocket handler - missing module, function name, or handler")
        return False
    
    logger.info(f"Attempting to patch {module.__name__}.{function_name}")
    
    # Create the request tracker singleton
    request_tracker = RequestTracker(default_timeout=30)
    request_tracker.start_monitoring()
    
    # Define the patched handler function
    def patched_handler(data):
        """Enhanced WebSocket handler with request tracking and timeout handling"""
        try:
            # Extract message_id and session_id
            message_id = data.get('message_id', 'unknown')
            session_id = data.get('session_id', 'unknown')
            
            logger.info(f"📩 [PATCHED_HANDLER] Received message: ID={message_id}")
            
            # Function to handle timeouts for this request
            def on_timeout(request_id):
                try:
                    logger.warning(f"⏰ [TIMEOUT] Request {request_id} timed out")
                    
                    # Try to import emit function
                    try:
                        from flask_socketio import emit
                    except ImportError:
                        # Fallback - find socketio and use its emit
                        socketio = find_socketio_module()
                        if socketio:
                            emit = socketio.emit
                        else:
                            logger.error("❌ Could not find emit function")
                            return
                    
                    # Send fallback response
                    emit('response', {
                        'message_id': request_id,
                        'session_id': session_id,
                        'response': "I'm sorry, but this request has timed out. Please try again.",
                        'source': 'Timeout Handler',
                        'model_info': {'error': True, 'timeout': True}
                    }, room=session_id)
                    
                    logger.info(f"📤 [FALLBACK_SENT] Sent timeout fallback for {request_id}")
                
                except Exception as e:
                    logger.error(f"❌ [TIMEOUT_HANDLER_ERROR] Error in timeout handler: {e}")
            
            # Track this request
            request_tracker.add_request(
                message_id, 
                session_id=session_id,
                callback=on_timeout
            )
            
            # Call the original handler
            result = original_handler(data)
            
            # When we get here, the handler has processed the request
            # Note: For asynchronous processing, this might not mean it's complete
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [PATCHED_HANDLER_ERROR] Error in patched handler: {e}")
            # Call the original handler if our wrapper fails
            return original_handler(data)
    
    # Apply the patch
    try:
        # Save attributes from the original function
        patched_handler.__name__ = original_handler.__name__
        patched_handler.__module__ = original_handler.__module__
        if hasattr(original_handler, '__qualname__'):
            patched_handler.__qualname__ = original_handler.__qualname__
        
        # Apply the patch
        setattr(module, function_name, patched_handler)
        
        # Verify the patch
        current_handler = getattr(module, function_name)
        if current_handler == patched_handler:
            logger.info(f"✅ Successfully patched {module.__name__}.{function_name}")
            return True
        else:
            logger.error(f"❌ Failed to patch {module.__name__}.{function_name} - verification failed")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error patching WebSocket handler: {e}")
        return False

def setup_socketio_timeouts():
    """Update Flask-SocketIO configuration to use more robust timeout settings"""
    try:
        socketio = find_socketio_module()
        if not socketio:
            logger.error("❌ Could not find socketio module to update timeout settings")
            return False
        
        # Check if this is a Flask-SocketIO instance
        if hasattr(socketio, 'server'):
            # Update the ping_timeout and ping_interval
            original_ping_timeout = getattr(socketio.server, 'ping_timeout', 'unknown')
            original_ping_interval = getattr(socketio.server, 'ping_interval', 'unknown')
            
            logger.info(f"Current ping_timeout: {original_ping_timeout}")
            logger.info(f"Current ping_interval: {original_ping_interval}")
            
            # Set more robust values
            socketio.server.ping_timeout = 10
            socketio.server.ping_interval = 25
            
            logger.info(f"✅ Updated ping_timeout to 10 and ping_interval to 25")
            return True
        else:
            logger.warning("⚠️ Found socketio module but it doesn't have a server attribute")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error updating socketio timeout settings: {e}")
        return False

def apply_fix():
    """Apply the minimal WebSocket fix to Minerva"""
    logger.info("Starting application of minimal WebSocket fix")
    print("📌 Starting application of minimal WebSocket fix")
    
    # Check if Minerva server is running
    if not check_minerva_running():
        logger.warning("⚠️ Minerva server doesn't appear to be running")
        print("⚠️ Warning: Minerva server doesn't appear to be running")
        
        proceed = input("Do you want to proceed with applying the fix anyway? (y/n): ")
        if proceed.lower() != 'y':
            logger.info("User chose not to proceed")
            print("Operation cancelled")
            return False
    
    # Update SocketIO timeout settings
    timeout_success = setup_socketio_timeouts()
    if timeout_success:
        print("✅ Updated SocketIO timeout settings")
    else:
        print("⚠️ Could not update SocketIO timeout settings")
    
    # Find and patch the WebSocket handler
    module, function_name, handler = find_websocket_handler()
    if handler:
        patch_success = patch_websocket_handler(module, function_name, handler)
        if patch_success:
            print(f"✅ Successfully patched WebSocket handler ({module.__name__}.{function_name})")
        else:
            print(f"❌ Failed to patch WebSocket handler")
            logger.error("Patching WebSocket handler failed")
    else:
        print("❌ Could not find WebSocket handler to patch")
        logger.error("Could not find WebSocket handler")
    
    # Summary
    print("\n=== Fix Application Summary ===")
    if timeout_success or (handler and patch_success):
        print("✅ WebSocket fix partially or fully applied")
        print("🔄 The changes will take effect when the Minerva server is restarted")
        logger.info("WebSocket fix application completed with some success")
        return True
    else:
        print("❌ WebSocket fix application failed")
        logger.error("WebSocket fix application failed completely")
        return False

if __name__ == "__main__":
    try:
        apply_fix()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An unexpected error occurred: {e}")
        traceback.print_exc()
