/**
 * Conversations Manager Initialization
 * 
 * Handles the initialization and display of conversations in Minerva
 */

// Make sure this function is available globally
window.initConversationsManager = function() {
    console.log('Initializing Conversations Manager');
    
    // Make sure we have the conversations view container
    ensureConversationsViewExists();
    
    // Load conversations from storage
    loadConversations();
    
    // Set up event listeners
    setupEventListeners();
};

/**
 * Make sure the conversations view container exists
 */
function ensureConversationsViewExists() {
    let conversationsView = document.getElementById('conversations-view');
    
    if (!conversationsView) {
        console.log('Conversations view element not found, creating it');
        
        // Create the container
        conversationsView = document.createElement('div');
        conversationsView.id = 'conversations-view';
        conversationsView.className = 'conversations-view';
        
        // Create inner HTML structure
        conversationsView.innerHTML = `
            <h1>Your Conversations</h1>
            <p>View, search, and manage your previous conversations with Minerva.</p>
            
            <div class="control-panel">
                <div class="search-container">
                    <input type="text" id="conversation-search" placeholder="Search conversations...">
                    <button id="search-button">Search</button>
                </div>
                <div class="filter-container">
                    <select id="project-filter">
                        <option value="all">All Projects</option>
                        <option value="none">Unassigned</option>
                    </select>
                </div>
                <div class="sort-container">
                    <select id="sort-options">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="az">A-Z</option>
                        <option value="za">Z-A</option>
                    </select>
                </div>
            </div>
            
            <div class="conversations-container" id="conversations-container">
                <div class="loading-conversations">Loading conversations...</div>
            </div>
            
            <div id="conversation-detail-view" class="hidden"></div>
        `;
        
        // Add it to the content display
        const contentDisplay = document.getElementById('content-display');
        if (contentDisplay) {
            contentDisplay.appendChild(conversationsView);
        } else {
            // Fallback to body if content display doesn't exist
            document.body.appendChild(conversationsView);
        }
    }
    
    // Make sure it starts hidden if we're not on the conversations section
    const currentSection = document.querySelector('.nav-option.active');
    if (currentSection && currentSection.getAttribute('data-section') !== 'conversations') {
        conversationsView.classList.add('hidden');
    }
    
    // Make sure the stylesheet is loaded
    if (typeof addConversationsStylesheet === 'function') {
        addConversationsStylesheet();
    } else {
        // Add stylesheet directly if function not available
        if (!document.querySelector('link[href*="conversations-manager.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'static/css/conversations-manager.css';
            document.head.appendChild(link);
        }
    }
}

/**
 * Load conversations from storage and display them
 */
function loadConversations() {
    // First, get the conversations container
    const container = document.getElementById('conversations-container');
    if (!container) return;
    
    // Start with loading indicator
    container.innerHTML = '<div class="loading-conversations">Loading conversations...</div>';
    
    let conversations = [];
    
    // Try to get conversations from conversation manager
    if (window.conversationManager) {
        conversations = window.conversationManager.getAllConversations();
        displayConversations(conversations);
    } else {
        // Try to load from localStorage directly
        try {
            const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
            if (savedConversations && savedConversations.general) {
                conversations = savedConversations.general.map(conv => ({...conv, type: 'general'}));
                
                // Add project conversations if they exist
                if (savedConversations.projects) {
                    for (const projectId in savedConversations.projects) {
                        const projectConvs = savedConversations.projects[projectId].map(conv => 
                            ({...conv, type: 'project', projectId}));
                        conversations = conversations.concat(projectConvs);
                    }
                }
                
                displayConversations(conversations);
            } else {
                // No conversations found
                container.innerHTML = '<div class="empty-state">No conversations found. Start a new conversation to see it here.</div>';
            }
        } catch (e) {
            console.error('Error loading conversations from localStorage:', e);
            container.innerHTML = '<div class="error-state">Error loading conversations. Please try again later.</div>';
        }
    }
}

/**
 * Display conversations in the container
 * @param {Array} conversations - Array of conversation objects
 */
function displayConversations(conversations) {
    // Get the container
    const container = document.getElementById('conversations-container');
    if (!container) return;
    
    // If no conversations, show empty state
    if (!conversations || conversations.length === 0) {
        container.innerHTML = '<div class="empty-state">No conversations found. Start a new conversation to see it here.</div>';
        return;
    }
    
    // Sort conversations by date (newest first)
    const sorted = [...conversations].sort((a, b) => {
        const dateA = new Date(a.lastUpdated || a.created || 0);
        const dateB = new Date(b.lastUpdated || b.created || 0);
        return dateB - dateA;
    });
    
    // Clear container
    container.innerHTML = '';
    
    // Create conversation cards
    sorted.forEach(conversation => {
        const card = createConversationCard(conversation);
        container.appendChild(card);
    });
    
    // Add event listeners to cards
    setupConversationCardListeners();
}

/**
 * Create a conversation card element
 * @param {Object} conversation - Conversation object
 * @returns {HTMLElement} - Conversation card element
 */
function createConversationCard(conversation) {
    const card = document.createElement('div');
    card.className = 'conversation-card';
    card.setAttribute('data-id', conversation.id);
    card.setAttribute('data-conversation-id', conversation.id);
    
    // Format the date
    const date = new Date(conversation.lastUpdated || conversation.created);
    const formattedTime = date.toLocaleString();
    
    // Get message count
    const messageCount = conversation.messages ? conversation.messages.length : 0;
    
    // Generate a preview from the messages
    const preview = conversation.messages && conversation.messages.length > 0 
        ? conversation.messages[conversation.messages.length - 1].content.substring(0, 100) + (conversation.messages[conversation.messages.length - 1].content.length > 100 ? '...' : '')
        : 'No messages';
    
    // Create badges
    let badges = '';
    if (conversation.tags && conversation.tags.length > 0) {
        badges += conversation.tags.map(tag => `<span class="badge tag">${tag}</span>`).join('');
    }
    if (conversation.project) {
        badges += `<span class="badge project">${conversation.project}</span>`;
    }
    if (conversation.hasMemories) {
        badges += `<span class="badge memory">Memories</span>`;
    }
    
    // Create HTML for the card
    card.innerHTML = `
        <div class="conversation-header">
            <h3>${conversation.title}</h3>
            <div class="action-buttons">
                <button class="action-btn" title="Open Conversation">
                    <span class="icon">💬</span>
                </button>
                <button class="action-btn" title="Rename">
                    <span class="icon">✏️</span>
                </button>
                <button class="action-btn convert-project-btn" title="Convert to Project">
                    <span class="icon">📂</span>
                </button>
                <button class="action-btn" title="${conversation.isArchived ? 'Unarchive' : 'Archive'}">
                    <span class="icon">${conversation.isArchived ? '📤' : '📥'}</span>
                </button>
                <button class="action-btn" title="Delete">
                    <span class="icon">🗑️</span>
                </button>
            </div>
        </div>
        <div class="conversation-preview">${preview}</div>
        <div class="conversation-meta">
            <div class="conversation-time">${formattedTime}</div>
            <div class="conversation-message-count">${messageCount} messages</div>
        </div>
        <div class="conversation-badges">
            ${badges}
        </div>
    `;
    
    return card;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search button
    const searchButton = document.getElementById('search-button');
    const searchInput = document.getElementById('conversation-search');
    
    if (searchButton && searchInput) {
        searchButton.addEventListener('click', () => {
            filterConversations(searchInput.value);
        });
        
        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                filterConversations(searchInput.value);
            }
        });
    }
    
    // Project filter
    const projectFilter = document.getElementById('project-filter');
    if (projectFilter) {
        projectFilter.addEventListener('change', () => {
            filterConversationsByProject(projectFilter.value);
        });
    }
    
    // Sort options
    const sortOptions = document.getElementById('sort-options');
    if (sortOptions) {
        sortOptions.addEventListener('change', () => {
            sortConversations(sortOptions.value);
        });
    }
}

