/**
 * Conversation History UI Integration for Minerva Dashboard
 * Handles the conversation history tab functionality and data fetching
 * Works with ThinkTankAPI to provide a unified conversation memory system
 */

// Global state for conversations UI
let currentConversations = [];
let activeProjectFilter = 'all';
let activeSearchTerm = '';

document.addEventListener("DOMContentLoaded", function() {
    // Initialize tab functionality for Think Tank section
    initializeThinkTankTabs();
    
    // Initialize conversation history functionality when the conversations tab is clicked
    document.querySelectorAll('.tab-button[data-tab="conversations"]').forEach(button => {
        button.addEventListener('click', function() {
            loadConversationHistoryList();
            loadProjectsList(); // Load projects for filtering
        });
    });
    
    // Listen for refresh button clicks
    const refreshButton = document.getElementById('refresh-conversations');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            loadConversationHistoryList();
            loadProjectsList();
        });
    }
    
    // Listen for project filter changes
    const projectFilter = document.getElementById('project-filter');
    if (projectFilter) {
        projectFilter.addEventListener('change', function() {
            activeProjectFilter = this.value;
            filterConversations();
        });
    }
    
    // Listen for search input
    const searchInput = document.getElementById('conversation-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            activeSearchTerm = this.value.toLowerCase();
            filterConversations();
        });
    }
    
    // Listen for organize projects button
    const organizeButton = document.getElementById('organize-projects');
    if (organizeButton) {
        organizeButton.addEventListener('click', function() {
            showProjectOrganizer();
        });
    }
});

/**
 * Show the project organizer modal
 */
function showProjectOrganizer() {
    // Check if the dialog exists, if not create it
    let dialog = document.getElementById('project-organizer-dialog');
    
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.id = 'project-organizer-dialog';
        dialog.className = 'modal-dialog';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Organize Projects</h3>
                    <button class="close-button" onclick="this.parentElement.parentElement.parentElement.style.display='none'">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="project-list" id="organizer-project-list">
                        <div class="loading">Loading projects...</div>
                    </div>
                    <div class="project-form">
                        <h4>Create New Project</h4>
                        <input type="text" id="new-project-name" placeholder="Project name">
                        <button id="create-project-btn" class="primary-btn">Create Project</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);
        
        // Add event listener for the create project button
        document.getElementById('create-project-btn').addEventListener('click', createNewProject);
    }
    
    // Show the dialog
    dialog.style.display = 'flex';
    
    // Load projects into the organizer
    loadProjectsForOrganizer();
}

/**
 * Initialize the tab functionality for the Think Tank section
 */
function initializeThinkTankTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Get the tab to show
            const tabToShow = this.getAttribute('data-tab');
            
            // Show the corresponding tab content
            document.getElementById(`${tabToShow}-tab`).classList.add('active');
        });
    });
}

/**
 * Load projects list for the conversation filter dropdown
 */
