#!/bin/bash

# Kill any existing Python server processes
echo "Stopping any existing server processes..."
pkill -f "python.*server.py" || true

# Activate virtualenv
if [ -d "./venv_minerva" ]; then
  echo "Activating virtual environment..."
  source ./venv_minerva/bin/activate
else
  echo "Virtual environment not found, using system Python..."
fi

# Make sure we have required packages with specific versions
echo "Installing required packages with compatible versions..."
pip install -q flask flask-socketio==5.3.4 flask-cors eventlet python-socketio==5.8.0 python-engineio==4.5.1

# Create a quick socket.io compatibility fix
echo "Creating Socket.IO compatibility fix..."
cat > socket_fix.js <<EOF
// Socket.IO version compatibility fix
console.log("Loading Socket.IO compatibility fix");

// Check if Socket.IO is already loaded
if (typeof io === 'undefined') {
    // Create script element to load Socket.IO v4.4.1 (compatible with python-socketio 5.8.0)
    const script = document.createElement('script');
    script.src = "https://cdn.socket.io/4.4.1/socket.io.min.js";
    script.integrity = "sha384-LzhRnpGmQP+lOvWruF/lgkcqD+WDVt9fU3H4BWmwP5u5LTmkUGafMcpZKNObVMLU";
    script.crossOrigin = "anonymous";
    document.head.appendChild(script);
    
    script.onload = function() {
        console.log("Socket.IO v4.4.1 loaded successfully");
        // Dispatch event when loaded
        document.dispatchEvent(new CustomEvent('socketio-compatible-loaded'));
    };
}
EOF

# Run the stable server
echo "Starting stable server..."
python simple_stable_server.py

# This point should not be reached due to signal handling in the Python script
echo "Server exited. Restarting in 5 seconds..."
sleep 5
exec $0  # Restart this script 