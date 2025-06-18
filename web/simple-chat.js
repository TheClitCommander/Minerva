// simple-chat.js - Reliable Socket.IO chat implementation
console.log('Loading simple-chat.js - reliable Socket.IO implementation');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - initializing chat');
    
    // Add status indicator for debugging
    const statusDiv = document.createElement('div');
    statusDiv.id = 'socketio-status';
    statusDiv.style.position = 'fixed';
    statusDiv.style.top = '10px';
    statusDiv.style.right = '10px';
    statusDiv.style.padding = '5px 10px';
    statusDiv.style.borderRadius = '5px';
    statusDiv.style.background = 'rgba(0,0,0,0.7)';
    statusDiv.style.color = 'white';
    statusDiv.style.fontSize = '12px';
    statusDiv.style.zIndex = '9999';
    statusDiv.innerHTML = '<span style="color:yellow">●</span> Connecting...';
    document.body.appendChild(statusDiv);
    
    // Find the chat elements
    const chatOrb = document.getElementById('chat-orb');
    const chatPanel = document.getElementById('chat-panel');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-chat-btn');
    
    if (!chatOrb || !chatPanel) {
        console.error('Chat elements not found!');
        statusDiv.innerHTML = '<span style="color:red">●</span> Chat UI elements missing';
        return;
    }
    
    // Make orb visible and clickable
    chatOrb.style.opacity = '1';
    chatOrb.style.cursor = 'pointer';
    
    // Initialize Socket.IO connection with proper parameters
    let socket;
    try {
        console.log('Creating Socket.IO connection with v4.4.1 compatibility');
        socket = io(window.location.origin, {
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });
        
        // Connection event handlers
        socket.on('connect', function() {
            console.log('✅ Socket.IO connected successfully');
            statusDiv.innerHTML = '<span style="color:green">●</span> Connected';
            
            // Show connected status in the chat panel
            if (chatMessages) {
                addMessage("Connected to Minerva. Type a message to chat!", "bot");
            }
        });
        
        socket.on('connect_error', function(error) {
            console.error('Socket.IO connection error:', error);
            statusDiv.innerHTML = '<span style="color:red">●</span> Connection Error';
        });
        
        socket.on('disconnect', function() {
            console.warn('Socket.IO disconnected');
            statusDiv.innerHTML = '<span style="color:orange">●</span> Disconnected';
        });
        
        // Message handling
        socket.on('chat_reply', function(data) {
            console.log('Received chat_reply:', data);
            let message = data;
            
            if (typeof data === 'object') {
                message = data.text || data.message || JSON.stringify(data);
            }
            
            addMessage(message, 'bot');
        });
        
        // Also handle other response events for compatibility
        socket.on('chat_response', function(data) {
            console.log('Received chat_response:', data);
            let message = data;
            
            if (typeof data === 'object') {
                message = data.message || data.text || JSON.stringify(data);
            }
            
            addMessage(message, 'bot');
        });
        
        socket.on('response', function(data) {
            console.log('Received response:', data);
            let message = data;
            
            if (typeof data === 'object') {
                message = data.text || data.message || JSON.stringify(data);
            }
            
            addMessage(message, 'bot');
        });
        
        // Click event for chat orb
        chatOrb.addEventListener('click', function() {
            console.log('Chat orb clicked');
            chatPanel.classList.toggle('active');
            
            // Focus input when panel is opened
            if (chatPanel.classList.contains('active') && chatInput) {
                setTimeout(() => chatInput.focus(), 300);
            }
        });
        
        // Send message event
        if (sendButton && chatInput) {
            sendButton.addEventListener('click', sendMessage);
            
            // Also support Enter key
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        }
        
        // Store the socket in window for debugging
        window.minervaSocket = socket;
        
    } catch (error) {
        console.error('Error initializing Socket.IO:', error);
        statusDiv.innerHTML = '<span style="color:red">●</span> Error: ' + error.message;
    }
    
    // Function to send a message
    function sendMessage() {
        if (!chatInput.value.trim()) return;
        
        const message = chatInput.value.trim();
        console.log('Sending message:', message);
        
        // Add to UI
        addMessage(message, 'user');
        
        // Send to server
        socket.emit('chat_message', { message: message });
        
        // Clear input
        chatInput.value = '';
    }
    
    // Function to add a message to the chat UI
    function addMessage(text, sender) {
        if (!chatMessages) return;
        
        console.log(`Adding ${sender} message: ${text}`);
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        
        // Format current time
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        timestamp.textContent = `${hours}:${minutes}`;
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(timestamp);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    console.log('Simple chat initialization complete');
}); 