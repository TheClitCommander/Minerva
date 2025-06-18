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
