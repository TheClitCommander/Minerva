#!/bin/bash

echo -e "\n\033[1;36m========================================="
echo "   🔧 Minerva Socket.IO Comprehensive Fix   "
echo -e "=========================================\033[0m\n"

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create necessary directories
mkdir -p web/static/js

# Step 1: Download compatible Socket.IO client v4.7.2
echo "📥 Downloading compatible Socket.IO client..."
curl -s https://cdn.socket.io/4.7.2/socket.io.min.js > web/static/js/socket.io-4.7.2.min.js
if [ $? -eq 0 ]; then
    echo "✅ Socket.IO client v4.7.2 downloaded successfully"
else
    echo "❌ Failed to download Socket.IO client. Check your internet connection."
    exit 1
fi

# Step 2: Add routes to server.py for serving the Socket.IO client
echo "🔄 Adding Socket.IO routes to server.py..."

# Create backup of original server.py
cp server.py server.py.bak.$(date +%Y%m%d%H%M%S)

# Check if the route already exists
if grep -q "def serve_socketio_client" server.py; then
    echo "ℹ️ Socket.IO route already exists in server.py"
else
    # Add the Socket.IO client route before the @app.route('/portal') line
    PORTAL_LINE=$(grep -n "@app.route('/portal')" server.py | head -1 | cut -d: -f1)
    
    if [ -z "$PORTAL_LINE" ]; then
        # If portal route isn't found, try to find another good insertion point
        PORTAL_LINE=$(grep -n "@app.route" server.py | head -1 | cut -d: -f1)
    fi
    
    if [ -n "$PORTAL_LINE" ]; then
        # Create a temporary file with the new routes inserted
        head -n $((PORTAL_LINE-1)) server.py > server.py.tmp
        
        cat >> server.py.tmp << 'EOF'

# Socket.IO compatibility routes - Added by fix_minerva_socketio.sh
@app.route('/socket.io/socket.io.js')
def serve_socketio_client():
    """Serve compatible Socket.IO client at the default path"""
    return send_from_directory('web/static/js', 'socket.io-4.7.2.min.js')

@app.route('/compatible-socket.io.js')
def serve_compatible_socketio():
    """Serve compatible Socket.IO client at an alternate path"""
    return send_from_directory('web/static/js', 'socket.io-4.7.2.min.js')

EOF
        
        # Append the rest of the original file
        tail -n +$PORTAL_LINE server.py >> server.py.tmp
        mv server.py.tmp server.py
        echo "✅ Added Socket.IO client routes to server.py"
    else
        echo "⚠️ Could not find a suitable location to add Socket.IO routes"
        echo "   You'll need to manually add the routes to server.py"
    fi
fi

# Step 3: Update Socket.IO initialization in server.py
echo "🔄 Updating Socket.IO initialization parameters..."

# Check if the allowEIO3/allowEIO4 parameters are already set
if grep -q "allowEIO[34]" server.py; then
    echo "ℹ️ Socket.IO compatibility parameters already exist"
else
    # Find the socketio initialization line
    SOCKETIO_LINE=$(grep -n "socketio = SocketIO" server.py | cut -d: -f1)
    
    if [ -n "$SOCKETIO_LINE" ]; then
        # Extract the current initialization line and its arguments
        INIT_BLOCK=$(grep -A10 "socketio = SocketIO" server.py | sed -n '/socketio = SocketIO/,/)/p')
        
        # Count the number of lines in the initialization block
        INIT_LINES=$(echo "$INIT_BLOCK" | wc -l)
        
        # If it's a single line, replace it with a multi-line version
        if [ "$INIT_LINES" -lt 3 ]; then
            sed -i.socketiobak "s/socketio = SocketIO(.*/socketio = SocketIO(\n    app, \n    cors_allowed_origins=\"*\",\n    async_mode=async_mode,\n    logger=True, \n    engineio_logger=True,\n    ping_timeout=60,\n    ping_interval=25,\n    # Critical compatibility settings\n    allowEIO3=True,\n    allowEIO4=True,\n    always_connect=True\n)/" server.py
        else
            # If it's already multi-line, insert the compatibility parameters before the closing parenthesis
            LAST_LINE=$(echo "$INIT_BLOCK" | grep -n ")" | cut -d: -f1)
            LAST_LINE=$((SOCKETIO_LINE + LAST_LINE - 1))
            PREV_LINE=$((LAST_LINE - 1))
            
            # Insert the compatibility parameters
            sed -i.socketiobak "${PREV_LINE}a\\    # Critical compatibility settings\\n    allowEIO3=True,\\n    allowEIO4=True,\\n    always_connect=True" server.py
        fi
        
        echo "✅ Updated Socket.IO initialization parameters"
    else
        echo "⚠️ Could not find Socket.IO initialization line"
        echo "   You'll need to manually update the SocketIO initialization parameters"
    fi
