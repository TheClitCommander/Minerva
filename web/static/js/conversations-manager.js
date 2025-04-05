/**
 * Minerva Conversations Manager
 * Handles conversation listings, searching, filtering, and project conversion
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the conversations manager once DOM is loaded
    initConversationsManager();
});

/**
 * Initialize the Conversations Manager
 */
function initConversationsManager() {
    // Ensure conversations container exists
    ensureConversationsContainer();

    // Load and display conversations
    loadConversations();
    
    // Setup event listeners for conversation actions
    setupConversationCardListeners();
    
    // Setup search, filter and sort functionality
    setupSearchAndFilters();
    
    // Ensure navigation to conversations view works
    setupConversationsNavigation();
    
    // Add CSS link to head if not already present
    addConversationsStylesheet();
    
    console.log('Conversations Manager initialized');
}

/**
 * Ensure conversations container exists in the DOM
 */
function ensureConversationsContainer() {
    // Check if conversations view exists
    let conversationsView = document.getElementById('conversations-view');
    
    // If not, create it
    if (!conversationsView) {
        conversationsView = document.createElement('div');
        conversationsView.id = 'conversations-view';
        conversationsView.className = 'conversations-view hidden';
        
        // Add header
        conversationsView.innerHTML = `
            <h1>💬 Conversations & Logs</h1>
            <p>All your conversations are automatically saved here. You can rename, archive, or convert them to projects.</p>
            
            <!-- Search and Filter Controls -->
            <div class="control-panel">
                <div class="search-container">
                    <input type="text" id="conversation-search" placeholder="Search conversations...">
                    <button id="search-btn"><span class="icon">🔍</span></button>
                </div>
                <div class="filter-container">
                    <select id="conversation-filter">
                        <option value="all">All Conversations</option>
                        <option value="with-memories">With Memories</option>
                        <option value="recent">Recent</option>
                        <option value="archived">Archived</option>
                    </select>
                    <select id="project-filter">
                        <option value="all-projects">All Projects</option>
                        <option value="unassigned">Unassigned</option>
                        <!-- Projects will be loaded dynamically -->
                    </select>
                    <select id="conversation-sort">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="a-z">A-Z</option>
                        <option value="z-a">Z-A</option>
                    </select>
                </div>
            </div>
            
            <div id="search-results-info" class="search-results-info"></div>
            
            <div class="conversations-container" id="conversations-container">
                <!-- Conversations will be loaded here by date and project -->
            </div>
            
            <div class="pagination-controls">
                <button id="prev-page" disabled>Previous</button>
                <span class="page-indicator">Page 1 of 1</span>
                <button id="next-page" disabled>Next</button>
            </div>
        `;
        
        // Add to content display
        const contentDisplay = document.getElementById('content-display');
        if (contentDisplay) {
            contentDisplay.appendChild(conversationsView);
        }
    }
}

/**
 * Load and display conversations categorized by date and project
 */
