/**
 * Minerva Conversation Management System
 * Handles conversation storage, retrieval, and organization
 * Allows conversations to be pinned, tagged, and saved as memories
 */

class MinervaConversationManager {
  constructor(options = {}) {
    // Core settings
    this.container = options.container || document.getElementById('conversation-manager-container');
    this.storageKey = 'minerva_conversations';
    this.defaultExpiryDays = 30; // Configurable expiry for conversations
    this.activeProject = options.activeProject || null;
    this.activeAgent = options.activeAgent || 'general-assistant';
    
    // Initialize conversation storage
    this.conversations = this.loadConversations();
    
    // Link to memory manager if available
    this.memoryManager = options.memoryManager || null;
    
    // DOM elements created dynamically
    this.panel = null;
    this.conversationList = null;
    this.searchInput = null;
    this.filterSelect = null;
    
    // Auto-save interval
    this.autoSaveInterval = null;
    
    // Only initialize UI if container exists
    if (this.container) {
      this.initializeUI();
    }
    
    // Set up auto-save interval (every 30 seconds)
    this.autoSaveInterval = setInterval(() => this.saveConversations(), 30000);
  }
  
  /**
   * Load saved conversations from localStorage
   */
  loadConversations() {
    const savedConversations = localStorage.getItem(this.storageKey);
    if (savedConversations) {
      try {
        return JSON.parse(savedConversations);
      } catch (e) {
        console.error('Failed to parse saved conversations:', e);
      }
    }
    
    // Default empty conversation structure
    return {
      general: [],           // General conversations not tied to projects
      projects: {},          // Project-specific conversations
      agents: {}             // Agent-specific conversations
    };
  }
  
