#!/usr/bin/env python3
"""
Socket.IO WebSocket Client for Minerva

This module provides a specialized Socket.IO client with enhanced authentication
and reliability features specifically designed for Minerva's WebSocket implementation.
"""
import os
import sys
import json
import time
import uuid
import logging
import threading
import socketio
from datetime import datetime

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/socketio_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('socketio_client')

class MinervaSocketIOClient:
    """Enhanced Socket.IO client specifically for Minerva with authentication features"""
    
    def __init__(self, url="http://localhost:9876", timeout=30, auto_reconnect=True):
        """Initialize the Socket.IO client
        
        Args:
            url: Socket.IO server URL
            timeout: Timeout for operations in seconds
            auto_reconnect: Whether to automatically reconnect on disconnection
        """
        self.url = url
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        
        # Client state
        self.session_id = None
        self.connected = False
        self.request_callbacks = {}
        self.response_event = threading.Event()
        self.last_response = None
        
        # Authentication state
        self.auth_method = None
        self.auth_credentials = None
        
        # Configure Socket.IO client with reliability features
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=auto_reconnect,
            reconnection_attempts=5,
            reconnection_delay=1,
            reconnection_delay_max=5,
            randomization_factor=0.5
        )
        
        # Register event handlers
        self._register_handlers()
        
        logger.info(f"MinervaSocketIOClient initialized: url={url}, timeout={timeout}s")
    
    def _register_handlers(self):
        """Register Socket.IO event handlers"""
        # Connection events
        @self.sio.event
        def connect():
            self.connected = True
            logger.info("✅ Connected to Minerva Socket.IO server")
            
        @self.sio.event
        def disconnect():
            self.connected = False
            logger.info("🔌 Disconnected from Minerva Socket.IO server")
            
        @self.sio.event
        def connect_error(error):
            logger.error(f"❌ Connection error: {error}")
            
        # Response handlers for different event types
        @self.sio.on('response')
        def on_response(data):
            logger.info(f"📩 Received response: {str(data)[:100]}..." if len(str(data)) > 100 else f"📩 Received response: {data}")
            self._handle_response(data, 'response')
            
        @self.sio.on('chat_response')
        def on_chat_response(data):
            logger.info(f"📩 Received chat response: {str(data)[:100]}..." if len(str(data)) > 100 else f"📩 Received chat response: {data}")
            self._handle_response(data, 'chat_response')
            
        @self.sio.on('think_tank_response')
        def on_think_tank_response(data):
            logger.info(f"📩 Received think tank response: {str(data)[:100]}..." if len(str(data)) > 100 else f"📩 Received think tank response: {data}")
            self._handle_response(data, 'think_tank_response')
            
        @self.sio.on('processing_update')
        def on_processing_update(data):
            logger.info(f"📊 Processing update: {data}")
            # Don't set response event for processing updates
            
        # Catch-all handler for any other events
        @self.sio.on('*')
        def catch_all(event, data):
            logger.debug(f"🔍 Caught event '{event}': {str(data)[:100]}..." if len(str(data)) > 100 else f"🔍 Caught event '{event}': {data}")
    
    def _handle_response(self, data, event_type):
        """Handle response data from any response event"""
        # Store the response
        self.last_response = {
            'event': event_type,
            'data': data,
            'timestamp': datetime.now()
        }
        
        # Set event to signal response received
        self.response_event.set()
        
        # Check if we have a callback for this specific message
        if isinstance(data, dict) and 'message_id' in data:
            message_id = data['message_id']
            if message_id in self.request_callbacks:
                try:
                    # Call the callback with the response data
                    self.request_callbacks[message_id](data)
                    # Remove the callback after it's called
                    del self.request_callbacks[message_id]
                except Exception as e:
                    logger.error(f"❌ Error in callback for message {message_id}: {e}")
    
    def set_authentication(self, method="auto", credentials=None):
        """Set authentication credentials
        
        Args:
            method: Authentication method ('auto', 'cookie', 'token', 'header')
            credentials: Dict with authentication credentials
            
        Returns:
            bool: Whether authentication was successfully set
        """
        if not credentials:
            logger.warning("⚠️ No credentials provided for authentication")
            return False
            
        self.auth_method = method
        self.auth_credentials = credentials
        
        # For Socket.IO, we'll apply these during connection
        # or when joining a conversation
        logger.info(f"✅ Authentication set: method={method}")
        return True
    
    def connect(self):
        """Connect to the Socket.IO server
        
        Returns:
            bool: Whether connection was successful
        """
        logger.info(f"Connecting to Socket.IO server at {self.url}")
        
        # Reset connection state
        self.response_event.clear()
        self.connected = False
        
        try:
            # Apply authentication if using auth headers
            headers = {}
            if self.auth_method == "token" and "token" in self.auth_credentials:
                headers["Authorization"] = f"Bearer {self.auth_credentials['token']}"
            elif self.auth_method == "basic" and "username" in self.auth_credentials and "password" in self.auth_credentials:
                import base64
                auth_str = f"{self.auth_credentials['username']}:{self.auth_credentials['password']}"
                encoded = base64.b64encode(auth_str.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
            elif self.auth_method == "header":
                for key, value in self.auth_credentials.items():
                    headers[key] = value
                    
            # Connect with any auth headers (cookies handled by socketio library)
            if headers:
                logger.info(f"Using authentication headers: {list(headers.keys())}")
                self.sio.connect(self.url, headers=headers, wait=False)
            else:
                self.sio.connect(self.url, wait=False)
                
            # Wait for connection or timeout
            start_time = time.time()
            while not self.connected and time.time() - start_time < self.timeout:
                time.sleep(0.1)
                
            if not self.connected:
                logger.error(f"❌ Connection timeout after {self.timeout}s")
                return False
                
            logger.info("✅ Successfully connected to Socket.IO server")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the Socket.IO server"""
        if self.connected:
            logger.info("Disconnecting from Socket.IO server")
            self.sio.disconnect()
            self.connected = False
    
    def join_conversation(self, session_id=None):
        """Join a conversation with a session ID
        
        Args:
            session_id: Optional session ID, or one will be generated
            
        Returns:
            str: The session ID used
        """
        if not self.connected:
            logger.warning("⚠️ Cannot join conversation: Not connected")
            return None
            
        # Generate session ID if not provided
        self.session_id = session_id or f"minerva_session_{str(uuid.uuid4())}"
        
        # Emit join_conversation event
        logger.info(f"Joining conversation with ID: {self.session_id}")
        self.sio.emit('join_conversation', {'conversation_id': self.session_id})
        
        # Small delay to allow joining to complete
        time.sleep(1)
        
        return self.session_id
    
    def send_message(self, message, mode="think_tank", message_id=None, callback=None):
        """Send a message to the Minerva server
        
        Args:
            message: Text message to send
            mode: Message processing mode (normal, think_tank)
            message_id: Optional custom message ID, or one will be generated
            callback: Optional callback function to be called with the response
            
        Returns:
            str: The message ID used
        """
        if not self.connected:
            logger.warning("⚠️ Cannot send message: Not connected")
            return None
            
        if not self.session_id:
            logger.warning("⚠️ Cannot send message: No active session")
            return None
            
        # Generate message ID if not provided
        message_id = message_id or str(uuid.uuid4())
        
        # Prepare message data
        message_data = {
            'session_id': self.session_id,
            'message_id': message_id,
            'message': message,
            'mode': mode,
            'include_model_info': True  # Include model info in response
        }
        
        # Register callback if provided
        if callback:
            self.request_callbacks[message_id] = callback
            
        # Reset response event
        self.response_event.clear()
        
        # Send the message
        logger.info(f"📤 Sending message: {message[:100]}..." if len(message) > 100 else f"📤 Sending message: {message}")
        logger.debug(f"Message data: {message_data}")
        
        self.sio.emit('chat_message', message_data)
        
        return message_id
    
    def wait_for_response(self, timeout=None):
        """Wait for a response with timeout
        
        Args:
            timeout: Optional timeout override, or use default timeout
            
        Returns:
            dict: The response data or None if timed out
        """
        timeout = timeout or self.timeout
        logger.info(f"Waiting up to {timeout}s for response...")
        
        if self.response_event.wait(timeout):
            logger.info("✅ Response received")
            return self.last_response
        else:
            logger.warning(f"⚠️ Timed out waiting for response after {timeout}s")
            return None
            
    def send_and_wait(self, message, mode="think_tank", timeout=None):
        """Send a message and wait for the response
        
        Args:
            message: Text message to send
            mode: Message processing mode (normal, think_tank)
            timeout: Optional timeout override
            
        Returns:
            dict: The response data or None if timed out
        """
        message_id = self.send_message(message, mode)
        if not message_id:
            return None
            
        return self.wait_for_response(timeout)

# Example usage
if __name__ == "__main__":
    import argparse
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Minerva Socket.IO Client")
    parser.add_argument("--url", type=str, default="http://localhost:9876", 
                      help="Socket.IO server URL")
    parser.add_argument("--message", type=str, default="What is the capital of France?",
                      help="Message to send")
    parser.add_argument("--mode", type=str, default="think_tank", choices=["normal", "think_tank"],
                      help="Message processing mode")
    parser.add_argument("--timeout", type=int, default=30,
                      help="Timeout in seconds")
    parser.add_argument("--verbose", action="store_true",
                      help="Enable verbose logging")
    args = parser.parse_args()
    
    # Enable verbose logging if requested
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create client
    client = MinervaSocketIOClient(url=args.url, timeout=args.timeout)
    
    print("\n" + "=" * 60)
    print(f"🔌 MINERVA SOCKET.IO CLIENT TEST")
    print("=" * 60)
    
    # Connect to server
    print(f"\n🔄 Connecting to {args.url}...")
    if client.connect():
        # Join conversation
        print("\n🔄 Joining conversation...")
        session_id = client.join_conversation()
        
        # Send message
        print(f"\n📤 Sending message: {args.message}")
        print(f"   Mode: {args.mode}")
        
        response = client.send_and_wait(args.message, args.mode)
        
        if response:
            print("\n✅ RESPONSE RECEIVED:")
            print("-" * 40)
            
            data = response['data']
            if isinstance(data, dict):
                # Print the response content
                if 'response' in data:
                    print(f"📝 {data['response']}")
                    
                # Print model info if available
                if 'model_info' in data:
                    print("\n🤖 MODEL INFO:")
                    print(f"   Model: {data['model_info'].get('model', 'Unknown')}")
                    print(f"   Processing Time: {data['model_info'].get('processing_time', 'Unknown')}")
            else:
                print(f"📝 {data}")
                
        # Disconnect
        print("\n🔌 Disconnecting...")
        client.disconnect()
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
    else:
        print("\n❌ CONNECTION FAILED")
        print("=" * 60)
