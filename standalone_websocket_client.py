#!/usr/bin/env python3
"""
Standalone WebSocket Client for Minerva Testing

This script creates a test client that connects to the standalone WebSocket server
and tests various scenarios to verify WebSocket reliability fixes.
"""
import os
import sys
import time
import json
import uuid
import logging
import threading
import argparse
import socketio
from datetime import datetime

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/standalone_client.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('standalone_client')

# Arguments
parser = argparse.ArgumentParser(description='WebSocket Client for Minerva Testing')
parser.add_argument('--url', type=str, default='http://localhost:5050', 
                    help='WebSocket server URL')
parser.add_argument('--mode', type=str, choices=['normal', 'timeout', 'think_tank', 'all'], 
                    default='all', help='Test mode')
parser.add_argument('--messages', type=int, default=1, 
                    help='Number of messages to send')
parser.add_argument('--parallel', type=int, default=1, 
                    help='Number of parallel messages')
args = parser.parse_args()

# Create a Socket.IO client
sio = socketio.Client(
    logger=True,
    engineio_logger=True,
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1,
    reconnection_delay_max=5
)

# Tracking variables
session_id = str(uuid.uuid4())
sent_messages = {}
received_responses = {}
message_count = 0
response_count = 0
response_event = threading.Event()
lock = threading.Lock()

# Connection events
@sio.event
def connect():
    logger.info("✅ Connected to server")
    print("✅ Connected to server")

@sio.event
def disconnect():
    logger.info("❌ Disconnected from server")
    print("❌ Disconnected from server")

@sio.event
def connect_error(error):
    logger.error(f"❌ Connection error: {error}")
    print(f"❌ Connection error: {error}")

# Response handler
@sio.on('response')
def on_response(data):
    global response_count
    
    try:
        if isinstance(data, dict):
            message_id = data.get('message_id', 'unknown')
            source = data.get('source', 'unknown')
            
            # Print a summary of the response
            print(f"\n==== RESPONSE RECEIVED ====")
            print(f"Message ID: {message_id}")
            print(f"Source: {source}")
            
            response_content = data.get('response', 'No response')
            if len(response_content) > 100:
                print(f"Response (preview): {response_content[:100]}...")
            else:
                print(f"Response: {response_content}")
            
            model_info = data.get('model_info', {})
            if model_info:
                print(f"Model Info: {json.dumps(model_info, indent=2)}")
            
            # Calculate response time if we sent this message
            with lock:
                if message_id in sent_messages:
                    sent_time = sent_messages[message_id]['timestamp']
                    elapsed = (datetime.now() - sent_time).total_seconds()
                    print(f"Response Time: {elapsed:.2f} seconds")
                    
                    # Record this response
                    received_responses[message_id] = {
                        'timestamp': datetime.now(),
                        'response': data,
                        'elapsed': elapsed
                    }
                    
                    # Update tracking metrics
                    response_count += 1
                    response_event.set()
                    
                    # Check if this was a timeout test
                    if sent_messages[message_id].get('mode') == 'test_timeout':
                        if 'timeout' in model_info and model_info['timeout']:
                            print("✅ Timeout correctly detected and handled")
                            logger.info(f"✅ Timeout correctly detected for {message_id}")
                        else:
                            print("⚠️ Expected timeout but got normal response")
                            logger.warning(f"⚠️ Expected timeout but got normal response for {message_id}")
                else:
                    # System message or other
                    print(f"➕ Received unsolicited response, possibly system message")
            
            print("=============================")
        else:
            print(f"Unexpected data format: {data}")
            logger.warning(f"Unexpected response format: {type(data)}")
    
    except Exception as e:
        logger.error(f"❌ Error processing response: {str(e)}")
        print(f"❌ Error processing response: {str(e)}")

def send_message(mode, message_text=None):
    """Send a test message with the specified mode"""
    global message_count
    
    message_id = str(uuid.uuid4())
    
    if message_text is None:
        message_text = f"Test message {message_count} in {mode} mode"
    
    try:
        # Create payload
        payload = {
            'message_id': message_id,
            'session_id': session_id,
            'message': message_text,
            'mode': mode
        }
        
        # Send the message
        sio.emit('chat_message', payload)
        
        # Track this message
        with lock:
            sent_messages[message_id] = {
                'timestamp': datetime.now(),
                'payload': payload,
                'mode': mode
            }
            message_count += 1
        
        logger.info(f"📤 Sent message {message_id} in {mode} mode")
        print(f"📤 Sent message: {message_text} (ID: {message_id}, Mode: {mode})")
        
        return message_id
    
    except Exception as e:
        logger.error(f"❌ Error sending message: {str(e)}")
        print(f"❌ Error sending message: {str(e)}")
        return None