  /**
   * Save conversations to localStorage
   */
  saveConversations() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.conversations));
  }
  
  /**
   * Initialize the Conversation Management UI
   */
  initializeUI() {
    if (!this.container) {
      console.warn('Conversation manager container not found. UI will not be created.');
      return;
    }
    
    // Create the main panel
    this.panel = document.createElement('div');
    this.panel.className = 'conversation-panel';
    this.panel.innerHTML = `
      <div class="conversation-header">
        <h3>Conversation History</h3>
        <div class="conversation-search-container">
          <input type="text" id="conversation-search" placeholder="Search conversations..." />
          <select id="conversation-filter">
            <option value="all">All</option>
            <option value="pinned">Pinned</option>
            <option value="project">Project</option>
            <option value="agent">Agent</option>
          </select>
        </div>
        <button id="clear-conversations-btn" class="action-button warning-button">Clear All</button>
      </div>
      <div class="conversation-tabs">
        <button class="conversation-tab active" data-tab="all">All Chats</button>
        <button class="conversation-tab" data-tab="pinned">Pinned</button>
        <button class="conversation-tab" data-tab="project">Projects</button>
        <button class="conversation-tab" data-tab="agent">Agents</button>
      </div>
      <div class="conversation-list"></div>
    `;
    
    this.container.appendChild(this.panel);
    
    // Get references to UI elements
    this.conversationList = this.panel.querySelector('.conversation-list');
    this.searchInput = this.panel.querySelector('#conversation-search');
    this.filterSelect = this.panel.querySelector('#conversation-filter');
    this.clearBtn = this.panel.querySelector('#clear-conversations-btn');
    this.tabs = this.panel.querySelectorAll('.conversation-tab');
    
    // Add event listeners
    this.searchInput.addEventListener('input', () => this.filterConversations());
    this.clearBtn.addEventListener('click', () => this.promptClearConversations());
    
    // Set up tab switching
    this.tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.tabs.forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        this.activeTab = e.target.dataset.tab;
        this.renderConversationList();
      });
    });
    
    // Initial render
    this.renderConversationList();
  }
  
  /**
   * Show a confirmation dialog before clearing conversations
   */
  promptClearConversations() {
    // Create the modal
    const modal = document.createElement('div');
    modal.className = 'conversation-modal';
    
    modal.innerHTML = `
      <div class="conversation-modal-content">
        <div class="conversation-modal-header">
          <h3>Clear Conversations</h3>
          <button class="close-modal">&times;</button>
        </div>
        <div class="conversation-modal-body">
          <p>Are you sure you want to clear all non-pinned conversations?</p>
          <p>This action cannot be undone. Pinned conversations will not be affected.</p>
        </div>
        <div class="conversation-modal-footer">
          <button class="cancel-action">Cancel</button>
          <button class="confirm-clear warning-button">Clear Conversations</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.querySelector('.close-modal').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    modal.querySelector('.cancel-action').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    modal.querySelector('.confirm-clear').addEventListener('click', () => {
      this.clearConversations();
      document.body.removeChild(modal);
    });
  }
  
  /**
   * Clear all non-pinned conversations
   */
  clearConversations() {
    // Filter out pinned conversations
    this.conversations.general = this.conversations.general.filter(c => c.pinned);
    
    // Clear project-specific conversations
    for (const projectId in this.conversations.projects) {
      this.conversations.projects[projectId] = this.conversations.projects[projectId].filter(c => c.pinned);
    }
    
    // Clear agent-specific conversations
    for (const agentId in this.conversations.agents) {
      this.conversations.agents[agentId] = this.conversations.agents[agentId].filter(c => c.pinned);
    }
    
    this.saveConversations();
    this.renderConversationList();
  }
  
  /**
   * Render the conversation list based on current filters
   */
  renderConversationList() {
    if (!this.conversationList) return;
    
    const searchTerm = this.searchInput ? this.searchInput.value.toLowerCase() : '';
    const activeTab = this.activeTab || 'all';
    
    // Clear current list
    this.conversationList.innerHTML = '';
    
    let visibleConversations = [];
    
    // Collect conversations based on active tab
    if (activeTab === 'all' || activeTab === 'general') {
      visibleConversations = visibleConversations.concat(
        this.conversations.general.map(c => ({...c, type: 'general'}))
      );
    }
    
    if (activeTab === 'all' || activeTab === 'project') {
      for (const projectId in this.conversations.projects) {
        visibleConversations = visibleConversations.concat(
          this.conversations.projects[projectId].map(c => ({...c, type: 'project', projectId}))
        );
      }
    }
    
    if (activeTab === 'all' || activeTab === 'agent') {
      for (const agentId in this.conversations.agents) {
        visibleConversations = visibleConversations.concat(
          this.conversations.agents[agentId].map(c => ({...c, type: 'agent', agentId}))
        );
      }
    }
    
    // Filter by pinned if that tab is selected
    if (activeTab === 'pinned') {
      visibleConversations = this.getAllConversations().filter(c => c.pinned);
    }
    
    // Apply search filter
    if (searchTerm) {
      visibleConversations = visibleConversations.filter(conversation => {
        // Search in title
        if (conversation.title.toLowerCase().includes(searchTerm)) {
          return true;
        }
        
        // Search in messages
        if (conversation.messages && conversation.messages.some(m => 
          m.content.toLowerCase().includes(searchTerm))) {
          return true;
        }
        
        // Search in tags
        if (conversation.tags && conversation.tags.some(tag => 
          tag.toLowerCase().includes(searchTerm))) {
          return true;
        }
        
        return false;
      });
    }
    
    // Sort by last updated date descending
    visibleConversations.sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));
    
    // Render each conversation
    visibleConversations.forEach(conversation => {
      const conversationItem = document.createElement('div');
      conversationItem.className = `conversation-item conversation-${conversation.type}`;
      if (conversation.pinned) {
        conversationItem.classList.add('pinned');
      }
      conversationItem.dataset.id = conversation.id;
      
      // Format the date
      const lastUpdated = new Date(conversation.lastUpdated);
      const formattedDate = lastUpdated.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric', 
        year: 'numeric'
      });
      
      // Get a preview of the conversation
      const messagePreview = this.getConversationPreview(conversation);
      
      // Build the HTML
      conversationItem.innerHTML = `
        <div class="conversation-item-header">
          <h4>${conversation.title || 'Untitled Conversation'}</h4>
          <div class="conversation-badges">
            ${conversation.pinned ? '<span class="conversation-pinned-badge">Pinned</span>' : ''}
            <span class="conversation-type-badge">${conversation.type}</span>
            ${conversation.projectId ? `<span class="conversation-project-badge">${this.getProjectName(conversation.projectId)}</span>` : ''}
            ${conversation.agentId ? `<span class="conversation-agent-badge">${this.getAgentName(conversation.agentId)}</span>` : ''}
          </div>
        </div>
        <div class="conversation-preview">${messagePreview}</div>
        <div class="conversation-footer">
          <div class="conversation-date">Last updated: ${formattedDate}</div>
          <div class="conversation-actions">
            <button class="load-conversation" data-id="${conversation.id}">Load</button>
            <button class="save-conversation-to-memory" data-id="${conversation.id}">Save to Memory</button>
            <button class="toggle-pin" data-id="${conversation.id}">${conversation.pinned ? 'Unpin' : 'Pin'}</button>
            <button class="delete-conversation" data-id="${conversation.id}">Delete</button>
          </div>
        </div>
      `;
      
      // Add event listeners for actions
      conversationItem.querySelector('.load-conversation').addEventListener('click', () => 
        this.loadConversation(conversation.id)
      );
      
      conversationItem.querySelector('.save-conversation-to-memory').addEventListener('click', () => 
        this.saveToMemory(conversation.id)
      );
      
      conversationItem.querySelector('.toggle-pin').addEventListener('click', () => 
        this.togglePinConversation(conversation.id)
      );
      
      conversationItem.querySelector('.delete-conversation').addEventListener('click', () => 
        this.deleteConversation(conversation.id)
      );
      
      this.conversationList.appendChild(conversationItem);
    });
    
    // Show empty state if no conversations
    if (visibleConversations.length === 0) {
      this.conversationList.innerHTML = `
        <div class="empty-state">
          <p>No conversations found. ${searchTerm ? 'Try a different search term.' : 'Start a new conversation to see it here.'}</p>
        </div>
      `;
    }
  }
  
  /**
   * Get a project name from projectId
   */
  getProjectName(projectId) {
    if (window.minervaProjects && window.minervaProjects[projectId]) {
      return window.minervaProjects[projectId].name;
    }
    return projectId;
  }
  
  /**
   * Get an agent name from agentId
   */
  getAgentName(agentId) {
    const agents = {
      'general-assistant': 'General Assistant',
      'research-agent': 'Research Agent',
      'coding-agent': 'Coding Expert',
      'writing-agent': 'Writing Assistant'
    };
    
    return agents[agentId] || agentId;
  }
  
  /**
   * Get a short preview of a conversation
   */
  getConversationPreview(conversation) {
    if (!conversation.messages || conversation.messages.length === 0) {
      return 'No messages';
    }
    
    // Find the last user message, or use the last message if no user messages
    const lastUserMessage = conversation.messages
      .filter(m => m.role === 'user')
      .pop();
    
    const previewMessage = lastUserMessage || conversation.messages[conversation.messages.length - 1];
    
    // Truncate the content if it's too long
    let preview = previewMessage.content;
    if (preview.length > 100) {
      preview = preview.substring(0, 100) + '...';
    }
    
    return preview;
  }
  
  /**
   * Get all conversations in a flat array
   */
  getAllConversations() {
    const allConversations = [];
    
    // Add general conversations
    this.conversations.general.forEach(c => {
      allConversations.push({...c, type: 'general'});
    });
    
    // Add project-specific conversations
    for (const projectId in this.conversations.projects) {
      this.conversations.projects[projectId].forEach(c => {
        allConversations.push({...c, type: 'project', projectId});
      });
    }
    
    // Add agent-specific conversations
    for (const agentId in this.conversations.agents) {
      this.conversations.agents[agentId].forEach(c => {
        allConversations.push({...c, type: 'agent', agentId});
      });
    }
    
    return allConversations;
  }
  
  /**
   * Find a conversation by its ID
   */
  findConversationById(conversationId) {
    // Search in general conversations
    let conversation = this.conversations.general.find(c => c.id === conversationId);
    if (conversation) {
      return { conversation, type: 'general' };
    }
    
    // Search in project conversations
    for (const projectId in this.conversations.projects) {
      conversation = this.conversations.projects[projectId].find(c => c.id === conversationId);
      if (conversation) {
        return { conversation, type: 'project', projectId };
      }
    }
    
    // Search in agent conversations
    for (const agentId in this.conversations.agents) {
      conversation = this.conversations.agents[agentId].find(c => c.id === conversationId);
      if (conversation) {
        return { conversation, type: 'agent', agentId };
      }
    }
    
    return null;
  }
  
  /**
   * Toggle the pinned status of a conversation
   */
  togglePinConversation(conversationId) {
    const result = this.findConversationById(conversationId);
    if (!result) return;
    
    const { conversation } = result;
    conversation.pinned = !conversation.pinned;
    
    this.saveConversations();
    this.renderConversationList();
  }
  
  /**
   * Delete a conversation
   */
  deleteConversation(conversationId) {
    const result = this.findConversationById(conversationId);
    if (!result) return;
    
    const { type, projectId, agentId } = result;
    
    if (type === 'general') {
      this.conversations.general = this.conversations.general.filter(c => c.id !== conversationId);
    } else if (type === 'project' && projectId) {
      this.conversations.projects[projectId] = this.conversations.projects[projectId].filter(c => c.id !== conversationId);
    } else if (type === 'agent' && agentId) {
      this.conversations.agents[agentId] = this.conversations.agents[agentId].filter(c => c.id !== conversationId);
    }
    
    this.saveConversations();
    this.renderConversationList();
  }
  
  /**
   * Save a conversation to memory
   */
  saveToMemory(conversationId) {
    if (!this.memoryManager) {
      console.warn('Memory manager not available. Cannot save conversation to memory.');
      return;
    }
    
    const result = this.findConversationById(conversationId);
    if (!result) return;
    
    const { conversation, type, projectId, agentId } = result;
    
    // Prompt for a title
    const modal = document.createElement('div');
    modal.className = 'conversation-modal';
    
    modal.innerHTML = `
      <div class="conversation-modal-content">
        <div class="conversation-modal-header">
          <h3>Save Conversation to Memory</h3>
          <button class="close-modal">&times;</button>
        </div>
        <div class="conversation-modal-body">
          <div class="form-group">
            <label for="memory-title">Memory Title</label>
            <input type="text" id="memory-title" value="${conversation.title || 'Conversation from ' + new Date().toLocaleDateString()}" required>
          </div>
          <div class="form-group">
            <label for="memory-type">Memory Type</label>
            <select id="memory-type">
              <option value="global">Global (available everywhere)</option>
              <option value="project" ${type === 'project' ? 'selected' : ''}>Project-specific</option>
              <option value="agent" ${type === 'agent' ? 'selected' : ''}>Agent-specific</option>
            </select>
          </div>
          <div class="form-group project-selector" ${type !== 'project' ? 'style="display:none;"' : ''}>
            <label for="memory-project">Project</label>
            <select id="memory-project">
              ${this.getProjectOptions(projectId)}
            </select>
          </div>
          <div class="form-group agent-selector" ${type !== 'agent' ? 'style="display:none;"' : ''}>
            <label for="memory-agent">Agent</label>
            <select id="memory-agent">
              ${this.getAgentOptions(agentId)}
            </select>
          </div>
        </div>
        <div class="conversation-modal-footer">
          <button class="cancel-action">Cancel</button>
          <button class="save-to-memory-action">Save to Memory</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.querySelector('.close-modal').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    modal.querySelector('.cancel-action').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    // Show/hide project/agent selectors based on memory type
    const typeSelect = modal.querySelector('#memory-type');
    const projectSelector = modal.querySelector('.project-selector');
    const agentSelector = modal.querySelector('.agent-selector');
    
    typeSelect.addEventListener('change', () => {
      projectSelector.style.display = typeSelect.value === 'project' ? 'block' : 'none';
      agentSelector.style.display = typeSelect.value === 'agent' ? 'block' : 'none';
    });
    
    // Handle save to memory
    modal.querySelector('.save-to-memory-action').addEventListener('click', () => {
      const titleInput = modal.querySelector('#memory-title');
      const memoryType = modal.querySelector('#memory-type').value;
      const projectSelect = modal.querySelector('#memory-project');
      const agentSelect = modal.querySelector('#memory-agent');
      
      // Validate title
      if (!titleInput.value.trim()) {
        alert('Please enter a title for the memory.');
        return;
      }
      
      // Save conversation to memory
      this.memoryManager.saveConversationAsMemory(
        conversation.messages,
        titleInput.value.trim(),
        memoryType,
        memoryType === 'project' ? projectSelect.value : 
        memoryType === 'agent' ? agentSelect.value : null
      );
      
      document.body.removeChild(modal);
      
      // Show success message
      this.showToast('Conversation saved to memory!');
    });
  }
  
  /**
   * Get options for project dropdown
   */
  getProjectOptions(selectedProject = null) {
    // Get projects from minervaProjects
    let options = '<option value="">Select a project</option>';
    
    if (window.minervaProjects) {
      for (const projectId in window.minervaProjects) {
        const project = window.minervaProjects[projectId];
        options += `<option value="${projectId}" ${projectId === selectedProject ? 'selected' : ''}>${project.name}</option>`;
      }
    }
    
    return options;
  }
  
  /**
   * Get options for agent dropdown
   */
  getAgentOptions(selectedAgent = null) {
    // For now, we have a fixed list of agents until we have a proper agent system
    const agents = {
      'general-assistant': 'General Assistant',
      'research-agent': 'Research Agent',
      'coding-agent': 'Coding Expert',
      'writing-agent': 'Writing Assistant'
    };
    
    let options = '<option value="">Select an agent</option>';
    
    for (const agentId in agents) {
      const agentName = agents[agentId];
      options += `<option value="${agentId}" ${agentId === selectedAgent ? 'selected' : ''}>${agentName}</option>`;
    }
    
    return options;
  }
  
  /**
   * Load a conversation into the chat UI
   */
  loadConversation(conversationId) {
    const result = this.findConversationById(conversationId);
    if (!result) return;
    
    const { conversation } = result;
    
    // Publish an event that the chat UI can listen for
    const event = new CustomEvent('minerva:load-conversation', {
      detail: {
        conversation: conversation
      }
    });
    
    document.dispatchEvent(event);
    
    // Hide the conversation panel if it's being displayed in a modal
    const modal = document.querySelector('.conversation-modal');
    if (modal) {
      document.body.removeChild(modal);
    }
  }
  
  /**
   * Create a new conversation
   */
  createConversation(title = '', messages = [], options = {}) {
    const now = new Date().toISOString();
    const conversation = {
      id: `conversation-${Date.now()}`,
      title: title || `Conversation ${new Date().toLocaleString()}`,
      messages: messages,
      created: now,
      lastUpdated: now,
      pinned: options.pinned || false,
      tags: options.tags || [],
      expireAt: options.neverExpire ? null : this.getExpiryDate(options.expiryDays),
    };
    
    // Store the conversation based on context
    if (options.projectId) {
      // Project-specific conversation
      if (!this.conversations.projects[options.projectId]) {
        this.conversations.projects[options.projectId] = [];
      }
      this.conversations.projects[options.projectId].push(conversation);
    } else if (options.agentId) {
      // Agent-specific conversation
      if (!this.conversations.agents[options.agentId]) {
        this.conversations.agents[options.agentId] = [];
      }
      this.conversations.agents[options.agentId].push(conversation);
    } else {
      // General conversation
      this.conversations.general.push(conversation);
    }
    
    this.saveConversations();
    this.renderConversationList();
    
    return conversation.id;
  }
  
  /**
   * Update an existing conversation
   */
  updateConversation(conversationId, updates = {}) {
    const result = this.findConversationById(conversationId);
    if (!result) return false;
    
    const { conversation } = result;
    
    // Update fields
    if (updates.title) conversation.title = updates.title;
    if (updates.messages) conversation.messages = updates.messages;
    if (updates.hasOwnProperty('pinned')) conversation.pinned = updates.pinned;
    if (updates.tags) conversation.tags = updates.tags;
    
    // Always update the lastUpdated timestamp
    conversation.lastUpdated = new Date().toISOString();
    
    this.saveConversations();
    this.renderConversationList();
    
    return true;
  }
  
  /**
   * Add a message to a conversation
   */
  addMessageToConversation(conversationId, message) {
    const result = this.findConversationById(conversationId);
    if (!result) return false;
    
    const { conversation } = result;
    
    // Add the message
    conversation.messages.push(message);
    
    // Update the lastUpdated timestamp
    conversation.lastUpdated = new Date().toISOString();
    
    // If this is a new conversation with just a few messages, update the title based on concept
    if (conversation.messages.length <= 5 && window.ConceptExtractor) {
      const conceptTitle = window.ConceptExtractor.extractConcept(conversation.messages);
      if (conceptTitle && conceptTitle !== 'New Conversation') {
        conversation.title = conceptTitle;
      }
    }
    
    // Update the summary
    conversation.summary = this.generateSummary(conversation.messages);
    
    this.saveConversations();
    this.renderConversationList();
    
    // Update in the options ring if available
    this.updateInOptionsRing(conversation);
    
    return true;
  }
  
  /**
   * Get the current active conversation ID or create a new one
   */
  getActiveConversationId() {
    // Check if there's an active conversation in the window object
    if (window.activeConversationId) {
      const result = this.findConversationById(window.activeConversationId);
      if (result) {
        return window.activeConversationId;
      }
    }
    
    // Create a new conversation
    const options = {};
    if (this.activeProject) {
      options.projectId = this.activeProject;
    } else if (this.activeAgent) {
      options.agentId = this.activeAgent;
    }
    
    const newId = this.createConversation('', [], options);
    window.activeConversationId = newId;
    return newId;
  }
  
  /**
   * Clean up expired conversations
   */
  cleanupExpiredConversations() {
    const now = new Date();
    
    // Function to filter out expired conversations
    const filterExpired = conversation => {
      if (conversation.pinned) return true; // Never expire pinned conversations
      if (!conversation.expireAt) return true; // No expiry date set
      
      return new Date(conversation.expireAt) > now;
    };
    
    // Clean up general conversations
    this.conversations.general = this.conversations.general.filter(filterExpired);
    
    // Clean up project-specific conversations
    for (const projectId in this.conversations.projects) {
      this.conversations.projects[projectId] = this.conversations.projects[projectId].filter(filterExpired);
    }
    
    // Clean up agent-specific conversations
    for (const agentId in this.conversations.agents) {
      this.conversations.agents[agentId] = this.conversations.agents[agentId].filter(filterExpired);
    }
    
    this.saveConversations();
    this.renderConversationList();
  }
  
  /**
   * Calculate expiry date based on days to expire
   */
  getExpiryDate(days = null) {
    const expiryDays = days || this.defaultExpiryDays;
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + expiryDays);
    return expiryDate.toISOString();
  }
  
  /**
   * Show a toast notification
   */
  showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `minerva-toast ${type}`;
    toast.innerHTML = message;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
      toast.classList.add('show');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        document.body.removeChild(toast);
      }, 300);
    }, 3000);
  }
  
  /**
   * Generate a brief summary of a conversation
   * @param {Array} messages - Array of conversation messages
   * @returns {String} - Brief summary
   */
  generateSummary(messages) {
    if (!messages || messages.length === 0) {
      return 'Empty conversation';
    }
    
    // Take first user message as a summary
    const firstUserMsg = messages.find(msg => msg.role === 'user');
    if (firstUserMsg) {
      // Truncate if needed
      const text = firstUserMsg.content;
      if (text.length > 100) {
        return text.substring(0, 97) + '...';
      }
      return text;
    }
    
    return 'Conversation with ' + messages.length + ' messages';
  }
  
  /**
   * Add a conversation to the dashboard options ring if available
   * @param {Object} conversation - Conversation to add
   */
  addToOptionsRing(conversation) {
    // Check if the dashboard interface exists
    if (window.dashboard && typeof window.dashboard.addConversationToRing === 'function') {
      window.dashboard.addConversationToRing(conversation);
    } else if (window.updateConversationsInOptionsRing) {
      // Fallback to using the global function if available
      window.updateConversationsInOptionsRing();
    }
  }
  
  /**
   * Update a conversation in the dashboard options ring
   * @param {Object} conversation - Conversation to update
   */
  updateInOptionsRing(conversation) {
    // Check if the dashboard interface exists
    if (window.dashboard && typeof window.dashboard.updateConversationInRing === 'function') {
      window.dashboard.updateConversationInRing(conversation);
    } else if (window.updateConversationsInOptionsRing) {
      // Fallback to using the global function if available
      window.updateConversationsInOptionsRing();
    }
  }
  
  /**
   * Convert a conversation to a project
   * @param {String} conversationId - ID of conversation to convert
   * @returns {String|null} - New project ID or null if conversion failed
   */
  convertToProject(conversationId) {
    const result = this.findConversationById(conversationId);
    if (!result) return null;
    
    const { conversation } = result;
    
    // Generate a project ID
    const projectId = `project-${Date.now()}`;
    
    // Create project data
    const projectData = {
      id: projectId,
      name: conversation.title,
      description: this.generateSummary(conversation.messages),
      created: new Date().toISOString(),
      lastModified: new Date().toISOString(),
      conversations: [conversationId],
      sourceConversation: conversationId,
      tags: [...(conversation.tags || []), 'auto-converted']
    };
    
    // Check if we have a project manager to handle this
    if (window.projectManager && typeof window.projectManager.createProject === 'function') {
      // Use the project manager to create the project
      const success = window.projectManager.createProject(projectData);
      if (success) {
        // Link the conversation to this project
        conversation.project = projectId;
        conversation.convertedToProject = true;
        this.saveConversations();
        return projectId;
      }
    } else {
      // Fallback: Store the project in localStorage
      try {
        const projects = JSON.parse(localStorage.getItem('minerva_projects') || '[]');
        projects.push(projectData);
        localStorage.setItem('minerva_projects', JSON.stringify(projects));
        
        // Link the conversation to this project
        conversation.project = projectId;
        conversation.convertedToProject = true;
        this.saveConversations();
        
        console.log(`Conversation ${conversationId} converted to project ${projectId}`);
        return projectId;
      } catch (e) {
        console.error('Failed to convert conversation to project:', e);
      }
    }
    
    return null;
  }
  
  /**
   * Assign a conversation to an existing project (for Project Intelligence Layer)
   * @param {String} conversationId - ID of conversation to assign
   * @param {String} projectId - ID of project to assign to
   * @returns {Boolean} - Success status
   */
  assignConversationToProject(conversationId, projectId) {
    // Find the conversation first
    const result = this.findConversationById(conversationId);
    if (!result) {
      console.error(`Conversation ${conversationId} not found`);
      return false;
    }
    
    const { conversation, type, projectId: currentProjectId } = result;
    
    // If already assigned to this project, nothing to do
    if (conversation.project === projectId) {
      return true;
    }
    
    // If currently in a project collection, remove it
    if (type === 'project' && currentProjectId) {
      this.conversations.projects[currentProjectId] = 
        this.conversations.projects[currentProjectId].filter(c => c.id !== conversationId);
      
      // If the project array is now empty, create it
      if (!this.conversations.projects[currentProjectId]) {
        this.conversations.projects[currentProjectId] = [];
      }
    }
    
    // If projects collection doesn't exist for the new project yet, create it
    if (!this.conversations.projects[projectId]) {
      this.conversations.projects[projectId] = [];
    }
    
    // Set project reference on the conversation
    conversation.project = projectId;
    conversation.lastModified = new Date().toISOString();
    
    // Add the conversation to the project's collection if not already there
    if (!this.conversations.projects[projectId].some(c => c.id === conversationId)) {
      this.conversations.projects[projectId].push(conversation);
    }
    
    // If the conversation was in the general collection, remove it
    if (type === 'general') {
      this.conversations.general = this.conversations.general.filter(c => c.id !== conversationId);
    }
    
    // Save changes
    this.saveConversations();
    
    // Update UI
    this.renderConversationList();
    
    // Emit event for other components
    const event = new CustomEvent('minerva:conversation:assigned', {
      detail: {
        conversationId,
        projectId,
        conversation
      }
    });
    document.dispatchEvent(event);
    
    console.log(`Conversation ${conversationId} assigned to project ${projectId}`);
    return true;
  }
}

// Export for use in other files
if (typeof window !== 'undefined') {
  window.MinervaConversationManager = MinervaConversationManager;
}
