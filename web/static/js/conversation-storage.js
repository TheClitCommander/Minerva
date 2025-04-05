/**
 * Minerva Conversation Storage System
 * Handles automatic saving, retrieval, and management of conversations
 * Integrates the floating chat with the main conversation system
 */

const conversationStorage = {
    conversations: JSON.parse(localStorage.getItem('conversations')) || [],
    
    /**
     * Save a message to a conversation
     * @param {string} conversationId - ID of the conversation
     * @param {string} message - Message content
     * @param {string} sender - Message sender (user or assistant)
     */
    saveMessage(conversationId, message, sender) {
        let conversation = this.conversations.find(c => c.id === conversationId);
        if (!conversation) {
            conversation = {
                id: conversationId,
                title: "New Conversation",
                messages: [],
                timestamp: new Date().toISOString(),
                isPinned: false,
                projectId: null
            };
            this.conversations.push(conversation);
            
            // Generate a title if it's a new conversation after the first user message
            if (sender === 'user') {
                conversation.title = this.generateTitle(message);
            }
        } else {
            // Update conversation timestamp to keep it at the top of recent conversations
            conversation.timestamp = new Date().toISOString();
        }
        
        // Add the message to the conversation
        conversation.messages.push({ 
            sender, 
            text: message, 
            timestamp: new Date().toISOString() 
        });
        
        // Update storage
        this.updateStorage();
        
        return conversation;
    },
    
    /**
     * Generate a smart title based on the first user message
     * @param {string} message - First user message
     * @returns {string} Generated title
     */
    generateTitle(message) {
        if (!message) {
            return "New Conversation";
        }
        
        // Simple approach: use first few words or characters
        // For a first version, we'll use a substring
        const maxTitleLength = 30;
        let title = message.trim();
        
        // If the message is too long, trim it and add ellipsis
        if (title.length > maxTitleLength) {
            // Try to cut at a word boundary
            const cutPoint = title.lastIndexOf(' ', maxTitleLength);
            title = cutPoint > 10 ? title.substring(0, cutPoint) : title.substring(0, maxTitleLength);
            title += "...";
        }
        
        // Capitalize first letter
        title = title.charAt(0).toUpperCase() + title.slice(1);
        
        return title;
    },
    
    /**
     * Update localStorage with current conversations
     */
    updateStorage() {
        localStorage.setItem('conversations', JSON.stringify(this.conversations));
        
        // Also sync with the main Minerva conversation storage if available
        this.syncWithMinervaStorage();
    },
    
    /**
     * Sync conversations with the main Minerva storage system
     */
    syncWithMinervaStorage() {
        // Check if we have access to the main conversation manager
        if (window.conversationManager && typeof window.conversationManager.importConversations === 'function') {
            try {
                // Format conversations for the main storage system
                const formattedConversations = {};
                
                this.conversations.forEach(conv => {
                    formattedConversations[conv.id] = {
                        title: conv.title,
                        messages: conv.messages.map(m => ({
                            role: m.sender,
                            content: m.text,
                            timestamp: m.timestamp
                        })),
                        created: conv.timestamp,
                        updated: new Date().toISOString(),
                        archived: conv.isArchived || false,
                        project: conv.projectId,
                        isPinned: conv.isPinned || false
                    };
                });
                
                // Import conversations to the main system
                window.conversationManager.importConversations(formattedConversations);
                console.log('Conversations synced with Minerva storage system');
            } catch (e) {
                console.error('Error syncing conversations with Minerva storage:', e);
            }
        }
    },
    
    /**
     * Get recent conversations sorted by timestamp and pinned status
     * @returns {Array} Sorted conversations with pinned items first
     */
    getRecentConversations() {
        return this.conversations
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .sort((a, b) => (b.isPinned ? 1 : 0) - (a.isPinned ? 1 : 0));
    },
    
    /**
     * Pin or unpin a conversation
     * @param {string} conversationId - ID of the conversation
     * @param {boolean} isPinned - Whether the conversation should be pinned
     */
    pinConversation(conversationId, isPinned = true) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        if (conversation) {
            conversation.isPinned = isPinned;
            this.updateStorage();
        }
    },
    
    /**
     * Get a specific conversation by ID
     * @param {string} conversationId - ID of the conversation to retrieve
     * @returns {Object} Conversation object or undefined if not found
     */
    getConversation(conversationId) {
        return this.conversations.find(c => c.id === conversationId);
    },
    
    /**
     * Rename a conversation
     * @param {string} conversationId - ID of the conversation to rename
     * @param {string} newTitle - New title for the conversation
     */
    renameConversation(conversationId, newTitle) {
        let conversation = this.conversations.find(c => c.id === conversationId);
        if (conversation) {
            conversation.title = newTitle;
            this.updateStorage();
        }
    },
    
    /**
     * Assign a conversation to a project
     * @param {string} conversationId - ID of the conversation
     * @param {string} projectId - ID of the project
     */
    assignToProject(conversationId, projectId) {
        const conversation = this.conversations.find(c => c.id === conversationId);
        if (conversation) {
            conversation.projectId = projectId;
            this.updateStorage();
        }
    },
    
    /**
     * Get all conversations associated with a project
     * @param {string} projectId - ID of the project
     * @returns {Array} Conversations assigned to the project
     */
    getConversationsByProject(projectId) {
        return this.conversations.filter(c => c.projectId === projectId);
    },
    
    /**
     * Get all available projects referenced in conversations
     * @returns {Array} Array of project IDs
     */
    getAvailableProjects() {
        const projectIds = new Set();
        
        this.conversations.forEach(convo => {
            if (convo.projectId) {
                projectIds.add(convo.projectId);
            }
        });
        
        return Array.from(projectIds);
    },
    
    /**
     * Search conversations by query text
     * @param {string} query - Search query text
     * @returns {Array} Matching conversations
     */
    searchConversations(query) {
        if (!query) return this.getRecentConversations();
        
        const lowerQuery = query.toLowerCase();
        
        // Filter conversations that match the query
        return this.conversations.filter(convo => {
            // Check title
            if (convo.title && convo.title.toLowerCase().includes(lowerQuery)) {
                return true;
            }
            
            // Check messages
            if (convo.messages && convo.messages.length > 0) {
                return convo.messages.some(msg => 
                    msg.text && msg.text.toLowerCase().includes(lowerQuery)
                );
            }
            
            return false;
        });
    }
};

