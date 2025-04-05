/**
 * Minerva Floating Chat Component
 * 
 * A flexible, draggable chat interface that can be integrated into any page
 * with conversation memory and project awareness.
 */

class MinervaFloatingChat {
    constructor(options = {}) {
        // Default options
        this.options = {
            containerId: 'minerva-floating-chat',
            apiEndpoint: '/api/think-tank',
            position: 'bottom-right',
            width: '350px',
            height: '500px',
            title: 'Minerva Chat',
            projectId: null,
            ...options
        };

        // Chat state
        this.conversationId = localStorage.getItem('minerva_conversation_id') || null;
        this.isMinimized = false;
        this.isHidden = false;
        this.sessionId = 'session-' + Date.now();
        this.userId = 'user-' + Date.now();
        this.projectContext = this.options.projectId ? { id: this.options.projectId } : null;
        
        // Initialize the chat UI
        this.initChatInterface();
    }

    /**
     * Initialize the chat interface
     */
    initChatInterface() {
        // Create container if it doesn't exist
        let container = document.getElementById(this.options.containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.containerId;
            document.body.appendChild(container);
        }
        
        // Set container styling
        container.style.position = 'fixed';
        container.style.width = this.options.width;
        container.style.height = this.options.height;
        container.style.zIndex = '9999';
        container.style.transition = 'all 0.3s ease';
        container.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.2)';
        container.style.borderRadius = '10px';
        container.style.overflow = 'hidden';
        container.style.display = 'flex';
        container.style.flexDirection = 'column';
        container.style.backgroundColor = 'rgba(15, 23, 42, 0.85)';
        container.style.backdropFilter = 'blur(8px)';
        
        // Position the container
        this.positionChat(container);
        
        // Create and inject HTML structure
        container.innerHTML = `
            <div class="chat-header" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background-color: rgba(30, 41, 59, 0.8); cursor: move;">
                <div class="chat-title" style="font-weight: bold; color: #e2e8f0;">${this.options.title}</div>
                <div class="chat-controls">
                    ${this.projectContext ? `<span class="project-badge" style="margin-right: 10px; font-size: 12px; color: #a5b4fc;">Project: ${this.projectContext.id}</span>` : ''}
                    <button class="minimize-btn" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; margin-left: 5px;">–</button>
                    <button class="close-btn" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; margin-left: 5px;">×</button>
                </div>
            </div>
            <div class="chat-messages" style="flex: 1; overflow-y: auto; padding: 15px; color: #e2e8f0;">
                <div class="system-message" style="padding: 10px; background-color: rgba(59, 130, 246, 0.1); border-radius: 8px; margin-bottom: 10px;">
                    ${this.projectContext 
                        ? `Welcome to Project ${this.projectContext.id}. How can I assist with this project?` 
                        : 'Welcome to Minerva. How can I assist you today?'}
                </div>
            </div>
            <div class="chat-input-container" style="padding: 10px; border-top: 1px solid rgba(100, 116, 139, 0.2); display: flex;">
                <textarea class="chat-input" placeholder="Type a message..." style="flex: 1; padding: 8px; border-radius: 5px; border: 1px solid rgba(100, 116, 139, 0.3); background-color: rgba(30, 41, 59, 0.5); color: #e2e8f0; resize: none;"></textarea>
                <button class="send-btn" style="background-color: #3b82f6; color: white; border: none; border-radius: 5px; padding: 8px 12px; margin-left: 8px; cursor: pointer;">Send</button>
            </div>
        `;
        
        // Store DOM references
        this.chatContainer = container;
        this.messageContainer = container.querySelector('.chat-messages');
        this.inputField = container.querySelector('.chat-input');
        this.sendButton = container.querySelector('.send-btn');
        this.minimizeButton = container.querySelector('.minimize-btn');
        this.closeButton = container.querySelector('.close-btn');
        
        // Make the chat draggable
        this.makeDraggable(container, container.querySelector('.chat-header'));
        
