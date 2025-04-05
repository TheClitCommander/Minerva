/**
 * Dashboard-Conversation Integration
 * 
 * Connects the conversation manager with the dashboard options ring
 * to display conversations with concept-based names
 */

document.addEventListener('DOMContentLoaded', function() {
  initDashboardConversationIntegration();
});

/**
 * Initialize the integration between conversations and dashboard
 */
function initDashboardConversationIntegration() {
  // Wait for both systems to be available
  const checkSystems = setInterval(() => {
    const conversationsReady = window.conversationManager || 
      (typeof MinervaConversationManager !== 'undefined');
    
    const dashboardReady = document.getElementById('options-ring') !== null;
    
    if (conversationsReady && dashboardReady) {
      clearInterval(checkSystems);
      console.log('Both conversation system and dashboard ready, initializing integration');
      setupConversationsInOptionsRing();
    }
  }, 500);
}

/**
 * Update the conversations in the options ring
 */
function updateConversationsInOptionsRing() {
  // Check if we can access the ring
  const optionsRing = document.getElementById('options-ring');
  if (!optionsRing) {
    console.warn('Options ring not found, cannot update conversations');
    return;
  }
  
  // Get conversation data
  let conversations = [];
  
  // Try to get conversations from conversation manager
  if (window.conversationManager && typeof window.conversationManager.getAllConversations === 'function') {
    conversations = window.conversationManager.getAllConversations();
  } else {
    // Fallback to localStorage
    try {
      const savedConversations = JSON.parse(localStorage.getItem('minerva_conversations'));
      if (savedConversations && savedConversations.general) {
        conversations = savedConversations.general;
      }
    } catch (e) {
      console.error('Error loading conversations:', e);
    }
  }
  
  // Find or create the conversation section in the ring
  let conversationSection = document.querySelector('.option-section[data-section="conversations"]');
  
  if (!conversationSection) {
    console.log('Creating new conversations section in options ring');
    // Create the section
    conversationSection = document.createElement('div');
    conversationSection.className = 'option-section';
    conversationSection.setAttribute('data-section', 'conversations');
    
    // Create the label
    const sectionLabel = document.createElement('div');
    sectionLabel.className = 'section-label';
    sectionLabel.textContent = 'Conversations';
    
    // Add the label to the section
    conversationSection.appendChild(sectionLabel);
    
    // Add the section to the ring
    optionsRing.appendChild(conversationSection);
  }
  
  // Clear existing conversation options (except the label)
  const existingOptions = conversationSection.querySelectorAll('.option:not(.section-label)');
  existingOptions.forEach(option => option.remove());
  
  // Add conversation options (up to 8 most recent)
  const recentConversations = conversations
    .sort((a, b) => new Date(b.lastUpdated || b.created) - new Date(a.lastUpdated || a.created))
    .slice(0, 8);
  
  recentConversations.forEach(conversation => {
    // Create the option
    const option = document.createElement('div');
    option.className = 'option conversation-option';
    option.setAttribute('data-id', conversation.id);
    option.setAttribute('data-conversation-id', conversation.id);
    
    // Create the icon
    const icon = document.createElement('div');
    icon.className = 'option-icon';
    icon.innerHTML = '💬';
    
    // Create the label
    const label = document.createElement('div');
    label.className = 'option-label';
    label.textContent = conversation.title || 'Unnamed Conversation';
    
    // Add elements to the option
    option.appendChild(icon);
    option.appendChild(label);
    
    // Add option to the section
    conversationSection.appendChild(option);
    
    // Add event listener
    option.addEventListener('click', () => {
      openConversation(conversation.id);
    });
  });
  
  // Update the section visibility
  if (recentConversations.length > 0) {
    conversationSection.style.display = 'block';
  } else {
    conversationSection.style.display = 'none';
  }
  
  // Make global function available
  window.updateConversationsInOptionsRing = updateConversationsInOptionsRing;
}

/**
 * Open a conversation from the options ring
 * @param {String} conversationId - ID of the conversation to open
 */
function openConversation(conversationId) {
  // Open the conversation in the manager if available
  if (window.conversationManager && typeof window.conversationManager.loadConversation === 'function') {
    window.conversationManager.loadConversation(conversationId);
    
    // Update the content display
    if (typeof updateContent === 'function') {
      updateContent('conversations');
    }
  } else {
    console.warn('Conversation manager not available, cannot open conversation');
    
    // Fallback: Try to show the conversations view
    const conversationsView = document.getElementById('conversations-view');
    if (conversationsView && typeof initConversationsManager === 'function') {
      // Show the conversations view
      document.querySelectorAll('#content-display > div').forEach(div => {
        div.classList.add('hidden');
      });
      conversationsView.classList.remove('hidden');
      
      // Initialize the manager
      initConversationsManager();
    }
  }
}

/**
 * Set up the initial conversations in the options ring
 */
function setupConversationsInOptionsRing() {
  console.log('Setting up conversations in options ring');
  
  // Add the stylesheet if not present
  addConversationsStylesheet();
  
  // Update the conversations in the ring
  updateConversationsInOptionsRing();
  
  // Set up a periodic update (every 30 seconds)
  setInterval(updateConversationsInOptionsRing, 30000);
}

/**
 * Add the conversations stylesheet
 */
function addConversationsStylesheet() {
  // Check if stylesheet already exists
  if (document.getElementById('conversations-styles')) {
    return;
  }
  
  // Create the style element
  const style = document.createElement('style');
  style.id = 'conversations-styles';
  style.textContent = `
    .conversation-option {
      background-color: rgba(95, 158, 160, 0.2);
      border: 1px solid rgba(95, 158, 160, 0.4);
      transition: all 0.3s ease;
    }
    
    .conversation-option:hover {
      background-color: rgba(95, 158, 160, 0.4);
      transform: scale(1.05);
    }
    
    .conversations-view {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }
    
    .conversations-container {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    
    .conversation-card {
      background-color: rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 15px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;
    }
    
    .conversation-card:hover {
      transform: translateY(-5px);
      box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .conversation-preview {
      margin: 10px 0;
      font-style: italic;
      opacity: 0.8;
    }
    
    .conversation-meta {
      display: flex;
      justify-content: space-between;
      font-size: 0.8em;
      opacity: 0.7;
    }
  `;
  
  // Add to the document head
  document.head.appendChild(style);
}

// Make functions globally available
window.updateConversationsInOptionsRing = updateConversationsInOptionsRing;
window.openConversation = openConversation;