function loadConversations() {
    console.log('Loading conversations from storage...');
    
    // Try to load real conversations first
    let conversations = [];
    let fromStorage = false;
    
    // Check if we can get conversations from the MinervaConversationManager instance
    if (window.conversationManager && typeof window.conversationManager.getAllConversations === 'function') {
        console.log('Using window.conversationManager to load conversations');
        const allConversations = window.conversationManager.getAllConversations();
        
        // Convert to array format
        for (const id in allConversations) {
            if (allConversations.hasOwnProperty(id)) {
                const conv = allConversations[id];
                conversations.push({
                    id: id,
                    title: conv.title || 'Untitled Conversation',
                    preview: conv.summary || (conv.messages && conv.messages.length > 0 ? conv.messages[0].content.substring(0, 100) + '...' : 'No preview available'),
                    date: conv.created || new Date().toISOString(),
                    messageCount: conv.messages ? conv.messages.length : 0,
                    hasMemories: conv.hasMemories || false,
                    isArchived: conv.archived || false,
                    project: conv.project || null
                });
            }
        }
        fromStorage = true;
    } else {
        // Try to load from localStorage directly
        try {
            const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
            if (savedConversations && savedConversations.general && savedConversations.general.length > 0) {
                console.log('Found conversations in localStorage');
                conversations = savedConversations.general.map(conv => ({
                    id: conv.id,
                    title: conv.title || 'Untitled Conversation',
                    preview: conv.summary || (conv.messages && conv.messages.length > 0 ? conv.messages[0].content.substring(0, 100) + '...' : 'No preview available'),
                    date: conv.created || new Date().toISOString(),
                    messageCount: conv.messages ? conv.messages.length : 0,
                    hasMemories: conv.hasMemories || false,
                    isArchived: conv.archived || false,
                    project: conv.project || null
                }));
                fromStorage = true;
            }
        } catch (e) {
            console.error('Error loading conversations from localStorage:', e);
        }
    }
    
    // If no conversations found in storage, use demo data
    if (!fromStorage || conversations.length === 0) {
        console.log('No conversations found in storage, using demo data');
        conversations = [
        {
            id: 'conv1',
            title: 'Quantum Computing Analysis',
            preview: 'Exploring quantum computing applications in cryptography and optimization problems.',
            date: '2025-03-16T14:30:00',
            messageCount: 42,
            hasMemories: true,
            isArchived: false,
            project: 'Quantum Research'
        },
        {
            id: 'conv2',
            title: 'Neural Network Architecture',
            preview: 'Discussing various neural network architectures for image recognition tasks.',
            date: '2025-03-16T10:15:00',
            messageCount: 28,
            hasMemories: true,
            isArchived: false,
            project: 'AI Models'
        },
        {
            id: 'conv3',
            title: 'Project Planning for Q2',
            preview: 'Outlining research objectives and milestones for the second quarter.',
            date: '2025-03-15T16:45:00',
            messageCount: 15,
            hasMemories: false,
            isArchived: false,
            project: null
        },
        {
            id: 'conv4',
            title: 'Literature Review: Transformers',
            preview: 'Analyzing recent papers on transformer architectures and their applications.',
            date: '2025-03-14T09:20:00',
            messageCount: 33,
            hasMemories: true,
            isArchived: false,
            project: 'AI Models'
        },
        {
            id: 'conv5',
            title: 'Debugging Neural Network',
            preview: 'Troubleshooting convergence issues in the training process.',
            date: '2025-03-12T11:05:00',
            messageCount: 19,
            hasMemories: false,
            isArchived: true,
            project: 'AI Models'
        },
        {
            id: 'conv6',
            title: 'Quantum Entanglement Experiment',
            preview: 'Discussing the setup for a quantum entanglement demonstration.',
            date: '2025-03-10T15:30:00',
            messageCount: 24,
            hasMemories: true,
            isArchived: false,
            project: 'Quantum Research'
        }
    ];
    
    // Get the container where we'll add the conversations
    const container = document.getElementById('conversations-container');
    if (!container) return;
    
    // Clear the container
    container.innerHTML = '';
    
    // Load available projects for the filter dropdown
    loadProjectsForFilter(mockConversations);
    
    // Group conversations by date
    const conversationsByDate = groupConversationsByDate(mockConversations);
    
    // Sort dates in descending order (newest first)
    const sortedDates = Object.keys(conversationsByDate).sort((a, b) => new Date(b) - new Date(a));
    
    // Display conversations grouped by date
    sortedDates.forEach(date => {
        // Create date header
        const dateHeader = document.createElement('div');
        dateHeader.className = 'date-header';
        dateHeader.innerHTML = `<h2>${formatDateHeader(date)}</h2>`;
        container.appendChild(dateHeader);
        
        // Create conversation group for this date
        const dateGroup = document.createElement('div');
        dateGroup.className = 'conversation-group';
        container.appendChild(dateGroup);
        
        // Add each conversation for this date
        conversationsByDate[date].forEach(conversation => {
            const card = createConversationCard(conversation);
            dateGroup.appendChild(card);
        });
    });
    
    // Setup event listeners for the newly created cards
    setupConversationCardListeners();
}

/**
 * Format date for header display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDateHeader(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Check if date is today
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    }
    
    // Check if date is yesterday
    if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday';
    }
    
    // For other dates, use date format
    const options = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

/**
 * Group conversations by date (year-month-day)
 * @param {Array} conversations - List of conversations
 * @returns {Object} Conversations grouped by date
 */
function groupConversationsByDate(conversations) {
    const groups = {};
    
    conversations.forEach(conversation => {
        // Extract just the date part (YYYY-MM-DD)
        const datePart = conversation.date.split('T')[0];
        
        // Initialize the array for this date if it doesn't exist
        if (!groups[datePart]) {
            groups[datePart] = [];
        }
        
        // Add the conversation to the appropriate date group
        groups[datePart].push(conversation);
    });
    
    return groups;
}

/**
 * Create a conversation card element
 * @param {Object} conversation - Conversation data
 * @returns {Element} Conversation card element
 */
function createConversationCard(conversation) {
    const card = document.createElement('div');
    card.className = 'conversation-card';
    card.setAttribute('data-id', conversation.id);
    card.setAttribute('data-has-memories', conversation.hasMemories);
    card.setAttribute('data-archived', conversation.isArchived);
    
    if (conversation.project) {
        card.setAttribute('data-project', conversation.project);
    }
    
    // Format the date for display
    const date = new Date(conversation.date);
    const formattedTime = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    
    // Create status badges
    let badges = '';
    
    if (conversation.hasMemories) {
        badges += `<span class="badge memory">Has Memories</span>`;
    }
    
    if (conversation.isArchived) {
        badges += `<span class="badge archived">Archived</span>`;
    }
    
    if (conversation.project) {
        badges += `<span class="badge project">${conversation.project}</span>`;
    }
    
    // Build the card HTML
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
        <div class="conversation-preview">${conversation.preview}</div>
        <div class="conversation-meta">
            <div class="conversation-time">${formattedTime}</div>
            <div class="conversation-message-count">${conversation.messageCount} messages</div>
        </div>
        <div class="conversation-badges">
            ${badges}
        </div>
    `;
    
    return card;
}

/**
 * Load available projects for the filter dropdown
 * @param {Array} conversations - List of conversations
 */
function loadProjectsForFilter(conversations) {
    // Get all unique project names
    const projects = new Set();
    conversations.forEach(conversation => {
        if (conversation.project) {
            projects.add(conversation.project);
        }
    });
    
    // Get the project filter dropdown
    const projectFilter = document.getElementById('project-filter');
    if (!projectFilter) return;
    
    // Keep the first two options (All Projects and Unassigned)
    const defaultOptions = [
        projectFilter.options[0].outerHTML,
        projectFilter.options[1].outerHTML
    ].join('');
    
    // Add project options
    projectFilter.innerHTML = defaultOptions;
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project;
        option.textContent = project;
        projectFilter.appendChild(option);
    });
}

/**
 * Add conversations stylesheet if not already in document
 */
function addConversationsStylesheet() {
    if (!document.querySelector('link[href*="conversations-manager.css"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'static/css/conversations-manager.css';
        document.head.appendChild(link);
        console.log('Conversations Manager stylesheet added');
    }
    
    // Also add inline styles for conversation selection
    const style = document.createElement('style');
    style.textContent = `
        .inactive-conversation {
            opacity: 0.6;
            transform: scale(0.95);
            transition: all 0.3s ease;
        }
        
        .active-conversation {
            opacity: 1;
            transform: scale(1);
            box-shadow: 0 0 15px rgba(70, 130, 180, 0.6);
            border: 1px solid rgba(70, 130, 180, 0.8);
            transition: all 0.3s ease;
        }
        
        #conversation-detail-view {
            background: rgba(30, 30, 40, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .conversation-messages {
            max-height: 400px;
            overflow-y: auto;
            padding: 10px;
            background: rgba(20, 20, 30, 0.7);
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .message {
            padding: 10px;
            margin: 8px 0;
            border-radius: 8px;
        }
        
        .user-message {
            background: rgba(70, 130, 180, 0.3);
            border-left: 3px solid steelblue;
            text-align: right;
        }
        
        .assistant-message {
            background: rgba(60, 179, 113, 0.3);
            border-left: 3px solid mediumseagreen;
        }
        
        .detail-actions {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Setup navigation to the conversations view
 */
function setupConversationsNavigation() {
    // Get navigation option for conversations
    const conversationsNavOption = document.querySelector('.nav-option[data-section="conversations"]');
    
    if (conversationsNavOption) {
        // Ensure we have the right event listener
        if (typeof handleNavOptionClick === 'function') {
            // If the dashboard already has a navigation handler, it will handle this
            console.log('Using existing navigation handler for conversations tab');
        } else {
            // Otherwise, add our own handler
            conversationsNavOption.addEventListener('click', function() {
                showConversationsView();
            });
            console.log('Added navigation handler for conversations tab');
        }
    }
}

/**
 * Show the conversations view and hide other views
 */
function showConversationsView() {
    // Hide all content views
    const allViews = document.querySelectorAll('#content-display > div');
    allViews.forEach(view => view.classList.add('hidden'));
    
    // Show conversations view
    const conversationsView = document.getElementById('conversations-view');
    if (conversationsView) {
        conversationsView.classList.remove('hidden');
        
        // Update active nav option
        const navOptions = document.querySelectorAll('.nav-option');
        navOptions.forEach(option => option.classList.remove('active'));
        
        const conversationsNavOption = document.querySelector('.nav-option[data-section="conversations"]');
        if (conversationsNavOption) {
            conversationsNavOption.classList.add('active');
        }
    }
}

/**
 * Setup event listeners for conversation card actions
 */
function setupConversationCardListeners() {
    // Open conversation
    const openButtons = document.querySelectorAll('.conversation-card .action-btn[title="Open Conversation"]');
    openButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.conversation-card');
            const title = card.querySelector('h3').textContent;
            openConversation(title);
        });
    });
    
    // Rename conversation
    const renameButtons = document.querySelectorAll('.conversation-card .action-btn[title="Rename"]');
    renameButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.conversation-card');
            const title = card.querySelector('h3').textContent;
            renameConversation(card, title);
        });
    });
    
    // Convert to project
    const convertButtons = document.querySelectorAll('.conversation-card .convert-project-btn');
    convertButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.conversation-card');
            const title = card.querySelector('h3').textContent;
            convertToProject(card, title);
        });
    });
    
    // Archive conversation
    const archiveButtons = document.querySelectorAll('.conversation-card .action-btn[title="Archive"]');
    archiveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.conversation-card');
            const title = card.querySelector('h3').textContent;
            archiveConversation(card, title);
        });
    });
    
    // Delete conversation
    const deleteButtons = document.querySelectorAll('.conversation-card .action-btn[title="Delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const card = this.closest('.conversation-card');
            const title = card.querySelector('h3').textContent;
            deleteConversation(card, title);
        });
    });
    
    // Make entire card clickable to open conversation
    const conversationCards = document.querySelectorAll('.conversation-card');
    conversationCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Only trigger if the click was directly on the card (not on a button)
            if (e.target === this || e.target.closest('.conversation-header') || 
                e.target.closest('.conversation-preview') || e.target.closest('.conversation-meta')) {
                const title = this.querySelector('h3').textContent;
                openConversation(title);
            }
        });
    });
}

