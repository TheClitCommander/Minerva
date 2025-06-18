// Debug Chat.js - A simple script to debug Socket.IO chat functionality
console.log('Debug Chat.js loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Status indicator
    const statusDiv = document.createElement('div');
    statusDiv.id = 'socketio-status';
    statusDiv.style.position = 'fixed';
    statusDiv.style.top = '10px';
    statusDiv.style.right = '10px';
    statusDiv.style.padding = '5px 10px';
    statusDiv.style.zIndex = '9999';
    statusDiv.style.background = 'rgba(0,0,0,0.7)';
    statusDiv.style.color = 'white';
    statusDiv.style.fontSize = '14px';
    statusDiv.innerHTML = '<span style="color:yellow">●</span> Connecting...';
    document.body.appendChild(statusDiv);

    // Debug log area
    const logDiv = document.createElement('div');
    logDiv.id = 'debug-log';
    logDiv.style.position = 'fixed';
    logDiv.style.bottom = '10px';
    logDiv.style.right = '10px';
    logDiv.style.width = '400px';
    logDiv.style.height = '300px';
    logDiv.style.padding = '10px';
    logDiv.style.background = 'rgba(0,0,0,0.8)';
    logDiv.style.color = 'lime';
    logDiv.style.fontFamily = 'monospace';
    logDiv.style.fontSize = '12px';
    logDiv.style.overflow = 'auto';
    logDiv.style.zIndex = '9998';
    logDiv.style.borderRadius = '5px';
    document.body.appendChild(logDiv);

    // Add debug log function
    function debugLog(message, type = 'info') {
        const now = new Date();
        const timestamp = now.toISOString().substr(11, 8);
        
        // Color based on type
        let color = 'lime';
        if (type === 'error') color = 'red';
        if (type === 'warn') color = 'orange';
        if (type === 'receive') color = 'cyan';
        if (type === 'send') color = 'yellow';
        
        const logItem = document.createElement('div');
        logItem.innerHTML = `<span style="color:gray">${timestamp}</span> <span style="color:${color}">${message}</span>`;
        
        const log = document.getElementById('debug-log');
        log.appendChild(logItem);
        log.scrollTop = log.scrollHeight;
    }
    
    // Expose the debug log function globally
    window.debugLog = debugLog;

    // Initialize Socket.IO with proper parameters
    debugLog('Initializing Socket.IO connection...');
    
    // Create a Socket.IO instance with all compatibility options
    const socket = io(window.location.origin, {
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        forceNew: true,
        timeout: 10000
    });
    
    // Store in window for debugging
    window.debugSocket = socket;
    
    // Handle connection events
    socket.on('connect', function() {
        debugLog('CONNECTED to Socket.IO server', 'info');
        statusDiv.innerHTML = '<span style="color:green">●</span> Connected';
        
        // Send a test message after connection
        setTimeout(() => {
            debugLog('Sending test message...', 'send');
            socket.emit('chat_message', { message: 'Test message from debug-chat.js' });
        }, 1000);
    });
    
    socket.on('connect_error', function(error) {
        debugLog(`CONNECTION ERROR: ${error}`, 'error');
        statusDiv.innerHTML = '<span style="color:red">●</span> Error: ' + error;
    });
    
    socket.on('disconnect', function() {
        debugLog('DISCONNECTED from Socket.IO server', 'warn');
        statusDiv.innerHTML = '<span style="color:orange">●</span> Disconnected';
    });
    
    // Handle response events - multiple formats for compatibility
    socket.on('chat_response', function(data) {
        debugLog(`Received chat_response: ${JSON.stringify(data)}`, 'receive');
    });
    
    socket.on('chat_reply', function(data) {
        debugLog(`Received chat_reply: ${JSON.stringify(data)}`, 'receive');
    });
    
    socket.on('response', function(data) {
        debugLog(`Received response: ${JSON.stringify(data)}`, 'receive');
    });
    
    socket.on('message', function(data) {
        debugLog(`Received message: ${JSON.stringify(data)}`, 'receive');
    });
    
    // Create a simple test UI
    const testUI = document.createElement('div');
    testUI.style.position = 'fixed';
    testUI.style.top = '50px';
    testUI.style.right = '10px';
    testUI.style.padding = '10px';
    testUI.style.background = 'rgba(0,0,0,0.8)';
    testUI.style.borderRadius = '5px';
    testUI.style.zIndex = '9997';
    
    testUI.innerHTML = `
        <div style="margin-bottom:10px">
            <input id="test-message" type="text" placeholder="Test message..." 
                   style="padding:5px; width:300px; border-radius:3px; border:none">
        </div>
        <div>
            <button id="send-test" style="padding:5px 10px; background:#6e4cf8; color:white; border:none; border-radius:3px; cursor:pointer">
                Send Test Message
            </button>
            <button id="reconnect-socket" style="padding:5px 10px; margin-left:10px; background:#333; color:white; border:none; border-radius:3px; cursor:pointer">
                Reconnect
            </button>
        </div>
    `;
    
    document.body.appendChild(testUI);
    
    // Add event handlers for test UI
    document.getElementById('send-test').addEventListener('click', function() {
        const message = document.getElementById('test-message').value;
        if (message) {
            debugLog(`Sending message: ${message}`, 'send');
            socket.emit('chat_message', { message: message });
            document.getElementById('test-message').value = '';
        }
    });
    
    document.getElementById('reconnect-socket').addEventListener('click', function() {
        debugLog('Manually reconnecting...', 'warn');
        socket.disconnect();
        setTimeout(() => {
            socket.connect();
        }, 1000);
    });
    
    // Handle Enter key in text input
    document.getElementById('test-message').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('send-test').click();
        }
    });
    
    debugLog('Debug Chat.js initialization complete');
}); 