/**
 * Filter conversations by search term
 * @param {string} searchTerm - Search term
 */
function filterConversations(searchTerm) {
    if (!searchTerm) {
        // Reset to show all conversations
        loadConversations();
        return;
    }
    
    // Get all conversations
    let conversations = [];
    if (window.conversationManager) {
        conversations = window.conversationManager.getAllConversations();
    } else {
        try {
            const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
            if (savedConversations && savedConversations.general) {
                conversations = savedConversations.general.map(conv => ({...conv, type: 'general'}));
                
                // Add project conversations if they exist
                if (savedConversations.projects) {
                    for (const projectId in savedConversations.projects) {
                        const projectConvs = savedConversations.projects[projectId].map(conv => 
                            ({...conv, type: 'project', projectId}));
                        conversations = conversations.concat(projectConvs);
                    }
                }
            }
        } catch (e) {
            console.error('Error loading conversations for filtering:', e);
        }
    }
    
    // Filter conversations
    const filtered = conversations.filter(conversation => {
        const title = conversation.title.toLowerCase();
        const term = searchTerm.toLowerCase();
        
        // Check title
        if (title.includes(term)) return true;
        
        // Check messages
        if (conversation.messages) {
            for (const msg of conversation.messages) {
                if (msg.content.toLowerCase().includes(term)) return true;
            }
        }
        
        // Check tags
        if (conversation.tags) {
            for (const tag of conversation.tags) {
                if (tag.toLowerCase().includes(term)) return true;
            }
        }
        
        return false;
    });
    
    // Display filtered conversations
    displayConversations(filtered);
}

