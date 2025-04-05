/**
 * Minerva Chat Bridge
 * 
 * This module creates a bridge between different chat implementations:
 * - FloatingChatComponent (floating-chat.js)
 * - ChatSimple (chat-simple.js)
 * - Chat UI Components
 * 
 * It ensures messages are properly routed between components and provides
 * a unified interface for conversation memory and API connectivity.
 */

// Create global MinervaChat namespace if it doesn't exist
window.MinervaChat = window.MinervaChat || {};

// Chat Bridge constructor
class ChatBridge {
    constructor(options = {}) {
        this.initialized = false;
        this.options = Object.assign({
            debug: false,
            useMemory: true,
            apiUrl: '/api/think-tank'
        }, options);
        
        // Track loaded components
        this.components = {
            floatingChat: null,  // FloatingChatComponent
            chatSimple: null,    // chat-simple.js
            chatCore: null       // Any other chat core
        };
        
        // Element references
        this.elements = {
            chatInput: null,
            sendButton: null,
            chatMessages: null
        };
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            // DOM already loaded
            this.init();
        }
        
        // Listen for delayed component initialization
        window.addEventListener('minerva_component_ready', (event) => {
            if (event.detail && event.detail.component) {
                this.connectComponent(event.detail.component, event.detail.instance);
            }
        });
        
        // Make this instance globally available
        window.MinervaChat.Bridge = this;
        