// UI Integration - Auto-save new messages
function handleNewMessage(conversationId, message, sender) {
    conversationStorage.saveMessage(conversationId, message, sender);
    updateConversationListUI();
}

/**
 * Update the conversation list based on search query
 * @param {string} query - Search query
 */
function updateConversationListWithSearch(query) {
    const conversationList = document.getElementById('conversation-list');
    if (!conversationList) {
        console.warn('Conversation list element not found');
        return;
    }
    
    conversationList.innerHTML = '';
    
    // Get matching conversations
    const conversations = query ? 
        conversationStorage.searchConversations(query) : 
        conversationStorage.getRecentConversations();
    
    // Show search results count if searching
    const searchStatus = document.getElementById('search-status');
    if (searchStatus) {
        if (query) {
            searchStatus.textContent = `Found ${conversations.length} conversation(s) matching "${query}"`;
            searchStatus.style.display = 'block';
        } else {
            searchStatus.style.display = 'none';
        }
    } else if (query && conversations.length > 0) {
        // Create status element if it doesn't exist
        const statusEl = document.createElement('div');
        statusEl.id = 'search-status';
        statusEl.classList.add('search-status');
        statusEl.textContent = `Found ${conversations.length} conversation(s) matching "${query}"`;
        
        const container = document.getElementById('conversation-list-container');
        const listEl = document.getElementById('conversation-list');
        if (container && listEl) {
            container.insertBefore(statusEl, listEl);
        }
    }
    
    // Display conversations
    renderConversationList(conversations, query);
}