/**
 * Open a conversation
 * @param {string} title - Conversation title
 */
function openConversation(title) {
    console.log(`Opening conversation: ${title}`);
    
    // Show notification
    showNotification(`Opening conversation: ${title}`, 'info');
    
    // Get conversation ID from title
    let conversationId = null;
    let conversationData = null;
    
    // Access the conversation manager to get the conversation
    if (window.conversationManager) {
        // Use the existing MinervaConversationManager instance
        const allConversations = window.conversationManager.getAllConversations();
        
        // Find the conversation with the matching title
        for (const id in allConversations) {
            if (allConversations[id].title === title) {
                conversationId = id;
                conversationData = allConversations[id];
                break;
            }
        }
    } else {
        // Try to get from localStorage directly if no manager instance
        try {
            const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
            if (savedConversations && savedConversations.general) {
                const found = savedConversations.general.find(conv => conv.title === title);
                if (found) {
                    conversationId = found.id;
                    conversationData = found;
                }
            }
        } catch (e) {
            console.error('Failed to retrieve conversation:', e);
        }
    }
    
    if (!conversationId) {
        console.warn(`Conversation "${title}" not found`);
        showNotification(`Conversation "${title}" not found`, 'error');
        return;
    }
    
    // Visual treatment - make all other conversations visually dimmed
    const allCards = document.querySelectorAll('.conversation-card');
    allCards.forEach(card => {
        // Mark all cards as inactive first
        card.classList.add('inactive-conversation');
        card.classList.remove('active-conversation');
    });
    
    // Find the selected card by title and make it active
    const selectedCard = Array.from(allCards).find(card => {
        return card.querySelector('h3').textContent === title;
    });
    
    if (selectedCard) {
        // Activate the selected card
        selectedCard.classList.remove('inactive-conversation');
        selectedCard.classList.add('active-conversation');
        
        // Make sure it's visible (scroll to it if needed)
        selectedCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    try {
        // Navigate to minerva_central.html with conversation ID
        if (window.location.pathname.includes('dashboard.html')) {
            // We're in the dashboard, redirect to minerva_central.html with conversation ID
            window.location.href = `minerva_central.html?conversation=${conversationId}`;
            return;
        }
        
        // If we're already in minerva_central.html, try to load the conversation into the chat interface
        const chatInterface = document.getElementById('chat-interface');
        if (!chatInterface) {
            console.warn('Chat interface not found, redirecting to minerva_central.html');
            window.location.href = `minerva_central.html?conversation=${conversationId}`;
            return;
        }
        
        // Make sure the chat interface is visible
        chatInterface.style.display = 'flex';
        
        // Access the chat messages container
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) {
            console.error('Chat messages container not found');
            return;
        }
        
        // Clear current messages but keep a system message
        chatMessages.innerHTML = '<div class="system-message">Loading previous conversation...</div>';
        
        // Add conversation messages with proper formatting
        if (conversationData && conversationData.messages && conversationData.messages.length > 0) {
            conversationData.messages.forEach(msg => {
                // Preserve the existing Think Tank formatting
                if (msg.role === 'user') {
                    // User message
                    const userMsg = document.createElement('div');
                    userMsg.className = 'user-message';
                    userMsg.textContent = msg.content;
                    chatMessages.appendChild(userMsg);
                } else if (msg.role === 'assistant') {
                    // Assistant message - try to preserve any model info if available
                    if (typeof window.displayThinkTankResponse === 'function' && msg.model_info) {
                        // Use the existing display function if available
                        window.displayThinkTankResponse({
                            response: msg.content,
                            model_info: msg.model_info
                        }, true);
                    } else {
                        // Simple assistant message
                        const assistantMsg = document.createElement('div');
                        assistantMsg.className = 'assistant-message';
                        assistantMsg.textContent = msg.content;
                        chatMessages.appendChild(assistantMsg);
                    }
                }
            });
        } else {
            // No messages found
            chatMessages.innerHTML = '<div class="system-message">No messages found in this conversation.</div>';
        }
        
        // Update the conversation history global variable if it exists
        if (window.conversationHistory !== undefined) {
            window.conversationHistory = conversationData.messages || [];
            console.log('Updated global conversation history with loaded messages');
        }
        
        // Update the conversation ID if that variable exists
        if (window.conversationId !== undefined) {
            window.conversationId = conversationId;
            console.log('Updated global conversation ID');
        }
        
        // Scroll to bottom when all messages are loaded
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Show success notification
        showNotification('Conversation loaded successfully', 'success');
    } catch (error) {
        console.error('Error opening conversation:', error);
        showNotification(`Error opening conversation: ${error.message}`, 'error');
    }
}

