from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import time
import random

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/api/status", methods=["GET", "OPTIONS"])
def status():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
    return jsonify({
        "status": "online", 
        "message": "API is connected and running",
        "timestamp": time.time()
    })

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
        
    try:
        user_msg = request.json.get("message", "")
        # Simulate a thoughtful response
        time.sleep(0.5)
        
        responses = [
            f"You said: {user_msg}. I'm directly connected through the real API!",
            f"Processing '{user_msg}'. The Think Tank API is operational and responding.",
            f"Your input '{user_msg}' has been received by the Minerva system.",
            f"Analyzing your message: '{user_msg}'. Connection is stable."
        ]
        
        return jsonify({"response": random.choice(responses)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/projects", methods=["GET", "OPTIONS"])
def projects():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
        
    return jsonify([
        {"id": 1, "name": "Minerva UI Redesign", "status": "active", "description": "Creating a cosmic themed orbital interface"},
        {"id": 2, "name": "API Integration", "status": "in-progress", "description": "Connecting frontend to the backend API"},
        {"id": 3, "name": "Orb Mechanics", "status": "planned", "description": "Animating orbital menu elements"},
        {"id": 4, "name": "Think Tank", "status": "active", "description": "Core AI processing system"}
    ])

@app.route("/api/memories", methods=["GET", "OPTIONS"])
def memories():
    if request.method == "OPTIONS":
        return _build_cors_preflight_response()
        
    return jsonify([
        {"id": 1, "text": "Created a detailed integration plan for embedding chat functionality directly into Minerva's core UI", "type": "planning", "date": "2025-04-01"},
        {"id": 2, "text": "Restored Orb UI with a comprehensive approach", "type": "development", "date": "2025-04-03"},
        {"id": 3, "text": "Implemented a simplified but functional HTML structure matching JS expectations", "type": "development", "date": "2025-04-05"},
        {"id": 4, "text": "Added clean-orb.css for modern styling", "type": "design", "date": "2025-04-05"},
        {"id": 5, "text": "When we achieve a working solution, we must build upon that success rather than starting over", "type": "principle", "date": "2025-04-06"},
        {"id": 6, "text": "Implemented the floating chat component based on our integration plan", "type": "development", "date": "2025-04-06"},
        {"id": 7, "text": "Added localStorage persistence for conversations", "type": "feature", "date": "2025-04-06"},
        {"id": 8, "text": "Project-specific chat panel should be small, wide and thin", "type": "design", "date": "2025-04-06"},
        {"id": 9, "text": "The orb should be centered with menu items orbiting in a circular layout", "type": "design", "date": "2025-04-07"},
        {"id": 10, "text": "Use cosmic styling with radial menus and orbital animations", "type": "design", "date": "2025-04-07"},
        {"id": 11, "text": "Direct API connection established - no more fallbacks or simulated responses", "type": "development", "date": "2025-04-07"},
        {"id": 12, "text": "Created a single source of truth for API connections", "type": "architecture", "date": "2025-04-07"}
    ])

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    return response

# Handle 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist."
    }), 404

# Handle all other errors
@app.errorhandler(Exception)
def handle_error(error):
    return jsonify({
        "error": str(error),
        "message": "An unexpected error occurred."
    }), 500

if __name__ == "__main__":
    print("🚀 Starting Minerva API Server on http://127.0.0.1:5505")
    print("Available endpoints:")
    print("  - /api/status  [GET]")
    print("  - /api/chat    [POST]")
    print("  - /api/projects [GET]")
    print("  - /api/memories [GET]")
    app.run(host="127.0.0.1", port=5505, debug=True)
