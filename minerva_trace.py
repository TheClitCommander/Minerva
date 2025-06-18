#!/usr/bin/env python3
"""
Minerva WebSocket Message Tracer

This script performs step-by-step tracing of a single message through the Minerva WebSocket flow
to precisely identify where authentication or processing failures occur.
"""
import socketio
import time
import uuid
import json
import threading
import signal
import sys
import traceback
import logging
import argparse
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
log_file = f"logs/minerva_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minerva_tracer')

# Global variables for tracking responses
received_responses = 0
response_event = threading.Event()

# Create a Socket.IO client with the specified EIO version
def create_socketio_client(eio_version=3):
    # For python-socketio, we need to use specific client configurations based on EIO version
    if eio_version == 3:
        return socketio.Client(logger=True, engineio_logger=True)
    elif eio_version == 4:
        return socketio.Client(logger=True, engineio_logger=True)
    else:
        raise ValueError(f"Unsupported EIO version: {eio_version}")

# Initialize with default version
sio = None

# Function to set up all event handlers
def setup_event_handlers(client):
    @client.event
    def connect():
        logger.info("🟢 [PROCESS_START] Connected to server")
        print("🟢 Connected to server")
    
    @client.event
    def connect_error(data):
        logger.error(f"❌ Connection error: {data}")
        print(f"❌ Connection error: {data}")
    
    @client.event
    def disconnect():
        logger.info("🔴 Disconnected from server")
        print("🔴 Disconnected from server")
    
    # Define response handlers
    @client.on('response')
    def on_response(data):
        global received_responses
        logger.info("\n=== [RESPONSE_RETURN] RESPONSE RECEIVED ===")
        
        if isinstance(data, dict):
            session_id = data.get('session_id', 'Not provided')
            message_id = data.get('message_id', 'Not provided')
            
            logger.info(f"📦 Response Metadata:")
            logger.info(f"  Session ID: {session_id}")
            logger.info(f"  Message ID: {message_id}")
            
            print("\n=== RESPONSE RECEIVED ===")
            print(f"Session ID: {session_id}")
            print(f"Message ID: {message_id}")
            
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
            
            logger.info(f"⏱️ Processing time: {data.get('time', 'N/A')}s")
            print(f"Processing time: {data.get('time', 'N/A')}s")
        else:
            logger.warning(f"⚠️ Unexpected data format: {data}")
            print(f"Unexpected data format: {data}")
        
        logger.info("=== [PROCESS_COMPLETE] 🏁 ===\n")
        print("=========================\n")
        
        received_responses += 1
        response_event.set()

@sio.on('chat_response')
def on_chat_response(data):
    global received_responses
    logger.info("\n=== [RESPONSE_RETURN] CHAT RESPONSE RECEIVED ===")
    print("\n=== CHAT RESPONSE RECEIVED ===")
    print(f"Data: {data}")
    received_responses += 1
    response_event.set()

@sio.on('think_tank_response')
def on_think_tank_response(data):
    global received_responses
    logger.info("\n=== [RESPONSE_RETURN] THINK TANK RESPONSE RECEIVED ===")
    print("\n=== THINK TANK RESPONSE RECEIVED ===")
    print(f"Data: {data}")
    received_responses += 1
    response_event.set()

@sio.on('processing_update')
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

@sio.on('message_received')
def on_message_received(data):
    message_id = data.get('message_id', 'unknown')
    logger.info(f"[PROCESS_START] 🔄 Message received: {message_id}")
    print(f"Message received: {message_id}")

@sio.on('error')
def on_error(data):
    error_message = data.get('message', 'Unknown error')
    logger.error(f"❌ ERROR: {error_message}")
    print(f"ERROR: {error_message}")

@sio.on('*')
def catch_all(event, data):
    # This catches all events not explicitly handled above
    logger.debug(f"[DEBUG] Event '{event}' received")
    print(f"[DEBUG] Event '{event}' received")
    
    # Any event with response or message in its data could be a response
    if isinstance(data, dict) and ('response' in data or 'message' in data):
        global received_responses
        received_responses += 1
        response_event.set()

def signal_handler(sig, frame):
    logger.info("Interrupted by user. Exiting...")
    print("Interrupted by user. Exiting...")
    if sio.connected:
        sio.disconnect()
    sys.exit(0)

def wait_for_response(timeout=45):
    """Wait for a response with timeout"""
    response_event.clear()
    logger.info(f"Waiting up to {timeout} seconds for response...")
    print(f"Waiting up to {timeout} seconds for response...")
    return response_event.wait(timeout)