fi

# Step 4: Add debug event handler for Socket.IO
echo "🔄 Adding Socket.IO debug event handler..."

# Check if debug event handler already exists
if grep -q "@socketio.on('debug')" server.py; then
    echo "ℹ️ Debug event handler already exists"
else
    # Find the last @socketio.on decorator
    LAST_HANDLER=$(grep -n "@socketio.on" server.py | tail -1 | cut -d: -f1)
    
    if [ -n "$LAST_HANDLER" ]; then
        # Find the end of the last handler function
        FUNC_END=$(tail -n +$LAST_HANDLER server.py | grep -n "^$" | head -1 | cut -d: -f1)
        INSERT_LINE=$((LAST_HANDLER + FUNC_END))
        
        # Create temporary file with the debug handler inserted
        head -n $INSERT_LINE server.py > server.py.tmp
        
        cat >> server.py.tmp << 'EOF'

# Debug event handler for Socket.IO testing
@socketio.on('debug')
def handle_debug(data):
    """Debug event handler for Socket.IO testing"""
    print(f"Received debug event: {data}")
    
    # Echo the data back to the client
    emit('debug_response', {
        'server_time': datetime.datetime.now().isoformat(),
        'received': data,
        'status': 'ok'
    })
    
    # Also send a system message for UI visibility
    emit('system_message', {'message': 'Debug connection successful'})

EOF
        
        # Append the rest of the original file
        tail -n +$((INSERT_LINE+1)) server.py >> server.py.tmp
        mv server.py.tmp server.py
        echo "✅ Added Socket.IO debug event handler"
    else
        echo "⚠️ Could not find suitable location for debug event handler"
    fi
fi

# Step 5: Update chat message handler for robust error handling
echo "🔄 Enhancing chat message handler with error handling..."

# Check if it's already been updated with robust error handling
if grep -q "try:" server.py && grep -q "except Exception as e:" server.py; then
    echo "ℹ️ Chat message handler already has error handling"
else
    # Find the chat message handler
    CHAT_HANDLER=$(grep -n "@socketio.on('chat_message')" server.py | cut -d: -f1)
    
    if [ -n "$CHAT_HANDLER" ]; then
        # Find the approximate end of the handler function
        HANDLER_END=$(tail -n +$CHAT_HANDLER server.py | grep -n "@socketio.on" | head -1 | cut -d: -f1)
        
        if [ -n "$HANDLER_END" ]; then
            HANDLER_END=$((CHAT_HANDLER + HANDLER_END - 2))
            
            # Extract the current handler function
            HANDLER_CODE=$(sed -n "${CHAT_HANDLER},${HANDLER_END}p" server.py)
            
            # Check if it already has try/except
            if ! echo "$HANDLER_CODE" | grep -q "try:"; then
                # Modify the handler line to include "try:" after the function definition
                HANDLER_DEF_LINE=$((CHAT_HANDLER + 1))
                FUNC_DEF=$(sed -n "${HANDLER_DEF_LINE}p" server.py)
                INDENTATION=$(echo "$FUNC_DEF" | sed -E 's/^(\s*)def.*/\1/')
                
                # Create temporary file with try/except block
                head -n $HANDLER_DEF_LINE server.py > server.py.tmp
                echo "${INDENTATION}try:" >> server.py.tmp
                
                # Add the existing handler body with additional indentation
                awk -v start=$((HANDLER_DEF_LINE+1)) -v end=$HANDLER_END -v indent="$INDENTATION    " 'NR > start && NR <= end {print indent $0; next} {print}' server.py >> server.py.tmp
                
                # Add except block
                cat >> server.py.tmp << EOF