        // Debug logging
        this.log('Chat Bridge created');
    }
    
    // Initialize the bridge
    init() {
        this.log('Initializing Chat Bridge');
        
        // Listen for API connection events from api-connector.js
        window.addEventListener('minerva_api_connected', (event) => {
            if (event.detail && event.detail.endpoint) {
                this.log('API connected event received with endpoint: ' + event.detail.endpoint);
                this.options.apiUrl = event.detail.endpoint;
            }
        });
        
        // First check for existing components
        this.detectExistingComponents();
        
        // Force creation of UI elements if they're not found
        if (!this.elements.chatInput || !this.elements.sendButton || !this.elements.chatMessages) {
            this.log('Critical UI elements not found, creating fallback interface');
            this.createFallbackInterface();
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initialize conversation management
        this.initConversationManagement();
        
        // Check for API availability using the new connector
        if (window.minervaAPI) {
            this.log('Found minervaAPI connector');
            if (window.minervaAPI.apiEndpoint) {
                this.log('Using API endpoint from connector: ' + window.minervaAPI.apiEndpoint);
                this.options.apiUrl = window.minervaAPI.apiEndpoint;
            }
        } else {
            // Try to set the API URL to port 8090 if it's not already set
            if (!this.options.apiUrl.includes('8090')) {
                const port8090Url = 'http://localhost:8090/api/think-tank';
                this.log('No API connector found, trying port 8090: ' + port8090Url);
                this.options.apiUrl = port8090Url;
            }
        }
        
        // Register with window as ready
        this.initialized = true;
        window.dispatchEvent(new CustomEvent('minerva_chat_bridge_ready', {
            detail: { instance: this }
        }));
        
        this.log('Chat Bridge initialized successfully with UI elements:', this.elements);
    }
    
    // Connect a component to the bridge
    connectComponent(componentName, instance) {
        this.log(`Connecting component: ${componentName}`);
        
        if (componentName === 'floatingChat') {
            this.components.floatingChat = instance || window.floatingChat;
            this.log('Connected floating chat component', this.components.floatingChat);
            
            // Update element references
            if (this.components.floatingChat) {
                this.elements.chatInput = this.components.floatingChat.chatInput || this.elements.chatInput;
                this.elements.sendButton = this.components.floatingChat.sendButton || this.elements.sendButton;
                this.elements.chatMessages = this.components.floatingChat.chatMessages || this.elements.chatMessages;
            }
        } else if (componentName === 'chatSimple') {
            this.components.chatSimple = instance || window;
            this.log('Connected chat simple component', this.components.chatSimple);
            
            // Update element references from chat-simple.js globals
            if (window.chatInput) this.elements.chatInput = window.chatInput;
            if (window.chatSendButton) this.elements.sendButton = window.chatSendButton;
        } else if (componentName === 'chatCore') {
            this.components.chatCore = instance;
            this.log('Connected chat core component', this.components.chatCore);
        }
        
        // Update UI references after connecting component
        this.updateElementReferences();
    }
    
    // Detect existing components already loaded
    detectExistingComponents() {
        this.log('Detecting existing components');
        
        // Check for FloatingChatComponent
        if (window.floatingChat) {
            this.connectComponent('floatingChat', window.floatingChat);
        }
        
        // Check for chat-simple.js features
        if (typeof window.sendMessage === 'function' || 
            typeof window.sendMessageToAPI === 'function') {
            this.connectComponent('chatSimple', window);
        }
        
        // Update element references as a fallback
        this.updateElementReferences();
    }
    
    // Update references to DOM elements
    updateElementReferences() {
        // Only update missing elements
        if (!this.elements.chatInput) {
            this.elements.chatInput = document.getElementById('chat-input') || 
                document.querySelector('.chat-input') || 
                document.querySelector('textarea[placeholder*="message"]') ||
                document.querySelector('input[placeholder*="message"]') ||
                document.querySelector('textarea') ||
                document.querySelector('input[type="text"]');
        }
        
        if (!this.elements.sendButton) {
            this.elements.sendButton = document.getElementById('send-button') || 
                document.querySelector('.send-button') || 
                document.querySelector('button[aria-label="Send"]') ||
                document.querySelector('button.chat-send') ||
                document.querySelector('.floating-chat button') ||
                document.querySelector('button');
        }
        
        if (!this.elements.chatMessages) {
            this.elements.chatMessages = document.getElementById('chat-box') || 
                document.querySelector('.chat-messages') || 
                document.getElementById('floating-chat-messages') ||
                document.querySelector('.floating-chat-container .chat-messages') ||
                document.querySelector('.chat-container');
        }
        
        this.log('Element references updated', this.elements);
    }
    
    // Create a fallback interface if needed
    createFallbackInterface() {
        this.log('Checking if fallback chat interface is needed');
        
        // Check if any other chat interfaces already exist
        const existingInterfaces = document.querySelectorAll('.chat-container, .floating-chat, #minerva-chat');
        if (existingInterfaces.length > 0) {
            this.log('Existing chat interface detected, not creating fallback', existingInterfaces);
            return;
        }
        
        this.log('Creating fallback chat interface');
        
        // Create container if it doesn't exist
        let chatContainer = document.getElementById('fallback-chat-container');
        if (!chatContainer) {
            chatContainer = document.createElement('div');
            chatContainer.id = 'fallback-chat-container';
            chatContainer.className = 'chat-container';
            chatContainer.style.position = 'fixed';
            chatContainer.style.bottom = '20px';
            chatContainer.style.right = '20px';
            chatContainer.style.width = '350px';
            chatContainer.style.maxHeight = '500px';
            chatContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            chatContainer.style.backdropFilter = 'blur(8px)';
            chatContainer.style.webkitBackdropFilter = 'blur(8px)';
            chatContainer.style.borderRadius = '10px';
            chatContainer.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
            chatContainer.style.display = 'flex';
            chatContainer.style.flexDirection = 'column';
            chatContainer.style.overflow = 'hidden';
            chatContainer.style.zIndex = '9999';
            document.body.appendChild(chatContainer);
        }
        
        // Create chat header
        let chatHeader = chatContainer.querySelector('.chat-header');
        if (!chatHeader) {
            chatHeader = document.createElement('div');
            chatHeader.className = 'chat-header';
            chatHeader.style.padding = '10px';
            chatHeader.style.backgroundColor = '#4a4a9e';
            chatHeader.style.color = 'white';
            chatHeader.style.fontWeight = 'bold';
            chatHeader.textContent = 'Minerva Chat';
            chatContainer.appendChild(chatHeader);
        }
        
        // Create messages area
        let chatMessages = chatContainer.querySelector('.chat-messages');
        if (!chatMessages) {
            chatMessages = document.createElement('div');
            chatMessages.className = 'chat-messages';
            chatMessages.style.flex = '1';
            chatMessages.style.overflowY = 'auto';
            chatMessages.style.padding = '10px';
            chatMessages.style.height = '300px';
            chatContainer.appendChild(chatMessages);
            
            // Add welcome message
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'chat-message system-message';
            welcomeMsg.innerHTML = '<div class="message-content">Welcome to Minerva Chat. How can I help you today?</div>';
            welcomeMsg.style.margin = '5px 0';
            welcomeMsg.style.padding = '8px';
            welcomeMsg.style.borderRadius = '5px';
            welcomeMsg.style.backgroundColor = '#f0f0f0';
            chatMessages.appendChild(welcomeMsg);
        }
        
        // Create input area
        let inputContainer = chatContainer.querySelector('.chat-input-container');
        if (!inputContainer) {
            inputContainer = document.createElement('div');
            inputContainer.className = 'chat-input-container';
            inputContainer.style.display = 'flex';
            inputContainer.style.padding = '10px';
            inputContainer.style.borderTop = '1px solid #eee';
            chatContainer.appendChild(inputContainer);
            
            // Create input field
            const chatInput = document.createElement('input');
            chatInput.type = 'text';
            chatInput.className = 'chat-input';
            chatInput.placeholder = 'Type your message here...';
            chatInput.style.flex = '1';
            chatInput.style.padding = '8px';
            chatInput.style.border = '1px solid #ddd';
            chatInput.style.borderRadius = '5px';
            chatInput.style.marginRight = '10px';
            inputContainer.appendChild(chatInput);
            
            // Create send button
            const sendButton = document.createElement('button');
            sendButton.className = 'chat-send';
            sendButton.textContent = 'Send';
            sendButton.style.padding = '8px 15px';
            sendButton.style.backgroundColor = '#4a4a9e';
            sendButton.style.color = 'white';
            sendButton.style.border = 'none';
            sendButton.style.borderRadius = '5px';
            sendButton.style.cursor = 'pointer';
            inputContainer.appendChild(sendButton);
            
            // Store references
            this.elements.chatInput = chatInput;
            this.elements.sendButton = sendButton;
            this.elements.chatMessages = chatMessages;
            
            // Setup event listeners
            this.setupEventListeners();
        }
    }
    
    // Set up event listeners for messaging
    setupEventListeners() {
        // Listen for messages from FloatingChatComponent
        document.addEventListener('floatingChatMessage', (event) => {
            if (event.detail && event.detail.message) {
                this.sendMessage(event.detail.message);
            }
        });
        
        // Setup send button click handler
        if (this.elements.sendButton) {
            // Remove existing handlers to prevent duplicates
            this.elements.sendButton.removeEventListener('click', this._handleSendClick);
            
            // Store reference to bound handler
            this._handleSendClick = () => this.handleSendClick();
            this.elements.sendButton.addEventListener('click', this._handleSendClick);
        }
        
        // Setup input field key handler
        if (this.elements.chatInput) {
            // Remove existing handlers to prevent duplicates
            this.elements.chatInput.removeEventListener('keypress', this._handleKeyPress);
            
            // Store reference to bound handler
            this._handleKeyPress = (e) => this.handleKeyPress(e);
            this.elements.chatInput.addEventListener('keypress', this._handleKeyPress);
        }
    }
    
    // Handle send button click
    handleSendClick() {
        // Get message from input field
        const message = this.getMessage();
        if (!message) return;
        
        // Send the message
        this.sendMessage(message);
    }
    
    // Handle key press in input field
    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            
            // Get message from input field
            const message = this.getMessage();
            if (!message) return;
            
            // Send the message
            this.sendMessage(message);
        }
    }
    
    // Get message from input field
    getMessage() {
        // Make sure we have an input field
        if (!this.elements.chatInput) {
            this.updateElementReferences();
            if (!this.elements.chatInput) {
                this.log('No chat input found', null, 'error');
                return null;
            }
        }
        
        // Get message
        const message = this.elements.chatInput.value.trim();
        if (!message) return null;
        
        // Clear input field
        this.elements.chatInput.value = '';
        
        // Focus back on input
        this.elements.chatInput.focus();
        
        return message;
    }
    
    // Send message to API and display in UI
    sendMessage(message) {
        this.log(`Sending message: ${message}`);
        
        // Display user message
        this.displayMessage(message, 'user');
        
        // Save to conversation memory
        this.saveToConversationMemory(message, 'user');
        
        // Try chat-simple.js sendMessageToAPI first if available
        if (typeof window.sendMessageToAPI === 'function') {
            window.sendMessageToAPI(message);
            return;
        }
        
        // Otherwise handle API call ourselves
        this.sendMessageToAPI(message);
    }
    
    // Send message to API directly
    async sendMessageToAPI(message) {
        // Create typing indicator
        const typingIndicator = this.addTypingIndicator();
        
        // Try API connector first if available
        if (window.minervaAPI && typeof window.minervaAPI.sendMessage === 'function') {
            try {
                this.log('Using minervaAPI connector to send message');
                const response = await window.minervaAPI.sendMessage(message);
                
                // Remove typing indicator
                this.removeTypingIndicator(typingIndicator);
                
                if (response.error) {
                    this.log('Error from minervaAPI:', response.error, 'error');
                    return this.simulateResponse(message);
                }
                
                this.log('Response received from minervaAPI');
                return this.processAPIResponse(response);
            } catch (error) {
                this.log('Error using minervaAPI connector:', error, 'error');
                // Fall through to fallback approach
            }
        }
        
        // Get conversation ID from storage
        let conversationId = localStorage.getItem('minerva_conversation_id');
        if (!conversationId) {
            conversationId = this.generateUUID();
            localStorage.setItem('minerva_conversation_id', conversationId);
        }
        
        // Get API URL from storage or options, prioritize port 8090 as that's where our API is running
        const apiUrl = localStorage.getItem('minerva_api_url') || 
                       'http://localhost:8090/api/think-tank' || 
                       this.options.apiUrl || 
                       '/api/think-tank';
                       
        // Define list of fallback endpoints to try - prioritizing port 7070 where test server is running
        const endpoints = [
            // Primary target - port 7070 (test server)
            'http://localhost:7070/api/think-tank',
            'http://127.0.0.1:7070/api/think-tank',
            // Try port 8090
            'http://localhost:8090/api/think-tank',
            'http://127.0.0.1:8090/api/think-tank',
            apiUrl, // This might already be set by the API connector
            // Fallbacks to other common ports
            'http://localhost:8080/api/think-tank',
            'http://127.0.0.1:8080/api/think-tank',
            // Relative URLs (when running on same server)
            '/api/think-tank',
            '/api/chat',
            '/api/minerva/think'
        ];
        
        // Create a unique list of endpoints without duplicates
        const uniqueEndpoints = [...new Set(endpoints)];
        
        let allErrors = {};
        
        // Try each endpoint
        for (const endpoint of uniqueEndpoints) {
            try {
                this.log(`Trying endpoint: ${endpoint}`);
                
                // Make API request
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                        // Note: CORS headers are set by the server, not the client
                        // Client-side CORS headers in request don't work and can cause issues
                    },
                    mode: 'cors', // This is important for cross-origin requests
                    credentials: 'same-origin',
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });
                
                // Check response
                if (!response.ok) {
                    throw new Error(`API error: ${response.status} - ${response.statusText}`);
                }
                
                // Parse response
                const data = await response.json();
                
                // Remove typing indicator
                this.removeTypingIndicator(typingIndicator);
                
                // Save successful endpoint
                localStorage.setItem('minerva_api_url', endpoint);
                this.log(`Successful API call to ${endpoint}`);
                
                // Process response
                this.processAPIResponse(data);
                
                // Success, exit the loop
                return;
            } catch (error) {
                allErrors[endpoint] = error.message;
                this.log(`API error with ${endpoint}: ${error.message}`, error, 'warn');
                // Continue to next endpoint
            }
        }
        
        // All endpoints failed
        this.log('All API attempts failed:', allErrors, 'error');
        
        // Remove typing indicator
        this.removeTypingIndicator(typingIndicator);
        
        // Try to fall back to local response simulation
        this.simulateResponse(message);
    }
    
    // Simulate a response when APIs fail
    simulateResponse(message) {
        this.log('Simulating response for: ' + message);
        
        // Get conversation ID for context
        const conversationId = localStorage.getItem('minerva_conversation_id') || this.generateUUID();
        
        // Create context-aware responses that maintain conversation memory functionality
        const responses = [
            "I've processed your message and saved it to conversation memory. The connection to the server is currently limited, but I can still help you.",
            "Your message has been saved to this conversation. Due to server connectivity issues, I'm operating in limited mode, but core memory features are still working.",
            "I understand your message about '" + message.substring(0, 30) + (message.length > 30 ? '...' : '') + "'. This conversation is being remembered even though we're having server issues.",
            "Thanks for your input. While I'm having trouble connecting to the main server, I can still maintain our conversation memory and help you organize your thoughts.",
            "I've saved your message to this conversation. Would you like to convert this conversation to a project? That feature should work even with the current connection issues.",
            "Your ideas are being saved to this conversation. Despite connection issues, you can continue to build on this conversation and it will be preserved."
        ];
        
        // Choose a response based on message content and conversation history
        let responseIndex = Math.floor(Math.random() * responses.length);
        
        // Look for project-related keywords to provide relevant responses
        if (message.toLowerCase().includes('project') || message.toLowerCase().includes('convert')) {
            responseIndex = 4; // Use the project conversion response
            
            // Handle project conversion if explicitly requested
            if ((message.toLowerCase().includes('convert') && message.toLowerCase().includes('project')) ||
                (message.toLowerCase().includes('save') && message.toLowerCase().includes('project')) ||
                (message.toLowerCase().includes('make') && message.toLowerCase().includes('project'))) {
                
                // Create a data structure to pass to the conversion handler
                const conversionData = {
                    response: responses[responseIndex],
                    conversation_id: conversationId,
                    project_conversion: true,
                    timestamp: new Date().toISOString()
                };
                
                // Call the conversion handler
                setTimeout(() => {
                    this.handleProjectConversion(conversionData);
                }, 1500);
            }
        }
        
        const responseText = responses[responseIndex];
        
        // Create a structured response similar to what the API would return
        const data = {
            status: 'success',
            message: 'Response generated in fallback mode',
            response: responseText,
            conversation_id: conversationId,
            timestamp: new Date().toISOString()
        };
        
        // Save the conversation ID
        localStorage.setItem('minerva_conversation_id', conversationId);
        
        // Display after a short delay to simulate thinking
        setTimeout(() => {
            this.displayMessage(responseText, 'assistant');
            this.saveToConversationMemory(responseText, 'assistant');
        }, 800 + Math.random() * 700);
    }
    
    // Process API response
    processAPIResponse(data) {
        this.log('Processing API response', data);
        
        // Store conversation ID if received from server
        if (data.conversation_id) {
            localStorage.setItem('minerva_conversation_id', data.conversation_id);
            this.log(`Saved conversation ID from server: ${data.conversation_id}`);
        }
        
        // Store memory information
        if (data.memory_id || data.memory_info) {
            localStorage.setItem('minerva_memory_id', data.memory_id || '');
            this.log('Memory information received', { 
                memory_id: data.memory_id, 
                memory_info: data.memory_info 
            });
        }
        
        // Process project conversion requests
        if (data.project_conversion || 
            (data.response && data.response.toLowerCase().includes('convert') && 
             data.response.toLowerCase().includes('project'))) {
            this.log('Project conversion detected in message');
            this.handleProjectConversion(data);
        }
        
        // Handle response text
        let responseText = null;
        
        // Check for various response formats
        if (data.response && typeof data.response === 'string') {
            // Standard Think Tank format
            responseText = data.response;
        } else if (data.message && typeof data.message === 'string') {
            // Alternative format
            responseText = data.message;
        } else if (data.content && typeof data.content === 'string') {
            // Another alternative format
            responseText = data.content;
        } else if (data.text && typeof data.text === 'string') {
            // Yet another format
            responseText = data.text;
        } else if (data.result && typeof data.result === 'object') {
            // Structured result format
            if (data.result.response) {
                responseText = data.result.response;
            } else if (data.result.message) {
                responseText = data.result.message;
            }
        }
        
        // Display response if we found one
        if (responseText) {
            this.displayMessage(responseText, 'assistant');
            this.saveToConversationMemory(responseText, 'assistant');
        } else {
            this.log('No response text found in API response', data, 'error');
            this.displayMessage("I'm sorry, I couldn't process that request properly.", 'system');
        }
    }
    
    // Display message in UI
    displayMessage(text, sender) {
        this.log(`Displaying ${sender} message: ${text.substring(0, 30)}...`);
        
        // Try FloatingChatComponent first
        if (this.components.floatingChat && typeof this.components.floatingChat.addMessage === 'function') {
            const isUser = sender === 'user';
            const success = this.components.floatingChat.addMessage(text, isUser);
            if (success) {
                this.log('Message displayed via FloatingChatComponent');
                return;
            }
        }
        
        // Try chat-simple.js if available
        if (typeof window.displayMessage === 'function') {
            window.displayMessage(text, sender);
            this.log('Message displayed via chat-simple.js');
            return;
        }
        
        // Fall back to direct DOM manipulation
        this.displayMessageDOM(text, sender);
    }
    
    // Display message via DOM manipulation
    displayMessageDOM(text, sender) {
        try {
            // Make sure we have a messages container
            if (!this.elements.chatMessages) {
                this.updateElementReferences();
                if (!this.elements.chatMessages) {
                    this.log('No chat messages container found', null, 'error');
                    return;
                }
            }
            
            // Create message element
            const message = document.createElement('div');
            message.className = `chat-message ${sender}-message`;
            
            // Format message
            if (typeof window.formatMessage === 'function') {
                message.innerHTML = `<div class="message-content">${window.formatMessage(text)}</div>`;
            } else if (typeof markdownit === 'function' && sender !== 'user') {
                // Use markdown if available for non-user messages
                try {
                    const md = markdownit({
                        html: false,
                        linkify: true,
                        typographer: true
                    });
                    message.innerHTML = `<div class="message-content">${md.render(text)}</div>`;
                } catch (error) {
                    message.innerHTML = `<div class="message-content">${text}</div>`;
                }
            } else {
                message.innerHTML = `<div class="message-content">${text}</div>`;
            }
            
            // Add to chat messages
            this.elements.chatMessages.appendChild(message);
            
            // Scroll to bottom
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
            
            this.log('Message displayed via DOM manipulation');
        } catch (error) {
            this.log('Error displaying message', error, 'error');
        }
    }
    
    // Add typing indicator
    addTypingIndicator() {
        try {
            // Try FloatingChatComponent first
            if (this.components.floatingChat && typeof this.components.floatingChat.addLoadingIndicator === 'function') {
                return this.components.floatingChat.addLoadingIndicator();
            }
            
            // Try chat-simple.js if available
            if (typeof window.addTypingIndicator === 'function') {
                return window.addTypingIndicator();
            }
            
            // Fall back to direct DOM manipulation
            if (!this.elements.chatMessages) {
                this.updateElementReferences();
                if (!this.elements.chatMessages) {
                    this.log('No chat messages container found', null, 'error');
                    return null;
                }
            }
            
            // Create indicator element
            const indicator = document.createElement('div');
            indicator.className = 'chat-message system-message typing-indicator';
            indicator.innerHTML = `<div class="message-content"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>`;
            
            // Add to chat messages
            this.elements.chatMessages.appendChild(indicator);
            
            // Scroll to bottom
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
            
            return indicator;
        } catch (error) {
            this.log('Error adding typing indicator', error, 'error');
            return null;
        }
    }
    
    // Remove typing indicator
    removeTypingIndicator(indicator) {
        try {
            // If it's a string ID from FloatingChatComponent
            if (typeof indicator === 'string' && this.components.floatingChat && 
                typeof this.components.floatingChat.removeLoadingIndicator === 'function') {
                this.components.floatingChat.removeLoadingIndicator(indicator);
                return;
            }
            
            // Try chat-simple.js if available
            if (typeof window.removeTypingIndicator === 'function' && indicator) {
                window.removeTypingIndicator(indicator);
                return;
            }
            
            // Fall back to direct DOM manipulation
            if (indicator && indicator.parentNode) {
                indicator.parentNode.removeChild(indicator);
            }
        } catch (error) {
            this.log('Error removing typing indicator', error, 'error');
        }
    }
    
    // Initialize conversation management
    initConversationManagement() {
        // Make sure we have a conversation ID
        let conversationId = localStorage.getItem('minerva_conversation_id');
        if (!conversationId) {
            conversationId = this.generateUUID();
            localStorage.setItem('minerva_conversation_id', conversationId);
            this.log(`Generated new conversation ID: ${conversationId}`);
        } else {
            this.log(`Using existing conversation ID: ${conversationId}`);
        }
        
        // Initialize project structure if needed
        this.initProjectStructure(conversationId);
        
        // Load existing conversation history
        this.loadConversationHistory();
    }
    
    // Save message to conversation memory
    saveToConversationMemory(text, sender) {
        try {
            if (!this.options.useMemory) return;
            
            const conversationId = localStorage.getItem('minerva_conversation_id');
            if (!conversationId) return;
            
            let conversationData = localStorage.getItem(`minerva_conversation_${conversationId}`);
            let messages = [];
            
            if (conversationData) {
                try {
                    messages = JSON.parse(conversationData);
                    if (!Array.isArray(messages)) messages = [];
                } catch (e) {
                    messages = [];
                }
            }
            
            messages.push({
                text: text,
                sender: sender,
                timestamp: new Date().toISOString()
            });
            
            localStorage.setItem(`minerva_conversation_${conversationId}`, JSON.stringify(messages));
            
            // Update conversation metadata
            this.updateConversationMetadata(conversationId, {
                lastActive: new Date().toISOString(),
                messageCount: messages.length
            });
            
            // Also save a name for the conversation if it doesn't exist
            if (!localStorage.getItem(`minerva_conversation_${conversationId}_name`)) {
                // Use the first user message as the conversation name
                if (sender === 'user' && text.length > 0) {
                    // Limit to first 30 chars
                    const name = text.substring(0, 30) + (text.length > 30 ? '...' : '');
                    localStorage.setItem(`minerva_conversation_${conversationId}_name`, name);
                }
            }
            
            this.log('Saved message to conversation memory');
        } catch (error) {
            this.log('Error saving to conversation memory', error, 'error');
        }
    }
    
    // Load conversation history
    loadConversationHistory() {
        try {
            if (!this.options.useMemory) return;
            
            const conversationId = localStorage.getItem('minerva_conversation_id');
            if (!conversationId) return;
            
            const conversationData = localStorage.getItem(`minerva_conversation_${conversationId}`);
            if (!conversationData) return;
            
            try {
                const messages = JSON.parse(conversationData);
                if (!Array.isArray(messages) || messages.length === 0) return;
                
                this.log(`Loading ${messages.length} messages from conversation history`);
                
                // Only show the last few messages to avoid cluttering the UI
                const recentMessages = messages.slice(-3);
                
                // Add separator to indicate history
                this.displayMessage('Continuing previous conversation...', 'system');
                
                // Add recent messages
                recentMessages.forEach(msg => {
                    if (msg && msg.text && msg.sender) {
                        this.displayMessage(msg.text, msg.sender);
                    }
                });
            } catch (error) {
                this.log('Error parsing conversation data', error, 'error');
            }
        } catch (error) {
            this.log('Error loading conversation history', error, 'error');
        }
    }
    
    // Initialize project structure
    initProjectStructure(conversationId) {
        // Check if projects structure exists
        let projects = localStorage.getItem('minerva_projects');
        if (!projects) {
            // Create default project structure
            const defaultProject = {
                id: 'default',
                name: 'Default Project',
                conversations: [conversationId],
                created: new Date().toISOString(),
                lastActive: new Date().toISOString()
            };
            
            projects = JSON.stringify({
                default: defaultProject
            });
            
            localStorage.setItem('minerva_projects', projects);
            this.log('Created default project structure');
            
            // Associate conversation with default project
            this.updateConversationMetadata(conversationId, {
                projectId: 'default'
            });
        }
    }
    
    // Update conversation metadata
    updateConversationMetadata(conversationId, updates) {
        if (!conversationId) return;
        
        let metadata = {};
        const metadataKey = `minerva_meta_${conversationId}`;
        
        // Get existing metadata
        try {
            const existing = localStorage.getItem(metadataKey);
            if (existing) {
                metadata = JSON.parse(existing);
            }
        } catch (e) {
            this.log('Error parsing conversation metadata', e);
        }
        
        // Update with new values
        metadata = { ...metadata, ...updates };
        
        // Save back to storage
        localStorage.setItem(metadataKey, JSON.stringify(metadata));
        this.log('Updated conversation metadata', { conversationId, updates });
    }
    
    // Handle project conversion
    handleProjectConversion(data) {
        const conversationId = localStorage.getItem('minerva_conversation_id');
        if (!conversationId) return;
        
        // Get conversation data to create a meaningful project name
        let projectName = 'New Project';
        try {
            const conversationData = localStorage.getItem(`minerva_conversation_${conversationId}`);
            if (conversationData) {
                const messages = JSON.parse(conversationData);
                if (Array.isArray(messages) && messages.length > 0) {
                    // Use first user message as project name
                    const userMsg = messages.find(m => m.sender === 'user');
                    if (userMsg) {
                        projectName = userMsg.text.substring(0, 30);
                        if (userMsg.text.length > 30) projectName += '...'; 
                    }
                }
            }
        } catch (e) {
            this.log('Error extracting project name from conversation', e);
        }
        
        // Create new project
        const projectId = 'proj-' + this.generateUUID();
        
        // Get existing projects
        let projects = {};
        try {
            const projectsData = localStorage.getItem('minerva_projects');
            if (projectsData) {
                projects = JSON.parse(projectsData);
            }
        } catch (e) {
            this.log('Error loading projects', e);
        }
        
        // Create new project entry
        projects[projectId] = {
            id: projectId,
            name: projectName,
            conversations: [conversationId],
            created: new Date().toISOString(),
            lastActive: new Date().toISOString()
        };
        
        // Save updated projects
        localStorage.setItem('minerva_projects', JSON.stringify(projects));
        
        // Update conversation metadata to reference new project
        this.updateConversationMetadata(conversationId, {
            projectId: projectId,
            convertedToProject: true,
            convertedOn: new Date().toISOString()
        });
        
        // Notify user about successful conversion
        this.displayMessage(
            `This conversation has been converted to a project: "${projectName}".`, 
            'system'
        );
        
        this.log('Conversation converted to project', { conversationId, projectId, projectName });
    }
    
    // Generate UUID
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    // Debug logging
    log(message, data = null, level = 'info') {
        if (!this.options.debug && level !== 'error') return;
        
        const prefix = '[ChatBridge]';
        
        switch (level) {
            case 'error':
                console.error(`${prefix} ${message}`, data || '');
                break;
            case 'warn':
                console.warn(`${prefix} ${message}`, data || '');
                break;
            default:
                console.log(`${prefix} ${message}`, data || '');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Create chat bridge instance with debugging enabled
    window.chatBridge = new ChatBridge({ 
        debug: true,
        useMemory: true
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChatBridge };
}
