#!/usr/bin/env python3
"""
WebSocket Authentication Debugger for Minerva

This script helps diagnose authentication issues by:
1. Testing HTTP endpoint access with different auth methods
2. Extracting authentication tokens and cookies
3. Attempting WebSocket connections with various auth combinations
4. Providing detailed diagnostics on what works and what doesn't
"""
import os
import sys
import json
import time
import logging
import argparse
import requests
from urllib.parse import urlparse
import websocket

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/websocket_auth_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('websocket_auth_debug')

# Parse command-line arguments
parser = argparse.ArgumentParser(description='WebSocket Authentication Debugger for Minerva')
parser.add_argument('--server', type=str, default='http://localhost:5000',
                    help='Minerva server URL')
parser.add_argument('--username', type=str, help='Username for login')
parser.add_argument('--password', type=str, help='Password for login')
parser.add_argument('--login-path', type=str, default='/login',
                    help='Path to login endpoint')
parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
args = parser.parse_args()

if args.verbose:
    logger.setLevel(logging.DEBUG)

# Authentication state
auth_state = {
    'session_cookie': None,
    'csrf_token': None,
    'auth_token': None,
    'cookies': {},
    'headers': {}
}

def test_basic_connectivity():
    """Test basic connectivity to the server"""
    logger.info(f"Testing basic connectivity to {args.server}")
    print(f"\n🔍 Testing basic connectivity to {args.server}")
    
    try:
        response = requests.get(f"{args.server}/", timeout=10)
        logger.info(f"Server returned status code {response.status_code}")
        print(f"Server returned status code {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ Basic connectivity successful")
            return True
        elif response.status_code == 403:
            print(f"⚠️ Server requires authentication (403 Forbidden)")
            return False
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection error: {e}")
        print(f"❌ Connection error: {e}")
        return False

def extract_auth_from_response(response):
    """Extract authentication tokens and cookies from a response"""
    # Extract cookies
    for cookie in response.cookies:
        auth_state['cookies'][cookie.name] = cookie.value
        logger.debug(f"Found cookie: {cookie.name}")
        
        if cookie.name.lower() == 'session':
            auth_state['session_cookie'] = cookie.value
            logger.info(f"Found session cookie: {cookie.name}={cookie.value[:5]}...")
            
    # Check for CSRF token in the response body
    if 'csrf_token' in response.text:
        try:
            # Try to find it in a JSON response
            data = response.json()
            if 'csrf_token' in data:
                auth_state['csrf_token'] = data['csrf_token']
                auth_state['headers']['X-CSRFToken'] = data['csrf_token']
                logger.info(f"Found CSRF token in JSON: {auth_state['csrf_token'][:10]}...")
        except:
            # Try to extract from HTML/text
            text = response.text.lower()
            if 'csrf_token' in text:
                # Simple extraction - might need adjustment based on actual format
                start = text.find('csrf_token') + 10
                start = text.find('"', start) + 1
                end = text.find('"', start)
                
                if start > 0 and end > start:
                    token = text[start:end]
                    auth_state['csrf_token'] = token
                    auth_state['headers']['X-CSRFToken'] = token
                    logger.info(f"Found CSRF token in HTML: {token[:10]}...")
    
    # Look for auth tokens in response headers
    if 'authorization' in response.headers:
        auth_state['auth_token'] = response.headers['authorization']
        auth_state['headers']['Authorization'] = response.headers['authorization']
        logger.info(f"Found Authorization header: {auth_state['auth_token'][:10]}...")
    
    return auth_state

def attempt_login():
    """Attempt to login using provided credentials"""
    if not args.username or not args.password:
        logger.info("No login credentials provided, skipping login attempt")
        print("No login credentials provided, skipping login attempt")
        return False
    
    logger.info(f"Attempting to login as {args.username}")
    print(f"\n🔑 Attempting to login as {args.username}")
    
    try:
        login_url = f"{args.server}{args.login_path}"
        login_data = {
            "username": args.username,
            "password": args.password
        }
        
        # First, get the login page to extract any CSRF tokens
        response = requests.get(login_url, timeout=10)
        extract_auth_from_response(response)
        
        # Now attempt the login
        login_response = requests.post(
            login_url,
            data=login_data,
            cookies=auth_state['cookies'],
            headers=auth_state['headers'],
            timeout=10
        )
        
        if login_response.status_code == 200:
            logger.info("Login successful")
            print("✅ Login successful")
            extract_auth_from_response(login_response)
            return True
        else:
            logger.error(f"Login failed with status code {login_response.status_code}")
            print(f"❌ Login failed with status code {login_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Login error: {e}")
        print(f"❌ Login error: {e}")
        return False

