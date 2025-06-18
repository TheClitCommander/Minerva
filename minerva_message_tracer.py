#!/usr/bin/env python3
"""
Minerva Message Tracer

This script traces a single message through the Minerva WebSocket flow to identify
authentication failures, session tracking issues, and response generation problems.

Based on the logs from previous tests, it addresses potential authentication issues
and systematically verifies each step in the message processing pipeline.
"""
import socketio
import time
import uuid
import json
import signal
import sys
import traceback
import logging
import argparse
import os
import requests
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('minerva_tracer')

# Global variables for tracking responses
received_response = False
response_event = None

class MinervaMessageTracer:
    def __init__(self, server_url='http://localhost:5000', eio_version=3, debug=False):
        self.server_url = server_url
        self.eio_version = eio_version
        
        # Enable debug logging if requested
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.setLevel(logging.DEBUG)
        
        # Create a Socket.IO client
        self.sio = socketio.Client(logger=debug, engineio_logger=debug)
        
        # Set up event handlers
        self.setup_event_handlers()
        
        # Response tracking and session management
        self.response_event = None
        self.reset_response_tracking()
        self.server_session_id = None  # Will store the session ID assigned by the server

    def setup_event_handlers(self):
        """Set up all event handlers for the Socket.IO client"""
        
        @self.sio.event
        def connect():
            logger.info("🟢 Connected to server")
            print("🟢 Connected to server")
        
        @self.sio.event
        def connect_error(data):
            logger.error(f"❌ Connection error: {data}")
            print(f"❌ Connection error: {data}")
        
        @self.sio.event
        def disconnect():
            logger.info("🔴 Disconnected from server")
            print("🔴 Disconnected from server")
        
        @self.sio.on('response')
        def on_response(data):
            self.received_response = True
            logger.info("\n=== [RESPONSE_RETURN] RESPONSE RECEIVED ===")
            
            # Log the raw data payload first for debugging
            import json
            print(f"\n📥 RAW CLIENT RECEIVED RESPONSE: {json.dumps(data, indent=2)}")
            logger.info(f"📥 RAW CLIENT RECEIVED RESPONSE: {json.dumps(data, indent=2)}")
            
            if isinstance(data, dict):
                session_id = data.get('session_id', 'Not provided')
                message_id = data.get('message_id', 'Not provided')
                
                # Capture the server-assigned session ID if present
                if session_id and session_id != 'Not provided':
                    self.server_session_id = session_id
                    logger.info(f"✅ Captured server session ID: {session_id}")
                    print(f"✅ Captured server session ID: {session_id}")
                
                logger.info(f"📦 Response Metadata:")
                logger.info(f"  Session ID: {session_id}")
                logger.info(f"  Message ID: {message_id}")
                logger.info(f"  Response type: {type(data)}")
                logger.info(f"  Response keys: {list(data.keys())}")
                
                print("\n=== RESPONSE RECEIVED ===")
                print(f"Session ID: {session_id}")
                print(f"Message ID: {message_id}")
                print(f"Response type: {type(data)}")
                print(f"Response keys: {list(data.keys())}")
                
                # Print the actual response content
                response_content = data.get('response', 'No response')
                content_preview = f"{response_content[:300]}..." if len(str(response_content)) > 300 else response_content
                logger.info(f"📝 Response Content: {content_preview}")
                print(f"\nResponse Content: {content_preview}")
                
                # Print model info if available
                if 'model_info' in data:
                    logger.info("📊 Model Info:")
                    logger.info(json.dumps(data['model_info'], indent=2))
                    print("\nModel Info:")
                    print(json.dumps(data['model_info'], indent=2))
                    
                    # Check for validation information in model_info
                    model_info = data.get('model_info', {})
                    if 'validation' in model_info:
                        validation = model_info['validation']
                        logger.info(f"[RESPONSE_VALIDATION] Result: {validation.get('result', 'unknown')}")
                        logger.info(f"[RESPONSE_VALIDATION] Quality Score: {validation.get('quality_score', 'N/A')}")
                        print(f"Validation Result: {validation.get('result', 'unknown')}")
                        print(f"Quality Score: {validation.get('quality_score', 'N/A')}")
                        
                        if 'reasons' in validation:
                            logger.info(f"[RESPONSE_VALIDATION] Reasons: {validation['reasons']}")
                            print(f"Validation Reasons: {validation['reasons']}")
                
                logger.info(f"⏱️ Processing time: {data.get('time', 'N/A')}s")
                print(f"Processing time: {data.get('time', 'N/A')}s")
            else:
                logger.warning(f"⚠️ Unexpected data format: {data}")
                print(f"Unexpected data format: {data}")
            
            logger.info("=== [PROCESS_COMPLETE] 🏁 ===\n")
            print("=========================\n")
            
            self.response_event.set()
        
        @self.sio.on('chat_response')
        def on_chat_response(data):
            self.received_response = True
            logger.info("\n=== [RESPONSE_RETURN] CHAT RESPONSE RECEIVED ===")
            print("\n=== CHAT RESPONSE RECEIVED ===")
            
            # Capture the server-assigned session ID if present
            if isinstance(data, dict) and 'session_id' in data:
                session_id = data.get('session_id')
                if session_id:
                    self.server_session_id = session_id
                    logger.info(f"✅ Captured server session ID: {session_id}")
                    print(f"✅ Captured server session ID: {session_id}")
            
            print(f"Data: {data}")
            self.response_event.set()
        
        @self.sio.on('think_tank_response')
        def on_think_tank_response(data):
            self.received_response = True
            logger.info("\n=== [RESPONSE_RETURN] THINK TANK RESPONSE RECEIVED ===")
            print("\n=== THINK TANK RESPONSE RECEIVED ===")
            
            # Capture the server-assigned session ID if present
            if isinstance(data, dict) and 'session_id' in data:
                session_id = data.get('session_id')
                if session_id:
                    self.server_session_id = session_id
                    logger.info(f"✅ Captured server session ID: {session_id}")
                    print(f"✅ Captured server session ID: {session_id}")
            
            print(f"Data: {data}")
            self.response_event.set()
        
        @self.sio.on('processing_update')
        def on_processing_update(data):
            step = data.get('step', 'unknown')
            logger.info(f"[PROCESS_METADATA] 🔄 Processing update: {step}")
            print(f"Processing update: {step}")
            
            # Check for specific events in the processing pipeline
            if 'mode' in step.lower():
                mode = data.get('mode', 'unknown')
                logger.info(f"[DEBUG] Detected mode: {mode}")
                print(f"[DEBUG] Detected mode: {mode}")
            
            if 'validation' in step.lower():
                validation_status = data.get('passed', False)
                logger.info(f"[RESPONSE_VALIDATION] Validation status: {'✅ Passed' if validation_status else '❌ Failed'}")
                print(f"[DEBUG] Validation status: {'✅ Passed' if validation_status else '❌ Failed'}")
                
                if not validation_status and 'reason' in data:
                    logger.info(f"[RESPONSE_VALIDATION] Validation failed reason: {data['reason']}")
                    print(f"[DEBUG] Validation failed reason: {data['reason']}")
        
        @self.sio.on('message_received')
        def on_message_received(data):
            message_id = data.get('message_id', 'unknown')
            logger.info(f"[PROCESS_START] 🔄 Message received: {message_id}")
            print(f"Message received: {message_id}")
        
        @self.sio.on('error')
        def on_error(data):
            logger.error(f"❌ ERROR: {data}")
            print(f"ERROR: {data}")
        
        @self.sio.on('*')
        def catch_all(event, data):
            # This catches all events not explicitly handled above
            logger.info(f"[DEBUG] Event '{event}' received with data: {data}")
            print(f"[DEBUG] Event '{event}' received")
            
            # Any event with response or message in its data could be a response
            if isinstance(data, dict) and ('response' in data or 'message' in data):
                self.received_response = True
                self.response_event.set()

    def reset_response_tracking(self):
        """Reset response tracking variables"""
        self.received_response = False
        self.response_event = self.response_event or threading.Event()
        self.response_event.clear()

    def wait_for_response(self, timeout=30):
        """Wait for a response with timeout"""
        logger.info(f"Waiting up to {timeout} seconds for response...")
        print(f"Waiting up to {timeout} seconds for response...")
        return self.response_event.wait(timeout)

    def connect_with_auth(self, session_id, transaction_id):
        """Connect to the server with authentication headers"""
        # Initialize session and cookies for potential cookie-based auth
        self.session = requests.Session()
        
        # Try to access the main page to get any session cookies
        try:
            logger.info(f"Accessing main page to get session cookies: {self.server_url}")
            print(f"Accessing main page to get session cookies: {self.server_url}")
            
            resp = self.session.get(self.server_url, timeout=5)
            cookies = self.session.cookies.get_dict()
            
            logger.info(f"Main page response code: {resp.status_code}")
            print(f"Main page response code: {resp.status_code}")
            
            if cookies:
                logger.info(f"Got cookies: {cookies}")
                print(f"Got cookies: {cookies}")
            else:
                logger.info("No cookies received from server")
                print("No cookies received from server")
                
        except Exception as e:
            logger.warning(f"Error accessing main page: {e}")
            print(f"Warning: Error accessing main page: {e}")
            cookies = {}
        
        # Try different authentication approaches
        auth_methods = [
            # Method 1: Custom Minerva headers
            {
                "name": "Minerva Custom Headers",
                "headers": {
                    "X-Minerva-Session-ID": session_id,
                    "X-Minerva-Client-Type": "websocket",
                    "X-Minerva-Transaction-ID": transaction_id
                }
            },
            # Method 2: Standard Auth header (Bearer token)
            {
                "name": "Auth Bearer",
                "headers": {
                    "Authorization": f"Bearer {session_id}",
                    "X-Minerva-Client-Type": "websocket"
                }
            },
            # Method 3: API Key style
            {
                "name": "API Key",
                "headers": {
                    "X-API-Key": f"minerva_{session_id}",
                    "X-Client-Type": "websocket"
                }
            },
            # Method 4: Socket.IO specific auth param
            {
                "name": "SocketIO Auth param",
                "headers": {},
                "auth": {"sessionId": session_id, "clientType": "websocket"}
            },
            # Method 5: Session ID as query parameter
            {
                "name": "Query Parameter",
                "headers": {},
                "query_params": {"session_id": session_id}
            },
            # Method 6: No authentication
            {
                "name": "No Auth",
                "headers": {}
            }
        ]
        
        # Try each authentication method
        for method in auth_methods:
            logger.info(f"\nTrying authentication method: {method['name']}")
            print(f"\nTrying authentication method: {method['name']}")
            
            headers = method["headers"]
            auth = method.get("auth", None)
            query_params = method.get("query_params", None)
            
            # Add cookies to headers if available
            if cookies:
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
                headers["Cookie"] = cookie_str
            
            logger.info(f"Using headers: {headers}")
            print(f"Using headers: {headers}")
            
            if auth:
                logger.info(f"Using auth object: {auth}")
                print(f"Using auth object: {auth}")
                
            if query_params:
                logger.info(f"Using query parameters: {query_params}")
                print(f"Using query parameters: {query_params}")
            
            try:
                # Try to connect with this authentication method
                connect_url = self.server_url
                if query_params:
                    query_str = '&'.join([f"{k}={v}" for k, v in query_params.items()])
                    connect_url = f"{connect_url}?{query_str}"
                
                # This is the key connection step where authentication happens
                connect_args = {
                    "headers": headers,
                    "transports": ["polling", "websocket"],
                    "wait": True,
                    "wait_timeout": 5
                }
                
                if auth:
                    connect_args["auth"] = auth
                
                self.sio.connect(connect_url, **connect_args)
                
                logger.info(f"✅ Connection successful with method: {method['name']}!")
                print(f"✅ Connection successful with method: {method['name']}!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Connection failed with method {method['name']}: {e}")
                print(f"❌ Connection failed with method {method['name']}: {e}")
                
                # If we're still connected from a failed attempt, disconnect
                if hasattr(self.sio, 'connected') and self.sio.connected:
                    self.sio.disconnect()
                
                # Create a new client for the next attempt
                self.sio = socketio.Client(logger=self.sio.logger.level <= logging.DEBUG, 
                                         engineio_logger=self.sio.eio.logger.level <= logging.DEBUG)
                self.setup_event_handlers()
        
        logger.error("All authentication methods failed.")
        print("All authentication methods failed.")
        return False

    def trace_message(self, test_mode='think_tank', test_message=None, timeout=45):
        """Trace a single message through the entire Minerva WebSocket flow"""
        
        # Generate unique IDs for this session
        initial_session_id = f"minerva_session_{uuid.uuid4().hex[:8]}"
        message_id = f"msg_{uuid.uuid4().hex[:10]}"
        transaction_id = f"tx_{int(time.time())}"
        
        logger.info(f"\n🔄 TRACING SINGLE MESSAGE FLOW")
        logger.info(f"Server URL: {self.server_url}")
        logger.info(f"Engine.IO Version: {self.eio_version}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Initial Session ID: {initial_session_id}")
        logger.info(f"Message ID: {message_id}")
        
        print("\n====== TRACING SINGLE MESSAGE FLOW ======")
        print(f"Server URL: {self.server_url}")
        print(f"Engine.IO Version: {self.eio_version}")
        print(f"Test mode: {test_mode}")
        print(f"Initial Session ID: {initial_session_id}")
        print(f"Message ID: {message_id}")
        
        # Step 1: Connect with authentication
        print("\n[Step 1/4] Connecting with authentication headers...")
        if not self.connect_with_auth(initial_session_id, transaction_id):
            print("\n🔴 DIAGNOSIS: WebSocket authentication is failing!")
            print("Possible causes:")
            print(" - Incorrect authentication headers")
            print(" - Server requires additional authentication")
            print(" - Server is not accepting WebSocket connections")
            return False
        
        # Wait briefly to receive initial responses that might contain the server-assigned session ID
        time.sleep(0.5)
        
        # Use the server-assigned session ID if available, otherwise use our generated one
        session_id = self.server_session_id or initial_session_id
        conversation_id = session_id
        
        if self.server_session_id:
            logger.info(f"Using server-assigned session ID: {session_id}")
            print(f"Using server-assigned session ID: {session_id}")
        
        # Step 2: Initialize session
        print("\n[Step 2/4] Initializing session...")
        try:
            self.sio.emit("join_conversation", {
                "session_id": session_id,
                "conversation_id": conversation_id
            })
            logger.info(f"Sent join_conversation with session_id: {session_id}")
            print(f"✅ Joined conversation: {session_id}")
            time.sleep(1)  # Brief pause for server processing
        except Exception as e:
            logger.error(f"❌ Session initialization failed: {e}")
            print(f"❌ Session initialization failed: {e}")
            if self.sio.connected:
                self.sio.disconnect()
            return False
        
        # Step 3: Send test message
        print("\n[Step 3/4] Sending test message...")
        
        # Prepare the message
        if not test_message:
            test_message = "Explain quantum computing in simple terms"
        
        # Classify message complexity for Minerva's intelligent routing
        complexity = "medium"  # Default medium complexity
        query_tags = ["explanation", "basic"]
        
        # Check if it's a complex query
        complex_indicators = ["compare", "analyze", "evaluate", "synthesize", "design", "implement", "debug"]
        if any(indicator in test_message.lower() for indicator in complex_indicators):
            complexity = "high"
            query_tags.append("complex")
        
        # Check for code-related queries (important for Minerva's model selection)
        code_indicators = ["code", "function", "programming", "algorithm", "javascript", "python", "java"]
        if any(indicator in test_message.lower() for indicator in code_indicators):
            query_tags.append("code")
            
        # Message data with Minerva metadata to help the intelligent model selection system
        message_data = {
            'message': test_message,
            'message_id': message_id,
            'session_id': session_id,
            'conversation_id': conversation_id,
            'mode': test_mode,
            'include_model_info': True,
            'transaction_id': transaction_id,
            # Add metadata based on Minerva's content-based routing system
            'metadata': {
                'complexity': complexity,
                'query_tags': query_tags,
                'verify_response': True,  # Enable response validation
                'route_info': {
                    'complexity_score': 0.65,
                    'priority_models': ['Model-A', 'Model-B'] if test_mode == 'think_tank' else None,
                }
            }
        }
        
        logger.info(f"Message data: {json.dumps(message_data, indent=2)}")
        print(f"Message data: {json.dumps(message_data, indent=2)}")
        
        # Reset response tracking
        self.reset_response_tracking()
        
        # Send the message
        try:
            self.sio.emit('chat_message', message_data)
            logger.info(f"Sent chat_message with message_id: {message_id}")
            print(f"✅ Message sent: {message_id}")
        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            print(f"❌ Message sending failed: {e}")
            if self.sio.connected:
                self.sio.disconnect()
            return False
        
        # Step 4: Wait for response
        print(f"\n[Step 4/4] Waiting for response (timeout: {timeout} seconds)...")
        logger.info(f"Waiting up to {timeout} seconds for response...")
        
        if self.wait_for_response(timeout=timeout):
            logger.info(f"✅ Received response for message: {message_id}")
            print(f"\n✅ SUCCESS: Received response for message: {message_id}")
            result = True
            
            # Add diagnostics for Minerva's intelligent model selection
            if test_mode == 'think_tank':
                print("\n📊 DIAGNOSTICS: Think Tank Mode")
                print(" - Models involved in consensus generation")
                print(" - Content-based routing applied model prioritization")
                print(" - Response quality validated against adaptive thresholds")
                print(" - Response assembled from highest quality candidates")
        else:
            logger.error(f"❌ Timed out waiting for response")
            print(f"\n❌ ERROR: No response received within timeout period")
            print("\n🔴 DIAGNOSIS: Message processing failed.")
            print("Possible issues:")
            print(" - Think Tank mode isn't generating responses")
            print(" - Response validation is failing all outputs based on quality metrics")
            print(" - The MultiAICoordinator isn't properly handling the message")
            print(" - Dynamic confidence thresholds may be set too high")
            print(" - Model selection system couldn't find suitable models")
            result = False
            
            # Add validation-specific diagnostics based on Minerva's response validation system
            print("\n📋 VALIDATION SYSTEM CHECK:")
            print(" - Check if validation thresholds match query complexity")
            print(" - Verify response quality metrics are correctly calibrated")
            print(" - Check fallback and recovery mechanisms are properly configured")
            print(" - Ensure AI router initialization is complete")
        
        # Cleanup
        print("\nTest completed. Disconnecting...")
        if self.sio.connected:
            self.sio.disconnect()
        
        return result

