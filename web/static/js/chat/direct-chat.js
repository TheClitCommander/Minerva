/**
 * Direct Chat Implementation
 * A simplified, reliable implementation of the Minerva chat interface
 * Uses the ThinkTankConnection class for reliable API connectivity
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Direct Chat implementation');
    
    // Create or ensure chat container exists
    ensureChatInterface();
    
    // Initialize Think Tank connection
    const thinkTank = new ThinkTankConnection({
        apiUrl: 'http://localhost:7070/api/think-tank',
        mockUrl: 'http://localhost:8080/api/think-tank-mock',
        localUrl: '/api/think-tank-mock',
        messagesContainer: document.getElementById('chat-history'),
        statusIndicator: document.getElementById('connection-status')
    });
    
    // DOM Elements - get after ensuring they exist
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    
    // Event Listeners
    if (chatInput && sendButton) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Function to send message
    async function sendMessage() {
        if (!chatInput || !chatHistory) {
            console.error('Chat interface elements missing');
            return;
        }
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Clear input
        chatInput.value = '';
        
        // Add user message to chat
        addUserMessage(message);
        
        // Send to Think Tank
        const response = await thinkTank.sendMessage(message);
        
        if (response) {
            // Add bot response to chat
            addBotMessage(response.response, response.model_info);
        }
    }
    
    // Add user message to chat
    function addUserMessage(message) {
        if (!chatHistory) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-text">${formatMessage(message)}</div>
                <div class="message-time">${getCurrentTime()}</div>
            </div>
        `;
        
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Store in memory if window.minervaMemory exists
        if (window.minervaMemory) {
            window.minervaMemory.push({
                role: 'user',
                content: message,
                timestamp: Date.now()
            });
        }
    }
    
    // Add bot message to chat
    function addBotMessage(message, modelInfo) {
        if (!chatHistory) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        
        // Format model info if available
        let modelInfoHtml = '';
        if (modelInfo && modelInfo.models && modelInfo.models.length > 0) {
            modelInfoHtml = `
                <div class="model-info">
                    <div class="model-info-label">Models:</div>
                    <div class="model-contribution">
                        ${modelInfo.models.map(model => 
                            `<span class="model-tag" title="${model.name}: ${model.contribution}%">
                                ${model.name.split('-')[0]} ${model.contribution}%
                            </span>`
                        ).join('')}
                    </div>
                </div>
            `;
        }
        
        messageElement.innerHTML = `
            <div class="message-content">
                <div class="message-text">${formatMessage(message)}</div>
                <div class="message-time">${getCurrentTime()}</div>
                ${modelInfoHtml}
            </div>
        `;
        
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Store in memory if window.minervaMemory exists
        if (window.minervaMemory) {
            window.minervaMemory.push({
                role: 'assistant',
                content: message,
                timestamp: Date.now(),
                model_info: modelInfo
            });
        }
    }
    
    // Add system message to chat
    function addSystemMessage(message, type = 'info') {
        if (!chatHistory) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message system ${type}`;
        messageElement.textContent = message;
        
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Show typing indicator
    window.showTypingIndicator = function() {
        if (!chatHistory) return;
        
        // Remove existing typing indicators
        const existingIndicators = chatHistory.querySelectorAll('.typing-indicator');
        existingIndicators.forEach(el => el.remove());
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message bot-message typing-indicator';
        typingIndicator.innerHTML = `
            <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        
        chatHistory.appendChild(typingIndicator);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };
    
    // Hide typing indicator
    window.hideTypingIndicator = function() {
        if (!chatHistory) return;
        
        const typingIndicators = chatHistory.querySelectorAll('.typing-indicator');
        typingIndicators.forEach(indicator => {
            indicator.remove();
        });
    };
    
    // Format message (handle markdown, links, code, etc.)
    function formatMessage(text) {
        if (!text) return '';
        
        // 1. Escape HTML
        let formatted = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // 2. Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        formatted = formatted.replace(urlRegex, '<a href="$1" target="_blank">$1</a>');
        
        // 3. Handle code blocks
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // 4. Handle inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // 5. Convert new lines to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        return formatted;
    }
    
    // Get current time in HH:MM format
    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const mins = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${mins}`;
    }
    
    // Init memory if not exists
    if (!window.minervaMemory) {
        window.minervaMemory = [];
        console.log('Initialized minervaMemory');
    }
    
    // Function to ensure chat interface exists
    function ensureChatInterface() {
        console.log('Ensuring chat interface exists');
        
        // Check if floating chat container exists
        let chatContainer = document.getElementById('floating-chat-container');
        
        // If not found, create it
        if (!chatContainer) {
            console.log('Creating floating chat container');
            chatContainer = document.createElement('div');
            chatContainer.id = 'floating-chat-container';
            chatContainer.className = 'chat-container floating-chat cosmic-theme';
            
            // Style the container
            Object.assign(chatContainer.style, {
                position: 'fixed',
                bottom: '20px',
                right: '20px',
                width: '350px',
                maxHeight: '500px',
                backgroundColor: 'rgba(26, 26, 46, 0.85)',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                flexDirection: 'column',
                zIndex: '1000',
                overflow: 'hidden',
                transition: 'all 0.3s ease'
            });
            
            // Create chat header
            const chatHeader = document.createElement('div');
            chatHeader.className = 'chat-header';
            chatHeader.innerHTML = `
                <h3>Minerva Assistant</h3>
                <div class="chat-controls">
                    <span id="connection-status" class="connection-status">Initializing...</span>
                    <button class="minimize-button">▼</button>
                    <button class="close-button">✕</button>
                </div>
            `;
            
            // Style header
            Object.assign(chatHeader.style, {
                padding: '10px',
                backgroundColor: 'rgba(74, 107, 223, 0.7)',
                color: 'white',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                cursor: 'move'
            });
            
            // Create chat history
            const chatHistory = document.createElement('div');
            chatHistory.id = 'chat-history';
            chatHistory.className = 'chat-history';
            
            // Style chat history
            Object.assign(chatHistory.style, {
                flex: '1',
                overflowY: 'auto',
                padding: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                maxHeight: '350px'
            });
            
            // Create chat input area
            const chatInputArea = document.createElement('div');
            chatInputArea.className = 'chat-input-area';
            chatInputArea.innerHTML = `
                <textarea id="chat-input" placeholder="Ask me anything..."></textarea>
                <button id="send-button">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            `;
            
            // Style input area
            Object.assign(chatInputArea.style, {
                display: 'flex',
                padding: '10px',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                backgroundColor: 'rgba(30, 30, 60, 0.7)'
            });
            
            // Append all elements
            chatContainer.appendChild(chatHeader);
            chatContainer.appendChild(chatHistory);
            chatContainer.appendChild(chatInputArea);
            
            // Add to document
            document.body.appendChild(chatContainer);
            
            // Add system welcome message
            setTimeout(() => {
                const welcomeMsg = document.createElement('div');
                welcomeMsg.className = 'message system info';
                welcomeMsg.textContent = 'Welcome to Minerva Assistant. How can I help you today?';
                chatHistory.appendChild(welcomeMsg);
            }, 500);
            
            // Make chat draggable
            makeChatDraggable(chatContainer, chatHeader);
            
            // Add minimize/close functionality
            const minimizeBtn = chatHeader.querySelector('.minimize-button');
            const closeBtn = chatHeader.querySelector('.close-button');
            
            if (minimizeBtn) {
                minimizeBtn.addEventListener('click', () => {
                    chatHistory.style.display = chatHistory.style.display === 'none' ? 'flex' : 'none';
                    chatInputArea.style.display = chatInputArea.style.display === 'none' ? 'flex' : 'none';
                    minimizeBtn.textContent = minimizeBtn.textContent === '▼' ? '▲' : '▼';
                });
            }
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    chatContainer.style.display = 'none';
                });
            }
        } else {
            console.log('Floating chat container already exists');
        }
    }
    
    // Make the chat draggable
    function makeChatDraggable(element, handle) {
        if (!element || !handle) return;
        
        let isDragging = false;
        let offsetX, offsetY;
        
        handle.addEventListener('mousedown', function(e) {
            if (e.target.closest('.minimize-button') || e.target.closest('.close-button')) {
                return; // Don't start drag if clicking on buttons
            }
            
            isDragging = true;
            offsetX = e.clientX - element.getBoundingClientRect().left;
            offsetY = e.clientY - element.getBoundingClientRect().top;
            
            // Prevent text selection during drag
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            
            const newX = e.clientX - offsetX;
            const newY = e.clientY - offsetY;
            
            // Get viewport boundaries
            const maxX = window.innerWidth - element.offsetWidth;
            const maxY = window.innerHeight - element.offsetHeight;
            
            // Set new position within viewport boundaries
            element.style.left = Math.max(0, Math.min(newX, maxX)) + 'px';
            element.style.top = Math.max(0, Math.min(newY, maxY)) + 'px';
            element.style.right = 'auto';
            element.style.bottom = 'auto';
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
        });
    }
    
    // Add welcome message
    addSystemMessage('Chat initialized and connected to Think Tank API');
    
    // Export functions to window
    window.sendDirectChatMessage = sendMessage;
    window.addUserMessage = addUserMessage;
    window.addBotMessage = addBotMessage;
    window.addSystemMessage = addSystemMessage;
    
    console.log('Direct Chat implementation initialized successfully');
});