async function loadProjectsList() {
    const projectFilter = document.getElementById('project-filter');
    if (!projectFilter) return;
    
    try {
        // Clear existing options except for 'All Projects'
        while (projectFilter.options.length > 1) {
            projectFilter.remove(1);
        }
        
        let projects = [];
        
        // Try using ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.getAllProjects) {
            projects = await window.ThinkTankAPI.getAllProjects();
        } else {
            // Fallback to traditional fetch
            const response = await fetch('/api/projects');
            if (response.ok) {
                projects = await response.json();
            } else {
                throw new Error('Failed to load projects');
            }
        }
        
        // Add options for each project
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            projectFilter.appendChild(option);
        });
        
        // Restore active filter if it exists
        if (activeProjectFilter !== 'all') {
            // Check if the project still exists
            const projectExists = Array.from(projectFilter.options).some(option => option.value === activeProjectFilter);
            
            if (projectExists) {
                projectFilter.value = activeProjectFilter;
            } else {
                // Reset to 'all' if project no longer exists
                activeProjectFilter = 'all';
                projectFilter.value = 'all';
            }
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

/**
 * Load projects for the project organizer modal
 */
async function loadProjectsForOrganizer() {
    const projectList = document.getElementById('organizer-project-list');
    if (!projectList) return;
    
    // Show loading indicator
    projectList.innerHTML = '<div class="loading">Loading projects...</div>';
    
    try {
        let projects = [];
        
        // Try using ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.getAllProjects) {
            projects = await window.ThinkTankAPI.getAllProjects();
        } else {
            // Fallback to traditional fetch
            const response = await fetch('/api/projects');
            if (response.ok) {
                projects = await response.json();
            } else {
                throw new Error('Failed to load projects');
            }
        }
        
        // Create project list HTML
        if (projects.length === 0) {
            projectList.innerHTML = '<div class="empty-state">No projects yet. Create your first project.</div>';
            return;
        }
        
        let html = '<ul class="project-items">';
        
        projects.forEach(project => {
            html += `
                <li class="project-item" data-project-id="${project.id}">
                    <span class="project-name">${escapeHtml(project.name)}</span>
                    <div class="project-actions">
                        <button onclick="renameProject('${project.id}')" title="Rename Project"><i class="fas fa-edit"></i></button>
                        <button onclick="deleteProject('${project.id}')" title="Delete Project"><i class="fas fa-trash"></i></button>
                    </div>
                </li>
            `;
        });
        
        html += '</ul>';
        projectList.innerHTML = html;
    } catch (error) {
        console.error('Error loading projects for organizer:', error);
        projectList.innerHTML = `
            <div class="error-state">
                Failed to load projects. 
                <button onclick="loadProjectsForOrganizer()">Try Again</button>
            </div>
        `;
    }
}

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} unsafe - Unsafe string that might contain HTML
 * @returns {string} - Escaped safe string
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Load conversation history list from the API
 */
async function loadConversationHistoryList() {
    const tbody = document.getElementById('conversation-history-tbody');
    
    if (!tbody) return;
    
    // Show loading state
    tbody.innerHTML = '<tr class="conversation-loading"><td colspan="5">Loading conversation history...</td></tr>';
    
    try {
        let conversations = [];
        
        // First try using ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.getAllConversations) {
            conversations = await window.ThinkTankAPI.getAllConversations();
        } else {
            // Fallback to traditional fetch
            const response = await fetch('/api/conversations');
            
            if (!response.ok) {
                throw new Error('Failed to load conversations');
            }
            
            conversations = await response.json();
        }
        
        // Store conversations in global state
        currentConversations = conversations;
        
        // Render the conversation list
        renderConversationList(conversations);
    } catch (error) {
        console.error('Error loading conversation history:', error);
        tbody.innerHTML = `
            <tr class="conversation-error">
                <td colspan="5">
                    Failed to load conversation history. 
                    <button class="retry-btn" onclick="loadConversationHistoryList()">Retry</button>
                </td>
            </tr>
        `;
    }
}

/**
 * Render the conversation list in the UI
 * @param {Array} conversations - List of conversation objects
 */