/**
 * Rename a conversation
 * @param {Element} card - The conversation card element
 * @param {string} currentTitle - Current conversation title
 */
function renameConversation(card, currentTitle) {
    const newTitle = prompt(`Rename conversation: ${currentTitle}`, currentTitle);
    
    if (newTitle && newTitle !== currentTitle) {
        console.log(`Renaming conversation from "${currentTitle}" to "${newTitle}"`);
        
        // Update the title in the card
        const titleElement = card.querySelector('h3');
        if (titleElement) {
            titleElement.textContent = newTitle;
        }
        
        // In a complete implementation, this would:
        // 1. Update the conversation title in the database
        // 2. Refresh the conversation list
        
        showNotification(`Renamed to: ${newTitle}`, 'success');
    }
}

/**
 * Convert a conversation to a project
 * @param {Element} card - The conversation card element
 * @param {string} title - Conversation title
 */
function convertToProject(card, title) {
    console.log(`Converting conversation to project: ${title}`);
    
    // Show confirmation dialog
    if (confirm(`Convert "${title}" to a project? This will create a new project with this conversation as the starting point.`)) {
        // In a complete implementation, this would:
        // 1. Create a new project in the database
        // 2. Link the conversation to the project
        // 3. Navigate to the new project view
        
        showNotification(`Conversation "${title}" converted to project`, 'success');
        
        // Add a project badge to the card
        const badgesContainer = card.querySelector('.conversation-badges');
        if (badgesContainer) {
            const projectBadge = document.createElement('span');
            projectBadge.className = 'badge success';
            projectBadge.textContent = 'Project';
            badgesContainer.appendChild(projectBadge);
        }
        
        // Disable the convert button
        const convertBtn = card.querySelector('.convert-project-btn');
        if (convertBtn) {
            convertBtn.disabled = true;
            convertBtn.title = "Already converted to project";
            convertBtn.style.opacity = "0.5";
            convertBtn.style.cursor = "not-allowed";
        }
    }
}

