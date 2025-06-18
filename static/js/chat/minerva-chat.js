// Initialize socket connection with proper configuration for v4.5.4
const socket = io({
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    timeout: 20000
});

// Connection status handlers with console logging
socket.on('connect', function() {
    console.log('Socket connected! ID:', socket.id);
    const status = document.getElementById('connection-status');
    if (status) {
        status.textContent = 'Connected ✅';
        status.classList.add('connected');
    }
});

socket.on('disconnect', function() {
    console.log('Socket disconnected');
    const status = document.getElementById('connection-status');
    if (status) {
        status.textContent = 'Disconnected';
        status.classList.remove('connected');
    }
});

socket.on('connect_error', function(error) {
    console.error('Connection error:', error);
    const status = document.getElementById('connection-status');
    if (status) {
        status.textContent = 'Connection Error';
        status.classList.remove('connected');
    }
});

// Setup chat functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create connection status element if not exists
    if (!document.getElementById('connection-status')) {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'connection-status';
        statusDiv.textContent = socket.connected ? 'Connected ✅' : 'Connecting...';
        if (socket.connected) statusDiv.classList.add('connected');
        document.body.appendChild(statusDiv);
    }
    
    // Get DOM elements
    const messageContainer = document.getElementById('message-container');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    
    // Add welcome message if container is empty
    if (messageContainer && messageContainer.children.length === 0) {
        addMessageToChat('Minerva', 'Hello! I\'m Minerva. How can I help you today?');
    }
    
    // Message handlers - properly log all events for debugging
    socket.on('response', function(message) {
        console.log('Response received:', message);
        addMessageToChat('Minerva', message);
        // Remove typing indicator if present
        document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
    });
    
    socket.on('typing_indicator', function(data) {
        console.log('Typing indicator:', data);
        if (data.status === 'typing') {
            removeTypingIndicators();
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.textContent = 'Minerva is typing...';
            messageContainer.appendChild(typingDiv);
            messageContainer.scrollTop = messageContainer.scrollHeight;
        } else {
            removeTypingIndicators();
        }
    });
    
    socket.on('error', function(data) {
        console.error('Server error:', data);
        addMessageToChat('System', 'Error: ' + (data.message || 'Unknown error'), 'error-message');
        removeTypingIndicators();
    });
    
    socket.on('ai_response', function(data) {
        console.log('AI response received:', data);
        const message = data.message || 'No response content';
        addMessageToChat('Minerva', message);
        removeTypingIndicators();
    });
    
    // Catch all other events for debugging
    socket.onAny((event, ...args) => {
        console.log(`Received event: ${event}`, args);
    });
    
    // Form submission
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            
            if (message) {
                console.log('Sending message:', message);
                
                // Add user message to the chat
                addMessageToChat('You', message, 'user-message');
                
                // Clear input
                messageInput.value = '';
                
                // Add typing indicator
                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing-indicator';
                typingDiv.textContent = 'Minerva is thinking...';
                messageContainer.appendChild(typingDiv);
                messageContainer.scrollTop = messageContainer.scrollHeight;
                
                // Send message to server with different event names to catch all possibilities
                socket.emit('user_message', {
                    message: message,
                    session_id: getSessionId(),
                    model: 'default'
                });
            }
        });
    } else {
        console.error('Chat form not found');
    }
    
    // Helper functions
    function addMessageToChat(sender, message, className = '') {
        if (!messageContainer) {
            console.error('Message container not found');
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ' + (className || (sender === 'Minerva' ? 'bot-message' : ''));
        
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="sender">${sender}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${message}</div>
        `;
        
        messageContainer.appendChild(messageDiv);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    function removeTypingIndicators() {
        document.querySelectorAll('.typing-indicator').forEach(el => el.remove());
    }
    
    function getSessionId() {
        let sessionId = localStorage.getItem('minerva_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Date.now();
            localStorage.setItem('minerva_session_id', sessionId);
        }
        return sessionId;
    }
}); 