function renderConversationList(conversations) {
    const tbody = document.getElementById('conversation-history-tbody');
    if (!tbody) return;
    
    // If no conversations
    if (!conversations || conversations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No conversations found. Start a new conversation to see it here.</td></tr>';
        return;
    }
    
    // Sort conversations by date (newest first)
    conversations.sort((a, b) => {
        const dateA = a.timestamp || a.created_at || 0;
        const dateB = b.timestamp || b.created_at || 0;
        return new Date(dateB) - new Date(dateA);
    });
    
    // Build table
    let html = '';
    
    // Keep track of conversations needing title generation
    const untitledConversations = [];
    
    conversations.forEach(conversation => {
        // Check if conversation has a title
        const hasTitle = conversation.title && conversation.title !== 'Untitled Conversation';
        const title = escapeHtml(conversation.title || 'Untitled Conversation');
        const date = formatTimestamp(conversation.timestamp || conversation.created_at);
        const projectId = conversation.project_id || 'general';
        const projectName = escapeHtml(conversation.project_name || 'General');
        const models = conversation.models || [];
        
        // Add to list of conversations needing titles
        if (!hasTitle && window.ThinkTankAPI && window.ThinkTankAPI.generateConversationTitle) {
            untitledConversations.push(conversation.id);
        }
        
        html += `
            <tr data-conversation-id="${conversation.id}" data-project="${projectId}">
                <td>
                    <div class="title-container">
                        <span class="conversation-title" title="${title}">${title}</span>
                        <button class="edit-title-btn" onclick="editConversationTitle('${conversation.id}')" title="Edit Title">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </td>
                <td><span class="project-tag">${projectName}</span></td>
                <td>${date}</td>
                <td class="models-used">
                    ${models.map(model => `<span class="model-tag">${escapeHtml(model)}</span>`).join('')}
                </td>
                <td>
                    <button class="view-btn" onclick="viewConversation('${conversation.id}')">View</button>
                    <button class="continue-btn" onclick="continueConversation('${conversation.id}')">Continue</button>
                    <button class="delete-btn" onclick="deleteConversation('${conversation.id}')">Delete</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
    
    // Apply active filters
    filterConversations();
    
    // Initialize conversation action buttons
    addConversationButtonListeners();
    
    // Generate titles for untitled conversations (in background)
    generateMissingTitles(untitledConversations);
}



/**
 * Load projects for the project organizer modal
 */
async function loadProjectsForOrganizer() {
    const projectList = document.getElementById('organizer-project-list');
    
    if (!projectList) return;
    
    // Show loading state
    projectList.innerHTML = '<div class="loading">Loading projects...</div>';
    
    try {
        let projects = [];
        
        // Try to get projects from ThinkTankAPI
        if (window.ThinkTankAPI && window.ThinkTankAPI.getAllProjects) {
            projects = await window.ThinkTankAPI.getAllProjects();
        } else {
            // Extract unique projects from conversations as fallback
            const projectSet = new Set();
            
            for (const conversation of currentConversations) {
                if (conversation.project && conversation.project.trim()) {
                    projectSet.add(conversation.project.trim());
                }
            }
            
            // Add "General" if there are any unassigned conversations
            if (currentConversations.some(conv => !conv.project || !conv.project.trim())) {
                projectSet.add('General');
            }
            
            projects = Array.from(projectSet).map(name => ({ id: name, name }));
        }
        
        if (projects.length === 0) {
            projectList.innerHTML = '<div class="empty-state">No projects found. Create your first project below!</div>';
            return;
        }
        
        // Generate project items HTML
        let projectsHTML = '<ul class="project-items" id="project-organizer-list">';
        
        projects.forEach(project => {
            projectsHTML += `
                <li class="project-item" data-project-id="${project.id}">
                    <div class="project-name">${escapeHtml(project.name)}</div>
                    <div class="project-actions">
                        <button class="rename-btn" onclick="renameProject('${project.id}')"><i class="fas fa-edit"></i></button>
                        <button class="delete-btn" onclick="deleteProject('${project.id}')"><i class="fas fa-trash"></i></button>
                    </div>
                </li>
            `;
        });
        
        projectsHTML += '</ul>';
        projectList.innerHTML = projectsHTML;
    } catch (error) {
        console.error('Error loading projects for organizer:', error);
        projectList.innerHTML = `
            <div class="error-state">
                Failed to load projects. 
                <button onclick="loadProjectsForOrganizer()">Retry</button>
            </div>
        `;
    }
}

/**
 * Render the conversation list in the table
 * @param {Array} conversations - List of conversation objects
 */
function renderConversationList(conversations) {
    const tbody = document.getElementById('conversation-history-tbody');
    
    if (!tbody) return;
    
    if (!conversations || conversations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No conversations found. Start a new conversation to see it here.</td></tr>';
        return;
    }
    
    // Sort conversations by date, newest first
    conversations.sort((a, b) => {
        const dateA = new Date(a.timestamp || a.date || a.created_at || 0);
        const dateB = new Date(b.timestamp || b.date || b.created_at || 0);
        return dateB - dateA;
    });
    
    // Generate HTML for the conversation rows
    tbody.innerHTML = conversations.map(conversation => {
        // Get the conversation title from the first message or use a default
        const title = getConversationTitle(conversation);
        
        // Format the date
        const date = formatTimestamp(conversation.timestamp || conversation.date || conversation.created_at);
        
        // Get the project name or use "General" as default
        const project = conversation.project || 'General';
        
        // Extract models used in this conversation
        const models = getConversationModels(conversation);
        
        return `
            <tr data-conversation-id="${conversation.id}" data-project="${project}">
                <td>
                    <div class="conversation-title">${escapeHtml(title)}</div>
                </td>
                <td>
                    <span class="project-tag">${escapeHtml(project)}</span>
                </td>
                <td>${date}</td>
                <td>
                    <div class="models-used">
                        ${models.map(model => `<span class="model-tag">${escapeHtml(model)}</span>`).join('')}
                    </div>
                </td>
                <td>
                    <button class="view-btn" onclick="viewConversation('${conversation.id}')">View</button>
                    <button class="continue-btn" onclick="continueConversation('${conversation.id}')">Continue</button>
                    <button class="delete-btn" onclick="deleteConversation('${conversation.id}')">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
    
    // Add event listeners for the buttons
    addConversationButtonListeners();
}

/**
 * Get a readable title for the conversation
 * @param {Object} conversation - Conversation object
 * @returns {string} - Conversation title
 */
function getConversationTitle(conversation) {
    // Try to get the first user message
    if (conversation.messages && conversation.messages.length > 0) {
        for (const message of conversation.messages) {
            if (message.role === 'user') {
                // Truncate long messages for display
                return message.content.length > 60 ? 
                    message.content.substring(0, 60) + '...' : 
                    message.content;
            }
        }
    }
    
    // If no messages found or no user messages, use the timestamp or ID
    return conversation.title || 
           `Conversation ${formatTimestamp(conversation.timestamp || conversation.date || conversation.created_at)}`;
}

/**
 * Get a list of models used in the conversation
 * @param {Object} conversation - Conversation object
 * @returns {Array} - List of model names
 */
function getConversationModels(conversation) {
    const modelSet = new Set();
    
    // Extract models from messages
    if (conversation.messages) {
        conversation.messages.forEach(message => {
            if (message.model) {
                modelSet.add(message.model);
            }
        });
    }
    
    // If we have metadata with models, use that too
    if (conversation.metadata && conversation.metadata.models) {
        if (Array.isArray(conversation.metadata.models)) {
            conversation.metadata.models.forEach(model => modelSet.add(model));
        } else if (typeof conversation.metadata.models === 'string') {
            modelSet.add(conversation.metadata.models);
        }
    }
    
    // If still no models, add a default
    if (modelSet.size === 0) {
        modelSet.add('Think Tank');
    }
    
    return Array.from(modelSet);
}

/**
 * Add event listeners for the conversation table buttons
 */
function addConversationButtonListeners() {
    // Add event listeners for row selection
    const rows = document.querySelectorAll('#conversation-history-tbody tr');
    
    rows.forEach(row => {
        row.addEventListener('click', function(event) {
            // Only handle clicks on the row itself, not on buttons
            if (!event.target.closest('button')) {
                // Toggle selected class
                this.classList.toggle('selected');
            }
        });
    });
}

/**
 * Generate titles for conversations that don't have meaningful titles
 * @param {Array} conversationIds - Array of conversation IDs that need titles
 */
async function generateMissingTitles(conversationIds) {
    if (!conversationIds || !conversationIds.length || !window.ThinkTankAPI || !window.ThinkTankAPI.generateConversationTitle) {
        return;
    }
    
    // Process a few at a time to avoid overwhelming the API
    const batchSize = 3;
    
    for (let i = 0; i < conversationIds.length; i += batchSize) {
        const batch = conversationIds.slice(i, i + batchSize);
        
        // Generate titles in parallel for this batch
        await Promise.all(batch.map(async (conversationId) => {
            try {
                // Generate a title
                const title = await window.ThinkTankAPI.generateConversationTitle(conversationId);
                
                // Update the title in the UI
                const titleElement = document.querySelector(`tr[data-conversation-id="${conversationId}"] .conversation-title`);
                if (titleElement) {
                    titleElement.textContent = title;
                    titleElement.setAttribute('title', title);
                }
                
                // Update the title in our local data
                if (currentConversations) {
                    const conversation = currentConversations.find(c => c.id === conversationId);
                    if (conversation) {
                        conversation.title = title;
                    }
                }
            } catch (error) {
                console.error(`Error generating title for conversation ${conversationId}:`, error);
            }
        }));
        
        // Small delay between batches to avoid overloading
        if (i + batchSize < conversationIds.length) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }
}

/**
 * Edit the title of a conversation
 * @param {string} conversationId - ID of the conversation to edit title for
 */
function editConversationTitle(conversationId) {
    if (!conversationId) return;
    
    // Find the conversation in our data
    const conversation = currentConversations.find(c => c.id === conversationId);
    if (!conversation) return;
    
    // Get current title
    const currentTitle = conversation.title || 'Untitled Conversation';
    
    // Prompt for new title
    const newTitle = prompt('Enter a new title for this conversation:', currentTitle);
    
    if (newTitle !== null && newTitle.trim() !== '' && newTitle !== currentTitle) {
        // Update title via API
        if (window.ThinkTankAPI && window.ThinkTankAPI.updateConversation) {
            window.ThinkTankAPI.updateConversation(conversationId, { title: newTitle })
                .then(() => {
                    // Update the title in the UI
                    const titleElement = document.querySelector(`tr[data-conversation-id="${conversationId}"] .conversation-title`);
                    if (titleElement) {
                        titleElement.textContent = newTitle;
                        titleElement.setAttribute('title', newTitle);
                    }
                    
                    // Update the title in our local data
                    conversation.title = newTitle;
                    
                    showNotification('Conversation title updated successfully', 'success');
                })
                .catch(error => {
                    console.error('Error updating conversation title:', error);
                    showNotification('Failed to update conversation title', 'error');
                });
        }
    }
}

/**
 * Filter conversations based on project and search term
 */
function filterConversations() {
    const rows = document.querySelectorAll('#conversation-history-tbody tr[data-conversation-id]');
    
    if (rows.length === 0) return;
    
    // Show/hide rows based on filter criteria
    rows.forEach(row => {
        const projectMatch = activeProjectFilter === 'all' || row.getAttribute('data-project') === activeProjectFilter;
        
        // Check title match
        const title = row.querySelector('.conversation-title')?.textContent?.toLowerCase() || '';
        const searchMatch = !activeSearchTerm || title.includes(activeSearchTerm);
        
        // Show/hide based on combined criteria
        if (projectMatch && searchMatch) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Check if any rows are visible
    const hasVisibleRows = Array.from(rows).some(row => row.style.display !== 'none');
    
    // Show a message if no rows are visible
    const tbody = document.getElementById('conversation-history-tbody');
    
    // Remove existing no-results row if it exists
    const existingNoResults = tbody.querySelector('.no-results');
    if (existingNoResults) {
        existingNoResults.remove();
    }
    
    if (!hasVisibleRows && tbody) {
        const noResultsRow = document.createElement('tr');
        noResultsRow.className = 'no-results';
        noResultsRow.innerHTML = `<td colspan="5">No conversations match your search criteria.</td>`;
        tbody.appendChild(noResultsRow);
    }
}

/**
 * View a conversation in detail
 * @param {string} conversationId - ID of the conversation to view
 */
function viewConversation(conversationId) {
    // If we have a chat interface on this page, load the conversation
    if (typeof loadConversationHistory === 'function') {
        loadConversationHistory(conversationId);
        return;
    }
    
    // If we're on dashboard and not chat page, redirect to chat with conversation ID
    window.location.href = `index.html?conversation=${conversationId}`;
}

/**
 * Continue a conversation in the chat interface
 * @param {string} conversationId - ID of the conversation to continue
 */
function continueConversation(conversationId) {
    // Set the active conversation ID in the ThinkTankAPI
    if (window.ThinkTankAPI) {
        window.ThinkTankAPI.setActiveConversation(conversationId);
    } else {
        // Fallback to local storage if API not available
        localStorage.setItem('minerva_conversation_id', conversationId);
    }
    
    // Redirect to the chat interface
    window.location.href = `index.html?conversation=${conversationId}&mode=continue`;
}

/**
 * Delete a conversation from history
 * @param {string} conversationId - ID of the conversation to delete
 */
function deleteConversation(conversationId) {
    if (!confirm('Are you sure you want to delete this conversation? This action cannot be undone.')) {
        return;
    }
    
    // Try using ThinkTankAPI if available
    if (window.ThinkTankAPI && window.ThinkTankAPI.deleteConversation) {
        window.ThinkTankAPI.deleteConversation(conversationId)
            .then(() => {
                // Remove the row from the table
                const row = document.querySelector(`tr[data-conversation-id="${conversationId}"]`);
                if (row) row.remove();
                
                // If no conversations left, show empty message
                const tbody = document.getElementById('conversation-history-tbody');
                if (tbody && tbody.children.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5">No conversations found. Start a new conversation to see it here.</td></tr>';
                }
            })
            .catch(error => {
                console.error('Error deleting conversation:', error);
                alert('Failed to delete conversation. Please try again later.');
            });
    } else {
        // Fallback to traditional fetch
        fetch(`/api/conversations/${conversationId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete conversation');
            }
            
            // Remove the row from the table
            const row = document.querySelector(`tr[data-conversation-id="${conversationId}"]`);
            if (row) row.remove();
            
            // If no conversations left, show empty message
            const tbody = document.getElementById('conversation-history-tbody');
            if (tbody && tbody.children.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5">No conversations found. Start a new conversation to see it here.</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error deleting conversation:', error);
            alert('Failed to delete conversation. Please try again later.');
        });
    }
}

/**
 * Format a timestamp in a human-readable way
 * @param {string|number|Date} timestamp - The timestamp to format
 * @returns {string} - Formatted date string
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    let date;
    try {
        if (timestamp instanceof Date) {
            date = timestamp;
        } else if (typeof timestamp === 'number') {
            date = new Date(timestamp);
        } else {
            date = new Date(timestamp);
        }
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return 'Invalid date';
        }
        
        const now = new Date();
        const diff = now - date;
        
        // Less than a minute
        if (diff < 60 * 1000) {
            return 'Just now';
        }
        
        // Less than an hour
        if (diff < 60 * 60 * 1000) {
            const minutes = Math.floor(diff / (60 * 1000));
            return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
        }
        
        // Less than a day
        if (diff < 24 * 60 * 60 * 1000) {
            const hours = Math.floor(diff / (60 * 60 * 1000));
            return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
        }
        
        // Less than a week
        if (diff < 7 * 24 * 60 * 60 * 1000) {
            const days = Math.floor(diff / (24 * 60 * 60 * 1000));
            return `${days} day${days !== 1 ? 's' : ''} ago`;
        }
        
        // Format date as MM/DD/YYYY
        return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
    } catch (error) {
        console.error('Error formatting timestamp:', error);
        return 'Date error';
    }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} unsafe - Unsafe string
 * @returns {string} - Escaped string
 */
function escapeHtml(unsafe) {
    if (typeof unsafe !== 'string') return '';
    
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Create a new project from the organizer modal
 */
async function createNewProject() {
    const nameInput = document.getElementById('new-project-name');
    const name = nameInput.value.trim();
    
    if (!name) {
        alert('Please enter a project name');
        nameInput.focus();
        return;
    }
    
    try {
        if (window.ThinkTankAPI && window.ThinkTankAPI.createProject) {
            // Create the project using the API
            const project = await window.ThinkTankAPI.createProject({
                name: name,
                description: ''
            });
            
            // Clear the input field
            nameInput.value = '';
            
            // Reload the projects list
            loadProjectsForOrganizer();
            loadProjectsList();
        } else {
            throw new Error('Project creation API not available');
        }
    } catch (error) {
        console.error('Error creating project:', error);
        alert('Failed to create project. Please try again.');
    }
}

/**
 * Rename an existing project
 * @param {string} projectId - ID of the project to rename
 */
async function renameProject(projectId) {
    // Get the current project name
    const projectElement = document.querySelector(`#project-organizer-list li[data-project-id="${projectId}"] .project-name`);
    const currentName = projectElement ? projectElement.textContent : '';
    
    // Prompt for the new name
    const newName = prompt('Enter new project name:', currentName);
    
    if (!newName || newName === currentName) {
        return; // No change
    }
    
    try {
        if (window.ThinkTankAPI && window.ThinkTankAPI.updateProject) {
            // Update the project using the API
            await window.ThinkTankAPI.updateProject(projectId, {
                name: newName
            });
            
            // Reload the projects lists
            loadProjectsForOrganizer();
            loadProjectsList();
            
            // Reload conversation list to update project names
            loadConversationHistoryList();
        } else {
            throw new Error('Project update API not available');
        }
    } catch (error) {
        console.error('Error renaming project:', error);
        alert('Failed to rename project. Please try again.');
    }
}

/**
 * Delete an existing project
 * @param {string} projectId - ID of the project to delete
 */
async function deleteProject(projectId) {
    // Ask for confirmation
    if (!confirm('Are you sure you want to delete this project? Conversations in this project will be moved to General.')) {
        return;
    }
    
    try {
        if (window.ThinkTankAPI && window.ThinkTankAPI.deleteProject) {
            // Delete the project using the API
            await window.ThinkTankAPI.deleteProject(projectId);
            
            // Reload the projects lists
            loadProjectsForOrganizer();
            loadProjectsList();
            
            // Reload conversation list
            loadConversationHistoryList();
        } else {
            throw new Error('Project deletion API not available');
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        alert('Failed to delete project. Please try again.');
    }
}

/**
 * Assign a conversation to a project
 * @param {string} conversationId - ID of the conversation to assign
 */
async function assignToProject(conversationId) {
    // Create a modal to select a project
    let modal = document.getElementById('assign-project-modal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'assign-project-modal';
        modal.className = 'modal-dialog';
        document.body.appendChild(modal);
    }
    
    try {
        // Get all projects
        let projects = [];
        
        if (window.ThinkTankAPI && window.ThinkTankAPI.getAllProjects) {
            projects = await window.ThinkTankAPI.getAllProjects();
        } else {
            throw new Error('Project API not available');
        }
        
        // Build the project selection options
        let projectOptions = '<option value="general">General</option>';
        
        projects.forEach(project => {
            projectOptions += `<option value="${project.id}">${escapeHtml(project.name)}</option>`;
        });
        
        // Build the modal content
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Assign to Project</h3>
                    <button class="close-button" onclick="this.parentElement.parentElement.parentElement.style.display='none'">&times;</button>
                </div>
                <div class="modal-body">
                    <p>Choose a project to assign this conversation to:</p>
                    <select id="project-assign-select" class="form-select">
                        ${projectOptions}
                    </select>
                    <div class="modal-actions">
                        <button id="confirm-assign-project" class="primary-btn">Assign</button>
                        <button onclick="document.getElementById('assign-project-modal').style.display='none'" class="secondary-btn">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        
        // Show the modal
        modal.style.display = 'flex';
        
        // Add event listener for the confirm button
        document.getElementById('confirm-assign-project').addEventListener('click', async function() {
            const projectSelect = document.getElementById('project-assign-select');
            const projectId = projectSelect.value;
            
            try {
                if (window.ThinkTankAPI && window.ThinkTankAPI.assignConversationToProject) {
                    await window.ThinkTankAPI.assignConversationToProject(conversationId, projectId);
                    
                    // Hide the modal
                    modal.style.display = 'none';
                    
                    // Reload conversation list
                    loadConversationHistoryList();
                    
                    // Update the conversation view if it's open
                    const viewModal = document.getElementById('conversation-view-modal');
                    if (viewModal && viewModal.style.display === 'flex') {
                        viewConversation(conversationId);
                    }
                } else {
                    throw new Error('Project assignment API not available');
                }
            } catch (error) {
                console.error('Error assigning conversation to project:', error);
                alert('Failed to assign conversation to project. Please try again.');
            }
        });
        
    } catch (error) {
        console.error('Error showing project assignment modal:', error);
        alert('Failed to load projects. Please try again.');
    }
}
