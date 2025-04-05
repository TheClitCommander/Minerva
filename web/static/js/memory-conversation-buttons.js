/**
 * Minerva Memory and Conversation Buttons
 * Fixes the management buttons for the conversation interface
 * Handles viewing, editing, project creation, archiving, and deleting
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Memory and Conversation Button Handlers...');
    
    // Set up the button handlers once the page is fully loaded
    setTimeout(function() {
        setupConversationButtons();
    }, 1000);
    
    // Observer to detect when new conversation items are added
    const conversationObserver = new MutationObserver(function(mutations) {
        for(let mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check if any conversation items were added
                let foundConversationItem = false;
                mutation.addedNodes.forEach(node => {
                    if (node.classList && node.classList.contains('conversation-item')) {
                        foundConversationItem = true;
                    }
                });
                
                if (foundConversationItem) {
                    console.log('New conversation items detected, refreshing button handlers...');
                    setupConversationButtons();
                }
            }
        }
    });
    
    // Once DOM is loaded, start observing the conversation list
    setTimeout(function() {
        const conversationList = document.querySelector('.conversation-list');
        if (conversationList) {
            conversationObserver.observe(conversationList, { childList: true, subtree: true });
            console.log('Started observing conversation list for changes');
        }
    }, 2000);
    
    // Set up all button handlers for conversations
    function setupConversationButtons() {
        // View conversation buttons (eye icon)
        document.querySelectorAll('.view-conversation-btn, .conversation-item [data-action="view"]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.conversation-item');
                const conversationId = item ? item.dataset.id : null;
                
                if (conversationId && window.conversationManager) {
                    console.log('Viewing conversation:', conversationId);
                    window.conversationManager.viewConversation(conversationId);
                } else {
                    console.error('Failed to view conversation - missing ID or conversation manager');
                }
            });
        });
        
        // Edit conversation buttons (pencil icon)
        document.querySelectorAll('.edit-conversation-btn, .conversation-item [data-action="edit"]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.conversation-item');
                const conversationId = item ? item.dataset.id : null;
                
                if (conversationId && window.conversationManager) {
                    console.log('Editing conversation:', conversationId);
                    window.conversationManager.editConversation(conversationId);
                } else {
                    console.error('Failed to edit conversation - missing ID or conversation manager');
                }
            });
        });
        
        // Create project buttons (folder icon)
        document.querySelectorAll('.create-project-btn, .conversation-item [data-action="project"]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.conversation-item');
                const conversationId = item ? item.dataset.id : null;
                
                if (conversationId && window.conversationManager) {
                    console.log('Creating project from conversation:', conversationId);
                    window.conversationManager.createProjectFromConversation(conversationId);
                } else {
                    console.error('Failed to create project - missing ID or conversation manager');
                }
            });
        });
        
        // Archive conversation buttons (box icon)
        document.querySelectorAll('.archive-conversation-btn, .conversation-item [data-action="archive"]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.conversation-item');
                const conversationId = item ? item.dataset.id : null;
                
                if (conversationId && window.conversationManager) {
                    console.log('Archiving conversation:', conversationId);
                    window.conversationManager.archiveConversation(conversationId);
                } else {
                    console.error('Failed to archive conversation - missing ID or conversation manager');
                }
            });
        });
        
        // Delete conversation buttons (trash icon)
        document.querySelectorAll('.delete-conversation-btn, .conversation-item [data-action="delete"]').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const item = this.closest('.conversation-item');
                const conversationId = item ? item.dataset.id : null;
                
                if (conversationId && window.conversationManager) {
                    if (confirm('Are you sure you want to delete this conversation? This cannot be undone.')) {
                        console.log('Deleting conversation:', conversationId);
                        window.conversationManager.deleteConversation(conversationId);
                    }
                } else {
                    console.error('Failed to delete conversation - missing ID or conversation manager');
                }
            });
        });
        
        console.log('Conversation button handlers have been set up');
    }
    
    // Make this function available globally for other scripts to call
    window.refreshConversationButtons = setupConversationButtons;
});
