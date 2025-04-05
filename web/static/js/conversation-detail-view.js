/**
 * Conversation Detail View
 * 
 * Handles the display of a selected conversation in detail,
 * ensuring only one conversation is prominently displayed
 */

/**
 * Create or show the conversation detail view
 * @param {Object} conversation - Conversation object to display
 */
function createConversationDetailView(conversation) {
    // Check if detail view already exists
    let detailView = document.getElementById('conversation-detail-view');
    
    if (!detailView) {
        // Create detail view container
        detailView = document.createElement('div');
        detailView.id = 'conversation-detail-view';
        
        // Add to the page - try to find the best location
        const conversationsView = document.getElementById('conversations-view');
        if (conversationsView) {
            conversationsView.appendChild(detailView);
        } else {
            const mainContent = document.getElementById('content-display') || document.body;
            mainContent.appendChild(detailView);
        }
    }
    
    // Add the HTML content for this conversation
    detailView.innerHTML = generateConversationDetailHTML(conversation);
    detailView.classList.remove('hidden');
    
    // Scroll to show the detail view
    detailView.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Add event listeners for detail view actions
    setupDetailViewListeners(conversation);
}

/**
 * Generate HTML for the conversation detail view
 * @param {Object} conversation - Conversation to display
 * @returns {string} - HTML content
 */
function generateConversationDetailHTML(conversation) {
    const formattedDate = new Date(conversation.lastUpdated || conversation.created).toLocaleString();
    
    // Generate messages HTML
    let messagesHTML = '';
    if (conversation.messages && conversation.messages.length > 0) {
        messagesHTML = conversation.messages.map(msg => {
            const messageClass = msg.role === 'user' ? 'user-message' : 'assistant-message';
            return `<div class="message ${messageClass}">
                <div class="message-content">${formatMessageContent(msg.content)}</div>
                <div class="message-meta">${msg.role} • ${new Date(msg.timestamp || Date.now()).toLocaleTimeString()}</div>
            </div>`;
        }).join('');
    } else {
        messagesHTML = '<div class="empty-messages">No messages in this conversation</div>';
    }
    
    // Generate tags HTML
    const tagsHTML = conversation.tags && conversation.tags.length > 0 
        ? conversation.tags.map(tag => `<span class="tag">${tag}</span>`).join('')
        : '<span class="no-tags">No tags</span>';
    
    // Generate HTML
    return `
        <div class="detail-header">
            <h2>${conversation.title}</h2>
            <div class="detail-meta">
                <span class="detail-date">${formattedDate}</span>
                <span class="detail-messages-count">${conversation.messages ? conversation.messages.length : 0} messages</span>
            </div>
            <div class="detail-tags">${tagsHTML}</div>
        </div>
        
        <div class="conversation-messages">
            ${messagesHTML}
        </div>
        
        <div class="detail-actions">
            <button class="action-button continue-conversation">Continue Conversation</button>
            <button class="action-button convert-to-project">Convert to Project</button>
            <button class="action-button close-detail-view">Close</button>
        </div>
    `;
}

/**
 * Format message content for display
 * @param {string} content - Message content
 * @returns {string} - Formatted HTML
 */
function formatMessageContent(content) {
    if (!content) return '';
    
    // Basic formatting - convert URLs to links, etc.
    let formatted = content
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
        .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    
    return formatted;
}

/**
 * Setup event listeners for the detail view
 * @param {Object} conversation - Conversation object
 */
function setupDetailViewListeners(conversation) {
    // Continue conversation
    const continueBtn = document.querySelector('#conversation-detail-view .continue-conversation');
    if (continueBtn) {
        continueBtn.addEventListener('click', () => {
            // Open in chat interface if available
            if (window.openChatWithConversation) {
                window.openChatWithConversation(conversation.id);
            } else {
                // Fallback - navigate to chat page with conversation ID
                window.location.href = `minerva_central.html?conversation=${conversation.id}`;
            }
        });
    }
    
    // Convert to project
    const convertBtn = document.querySelector('#conversation-detail-view .convert-to-project');
    if (convertBtn) {
        convertBtn.addEventListener('click', () => {
            // Use the conversation manager if available
            if (window.conversationManager && typeof window.conversationManager.convertToProject === 'function') {
                const projectId = window.conversationManager.convertToProject(conversation.id);
                if (projectId) {
                    showNotification(`Conversation "${conversation.title}" converted to project`, 'success');
                    
                    // Navigate to the project if we have a projects view
                    if (window.showProjectsView && typeof window.openProject === 'function') {
                        setTimeout(() => {
                            window.showProjectsView();
                            window.openProject(projectId);
                        }, 1000);
                    }
                } else {
                    showNotification('Failed to convert conversation to project', 'error');
                }
            }
        });
    }
    
    // Close detail view
    const closeBtn = document.querySelector('#conversation-detail-view .close-detail-view');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('conversation-detail-view').classList.add('hidden');
            
            // Reset all conversation cards to normal state
            const allCards = document.querySelectorAll('.conversation-card');
            allCards.forEach(card => {
                card.classList.remove('active-conversation');
                card.classList.remove('inactive-conversation');
            });
        });
    }
}

/**
 * Show notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type (info, success, error, warning)
 */
function showNotification(message, type = 'info') {
    // Check if notification function exists
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }
    
    // Create our own notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
