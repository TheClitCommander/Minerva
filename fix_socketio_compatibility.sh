#!/bin/bash

echo -e "\n\033[1;36m=== Minerva Socket.IO Compatibility Fix ===\033[0m\n"

# Create backup files
echo "Creating backups of files..."
cp server.py server.py.bak
cp web/minerva-portal.html web/minerva-portal.html.bak

# Step 1: Fix server.py Socket.IO initialization
echo "Fixing Socket.IO server initialization in server.py..."
# Look for the SocketIO initialization
SOCKETIO_PATTERN="socketio = SocketIO\\(.*?\\)"
SOCKETIO_REPLACEMENT="socketio = SocketIO(\n    app,\n    cors_allowed_origins=\"*\",\n    async_mode='eventlet',\n    allowEIO3=True,\n    allowEIO4=True,\n    logger=True,\n    engineio_logger=True,\n    ping_timeout=60,\n    ping_interval=25,\n    max_http_buffer_size=10 * 1024 * 1024\n)"

# Use perl for multiline regex replacement
perl -0777 -i -pe "s/$SOCKETIO_PATTERN/$SOCKETIO_REPLACEMENT/s" server.py

# Step 2: Update minerva-portal.html to use Socket.IO 4.4.1
echo "Updating minerva-portal.html to use Socket.IO 4.4.1..."
# Look for existing Socket.IO script tags and update or add
if grep -q "socket.io.*min.js" web/minerva-portal.html; then
    # Replace existing Socket.IO script tag
    perl -i -pe 's|<script src=".*socket.io.*min.js.*?"></script>|<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>|g' web/minerva-portal.html
else
    # Add Socket.IO script tag before the first script tag
    perl -i -pe 's|(<script.*?>)|<script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>\n    $1|' web/minerva-portal.html
fi

# Step 3: Create a directory for the socket.io client library
mkdir -p web/static/js

# Step 4: Download the Socket.IO client as a fallback
echo "Downloading Socket.IO 4.4.1 client as fallback..."
curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js

# Step 5: Create a socket.io.js route in server.py if it doesn't exist
if ! grep -q "@app.route('/socket.io/socket.io.js')" server.py; then
    echo "Adding Socket.IO client route to server.py..."
    # Add the route before the first @app.route
    ROUTE_CODE="\n@app.route('/socket.io/socket.io.js')\ndef serve_socketio_client():\n    \"\"\"Serve Socket.IO client library\"\"\"\n    return send_from_directory('web/static/js', 'socket.io.min.js')\n\n"
    perl -i -pe "s|(@app.route.*)|$ROUTE_CODE\$1|" server.py
fi

# Step 6: Create or update the minerva-chat.js file with proper connection logic
echo "Creating/updating minerva-chat.js with proper Socket.IO connection..."
mkdir -p web/static/js/chat