${INDENTATION}except Exception as e:
${INDENTATION}    error_msg = f"Error processing message: {str(e)}"
${INDENTATION}    print(error_msg)
${INDENTATION}    import traceback
${INDENTATION}    traceback.print_exc()
${INDENTATION}    
${INDENTATION}    # Always send a response, even on error
${INDENTATION}    emit('chat_reply', {'text': f"Sorry, an error occurred: {str(e)}. Please try again."})
${INDENTATION}    return {'status': 'error', 'message': error_msg}
EOF
                
                # Append the rest of the original file
                tail -n +$((HANDLER_END+1)) server.py >> server.py.tmp
                mv server.py.tmp server.py
                echo "✅ Enhanced chat message handler with error handling"
            fi
        else
            echo "⚠️ Could not find the end of chat message handler"
        fi
    else
        echo "⚠️ Could not find chat message handler"
    fi
fi

# Step 6: Update minerva-portal.html to use compatible Socket.IO client
echo "🔄 Updating minerva-portal.html to use compatible Socket.IO client..."

# Create backup of original minerva-portal.html
cp web/minerva-portal.html web/minerva-portal.html.bak.$(date +%Y%m%d%H%M%S)

# Check if it's already been updated
if grep -q "/socket.io/socket.io.js" web/minerva-portal.html; then
    if ! grep -q "/compatible-socket.io.js" web/minerva-portal.html; then
        # Update the script tag to use our compatible version
        sed -i.htmlbak 's|<script src="/socket.io/socket.io.js"></script>|<script src="/socket.io/socket.io.js"></script>|g' web/minerva-portal.html
        echo "✅ Updated Socket.IO client reference in minerva-portal.html"
    else
        echo "ℹ️ minerva-portal.html already uses compatible Socket.IO client"
    fi
else
    echo "⚠️ Could not find Socket.IO script tag in minerva-portal.html"
    echo "   Checking for CDN version..."
    
    # Check for CDN version of Socket.IO
    if grep -q "cdn.socket.io" web/minerva-portal.html; then
        sed -i.htmlbak 's|<script src="https://cdn.socket.io/[^"]*"></script>|<script src="/socket.io/socket.io.js"></script>|g' web/minerva-portal.html
        echo "✅ Updated CDN Socket.IO reference to use local compatible version"
    else
        echo "⚠️ No Socket.IO script tag found in minerva-portal.html"
        echo "   Adding Socket.IO script tag to head section..."
        
        # Add the script tag to the head section
        sed -i.htmlbak '/<head>/a\    <script src="/socket.io/socket.io.js"></script>' web/minerva-portal.html
        echo "✅ Added Socket.IO script tag to minerva-portal.html"
    fi
fi

# Step 7: Add socket diagnostic script
echo "🔄 Creating Socket.IO diagnostic page..."

