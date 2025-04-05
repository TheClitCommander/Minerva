/**
 * Minerva Chat Core System
 * A unified chat interface that works across all Minerva UIs
 * Includes conversation memory and project management
 */

class MinervaChat {
  constructor(options = {}) {
    // Core settings
    this.container = options.container || document.getElementById('chat-messages');
    this.inputField = options.inputField || document.getElementById('chat-input');
    this.sendButton = options.sendButton || document.getElementById('chat-send-button');
    
    // API endpoints
    this.thinkTankEndpoint = options.thinkTankEndpoint || 'http://localhost:7070/api/think-tank';
    this.chatBackupEndpoint = options.chatBackupEndpoint || '/api/think-tank-mock';
    this.memoryEndpoint = options.memoryEndpoint || '/api/memory';
    
    // State
    this.conversationId = localStorage.getItem('minerva_conversation_id') || ('conv-' + Date.now());
    this.activeProject = options.activeProject || localStorage.getItem('minerva_active_project') || 'general';
    this.useMemory = options.useMemory !== undefined ? options.useMemory : true;
    this.DEBUG_MODE = options.debug || false;
    
    // Initialize memory if not exists
    if (!window.minervaMemory) {
      window.minervaMemory = [];
    }
    
    // Initialize projects if not exists
    if (!window.minervaProjects) {
      window.minervaProjects = {
        general: { name: 'General Conversation', conversations: [] }
      };
      localStorage.setItem('minervaProjects', JSON.stringify(window.minervaProjects));
    }
    
    // Bind methods
    this.sendMessage = this.sendMessage.bind(this);
    this.displayMessage = this.displayMessage.bind(this);
    this.addTypingIndicator = this.addTypingIndicator.bind(this);
    this.removeTypingIndicator = this.removeTypingIndicator.bind(this);
    
    // Set up event listeners if elements are available
    this.setupEventListeners();
    
    // Log initialization
    console.log('MinervaChat initialized with:', {
      project: this.activeProject,
      memory: this.useMemory ? 'enabled' : 'disabled',
      conversationId: this.conversationId
    });
  }
  
