import logging
import json
import os
import threading
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Fix Import Paths for Minerva AI Components
try:
    from web.multi_ai_coordinator import MultiAICoordinator
    from web.response_handler import validate_response
    from web.think_tank_processor import route_request
except ImportError as e:
    logging.error(f"❌ Failed to import Minerva AI components: {e}")
    MultiAICoordinator = None
    validate_response = None
    route_request = None

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
logger = logging.getLogger("standalone_websocket")
logging.basicConfig(level=logging.DEBUG)

# Initialize AI Coordinator
if MultiAICoordinator:
    try:
        coordinator = MultiAICoordinator(config_path="web/config.json")
        logger.info("✅ MultiAICoordinator successfully initialized!")
    except Exception as e:
        logger.error(f"❌ Error initializing MultiAICoordinator: {e}")
        coordinator = None
else:
    logger.warning("⚠️ MultiAICoordinator not available. Using fallback mode.")

def process_think_tank(message, session_id):
    """Process message using Minerva's Think Tank system."""
    if not coordinator or not route_request:
        logger.warning("⚠️ AI routing unavailable. Defaulting to echo response.")
        emit("response", {"message_id": message["message_id"], "session_id": session_id, "response": f"Echo: {message['message']}"}, room=session_id)
        return
    
    try:
        logger.info(f"🧠 Think Tank processing started for {message['message_id']}")
        routing_info = route_request(message["message"])
        responses = coordinator.process_query(message["message"], routing_info)
        
        if validate_response:
            responses = [validate_response(resp) for resp in responses]
        
        best_response = max(responses, key=lambda x: x.get("quality_score", 0))
        emit("response", {"message_id": message["message_id"], "session_id": session_id, "response": best_response["response"]}, room=session_id)
        logger.info(f"✅ AI Response Sent for {message['message_id']}")
    except Exception as e:
        logger.error(f"❌ Error in AI processing: {e}")
        emit("response", {"message_id": message["message_id"], "session_id": session_id, "response": "Error processing AI request"}, room=session_id)

@socketio.on("message")
def handle_message(message):
    session_id = request.sid
    logger.info(f"📩 Received message: ID={message['message_id']}, Mode={message.get('mode', 'normal')}")
    if message.get("mode") == "think_tank":
        threading.Thread(target=process_think_tank, args=(message, session_id)).start()
    else:
        emit("response", {"message_id": message["message_id"], "session_id": session_id, "response": f"Echo: {message['message']}"}, room=session_id)

if __name__ == "__main__":
    logger.info("🚀 Starting standalone WebSocket server for Minerva AI testing")
    socketio.run(app, host="0.0.0.0", port=5050, debug=True)
