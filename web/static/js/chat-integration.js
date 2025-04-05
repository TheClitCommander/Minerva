/**
 * Minerva Chat Integration
 * This script connects the Minerva Central UI chat interface to the Think Tank Bridge Server
 */

// Global chat instance for the entire application
let chatInstance = null;

// Initialize the chat system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Minerva Chat Integration...');
    
    // Initialize direct connector to the local Think Tank API endpoint
    const connector = new MinervaDirectConnector({
        debug: true,
        primaryEndpoint: '/api/think-tank',  // Use local endpoint instead of hardcoded URL
        retryAttempts: 2,
        storeConversations: true  // Ensure conversation memory is maintained
    });
    
    console.log('MinervaDirectConnector initialized with local endpoint: /api/think-tank');
    
    // Check if floating chat component exists
    if (typeof window.floatingChat !== 'undefined') {
        console.log('FloatingChat found, connecting it to Think Tank...');
        // Connect floating chat to direct connector
        window.floatingChat.chatInstance = {
            sendMessage: function(message) {
                console.log('Sending message via direct connector:', message);
                
                // Add user message to chat
                window.floatingChat.addUserMessage(message);
                
                // Show loading indicator
                const loadingId = window.floatingChat.showLoading();
                
                // Send to Think Tank bridge
                connector.sendMessage(
                    message,
                    // Success callback
                    function(response) {
                        console.log('Received response from bridge server:', response);
                        
                        // Remove loading indicator
                        window.floatingChat.hideLoading(loadingId);
                        
                        if (response && response.response) {
                            // Add response to chat
                            window.floatingChat.addAIMessage(response.response);
                            
                            // Store conversation ID if provided
                            if (response.conversation_id) {
                                localStorage.setItem('minerva_conversation_id', response.conversation_id);
                            }
                        } else {
                            window.floatingChat.addSystemMessage('Received empty response from server.');
                        }
                    },
                    // Error callback
                    function(error) {
                        console.error('Error sending message:', error);
                        
                        // Remove loading indicator
                        window.floatingChat.hideLoading(loadingId);
                        
                        // Show error message
                        window.floatingChat.addSystemMessage('Connection error: ' + (error.message || 'Unknown error'));
                    }
                );
            },
            
            switchProject: function(projectId) {
                console.log('Switching to project:', projectId);
                connector.setProject(projectId);
                window.floatingChat.addSystemMessage('Switched to project: ' + projectId);
            }
        };
        
        console.log('Chat instance connected to the Think Tank bridge server.');
    } else {
        console.warn('FloatingChat component not found. Chat will not work properly.');
    }
});
