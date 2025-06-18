/**
 * Socket.IO client initializer with compatibility settings
 * For Minerva Portal - Compatible with Python 3.13
 */

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Socket.IO initializer loaded");
    
    // Create global socketConnect function that will be called after
    // the Socket.IO client library is loaded
    window.socketConnect = function() {
        console.log("Connecting to Socket.IO server...");
        
        // Initialize Socket.IO with compatibility options
        window.socket = io({
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            // Important: Support both WebSocket and polling for maximum compatibility
            transports: ['websocket', 'polling']
        });
        
        // Connection events
        socket.on('connect', function() {
            console.log('✅ Socket.IO connected successfully');
            // Add a connection indicator to the page
            showConnectionStatus(true);
        });
        
        socket.on('disconnect', function(reason) {
            console.log('❌ Socket.IO disconnected: ' + reason);
            showConnectionStatus(false);
        });
        
        socket.on('connect_error', function(error) {
            console.error('Socket.IO connection error:', error);
            showConnectionStatus(false, error.message);
        });
        
        // Listen for chat replies
        socket.on('chat_reply', function(data) {
            console.log('Received chat_reply:', data);
            // The main chat.js will handle this event
        });
        
        socket.on('chat_response', function(data) {
            console.log('Received chat_response:', data);
            // The main chat.js will handle this event
        });
    };
    
    // Create a small indicator element for connection status
    function showConnectionStatus(connected, message) {
        let statusEl = document.getElementById('socket-status-indicator');
        
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'socket-status-indicator';
            statusEl.style.position = 'fixed';
            statusEl.style.bottom = '10px';
            statusEl.style.right = '10px';
            statusEl.style.padding = '5px 10px';
            statusEl.style.borderRadius = '3px';
            statusEl.style.fontSize = '12px';
            statusEl.style.fontWeight = 'bold';
            statusEl.style.zIndex = '9999';
            document.body.appendChild(statusEl);
        }
        
        if (connected) {
            statusEl.style.backgroundColor = '#d4edda';
            statusEl.style.color = '#155724';
            statusEl.style.border = '1px solid #c3e6cb';
            statusEl.textContent = 'Socket.IO: Connected';
        } else {
            statusEl.style.backgroundColor = '#f8d7da';
            statusEl.style.color = '#721c24';
            statusEl.style.border = '1px solid #f5c6cb';
            statusEl.textContent = 'Socket.IO: Disconnected' + (message ? ' (' + message + ')' : '');
        }
    }
    
    // Call socketConnect after Socket.IO is loaded
    if (typeof io !== 'undefined') {
        socketConnect();
    } else {
        console.log('Waiting for Socket.IO library to load...');
        // This will be called after the fallback script loads
        window.addEventListener('load', function() {
            if (typeof io !== 'undefined') {
                socketConnect();
            } else {
                console.error('Socket.IO library failed to load');
                showConnectionStatus(false, 'Failed to load Socket.IO');
            }
        });
    }
}); 