/**
 * Archive a conversation
 * @param {Element} card - The conversation card element
 * @param {string} title - Conversation title
 */
function archiveConversation(card, title) {
    console.log(`Archiving conversation: ${title}`);
    
    if (confirm(`Archive conversation "${title}"? You can find it later in the archived conversations.`)) {
        // Add a subtle animation
        card.style.transition = "all 0.5s ease";
        card.style.opacity = "0.5";
        card.style.transform = "scale(0.95) translateY(10px)";
        
        // In a complete implementation, this would:
        // 1. Mark the conversation as archived in the database
        // 2. Refresh the conversation list or move card to archived section
        
        setTimeout(() => {
            // Add archived badge
            const badgesContainer = card.querySelector('.conversation-badges');
            if (badgesContainer) {
                const archivedBadge = document.createElement('span');
                archivedBadge.className = 'badge warning';
                archivedBadge.textContent = 'Archived';
                badgesContainer.appendChild(archivedBadge);
                
                // Remove recent badge if exists
                const recentBadge = badgesContainer.querySelector('.badge.recent');
                if (recentBadge) {
                    recentBadge.remove();
                }
            }
            
            card.style.opacity = "1";
            card.style.transform = "scale(1) translateY(0)";
            
            showNotification(`Conversation "${title}" archived`, 'success');
        }, 500);
    }
}

/**
 * Delete a conversation
 * @param {Element} card - The conversation card element
 * @param {string} title - Conversation title
 */
function deleteConversation(card, title) {
    console.log(`Deleting conversation: ${title}`);
    
    if (confirm(`Delete conversation "${title}"? This action cannot be undone.`)) {
        // Add a subtle animation
        card.style.transition = "all 0.5s ease";
        card.style.opacity = "0";
        card.style.transform = "scale(0.9)";
        
        // In a complete implementation, this would:
        // 1. Delete the conversation from the database
        // 2. Remove the card from the DOM
        
        setTimeout(() => {
            card.remove();
            showNotification(`Conversation "${title}" deleted`, 'success');
        }, 500);
    }
}

/**
 * Set up search, filter, and sort functionality
 */
