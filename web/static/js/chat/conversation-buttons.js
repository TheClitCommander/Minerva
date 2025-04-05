/**
 * Minerva Conversation Buttons Manager
 * Fixes the buttons on the conversations interface to properly handle
 * viewing, editing, creating projects, archiving, and deleting conversations.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Conversation Buttons Manager...');
    
    // Wait for the conversation manager to be initialized
    function initConversationButtons() {
        // Check if conversation buttons exist
        const viewButtons = document.querySelectorAll('.view-conversation-btn');
        const editButtons = document.querySelectorAll('.edit-conversation-btn');
        const projectButtons = document.querySelectorAll('.create-project-btn');
        const archiveButtons = document.querySelectorAll('.archive-conversation-btn');
        const deleteButtons = document.querySelectorAll('.delete-conversation-btn');
        
        if (viewButtons.length > 0) {
            console.log('Found conversation buttons, attaching event handlers...');
            
            // Attach event handlers to view buttons
            viewButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const conversationId = this.closest('.conversation-item').dataset.id;
                    if (conversationId && window.conversationManager) {
                        window.conversationManager.viewConversation(conversationId);
                    } else {
                        console.error('Cannot view conversation: missing ID or conversation manager');
                    }
                });
            });
            
            // Attach event handlers to edit buttons
            editButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const conversationId = this.closest('.conversation-item').dataset.id;
                    if (conversationId && window.conversationManager) {
                        window.conversationManager.editConversation(conversationId);
                    } else {
                        console.error('Cannot edit conversation: missing ID or conversation manager');
                    }
                });
            });
            
            // Attach event handlers to project buttons
            projectButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const conversationId = this.closest('.conversation-item').dataset.id;
                    if (conversationId && window.conversationManager) {
                        window.conversationManager.createProjectFromConversation(conversationId);
                    } else {
                        console.error('Cannot create project: missing ID or conversation manager');
                    }
                });
            });
            
            // Attach event handlers to archive buttons
            archiveButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const conversationId = this.closest('.conversation-item').dataset.id;
                    if (conversationId && window.conversationManager) {
                        window.conversationManager.archiveConversation(conversationId);
                    } else {
                        console.error('Cannot archive conversation: missing ID or conversation manager');
                    }
                });
            });
            
            // Attach event handlers to delete buttons
            deleteButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    const conversationId = this.closest('.conversation-item').dataset.id;
                    if (conversationId && window.conversationManager) {
                        window.conversationManager.deleteConversation(conversationId);
                    } else {
                        console.error('Cannot delete conversation: missing ID or conversation manager');
                    }
                });
            });
            
            console.log('Event handlers attached to conversation buttons');
        } else {
            console.log('No conversation buttons found yet, will retry...');
            // Try again after a delay
            setTimeout(initConversationButtons, 1000);
        }
    }
    
    // Add a global function to handle attaching event handlers
    window.refreshConversationButtonHandlers = function() {
        console.log('Refreshing conversation button handlers...');
        initConversationButtons();
    };
    
    // Initialize conversation buttons with a delay to ensure everything is loaded
    setTimeout(initConversationButtons, 1000);
    
    // Create MutationObserver to watch for dynamically added conversation items
    const conversationListObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if any of the added nodes are conversation items or contain them
                let hasConversationItems = false;
                
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList && node.classList.contains('conversation-item')) {
                            hasConversationItems = true;
                        } else if (node.querySelector && node.querySelector('.conversation-item')) {
                            hasConversationItems = true;
                        }
                    }
                });
                
                if (hasConversationItems) {
                    console.log('New conversation items added, refreshing button handlers...');
                    window.refreshConversationButtonHandlers();
                }
            }
        });
    });
    
    // Start observing the conversation list container
    setTimeout(() => {
        const conversationList = document.querySelector('.conversation-list');
        if (conversationList) {
            conversationListObserver.observe(conversationList, { childList: true, subtree: true });
            console.log('Observing conversation list for changes');
        } else {
            console.warn('Conversation list not found, cannot observe changes');
        }
    }, 2000); // Wait for the conversation list to be created
});
