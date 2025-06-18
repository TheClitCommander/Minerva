#!/usr/bin/env python3
"""
Minerva Authentication Credentials Capture Utility

This tool helps capture and analyze authentication credentials used by Minerva
to establish WebSocket connections. It can detect cookies, headers, and tokens
by monitoring successful connections to help diagnose authentication issues.
"""

import os
import sys
import json
import time
import argparse
import logging
import requests
from http.cookies import SimpleCookie
from urllib.parse import urlparse

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auth_capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auth_capture')

def capture_cookies(url, save_to_file=True):
    """Capture cookies from a successful web request to Minerva"""
    print(f"\n🔍 Capturing cookies from {url}")
    logger.info(f"Attempting to capture cookies from {url}")
    
    try:
        # Create a session to maintain cookies
        session = requests.Session()
        
        # Make initial request to the main page
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()
        
        # Get cookies from the session
        cookies = session.cookies.get_dict()
        
        if cookies:
            print(f"✅ Captured {len(cookies)} cookies:")
            for name, value in cookies.items():
                print(f"  🍪 {name}: {value[:10]}..." if len(value) > 10 else f"  🍪 {name}: {value}")
                
            # Save cookies to file
            if save_to_file:
                cookie_file = 'minerva_cookies.txt'
                with open(cookie_file, 'w') as f:
                    for name, value in cookies.items():
                        f.write(f"{name}={value}\n")
                print(f"✅ Saved cookies to {cookie_file}")
                
            return cookies
        else:
            print("⚠️ No cookies found in the response")
            return {}
            
    except Exception as e:
        logger.error(f"Error capturing cookies: {e}")
        print(f"❌ Error: {e}")
        return {}

def analyze_response_headers(url):
    """Analyze response headers to identify authentication mechanisms"""
    print(f"\n🔍 Analyzing response headers from {url}")
    logger.info(f"Analyzing response headers from {url}")
    
    try:
        # Make request to the server
        response = requests.get(url)
        response.raise_for_status()
        
        # Analyze headers
        headers = response.headers
        auth_headers = {}
        
        # Look for authentication-related headers
        auth_related = ['Authorization', 'X-Auth', 'Token', 'Bearer', 'Api-Key', 
                        'X-API-Key', 'X-Auth-Token', 'X-CSRF-Token', 'X-XSRF-Token']
        
        print("📋 Response Headers:")
        for name, value in headers.items():
            # Mask potential sensitive values in the log
            masked_value = value
            if any(auth_name.lower() in name.lower() for auth_name in auth_related):
                masked_value = value[:5] + "..." if len(value) > 5 else value
                auth_headers[name] = value
                
            print(f"  📄 {name}: {masked_value}")
        
        # Check for cookies in response
        if 'Set-Cookie' in headers:
            print("\n🍪 Cookies found in response:")
            cookie = SimpleCookie()
            cookie.load(headers['Set-Cookie'])
            for key, morsel in cookie.items():
                print(f"  {key}: {morsel.value}")
        
        # Check for WWW-Authenticate header
        if 'WWW-Authenticate' in headers:
            print(f"\n🔐 Authentication scheme: {headers['WWW-Authenticate']}")
            
        return headers
        
    except Exception as e:
        logger.error(f"Error analyzing headers: {e}")
        print(f"❌ Error: {e}")
        return {}

