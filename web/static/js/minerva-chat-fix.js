// Minerva Chat Fix - Ensures proper Socket.IO connectivity
(function() {
    console.log('🔧 Minerva Chat Fix Loading...');
    
    document.addEventListener('DOMContentLoaded', function() {
        // Find chat elements
        const chatOrb = document.getElementById('chat-orb');
        const chatPanel = document.getElementById('chat-panel');
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-chat-btn');
        
        if (!chatOrb || !chatPanel) {
            console.error('❌ Chat elements not found');
            return;
        }
        
        console.log('✅ Chat elements found, initializing Socket.IO');
        
        // Initialize Socket.IO with compatible settings
        let socket;
        try {
            socket = io({
                forceNew: true,
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionAttempts: 5
            });
            
            // Store in global window for debugging
            window.minervaSocket = socket;
            
            // Socket event handlers
            socket.on('connect', function() {
                console.log('✅ Socket.IO connected successfully');
                showStatus('Connected', 'success');
                
                // Enable chat orb
                chatOrb.style.opacity = '1';
                chatOrb.style.cursor = 'pointer';
            });
            
            socket.on('connect_error', function(error) {
                console.error('❌ Socket.IO connection error:', error);
                showStatus('Connection Error', 'error');
            });
            
            socket.on('disconnect', function() {
                console.warn('⚠️ Socket.IO disconnected');
                showStatus('Disconnected', 'warning');
            });
            
            // Message handler - handles any message format
            socket.on('chat_response', function(data) {
                console.log('📨 Message received:', data);
                const message = data.message || data.text || (typeof data === 'string' ? data : JSON.stringify(data));
                addMessage(message, 'bot');
            });
            
            // Legacy handlers for compatibility
            socket.on('chat_reply', function(data) {
                console.log('📨 Legacy chat_reply received:', data);
                const message = data.text || data.message || (typeof data === 'string' ? data : JSON.stringify(data));
                addMessage(message, 'bot');
            });
            
            socket.on('response', function(data) {
                console.log('📨 Legacy response received:', data);
                const message = data.text || data.message || (typeof data === 'string' ? data : JSON.stringify(data));
                addMessage(message, 'bot');
            });
            
            // Chat orb click handler
            chatOrb.addEventListener('click', function() {
                console.log('🖱️ Chat orb clicked');
                chatPanel.classList.toggle('active');
                
                // If first time opening, send a welcome message
                if (chatMessages && chatMessages.children.length === 0) {
                    socket.emit('debug', { message: 'Chat panel opened' });
                }
            });
            
            // Send button click handler
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
                console.log('📤 Sending message:', message);
                
                // Add to chat
                addMessage(message, 'user');
                
                // Send to server - try multiple event names for compatibility
                socket.emit('chat_message', { message: message });
                
                // Clear input
                chatInput.value = '';
            }
            
        } catch (e) {
            console.error('❌ Error initializing Socket.IO:', e);
            showStatus('Initialization Error', 'error');
        }
        
        // Show status message
        function showStatus(message, type) {
            const statusDiv = document.getElementById('chat-status');
            
            if (!statusDiv) {
                // Create status indicator if it doesn't exist
                const newStatus = document.createElement('div');
                newStatus.id = 'chat-status';
                newStatus.style.position = 'fixed';
                newStatus.style.bottom = '170px';
                newStatus.style.right = '30px';
                newStatus.style.padding = '8px 15px';
                newStatus.style.borderRadius = '4px';
                newStatus.style.fontSize = '14px';
                newStatus.style.zIndex = '1000';
                newStatus.style.transition = 'opacity 0.5s ease';
                document.body.appendChild(newStatus);
                
                // Fade out after 5 seconds
                setTimeout(() => {
                    newStatus.style.opacity = '0.3';
                }, 5000);
                
                // Show on hover
                newStatus.addEventListener('mouseenter', function() {
                    this.style.opacity = '1';
                });
                
                newStatus.addEventListener('mouseleave', function() {
                    this.style.opacity = '0.3';
                });
                
                setStatusStyle(newStatus, type);
                newStatus.textContent = message;
            } else {
                setStatusStyle(statusDiv, type);
                statusDiv.textContent = message;
            }
        }
        
        // Set status indicator style based on type
        function setStatusStyle(element, type) {
            switch(type) {
                case 'success':
                    element.style.background = 'rgba(40, 167, 69, 0.8)';
                    break;
                case 'error':
                    element.style.background = 'rgba(220, 53, 69, 0.8)';
                    break;
                case 'warning':
                    element.style.background = 'rgba(255, 193, 7, 0.8)';
                    element.style.color = '#333';
                    break;
                default:
                    element.style.background = 'rgba(0, 0, 0, 0.7)';
            }
            element.style.color = type === 'warning' ? '#333' : 'white';
        }
        
        // Add message to chat
        function addMessage(text, sender) {
            if (!chatMessages) return;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            const messageContent = document.createElement('div');
            messageContent.className = 'message-content';
            messageContent.textContent = text;
            
            const timestamp = document.createElement('div');
            timestamp.className = 'timestamp';
            
            // Format time as HH:MM
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
        
        console.log('✅ Minerva chat fix initialized successfully');
    });
})(); 