def trace_single_message(server_url, port=None, eio_version=3, test_mode='think_tank', test_message=None):
    """
    Trace a single message through the Minerva WebSocket flow to identify failure points
    """
    global received_responses
    
    # Apply port override if specified
    if port:
        parts = server_url.split(':')
        if len(parts) >= 3:
            server_url = f"{parts[0]}:{parts[1]}:{port}"
        else:
            server_url = f"{server_url}:{port}"
    
    try:
        # Generate unique IDs for this session
        session_id = f"minerva_session_{uuid.uuid4().hex[:8]}"
        message_id = f"msg_{uuid.uuid4().hex[:10]}"
        transaction_id = f"tx_{int(time.time())}"
        
        logger.info(f"\n🔄 [PROCESS_START] TRACING SINGLE MESSAGE FLOW")
        logger.info(f"Server URL: {server_url}")
        logger.info(f"Engine.IO Version: {eio_version}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Message ID: {message_id}")
        logger.info(f"Transaction ID: {transaction_id}")
        
        print("\n====== TRACING SINGLE MESSAGE FLOW ======")
        print(f"Server URL: {server_url}")
        print(f"Engine.IO Version: {eio_version}")
        print(f"Test mode: {test_mode}")
        print(f"Session ID: {session_id}")
        print(f"Message ID: {message_id}")
        print(f"Transaction ID: {transaction_id}")
        
        # Step 1: Prepare Minerva-specific headers
        print(f"\n[Step 1/5] Preparing authentication headers")
        headers = {
            "X-Minerva-Session-ID": session_id,
            "X-Minerva-Client-Type": "websocket",
            "X-Minerva-Transaction-ID": transaction_id
        }
        
        logger.info(f"Using headers: {headers}")
        print(f"Using headers: {headers}")
        
        # Step 2: Connect to the server with the prepared headers
        print(f"\n[Step 2/5] Connecting to server: {server_url} with EIO v{eio_version}")
        
        try:
            # Create a Socket.IO client with the correct EIO version
            global sio
            sio = create_socketio_client(eio_version)
            
            # Set up all the event handlers
            setup_event_handlers(sio)
            
            # Connect with proper headers
            sio.connect(
                server_url,
                headers=headers,
                transports=["polling", "websocket"],
                wait=True,
                wait_timeout=5
            )
            logger.info("✅ Connection successful!")
            print("✅ Connection successful!")
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            print(f"❌ Connection failed: {e}")
            print("\n🔴 DIAGNOSIS: WebSocket authentication is still failing.")
            print("Possible solutions:")
            print(" - Verify the X-Minerva-* headers are correctly formatted")
            print(" - Try different EIO versions (--eio 3 or --eio 4)")
            print(" - Check server port (--port 5000, 5050, or 9876)")
            return False
        
        # Step 3: Initialize session by joining a conversation
        print(f"\n[Step 3/5] Initializing session: {session_id}")
        
        try:
            sio.emit("join_conversation", {"session_id": session_id, "conversation_id": session_id})
            logger.info(f"Emitted join_conversation with session_id: {session_id}")
            time.sleep(1)  # Brief pause for server processing
        except Exception as e:
            logger.error(f"❌ Session initialization failed: {e}")
            print(f"❌ Session initialization failed: {e}")
            if sio.connected:
                sio.disconnect()
            return False
        
        # Step 4: Send a test message with the appropriate mode
        print(f"\n[Step 4/5] Sending test message with mode: {test_mode}")
        
        # Prepare a test message
        if not test_message:
            test_message = "Explain quantum computing in simple terms"
            
        message_data = {
            'message': test_message,
            'message_id': message_id,
            'session_id': session_id,
            'conversation_id': session_id,
            'mode': test_mode,
            'include_model_info': True,
            'transaction_id': transaction_id
        }
        
        logger.info(f"Message data: {json.dumps(message_data, indent=2)}")
        print(f"Message data: {json.dumps(message_data, indent=2)}")
        
        # Reset response tracking
        received_responses = 0
        response_event.clear()
        
        # Send the message
        try:
            sio.emit('chat_message', message_data)
            logger.info(f"Emitted chat_message with message_id: {message_id}")
            print(f"✅ Message sent with ID: {message_id}")
        except Exception as e:
            logger.error(f"❌ Message sending failed: {e}")
            print(f"❌ Message sending failed: {e}")
            if sio.connected:
                sio.disconnect()
            return False
        
        # Step 5: Wait for and analyze the response
        print(f"\n[Step 5/5] Waiting for response (timeout: 45 seconds)...")
        
        if wait_for_response(timeout=45):
            logger.info(f"✅ [PROCESS_COMPLETE] Received response for message: {message_id}")
            print(f"\n✅ SUCCESS: Received response for message ID: {message_id}")
            result = True
        else:
            logger.error(f"❌ Timed out waiting for response to message: {message_id}")
            print(f"\n❌ ERROR: No response received within timeout period")
            print("\n🔴 DIAGNOSIS: Message processing failed.")
            print("Possible issues:")
            print(" - Think Tank mode isn't functioning properly")
            print(" - Response validation is failing all generated content")
            print(" - The AI coordinator isn't processing the message")
            result = False
        
        # Disconnect and return success status
        print("\nTest completed. Disconnecting...")
        if sio.connected:
            sio.disconnect()
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        if sio.connected:
            sio.disconnect()
        return False

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(description="Trace a single message through Minerva's WebSocket flow")
    parser.add_argument("--url", default="http://localhost:5000", help="Server URL (default: http://localhost:5000)")
    parser.add_argument("--port", type=int, help="Server port to try")
    parser.add_argument("--eio", type=int, choices=[3, 4], default=3, help="Engine.IO version (default: 3)")
    parser.add_argument("--mode", choices=["standard", "think_tank"], default="think_tank", help="Processing mode")
    parser.add_argument("--message", help="Test message to send")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-all", action="store_true", help="Test all port and EIO version combinations")
    
    args = parser.parse_args()
    
    # Set up debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Setup signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # If test-all flag is set, try all combinations
    if args.test_all:
        print("\n🔍 TESTING ALL PORT AND EIO VERSION COMBINATIONS")
        ports = [5000, 5050, 9876]
        eio_versions = [3, 4]
        
        for port in ports:
            for eio in eio_versions:
                print(f"\n====== TESTING PORT {port} + EIO v{eio} ======")
                trace_single_message(
                    server_url=args.url,
                    port=port,
                    eio_version=eio,
                    test_mode=args.mode,
                    test_message=args.message
                )
                # Give time between tests
                time.sleep(1)
    else:
        # Run the trace with specified settings
        trace_single_message(
            server_url=args.url,
            port=args.port,
            eio_version=args.eio,
            test_mode=args.mode,
            test_message=args.message
        )

if __name__ == "__main__":
    main()
