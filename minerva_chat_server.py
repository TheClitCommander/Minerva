import os
import signal
import requests
import sys
from flask import Flask, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO

# ---- SIGTERM HANDLING - MUST BE AT THE VERY TOP ---- #
print("🛡️ Setting up signal handlers to prevent termination...")
# Ignore ALL termination signals
signal.signal(signal.SIGTERM, signal.SIG_IGN)
signal.signal(signal.SIGINT, signal.SIG_IGN)  # Also ignore Ctrl+C in terminal
signal.signal(signal.SIGHUP, signal.SIG_IGN)  # Also ignore terminal closing

# Override Python's default handling to prevent sys.exit()
original_exit = sys.exit
def protected_exit(*args, **kwargs):
    print(f"🚨 Something tried to exit Python with: {args} {kwargs}")
    print("🛡️ Exit blocked - server will continue running")
    return None
sys.exit = protected_exit

print("✅ All termination signals disabled - server CANNOT be killed except with kill -9")

# ---- DUMMY COORDINATOR W/ REAL FALLBACK ---- #
class ChatCoordinator:
    def __init__(self):
        self.models = {}
        self.load_models()
        print(f"✅ ChatCoordinator initialized with {len(self.models)} models")

    def load_models(self):
        if os.getenv("OPENAI_API_KEY", "").startswith("sk-"):
            self.models['openai'] = ['gpt-4']
            print("✅ OpenAI models loaded")
        if os.getenv("HUGGINGFACE_API_KEY", "").startswith("hf_"):
            self.models['huggingface'] = ['gpt2']
            print("✅ HuggingFace models loaded")
        if not self.models:
            print("⚠️ No API keys found, using simulation mode")

    def list_models(self):
        return self.models

    def call_model(self, prompt):
        if 'huggingface' in self.models:
            return self._call_huggingface("gpt2", prompt)
        if 'openai' in self.models:
            return self._call_openai("gpt-4", prompt)
        return f"[SIMULATED] Response to: {prompt}"

    def _call_huggingface(self, model, prompt):
        headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}",
            "Content-Type": "application/json"
        }
        payload = {"inputs": prompt}
        url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            r = requests.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data[0]['generated_text'] if isinstance(data, list) else str(data)
        except Exception as e:
            return f"[HF ERROR] {str(e)}"
    
    def _call_openai(self, model, prompt):
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OPENAI ERROR] {str(e)}"

# Create coordinator BEFORE anything else
coordinator = ChatCoordinator()
Coordinator = coordinator  # Capital C version for compatibility

# ---- FLASK APP + SOCKET.IO CONFIG ---- #
app = Flask(__name__, 
            static_folder='web',
            template_folder='templates')
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='eventlet',
    logger=True,
    allowEIO3=True,  # Critical for compatibility
    allowEIO4=True   # Critical for compatibility
)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/portal")
def portal():
    return render_template('portal.html')

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory('web', path)

@app.route("/api/status")
def status():
    return jsonify({
        "status": "healthy",
        "models": coordinator.list_models(),
        "version": "1.0.0"
    })

@socketio.on('connect')
def handle_connect():
    print(f"[SOCKET] Client connected")
    socketio.emit('system_message', {'message': 'Connected to Minerva Chat'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[SOCKET] Client disconnected")

@socketio.on("chat")
def handle_chat(data):
    msg = data.get("message", "")
    print(f"[CHAT IN] {msg}")
    reply = coordinator.call_model(msg)
    print(f"[CHAT OUT] {reply}")
    
    # Send through multiple channel formats for compatibility
    print("⚡ Emitting response on 'response' channel")
    socketio.emit("response", {"reply": reply})
    print("⚡ Emitting response on 'ai_response' channel")
    socketio.emit("ai_response", {"message": reply})
    print("⚡ Emitting response on 'chat_reply' channel")
    socketio.emit("chat_reply", {"text": reply})
    print("✅ All responses sent successfully")

# Socket.IO v3/v4 compatibility - handle multiple message formats
@socketio.on("user_message")
def handle_user_message(data):
    message = data.get("message", "") or data.get("text", "")
    print(f"[USER MSG] {message}")
    reply = coordinator.call_model(message)
    print(f"[AI REPLY] {reply}")
    
    # Send through multiple channel formats for compatibility
    socketio.emit("response", {"reply": reply})
    socketio.emit("ai_response", {"message": reply})
    socketio.emit("chat_reply", {"text": reply})

if __name__ == '__main__':
    print("✅ Minerva Chat Server starting on http://localhost:5505")
    print("✅ Visit http://localhost:5505/portal to access the chat")
    try:
        socketio.run(app, host="0.0.0.0", port=5505)
    except Exception as e:
        print(f"🚨 Socket.IO EXCEPTION: {e}")
    print("🚨 Server terminated - THIS SHOULD NEVER PRINT UNLESS -9 KILLED") 