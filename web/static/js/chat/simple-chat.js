/**
 * Simple Chat Implementation
 * A clean, direct implementation that connects to the Think Tank API
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Simple Chat');
    
    // Create chat container if it doesn't exist
    ensureChatInterface();
    
    // DOM Elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const chatContainer = document.getElementById('floating-chat-container');
    
    // Event listeners
    if (chatInput && sendButton) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
    } else {
        console.error('Chat input or send button not found!');
    }
    
    // Send message function
    async function sendMessage() {
        if (!chatInput || !chatHistory) {
            console.error('Chat elements missing');
            return;
        }
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Clear input
        chatInput.value = '';
        
        // Add user message to chat
        addUserMessage(message);
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send message to Think Tank API
            const response = await window.thinkTankAPI.sendMessage(message);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            if (response && response.response) {
                addBotMessage(response.response, response.model_info);
            } else {
                throw new Error('Invalid response from API');
            }
        } catch (error) {
            console.error('Error in sendMessage:', error);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Show error message
            addSystemMessage('Error connecting to Think Tank API: ' + error.message, 'error');
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
                    <span class="model-info-label">Models: </span>
                    ${modelInfo.models.map(model => 
                        `<span class="model-tag" title="${model.name}: ${model.contribution}%">
                            ${model.name.split('-')[0]} ${model.contribution}%
                        </span>`
                    ).join(' ')}
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
    }
    
    // Add system message
    function addSystemMessage(message, type = 'info') {
        if (!chatHistory) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message system ${type}`;
        messageElement.textContent = message;
        
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Show typing indicator
    function showTypingIndicator() {
        if (!chatHistory) return;
        
        // Remove existing indicators
        hideTypingIndicator();
        
        const indicatorElement = document.createElement('div');
        indicatorElement.className = 'message bot-message typing-indicator';
        indicatorElement.id = 'typing-indicator';
        indicatorElement.innerHTML = `
            <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        
        chatHistory.appendChild(indicatorElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const indicators = document.querySelectorAll('.typing-indicator');
        indicators.forEach(indicator => indicator.remove());
    }
    
    // Format message (convert links, code, etc.)
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
    
    // Get current time (HH:MM)
    function getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    // Make the chat draggable
    function makeDraggable(element, handle) {
        if (!element || !handle) return;
        
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        handle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            
            // Get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            
            // Calculate the new cursor position
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            // Set the element's new position
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
        }
        
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
    
    // Ensure chat interface exists
    function ensureChatInterface() {
        let chatContainer = document.getElementById('floating-chat-container');
        
        if (!chatContainer) {
            console.log('Creating chat container');
            
            // Create container
            chatContainer = document.createElement('div');
            chatContainer.id = 'floating-chat-container';
            chatContainer.className = 'chat-container floating-chat';
            
            // Style container
            Object.assign(chatContainer.style, {
                position: 'fixed',
                bottom: '20px',
                right: '20px',
                width: '350px',
                maxHeight: '500px',
                backgroundColor: 'rgba(25, 25, 45, 0.9)',
                borderRadius: '10px',
                boxShadow: '0 5px 15px rgba(0, 0, 0, 0.3)',
                zIndex: '1000',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
            });
            
            // Create header
            const header = document.createElement('div');
            header.className = 'chat-header';
            header.innerHTML = `
                <h3>Minerva Assistant</h3>
                <div class="chat-controls">
                    <button class="minimize-button">−</button>
                    <button class="close-button">×</button>
                </div>
            `;
            
            // Style header
            Object.assign(header.style, {
                padding: '10px 15px',
                backgroundColor: '#3a5bcf',
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
                maxHeight: '350px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
            });
            
            // Create chat input area
            const inputArea = document.createElement('div');
            inputArea.className = 'chat-input-area';
            inputArea.innerHTML = `
                <textarea id="chat-input" placeholder="Type your message..."></textarea>
                <button id="send-button">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            `;
            
            // Style input area
            Object.assign(inputArea.style, {
                display: 'flex',
                padding: '10px',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)'
            });
            
            // Add all elements to container
            chatContainer.appendChild(header);
            chatContainer.appendChild(chatHistory);
            chatContainer.appendChild(inputArea);
            
            // Add container to body
            document.body.appendChild(chatContainer);
            
            // Make chat draggable
            makeDraggable(chatContainer, header);
            
            // Add functional controls
            const minimizeButton = header.querySelector('.minimize-button');
            const closeButton = header.querySelector('.close-button');
            
            minimizeButton.addEventListener('click', function() {
                const isMinimized = chatHistory.style.display === 'none';
                chatHistory.style.display = isMinimized ? 'flex' : 'none';
                inputArea.style.display = isMinimized ? 'flex' : 'none';
                minimizeButton.textContent = isMinimized ? '−' : '+';
            });
            
            closeButton.addEventListener('click', function() {
                chatContainer.style.display = 'none';
            });
            
            // Add welcome message
            setTimeout(() => {
                addSystemMessage('Welcome to Minerva Assistant. I\'m connected to the Think Tank API and ready to help.');
            }, 500);
        }
    }
    
    // Check API availability on load and show welcome message
    setTimeout(() => {
        addSystemMessage('Welcome to Minerva Assistant. I\'m connected to the Think Tank API and ready to help.', 'info');
        
        // Check API availability silently
        window.thinkTankAPI.checkAvailability()
            .then(available => {
                if (!available) {
                    console.warn('Think Tank API availability check failed.');
                }
            });
    }, 500);
    
    // Add CSS styles for the chat
    addChatStyles();
    
    // Function to add necessary CSS
    function addChatStyles() {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Chat container styles */
            .floating-chat {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
                font-size: 14px;
                line-height: 1.4;
                transition: all 0.3s ease;
            }
            
            /* Chat messages */
            .message {
                padding: 10px;
                border-radius: 8px;
                max-width: 85%;
                margin-bottom: 8px;
                word-wrap: break-word;
            }
            
            .user-message {
                background-color: rgba(74, 107, 223, 0.2);
                align-self: flex-end;
                margin-left: auto;
            }
            
            .bot-message {
                background-color: rgba(45, 45, 65, 0.8);
                align-self: flex-start;
                margin-right: auto;
            }
            
            .system {
                background-color: rgba(100, 100, 100, 0.2);
                font-style: italic;
                text-align: center;
                max-width: 100%;
                font-size: 0.9em;
                padding: 5px 10px;
            }
            
            .error {
                background-color: rgba(200, 50, 50, 0.2);
            }
            
            .info {
                background-color: rgba(50, 100, 200, 0.2);
            }
            
            .warning {
                background-color: rgba(200, 150, 50, 0.2);
            }
            
            /* Message content */
            .message-content {
                position: relative;
            }
            
            .message-text {
                margin-bottom: 5px;
            }
            
            .message-time {
                font-size: 0.8em;
                opacity: 0.7;
                text-align: right;
            }
            
            /* Model info */
            .model-info {
                font-size: 0.8em;
                margin-top: 5px;
                opacity: 0.7;
            }
            
            .model-tag {
                display: inline-block;
                padding: 2px 5px;
                background-color: rgba(60, 60, 70, 0.5);
                border-radius: 3px;
                margin-right: 3px;
            }
            
            /* Input area */
            #chat-input {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 5px;
                resize: none;
                background-color: rgba(60, 60, 80, 0.5);
                color: white;
                height: 20px;
                max-height: 100px;
                min-height: 20px;
            }
            
            #chat-input:focus {
                outline: none;
                box-shadow: 0 0 0 2px rgba(74, 107, 223, 0.5);
            }
            
            #send-button {
                margin-left: 10px;
                background-color: #3a5bcf;
                border: none;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
            }
            
            #send-button:hover {
                background-color: #4a6bdf;
            }
            
            /* Typing indicator */
            .typing-indicator {
                background-color: transparent !important;
                padding: 5px !important;
            }
            
            .typing-dots {
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .dot {
                width: 8px;
                height: 8px;
                background-color: #aaa;
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }
            
            .dot:nth-child(2) {
                animation-delay: 0.2s;
            }
            
            .dot:nth-child(3) {
                animation-delay: 0.4s;
            }
            
            @keyframes pulse {
                0%, 50%, 100% { transform: scale(1); opacity: 0.7; }
                25% { transform: scale(1.2); opacity: 1; }
            }
            
            /* Button styles */
            .minimize-button, .close-button {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
            }
            
            .minimize-button:hover, .close-button:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            /* Code formatting */
            .message pre {
                background-color: rgba(30, 30, 40, 0.5);
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                margin: 5px 0;
            }
            
            .message code {
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 0.9em;
                background-color: rgba(30, 30, 40, 0.5);
                padding: 2px 4px;
                border-radius: 3px;
            }
        `;
        
        document.head.appendChild(styleElement);
    }
    
    // Expose functions to window
    window.minervaChat = {
        sendMessage,
        addUserMessage,
        addBotMessage,
        addSystemMessage,
        showTypingIndicator,
        hideTypingIndicator
    };
    
    console.log('Simple Chat initialized successfully');
});
