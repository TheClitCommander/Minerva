#!/usr/bin/env python3
"""
Minerva Connection Tester

This script systematically tests different authentication methods and connection
approaches to identify the correct way to authenticate with Minerva's WebSocket server.
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
import websocket
from urllib.parse import urlparse

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/connection_tester.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('connection_tester')

def check_server_availability(urls):
    """
    Check which server URLs are accessible
    
    Args:
        urls (list): List of URLs to check
        
    Returns:
        dict: Dictionary of URL status (True if available)
    """
    results = {}
    
    for url in urls:
        logger.info(f"Checking server availability: {url}")
        try:
            response = requests.get(url, timeout=5)
            results[url] = {
                'status_code': response.status_code,
                'available': response.status_code < 500,  # Consider 4xx as "available but unauthorized"
                'headers': dict(response.headers),
                'cookies': dict(response.cookies.get_dict())
            }
            logger.info(f"Server {url}: Status {response.status_code}")
        except Exception as e:
            logger.error(f"Server {url} error: {e}")
            results[url] = {
                'status_code': None, 
                'available': False,
                'error': str(e)
            }
    
    return results

def extract_csrf_token(html_content):
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

def test_login_endpoints(base_url, session=None):
    """
    Test various login endpoints to find authentication method
    
    Args:
        base_url (str): Base URL
        session (requests.Session): Session to use (optional)
        
    Returns:
        dict: Results of login endpoint tests
    """
    if session is None:
        session = requests.Session()
        
    endpoints = [
        "/login", 
        "/auth", 
        "/signin", 
        "/api/login", 
        "/api/auth",
        "/user/login",
        "/app/login",
        "/minerva/login"
    ]
    
    results = {}
    
    logger.info(f"Testing login endpoints at {base_url}")
    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}{endpoint}"
        try:
            response = session.get(url, timeout=5)
            status_code = response.status_code
            
            results[endpoint] = {
                'status_code': status_code,
                'accessible': status_code < 400,
                'cookies': dict(session.cookies.get_dict()),
                'headers': dict(response.headers)
            }
            
            # Check for login form
            if status_code == 200:
                csrf_token = extract_csrf_token(response.text)
                results[endpoint]['csrf_token'] = csrf_token
                
                # Look for login form fields
                import re
                username_field = re.search(r'<input[^>]*name=[\'"]username[\'"]', response.text)
                password_field = re.search(r'<input[^>]*name=[\'"]password[\'"]', response.text)
                results[endpoint]['has_login_form'] = (username_field is not None) and (password_field is not None)
                
            logger.info(f"Endpoint {endpoint}: Status {status_code}")
            
        except Exception as e:
            logger.error(f"Error with {endpoint}: {e}")
            results[endpoint] = {'error': str(e), 'accessible': False}
    
    return results

def test_basic_websocket(url, headers=None):
    """
    Test basic WebSocket connection
    
    Args:
        url (str): WebSocket URL
        headers (dict): Headers to use
        
    Returns:
        bool: Whether connection was successful
    """
    logger.info(f"Testing basic WebSocket connection to {url}")
    logger.info(f"Using headers: {headers}")
    
    try:
        ws = websocket.create_connection(url, header=headers)
        logger.info("WebSocket connection established!")
        ws.close()
        return True
    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")
        return False

def test_socketio_connection(url, headers=None, eio_version=3):
    """
    Test Socket.IO connection
    
    Args:
        url (str): Server URL
        headers (dict): Headers to use
        eio_version (int): Engine.IO version (3 or 4)
        
    Returns:
        bool: Whether connection was successful
    """
    logger.info(f"Testing Socket.IO connection to {url} with EIO v{eio_version}")
    
    sio = socketio.Client(logger=True, engineio_logger=True)
    connected = False
    
    @sio.event
    def connect():
        nonlocal connected
        connected = True
        logger.info("Socket.IO connected!")
    
    @sio.event
    def connect_error(data):
        logger.error(f"Socket.IO connection error: {data}")
    
    try:
        # Set EIO version
        kwargs = {}
        if eio_version:
            kwargs['eio_version'] = eio_version
            
        # Connect with headers if provided
        if headers:
            sio.connect(url, headers=headers, wait_timeout=5, **kwargs)
        else:
            sio.connect(url, wait_timeout=5, **kwargs)
            
        # Wait for connection or timeout
        time.sleep(2)
        
        # Clean up
        if connected:
            sio.disconnect()
            
        return connected
    except Exception as e:
        logger.error(f"Socket.IO connection error: {e}")
        return False

def test_multiple_auth_methods(base_url):
    """
    Test multiple authentication methods against Minerva
    
    Args:
        base_url (str): Base HTTP URL
        
    Returns:
        dict: Results of authentication tests
    """
    results = {"base_url": base_url, "tests": {}}
    session = requests.Session()
    
    # 1. Check server availability
    server_urls = [
        base_url,
        f"{base_url}/socket.io/",
        f"{base_url}/api/"
    ]
    results["server_availability"] = check_server_availability(server_urls)
    
    if not results["server_availability"][base_url]["available"]:
        logger.error(f"Server {base_url} is not available")
        return results
    
    # 2. Test login endpoints
    results["login_endpoints"] = test_login_endpoints(base_url, session)
    
    # 3. Generate session ID and transaction ID
    session_id = f"minerva_session_{uuid.uuid4().hex[:8]}"
    transaction_id = f"tx_{int(time.time())}"
    results["session_id"] = session_id
    results["transaction_id"] = transaction_id
    
    # 4. Test different WebSocket authentication methods
    ws_tests = {}
    
    # 4.1 Test basic WebSocket without auth
    ws_url = f"ws://{urlparse(base_url).netloc}/socket.io/?EIO=3&transport=websocket"
    ws_tests["basic_no_auth"] = {
        "url": ws_url,
        "success": test_basic_websocket(ws_url)
    }
    
    # 4.2 Test basic WebSocket with session cookies
    cookies = "; ".join([f"{k}={v}" for k, v in session.cookies.items()])
    if cookies:
        ws_tests["basic_with_cookies"] = {
            "url": ws_url,
            "headers": {"Cookie": cookies},
            "success": test_basic_websocket(ws_url, headers={"Cookie": cookies})
        }
    
    # 4.3 Test basic WebSocket with Minerva headers
    minerva_headers = {
        "X-Minerva-Session-ID": session_id,
        "X-Minerva-Client-Type": "websocket",
        "X-Minerva-Transaction-ID": transaction_id
    }
    ws_tests["basic_with_minerva_headers"] = {
        "url": ws_url,
        "headers": minerva_headers,
        "success": test_basic_websocket(ws_url, headers=minerva_headers)
    }
    
    # 4.4 Test Socket.IO with EIO v3
    socketio_tests = {}
    socketio_tests["socketio_v3_no_auth"] = {
        "url": base_url,
        "eio": 3,
        "success": test_socketio_connection(base_url, eio_version=3)
    }
    
    # 4.5 Test Socket.IO with EIO v4
    socketio_tests["socketio_v4_no_auth"] = {
        "url": base_url,
        "eio": 4,
        "success": test_socketio_connection(base_url, eio_version=4)
    }
    
    # 4.6 Test Socket.IO with Minerva headers
    socketio_tests["socketio_v3_with_minerva_headers"] = {
        "url": base_url,
        "eio": 3,
        "headers": minerva_headers,
        "success": test_socketio_connection(base_url, headers=minerva_headers, eio_version=3)
    }
    
    # 4.7 Test Socket.IO with EIO v4 and Minerva headers
    socketio_tests["socketio_v4_with_minerva_headers"] = {
        "url": base_url,
        "eio": 4,
        "headers": minerva_headers,
        "success": test_socketio_connection(base_url, headers=minerva_headers, eio_version=4)
    }
    
    results["tests"]["websocket"] = ws_tests
    results["tests"]["socketio"] = socketio_tests
    
    # Count successful tests
    ws_success_count = sum(1 for test in ws_tests.values() if test.get("success", False))
    socketio_success_count = sum(1 for test in socketio_tests.values() if test.get("success", False))
    
    results["summary"] = {
        "websocket_success_count": ws_success_count,
        "socketio_success_count": socketio_success_count,
        "any_successful": ws_success_count > 0 or socketio_success_count > 0
    }
    
    return results

def print_results_summary(results):
    """
    Print a summary of test results
    
    Args:
        results (dict): Test results
    """
    print("\n----- MINERVA CONNECTION TEST SUMMARY -----")
    print(f"Base URL: {results['base_url']}")
    
    # Server availability
    print("\n📡 Server Availability:")
    for url, status in results["server_availability"].items():
        status_msg = "✅ Available" if status["available"] else "❌ Not available"
        status_code = f"(Status: {status['status_code']})" if status["status_code"] else ""
        print(f"  {url}: {status_msg} {status_code}")
    
    # Login endpoints
    print("\n🔑 Login Endpoints:")
    login_found = False
    for endpoint, status in results["login_endpoints"].items():
        if status.get("accessible", False):
            login_found = True
            has_form = status.get("has_login_form", False)
            has_csrf = status.get("csrf_token") is not None
            form_status = "with login form" if has_form else "without login form"
            csrf_status = "with CSRF token" if has_csrf else "without CSRF token"
            print(f"  ✅ {endpoint}: Accessible {form_status}, {csrf_status}")
        else:
            error = status.get("error", f"Status: {status.get('status_code')}")
            print(f"  ❌ {endpoint}: Not accessible ({error})")
            
    if not login_found:
        print("  ⚠️ No accessible login endpoints found!")
    
    # WebSocket tests
    print("\n🔌 WebSocket Connection Tests:")
    ws_success = False
    for name, test in results["tests"]["websocket"].items():
        status = "✅ Success" if test["success"] else "❌ Failed"
        headers = test.get("headers", "None")
        header_summary = f"with headers: {headers}" if headers else "without auth"
        print(f"  {name}: {status} ({header_summary})")
        if test["success"]:
            ws_success = True
            
    if not ws_success:
        print("  ⚠️ All WebSocket connection tests failed!")
    
    # Socket.IO tests
    print("\n🔄 Socket.IO Connection Tests:")
    socketio_success = False
    for name, test in results["tests"]["socketio"].items():
        status = "✅ Success" if test["success"] else "❌ Failed"
        eio = f"EIO v{test['eio']}"
        headers = test.get("headers", "None")
        header_summary = f"with headers: {headers}" if headers else "without auth"
        print(f"  {name}: {status} ({eio}, {header_summary})")
        if test["success"]:
            socketio_success = True
            
    if not socketio_success:
        print("  ⚠️ All Socket.IO connection tests failed!")
    
    # Overall summary
    print("\n📋 Overall Summary:")
    if results["summary"]["any_successful"]:
        print("  ✅ Successfully found working connection methods!")
        print(f"  WebSocket successful tests: {results['summary']['websocket_success_count']}")
        print(f"  Socket.IO successful tests: {results['summary']['socketio_success_count']}")
    else:
        print("  ❌ All connection tests failed!")
        print("  - Check if the Minerva server is running and accessible")
        print("  - Verify authentication requirements")
        print("  - Check if WebSocket/Socket.IO is enabled on the server")

def main():
    """Main function"""
    print("🧪 Minerva Connection Tester 🧪")
    print("==============================")
    
    # Configuration
    base_urls = [
        "http://localhost:5000",
        "http://localhost:5050",
        "http://localhost:9876"
    ]
    
    # Check environment variables for credentials
    if os.environ.get("MINERVA_URL"):
        base_urls.insert(0, os.environ.get("MINERVA_URL"))
    
    # Allow command-line override
    if len(sys.argv) > 1:
        base_urls.insert(0, sys.argv[1])
    
    print(f"Testing the following server URLs: {', '.join(base_urls)}")
    
    # Test each base URL
    successful_results = None
    
    for base_url in base_urls:
        print(f"\nTesting {base_url}...")
        
        # Run tests for this URL
        results = test_multiple_auth_methods(base_url)
        
        # Save results to file
        filename = f"minerva_connection_results_{urlparse(base_url).netloc.replace(':', '_')}.json"
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print_results_summary(results)
        
        # If any tests were successful, remember these results
        if results["summary"]["any_successful"]:
            successful_results = results
            print(f"\n✅ Successfully connected to {base_url}!")
            print(f"Detailed results saved to {filename}")
            break
    
    if successful_results:
        # Output the optimal connection method
        print("\n🚀 RECOMMENDED CONNECTION METHOD:")
        
        if successful_results["summary"]["socketio_success_count"] > 0:
            # Find the first successful Socket.IO test
            for name, test in successful_results["tests"]["socketio"].items():
                if test["success"]:
                    eio = test["eio"]
                    headers = test.get("headers", {})
                    print(f"Use Socket.IO with EIO v{eio} and these headers:")
                    for k, v in headers.items():
                        print(f"  {k}: {v}")
                    break
        elif successful_results["summary"]["websocket_success_count"] > 0:
            # Find the first successful WebSocket test
            for name, test in successful_results["tests"]["websocket"].items():
                if test["success"]:
                    headers = test.get("headers", {})
                    print(f"Use WebSocket with these headers:")
                    for k, v in headers.items():
                        print(f"  {k}: {v}")
                    break
    else:
        print("\n❌ Could not establish connection to any Minerva server!")
        print("Try checking server logs for more information about authentication requirements.")

if __name__ == "__main__":
    main()