        // Set up event listeners
        this.setupEventListeners();
    }

    /**
     * Set up event listeners for the chat interface
     */
    setupEventListeners() {
        // Send button event listener
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send (without shift)
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Minimize button
        this.minimizeButton.addEventListener('click', () => this.toggleMinimize());
        
        // Close button
        this.closeButton.addEventListener('click', () => this.toggleVisibility());
    }

    /**
     * Position the chat based on the selected position
     */
    positionChat(container) {
        // Clear all positions first
        container.style.top = 'auto';
        container.style.bottom = 'auto';
        container.style.left = 'auto';
        container.style.right = 'auto';
        
        // Set position based on option
        switch(this.options.position) {
            case 'bottom-right':
                container.style.bottom = '20px';
                container.style.right = '20px';
                break;
            case 'bottom-left':
                container.style.bottom = '20px';
                container.style.left = '20px';
                break;
            case 'top-right':
                container.style.top = '20px';
                container.style.right = '20px';
                break;
            case 'top-left':
                container.style.top = '20px';
                container.style.left = '20px';
                break;
            default:
                container.style.bottom = '20px';
                container.style.right = '20px';
        }
    }

    /**
     * Make an element draggable
     */
    makeDraggable(element, handle) {
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
            
            // Add a dragging class
            element.classList.add('dragging');
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
            
            // When manually positioned, clear automatic positioning
            element.style.bottom = 'auto';
            element.style.right = 'auto';
        }
        
        function closeDragElement() {
            // Stop moving when mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
            
            // Remove dragging class
            element.classList.remove('dragging');
        }
    }

    /**
     * Toggle chat minimized state
     */
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            this.chatContainer.style.height = '50px';
            this.messageContainer.style.display = 'none';
            this.chatContainer.querySelector('.chat-input-container').style.display = 'none';
            this.minimizeButton.textContent = '□';
            this.minimizeButton.setAttribute('title', 'Expand');
        } else {
            this.chatContainer.style.height = this.options.height;
            this.messageContainer.style.display = 'block';
            this.chatContainer.querySelector('.chat-input-container').style.display = 'flex';
            this.minimizeButton.textContent = '–';
            this.minimizeButton.setAttribute('title', 'Minimize');
        }
    }

    /**
     * Toggle chat visibility
     */
    toggleVisibility() {
        this.isHidden = !this.isHidden;
        
        if (this.isHidden) {
            this.chatContainer.style.display = 'none';
        } else {
            this.chatContainer.style.display = 'flex';
        }
    }

    /**
     * Create a chat toggle button that can be used elsewhere on the page
     */
    createToggleButton(parentElement) {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'minerva-chat-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-comments"></i>';
        toggleBtn.style.position = 'fixed';
        toggleBtn.style.bottom = '20px';
        toggleBtn.style.right = '20px';
        toggleBtn.style.width = '50px';
        toggleBtn.style.height = '50px';
        toggleBtn.style.borderRadius = '50%';
        toggleBtn.style.backgroundColor = '#3b82f6';
        toggleBtn.style.color = 'white';
        toggleBtn.style.border = 'none';
        toggleBtn.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
        toggleBtn.style.cursor = 'pointer';
        toggleBtn.style.zIndex = '9998';
        toggleBtn.style.display = this.isHidden ? 'block' : 'none';
        
        toggleBtn.addEventListener('click', () => {
            this.toggleVisibility();
            toggleBtn.style.display = this.isHidden ? 'block' : 'none';
        });
        
        if (parentElement) {
            parentElement.appendChild(toggleBtn);
        } else {
            document.body.appendChild(toggleBtn);
        }
        
        // Update visibility when chat is closed
        this.closeButton.addEventListener('click', () => {
            toggleBtn.style.display = 'block';
        });
        
        return toggleBtn;
    }

    /**
     * Send a message to the Think Tank API
     */
    sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessageToChat(message, 'user');
        
        // Clear input field
        this.inputField.value = '';
        
        // Add loading indicator
        const loadingId = 'loading-' + Date.now();
        const loadingIndicator = document.createElement('div');
        loadingIndicator.id = loadingId;
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = '<div class="typing-dots"><span>.</span><span>.</span><span>.</span></div>';
        loadingIndicator.style.padding = '10px';
        loadingIndicator.style.margin = '5px 0';
        loadingIndicator.style.backgroundColor = 'rgba(30, 41, 59, 0.4)';
        loadingIndicator.style.borderRadius = '8px';
        this.messageContainer.appendChild(loadingIndicator);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        
        // Create request payload
        const payload = {
            query: message,  // Use 'query' as the parameter name for the Think Tank API
            conversation_id: this.conversationId || null,
            store_in_memory: true,
            project_id: this.projectContext ? this.projectContext.id : null
        };
        
        // Add project context if available
        if (this.projectContext) {
            payload.project_id = this.projectContext.id;
            payload.context = 'project';
        }
        
        // Send to API with timeout to prevent hanging
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout
        
        fetch(this.options.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload),
            signal: controller.signal
        })
        .then(response => {
            clearTimeout(timeoutId);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement && this.messageContainer.contains(loadingElement)) {
                this.messageContainer.removeChild(loadingElement);
            }
            
            // Store conversation ID for memory persistence
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
                console.log("Stored conversation ID for memory persistence:", data.conversation_id);
                
                // If this conversation can be turned into a project, provide UI for that
                if (!this.projectContext && data.can_create_project) {
                    this.addProjectConversionOption(data.conversation_id);
                }
            }
            
            // Handle API response - ensure it's a string
            let responseText;
            if (typeof data.response === 'string') {
                responseText = data.response;
            } else if (data.response) {
                // Convert object to string if needed
                try {
                    responseText = JSON.stringify(data.response);
                } catch (e) {
                    responseText = "Received response in unexpected format";
                }
            } else {
                responseText = "No response received from server";
            }
            
            // Add AI response to chat
            this.addMessageToChat(responseText, 'ai', data.model_info);
        })
        .catch(error => {
            clearTimeout(timeoutId);
            console.error("API error:", error);
            
            // Remove loading indicator
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement && this.messageContainer.contains(loadingElement)) {
                this.messageContainer.removeChild(loadingElement);
            }
            
            // Show error message
            this.addMessageToChat("Sorry, there was an error processing your request. Please try again later.", 'system');
        });
    }

    /**
     * Add a message to the chat interface
     */
    addMessageToChat(message, sender, modelInfo = null) {
        const messageElement = document.createElement('div');
        
        if (sender === 'user') {
            messageElement.className = 'user-message';
            messageElement.style.textAlign = 'right';
            messageElement.style.marginLeft = 'auto';
            messageElement.style.marginRight = '0';
            messageElement.style.maxWidth = '80%';
            messageElement.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
            messageElement.style.borderRadius = '10px 10px 0 10px';
            messageElement.style.padding = '10px';
            messageElement.style.marginBottom = '10px';
        } else if (sender === 'ai') {
            messageElement.className = 'ai-message';
            messageElement.style.textAlign = 'left';
            messageElement.style.marginRight = 'auto';
            messageElement.style.marginLeft = '0';
            messageElement.style.maxWidth = '80%';
            messageElement.style.backgroundColor = 'rgba(30, 41, 59, 0.5)';
            messageElement.style.borderRadius = '10px 10px 10px 0';
            messageElement.style.padding = '10px';
            messageElement.style.marginBottom = '10px';
            
            // Add model info if available
            if (modelInfo) {
                const modelInfoElement = document.createElement('div');
                modelInfoElement.className = 'model-info';
                modelInfoElement.style.fontSize = '10px';
                modelInfoElement.style.color = '#94a3b8';
                modelInfoElement.style.marginTop = '5px';
                
                let modelText = '';
                if (typeof modelInfo === 'object' && modelInfo.primary_model) {
                    modelText = modelInfo.primary_model;
                } else if (Array.isArray(modelInfo)) {
                    modelText = modelInfo.join(', ');
                } else if (typeof modelInfo === 'string') {
                    modelText = modelInfo;
                } else {
                    modelText = 'Think Tank';
                }
                
                modelInfoElement.textContent = `Powered by ${modelText}`;
                messageElement.appendChild(document.createElement('div')).textContent = message;
                messageElement.appendChild(modelInfoElement);
            } else {
                messageElement.textContent = message;
            }
        } else {
            // System message
            messageElement.className = 'system-message';
            messageElement.style.backgroundColor = 'rgba(234, 88, 12, 0.1)';
            messageElement.style.borderRadius = '8px';
            messageElement.style.padding = '10px';
            messageElement.style.marginBottom = '10px';
            messageElement.textContent = message;
        }
        
        // If not AI message with model info (which was already appended)
        if (!(sender === 'ai' && modelInfo)) {
            messageElement.textContent = message;
        }
        
        this.messageContainer.appendChild(messageElement);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    /**
     * Add UI option to convert conversation to project
     */
    addProjectConversionOption(conversationId) {
        const conversionOption = document.createElement('div');
        conversionOption.className = 'project-conversion-option';
        conversionOption.style.padding = '10px';
        conversionOption.style.margin = '10px 0';
        conversionOption.style.backgroundColor = 'rgba(130, 59, 246, 0.1)';
        conversionOption.style.borderRadius = '8px';
        conversionOption.style.fontSize = '14px';
        conversionOption.style.textAlign = 'center';
        
        conversionOption.innerHTML = `
            <div>Would you like to convert this conversation to a project?</div>
            <div style="margin-top: 8px; display: flex; justify-content: center; gap: 10px;">
                <input type="text" placeholder="Project name" class="project-name-input" style="padding: 5px; border-radius: 4px; border: 1px solid rgba(100, 116, 139, 0.3); background-color: rgba(30, 41, 59, 0.5); color: #e2e8f0;">
                <button class="create-project-btn" style="background-color: #8B5CF6; color: white; border: none; border-radius: 4px; padding: 5px 10px; cursor: pointer;">Create</button>
            </div>
        `;
        
        this.messageContainer.appendChild(conversionOption);
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
        
        // Add event listener to create project button
        const createButton = conversionOption.querySelector('.create-project-btn');
        const nameInput = conversionOption.querySelector('.project-name-input');
        
        createButton.addEventListener('click', () => {
            const projectName = nameInput.value.trim();
            if (!projectName) {
                alert('Please enter a project name');
                return;
            }
            
            // Show loading state
            createButton.textContent = 'Creating...';
            createButton.disabled = true;
            
            // Call API to create project from conversation
            fetch('/api/projects/create-from-conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    project_name: projectName
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to create project');
                return response.json();
            })
            .then(data => {
                // Remove conversion option
                this.messageContainer.removeChild(conversionOption);
                
                // Add success message
                this.addMessageToChat(`Successfully created project "${projectName}". You can now continue this conversation in the project context.`, 'system');
                
                // Update project context
                this.projectContext = {
                    id: data.project_id,
                    name: projectName
                };
                
                // Update title to show project
                this.chatContainer.querySelector('.chat-title').innerHTML = 
                    `${this.options.title} <span style="font-size: 12px; color: #a5b4fc;">- Project: ${projectName}</span>`;
            })
            .catch(error => {
                console.error('Error creating project:', error);
                createButton.textContent = 'Create';
                createButton.disabled = false;
                alert('Failed to create project. Please try again.');
            });
        });
    }
}

// Global initialization function
function initMinervaChat(options = {}) {
    window.minervaChat = new MinervaFloatingChat(options);
    return window.minervaChat;
}

// Initialize if being loaded directly
if (typeof window !== 'undefined') {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', () => {
        // Check if auto-init is needed
        if (!window.MINERVA_CHAT_NO_AUTO_INIT) {
            window.minervaChat = new MinervaFloatingChat();
            
            // Create toggle button by default
            window.minervaChat.createToggleButton();
        }
    });
}
