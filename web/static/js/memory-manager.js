/**
 * Minerva Memory Management System
 * Handles permanent memory storage and retrieval distinct from conversations
 */

class MinervaMemoryManager {
  constructor(options = {}) {
    // Core settings
    this.container = options.container || document.getElementById('memory-manager-container');
    this.storageKey = 'minerva_memories';
    this.activeProject = options.activeProject || null;
    
    // Initialize memory storage
    this.memories = this.loadMemories();
    
    // DOM elements created dynamically
    this.panel = null;
    this.memoryList = null;
    this.searchInput = null;
    this.addMemoryBtn = null;
    
    // Initialize the UI
    this.initializeUI();
  }
  
  /**
   * Load saved memories from localStorage
   */
  loadMemories() {
    const savedMemories = localStorage.getItem(this.storageKey);
    if (savedMemories) {
      try {
        return JSON.parse(savedMemories);
      } catch (e) {
        console.error('Failed to parse saved memories:', e);
      }
    }
    
    // Default empty memory structure
    return {
      global: [],           // Global memories available everywhere
      projects: {},         // Project-specific memories
      agents: {}            // Agent-specific memories
    };
  }
  
  /**
   * Save memories to localStorage
   */
  saveMemories() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.memories));
  }
  
  /**
   * Initialize the Memory Management UI
   */
  initializeUI() {
    if (!this.container) {
      console.warn('Memory manager container not found. Memory UI will not be created.');
      return;
    }
    
    // Create the main panel
    this.panel = document.createElement('div');
    this.panel.className = 'memory-panel';
    this.panel.innerHTML = `
      <div class="memory-header">
        <h3>Memory Management</h3>
        <div class="memory-search-container">
          <input type="text" id="memory-search" placeholder="Search memories..." />
          <select id="memory-filter">
            <option value="all">All</option>
            <option value="global">Global</option>
            <option value="project">Project</option>
            <option value="agent">Agent</option>
          </select>
        </div>
        <button id="add-memory-btn" class="action-button">+ New Memory</button>
      </div>
      <div class="memory-tabs">
        <button class="memory-tab active" data-tab="all">All Memories</button>
        <button class="memory-tab" data-tab="global">Global</button>
        <button class="memory-tab" data-tab="project">Project</button>
        <button class="memory-tab" data-tab="agent">Agent</button>
      </div>
      <div class="memory-list"></div>
    `;
    
    this.container.appendChild(this.panel);
    
    // Get references to UI elements
    this.memoryList = this.panel.querySelector('.memory-list');
    this.searchInput = this.panel.querySelector('#memory-search');
    this.addMemoryBtn = this.panel.querySelector('#add-memory-btn');
    this.tabs = this.panel.querySelectorAll('.memory-tab');
    
    // Add event listeners
    this.searchInput.addEventListener('input', () => this.filterMemories());
    this.addMemoryBtn.addEventListener('click', () => this.showAddMemoryForm());
    
    // Set up tab switching
    this.tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.tabs.forEach(t => t.classList.remove('active'));
        e.target.classList.add('active');
        this.activeTab = e.target.dataset.tab;
        this.renderMemoryList();
      });
    });
    
    // Initial render
    this.renderMemoryList();
  }
  
  /**
   * Render the memory list based on current filters
   */
  renderMemoryList() {
    if (!this.memoryList) return;
    
    const searchTerm = this.searchInput ? this.searchInput.value.toLowerCase() : '';
    const activeTab = this.activeTab || 'all';
    
    // Clear current list
    this.memoryList.innerHTML = '';
    
    let visibleMemories = [];
    
    // Collect memories based on active tab
    if (activeTab === 'all' || activeTab === 'global') {
      visibleMemories = visibleMemories.concat(this.memories.global.map(m => ({...m, type: 'global'})));
    }
    
    if (activeTab === 'all' || activeTab === 'project') {
      for (const projectId in this.memories.projects) {
        visibleMemories = visibleMemories.concat(
          this.memories.projects[projectId].map(m => ({...m, type: 'project', projectId}))
        );
      }
    }
    
    if (activeTab === 'all' || activeTab === 'agent') {
      for (const agentId in this.memories.agents) {
        visibleMemories = visibleMemories.concat(
          this.memories.agents[agentId].map(m => ({...m, type: 'agent', agentId}))
        );
      }
    }
    
    // Apply search filter
    if (searchTerm) {
      visibleMemories = visibleMemories.filter(memory => 
        memory.content.toLowerCase().includes(searchTerm) || 
        memory.title.toLowerCase().includes(searchTerm) ||
        (memory.tags && memory.tags.some(tag => tag.toLowerCase().includes(searchTerm)))
      );
    }
    
    // Sort by modified date descending
    visibleMemories.sort((a, b) => new Date(b.modified) - new Date(a.modified));
    
    // Render each memory
    visibleMemories.forEach(memory => {
      const memoryItem = document.createElement('div');
      memoryItem.className = `memory-item memory-${memory.type}`;
      memoryItem.dataset.id = memory.id;
      
      // Format the date
      const created = new Date(memory.created);
      const formattedDate = created.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric', 
        year: 'numeric'
      });
      
      // Build the HTML
      memoryItem.innerHTML = `
        <div class="memory-item-header">
          <h4>${memory.title}</h4>
          <div class="memory-badges">
            <span class="memory-type-badge">${memory.type}</span>
            ${memory.projectId ? `<span class="memory-project-badge">${memory.projectId}</span>` : ''}
            ${memory.agentId ? `<span class="memory-agent-badge">${memory.agentId}</span>` : ''}
          </div>
        </div>
        <div class="memory-content">${memory.content}</div>
        <div class="memory-footer">
          <div class="memory-date">Created: ${formattedDate}</div>
          <div class="memory-actions">
            <button class="edit-memory" data-id="${memory.id}">Edit</button>
            <button class="delete-memory" data-id="${memory.id}">Delete</button>
          </div>
        </div>
      `;
      
      // Add event listeners for actions
      memoryItem.querySelector('.edit-memory').addEventListener('click', () => 
        this.editMemory(memory.id)
      );
      
      memoryItem.querySelector('.delete-memory').addEventListener('click', () => 
        this.deleteMemory(memory.id)
      );
      
      this.memoryList.appendChild(memoryItem);
    });
    
    // Show empty state if no memories
    if (visibleMemories.length === 0) {
      this.memoryList.innerHTML = `
        <div class="empty-state">
          <p>No memories found. ${searchTerm ? 'Try a different search term.' : 'Add your first memory to help Minerva remember important information.'}</p>
        </div>
      `;
    }
  }
  
  /**
   * Show the form to add a new memory
   */
  showAddMemoryForm(existingMemory = null) {
    // Create the modal form
    const modal = document.createElement('div');
    modal.className = 'memory-modal';
    
    const isEditing = existingMemory !== null;
    const title = isEditing ? existingMemory.title : '';
    const content = isEditing ? existingMemory.content : '';
    const tags = isEditing && existingMemory.tags ? existingMemory.tags.join(', ') : '';
    const type = isEditing ? existingMemory.type : 'global';
    const projectId = isEditing ? existingMemory.projectId : this.activeProject;
    
    modal.innerHTML = `
      <div class="memory-modal-content">
        <div class="memory-modal-header">
          <h3>${isEditing ? 'Edit' : 'Add'} Memory</h3>
          <button class="close-modal">&times;</button>
        </div>
        <div class="memory-modal-body">
          <form id="memory-form">
            <div class="form-group">
              <label for="memory-title">Title</label>
              <input type="text" id="memory-title" value="${title}" required>
            </div>
            <div class="form-group">
              <label for="memory-content">Content</label>
              <textarea id="memory-content" rows="5" required>${content}</textarea>
            </div>
            <div class="form-group">
              <label for="memory-tags">Tags (comma-separated)</label>
              <input type="text" id="memory-tags" value="${tags}">
            </div>
            <div class="form-group">
              <label for="memory-type">Memory Type</label>
              <select id="memory-type">
                <option value="global" ${type === 'global' ? 'selected' : ''}>Global (available everywhere)</option>
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
                ${this.getAgentOptions(existingMemory?.agentId)}
              </select>
            </div>
          </form>
        </div>
        <div class="memory-modal-footer">
          <button class="cancel-memory">Cancel</button>
          <button class="save-memory">${isEditing ? 'Update' : 'Save'} Memory</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listeners
    modal.querySelector('.close-modal').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    modal.querySelector('.cancel-memory').addEventListener('click', () => {
      document.body.removeChild(modal);
    });
    
    // Show/hide project selector based on type
    const typeSelect = modal.querySelector('#memory-type');
    const projectSelector = modal.querySelector('.project-selector');
    const agentSelector = modal.querySelector('.agent-selector');
    
    typeSelect.addEventListener('change', () => {
      projectSelector.style.display = typeSelect.value === 'project' ? 'block' : 'none';
      agentSelector.style.display = typeSelect.value === 'agent' ? 'block' : 'none';
    });
    
    // Handle form submission
    modal.querySelector('.save-memory').addEventListener('click', () => {
      const titleInput = modal.querySelector('#memory-title');
      const contentInput = modal.querySelector('#memory-content');
      const tagsInput = modal.querySelector('#memory-tags');
      const typeSelect = modal.querySelector('#memory-type');
      const projectSelect = modal.querySelector('#memory-project');
      const agentSelect = modal.querySelector('#memory-agent');
      
      // Validate form
      if (!titleInput.value.trim() || !contentInput.value.trim()) {
        alert('Please fill in all required fields.');
        return;
      }
      
      // Create memory object
      const memoryData = {
        id: isEditing ? existingMemory.id : `memory-${Date.now()}`,
        title: titleInput.value.trim(),
        content: contentInput.value.trim(),
        tags: tagsInput.value.split(',').map(tag => tag.trim()).filter(tag => tag),
        created: isEditing ? existingMemory.created : new Date().toISOString(),
        modified: new Date().toISOString()
      };
      
      if (isEditing) {
        this.updateMemory(memoryData, typeSelect.value, 
          typeSelect.value === 'project' ? projectSelect.value : null,
          typeSelect.value === 'agent' ? agentSelect.value : null
        );
      } else {
        this.addMemory(memoryData, typeSelect.value, 
          typeSelect.value === 'project' ? projectSelect.value : null,
          typeSelect.value === 'agent' ? agentSelect.value : null
        );
      }
      
      document.body.removeChild(modal);
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
   * Add a new memory
   */
  addMemory(memoryData, type = 'global', projectId = null, agentId = null) {
    if (type === 'global') {
      this.memories.global.push(memoryData);
    } else if (type === 'project' && projectId) {
      if (!this.memories.projects[projectId]) {
        this.memories.projects[projectId] = [];
      }
      this.memories.projects[projectId].push(memoryData);
    } else if (type === 'agent' && agentId) {
      if (!this.memories.agents[agentId]) {
        this.memories.agents[agentId] = [];
      }
      this.memories.agents[agentId].push(memoryData);
    }
    
    this.saveMemories();
    this.renderMemoryList();
  }
  
  /**
   * Update an existing memory
   */
  updateMemory(memoryData, type = 'global', projectId = null, agentId = null) {
    // First, find and remove the old memory (could be in any section)
    this.deleteMemory(memoryData.id, false);
    
    // Then add it to the new section
    if (type === 'global') {
      this.memories.global.push(memoryData);
    } else if (type === 'project' && projectId) {
      if (!this.memories.projects[projectId]) {
        this.memories.projects[projectId] = [];
      }
      this.memories.projects[projectId].push(memoryData);
    } else if (type === 'agent' && agentId) {
      if (!this.memories.agents[agentId]) {
        this.memories.agents[agentId] = [];
      }
      this.memories.agents[agentId].push(memoryData);
    }
    
    this.saveMemories();
    this.renderMemoryList();
  }
  
  /**
   * Edit an existing memory
   */
  editMemory(memoryId) {
    // Find the memory
    let memory = null;
    let type = '';
    let projectId = null;
    let agentId = null;
    
    // Search in global memories
    memory = this.memories.global.find(m => m.id === memoryId);
    if (memory) {
      type = 'global';
    }
    
    // Search in project memories
    if (!memory) {
      for (const pid in this.memories.projects) {
        const found = this.memories.projects[pid].find(m => m.id === memoryId);
        if (found) {
          memory = found;
          type = 'project';
          projectId = pid;
          break;
        }
      }
    }
    
    // Search in agent memories
    if (!memory) {
      for (const aid in this.memories.agents) {
        const found = this.memories.agents[aid].find(m => m.id === memoryId);
        if (found) {
          memory = found;
          type = 'agent';
          agentId = aid;
          break;
        }
      }
    }
    
    if (memory) {
      this.showAddMemoryForm({
        ...memory,
        type,
        projectId,
        agentId
      });
    }
  }
  
  /**
   * Delete a memory
   */
  deleteMemory(memoryId, shouldRender = true) {
    // Look for the memory in all sections and remove it
    // Global memories
    const globalIndex = this.memories.global.findIndex(m => m.id === memoryId);
    if (globalIndex !== -1) {
      this.memories.global.splice(globalIndex, 1);
    }
    
    // Project memories
    for (const projectId in this.memories.projects) {
      const projectIndex = this.memories.projects[projectId].findIndex(m => m.id === memoryId);
      if (projectIndex !== -1) {
        this.memories.projects[projectId].splice(projectIndex, 1);
      }
    }
    
    // Agent memories
    for (const agentId in this.memories.agents) {
      const agentIndex = this.memories.agents[agentId].findIndex(m => m.id === memoryId);
      if (agentIndex !== -1) {
        this.memories.agents[agentId].splice(agentIndex, 1);
      }
    }
    
    this.saveMemories();
    if (shouldRender) {
      this.renderMemoryList();
    }
  }
  
  /**
   * Convert a conversation to a memory
   * @param {Array} conversation - Array of conversation messages
   * @param {String} title - Title for the memory
   * @param {String} type - Memory type (global, project, agent)
   * @param {String} associatedId - Project ID or Agent ID if applicable
   */
  saveConversationAsMemory(conversation, title, type = 'global', associatedId = null) {
    if (!conversation || !conversation.length) return;
    
    // Format the conversation to display nicely
    const formattedContent = conversation.map(msg => {
      const role = msg.role.charAt(0).toUpperCase() + msg.role.slice(1);
      return `${role}: ${msg.content}`;
    }).join('\n\n');
    
    // Create memory object
    const memoryData = {
      id: `memory-${Date.now()}`,
      title: title || `Conversation from ${new Date().toLocaleDateString()}`,
      content: formattedContent,
      tags: ['conversation'],
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      source: 'conversation',
      conversationId: conversation[0]?.conversationId
    };
    
    // Add to appropriate section
    if (type === 'project' && associatedId) {
      if (!this.memories.projects[associatedId]) {
        this.memories.projects[associatedId] = [];
      }
      this.memories.projects[associatedId].push(memoryData);
    } else if (type === 'agent' && associatedId) {
      if (!this.memories.agents[associatedId]) {
        this.memories.agents[associatedId] = [];
      }
      this.memories.agents[associatedId].push(memoryData);
    } else {
      this.memories.global.push(memoryData);
    }
    
    this.saveMemories();
    return memoryData.id;
  }
  
  /**
   * Get memories that might be relevant to the current context
   * @param {Object} context - Context object with project, agent, etc.
   * @param {String} query - Optional search query to filter memories
   * @returns {Array} Relevant memories
   */
  getRelevantMemories(context = {}, query = '') {
    const relevant = [];
    const { projectId, agentId } = context;
    
    // Always include global memories
    relevant.push(...this.memories.global);
    
    // Include project-specific memories if a project is active
    if (projectId && this.memories.projects[projectId]) {
      relevant.push(...this.memories.projects[projectId]);
    }
    
    // Include agent-specific memories if an agent is active
    if (agentId && this.memories.agents[agentId]) {
      relevant.push(...this.memories.agents[agentId]);
    }
    
    // Filter by query if provided
    if (query) {
      return relevant.filter(memory => 
        memory.content.toLowerCase().includes(query.toLowerCase()) || 
        memory.title.toLowerCase().includes(query.toLowerCase()) ||
        (memory.tags && memory.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase())))
      );
    }
    
    return relevant;
  }
  
  /**
   * Process memory updates from Think Tank responses
   * @param {Array|Object} memoryUpdates - Memory updates from server
   */
  processMemoryUpdates(memoryUpdates) {
    if (!memoryUpdates) return;
    
    console.log('Memory Manager: Processing memory updates', 
      Array.isArray(memoryUpdates) ? `Array with ${memoryUpdates.length} items` : 'Single object');
    
    // Handle array format
    if (Array.isArray(memoryUpdates)) {
      memoryUpdates.forEach(memory => this.processSingleMemoryUpdate(memory));
    } 
    // Handle object format
    else if (typeof memoryUpdates === 'object') {
      this.processSingleMemoryUpdate(memoryUpdates);
    }
    
    // Save updated memories
    this.saveMemories();
    
    // Refresh the UI
    this.renderMemoryList();
    
    // Dispatch event for memory updates
    document.dispatchEvent(new CustomEvent('minerva-memories-updated', { 
      detail: { source: 'think-tank', count: Array.isArray(memoryUpdates) ? memoryUpdates.length : 1 }
    }));
    
    return Array.isArray(memoryUpdates) ? memoryUpdates.length : 1;
  }
  
  /**
   * Process a single memory update
   * @param {Object} memory - Single memory to process
   */
  processSingleMemoryUpdate(memory) {
    if (!memory || !memory.content) return;
    
    // Determine memory type and target collection
    let targetCollection;
    let targetKey = null;
    
    if (memory.type === 'global' || !memory.type) {
      targetCollection = this.memories.global;
    } else if (memory.type === 'project' && memory.projectId) {
      // Initialize project memories if needed
      if (!this.memories.projects[memory.projectId]) {
        this.memories.projects[memory.projectId] = [];
      }
      targetCollection = this.memories.projects[memory.projectId];
      targetKey = memory.projectId;
    } else if (memory.type === 'agent' && memory.agentId) {
      // Initialize agent memories if needed
      if (!this.memories.agents[memory.agentId]) {
        this.memories.agents[memory.agentId] = [];
      }
      targetCollection = this.memories.agents[memory.agentId];
      targetKey = memory.agentId;
    } else {
      // Default to global if no valid type
      targetCollection = this.memories.global;
    }
    
    // Check if memory already exists (by id or similar content)
    const existingIndex = targetCollection.findIndex(m => 
      (m.id && m.id === memory.id) || 
      (m.content && m.content.trim() === memory.content.trim())
    );
    
    if (existingIndex >= 0) {
      // Update existing memory
      targetCollection[existingIndex] = {
        ...targetCollection[existingIndex],
        ...memory,
        updated: new Date().toISOString()
      };
    } else {
      // Add new memory
      targetCollection.push({
        id: memory.id || 'mem_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9),
        title: memory.title || 'Untitled Memory',
        content: memory.content,
        tags: memory.tags || [],
        created: new Date().toISOString(),
        updated: new Date().toISOString(),
        importance: memory.importance || 3
      });
    }
  }
}

// Export for use in other files
if (typeof window !== 'undefined') {
  window.MinervaMemoryManager = MinervaMemoryManager;
}