/**
 * Render conversations to the list with optional highlighting
 * @param {Array} conversations - Array of conversations to display
 * @param {string} highlightQuery - Optional query to highlight in results
 */
function renderConversationList(conversations, highlightQuery = null) {
    const conversationList = document.getElementById('conversation-list');
    if (!conversationList) return;
    
    if (conversations.length === 0) {
        const emptyMessage = document.createElement('div');
        emptyMessage.classList.add('empty-conversations');
        
        if (highlightQuery) {
            emptyMessage.textContent = `No conversations found matching "${highlightQuery}". Try a different search term.`;
        } else {
            emptyMessage.textContent = 'No conversations yet. Start chatting to create one!';
        }
        
        conversationList.appendChild(emptyMessage);
        return;
    }
    
    conversations.forEach(convo => {
        const convoItem = document.createElement('div');
        convoItem.classList.add('conversation-item');
        convoItem.dataset.conversationId = convo.id;
        
        // Add pinned status
        if (convo.isPinned) {
            convoItem.classList.add('pinned');
        }
        
        // Create title and controls container
        const titleContainer = document.createElement('div');
        titleContainer.classList.add('conversation-title');
        
        // Add pin icon
        const pinIcon = document.createElement('span');
        pinIcon.classList.add('pin-icon');
        pinIcon.innerHTML = convo.isPinned ? 
            '<i class="fas fa-thumbtack"></i>' : 
            '<i class="far fa-thumbtack"></i>';
        pinIcon.title = convo.isPinned ? 'Unpin conversation' : 'Pin conversation';
        
        // Add title
        const titleSpan = document.createElement('span');
        titleSpan.textContent = convo.title;
        titleSpan.classList.add('title-text');
        
        // Add pin/unpin handler
        pinIcon.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent loading the conversation
            conversationStorage.pinConversation(convo.id, !convo.isPinned);
            updateConversationListUI();
        });
        
        // Assemble the title container
        titleContainer.appendChild(pinIcon);
        titleContainer.appendChild(titleSpan);
        convoItem.appendChild(titleContainer);
        
        // Add preview if available
        if (convo.messages && convo.messages.length > 0) {
            const previewDiv = document.createElement('div');
            previewDiv.classList.add('conversation-preview');
            const lastMessage = convo.messages[convo.messages.length - 1];
            const previewText = lastMessage.text.substring(0, 60) + (lastMessage.text.length > 60 ? '...' : '');
            previewDiv.textContent = previewText;
            convoItem.appendChild(previewDiv);
        }
        
        // Add project badge if assigned to a project
        if (convo.projectId) {
            const projectBadge = document.createElement('div');
            projectBadge.classList.add('project-badge');
            
            // Get project name (if available) or use project ID
            const projectName = getProjectName(convo.projectId) || `Project ${convo.projectId}`;
            projectBadge.textContent = projectName;
            
            // Append the badge
            convoItem.appendChild(projectBadge);
        }
        
        // Set click handler to load the conversation
        convoItem.addEventListener('click', () => loadConversation(convo.id));
        
        // Add to the list
        conversationList.appendChild(convoItem);
    });
}

// Standard function to update conversation list without search
function updateConversationListUI() {
    updateConversationListWithSearch(''); // Call with empty search query
}

// Load past conversations into the floating chat
function loadConversation(conversationId) {
    const conversation = conversationStorage.getConversation(conversationId);
    if (!conversation) return;
    
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) {
        console.warn('Chat messages element not found');
        return;
    }
    
    chatMessages.innerHTML = conversation.messages.map(m => `
        <div class="message ${m.sender}">
            <span>${m.text}</span>
        </div>
    `).join('');
    
    // Set the current conversation ID
    window.currentConversationId = conversationId;
    
    // Update UI to show which conversation is active
    updateActiveConversationIndicator(conversationId);
}

