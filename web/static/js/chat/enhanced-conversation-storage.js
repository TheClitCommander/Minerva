/**
 * Enhanced Conversation Storage Manager
 * 
 * This is the primary system for managing Minerva's conversation memory.
 * It provides functionality for storing, retrieving, and managing conversations
 * with proper metadata and organization.
 */

const enhancedConversationStorage = (function() {
  // Private state
  let conversations = [];
  let currentConversationId = null;
  
  // Storage constants
  const STORAGE_KEY = 'minerva_conversations';
  const CURRENT_CONVERSATION_KEY = 'minerva_current_conversation';
  
  // Initialize on load
  function initialize() {
    console.log('Initializing Enhanced Conversation Storage');
    loadFromLocalStorage();
    return true;
  }
  
  // Save current state to localStorage
  function saveToLocalStorage() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      localStorage.setItem(CURRENT_CONVERSATION_KEY, currentConversationId);
      console.log('Saved conversations to localStorage');
    } catch (error) {
      console.error('Error saving conversations to localStorage:', error);
    }
  }
  
  // Load from localStorage
  function loadFromLocalStorage() {
    try {
      const savedConversations = localStorage.getItem(STORAGE_KEY);
      if (savedConversations) {
        conversations = JSON.parse(savedConversations);
        console.log(`Loaded ${conversations.length} conversations from localStorage`);
      }
      
      currentConversationId = localStorage.getItem(CURRENT_CONVERSATION_KEY);
      
      // Create a new conversation if none exists
      if (conversations.length === 0) {
        createNewConversation();
      }
    } catch (error) {
      console.error('Error loading conversations from localStorage:', error);
      conversations = [];
      createNewConversation();
    }
  }
  
  // Create a new conversation
  function createNewConversation(title = 'New Chat') {
    const conversationId = 'conv_' + Date.now();
    const newConversation = {
      id: conversationId,
      title: title,
      messages: [],
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      projectId: null,
      summary: '',
      tags: []
    };
    
    conversations.push(newConversation);
    currentConversationId = conversationId;
    saveToLocalStorage();
    console.log('Created new conversation:', conversationId);
    return conversationId;
  }
  
  // Add a message to the current conversation
  function addMessageToConversation(message) {
    if (!message || !message.role || !message.content) {
      console.error('Invalid message format:', message);
      return false;
    }
    
    // Ensure we have a current conversation
    if (!currentConversationId || !getCurrentConversation()) {
      currentConversationId = createNewConversation();
    }
    
    const currentConversation = getCurrentConversation();
    
    // Create a properly formatted message object
    const messageObj = {
      role: message.role,
      content: message.content,
      timestamp: message.timestamp || new Date().toISOString(),
      model: message.model || 'minerva-core'
    };
    
    // Add model info if provided
    if (message.model_info) {
      messageObj.model_info = message.model_info;
    }
    
    // Add the message to the current conversation
    currentConversation.messages.push(messageObj);
    
    // Update the conversation's updated timestamp
    currentConversation.updated = new Date().toISOString();
    
    // Generate a title if this is a new conversation with at least one exchange
    if (currentConversation.title === 'New Chat' && currentConversation.messages.length >= 3) {
      generateConversationTitle();
    }
    
    // Save to localStorage
    saveToLocalStorage();
    
    console.log('Added message to conversation:', currentConversationId, 'New count:', currentConversation.messages.length);
    return true;
  }
  
  // Generate a title based on the first user message
  function generateConversationTitle() {
    const currentConversation = getCurrentConversation();
    if (!currentConversation) return null;
    
    // Find the first user message
    const firstUserMessage = currentConversation.messages.find(m => m.role === 'user');
    if (!firstUserMessage) return null;
    
    // Generate title from first user message (max 50 chars)
    let title = firstUserMessage.content.substring(0, 50);
    if (firstUserMessage.content.length > 50) {
      title += '...';
    }
    
    // Update the conversation title
    currentConversation.title = title;
    saveToLocalStorage();
    
    console.log('Generated conversation title:', title);
    return title;
  }
  
  // Update an existing conversation title
  function updateConversationTitle(conversationId, title) {
    const id = conversationId || currentConversationId;
    if (!id) return false;
    
    const conversation = conversations.find(c => c.id === id);
    if (!conversation) return false;
    
    conversation.title = title;
    saveToLocalStorage();
    
    return true;
  }
  
  // Get the current conversation
  function getCurrentConversation() {
    if (!currentConversationId) {
      if (conversations.length === 0) {
        createNewConversation();
      } else {
        currentConversationId = conversations[conversations.length - 1].id;
      }
    }
    
    return conversations.find(c => c.id === currentConversationId) || null;
  }
  
  // Get the current conversation history
  function getCurrentConversationHistory() {
    const conversation = getCurrentConversation();
    return conversation ? conversation.messages : [];
  }
  
  // Get all conversations
  function getAllConversations() {
    return [...conversations];
  }
  
  // Delete a conversation
  function deleteConversation(conversationId) {
    const id = conversationId || currentConversationId;
    if (!id) return false;
    
    const index = conversations.findIndex(c => c.id === id);
    if (index === -1) return false;
    
    conversations.splice(index, 1);
    
    // If we deleted the current conversation, set current to the last one
    if (id === currentConversationId) {
      currentConversationId = conversations.length > 0 ? 
        conversations[conversations.length - 1].id : null;
    }
    
    saveToLocalStorage();
    return true;
  }
  
  // Clear all conversations
  function clearAllConversations() {
    conversations = [];
    createNewConversation();
    saveToLocalStorage();
    return true;
  }
  
  // Set a project ID for the current conversation
  function setConversationProject(projectId) {
    const conversation = getCurrentConversation();
    if (!conversation) return false;
    
    conversation.projectId = projectId;
    saveToLocalStorage();
    return true;
  }
  
  // Add a tag to the current conversation
  function addConversationTag(tag) {
    const conversation = getCurrentConversation();
    if (!conversation) return false;
    
    if (!conversation.tags) {
      conversation.tags = [];
    }
    
    if (!conversation.tags.includes(tag)) {
      conversation.tags.push(tag);
      saveToLocalStorage();
    }
    
    return true;
  }
  
  // Set the current conversation by ID
  function setCurrentConversation(conversationId) {
    if (!conversationId) return false;
    
    const exists = conversations.some(c => c.id === conversationId);
    if (!exists) return false;
    
    currentConversationId = conversationId;
    saveToLocalStorage();
    return true;
  }
  
  // Initialize at load time
  initialize();
  
  // Public API
  return {
    addMessageToConversation,
    createNewConversation,
    getCurrentConversation,
    getCurrentConversationHistory,
    getAllConversations,
    deleteConversation,
    clearAllConversations,
    setConversationProject,
    addConversationTag,
    setCurrentConversation,
    generateConversationTitle,
    updateConversationTitle
  };
})();

// Legacy adapter for backward compatibility
function saveToConversationMemory(role, content, modelInfo = null) {
  if (!content) return false;
  
  return enhancedConversationStorage.addMessageToConversation({
    role: role,
    content: content,
    timestamp: new Date().toISOString(),
    model_info: modelInfo
  });
}

// Make available globally
window.enhancedConversationStorage = enhancedConversationStorage;
