#!/usr/bin/env python3
"""
Minerva Authentication Tester

This script attempts multiple authentication methods to connect to Minerva's WebSocket server.
"""
import os
import sys
import json
import time
import requests
import logging
import socketio
import argparse
import getpass
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('minerva_auth')

class MinervaAuthTester:
    """Test various authentication methods with Minerva server"""
    
    def __init__(self, base_url="http://localhost:5000", debug=False):
        """Initialize the tester with base URL"""
        self.base_url = base_url
        self.session = requests.Session()
        self.cookies = {}
        self.headers = {}
        self.csrf_token = None
        
        # Socket.IO client setup
        self.sio = socketio.Client(
            logger=debug,
            engineio_logger=debug,
            reconnection=True,
            reconnection_attempts=3
        )
        
        # Configure logging level
        if debug:
            logger.setLevel(logging.DEBUG)
            
        logger.info(f"Initialized auth tester for {base_url}")
        
    def _parse_server_info(self):
        """Parse server URL to get host, port, and path"""
        parsed = urlparse(self.base_url)
        self.host = parsed.netloc.split(':')[0]
        self.port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        self.path = parsed.path or '/'
        
        logger.debug(f"Server info: host={self.host}, port={self.port}, path={self.path}")
    
    def test_server_connectivity(self):
        """Test basic connectivity to the server"""
        logger.info(f"Testing connectivity to {self.base_url}")
        
        try:
            resp = self.session.get(self.base_url, timeout=10)
            logger.info(f"Server response: Status={resp.status_code}, Length={len(resp.content)}")
            
            # Check for redirect to login page
            if resp.history:
                redirect_url = resp.url
                logger.info(f"Redirected to: {redirect_url}")
                
                if "login" in redirect_url.lower():
                    logger.info("✅ Detected login page redirect")
                    return "login_redirect", redirect_url
            
            # Check response status
            if resp.status_code == 200:
                return "success", resp.url
            elif resp.status_code == 401 or resp.status_code == 403:
                logger.info("⚠️ Authentication required")
                return "auth_required", resp.url
            else:
                logger.warning(f"Unexpected status code: {resp.status_code}")
                return "unexpected_status", resp.url
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection error - server may not be running")
            return "connection_error", None
        except Exception as e:
            logger.error(f"❌ Error during connectivity test: {e}")
            return "error", None
    
    def check_login_endpoint(self):
        """Check if the server has a login endpoint"""
        login_endpoints = [
            "/login", 
            "/auth", 
            "/signin", 
            "/api/login", 
            "/user/login"
        ]
        
        for endpoint in login_endpoints:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"Checking login endpoint: {url}")
            
            try:
                resp = self.session.get(url, timeout=5)
                logger.info(f"Response: Status={resp.status_code}, Length={len(resp.content)}")
                
                if resp.status_code == 200:
                    logger.info(f"✅ Found login endpoint: {endpoint}")
                    
                    # Check for CSRF token in response
                    html = resp.text
                    if "csrf" in html.lower():
                        import re
                        # Try to extract CSRF token
                        csrf_matches = re.findall(r'name="csrf[^"]*" value="([^"]+)"', html)
                        if csrf_matches:
                            self.csrf_token = csrf_matches[0]
                            logger.info(f"✅ Found CSRF token: {self.csrf_token[:10]}...")
                    
                    return True, endpoint
                    
            except Exception as e:
                logger.debug(f"Error checking {endpoint}: {e}")
                
        logger.info("❌ No standard login endpoint found")
        return False, None
    
    def try_login(self, username, password, endpoint=None):
        """Attempt to login with username and password"""
        if not endpoint:
            found, endpoint = self.check_login_endpoint()
            if not found:
                logger.warning("❌ Cannot try login: No login endpoint found")
                return False
                
        login_url = f"{self.base_url}{endpoint}"
        logger.info(f"Attempting login to {login_url}")
        
        # Prepare login data
        login_data = {
            "username": username,
            "password": password
        }
        
        # Add CSRF token if found
        if self.csrf_token:
            login_data["csrf_token"] = self.csrf_token
            
        # Try common field name variations
        variations = [
            {"username": username, "password": password},
            {"user": username, "pass": password},
            {"email": username, "password": password},
            {"login": username, "password": password}
        ]
        
        # Try each variation
        for data in variations:
            try:
                logger.info(f"Trying login with fields: {list(data.keys())}")
                resp = self.session.post(login_url, data=data, allow_redirects=True)
                
                logger.info(f"Login response: Status={resp.status_code}")
                
                # Check for successful login
                if resp.status_code == 200 or resp.status_code == 302:
                    # Save cookies from the session
                    self.cookies = self.session.cookies.get_dict()
                    logger.info(f"✅ Received cookies: {list(self.cookies.keys())}")
                    
                    # Check for auth tokens in response
                    try:
                        resp_data = resp.json()
                        if "token" in resp_data:
                            logger.info("✅ Found token in response")
                            self.headers["Authorization"] = f"Bearer {resp_data['token']}"
                    except:
                        pass
                        
                    # Test if authentication was successful
                    if self.test_authenticated_request():
                        logger.info("✅ Login successful!")
                        return True
                    
            except Exception as e:
                logger.error(f"Error during login attempt: {e}")
                
        logger.warning("❌ All login attempts failed")
        return False
    
    def test_authenticated_request(self):
        """Test if we have successful authentication by accessing a protected resource"""
        test_endpoints = [
            "/api/user", 
            "/api/profile", 
            "/api/data", 
            "/dashboard"
        ]
        
        for endpoint in test_endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                resp = self.session.get(url, timeout=5)
                if resp.status_code == 200:
                    logger.info(f"✅ Successfully accessed {endpoint} - Authentication confirmed")
                    return True
            except:
                pass
                
        logger.warning("⚠️ Could not confirm successful authentication")
        return False
    
    def try_websocket_connection(self):
        """Attempt to connect to WebSocket/Socket.IO with current authentication"""
        logger.info(f"Attempting Socket.IO connection with authentication")
        
        # Register event handlers
        @self.sio.event
        def connect():
            logger.info("✅ Socket.IO connected successfully!")
            
        @self.sio.event
        def connect_error(error):
            logger.error(f"❌ Socket.IO connection error: {error}")
            
        # Prepare headers and cookies
        headers = self.headers.copy()
        
        # Include cookies in request
        if self.cookies:
            cookies_str = "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
            headers["Cookie"] = cookies_str
        
        # Try to connect with auth cookies and headers    
        try:
            self.sio.connect(
                self.base_url,
                headers=headers,
                transports=["polling", "websocket"],
                wait=True,
                wait_timeout=10
            )
            
            time.sleep(1)  # Wait a moment to ensure connection is established
            
            if self.sio.connected:
                logger.info("✅ Successfully connected to Socket.IO server!")
                return True
            else:
                logger.warning("❌ Socket.IO connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error during Socket.IO connection: {e}")
            return False
        finally:
            if self.sio.connected:
                self.sio.disconnect()
    
    def try_api_key_authentication(self, api_key):
        """Test if API key authentication works"""
        if not api_key:
            logger.warning("No API key provided to test")
            return False
            
        logger.info("Testing API key authentication")
        
        # Test common API key header formats
        api_key_headers = [
            {"Authorization": f"Bearer {api_key}"},
            {"Authorization": f"Token {api_key}"},
            {"X-API-Key": api_key},
            {"API-Key": api_key},
            {"X-Auth-Token": api_key}
        ]
        
        for headers in api_key_headers:
            logger.info(f"Trying API key with header: {list(headers.keys())[0]}")
            
            try:
                resp = requests.get(self.base_url, headers=headers)
                
                if resp.status_code == 200:
                    logger.info(f"✅ API key authentication successful with {list(headers.keys())[0]}")
                    self.headers.update(headers)
                    return True
                    
            except Exception as e:
                logger.debug(f"Error during API key test: {e}")
                
        logger.warning("❌ API key authentication failed")
        return False
    
    def run_all_tests(self, username=None, password=None, api_key=None):
        """Run all authentication tests"""
        print("\n" + "=" * 60)
        print("🔐 MINERVA AUTHENTICATION TESTER")
        print("=" * 60)
        
        # Step 1: Test basic server connectivity
        print("\n[Step 1/5] Testing server connectivity...")
        result, url = self.test_server_connectivity()
        
        if result == "connection_error":
            print("❌ Cannot connect to server - please check if it's running")
            return False
            
        # Step 2: Check for login endpoint
        print("\n[Step 2/5] Checking for login endpoint...")
        has_login, endpoint = self.check_login_endpoint()
        
        # Step 3: Try username/password login if credentials provided
        print("\n[Step 3/5] Testing username/password authentication...")
        if username and password:
            if self.try_login(username, password, endpoint if has_login else None):
                print("✅ Username/password authentication successful!")
            else:
                print("❌ Username/password authentication failed")
        else:
            print("⚠️ Skipping username/password test (no credentials provided)")
            
        # Step 4: Try API key authentication if provided
        print("\n[Step 4/5] Testing API key authentication...")
        if api_key:
            if self.try_api_key_authentication(api_key):
                print("✅ API key authentication successful!")
            else:
                print("❌ API key authentication failed")
        else:
            print("⚠️ Skipping API key test (no API key provided)")
            
        # Step 5: Test WebSocket connection with authentication
        print("\n[Step 5/5] Testing authenticated WebSocket connection...")
        if self.try_websocket_connection():
            print("✅ WebSocket connection successful!")
            return True
        else:
            print("❌ WebSocket connection failed")
            return False

def main():
    parser = argparse.ArgumentParser(description="Minerva Authentication Tester")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL of Minerva server")
    parser.add_argument("--username", help="Username for login attempt")
    parser.add_argument("--password", help="Password for login attempt")
    parser.add_argument("--api-key", help="API key to test")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # If username is provided but not password, prompt for it
    if args.username and not args.password:
        args.password = getpass.getpass("Enter password: ")
        
    # Create and run the tester
    tester = MinervaAuthTester(args.url, args.debug)
    result = tester.run_all_tests(args.username, args.password, args.api_key)
    
    # Show summary
    print("\n" + "=" * 60)
    print("📊 AUTHENTICATION TEST SUMMARY")
    print("=" * 60)
    
    if result:
        print("\n✅ Successfully authenticated with Minerva!")
        print("\nRecommended next steps:")
        print("  1. Use the obtained authentication credentials with your WebSocket client")
        print("  2. Implement the authentication method in your application")
    else:
        print("\n❌ Authentication with Minerva was unsuccessful")
        print("\nRecommended next steps:")
        print("  1. Check server logs for authentication requirements")
        print("  2. Verify credentials are correct")
        print("  3. Try accessing the web interface directly to understand the auth flow")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
