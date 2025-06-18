#!/usr/bin/env python3
"""
Enhanced WebSocket Verification for Minerva

This script provides a comprehensive verification process for testing
the WebSocket and Think Tank reliability fixes:
1. Progressive testing - checks server, then auth, then WebSocket
2. Detailed diagnostics - captures and logs all connection issues
3. Authentication support - handles session cookies and tokens
4. Think Tank verification - ensures model routing and quality validation work
"""
import os
import sys
import time
import json
import uuid
import logging
import argparse
import threading
import traceback
from datetime import datetime
import requests
import websocket

# Import our minimal WebSocket fix
try:
    from minimal_websocket_fix import WebSocketClient
except ImportError:
    print("❌ Error: minimal_websocket_fix.py not found. Make sure it's in the current directory.")
    sys.exit(1)

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_verification')

# Parse command line arguments
parser = argparse.ArgumentParser(description='Enhanced WebSocket Verification')
parser.add_argument('--server', type=str, default='http://localhost:5000',
                    help='Minerva server URL')
parser.add_argument('--auth', action='store_true',
                    help='Use authentication')
parser.add_argument('--timeout', type=int, default=60,
                    help='Timeout for test in seconds')
parser.add_argument('--test-mode', type=str, choices=['basic', 'think_tank', 'timeout', 'all'],
                   default='all', help='Test mode')
parser.add_argument('--cookie-file', type=str,
                    help='Path to file containing cookies (name=value format)')
parser.add_argument('--token-file', type=str,
                    help='Path to file containing authentication token')
parser.add_argument('--token', type=str,
                    help='Authentication token')
parser.add_argument('--username', type=str,
                    help='Username for basic authentication')
parser.add_argument('--password', type=str,
                    help='Password for basic authentication')
parser.add_argument('--auth-method', type=str, choices=['auto', 'cookie', 'token', 'basic', 'header'],
                    default='auto', help='Authentication method to use')
parser.add_argument('--header', type=str, action='append',
                    help='Custom headers in format "Name: Value" (can be used multiple times)')
parser.add_argument('--fallback', action='store_true',
                    help='Enable fallback to HTTP polling if WebSocket fails')
parser.add_argument('--verbose', action='store_true',
                    help='Enable verbose logging')
args = parser.parse_args()

# Set log level based on verbosity
if args.verbose:
    logger.setLevel(logging.DEBUG)

# URLs and configuration
SERVER_URL = args.server
WS_URL = f"{SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://')}/socket.io/?EIO=3&transport=websocket"
SESSION_COOKIE = None
CSRF_TOKEN = None
AUTH_TOKEN = None

