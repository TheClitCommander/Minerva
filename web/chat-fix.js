// Chat orb fix for Minerva
document.addEventListener('DOMContentLoaded', function() {
    console.log('Chat fix loaded');
    
    // Find the chat orb and panel
    const chatOrb = document.getElementById('chat-orb');
    const chatPanel = document.getElementById('chat-panel');
    const messages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-chat-btn');
    
    if (!chatOrb || !chatPanel) {
        console.error('Chat elements not found');
        return;
    }
    
    console.log('Chat elements found, setting up handlers');
    
    // Make the chat orb clickable
    chatOrb.style.cursor = 'pointer';
    chatOrb.style.opacity = '1';
    
    // Connect to Socket.IO with older compatible version
    let socket;
    try {
        // Basic initialization with compatibility
        socket = io({
            transports: ['websocket', 'polling'],
            forceNew: true,
            reconnection: true
        });
        
        // Store in window for debugging
        window.minervaSocket = socket;
        
        // Listen for connection events
        socket.on('connect', function() {
            console.log('Socket.IO connected');
            showStatus('Socket.IO Connected', 'success');
        });
        
        socket.on('connect_error', function(error) {
            console.error('Socket.IO connection error:', error);
            showStatus('Connection Error', 'error');
        });
        
        // Listen for messages
        socket.on('chat_response', function(data) {
            addMessage(data.message || data, 'bot');
        });
    } catch (e) {
        console.error('Error connecting to Socket.IO:', e);
    }
    
    // Add click handler to chat orb
    chatOrb.addEventListener('click', function() {
        console.log('Chat orb clicked');
        chatPanel.classList.toggle('active');
    });
    
    // Add send message functionality
    if (sendButton && chatInput) {
        sendButton.addEventListener('click', sendMessage);
        
        // Also handle Enter key
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Send message function
    function sendMessage() {
        if (!chatInput.value.trim()) return;
        
        const message = chatInput.value.trim();
        console.log('Sending message:', message);
        
        // Add message to chat
        addMessage(message, 'user');
        
        // Send to server
        if (socket && socket.connected) {
            socket.emit('chat_message', { message });
        } else {
            console.error('Socket not connected, cannot send message');
            addMessage('Cannot send message: Socket.IO not connected', 'system');
        }
        
        // Clear input
        chatInput.value = '';
    }
    
    // Add message to chat panel
    function addMessage(text, sender) {
        if (!messages) return;
        
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
        messages.appendChild(messageDiv);
        
        // Scroll to bottom
        messages.scrollTop = messages.scrollHeight;
    }
    
    // Show status message
    function showStatus(message, type) {
        // Create status div
        const statusDiv = document.createElement('div');
        statusDiv.style.position = 'fixed';
        statusDiv.style.bottom = '10px';
        statusDiv.style.right = '10px';
        statusDiv.style.padding = '8px 15px';
        statusDiv.style.borderRadius = '4px';
        statusDiv.style.zIndex = '9999';
        
        // Set color based on type
        if (type === 'success') {
            statusDiv.style.backgroundColor = 'rgba(40, 167, 69, 0.9)';
        } else if (type === 'error') {
            statusDiv.style.backgroundColor = 'rgba(220, 53, 69, 0.9)';
        } else {
            statusDiv.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
        }
        
        statusDiv.style.color = 'white';
        statusDiv.textContent = message;
        
        document.body.appendChild(statusDiv);
        
        // Remove after 3 seconds
        setTimeout(function() {
            statusDiv.style.opacity = '0';
            statusDiv.style.transition = 'opacity 0.5s ease';
            
            setTimeout(function() {
                if (statusDiv.parentNode) {
                    document.body.removeChild(statusDiv);
                }
            }, 500);
        }, 3000);
    }
}); 