cat > web/static/js/chat/minerva-chat.js << 'EOF'
// Minerva Chat Socket.IO Connection
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Initializing Minerva chat connection...');
        
        // Initialize Socket.IO with proper parameters
        const socket = io(window.location.origin, {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });
        
        // Store in window for debugging and global access
        window.minervaSocket = socket;
        
        // Connection event handlers
        socket.on('connect', function() {
            console.log('✅ Connected to Socket.IO');
            const statusDiv = document.getElementById('socketio-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<span style="color:green">●</span> Connected';
            }
            
            // Enable chat UI elements
            const chatOrb = document.getElementById('chat-orb');
            if (chatOrb) {
                chatOrb.style.opacity = '1';
                chatOrb.style.cursor = 'pointer';
                
                // Ensure click handler for chat orb
                chatOrb.addEventListener('click', function() {
                    const chatPanel = document.getElementById('chat-panel');
                    if (chatPanel) {
                        chatPanel.classList.toggle('active');
                    }
                });
            }
        });
        
        socket.on('connect_error', function(error) {
            console.error('❌ Socket.IO connection error:', error);
            const statusDiv = document.getElementById('socketio-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<span style="color:red">●</span> Connection Error';
            }
        });
        
        socket.on('disconnect', function() {
            console.warn('⚠️ Socket.IO disconnected');
            const statusDiv = document.getElementById('socketio-status');
            if (statusDiv) {
                statusDiv.innerHTML = '<span style="color:orange">●</span> Disconnected';
            }
        });
        
        // Create status indicator
        const statusDiv = document.createElement('div');
        statusDiv.id = 'socketio-status';
        statusDiv.style.position = 'fixed';
        statusDiv.style.top = '10px';
        statusDiv.style.right = '10px';
        statusDiv.style.padding = '5px 10px';
        statusDiv.style.borderRadius = '4px';
        statusDiv.style.background = 'rgba(0,0,0,0.7)';
        statusDiv.style.color = 'white';
        statusDiv.style.fontSize = '12px';
        statusDiv.style.zIndex = '9999';
        statusDiv.innerHTML = '<span style="color:yellow">●</span> Connecting...';
        document.body.appendChild(statusDiv);
        
        // Handle chat message sending
        const sendButton = document.getElementById('send-chat-btn');
        const chatInput = document.getElementById('chat-input');
        
        if (sendButton && chatInput) {
            sendButton.addEventListener('click', sendMessage);
            
            // Also handle Enter key
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }
        
        function sendMessage() {
            if (!chatInput.value.trim()) return;
            
            const message = chatInput.value.trim();
            
            // Add message to chat UI
            addMessage(message, 'user');
            
            // Send to server
            socket.emit('chat_message', { message: message });
            
            // Clear input
            chatInput.value = '';
        }
        
        // Add message to chat interface
        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('chat-messages');
            if (!messagesContainer) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = text;
            
            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            
            // Format current time as HH:MM
            const now = new Date();
            const hours = now.getHours().toString().padStart(2, '0');
            const minutes = now.getMinutes().toString().padStart(2, '0');
            timestamp.textContent = `${hours}:${minutes}`;
            
            messageDiv.appendChild(messageContent);
            messageDiv.appendChild(timestamp);
            messagesContainer.appendChild(messageDiv);
            
            // Scroll to bottom
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        // Handle received messages from server
        socket.on('chat_response', function(data) {
            console.log('Received chat response:', data);
            let message = data;
            
            // Handle different message formats
            if (typeof data === 'object') {
                message = data.message || data.text || JSON.stringify(data);
            }
            
            addMessage(message, 'bot');
        });
        
        // For compatibility with older events
        socket.on('chat_reply', function(data) {
            console.log('Received chat reply:', data);
            let message = data;
            
            if (typeof data === 'object') {
                message = data.text || data.message || JSON.stringify(data);
            }
            
            addMessage(message, 'bot');
        });
    });
})();
EOF

# Step 7: Add the minerva-chat.js script to the HTML if needed
if ! grep -q "minerva-chat.js" web/minerva-portal.html; then
    echo "Adding minerva-chat.js script to the HTML..."
    # Add before </head>
    perl -i -pe 's|(</head>)|    <script src="/static/js/chat/minerva-chat.js"></script>\n$1|' web/minerva-portal.html
fi

# Step 8: Create a restart script
echo "Creating server restart script..."
cat > run_fixed_minerva.sh << 'EOF'
#!/bin/bash

# Stop any existing server
pkill -f server.py || true

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +  2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Ensure Socket.IO client is available
if [ ! -f "web/static/js/socket.io.min.js" ]; then
    echo "Downloading Socket.IO client..."
    curl -s https://cdn.socket.io/4.4.1/socket.io.min.js -o web/static/js/socket.io.min.js
fi

# Activate virtual environment if it exists
if [ -d "venv_minerva" ]; then
    source venv_minerva/bin/activate
fi

# Run the server
echo -e "\n\033[1;32m=== Starting Minerva with Fixed Socket.IO ===\033[0m\n"
echo "Access the portal at: http://localhost:5505/portal"
echo -e "==========================================\n"

python server.py
EOF

chmod +x run_fixed_minerva.sh

echo -e "\n\033[1;32m✅ Socket.IO compatibility fix applied!\033[0m"
echo -e "✅ Run \033[1;36m./run_fixed_minerva.sh\033[0m to start the server with fixed Socket.IO\n"

# Make this script executable
chmod +x "$0" 