def check_csrf_protection(url):
    """Check if CSRF protection is enabled"""
    print(f"\n🔍 Checking for CSRF protection on {url}")
    logger.info(f"Checking for CSRF protection on {url}")
    
    try:
        # Make request to the server
        session = requests.Session()
        response = session.get(url)
        response.raise_for_status()
        
        # Look for CSRF tokens in the page content
        csrf_present = False
        page_content = response.text.lower()
        
        csrf_indicators = [
            'csrf', 'xsrf', '_token', 'authenticity_token',
            'anti-forgery', 'request-verification-token'
        ]
        
        for indicator in csrf_indicators:
            if indicator in page_content:
                csrf_present = True
                print(f"✅ CSRF protection detected: Found '{indicator}' in page content")
                logger.info(f"CSRF protection detected: Found '{indicator}' in page content")
        
        # Check headers for CSRF tokens
        headers = response.headers
        for name in headers:
            if any(indicator.lower() in name.lower() for indicator in csrf_indicators):
                csrf_present = True
                print(f"✅ CSRF protection detected: Found header '{name}'")
                logger.info(f"CSRF protection detected: Found header '{name}'")
        
        if not csrf_present:
            print("ℹ️ No explicit CSRF protection detected")
            logger.info("No explicit CSRF protection detected")
            
        return csrf_present
    
    except Exception as e:
        logger.error(f"Error checking CSRF protection: {e}")
        print(f"❌ Error: {e}")
        return False

def generate_auth_config(url, include_cookies=True, include_headers=True, include_csrf=True):
    """Generate auth configuration based on captured credentials"""
    print(f"\n🔧 Generating authentication configuration for {url}")
    logger.info(f"Generating authentication configuration for {url}")
    
    auth_config = {
        "url": url,
        "websocket_url": f"ws://{urlparse(url).netloc}/socket.io/?EIO=3&transport=websocket",
        "auth_method": "auto",
        "credentials": {}
    }
    
    # Capture cookies if requested
    if include_cookies:
        cookies = capture_cookies(url, save_to_file=True)
        if cookies:
            auth_config["credentials"]["cookies"] = cookies
            auth_config["auth_method"] = "cookie"
    
    # Analyze headers if requested
    if include_headers:
        headers = analyze_response_headers(url)
        auth_headers = {}
        
        # Extract authentication-related headers
        auth_related = ['Authorization', 'X-Auth', 'Token', 'Bearer', 'Api-Key', 
                        'X-API-Key', 'X-Auth-Token']
        
        for name, value in headers.items():
            if any(auth_name.lower() in name.lower() for auth_name in auth_related):
                auth_headers[name] = value
        
        if auth_headers:
            auth_config["credentials"]["headers"] = auth_headers
            auth_config["auth_method"] = "header"
    
    # Check CSRF protection if requested
    if include_csrf:
        csrf_present = check_csrf_protection(url)
        auth_config["csrf_protection"] = csrf_present
    
    # Save configuration to file
    config_file = 'minerva_auth_config.json'
    with open(config_file, 'w') as f:
        json.dump(auth_config, f, indent=2)
    
    print(f"\n✅ Saved authentication configuration to {config_file}")
    logger.info(f"Saved authentication configuration to {config_file}")
    
    return auth_config