// Update the visual indicator for the active conversation
function updateActiveConversationIndicator(conversationId) {
    const items = document.querySelectorAll('.conversation-item');
    items.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.conversationId === conversationId) {
            item.classList.add('active');
        }
    });
}

/**
 * Get the name of a project by its ID
 * @param {string} projectId - ID of the project
 * @returns {string} Project name or null if not found
 */
function getProjectName(projectId) {
    // Try to get project name from the projects system if available
    if (window.projectManager && typeof window.projectManager.getProjectName === 'function') {
        return window.projectManager.getProjectName(projectId);
    }
    
    // Try to get from localStorage
    try {
        const projects = JSON.parse(localStorage.getItem('minerva_projects')) || {};
        if (projects[projectId] && projects[projectId].name) {
            return projects[projectId].name;
        }
    } catch (e) {
        console.error('Error fetching project name:', e);
    }
    
    return null;
}

/**
 * Get the current active project context if any
 * @returns {string|null} Project ID or null if no project is active
 */
function getCurrentActiveProject() {
    // Check URL parameters for project context
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    // If we have a project ID in the URL, use that
    if (projectId) {
        return projectId;
    }
    
    // Check global variable if set by application
    if (window.currentProjectId) {
        return window.currentProjectId;
    }
    
    return null;
}

/**
 * Start a new conversation, optionally in a project context
 * @returns {string} ID of the new conversation
 */
function startNewConversation() {
    // Generate a new conversation ID
    const conversationId = 'conv_' + Date.now();
    
    // Check if we have a current project context
    const currentProject = getCurrentActiveProject();
    
    // Create empty conversation with project assignment if needed
    if (currentProject) {
        conversationStorage.assignToProject(conversationId, currentProject);
    }
    
    // Update UI
    updateConversationListUI();
    
    return conversationId;
}

// Initialize the conversation storage system
function initConversationStorage() {
    console.log('Initializing conversation storage system...');
    
    // Create conversation list if it doesn't exist
    if (!document.getElementById('conversation-list')) {
        const chatInterface = document.getElementById('chat-interface');
        if (chatInterface) {
            const conversationListContainer = document.createElement('div');
            conversationListContainer.id = 'conversation-list-container';
            conversationListContainer.innerHTML = `
                <h3>Recent Conversations</h3>
                <div class="conversation-controls">
                    <input type="text" id="conversation-search" placeholder="Search conversations..." />
                    <button id="new-conversation-btn">New Chat</button>
                </div>
                <div id="conversation-list"></div>
            `;
            
            // Insert before the chat messages area
            const chatMessages = chatInterface.querySelector('#chat-messages');
            if (chatMessages) {
                chatInterface.insertBefore(conversationListContainer, chatMessages);
            } else {
                chatInterface.appendChild(conversationListContainer);
            }
            
            // Add event listener for new conversation button
            const newConversationBtn = document.getElementById('new-conversation-btn');
            if (newConversationBtn) {
                newConversationBtn.addEventListener('click', () => {
                    window.currentConversationId = startNewConversation();
                    document.getElementById('chat-messages').innerHTML = '';
                    updateConversationListUI();
                });
            }
            
            // Add event listener for search input
            const searchInput = document.getElementById('conversation-search');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    const query = e.target.value.trim();
                    updateConversationListWithSearch(query);
                });
            }
        }
    }
    
    // Update the conversation list
    updateConversationListUI();
    
    // Set up a handler for the send button
    const sendButton = document.getElementById('send-message');
    const messageInput = document.getElementById('user-message');
    
    if (sendButton && messageInput) {
        // Save the original onclick handler
        const originalOnClick = sendButton.onclick;
        
        // Replace with our enhanced handler
        sendButton.onclick = function() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Ensure we have a conversation ID
            if (!window.currentConversationId) {
                window.currentConversationId = 'conv_' + Date.now();
            }
            
            // Save the message to our storage system
            handleNewMessage(window.currentConversationId, message, 'user');
            
            // Call the original handler
            if (originalOnClick) {
                originalOnClick.call(this);
            }
        };
    }
    
    console.log('Conversation storage system initialized');
}