/**
 * Filter conversations by project
 * @param {string} projectFilter - Project filter value
 */
function filterConversationsByProject(projectFilter) {
    // Get all conversations
    let conversations = [];
    if (window.conversationManager) {
        conversations = window.conversationManager.getAllConversations();
    } else {
        try {
            const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
            if (savedConversations && savedConversations.general) {
                conversations = savedConversations.general.map(conv => ({...conv, type: 'general'}));
                
                // Add project conversations if they exist
                if (savedConversations.projects) {
                    for (const projectId in savedConversations.projects) {
                        const projectConvs = savedConversations.projects[projectId].map(conv => 
                            ({...conv, type: 'project', projectId}));
                        conversations = conversations.concat(projectConvs);
                    }
                }
            }
        } catch (e) {
            console.error('Error loading conversations for project filtering:', e);
        }
    }
    
    // Filter by project
    let filtered = conversations;
    
    if (projectFilter === 'none') {
        // Only show conversations without a project
        filtered = conversations.filter(conv => !conv.project);
    } else if (projectFilter !== 'all') {
        // Show conversations for a specific project
        filtered = conversations.filter(conv => conv.project === projectFilter);
    }
    
    // Display filtered conversations
    displayConversations(filtered);
}

/**
 * Sort conversations
 * @param {string} sortOption - Sort option value
 */
function sortConversations(sortOption) {
    // Get container and all cards
    const container = document.getElementById('conversations-container');
    const cards = Array.from(container.querySelectorAll('.conversation-card'));
    
    if (cards.length === 0) return;
    
    // Sort cards based on option
    cards.sort((a, b) => {
        const titleA = a.querySelector('h3').textContent;
        const titleB = b.querySelector('h3').textContent;
        
        const dateA = new Date(a.querySelector('.conversation-time').textContent);
        const dateB = new Date(b.querySelector('.conversation-time').textContent);
        
        switch (sortOption) {
            case 'newest':
                return dateB - dateA;
            case 'oldest':
                return dateA - dateB;
            case 'az':
                return titleA.localeCompare(titleB);
            case 'za':
                return titleB.localeCompare(titleA);
            default:
                return 0;
        }
    });
    
    // Clear container and re-append sorted cards
    container.innerHTML = '';
    cards.forEach(card => container.appendChild(card));
    
    // Re-setup listeners
    setupConversationCardListeners();
}