def test_auth_config(auth_config):
    """Test the authentication configuration with our WebSocket client"""
    print(f"\n🧪 Testing authentication configuration")
    logger.info(f"Testing authentication configuration")
    
    try:
        # Try to import our WebSocket client
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from minimal_websocket_fix import WebSocketClient, setup_logger
        
        # Setup test logger
        test_logger = setup_logger("auth_test", level=logging.INFO)
        
        # Create WebSocket client with the configuration
        ws_url = auth_config["websocket_url"]
        client = WebSocketClient(
            url=ws_url,
            timeout=30,
            auto_reconnect=True,
            fallback_to_polling=True
        )
        
        # Set authentication based on the configuration
        auth_method = auth_config["auth_method"]
        credentials = auth_config["credentials"]
        
        print(f"🔑 Using authentication method: {auth_method}")
        logger.info(f"Using authentication method: {auth_method}")
        
        if auth_method == "cookie" and "cookies" in credentials:
            auth_success = client.set_authentication(method="cookie", credentials=credentials["cookies"])
        elif auth_method == "header" and "headers" in credentials:
            auth_success = client.set_authentication(method="header", credentials=credentials["headers"])
        elif auth_method == "token" and "token" in credentials:
            auth_success = client.set_authentication(method="token", credentials={"token": credentials["token"]})
        else:
            auth_success = client.set_authentication(method="auto", credentials=credentials)
        
        if not auth_success:
            print("⚠️ Failed to set authentication credentials")
            logger.warning("Failed to set authentication credentials")
            return False
        
        # Try to connect
        print(f"🔌 Connecting to WebSocket server at {ws_url}")
        logger.info(f"Connecting to WebSocket server at {ws_url}")
        
        connected = client.connect(timeout=10)
        
        if connected:
            print("✅ Successfully connected to WebSocket server!")
            logger.info("Successfully connected to WebSocket server")
            
            # Close the connection
            client.close()
            return True
        else:
            print("❌ Failed to connect to WebSocket server")
            logger.error("Failed to connect to WebSocket server")
            
            if client.using_fallback:
                print("⚠️ Using HTTP polling fallback")
                logger.warning("Using HTTP polling fallback")
                
                # Test sending a message via fallback
                test_message = {
                    "message": "Test authentication with HTTP polling fallback",
                    "timestamp": time.time()
                }
                
                response_received = [False]
                
                def on_response(data):
                    print(f"✅ Received fallback response: {json.dumps(data)[:100]}...")
                    response_received[0] = True
                
                client.send("test", test_message, callback=on_response)
                
                # Wait for response
                timeout = 10
                for i in range(timeout):
                    if response_received[0]:
                        break
                    print(f"Waiting for response... ({i+1}/{timeout})")
                    time.sleep(1)
                
                if response_received[0]:
                    print("✅ Successfully received response via HTTP polling fallback")
                    logger.info("Successfully received response via HTTP polling fallback")
                    client.close()
                    return True
                else:
                    print("❌ Failed to receive response via HTTP polling fallback")
                    logger.error("Failed to receive response via HTTP polling fallback")
                    client.close()
                    return False
            
            return False
    
    except ImportError as e:
        logger.error(f"Error importing WebSocket client: {e}")
        print(f"❌ Error importing WebSocket client: {e}")
        print("  Make sure you have the minimal_websocket_fix.py file in the same directory")
        return False
    
    except Exception as e:
        logger.error(f"Error testing authentication: {e}")
        print(f"❌ Error testing authentication: {e}")
        return False

def main():
    """Main function to parse arguments and run the capture process"""
    parser = argparse.ArgumentParser(description="Capture and analyze Minerva authentication credentials")
    
    parser.add_argument("--url", type=str, default="http://localhost:5000",
                       help="URL of the Minerva server")
    parser.add_argument("--no-cookies", action="store_true",
                       help="Skip cookie capture")
    parser.add_argument("--no-headers", action="store_true",
                       help="Skip header analysis")
    parser.add_argument("--no-csrf", action="store_true",
                       help="Skip CSRF protection check")
    parser.add_argument("--test", action="store_true",
                       help="Test the authentication configuration with the WebSocket client")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🔑 MINERVA AUTHENTICATION CREDENTIALS CAPTURE UTILITY")
    print("=" * 60)
    
    print(f"\n🌐 Target URL: {args.url}")
    print(f"🔍 Capturing: {'Cookies' if not args.no_cookies else ''} {'Headers' if not args.no_headers else ''} {'CSRF' if not args.no_csrf else ''}")
    
    # Generate authentication configuration
    auth_config = generate_auth_config(
        args.url,
        include_cookies=not args.no_cookies,
        include_headers=not args.no_headers,
        include_csrf=not args.no_csrf
    )
    
    # Test the configuration if requested
    if args.test:
        test_auth_config(auth_config)
    
    print("\n" + "=" * 60)
    print("✅ CREDENTIAL CAPTURE COMPLETE")
    print("=" * 60)
    
    print("\nTo test these credentials with your WebSocket client, run:")
    print(f"python test_websocket_auth.py --method={auth_config['auth_method']} --cookie-file=minerva_cookies.txt --fallback --verbose")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