def check_protected_endpoints():
    """Check access to protected endpoints with current auth state"""
    protected_paths = [
        '/api/protected',  # Generic protected endpoint
        '/api/user',       # User info endpoint
        '/api/settings',   # Settings endpoint
        '/think_tank'      # Think Tank endpoint
    ]
    
    logger.info("Testing access to potentially protected endpoints")
    print("\n🔒 Testing access to potentially protected endpoints")
    
    results = {}
    
    for path in protected_paths:
        url = f"{args.server}{path}"
        try:
            response = requests.get(
                url,
                cookies=auth_state['cookies'],
                headers=auth_state['headers'],
                timeout=10
            )
            
            status = response.status_code
            results[path] = status
            
            log_msg = f"Endpoint {path}: {status}"
            if status == 200:
                logger.info(f"✅ {log_msg}")
                print(f"✅ {log_msg} (Accessible)")
            elif status == 403 or status == 401:
                logger.info(f"❌ {log_msg}")
                print(f"❌ {log_msg} (Requires Authentication)")
            else:
                logger.info(f"⚠️ {log_msg}")
                print(f"⚠️ {log_msg} (Unexpected Status)")
                
        except requests.exceptions.RequestException as e:
            results[path] = str(e)
            logger.error(f"Error accessing {path}: {e}")
            print(f"❌ Error accessing {path}: {e}")
    
    return results