function setupSearchAndFilters() {
    // Search functionality
    const searchInput = document.getElementById('conversation-search');
    const searchBtn = document.getElementById('search-btn');
    
    if (searchInput && searchBtn) {
        // Search on Enter key
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                performSearch(this.value);
            }
        });
        
        // Search on button click
        searchBtn.addEventListener('click', function() {
            performSearch(searchInput.value);
        });
    }
    
    // Filter functionality
    const filterSelect = document.getElementById('conversation-filter');
    // Project filter functionality
    const projectFilterSelect = document.getElementById('project-filter');
    
    // Apply filters when status filter changes
    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            const projectFilter = projectFilterSelect ? projectFilterSelect.value : 'all-projects';
            applyFilter(this.value, projectFilter);
        });
    }
    
    // Apply filters when project filter changes
    if (projectFilterSelect) {
        projectFilterSelect.addEventListener('change', function() {
            const statusFilter = filterSelect ? filterSelect.value : 'all';
            applyFilter(statusFilter, this.value);
        });
    }
    
    // Sort functionality
    const sortSelect = document.getElementById('conversation-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            applySort(this.value);
        });
    }
    
    // Pagination controls
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', function() {
            if (!this.disabled) {
                goToPreviousPage();
            }
        });
        
        nextBtn.addEventListener('click', function() {
            if (!this.disabled) {
                goToNextPage();
            }
        });
    }
}

/**
 * Perform search on conversations
 * @param {string} query - Search query
 */
function performSearch(query) {
    console.log(`Searching for: ${query}`);
    
    if (!query.trim()) {
        // If query is empty, show all conversations
        showAllConversations();
        return;
    }
    
    // Get all conversation cards
    const cards = document.querySelectorAll('.conversation-card');
    let matchCount = 0;
    
    cards.forEach(card => {
        const title = card.querySelector('h3').textContent.toLowerCase();
        const preview = card.querySelector('.conversation-preview').textContent.toLowerCase();
        const searchText = query.toLowerCase();
        
        if (title.includes(searchText) || preview.includes(searchText)) {
            card.style.display = 'flex';
            matchCount++;
            
            // Highlight matching text (for demonstration purposes)
            highlightMatches(card, searchText);
        } else {
            card.style.display = 'none';
        }
    });
    
    updateSearchResults(matchCount, query);
}

/**
 * Highlight matching text in cards (simple implementation)
 * @param {Element} card - The conversation card element
 * @param {string} searchText - Text to highlight
 */
function highlightMatches(card, searchText) {
    // This is a simplified highlight implementation
    // In a real implementation, would use a more robust approach like marking and replacing text nodes
    const title = card.querySelector('h3');
    const preview = card.querySelector('.conversation-preview');
    
    // For now, we're just adding a flash animation to matching cards
    card.style.animation = 'flash-highlight 1s ease';
    
    // Remove animation after it completes
    setTimeout(() => {
        card.style.animation = '';
    }, 1000);
}

/**
 * Show all conversations
 */
function showAllConversations() {
    const cards = document.querySelectorAll('.conversation-card');
    cards.forEach(card => {
        card.style.display = 'flex';
    });
    
    resetHighlights();
    updateSearchResults(cards.length, '');
}

/**
 * Reset any search highlighting
 */
function resetHighlights() {
    // Reset any custom highlighting
    document.querySelectorAll('.conversation-card h3, .conversation-card .conversation-preview')
        .forEach(el => {
            el.style.animation = '';
        });
}

/**
 * Update search results message
 * @param {number} count - Number of matching conversations
 * @param {string} query - Search query
 */
function updateSearchResults(count, query) {
    const searchMsg = query ? 
        `Found ${count} conversation${count !== 1 ? 's' : ''} matching "${query}"` : 
        'Showing all conversations';
    
    showNotification(searchMsg, 'info', true);
}

/**
 * Apply filter to conversations
 * @param {string} filter - Filter to apply
 */
