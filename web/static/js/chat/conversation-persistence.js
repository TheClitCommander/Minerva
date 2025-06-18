/**
 * Minerva Chat Persistence Module
 * Handles saving, loading, and managing chat conversations
 * Part of our comprehensive integration plan for embedding chat functionality
 */

// Constants
const STORAGE_KEY = 'minerva_conversations';
const MAX_CONVERSATIONS = 50;
const MAX_MESSAGES_PER_CONVERSATION = 100;

/**
 * Save the current conversation to localStorage
 * This function is referenced in multiple places and must be globally available
 */
function saveCurrentConversation(userMessage, minervaResponse) {
  try {
    console.log('Saving conversation data to localStorage...');
    
    // Get the current conversation ID or create a new one
    const conversationId = window.conversationId || ('conv_' + Date.now());
    
    // Ensure window.conversationId is set for future reference
    window.conversationId = conversationId;
    
    // Get project context if available
    const projectContext = {
      id: window.activeProject?.id || null,
      name: window.activeProject?.name || null
    };
    
    // Load existing conversations
    const storedData = localStorage.getItem(STORAGE_KEY);
    let conversations = [];
    
    if (storedData) {
      try {
        conversations = JSON.parse(storedData);
        if (!Array.isArray(conversations)) {
          console.warn('Invalid conversations data in localStorage, resetting');
          conversations = [];
        }
      } catch (e) {
        console.error('Error parsing conversations from localStorage:', e);
      }
    }
    
    // Find existing conversation or create new one
    let conversation = conversations.find(c => c.id === conversationId);
    
    if (!conversation) {
      conversation = {
        id: conversationId,
        title: userMessage ? userMessage.substring(0, 30) + (userMessage.length > 30 ? '...' : '') : 'New Conversation',
        messages: [],
        projectContext: projectContext,
        created: new Date().toISOString(),
        updated: new Date().toISOString()
      };
      
      // Add to front of array
      conversations.unshift(conversation);
    } else {
      // Move to front (most recent)
      conversations = conversations.filter(c => c.id !== conversationId);
      conversations.unshift(conversation);
    }
    
    // Add messages if provided
    if (userMessage) {
      conversation.messages.push({
        sender: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
      });
    }
    
    if (minervaResponse) {
      conversation.messages.push({
        sender: 'minerva',
        content: minervaResponse,
        timestamp: new Date().toISOString()
      });
    }
    
    // Limit messages per conversation to prevent localStorage overflow
    if (conversation.messages.length > MAX_MESSAGES_PER_CONVERSATION) {
      conversation.messages = conversation.messages.slice(-MAX_MESSAGES_PER_CONVERSATION);
    }
    
    // Update timestamp
    conversation.updated = new Date().toISOString();
    
    // Limit total conversations
    if (conversations.length > MAX_CONVERSATIONS) {
      conversations = conversations.slice(0, MAX_CONVERSATIONS);
    }
    
    // Save back to localStorage
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    
    // Trigger event for other components
    window.dispatchEvent(new CustomEvent('minerva-conversation-updated', {
      detail: { conversationId, conversation }
    }));
    
    return { success: true, conversationId };
  } catch (error) {
    console.error('Error saving conversation:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Load a specific conversation by ID
 */
function loadConversation(conversationId) {
  try {
    const storedData = localStorage.getItem(STORAGE_KEY);
    if (!storedData) return null;
    
    const conversations = JSON.parse(storedData);
    return conversations.find(c => c.id === conversationId) || null;
  } catch (error) {
    console.error('Error loading conversation:', error);
    return null;
  }
}

/**
 * Get all saved conversations
 */
function getAllConversations() {
  try {
    const storedData = localStorage.getItem(STORAGE_KEY);
    if (!storedData) return [];
    
    return JSON.parse(storedData) || [];
  } catch (error) {
    console.error('Error getting all conversations:', error);
    return [];
  }
}

/**
 * Delete a conversation by ID
 */
function deleteConversation(conversationId) {
  try {
    const storedData = localStorage.getItem(STORAGE_KEY);
    if (!storedData) return false;
    
    let conversations = JSON.parse(storedData);
    conversations = conversations.filter(c => c.id !== conversationId);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    return true;
  } catch (error) {
    console.error('Error deleting conversation:', error);
    return false;
  }
}

/**
 * Clear all conversations
 */
function clearAllConversations() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (error) {
    console.error('Error clearing conversations:', error);
    return false;
  }
}

// Make functions globally available
window.saveCurrentConversation = saveCurrentConversation;
window.loadConversation = loadConversation;
window.getAllConversations = getAllConversations;
window.deleteConversation = deleteConversation;
window.clearAllConversations = clearAllConversations;

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('📝 Conversation persistence module initialized');
  
  // Set initial conversation ID if not already set
  if (!window.conversationId) {
    const lastConversation = getAllConversations()[0] || null;
    window.conversationId = lastConversation?.id || ('conv_' + Date.now());
    console.log('Set initial conversation ID:', window.conversationId);
  }
});