  setupEventListeners() {
    if (this.sendButton) {
      this.sendButton.addEventListener('click', () => {
        const message = this.inputField.value.trim();
        if (message) {
          this.sendMessage(message);
          this.inputField.value = '';
        }
      });
    }
    
    if (this.inputField) {
      this.inputField.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          const message = this.inputField.value.trim();
          if (message) {
            this.sendMessage(message);
            this.inputField.value = '';
          }
        }
      });
    }
  }
  
  async sendMessage(message) {
    // Don't send empty messages
    if (!message || !message.trim()) return;
    
    // Display user message immediately
    this.displayMessage(message, 'user');
    
    // Add to memory
    window.minervaMemory.push({
      role: 'user',
      content: message,
      project: this.activeProject,
      timestamp: new Date().toISOString()
    });
    
    // Show typing indicator
    const typingIndicator = this.addTypingIndicator();
    
    try {
      // Prepare request data
      const requestData = {
        message: message,
        conversation_id: this.conversationId,
        project: this.activeProject,
        conversation_history: this.useMemory ? window.minervaMemory : [],
        use_memory: this.useMemory,
        client_version: '1.0.2'
      };
      
      if (this.DEBUG_MODE) {
        console.log('Sending to Think Tank:', requestData);
      }
      
      // First try the Think Tank endpoint with improved error handling
      let response;
      try {
        console.log(`Connecting to Think Tank API at ${this.thinkTankEndpoint}`);
        response = await fetch(this.thinkTankEndpoint, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          mode: 'cors',  // Enable CORS for cross-domain requests
          body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
          throw new Error(`Think Tank API error: ${response.status}`);
        }
        
        // Log successful connection
        console.log('Successfully connected to Think Tank API');
      } catch (error) {
        console.warn('Think Tank API failed, trying backup endpoint:', error);
        
        try {
          // Try fallback endpoint with mock data
          response = await fetch(this.chatBackupEndpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              message: message,
              conversation_id: this.conversationId,
              conversation_history: window.minervaMemory.slice(-10) // Last 10 messages only
            })
          });
          
          if (!response.ok) {
            throw new Error(`Backup API error: ${response.status}`);
          }
        } catch (backupError) {
          // All API attempts failed, create a simple response
          console.error('All API attempts failed, using local fallback', backupError);
          
          // Create a fallback response object
          return {
            response: "I'm sorry, I'm having trouble connecting to the Think Tank right now. Please try again later.",
            conversation_id: this.conversationId,
            error: true
          };
        }
      }
      
      // Process the response
      const data = await response.json();
      
      // Remove typing indicator
      this.removeTypingIndicator(typingIndicator);
      
      // Get the response text
      const responseText = data.response || data.text || data.message || "I couldn't generate a response.";
      
      // Add model info if available
      const modelInfo = data.model_info || data.models_used || null;
      
      // Display the response
      this.displayMessage(responseText, 'assistant', modelInfo);
      
      // Add to memory
      window.minervaMemory.push({
        role: 'assistant',
        content: responseText,
        project: this.activeProject,
        timestamp: new Date().toISOString(),
        model_info: modelInfo
      });
      
      // Update project conversation
      if (window.minervaProjects[this.activeProject]) {
        window.minervaProjects[this.activeProject].conversations = [...window.minervaMemory];
        localStorage.setItem('minervaProjects', JSON.stringify(window.minervaProjects));
      }
      
      return responseText;
    } catch (error) {
      console.error('Error in chat processing:', error);
      
      // Remove typing indicator
      this.removeTypingIndicator(typingIndicator);
      
      // Show error message
      this.displayMessage(
        "I'm having trouble connecting to the server. Your message was saved locally.", 
        'system'
      );
      
      return null;
    }
  }
  
  displayMessage(text, sender, modelInfo = null) {
    if (!this.container) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `${sender}-message`;
    messageElement.textContent = text;
    
    // Add model info for assistant messages
    if (sender === 'assistant' && modelInfo) {
      const modelIndicator = document.createElement('div');
      modelIndicator.className = 'model-indicator';
      
      let modelText = '';
      if (typeof modelInfo === 'string') {
        modelText = modelInfo;
      } else if (Array.isArray(modelInfo)) {
        modelText = modelInfo.join(', ');
      } else if (typeof modelInfo === 'object') {
        modelText = Object.keys(modelInfo).join(', ');
      }
      
      modelIndicator.innerHTML = `<span class="model-badge" title="Models used for this response">${modelText}</span>`;
      messageElement.appendChild(modelIndicator);
    }
    
    // Add to chat container
    this.container.appendChild(messageElement);
    
    // Scroll to bottom
    this.container.scrollTop = this.container.scrollHeight;
  }
  
  addTypingIndicator() {
    if (!this.container) return null;
    
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    this.container.appendChild(typingIndicator);
    this.container.scrollTop = this.container.scrollHeight;
    
    return typingIndicator;
  }
  
  removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
      indicator.parentNode.removeChild(indicator);
    }
  }
  
  // Project management functionality
  switchProject(projectId) {
    if (projectId && window.minervaProjects[projectId]) {
      this.activeProject = projectId;
      localStorage.setItem('minerva_active_project', projectId);
      
      // Clear current memory and load project memory
      window.minervaMemory = [...(window.minervaProjects[projectId].conversations || [])];
      
      // Clear chat display
      if (this.container) {
        this.container.innerHTML = '';
        
        // Add welcome message for project
        this.displayMessage(
          `Switched to project: ${window.minervaProjects[projectId].name}. How can I help with this project?`,
          'system'
        );
      }
      
      console.log(`Switched to project: ${projectId}`);
      return true;
    }
    return false;
  }
  
  createProject(projectName) {
    if (!projectName) return null;
    
    const projectId = 'proj-' + Date.now();
    window.minervaProjects[projectId] = {
      name: projectName,
      conversations: [...window.minervaMemory], // Copy current conversation
      created: new Date().toISOString()
    };
    
    // Save to local storage
    localStorage.setItem('minervaProjects', JSON.stringify(window.minervaProjects));
    
    // Switch to new project
    this.switchProject(projectId);
    
    return projectId;
  }
  
  // Conversation memory management
  clearMemory() {
    window.minervaMemory = [];
    return true;
  }
  
  getMemory() {
    return window.minervaMemory;
  }
  
  getProjects() {
    return window.minervaProjects;
  }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MinervaChat };
}