function applyFilter(filter, projectFilter) {
    console.log(`Applying filter: ${filter}, Project filter: ${projectFilter || 'all'}`);
    
    // Get the project filter value if not provided
    if (projectFilter === undefined) {
        const projectFilterSelect = document.getElementById('project-filter');
        projectFilter = projectFilterSelect ? projectFilterSelect.value : 'all-projects';
    }
    
    const cards = document.querySelectorAll('.conversation-card');
    const dateHeaders = document.querySelectorAll('.date-header');
    const conversationGroups = document.querySelectorAll('.conversation-group');
    
    // Reset visibility of date headers and groups
    dateHeaders.forEach(header => header.style.display = 'none');
    conversationGroups.forEach(group => group.style.display = 'none');
    
    // Track which date groups have visible cards
    const dateGroupsVisible = {};
    
    let visibleCount = 0;
    
    cards.forEach(card => {
        // Reset visibility
        card.style.display = 'flex';
        let shouldShowByStatus = true;
        let shouldShowByProject = true;
        
        // Apply status filter
        switch (filter) {
            case 'with-memories':
                shouldShowByStatus = card.getAttribute('data-has-memories') === 'true';
                break;
                
            case 'recent':
                // In an actual implementation, would check date against recent threshold
                // For now, check if the card has the recent badge or is not archived
                shouldShowByStatus = card.getAttribute('data-archived') !== 'true';
                break;
                
            case 'archived':
                shouldShowByStatus = card.getAttribute('data-archived') === 'true';
                break;
                
            case 'all':
            default:
                shouldShowByStatus = true;
                break;
        }
        
        // Apply project filter
        if (projectFilter !== 'all-projects') {
            if (projectFilter === 'unassigned') {
                // Show conversations not assigned to any project
                shouldShowByProject = !card.hasAttribute('data-project');
            } else {
                // Show conversations for specific project
                shouldShowByProject = card.getAttribute('data-project') === projectFilter;
            }
        }
        
        // Apply both filters
        const shouldShow = shouldShowByStatus && shouldShowByProject;
        
        // Find parent group to show date headers properly
        const group = card.closest('.conversation-group');
        if (group) {
            const index = Array.from(conversationGroups).indexOf(group);
            if (index >= 0 && shouldShow) {
                dateGroupsVisible[index] = true;
            }
        }
        
        if (shouldShow) {
            card.style.display = 'flex';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show date headers and groups for conversations that are visible
    Object.keys(dateGroupsVisible).forEach(index => {
        if (dateHeaders[index]) dateHeaders[index].style.display = 'block';
        if (conversationGroups[index]) conversationGroups[index].style.display = 'block';
    });
    
    // Get filter message components
    const projectFilterSelect = document.getElementById('project-filter');
    const projectName = projectFilterSelect && projectFilter !== 'all-projects' ? 
        projectFilterSelect.options[projectFilterSelect.selectedIndex].text : null;
    
    let filterMsg;
    
    // Create base message based on status filter
    switch (filter) {
        case 'with-memories':
            filterMsg = `Showing ${visibleCount} conversation${visibleCount !== 1 ? 's' : ''} with saved memories`;
            break;
        case 'recent':
            filterMsg = `Showing ${visibleCount} recent conversation${visibleCount !== 1 ? 's' : ''}`;
            break;
        case 'archived':
            filterMsg = `Showing ${visibleCount} archived conversation${visibleCount !== 1 ? 's' : ''}`;
            break;
        default:
            filterMsg = `Showing ${visibleCount} conversation${visibleCount !== 1 ? 's' : ''}`;
    }
    
    // Add project filter information if applicable
    if (projectName && projectFilter !== 'all-projects') {
        if (projectFilter === 'unassigned') {
            filterMsg += ` (unassigned to any project)`;
        } else {
            filterMsg += ` in project "${projectName}"`;
        }
    }
    
    showNotification(filterMsg, 'info', true);
}

/**
 * Apply sort to conversations
 * @param {string} sortType - Sort type to apply
 */
function applySort(sortType) {
    console.log(`Applying sort: ${sortType}`);
    
    const container = document.querySelector('.conversations-container');
    if (!container) return;
    
    const cards = Array.from(container.querySelectorAll('.conversation-card'));
    
    // Sort the cards
    cards.sort((a, b) => {
        const titleA = a.querySelector('h3').textContent;
        const titleB = b.querySelector('h3').textContent;
        const dateA = a.querySelector('.conversation-date').textContent;
        const dateB = b.querySelector('.conversation-date').textContent;
        
        switch (sortType) {
            case 'newest':
                // Simplistic date comparison - a more robust implementation would parse actual dates
                if (dateA.includes('Today') && !dateB.includes('Today')) return -1;
                if (!dateA.includes('Today') && dateB.includes('Today')) return 1;
                if (dateA.includes('Yesterday') && !dateB.includes('Yesterday') && !dateB.includes('Today')) return -1;
                if (!dateA.includes('Yesterday') && !dateA.includes('Today') && dateB.includes('Yesterday')) return 1;
                return titleA.localeCompare(titleB); // fallback to alphabetical
                
            case 'oldest':
                if (dateA.includes('Today') && !dateB.includes('Today')) return 1;
                if (!dateA.includes('Today') && dateB.includes('Today')) return -1;
                if (dateA.includes('Yesterday') && !dateB.includes('Yesterday') && !dateB.includes('Today')) return 1;
                if (!dateA.includes('Yesterday') && !dateA.includes('Today') && dateB.includes('Yesterday')) return -1;
                return titleB.localeCompare(titleA); // fallback to reverse alphabetical
                
            case 'a-z':
                return titleA.localeCompare(titleB);
                
            case 'z-a':
                return titleB.localeCompare(titleA);
                
            default:
                return 0;
        }
    });
    
    // Reorder the DOM elements
    cards.forEach(card => container.appendChild(card));
    
    showNotification(`Conversations sorted by: ${getSortLabel(sortType)}`, 'info', true);
}

/**
 * Get human-readable sort label
 * @param {string} sortType - Sort type
 * @returns {string} Human-readable label
 */
function getSortLabel(sortType) {
    switch (sortType) {
        case 'newest': return 'Newest first';
        case 'oldest': return 'Oldest first';
        case 'a-z': return 'Name (A to Z)';
        case 'z-a': return 'Name (Z to A)';
        default: return sortType;
    }
}

/**
 * Go to previous page of results
 */
function goToPreviousPage() {
    console.log('Going to previous page');
    // This would be implemented when pagination is fully functional
    showNotification('Previous page', 'info');
}

/**
 * Go to next page of results
 */
function goToNextPage() {
    console.log('Going to next page');
    // This would be implemented when pagination is fully functional
    showNotification('Next page', 'info');
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, error)
 * @param {boolean} isTemporary - Whether notification should auto-dismiss
 */
function showNotification(message, type = 'info', isTemporary = true) {
    // Check if notification container exists, if not create it
    let notificationContainer = document.querySelector('.minerva-notifications');
    
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'minerva-notifications';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.bottom = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.backgroundColor = 'rgba(30, 40, 80, 0.9)';
    notification.style.color = '#e0e0ff';
    notification.style.padding = '12px 20px';
    notification.style.borderRadius = '8px';
    notification.style.marginTop = '10px';
    notification.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
    notification.style.backdropFilter = 'blur(8px)';
    notification.style.borderLeft = '4px solid #4a6bdf';
    notification.style.fontSize = '0.9rem';
    notification.style.transition = 'all 0.3s ease';
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(20px)';
    
    // Adjust color based on type
    switch (type) {
        case 'success':
            notification.style.borderLeftColor = '#32c864';
            break;
        case 'warning':
            notification.style.borderLeftColor = '#ffb432';
            break;
        case 'error':
            notification.style.borderLeftColor = '#ff4260';
            break;
        default: // info
            notification.style.borderLeftColor = '#4a6bdf';
    }
    
    // Add to container
    notificationContainer.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);
    
    // Auto-dismiss if temporary
    if (isTemporary) {
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            
            // Remove from DOM after animation
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    } else {
        // Add close button for persistent notifications
        const closeBtn = document.createElement('span');
        closeBtn.textContent = '×';
        closeBtn.style.marginLeft = '10px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.fontWeight = 'bold';
        closeBtn.addEventListener('click', () => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
        
        notification.appendChild(closeBtn);
    }
    
    return notification;
}

// Add global styles for notification animations
function addGlobalStyles() {
    if (!document.getElementById('minerva-conversations-global-styles')) {
        const style = document.createElement('style');
        style.id = 'minerva-conversations-global-styles';
        style.textContent = `
            @keyframes flash-highlight {
                0% { background-color: rgba(74, 107, 223, 0.3); }
                100% { background-color: transparent; }
            }
        `;
        document.head.appendChild(style);
    }
}

// Call this on init
addGlobalStyles();

/**
 * Create and save a new conversation
 * @param {Object} conversation - Conversation data
 */
function createNewConversation(conversation) {
    console.log('Creating new conversation:', conversation);
    
    // Make sure we have the minimum required fields
    const newConversation = {
        id: conversation.id || 'conv_' + Date.now(),
        title: conversation.title || 'Conversation ' + new Date().toLocaleString(),
        messages: conversation.messages || [],
        created: conversation.created || new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        hasMemories: conversation.hasMemories || false,
        isArchived: false,
        project: conversation.project || null
    };
    
    // Get a preview from the first message if available
    if (newConversation.messages.length > 0) {
        newConversation.preview = newConversation.messages[0].content.substring(0, 100) + '...';
    } else {
        newConversation.preview = 'No messages yet';
    }
    
    // Save using the conversation manager if available
    if (window.conversationManager && typeof window.conversationManager.addConversation === 'function') {
        window.conversationManager.addConversation(newConversation);
        console.log('Saved conversation using conversationManager');
    } else {
        // Otherwise save directly to localStorage
        try {
            let savedConversations = JSON.parse(localStorage.getItem('minerva_conversations')) || {
                general: [],
                projects: {},
                agents: {}
            };
            
            // Add to general conversations
            savedConversations.general.push(newConversation);
            
            // Add to project-specific conversations if applicable
            if (newConversation.project) {
                if (!savedConversations.projects[newConversation.project]) {
                    savedConversations.projects[newConversation.project] = [];
                }
                savedConversations.projects[newConversation.project].push(newConversation.id);
            }
            
            // Save back to localStorage
            localStorage.setItem('minerva_conversations', JSON.stringify(savedConversations));
            console.log('Saved conversation directly to localStorage');
            
            // Show success notification
            showNotification('Conversation saved successfully', 'success');
            
            // Reload conversations list
            loadConversations();
        } catch (e) {
            console.error('Failed to save conversation:', e);
            showNotification('Failed to save conversation: ' + e.message, 'error');
        }
    }
    
    return newConversation;
}