def wait_for_responses(num_responses, timeout=60):
    """Wait for the expected number of responses"""
    start_time = time.time()
    
    while (response_count < num_responses) and (time.time() - start_time < timeout):
        # Wait for new responses (with a short timeout to periodically check conditions)
        response_event.wait(timeout=1)
        response_event.clear()
        
        # Print progress
        print(f"🔄 Progress: Received {response_count}/{num_responses} responses...")
    
    # Check if we timed out waiting for responses
    if response_count < num_responses:
        print(f"⚠️ Timed out waiting for responses: {response_count}/{num_responses} received")
        logger.warning(f"Timed out waiting for responses: {response_count}/{num_responses} received")
        
        # List missing responses
        with lock:
            missing = []
            for msg_id, msg_data in sent_messages.items():
                if msg_id not in received_responses:
                    missing.append({
                        'id': msg_id,
                        'mode': msg_data.get('mode', 'unknown'),
                        'time_elapsed': (datetime.now() - msg_data['timestamp']).total_seconds()
                    })
            
            if missing:
                print("\n⚠️ Missing responses:")
                for msg in missing:
                    print(f"  - ID: {msg['id']}, Mode: {msg['mode']}, Elapsed: {msg['time_elapsed']:.2f}s")
    else:
        print(f"✅ All {num_responses} responses received!")
        logger.info(f"All {num_responses} responses received")

def run_tests():
    """Run the requested tests"""
    start_time = datetime.now()
    print(f"\n🚀 Starting WebSocket tests at {start_time.strftime('%H:%M:%S')}")
    print(f"Mode: {args.mode}, Messages: {args.messages}, Parallel: {args.parallel}")
    
    try:
        # Connect to the server
        print(f"Connecting to {args.url}...")
        sio.connect(args.url)
        
        # Wait briefly for initial connection messages
        time.sleep(1)
        
        # Run the requested test mode(s)
        test_count = 0
        
        if args.mode == 'all' or args.mode == 'normal':
            print("\n=== RUNNING NORMAL MODE TESTS ===")
            for i in range(args.messages):
                threads = []
                for j in range(args.parallel):
                    thread = threading.Thread(
                        target=send_message, 
                        args=('normal', f"Normal test {i+1}.{j+1}")
                    )
                    thread.start()
                    threads.append(thread)
                    test_count += 1
                
                # Wait for all threads to finish sending
                for thread in threads:
                    thread.join()
                
                # Small delay between batches
                if args.parallel > 1:
                    time.sleep(0.5)
            
            # Wait for responses from normal tests
            wait_for_responses(test_count)
            test_count = 0  # Reset for next mode
        
        if args.mode == 'all' or args.mode == 'think_tank':
            print("\n=== RUNNING THINK TANK MODE TESTS ===")
            for i in range(args.messages):
                threads = []
                for j in range(args.parallel):
                    thread = threading.Thread(
                        target=send_message, 
                        args=('think_tank', f"Think tank test {i+1}.{j+1}")
                    )
                    thread.start()
                    threads.append(thread)
                    test_count += 1
                
                # Wait for all threads to finish sending
                for thread in threads:
                    thread.join()
                
                # Small delay between batches
                if args.parallel > 1:
                    time.sleep(0.5)
            
            # Wait for responses from think tank tests
            wait_for_responses(test_count)
            test_count = 0  # Reset for next mode
        
        if args.mode == 'all' or args.mode == 'timeout':
            print("\n=== RUNNING TIMEOUT MODE TESTS ===")
            for i in range(args.messages):
                threads = []
                for j in range(args.parallel):
                    thread = threading.Thread(
                        target=send_message, 
                        args=('test_timeout', f"Timeout test {i+1}.{j+1}")
                    )
                    thread.start()
                    threads.append(thread)
                    test_count += 1
                
                # Wait for all threads to finish sending
                for thread in threads:
                    thread.join()
                
                # Small delay between batches
                if args.parallel > 1:
                    time.sleep(0.5)
            
            # Wait longer for timeout tests
            print("Waiting for timeout handling (this will take at least 30 seconds)...")
            wait_for_responses(test_count, timeout=40)  # Extra time for timeouts
        
        # Report overall statistics
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print("\n=== TEST SUMMARY ===")
        print(f"Total Messages Sent: {message_count}")
        print(f"Total Responses Received: {response_count}")
        print(f"Success Rate: {response_count/message_count*100:.1f}%")
        print(f"Total Test Time: {elapsed:.2f} seconds")
        
        with lock:
            # Calculate response time statistics
            if received_responses:
                response_times = [data['elapsed'] for data in received_responses.values()]
                avg_time = sum(response_times) / len(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                print(f"Average Response Time: {avg_time:.2f} seconds")
                print(f"Fastest Response: {min_time:.2f} seconds")
                print(f"Slowest Response: {max_time:.2f} seconds")
            
            # List timed out messages
            timeouts = [
                msg_id for msg_id, data in received_responses.items() 
                if data['response'].get('model_info', {}).get('timeout', False)
            ]
            if timeouts:
                print(f"Detected {len(timeouts)} timeout(s)")
        
        print("\n✅ Tests completed")
        logger.info("Tests completed successfully")
    
    except Exception as e:
        logger.error(f"❌ Error in test runner: {str(e)}")
        print(f"❌ Error in test runner: {str(e)}")
    
    finally:
        # Disconnect from the server
        try:
            if sio.connected:
                sio.disconnect()
                print("Disconnected from server")
        except:
            pass

if __name__ == "__main__":
    run_tests()