def attempt_websocket_connection(auth_mode='none'):
    """Attempt WebSocket connection with different authentication modes"""
    server_url = args.server
    if server_url.startswith('http://'):
        ws_url = server_url.replace('http://', 'ws://')
    elif server_url.startswith('https://'):
        ws_url = server_url.replace('https://', 'wss://')
    else:
        ws_url = f"ws://{server_url}"
    
    # Add socket.io path if not present
    if not "/socket.io/" in ws_url:
        ws_url = f"{ws_url}/socket.io/?EIO=3&transport=websocket"
    
    headers = {}
    
    if auth_mode == 'none':
        logger.info(f"Attempting WebSocket connection without authentication")
        print(f"\n🔌 Attempting WebSocket connection without authentication")
    
    elif auth_mode == 'cookies':
        logger.info(f"Attempting WebSocket connection with cookies only")
        print(f"\n🔌 Attempting WebSocket connection with cookies only")
        
        if auth_state['session_cookie']:
            cookie_str = f"session={auth_state['session_cookie']}"
            headers['Cookie'] = cookie_str
            logger.debug(f"Added cookie header: {cookie_str[:20]}...")
    
    elif auth_mode == 'headers':
        logger.info(f"Attempting WebSocket connection with auth headers only")
        print(f"\n🔌 Attempting WebSocket connection with auth headers only")
        
        if auth_state['csrf_token']:
            headers['X-CSRFToken'] = auth_state['csrf_token']
            logger.debug(f"Added CSRF token header")
        
        if auth_state['auth_token']:
            headers['Authorization'] = auth_state['auth_token']
            logger.debug(f"Added Authorization header")
    
    elif auth_mode == 'full':
        logger.info(f"Attempting WebSocket connection with full authentication")
        print(f"\n🔌 Attempting WebSocket connection with full authentication")
        
        # Add all available auth
        if auth_state['session_cookie']:
            cookie_str = f"session={auth_state['session_cookie']}"
            headers['Cookie'] = cookie_str
            logger.debug(f"Added cookie header: {cookie_str[:20]}...")
        
        if auth_state['csrf_token']:
            headers['X-CSRFToken'] = auth_state['csrf_token']
            logger.debug(f"Added CSRF token header")
        
        if auth_state['auth_token']:
            headers['Authorization'] = auth_state['auth_token']
            logger.debug(f"Added Authorization header")
    
    # Log headers for debugging
    logger.debug(f"WebSocket connection headers: {headers}")
    
    # Custom callback handlers
    def on_open(ws):
        logger.info(f"✅ WebSocket connection opened successfully")
        print(f"✅ WebSocket connection opened successfully")
        # Send a socket.io handshake
        ws.send("2probe")
    
    def on_message(ws, message):
        logger.info(f"Received message: {message[:50]}..." if len(message) > 50 else f"Received message: {message}")
        print(f"Received: {message[:50]}..." if len(message) > 50 else f"Received: {message}")
        
        # Handle socket.io handshake
        if message == "3probe":
            logger.info("Handshake successful, sending ping")
            ws.send("5")  # socket.io ping
        elif message == "2":
            logger.info("Received ping, sending pong")
            ws.send("3")  # socket.io pong
    
    def on_error(ws, error):
        logger.error(f"❌ WebSocket error: {error}")
        print(f"❌ WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        close_info = f" (Status: {close_status_code}, Message: {close_msg})" if close_status_code else ""
        logger.info(f"WebSocket connection closed{close_info}")
        print(f"WebSocket connection closed{close_info}")
    
    # Attempt connection
    try:
        ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        logger.info(f"Connecting to {ws_url}")
        print(f"Connecting to {ws_url}")
        
        # Start the WebSocket connection with a timeout
        ws_thread = ws.run_forever(ping_interval=10, ping_timeout=5)
        
        # Sleep briefly to allow the connection to establish
        time.sleep(5)
        
        # Close the connection
        ws.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        print(f"❌ Failed to connect: {e}")
        return False

def run_auth_debug():
    """Run the authentication debugging process"""
    print("=== Minerva WebSocket Authentication Debugger ===")
    print("This tool will help diagnose authentication issues with WebSocket connections")
    
    # Step 1: Test basic connectivity
    connectivity = test_basic_connectivity()
    
    # Step 2: Attempt login if credentials provided
    if args.username and args.password:
        login_successful = attempt_login()
    
    # Step 3: Check protected endpoints with our current auth state
    endpoint_results = check_protected_endpoints()
    
    # Step 4: Attempt WebSocket connections with different auth methods
    print("\n=== Testing WebSocket Connections with Different Auth Methods ===")
    
    # Without authentication
    attempt_websocket_connection('none')
    
    # With cookies only
    if auth_state['session_cookie']:
        attempt_websocket_connection('cookies')
    
    # With auth headers only
    if auth_state['csrf_token'] or auth_state['auth_token']:
        attempt_websocket_connection('headers')
    
    # With full authentication
    if auth_state['session_cookie'] or auth_state['csrf_token'] or auth_state['auth_token']:
        attempt_websocket_connection('full')
    
    # Print authentication summary
    print("\n=== Authentication Summary ===")
    print(f"Session Cookie: {'✅ Found' if auth_state['session_cookie'] else '❌ Not found'}")
    print(f"CSRF Token: {'✅ Found' if auth_state['csrf_token'] else '❌ Not found'}")
    print(f"Auth Token: {'✅ Found' if auth_state['auth_token'] else '❌ Not found'}")
    
    # Recommendations based on findings
    print("\n=== Recommendations ===")
    if not auth_state['session_cookie'] and not auth_state['csrf_token'] and not auth_state['auth_token']:
        print("❌ No authentication credentials were found.")
        print("   Try logging in with valid credentials using --username and --password")
    else:
        print("Based on the test results, try the following in your WebSocket client:")
        
        if auth_state['session_cookie']:
            print(f"1. Add the session cookie to your WebSocket headers:")
            print(f"   headers['Cookie'] = 'session={auth_state['session_cookie']}'")
        
        if auth_state['csrf_token']:
            print(f"2. Add the CSRF token to your WebSocket headers:")
            print(f"   headers['X-CSRFToken'] = '{auth_state['csrf_token']}'")
        
        if auth_state['auth_token']:
            print(f"3. Add the Authorization header to your WebSocket headers:")
            print(f"   headers['Authorization'] = '{auth_state['auth_token']}'")

if __name__ == "__main__":
    try:
        run_auth_debug()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ An unexpected error occurred: {e}")