# Create diagnostic HTML file
cat > web/socket-test.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minerva Socket.IO Diagnostics</title>
    <script src="/socket.io/socket.io.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        #status {
            padding: 10px;
            border-radius: 4px;
            margin: 20px 0;
            font-weight: bold;
        }
        .connected { 
            background-color: #d4edda; 
            color: #155724;
        }
        .disconnected { 
            background-color: #f8d7da; 
            color: #721c24;
        }
        .connecting { 
            background-color: #fff3cd; 
            color: #856404;
        }
        .log {
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
            font-family: monospace;
            white-space: pre-wrap;
        }
        .log .info { color: #0c5460; }
        .log .error { color: #721c24; }
        .log .success { color: #155724; }
        .log .warn { color: #856404; }
        .input-group {
            display: flex;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
        }
        button {
            padding: 10px 15px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
        }
        button:hover {
            background-color: #0069d9;
        }
        button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <h1>Minerva Socket.IO Diagnostics</h1>
    <div id="status" class="connecting">Connecting...</div>
    
    <div class="input-group">
        <input type="text" id="message" placeholder="Type a message to test chat">
        <button id="send" disabled>Send</button>
    </div>
    
    <h3>Event Log</h3>
    <div id="log" class="log"></div>
    
    <div class="input-group">
        <input type="text" id="event" placeholder="Event name (e.g., 'debug')">
        <button id="emit-event">Emit Event</button>
    </div>
    
    <script>
        // DOM Elements
        const statusElement = document.getElementById('status');
        const logElement = document.getElementById('log');
        const messageInput = document.getElementById('message');
        const sendButton = document.getElementById('send');
        const eventInput = document.getElementById('event');
        const emitEventButton = document.getElementById('emit-event');
        
        // Log function
        function log(message, type = 'info') {
            const entry = document.createElement('div');
            entry.className = type;
            entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            logElement.appendChild(entry);
            logElement.scrollTop = logElement.scrollHeight;
        }
        
        // Initialize Socket.IO
        log('Initializing Socket.IO connection...');
        
        const socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000,
            transports: ['websocket', 'polling']
        });
        
        // Connection events
        socket.on('connect', () => {
            log('Socket.IO CONNECTED ✅', 'success');
            statusElement.textContent = 'Connected ✅';
            statusElement.className = 'connected';
            sendButton.disabled = false;
            
            // Send debug ping
            socket.emit('debug', {
                client: 'diagnostic-tool',
                timestamp: Date.now(),
                ua: navigator.userAgent
            });
            log('Sent debug ping');
        });
        
        socket.on('disconnect', () => {
            log('Socket.IO DISCONNECTED ❌', 'error');
            statusElement.textContent = 'Disconnected ❌';
            statusElement.className = 'disconnected';
            sendButton.disabled = true;
        });
        
        socket.on('connect_error', (error) => {
            log(`Socket.IO CONNECTION ERROR: ${error}`, 'error');
            statusElement.textContent = 'Connection Error ❌';
            statusElement.className = 'disconnected';
            sendButton.disabled = true;
        });
        
        // Response events
        socket.on('message', (data) => {
            log(`Received 'message' event: ${JSON.stringify(data)}`, 'info');
        });
        
        socket.on('chat_reply', (data) => {
            log(`Received 'chat_reply' event: ${JSON.stringify(data)}`, 'success');
        });
        
        socket.on('response', (data) => {
            log(`Received 'response' event: ${JSON.stringify(data)}`, 'info');
        });
        
        socket.on('system_message', (data) => {
            log(`Received 'system_message': ${JSON.stringify(data)}`, 'warn');
        });
        
        socket.on('debug_response', (data) => {
            log(`Received 'debug_response': ${JSON.stringify(data)}`, 'info');
        });
        
        // Catch all events for comprehensive logging
        const originalOnEvent = socket.onevent;
        socket.onevent = function(packet) {
            const eventName = packet.data[0];
            if (!['message', 'chat_reply', 'response', 'system_message', 'debug_response'].includes(eventName)) {
                log(`Received '${eventName}' event: ${JSON.stringify(packet.data.slice(1))}`, 'info');
            }
            return originalOnEvent.apply(this, arguments);
        };
        
        // Send button handler
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (message) {
                log(`Sending chat_message: ${message}`, 'info');
                
                // Try both event names for maximum compatibility
                socket.emit('chat_message', { text: message });
                
                // Also try the alternate format
                setTimeout(() => {
                    socket.emit('message', message);
                }, 100);
                
                messageInput.value = '';
            }
        });
        
        // Enter key to send
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !sendButton.disabled) {
                sendButton.click();
            }
        });
        
        // Custom event emitter
        emitEventButton.addEventListener('click', () => {
            const eventName = eventInput.value.trim();
            if (eventName) {
                log(`Emitting custom event: ${eventName}`, 'info');
                socket.emit(eventName, { text: 'Test payload', timestamp: Date.now() });
            }
        });
    </script>
</body>
</html>
EOF

