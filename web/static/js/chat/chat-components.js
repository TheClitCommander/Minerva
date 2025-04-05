/**
 * Floating Chat Component for Minerva
 * Provides a reusable chat interface that can be embedded anywhere
 */

class FloatingChatComponent {
    constructor(options = {}) {
        // Default options
        this.options = {
            containerId: 'floating-chat-container',
            title: 'Minerva Assistant',
            placeholder: 'Ask me anything...',
            position: { bottom: '20px', right: '20px' },
            initiallyVisible: true,
            width: '350px',
            maxHeight: '500px',
            transparency: 0.9,
            theme: 'cosmic',
            ...options
        };
        
        this.container = document.getElementById(this.options.containerId);
        
        // Create the container if it doesn't exist
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = this.options.containerId;
            document.body.appendChild(this.container);
        }
        
        this.initialized = false;
        this.initialize();
    }
    
    initialize() {
        // Create the chat UI elements
        this.createChatInterface();
        
        // Set up event listeners
        this.setupEventListeners();
        
        this.initialized = true;
        console.log("FloatingChatComponent initialized successfully");
    }
    
    createChatInterface() {
        // Apply container styles
        Object.assign(this.container.style, {
            position: 'fixed',
            bottom: this.options.position.bottom,
            right: this.options.position.right,
            width: this.options.width,
            maxHeight: this.options.maxHeight,
            backgroundColor: `rgba(30, 30, 60, ${this.options.transparency})`,
            borderRadius: '12px',
            boxShadow: '0 5px 15px rgba(0, 0, 0, 0.5)',
            zIndex: '9999',
            display: this.options.initiallyVisible ? 'flex' : 'none',
            flexDirection: 'column',
            overflow: 'hidden',
            transition: 'all 0.3s ease',
            border: '1px solid rgba(100, 100, 255, 0.3)'
        });
        
        this.container.className = 'floating-chat';
        
        // Create header
        const header = document.createElement('div');
        header.className = 'chat-header';
        Object.assign(header.style, {
            padding: '12px 16px',
            backgroundColor: 'rgba(50, 50, 80, 0.7)',
            color: 'white',
            fontWeight: 'bold',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        });
        
        // Add title
        const title = document.createElement('div');
        title.textContent = this.options.title;
        
        // Add controls
        const controls = document.createElement('div');
        
        // Minimize button
        const minimizeBtn = document.createElement('button');
        minimizeBtn.textContent = '−';
        minimizeBtn.className = 'chat-control-btn minimize-btn';
        Object.assign(minimizeBtn.style, {
            background: 'none',
            border: 'none',
            color: 'white',
            fontSize: '16px',
            cursor: 'pointer',
            marginLeft: '8px'
        });
        minimizeBtn.addEventListener('click', () => this.toggleVisibility());
        
        controls.appendChild(minimizeBtn);
        header.appendChild(title);
        header.appendChild(controls);
        
        // Create messages container
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'chat-messages';
        messagesContainer.id = 'floating-chat-messages';
        Object.assign(messagesContainer.style, {
            flex: '1',
            overflowY: 'auto',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            minHeight: '300px',
            backgroundColor: 'rgba(40, 40, 70, 0.7)'
        });
        
        // Create input area
        const inputArea = document.createElement('div');
        inputArea.className = 'chat-input-area';
        Object.assign(inputArea.style, {
            padding: '12px',
            borderTop: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'rgba(40, 40, 70, 0.7)'
        });
        
        // Create input
        const input = document.createElement('input');
        input.type = 'text';
        input.placeholder = this.options.placeholder;
        input.className = 'chat-input';
        input.id = 'floating-chat-input';
        Object.assign(input.style, {
            flex: '1',
            padding: '10px 12px',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '6px',
            backgroundColor: 'rgba(30, 30, 50, 0.7)',
            color: 'white',
            outline: 'none'
        });
        
        // Create send button
        const sendButton = document.createElement('button');
        sendButton.textContent = 'Send';
        sendButton.className = 'chat-send-button';
        sendButton.id = 'floating-chat-send-button';
        Object.assign(sendButton.style, {
            marginLeft: '8px',
            padding: '10px 16px',
            border: 'none',
            borderRadius: '6px',
            backgroundColor: 'rgba(74, 107, 223, 0.8)',
            color: 'white',
            cursor: 'pointer',
            fontWeight: 'bold'
        });
        
        inputArea.appendChild(input);
        inputArea.appendChild(sendButton);
        
        // Add everything to container
        this.container.appendChild(header);
        this.container.appendChild(messagesContainer);
        this.container.appendChild(inputArea);
        
        // Save references
        this.messagesContainer = messagesContainer;
        this.input = input;
        this.sendButton = sendButton;
        this.header = header;
        this.minimizeBtn = minimizeBtn;
    }
    
    setupEventListeners() {
        // Handle input submission
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
    }
    
    sendMessage() {
        const message = this.input.value.trim();
        if (message) {
            // Emit event for external handling
            const event = new CustomEvent('floatingChatMessage', {
                detail: { message }
            });
            document.dispatchEvent(event);
            
            // Clear input
            this.input.value = '';
        }
    }
    
    addMessage(message, isUser = false) {
        console.log(`Adding ${isUser ? 'user' : 'assistant'} message to floating chat:`, message);
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${isUser ? 'user-message' : 'assistant-message'}`;
        Object.assign(messageEl.style, {
            maxWidth: '80%',
            padding: '10px 14px',
            borderRadius: '16px',
            marginBottom: '10px',
            wordBreak: 'break-word',
            backgroundColor: isUser ? 'rgba(74, 107, 223, 0.8)' : 'rgba(50, 50, 70, 0.7)',
            color: 'white',
            alignSelf: isUser ? 'flex-end' : 'flex-start',
            boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)'
        });
        
        messageEl.textContent = message;
        this.messagesContainer.appendChild(messageEl);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // Make sure the chat container is visible
        this.container.style.display = 'flex';
        return messageEl;
    }
    
    toggleVisibility() {
        if (this.container.style.display === 'none') {
            this.container.style.display = 'flex';
            this.minimizeBtn.textContent = '−';
        } else {
            this.container.style.display = 'none';
            this.minimizeBtn.textContent = '+';
        }
    }
}

// Add to window object for global access
window.FloatingChatComponent = FloatingChatComponent;