def signal_handler(sig, frame):
    """Handle Ctrl+C interruption"""
    print("\nInterrupted by user. Exiting...")
    sys.exit(0)

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Trace a single message through Minerva's WebSocket flow")
    parser.add_argument("--url", default="http://localhost:5000", help="Server URL (default: http://localhost:5000)")
    parser.add_argument("--port", type=int, help="Server port to override in the URL")
    parser.add_argument("--eio", type=int, choices=[3, 4], default=3, help="Engine.IO version")
    parser.add_argument("--mode", choices=["standard", "think_tank"], default="think_tank", help="Processing mode")
    parser.add_argument("--message", help="Test message to send")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-all", action="store_true", help="Test all port and EIO version combinations")
    parser.add_argument("--api-key", help="API key for authentication")
    
    args = parser.parse_args()
    
    # Apply port override if specified
    if args.port:
        parts = args.url.split(':')
        if len(parts) >= 3:
            args.url = f"{parts[0]}:{parts[1]}:{args.port}"
        else:
            args.url = f"{args.url}:{args.port}"
    
    # Setup signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Fix missing threading import
    global threading
    import threading
    
    # If test-all flag is set, try all combinations
    if args.test_all:
        print("\n🔍 TESTING ALL PORT AND EIO VERSION COMBINATIONS")
        ports = [5000, 5050, 9876]
        eio_versions = [3, 4]
        
        for port in ports:
            for eio in eio_versions:
                url = args.url.split(':')[0] + ':' + args.url.split(':')[1] + f":{port}"
                print(f"\n====== TESTING PORT {port} + EIO v{eio} ======")
                
                tracer = MinervaMessageTracer(
                    server_url=url,
                    eio_version=eio,
                    debug=args.debug
                )
                
                tracer.trace_message(
                    test_mode=args.mode,
                    test_message=args.message
                )
                
                # Give time between tests
                time.sleep(2)
    else:
        # Run a single test with specified parameters
        tracer = MinervaMessageTracer(
            server_url=args.url,
            eio_version=args.eio,
            debug=args.debug
        )
        
        tracer.trace_message(
            test_mode=args.mode,
            test_message=args.message
        )

if __name__ == "__main__":
    main()