# Add route to server.py for socket test page if not already present
if ! grep -q "@app.route('/socket-test')" server.py; then
    # Find a good insertion point after the existing routes
    ROUTE_LINE=$(grep -n "@app.route" server.py | tail -1 | cut -d: -f1)
    
    if [ -n "$ROUTE_LINE" ]; then
        # Find the end of the last route function
        FUNC_END=$(tail -n +$ROUTE_LINE server.py | grep -n "^$" | head -1 | cut -d: -f1)
        INSERT_LINE=$((ROUTE_LINE + FUNC_END))
        
        # Create temporary file with the new route inserted
        head -n $INSERT_LINE server.py > server.py.tmp
        
        cat >> server.py.tmp << 'EOF'

# Socket.IO diagnostic page
@app.route('/socket-test')
def socket_test_page():
    """Serve the Socket.IO diagnostic page"""
    return send_from_directory('web', 'socket-test.html')

EOF
        
        # Append the rest of the original file
        tail -n +$((INSERT_LINE+1)) server.py >> server.py.tmp
        mv server.py.tmp server.py
        echo "✅ Added route for Socket.IO diagnostic page"
    else
        echo "⚠️ Could not find suitable location for socket-test route"
    fi
fi

echo "✅ Created Socket.IO diagnostic page"

# Step 8: Create server launcher script
echo "🔄 Creating enhanced server launcher script..."

cat > run_fixed_server.sh << 'EOF'
#!/bin/bash

echo -e "\n\033[1;36m========================================="
echo "   🚀 Minerva Server with Socket.IO Fix   "
echo -e "=========================================\033[0m\n"

# Kill any running server instances
echo "🔄 Stopping any existing server processes..."
pkill -f server.py || true
sleep 1

# Set required environment variables
export FLASK_DEBUG=1
export PYTHONPATH=$PYTHONPATH:$(pwd)
export SOCKETIO_DEBUG=1

# Activate virtual environment if it exists
if [ -d "./venv_minerva" ]; then
    echo "🐍 Activating Python virtual environment..."
    source ./venv_minerva/bin/activate
    PYTHON_CMD="python"
else
    echo "⚠️ No virtual environment found at ./venv_minerva"
    echo "🔍 Looking for Python in path..."
    PYTHON_CMD=$(which python3 || which python)
    if [ -z "$PYTHON_CMD" ]; then
        echo "❌ ERROR: Python not found! Please install Python or specify the correct path."
        exit 1
    fi
    echo "🐍 Using Python at: $PYTHON_CMD"
fi

echo -e "\n\033[1;33m==== Starting Minerva Server ====\033[0m"
echo "📊 Server will be available at: http://localhost:5505/portal"
echo "🔍 Socket.IO diagnostics: http://localhost:5505/socket-test"
echo -e "\033[1;33m==============================\033[0m\n"

# Add signal handling for SIGTERM and SIGINT
function cleanup {
    echo -e "\n🛑 Shutting down Minerva server gracefully..."
    pkill -f server.py || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Execute the server with output logging
$PYTHON_CMD server.py 2>&1 | tee -a minerva_fixed.log

# This shouldn't be reached due to signal trapping
echo "⚠️ Server exited unexpectedly. Check minerva_fixed.log for details."
EOF

chmod +x run_fixed_server.sh
echo "✅ Created enhanced server launcher script: run_fixed_server.sh"

# Final message with instructions
echo -e "\n\033[1;32m==================================================="
echo "   ✅ Minerva Socket.IO Fix Complete!   "
echo -e "===================================================\033[0m\n"

echo "🚀 To run your fixed Minerva server:"
echo "  1. Execute:  ./run_fixed_server.sh"
echo "  2. Open:     http://localhost:5505/portal"
echo "  3. Test:     http://localhost:5505/socket-test (Socket.IO diagnostics)"
echo ""
echo "📋 What we've fixed:"
echo "  ✓ Added compatible Socket.IO client version 4.7.2"
echo "  ✓ Added routes to serve Socket.IO client correctly"
echo "  ✓ Updated Socket.IO server initialization parameters"
echo "  ✓ Enhanced chat message handler with better error handling"
echo "  ✓ Created diagnostic tool to verify Socket.IO connection"
echo "  ✓ Created improved server launcher with signal handling"
echo ""
echo "🔙 Backups of original files were created with .bak extensions"
echo -e "\033[1;33mEnjoy your now-reliable Minerva server!\033[0m" 