// Initialize our storage system independently, focused on the floating chat UI
document.addEventListener('DOMContentLoaded', function() {
    // Check if we have a chat interface element
    const chatInterface = document.getElementById('chat-interface');
    if (chatInterface) {
        console.log('Initializing floating chat conversation storage...');
        initConversationStorage();
    }
});

// Make our functions available globally to integrate with the existing system
window.enhancedConversationStorage = {
    saveMessage: function(conversationId, message, sender) {
        return conversationStorage.saveMessage(conversationId, message, sender);
    },
    getConversation: function(conversationId) {
        return conversationStorage.getConversation(conversationId);
    },
    pinConversation: function(conversationId, isPinned) {
        return conversationStorage.pinConversation(conversationId, isPinned);
    },
    assignToProject: function(conversationId, projectId) {
        return conversationStorage.assignToProject(conversationId, projectId);
    },
    // Important methods for memory integration
    importConversations: function(conversationData) {
        console.log('Importing conversations to enhanced storage system:', Object.keys(conversationData).length);
        // Process each conversation for import
        Object.entries(conversationData).forEach(([id, convData]) => {
            let existing = conversationStorage.getConversation(id);
            if (!existing) {
                // Create new conversation
                const newConv = {
                    id: id,
                    title: convData.title || 'Imported Conversation',
                    messages: (convData.messages || []).map(m => ({
                        sender: m.role,
                        text: m.content,
                        timestamp: m.timestamp || new Date().toISOString(),
                        model_info: m.model_info || null,
                        memory_references: m.memory_references || []
                    })),
                    timestamp: convData.created || new Date().toISOString(),
                    isPinned: convData.isPinned || false,
                    projectId: convData.project || null,
                    hasMemories: convData.hasMemories || false,
                    memoryReferences: convData.memoryReferences || []
                };
                conversationStorage.conversations.push(newConv);
                console.log('Created new conversation in storage with ID:', id);
            } else {
                // Update existing conversation
                existing.title = convData.title || existing.title;
                existing.isPinned = convData.isPinned || existing.isPinned;
                existing.projectId = convData.project || existing.projectId;
                existing.hasMemories = convData.hasMemories || existing.hasMemories || false;
                existing.memoryReferences = convData.memoryReferences || existing.memoryReferences || [];
                
                // Merge messages if needed
                if (convData.messages && convData.messages.length > 0) {
                    // Simple approach - replace if the new one has more messages
                    if (convData.messages.length > existing.messages.length) {
                        existing.messages = convData.messages.map(m => ({
                            sender: m.role,
                            text: m.content,
                            timestamp: m.timestamp || new Date().toISOString()
                        }));
                    }
                }
            }
        });
        
        // Update storage after import
        conversationStorage.updateStorage();
        return true;
    },
    // Add additional required methods for integration
    generateSmartTitle: function(conversationId, firstMessage) {
        let conversation = conversationStorage.getConversation(conversationId);
        if (conversation) {
            conversation.title = conversationStorage.generateTitle(firstMessage);
            conversationStorage.updateStorage();
            return conversation.title;
        }
        return null;
    },
    updateConversation: function(conversationId, updates) {
        let conversation = conversationStorage.getConversation(conversationId);
        if (conversation) {
            // Apply all updates to the conversation object
            Object.assign(conversation, updates);
            conversationStorage.updateStorage();
            return true;
        }
        return false;
    },
    getRecentConversations: function() {
        return conversationStorage.getRecentConversations();
    }
};
