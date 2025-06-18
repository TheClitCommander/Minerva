#!/usr/bin/env python3
"""
Enhanced Minerva WebSocket Client

This client implements multiple authentication strategies and session initialization
patterns to resolve the 403 Forbidden errors when connecting to Minerva.
"""
import os
import sys
import time
import json
import uuid
import base64
import logging
import requests
import socketio
from urllib.parse import urlparse

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/minerva_websocket.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minerva_websocket')

class EnhancedMinervaClient:
    """
    Enhanced WebSocket client for Minerva with multi-strategy authentication
    and session initialization support.
    """
    
    def __init__(self, url="http://localhost:5000", timeout=30, auto_reconnect=True):
        """Initialize the enhanced Minerva client"""
        self.url = url
        self.base_url = urlparse(url).netloc
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.session = requests.Session()
        self.connected = False
        self.session_id = f"minerva_session_{uuid.uuid4().hex[:8]}"
        
        # Track request information
        self.last_message_id = None
        self.active_requests = {}
        
        # Authentication state
        self.auth_method = None
        self.auth_credentials = {}
        self.auth_headers = {}
        self.cookies = {}
        
        # Setup event handlers
        self._setup_event_handlers()
        
    def _setup_event_handlers(self):
        """Setup default Socket.IO event handlers"""
        @self.sio.event
        def connect():
            self.connected = True
            logger.info("✅ Connected to Minerva WebSocket server")
            # Attempt to join a conversation immediately after connecting
            self.join_conversation(self.session_id)
            
        @self.sio.event
        def disconnect():
            self.connected = False
            logger.info("❌ Disconnected from Minerva WebSocket server")
            if self.auto_reconnect:
                logger.info("🔄 Attempting to reconnect...")
                time.sleep(2)
                self.connect()
                
        @self.sio.event
        def connect_error(data):
            logger.error(f"❌ Connection error: {data}")
            
        # Additional event handlers for Minerva-specific events
        @self.sio.on('response')
        def on_response(data):
            logger.info(f"📥 Received response: {data}")
            msg_id = data.get('message_id')
            if msg_id and msg_id in self.active_requests:
                self.active_requests[msg_id]['response'] = data
                self.active_requests[msg_id]['completed'] = True
                
    def set_authentication(self, method="auto", credentials=None):
        """
        Set authentication method and credentials
        
        Args:
            method (str): Authentication method - "token", "cookie", "basic", "custom", or "auto"
            credentials (dict): Authentication credentials
        """
        self.auth_method = method
        self.auth_credentials = credentials or {}
        
        # Process credentials based on the method
        if method == "token" and "token" in self.auth_credentials:
            self.auth_headers["Authorization"] = f"Bearer {self.auth_credentials['token']}"
        elif method == "basic" and "username" in self.auth_credentials:
            auth_str = f"{self.auth_credentials['username']}:{self.auth_credentials['password']}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            self.auth_headers["Authorization"] = f"Basic {encoded}"
        elif method == "custom" and "headers" in self.auth_credentials:
            self.auth_headers.update(self.auth_credentials["headers"])
            
        logger.info(f"🔒 Authentication set: method={method}")
        return True
        
    def discover_authentication(self):
        """
        Attempt to discover the authentication method by trying different approaches
        
        Returns:
            bool: True if authentication was discovered, False otherwise
        """
        logger.info(f"🔍 Attempting to discover authentication for {self.url}")
        
        # Try main page
        try:
            logger.info(f"🔍 Checking main page at {self.url}")
            response = self.session.get(self.url, timeout=self.timeout)
            logger.info(f"📊 Server response: {response.status_code}")
            
            # Save cookies
            if response.cookies:
                self.cookies = {k: v for k, v in response.cookies.items()}
                logger.info(f"🍪 Found cookies: {self.cookies}")
                
            # Look for CSRF token in response body
            if response.status_code == 200 and 'csrf' in response.text.lower():
                logger.info("🔍 Checking for CSRF token")
                csrf_token = self._extract_csrf_token(response.text)
                if csrf_token:
                    logger.info(f"🔑 Found CSRF token: {csrf_token}")
                    self.auth_headers["X-CSRF-Token"] = csrf_token
                    
        except Exception as e:
            logger.error(f"❌ Error checking main page: {e}")
            
        # Try different auth endpoints
        auth_endpoints = ['/login', '/auth', '/signin', '/api/auth', '/api/login']
        for endpoint in auth_endpoints:
            full_url = f"{self.url.rstrip('/')}{endpoint}"
            try:
                logger.info(f"🔍 Checking auth endpoint: {full_url}")
                response = self.session.get(full_url, timeout=self.timeout)
                logger.info(f"📊 Endpoint {endpoint} response: {response.status_code}")
                
                if response.status_code == 200:
                    # Update cookies from auth endpoint
                    if response.cookies:
                        self.cookies.update({k: v for k, v in response.cookies.items()})
                        logger.info(f"🍪 Updated cookies from {endpoint}: {self.cookies}")
                    break
                    
            except Exception as e:
                logger.error(f"❌ Error checking {endpoint}: {e}")
                
        # Set any discovered cookies
        if self.cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            self.auth_headers["Cookie"] = cookie_str
            
        # Add custom Minerva headers that might be required
        self.auth_headers.update({
            "X-Minerva-Session-ID": self.session_id,
            "X-Minerva-Client-Type": "websocket",
            "X-Minerva-Transaction-ID": f"tx_{int(time.time())}",
            "X-Minerva-Model-Request": "default"
        })
        
        logger.info(f"🔒 Authentication discovery completed: {len(self.auth_headers)} headers set")
        return len(self.auth_headers) > 0
        
    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content"""
        import re
        # Look for common CSRF token patterns
        patterns = [
            r'<meta\s+name="csrf-token"\s+content="([^"]+)"',
            r'<input\s+type="hidden"\s+name="_csrf_token"\s+value="([^"]+)"',
            r'<input\s+type="hidden"\s+name="csrf_token"\s+value="([^"]+)"',
            r'csrfToken\s*=\s*[\'"]([^"\']+)[\'"]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content)
            if match:
                return match.group(1)
        return None
    
    def connect(self, discover_auth=True, eio_version=None):
        """
        Connect to the Minerva Socket.IO server
        
        Args:
            discover_auth (bool): Whether to attempt to discover authentication
            eio_version (int): Engine.IO version to use (3 or 4)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        logger.info(f"🔌 Connecting to Minerva at {self.url}")
        
        # Try to discover authentication if needed
        if discover_auth and not self.auth_headers:
            self.discover_authentication()
            
        # Prepare connection parameters
        connect_params = {}
        if eio_version:
            connect_params['eio_version'] = eio_version
        
        try:
            # Add session ID to transports query
            transports_url = f"{self.url}/socket.io/?EIO={eio_version or 3}&transport=websocket&sid={self.session_id}"
            logger.info(f"🔌 Using transport URL: {transports_url}")
            
            # Connect with auth headers
            if self.auth_headers:
                logger.info(f"🔒 Connecting with {len(self.auth_headers)} auth headers")
                self.sio.connect(
                    self.url, 
                    headers=self.auth_headers,
                    wait=True,
                    wait_timeout=self.timeout,
                    **connect_params
                )
            else:
                logger.info("🔓 Connecting without auth headers")
                self.sio.connect(
                    self.url,
                    wait=True,
                    wait_timeout=self.timeout, 
                    **connect_params
                )
                
            return self.connected
            
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
            
            # Try fallback connection with different EIO version
            if eio_version != 4 and "Invalid transport" in str(e):
                logger.info("🔄 Trying fallback connection with EIO v4")
                return self.connect(discover_auth=False, eio_version=4)
                
            return False
    
    def join_conversation(self, conversation_id=None):
        """
        Join a conversation - required step for Minerva before sending messages
        
        Args:
            conversation_id (str): Conversation ID to join
        """
        cid = conversation_id or self.session_id
        logger.info(f"👥 Joining conversation: {cid}")
        
        try:
            self.sio.emit('join_conversation', {'conversation_id': cid})
            logger.info(f"👥 Join request sent for conversation: {cid}")
            return True
        except Exception as e:
            logger.error(f"❌ Error joining conversation: {e}")
            return False
            
    def send_message(self, message, mode="normal", wait_for_response=True, timeout=None):
        """
        Send a message to Minerva
        
        Args:
            message (str): Message to send
            mode (str): Processing mode (normal, think_tank)
            wait_for_response (bool): Whether to wait for a response
            timeout (int): Response timeout in seconds
            
        Returns:
            dict: Response data or None
        """
        if not self.connected:
            logger.warning("⚠️ Not connected, attempting to connect...")
            if not self.connect():
                logger.error("❌ Failed to connect, cannot send message")
                return None
        
        # Generate message ID  
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        self.last_message_id = message_id
        
        # Prepare message data
        message_data = {
            'message_id': message_id,
            'session_id': self.session_id, 
            'message': message,
            'mode': mode
        }
        
        # Track this request
        self.active_requests[message_id] = {
            'timestamp': time.time(),
            'message': message,
            'completed': False,
            'response': None
        }
        
        logger.info(f"📤 Sending message: {message_id}")
        
        try:
            # Send the message
            self.sio.emit('chat_message', message_data)
            
            # Wait for response if requested
            if wait_for_response:
                wait_timeout = timeout or self.timeout
                logger.info(f"⏳ Waiting for response (timeout: {wait_timeout}s)")
                
                start_time = time.time()
                while time.time() - start_time < wait_timeout:
                    if (message_id in self.active_requests and 
                        self.active_requests[message_id].get('completed')):
                        response = self.active_requests[message_id].get('response')
                        logger.info(f"✅ Response received for {message_id}")
                        return response
                    time.sleep(0.1)
                    
                logger.warning(f"⚠️ Timeout waiting for response to {message_id}")
                return None
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending message: {e}")
            return None
            
    def disconnect(self):
        """Disconnect from the Socket.IO server"""
        if self.connected:
            logger.info("🔌 Disconnecting from server")
            try:
                self.sio.disconnect()
                return True
            except Exception as e:
                logger.error(f"❌ Error disconnecting: {e}")
                return False
        return True


