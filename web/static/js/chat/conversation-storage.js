/**
 * Conversation Storage System
 * Manages saving and retrieving conversation history
 */

// Initialize enhanced conversation storage system
const enhancedConversationStorage = (function() {
    // Constants
    const STORAGE_KEY_PREFIX = 'minerva_conversation_';
    const CONVERSATIONS_INDEX_KEY = 'minerva_conversations_index';
    
    // State
    let currentConversationId = null;
    let currentConversation = {
        id: null,
        title: '',
        messages: [],
        timestamp: null,
        projectId: null,
        summary: '',
        tags: []
    };
    
    // Initialize
    function initialize() {
        console.log('Initializing enhanced conversation storage system');
        
        // Load the conversation index
        loadConversationsIndex();
        
        // Set up auto-save interval
        setInterval(autoSaveCurrentConversation, 30000); // Save every 30 seconds
        
        return true;
    }
    
    // Get a list of all saved conversations
    function getConversationsList() {
        try {
            const indexJson = localStorage.getItem(CONVERSATIONS_INDEX_KEY);
            if (!indexJson) return [];
            
            return JSON.parse(indexJson) || [];
        } catch (e) {
            console.error('Error loading conversations index:', e);
            return [];
        }
    }
    
    // Add or update a conversation in the index
    function updateConversationsIndex(conversation) {
        const existingList = getConversationsList();
        
        // Find if this conversation already exists
        const existingIndex = existingList.findIndex(c => c.id === conversation.id);
        
        if (existingIndex >= 0) {
            // Update existing entry
            existingList[existingIndex] = {
                id: conversation.id,
                title: conversation.title || 'Untitled Conversation',
                preview: getConversationPreview(conversation),
                timestamp: conversation.timestamp || new Date().toISOString(),
                messageCount: conversation.messages.length,
                projectId: conversation.projectId || null
            };
        } else {
            // Add new entry
            existingList.push({
                id: conversation.id,
                title: conversation.title || 'Untitled Conversation',
                preview: getConversationPreview(conversation),
                timestamp: conversation.timestamp || new Date().toISOString(), 
                messageCount: conversation.messages.length,
                projectId: conversation.projectId || null
            });
        }
        
        // Sort by timestamp, newest first
        existingList.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Save the updated index
        try {
            localStorage.setItem(CONVERSATIONS_INDEX_KEY, JSON.stringify(existingList));
            console.log('Conversation index updated:', existingList.length, 'conversations');
            return true;
        } catch (e) {
            console.error('Error saving conversations index:', e);
            return false;
        }
    }
    
    // Get a preview of the conversation for listings
    function getConversationPreview(conversation) {
        if (!conversation || !conversation.messages || conversation.messages.length === 0) {
            return '';
        }
        
        // Get the first user message
        const firstUserMessage = conversation.messages.find(msg => msg.role === 'user');
        if (firstUserMessage) {
            return truncateText(firstUserMessage.content, 100);
        }
        
        return '';
    }
    
    // Create a new conversation
    function createNewConversation(title = 'New Conversation', projectId = null) {
        const conversationId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substring(2, 10);
        
        currentConversation = {
            id: conversationId,
            title: title,
            messages: [],
            timestamp: new Date().toISOString(),
            projectId: projectId,
            summary: '',
            tags: []
        };
        
        currentConversationId = conversationId;
        
        // Add system welcome message
        addMessageToConversation({
            role: 'system',
            content: 'Welcome to Minerva Assistant. I\'m connected to the Think Tank API and ready to help.'
        });
        
        // Save immediately
        saveCurrentConversation();
        
        return conversationId;
    }
    
    // Load a specific conversation by ID
    function loadConversation(conversationId) {
        if (!conversationId) {
            console.error('No conversation ID provided to load');
            return null;
        }
        
        try {
            const conversationJson = localStorage.getItem(STORAGE_KEY_PREFIX + conversationId);
            
            if (!conversationJson) {
                console.error('Conversation not found:', conversationId);
                return null;
            }
            
            const loadedConversation = JSON.parse(conversationJson);
            
            // Update current conversation
            currentConversation = loadedConversation;
            currentConversationId = conversationId;
            
            console.log('Loaded conversation:', conversationId, 'with', loadedConversation.messages.length, 'messages');
            
            return loadedConversation;
        } catch (e) {
            console.error('Error loading conversation:', e);
            return null;
        }
    }
    
    // Save the current conversation
    function saveCurrentConversation() {
        if (!currentConversationId || !currentConversation) {
            console.warn('No active conversation to save');
            return false;
        }
        
        // Make sure timestamp is updated
        currentConversation.timestamp = new Date().toISOString();
        
        try {
            // Save the conversation data
            localStorage.setItem(
                STORAGE_KEY_PREFIX + currentConversationId, 
                JSON.stringify(currentConversation)
            );
            
            // Update the index
            updateConversationsIndex(currentConversation);
            
            console.log('Conversation saved:', currentConversationId);
            
            // Send save event
            const saveEvent = new CustomEvent('conversation-saved', {
                detail: { 
                    conversationId: currentConversationId,
                    messageCount: currentConversation.messages.length
                }
            });
            document.dispatchEvent(saveEvent);
            
            return true;
        } catch (e) {
            console.error('Error saving conversation:', e);
            return false;
        }
    }
    
    // Auto-save function
    function autoSaveCurrentConversation() {
        if (currentConversationId && currentConversation && currentConversation.messages.length > 0) {
            saveCurrentConversation();
        }
    }
    
    // Add a message to the current conversation
    function addMessageToConversation(message) {
        // Ensure we have a current conversation
        if (!currentConversationId) {
            createNewConversation();
        }
        
        // Add the message
        currentConversation.messages.push({
            ...message,
            timestamp: new Date().toISOString(),
            id: 'msg_' + Date.now() + '_' + Math.random().toString(36).substring(2, 7)
        });
        
        // Save after each message is added
        saveCurrentConversation();
        
        return currentConversation.messages.length;
    }
    
    // Get the current conversation history
    function getCurrentConversationHistory() {
        if (!currentConversation) return [];
        return currentConversation.messages;
    }
    
    // Update the conversation title
    function updateConversationTitle(title) {
        if (!currentConversation) return false;
        
        currentConversation.title = title;
        saveCurrentConversation();
        return true;
    }
    
    // Generate a title based on conversation content
    function generateConversationTitle() {
        if (!currentConversation || currentConversation.messages.length < 2) {
            return 'New Conversation';
        }
        
        // Get the first user message
        const firstUserMessage = currentConversation.messages.find(msg => msg.role === 'user');
        
        if (firstUserMessage) {
            // Use the first user message as basis for title
            const titleBase = firstUserMessage.content.trim();
            
            // Truncate and clean up
            return truncateText(titleBase, 40);
        }
        
        return 'Conversation ' + new Date().toLocaleString();
    }
    
    // Delete a conversation
    function deleteConversation(conversationId) {
        try {
            // Remove from storage
            localStorage.removeItem(STORAGE_KEY_PREFIX + conversationId);
            
            // Update index
            const existingList = getConversationsList();
            const updatedList = existingList.filter(c => c.id !== conversationId);
            localStorage.setItem(CONVERSATIONS_INDEX_KEY, JSON.stringify(updatedList));
            
            console.log('Deleted conversation:', conversationId);
            
            // If this was the current conversation, reset
            if (currentConversationId === conversationId) {
                currentConversationId = null;
                currentConversation = null;
            }
            
            return true;
        } catch (e) {
            console.error('Error deleting conversation:', e);
            return false;
        }
    }
    
    // Helper: Truncate text to specified length
    function truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
    
    // Load the conversations index
    function loadConversationsIndex() {
        try {
            const indexJson = localStorage.getItem(CONVERSATIONS_INDEX_KEY);
            if (!indexJson) {
                // Initialize with empty array if not found
                localStorage.setItem(CONVERSATIONS_INDEX_KEY, JSON.stringify([]));
            }
        } catch (e) {
            console.error('Error initializing conversations index:', e);
        }
    }
    
    // Public API
    return {
        initialize,
        createNewConversation,
        loadConversation,
        saveCurrentConversation,
        addMessageToConversation,
        getCurrentConversationHistory,
        updateConversationTitle,
        generateConversationTitle,
        getConversationsList,
        deleteConversation,
        getCurrentConversationId: () => currentConversationId,
        isConversationActive: () => !!currentConversationId
    };
})();

// Initialize the storage system
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing conversation storage system...');
    window.enhancedConversationStorage = enhancedConversationStorage;
    enhancedConversationStorage.initialize();
    
    // Create a new conversation if none exists
    if (!enhancedConversationStorage.isConversationActive()) {
        const newConvId = enhancedConversationStorage.createNewConversation();
        console.log('Created new conversation:', newConvId);
    }
});
