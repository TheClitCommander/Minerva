/**
 * Minerva Chat Integration
 * 
 * This module handles the integration of the Minerva Chat component
 * into different pages of the Minerva platform, with context-awareness
 * and project-specific functionality.
 */

(function() {
    // Store references to different chat instances
    const chatInstances = {
        floating: null,    // Homepage floating chat
        project: null,     // Project page chat panel
        current: null      // Reference to currently active chat
    };
    
    // Configuration options
    const config = {
        persistenceEnabled: true,
        conversationMemoryKey: 'minerva_conversation_id',
        projectContextKey: 'current_project_context',
        autoInitialize: true
    };
    
    /**
     * Initialize the appropriate chat interface based on the current page
     */
    function initializeChatInterface() {
        // Determine which page we're on
        const isHomePage = document.querySelector('.home-container') !== null;
        const isProjectPage = document.querySelector('.project-container') !== null;
        
        if (isHomePage) {
            initializeFloatingChat();
        } else if (isProjectPage) {
            initializeProjectChat();
        }
        
        // Listen for project context changes
        setupProjectContextListeners();
    }
    
    /**
     * Initialize the floating chat component for the homepage
     */
    function initializeFloatingChat() {
        // Check if we already have the floating chat
        if (document.getElementById('minerva-floating-chat')) {
            return;
        }
        
        // Create the floating chat container
        const floatingChat = document.createElement('div');
        floatingChat.id = 'minerva-floating-chat';
        floatingChat.className = 'minerva-floating-chat collapsed';
        
        // Create chat header with toggle and title
        const chatHeader = document.createElement('div');
        chatHeader.className = 'chat-header';
        chatHeader.innerHTML = `
            <div class="chat-title">Minerva Think Tank</div>
            <button class="chat-toggle">💬</button>
        `;
        
        // Create chat body with container for chat component
        const chatBody = document.createElement('div');
        chatBody.className = 'chat-body';
        chatBody.innerHTML = `
            <div id="floating-chat-container" class="chat-container"></div>
        `;
        
        // Add header and body to floating chat
        floatingChat.appendChild(chatHeader);
        floatingChat.appendChild(chatBody);
        
        // Add the floating chat to the page
        document.body.appendChild(floatingChat);
        
        // Initialize the chat component inside the container
        chatInstances.floating = new MinervaChat({
            container: document.getElementById('floating-chat-container'),
            mode: 'floating',
            persistence: config.persistenceEnabled
        });
        
        // Set as current chat instance
        chatInstances.current = chatInstances.floating;
        
        // Add event listener for toggling the chat
        const toggleButton = floatingChat.querySelector('.chat-toggle');
        toggleButton.addEventListener('click', function() {
            floatingChat.classList.toggle('collapsed');
            if (!floatingChat.classList.contains('collapsed')) {
                // Focus the input when expanded
                setTimeout(() => {
                    const input = floatingChat.querySelector('.chat-input');
                    if (input) input.focus();
                }, 300);
            }
        });
        
        // Add glass-like effect and animations
        addFloatingChatStyles();
    }
    
    /**
     * Initialize the project chat panel for project pages
     */
    function initializeProjectChat() {
        // Check if project sidebar exists
        const projectSidebar = document.querySelector('.project-sidebar');
        if (!projectSidebar) {
            console.warn('Project sidebar not found for chat integration');
            return;
        }
        
        // Create project chat container
        const projectChatPanel = document.createElement('div');
        projectChatPanel.id = 'minerva-project-chat';
        projectChatPanel.className = 'minerva-project-chat';
        
        // Create chat header
        const chatHeader = document.createElement('div');
        chatHeader.className = 'project-chat-header';
        chatHeader.innerHTML = `
            <div class="chat-title">Project Assistant</div>
            <div class="chat-actions">
                <button class="chat-action create-project" title="Convert to Project">📋</button>
                <button class="chat-action collapse-chat" title="Collapse">⬆️</button>
            </div>
        `;
        
        // Create chat body
        const chatBody = document.createElement('div');
        chatBody.className = 'project-chat-body';
        chatBody.innerHTML = `
            <div id="project-chat-container" class="chat-container"></div>
        `;
        
        // Add header and body to project chat
        projectChatPanel.appendChild(chatHeader);
        projectChatPanel.appendChild(chatBody);
        
        // Add the project chat to the sidebar
        projectSidebar.appendChild(projectChatPanel);
        
        // Get current project context
        const projectContext = getCurrentProjectContext();
        
        // Initialize the chat component with project context
        chatInstances.project = new MinervaChat({
            container: document.getElementById('project-chat-container'),
            mode: 'project',
            persistence: config.persistenceEnabled,
            context: {
                projectId: projectContext.id,
                projectName: projectContext.name
            }
        });
        
        // Set as current chat instance
        chatInstances.current = chatInstances.project;
        
        // Setup event listeners for chat actions
        setupProjectChatActions(projectChatPanel);
    }
    
    /**
     * Set up event listeners for the project chat panel actions
     */
    function setupProjectChatActions(panel) {
        // Collapse/expand functionality
        const collapseButton = panel.querySelector('.collapse-chat');
        collapseButton.addEventListener('click', function() {
            panel.classList.toggle('collapsed');
            this.textContent = panel.classList.contains('collapsed') ? '⬇️' : '⬆️';
            this.title = panel.classList.contains('collapsed') ? 'Expand' : 'Collapse';
        });
        
        // Convert conversation to project
        const createProjectButton = panel.querySelector('.create-project');
        createProjectButton.addEventListener('click', function() {
            convertConversationToProject();
        });
    }
    
    /**
     * Get the current project context from the page
     */
    function getCurrentProjectContext() {
        // Try to get from localStorage first
        const savedContext = localStorage.getItem(config.projectContextKey);
        if (savedContext) {
            try {
                return JSON.parse(savedContext);
            } catch (e) {
                console.error('Error parsing saved project context:', e);
            }
        }
        
        // Otherwise extract from the page
        const projectContainer = document.querySelector('.project-container');
        let context = {
            id: null,
            name: 'Unknown Project'
        };
        
        if (projectContainer) {
            // Extract project ID from data attribute or URL
            const projectId = projectContainer.dataset.projectId || 
                             window.location.pathname.split('/').pop();
            
            // Extract project name from header or title
            const projectName = document.querySelector('.project-name')?.textContent || 
                              document.title.replace(' - Minerva', '');
            
            context = {
                id: projectId,
                name: projectName
            };
            
            // Save to localStorage for persistence
            localStorage.setItem(config.projectContextKey, JSON.stringify(context));
        }
        
        return context;
    }
    
    /**
     * Listen for changes in project context across the application
     */
    function setupProjectContextListeners() {
        // Listen for custom events that might change project context
        document.addEventListener('minerva:project-changed', function(e) {
            if (e.detail && e.detail.projectId) {
                const newContext = {
                    id: e.detail.projectId,
                    name: e.detail.projectName || 'Unknown Project'
                };
                
                // Update localStorage
                localStorage.setItem(config.projectContextKey, JSON.stringify(newContext));
                
                // Update chat instances with new context
                if (chatInstances.project) {
                    chatInstances.project.updateContext({
                        projectId: newContext.id,
                        projectName: newContext.name
                    });
                }
            }
        });
    }
    
    /**
     * Convert the current conversation to a new project
     */
    function convertConversationToProject() {
        // Get conversation history from current chat instance
        const currentChat = chatInstances.current;
        if (!currentChat) {
            console.error('No active chat instance found');
            return;
        }
        
        // Get conversation title from first few messages
        let conversationTitle = 'New Project from Chat';
        const firstUserMessage = document.querySelector('.message.user-message');
        if (firstUserMessage) {
            // Use first 40 chars of first user message as title
            const messageText = firstUserMessage.textContent.trim();
            conversationTitle = messageText.substring(0, 40) + (messageText.length > 40 ? '...' : '');
        }
        
        // Show creation UI
        showProjectCreationUI(conversationTitle, function(confirmed, projectName) {
            if (confirmed) {
                // Call API to create project from conversation
                createProjectFromConversation(projectName, currentChat.getConversationId());
            }
        });
    }
    
    /**
     * Show UI for confirming project creation and naming
     */
    function showProjectCreationUI(defaultName, callback) {
        // Create modal for project creation
        const modal = document.createElement('div');
        modal.className = 'minerva-modal';
        modal.innerHTML = `
            <div class="minerva-modal-content">
                <h3>Create Project from Conversation</h3>
                <p>Your conversation will be converted into a new project.</p>
                <div class="form-group">
                    <label for="project-name">Project Name:</label>
                    <input type="text" id="project-name" value="${defaultName}" class="form-control">
                </div>
                <div class="modal-actions">
                    <button class="btn cancel">Cancel</button>
                    <button class="btn create">Create Project</button>
                </div>
            </div>
        `;
        
        // Add modal to page
        document.body.appendChild(modal);
        
        // Focus the input
        setTimeout(() => {
            const input = modal.querySelector('#project-name');
            input.focus();
            input.select();
        }, 100);
        
        // Setup event listeners
        const cancelButton = modal.querySelector('.btn.cancel');
        const createButton = modal.querySelector('.btn.create');
        const nameInput = modal.querySelector('#project-name');
        
        cancelButton.addEventListener('click', function() {
            modal.remove();
            if (callback) callback(false);
        });
        
        createButton.addEventListener('click', function() {
            const projectName = nameInput.value.trim() || defaultName;
            modal.remove();
            if (callback) callback(true, projectName);
        });
        
        // Also handle enter key
        nameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                createButton.click();
            }
        });
    }
    
    /**
     * API call to create a new project from conversation
     */
    function createProjectFromConversation(projectName, conversationId) {
        // Show loading indicator
        const loadingToast = showToast('Creating project...', 'loading');
        
        // Make API request
        fetch('/api/projects/create-from-conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_name: projectName,
                conversation_id: conversationId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            hideToast(loadingToast);
            
            // Show success message
            showToast(`Project "${projectName}" created successfully!`, 'success');
            
            // Redirect to the new project page
            if (data.project_id) {
                setTimeout(() => {
                    window.location.href = `/projects/${data.project_id}`;
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Error creating project:', error);
            hideToast(loadingToast);
            showToast('Error creating project. Please try again.', 'error');
        });
    }
    
    /**
     * Simple toast notification system
     */
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `minerva-toast ${type}`;
        toast.innerHTML = `<div class="toast-message">${message}</div>`;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => {
            toast.classList.add('visible');
        }, 10);
        
        // Auto-hide after delay unless it's a loading toast
        if (type !== 'loading') {
            setTimeout(() => {
                hideToast(toast);
            }, 4000);
        }
        
        return toast;
    }
    
    function hideToast(toast) {
        if (!toast) return;
        toast.classList.remove('visible');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }
    
    /**
     * Add styles for the floating chat
     */
    function addFloatingChatStyles() {
        // Create the style element if it doesn't exist
        let styleElement = document.getElementById('minerva-chat-integration-styles');
        if (!styleElement) {
            styleElement = document.createElement('style');
            styleElement.id = 'minerva-chat-integration-styles';
            document.head.appendChild(styleElement);
            
            // Add styles
            styleElement.textContent = `
                /* Floating Chat Styles */
                .minerva-floating-chat {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 350px;
                    height: 500px;
                    background: rgba(255, 255, 255, 0.9);
                    backdrop-filter: blur(10px);
                    border-radius: 12px;
                    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                    z-index: 1000;
                    border: 1px solid rgba(0, 0, 0, 0.1);
                }
                
                .minerva-floating-chat.collapsed {
                    height: 50px;
                    width: 180px;
                }
                
                .minerva-floating-chat .chat-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 15px;
                    background: linear-gradient(135deg, #4b79a1, #283e51);
                    color: white;
                    cursor: pointer;
                }
                
                .minerva-floating-chat .chat-title {
                    font-weight: 500;
                    font-size: 14px;
                }
                
                .minerva-floating-chat .chat-toggle {
                    background: transparent;
                    border: none;
                    color: white;
                    cursor: pointer;
                    font-size: 16px;
                    padding: 0;
                }
                
                .minerva-floating-chat .chat-body {
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                
                .minerva-floating-chat.collapsed .chat-body {
                    height: 0;
                }
                
                /* Project Chat Styles */
                .minerva-project-chat {
                    width: 100%;
                    height: 250px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                    margin-top: 15px;
                    border: 1px solid #eee;
                }
                
                .minerva-project-chat.collapsed {
                    height: 40px;
                }
                
                .minerva-project-chat .project-chat-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background: #f5f7fa;
                    border-bottom: 1px solid #eee;
                }
                
                .minerva-project-chat .chat-title {
                    font-weight: 500;
                    font-size: 13px;
                    color: #444;
                }
                
                .minerva-project-chat .chat-actions {
                    display: flex;
                    gap: 5px;
                }
                
                .minerva-project-chat .chat-action {
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                    padding: 2px;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                
                .minerva-project-chat .chat-action:hover {
                    opacity: 1;
                }
                
                .minerva-project-chat .project-chat-body {
                    flex-grow: 1;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transition: all 0.3s ease;
                }
                
                .minerva-project-chat.collapsed .project-chat-body {
                    height: 0;
                }
                
                /* Modal Styles */
                .minerva-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 2000;
                }
                
                .minerva-modal-content {
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    width: 400px;
                    max-width: 90%;
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                }
                
                .minerva-modal h3 {
                    margin-top: 0;
                    margin-bottom: 15px;
                    color: #333;
                }
                
                .minerva-modal .form-group {
                    margin-bottom: 20px;
                }
                
                .minerva-modal label {
                    display: block;
                    margin-bottom: 5px;
                    font-weight: 500;
                }
                
                .minerva-modal .form-control {
                    width: 100%;
                    padding: 8px 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }
                
                .minerva-modal .modal-actions {
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                }
                
                .minerva-modal .btn {
                    padding: 8px 15px;
                    border-radius: 4px;
                    border: none;
                    font-size: 14px;
                    cursor: pointer;
                }
                
                .minerva-modal .btn.cancel {
                    background: #eee;
                    color: #333;
                }
                
                .minerva-modal .btn.create {
                    background: #4b79a1;
                    color: white;
                }
                
                /* Toast Notifications */
                .minerva-toast {
                    position: fixed;
                    bottom: 20px;
                    left: 20px;
                    padding: 10px 15px;
                    background: white;
                    border-radius: 4px;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
                    font-size: 14px;
                    transform: translateY(100px);
                    opacity: 0;
                    transition: all 0.3s ease;
                    z-index: 2000;
                }
                
                .minerva-toast.visible {
                    transform: translateY(0);
                    opacity: 1;
                }
                
                .minerva-toast.success {
                    border-left: 4px solid #2ecc71;
                }
                
                .minerva-toast.error {
                    border-left: 4px solid #e74c3c;
                }
                
                .minerva-toast.info {
                    border-left: 4px solid #3498db;
                }
                
                .minerva-toast.loading {
                    border-left: 4px solid #f39c12;
                }
                
                .minerva-toast.loading:after {
                    content: '';
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border: 2px solid #f39c12;
                    border-top-color: transparent;
                    border-radius: 50%;
                    margin-left: 10px;
                    animation: spin 1s infinite linear;
                }
                
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
        }
    }
    
    // Static method to update all chat instances with a conversation ID
    window.MinervaChat.updateConversationId = function(conversationId) {
        // Update any active instances
        if (window.floatingChat && window.floatingChat.updateConversationId) {
            window.floatingChat.updateConversationId(conversationId);
        }
        
        if (window.projectChat && window.projectChat.updateConversationId) {
            window.projectChat.updateConversationId(conversationId);
        }
    };
    
    // MinervaChat class constructor for creating new chat instances
    window.MinervaChat = function(options) {
        // Default options
        const defaults = {
            container: null,
            mode: 'standard', // standard, floating, project
            persistence: true,
            context: {}
        };
        
        // Merge options
        const settings = Object.assign({}, defaults, options);
        
        // Validate container
        if (!settings.container) {
            console.error('MinervaChat: container element is required');
            return null;
        }
        
        const chat = {
            container: settings.container,
            mode: settings.mode,
            context: settings.context,
            conversationId: null,
            
            initialize: function() {
                // Create chat UI
                this.createChatUI();
                
                // Get conversation ID from localStorage if persistence enabled
                if (settings.persistence) {
                    const savedId = localStorage.getItem(config.conversationMemoryKey);
                    if (savedId) {
                        this.conversationId = savedId;
                    }
                }
                
                // Initialize event listeners
                this.setupEventListeners();
                
                return this;
            },
            
            createChatUI: function() {
                // Create the basic chat HTML
                this.container.innerHTML = `
                    <div class="chat-messages" id="chat-history"></div>
                    <div class="chat-input-container">
                        <textarea class="chat-input" placeholder="Ask Minerva..."></textarea>
                        <button class="chat-send">Send</button>
                    </div>
                `;
                
                // Add mode-specific classes
                this.container.classList.add(`chat-mode-${this.mode}`);
            },
            
            setupEventListeners: function() {
                const sendButton = this.container.querySelector('.chat-send');
                const inputField = this.container.querySelector('.chat-input');
                
                // Send message on button click
                sendButton.addEventListener('click', () => {
                    this.sendMessage();
                });
                
                // Send message on Enter (but allow shift+enter for new lines)
                inputField.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        this.sendMessage();
                    }
                });
            },
            
            sendMessage: function() {
                const inputField = this.container.querySelector('.chat-input');
                const message = inputField.value.trim();
                
                if (!message) return;
                
                // Clear input
                inputField.value = '';
                
                // Send to the existing Minerva chat system
                // This will trigger the main chat functionality we've been enhancing
                if (typeof window.sendToChatAPI === 'function') {
                    // Build context object to include with message
                    const contextData = {
                        ...this.context,
                        chat_mode: this.mode,
                        conversation_id: this.conversationId
                    };
                    
                    // Send the message with context
                    window.sendToChatAPI(message, contextData);
                } else {
                    console.error('sendToChatAPI function not found. Chat integration may not work properly.');
                }
            },
            
            getConversationId: function() {
                return this.conversationId;
            },
            
            updateContext: function(newContext) {
                this.context = {
                    ...this.context,
                    ...newContext
                };
            },
            
            /**
             * Update the conversation ID
             * This is critical for conversation memory persistence
             */
            updateConversationId: function(conversationId) {
                if (!conversationId) return;
                
                console.log(`Chat instance updated with conversation ID: ${conversationId}`);
                this.conversationId = conversationId;
                
                // Store in context for API calls
                this.updateContext({
                    conversation_id: conversationId
                });
                
                // Store in localStorage if persistence enabled
                if (settings.persistence) {
                    localStorage.setItem(config.conversationMemoryKey, conversationId);
                }
                
                // Update UI if needed to show conversation is linked
                const container = this.container;
                if (container) {
                    // Add a visual indicator that this chat has memory
                    if (!container.classList.contains('has-memory')) {
                        container.classList.add('has-memory');
                    }
                }
            }
        };
        
        // Initialize and return the chat object
        return chat.initialize();
    };
    
    // Auto-initialize on document ready
    if (config.autoInitialize) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeChatInterface);
        } else {
            initializeChatInterface();
        }
    }
    
    // Expose API to window
    window.MinervaIntegration = {
        initChat: initializeChatInterface,
        getActiveChat: function() {
            return chatInstances.current;
        },
        convertToProject: convertConversationToProject
    };
})();