def test_minerva_connection(url="http://localhost:5000"):
    """
    Test Minerva connection with multiple authentication strategies
    
    Args:
        url (str): Minerva server URL
        
    Returns:
        tuple: (success, client, response) - whether connection was successful, 
               client instance, and response data
    """
    logger.info(f"🧪 Testing Minerva connection to {url}")
    
    # 1. Test with EIO version 3
    logger.info("🔍 Testing with Engine.IO v3")
    client = EnhancedMinervaClient(url=url)
    if client.connect(eio_version=3):
        logger.info("✅ Connected with EIO v3")
        response = client.send_message("Hello, Minerva!")
        if response:
            logger.info("✅ Message sent and response received")
            return True, client, response
        client.disconnect()
    
    # 2. Test with EIO version 4
    logger.info("🔍 Testing with Engine.IO v4")
    client = EnhancedMinervaClient(url=url)
    if client.connect(eio_version=4):
        logger.info("✅ Connected with EIO v4")
        response = client.send_message("Hello, Minerva!")
        if response:
            logger.info("✅ Message sent and response received")
            return True, client, response
        client.disconnect()
    
    # 3. Test with custom headers including session ID
    logger.info("🔍 Testing with custom Minerva headers")
    client = EnhancedMinervaClient(url=url)
    session_id = f"minerva_session_{uuid.uuid4().hex[:8]}"
    client.set_authentication("custom", {
        "headers": {
            "X-Minerva-Session-ID": session_id,
            "X-Minerva-Client-Type": "websocket",
            "X-Minerva-Transaction-ID": f"tx_{int(time.time())}",
            "X-Minerva-Model-Request": "default"
        }
    })
    if client.connect(discover_auth=False):
        logger.info("✅ Connected with custom Minerva headers")
        # Explicitly join a conversation first
        client.join_conversation(session_id)
        time.sleep(1)  # Wait for join to complete
        
        response = client.send_message("Hello, Minerva!")
        if response:
            logger.info("✅ Message sent and response received")
            return True, client, response
        client.disconnect()
    
    logger.error("❌ All connection attempts failed")
    return False, client, None


if __name__ == "__main__":
    print("🔌 Minerva Enhanced WebSocket Client")
    print("====================================")
    
    # Test different server ports
    for port in [5000, 5050, 9876]:
        url = f"http://localhost:{port}"
        print(f"\nTesting connection to {url}...")
        
        success, client, response = test_minerva_connection(url)
        
        if success:
            print(f"\n✅ Successfully connected to Minerva at {url}")
            if response:
                print(f"📊 Response: {json.dumps(response, indent=2)}")
            break
        else:
            print(f"\n❌ Failed to connect to Minerva at {url}")
    
    if not success:
        print("\n📋 All connection attempts failed. Check logs for details.")