class EnhancedVerification:
    """Enhanced verification for WebSocket and Think Tank functionality"""
    
    def __init__(self):
        self.responses = {}
        self.response_events = {}
        self.ws_client = None
        self.success = False
        self.headers = {}
        self.cookies = {}
        
    def check_server_running(self):
        """Check if the Minerva server is running and get auth tokens if needed"""
        logger.info(f"Checking server at {SERVER_URL}")
        
        try:
            # Start with a basic connection test
            response = requests.get(f"{SERVER_URL}/", timeout=10)
            
            # Check the status
            if response.status_code == 200:
                logger.info(f"✅ Server is running ({response.status_code})")
                print(f"✅ Server is running ({response.status_code})")
                
                # Extract auth cookies if present
                if 'set-cookie' in response.headers:
                    cookie_header = response.headers['set-cookie']
                    logger.info(f"Found cookies: {cookie_header}")
                    
                    # Parse session cookie
                    if 'session=' in cookie_header:
                        start = cookie_header.find('session=') + 8
                        end = cookie_header.find(';', start)
                        if end == -1:
                            end = len(cookie_header)
                        self.cookies['session'] = cookie_header[start:end]
                        logger.info(f"Extracted session cookie: {self.cookies['session'][:10]}...")
                
                # Check for CSRF token in the response body
                if 'csrf_token' in response.text:
                    # Simple extraction - might need adjustment based on actual format
                    start = response.text.find('csrf_token') + 10
                    start = response.text.find('"', start) + 1
                    end = response.text.find('"', start)
                    
                    if start > 0 and end > start:
                        self.headers['X-CSRFToken'] = response.text[start:end]
                        logger.info(f"Extracted CSRF token: {self.headers['X-CSRFToken'][:10]}...")
                
                return True
            else:
                logger.error(f"❌ Server returned status code {response.status_code}")
                print(f"❌ Server returned status code {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error connecting to server: {e}")
            print(f"❌ Error connecting to server: {e}")
            return False
    
    def extract_cookies_from_file(self, cookie_file):
        """Extract cookies from a file with format 'name=value'"""
        extracted_cookies = {}
        try:
            with open(cookie_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        name, value = line.split('=', 1)
                        extracted_cookies[name] = value
            logger.info(f"Loaded {len(extracted_cookies)} cookies from {cookie_file}")
            return extracted_cookies
        except Exception as e:
            logger.error(f"Failed to load cookies from {cookie_file}: {e}")
            return {}
    
    def extract_token_from_file(self, token_file):
        """Extract token from a file containing just the token string"""
        try:
            with open(token_file, 'r') as f:
                token = f.read().strip()
            if token:
                logger.info(f"Loaded token from {token_file}: {token[:10]}...")
                return token
            else:
                logger.error(f"Token file {token_file} is empty")
                return None
        except Exception as e:
            logger.error(f"Failed to load token from {token_file}: {e}")
            return None
            
    def authenticate(self):
        """Authenticate with the server if needed"""
        if not args.auth:
            logger.info("Authentication not requested, skipping")
            print("Authentication not requested, skipping")
            return True
            
        logger.info("Attempting to authenticate with server")
        print("Attempting to authenticate with server")
        
        # Check for authentication credentials from command line args
        auth_method = args.auth_method
        auth_provided = False
        
        # Load credentials from files if specified
        if args.cookie_file:
            file_cookies = self.extract_cookies_from_file(args.cookie_file)
            if file_cookies:
                self.cookies.update(file_cookies)
                auth_provided = True
                if auth_method == 'auto':
                    auth_method = 'cookie'
        
        if args.token_file:
            token = self.extract_token_from_file(args.token_file)
            if token:
                AUTH_TOKEN = token
                self.headers['Authorization'] = f"Bearer {token}"
                auth_provided = True
                if auth_method == 'auto':
                    auth_method = 'token'
        
        if args.token:
            AUTH_TOKEN = args.token
            self.headers['Authorization'] = f"Bearer {args.token}"
            auth_provided = True
            if auth_method == 'auto':
                auth_method = 'token'
        
        if args.username and args.password:
            import base64
            auth_str = f"{args.username}:{args.password}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            self.headers['Authorization'] = f"Basic {encoded}"
            auth_provided = True
            if auth_method == 'auto':
                auth_method = 'basic'
                
        if args.header:
            for header in args.header:
                if ':' in header:
                    key, value = header.split(':', 1)
                    self.headers[key.strip()] = value.strip()
                    auth_provided = True
                    if auth_method == 'auto':
                        auth_method = 'header'
        
        # If no authentication provided, try interactive login
        if not auth_provided:
            try:
                # Try to access a protected route to test authentication
                auth_url = f"{SERVER_URL}/api/protected"
                
                response = requests.get(
                    auth_url,
                    cookies=self.cookies,
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("✅ Authentication successful")
                    print("✅ Authentication successful")
                    return True
                elif response.status_code == 401 or response.status_code == 403:
                    logger.error(f"❌ Authentication failed: {response.status_code}")
                    print(f"❌ Authentication failed: {response.status_code}")
                    
                    # Try to login if credentials are provided
                    print("\nWould you like to try logging in? (y/n): ", end="")
                    choice = input().lower()
                    
                    if choice == 'y':
                        username = input("Username: ")
                        password = input("Password: ")
                        
                        login_url = f"{SERVER_URL}/login"
                        login_data = {
                            "username": username,
                            "password": password
                        }
                    
                    login_response = requests.post(
                        login_url,
                        data=login_data,
                        cookies=self.cookies,
                        headers=self.headers,
                        timeout=10
                    )
                    
                    if login_response.status_code == 200:
                        # Update cookies and tokens
                        self.cookies.update(login_response.cookies)
                        
                        if 'set-cookie' in login_response.headers:
                            cookie_header = login_response.headers['set-cookie']
                            if 'session=' in cookie_header:
                                start = cookie_header.find('session=') + 8
                                end = cookie_header.find(';', start)
                                if end == -1:
                                    end = len(cookie_header)
                                self.cookies['session'] = cookie_header[start:end]
                        
                        logger.info("✅ Login successful")
                        print("✅ Login successful")
                        return True
                    else:
                        logger.error(f"❌ Login failed: {login_response.status_code}")
                        print(f"❌ Login failed: {login_response.status_code}")
                        return False
                else:
                    return False
            else:
                logger.warning(f"⚠️ Unexpected status: {response.status_code}")
                print(f"⚠️ Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in authentication: {e}")
            print(f"❌ Error in authentication: {e}")
            return False
    
    def on_response(self, data):
        """Handle WebSocket responses"""
        try:
            # Extract message_id
            message_id = data.get('message_id', 'unknown')
            
            # Log the response
            source = data.get('source', 'Unknown')
            logger.info(f"✅ Received response from {source} for message {message_id}")
            
            # Save the response data
            self.responses[message_id] = data
            
            # Signal that we got a response for this message
            if message_id in self.response_events:
                self.response_events[message_id].set()
            
            # Check for Think Tank mode
            model_info = data.get('model_info', {})
            if source.lower() == 'think tank' or model_info.get('think_tank', False):
                logger.info("✅ Response came from Think Tank mode")
                print("✅ Response came from Think Tank mode")
                
                # Check additional Think Tank metrics if available
                if 'models_used' in model_info:
                    logger.info(f"Think Tank used {model_info['models_used']} models")
                if 'quality_score' in model_info:
                    logger.info(f"Response quality score: {model_info['quality_score']}")
            
            # Extract response text
            response_text = data.get('response', '')
            if response_text:
                # Log a preview
                preview = response_text[:100] + '...' if len(response_text) > 100 else response_text
                logger.info(f"Response preview: {preview}")
                print(f"\nResponse preview: {preview}")
        
        except Exception as e:
            logger.error(f"❌ Error processing response: {e}")
            print(f"❌ Error processing response: {e}")
    
    def send_test_message(self, mode='normal', timeout=30):
        """Send a test message and wait for the response"""
        # Make sure we have a connection
        if not self.ws_client or not self.ws_client.connected:
            logger.error("❌ WebSocket not connected")
            print("❌ WebSocket not connected")
            return None
        
        # Create a unique message ID
        message_id = str(uuid.uuid4())
        
        # Create an event for this message
        self.response_events[message_id] = threading.Event()
        
        # Prepare test data
        if mode == 'normal':
            message = "What's the weather like today?"
            test_mode = 'normal'
        elif mode == 'think_tank':
            message = "What are the differences between supervised and unsupervised learning in machine learning?"
            test_mode = 'think_tank'
        elif mode == 'timeout':
            message = "This is a timeout test"
            test_mode = 'test_timeout'
        else:
            message = "Hello, this is a test message"
            test_mode = 'normal'
        
        # Create the payload
        payload = {
            'message_id': message_id,
            'message': message,
            'mode': test_mode
        }
        
        # Send the message
        logger.info(f"Sending test message: ID={message_id}, Mode={test_mode}")
        print(f"Sending test message: {message} (ID: {message_id}, Mode: {test_mode})")
        
        self.ws_client.send('chat_message', payload, callback=self.on_response, timeout=timeout)
        
        # Wait for a response
        if self.response_events[message_id].wait(timeout):
            logger.info(f"✅ Received response for message {message_id}")
            print(f"✅ Received response for message {message_id}")
            return message_id
        else:
            logger.error(f"❌ Timed out waiting for response to message {message_id}")
            print(f"❌ Timed out waiting for response to message {message_id}")
            return None
    
    def connect_websocket(self):
        """Connect to the WebSocket server with enhanced authentication"""
        logger.info(f"Connecting to WebSocket at {WS_URL}")
        print(f"Connecting to WebSocket at {WS_URL}")
        
        try:
            # Create the WebSocketClient with our enhanced features
            self.ws_client = WebSocketClient(
                url=WS_URL,
                timeout=args.timeout,
                auto_reconnect=True,
                fallback_to_polling=args.fallback
            )
            
            # Set authentication based on method and available credentials
            auth_credentials = {}
            auth_method = args.auth_method
            
            # Determine authentication method and credentials
            if self.cookies:
                auth_credentials.update(self.cookies)
                if auth_method == 'auto':
                    auth_method = 'cookie'
            
            if 'Authorization' in self.headers:
                auth_header = self.headers['Authorization']
                if auth_header.startswith('Bearer '):
                    auth_credentials['token'] = auth_header[7:]
                    if auth_method == 'auto':
                        auth_method = 'token'
                elif auth_header.startswith('Basic '):
                    auth_credentials['authorization'] = auth_header
                    if auth_method == 'auto':
                        auth_method = 'basic'
            
            # Add all headers as potential credentials
            for key, value in self.headers.items():
                if key not in ['Cookie', 'Authorization']:
                    auth_credentials[key] = value
            
            # Set the authentication on the client if we have credentials
            if auth_credentials:
                logger.info(f"Setting authentication with method: {auth_method}")
                auth_success = self.ws_client.set_authentication(
                    method=auth_method,
                    credentials=auth_credentials
                )
                if auth_success:
                    logger.info("✅ Authentication credentials applied successfully")
                    print("✅ Authentication credentials applied successfully")
                else:
                    logger.warning("⚠️ Failed to apply authentication credentials")
                    print("⚠️ Failed to apply authentication credentials")
            
            # Connect with a timeout
            connected = self.ws_client.connect(timeout=10)
            
            if connected:
                logger.info("✅ WebSocket connection established")
                print("✅ WebSocket connection established")
                return True
            else:
                logger.error("❌ WebSocket connection failed")
                print("❌ WebSocket connection failed")
                
                # Check if we're using fallback
                if args.fallback and self.ws_client.using_fallback:
                    logger.info("✅ Using HTTP polling fallback")
                    print("✅ Using HTTP polling fallback")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error connecting to WebSocket: {e}")
            print(f"❌ Error connecting to WebSocket: {e}")
            traceback.print_exc()
            return False
    
    def run_tests(self):
        """Run the requested tests"""
        tests_passed = 0
        tests_failed = 0
        
        # Run basic test
        if args.test_mode in ['basic', 'all']:
            print("\n=== Running Basic Message Test ===")
            message_id = self.send_test_message(mode='normal', timeout=args.timeout)
            
            if message_id and message_id in self.responses:
                print("✅ Basic message test passed")
                tests_passed += 1
            else:
                print("❌ Basic message test failed")
                tests_failed += 1
        
        # Run Think Tank test
        if args.test_mode in ['think_tank', 'all']:
            print("\n=== Running Think Tank Test ===")
            message_id = self.send_test_message(mode='think_tank', timeout=args.timeout)
            
            if message_id and message_id in self.responses:
                response = self.responses[message_id]
                source = response.get('source', '').lower()
                model_info = response.get('model_info', {})
                
                if 'think tank' in source or model_info.get('think_tank', False):
                    print("✅ Think Tank test passed")
                    tests_passed += 1
                else:
                    print(f"❌ Think Tank test failed - response source: {source}")
                    tests_failed += 1
            else:
                print("❌ Think Tank test failed - no response received")
                tests_failed += 1
        
        # Run timeout test
        if args.test_mode in ['timeout', 'all']:
            print("\n=== Running Timeout Handling Test ===")
            message_id = self.send_test_message(mode='timeout', timeout=args.timeout)
            
            if message_id and message_id in self.responses:
                response = self.responses[message_id]
                model_info = response.get('model_info', {})
                
                if model_info.get('timeout', False):
                    print("✅ Timeout handling test passed")
                    tests_passed += 1
                else:
                    print("❌ Timeout handling test failed - response didn't indicate timeout")
                    tests_failed += 1
            else:
                print("❌ Timeout handling test failed - no response received")
                tests_failed += 1
        
        # Report results
        print(f"\n=== Test Results: {tests_passed} passed, {tests_failed} failed ===")
        
        return tests_passed > 0 and tests_failed == 0
    
    def close_connection(self):
        """Close the WebSocket connection"""
        if self.ws_client:
            self.ws_client.close()
            logger.info("WebSocket connection closed")
            print("WebSocket connection closed")
    
    def run_verification(self):
        """Run the complete verification process with enhanced diagnostics"""
        print("\n📋 ENHANCED WEBSOCKET VERIFICATION")
        logger.info("=== Starting Enhanced WebSocket Verification ===")
        print("=== Starting Enhanced WebSocket Verification ===\n")
        
        # Print the configuration
        print(f"🔷 Server URL: {SERVER_URL}")
        print(f"🔷 WebSocket URL: {WS_URL}")
        print(f"🔷 Authentication: {'Enabled' if args.auth else 'Disabled'}")
        if args.auth:
            print(f"🔷 Auth Method: {args.auth_method}")
        print(f"🔷 Test Mode: {args.test_mode}")
        print(f"🔷 Timeout: {args.timeout}s")
        print(f"🔷 Fallback to HTTP polling: {'Enabled' if args.fallback else 'Disabled'}")
        print("\n")
        
        try:
            # Step 1: Check if server is running
            print("🔍 Checking server status...")
            if not self.check_server_running():
                logger.error("❌ Verification failed: Server not running")
                print("\n❌ Verification failed: Server not running or inaccessible")
                return False
            print("✅ Server check passed\n")
            
            # Step 2: Authenticate if requested
            if args.auth:
                print("🔑 Authenticating with server...")
                if not self.authenticate():
                    logger.error("❌ Verification failed: Authentication failed")
                    print("\n❌ Verification failed: Authentication failed")
                    return False
                print("✅ Authentication successful\n")
            
            # Step 3: Connect to WebSocket
            print("🔌 Connecting to WebSocket...")
            if not self.connect_websocket():
                logger.error("❌ Verification failed: Could not connect to WebSocket")
                print("\n❌ Verification failed: Could not connect to WebSocket")
                
                # Detailed diagnostics for WebSocket connection failure
                print("\n🛠 DIAGNOSTIC INFORMATION:")
                print(f"1. Server URL: {SERVER_URL}")
                print(f"2. WebSocket URL: {WS_URL}")
                print(f"3. Authentication enabled: {args.auth}")
                print(f"4. Headers: {json.dumps(self.headers, indent=2)}")
                print(f"5. Cookies: {json.dumps(self.cookies, indent=2)}")
                
                return False
            print("✅ WebSocket connection successful\n")
            
            # Step 4: Run the requested tests
            print("🧪 Running verification tests...")
            success = self.run_tests()
            
            # Step 5: Close the connection
            self.close_connection()
            
            if success:
                logger.info("✅ Verification test passed!")
                print("\n🎉 VERIFICATION COMPLETED SUCCESSFULLY")
                print("WebSocket connection is stable and the requested features are working")
                
                # Provide a summary based on connection type
                if self.ws_client and self.ws_client.using_fallback:
                    print("\n📝 SUMMARY: The system is working but using HTTP polling fallback")
                    print("    This indicates WebSocket connection issues but the system")
                    print("    is still functional through the fallback mechanism.")
                else:
                    print("\n📝 SUMMARY: The WebSocket connection is working properly")
                    print("    All tests passed with direct WebSocket communication.")
                    
                # Print auth method used
                if args.auth:
                    print(f"\n🔐 Authentication method used: {args.auth_method}")
            else:
                logger.error("❌ Verification test failed")
                print("\n❌ VERIFICATION FAILED")
                print("Some tests failed - check the logs for details")
            
            logger.info("====== Verification Test Complete ======")
            print("\n====== Verification Test Complete ======")
            return success
            
        except KeyboardInterrupt:
            logger.info("Verification interrupted by user")
            print("\nVerification interrupted by user")
            self.close_connection()
            return False
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"\n❌ Unexpected error: {e}")
            traceback.print_exc()
            self.close_connection()
            return False

if __name__ == "__main__":
    verification = EnhancedVerification()
    result = verification.run_verification()
    sys.exit(0 if result else 1)
