/**
 * Minerva Floating Chat Component
 * Adds a transparent, draggable chat interface that can be embedded in any page
 * Maintains conversation persistence across the Minerva application
 * Integrates with Minerva orb for a seamless user experience
 */

class FloatingChatComponent {
  constructor(options = {}) {
    // Chat configuration
    this.options = {
      containerId: options.containerId || 'floating-chat-container',
      title: options.title || 'Minerva Assistant',
      placeholder: options.placeholder || 'Ask me anything...',
      position: options.position || { bottom: '20px', right: '20px' },
      initiallyVisible: options.initiallyVisible !== undefined ? options.initiallyVisible : true,
      width: options.width || '350px',
      height: options.height || 'auto',
      maxHeight: options.maxHeight || '500px',
      transparency: options.transparency || 0.85,
      projectAware: options.projectAware !== undefined ? options.projectAware : true,
      theme: options.theme || 'cosmic',
      alwaysOnTop: options.alwaysOnTop !== undefined ? options.alwaysOnTop : true
    };

    // Element references
    this.container = null;
    this.chatMessages = null;
    this.chatInput = null;
    this.closeButton = null;
    this.minimizeButton = null;
    this.projectSelect = null;
    
    // Chat state
    this.isVisible = this.options.initiallyVisible;
    this.isMinimized = false;
    this.chatInstance = null;
    this.dragOffset = { x: 0, y: 0 };
    this.isDragging = false;
    
    // Initialize
    this.init();
  }
  
  init() {
    // Check if container already exists
    let existingContainer = document.getElementById(this.options.containerId);
    if (existingContainer) {
      console.log('Floating chat container already exists, skipping creation');
      this.container = existingContainer;
      this.bindEvents();
      return;
    }
    
    // Create container
    this.createChatInterface();
    
    // Add to document
    document.body.appendChild(this.container);
    
    // Initialize chat core
    this.initChatCore();
    
    // Bind events
    this.bindEvents();
    
    // Set initial state
    if (!this.isVisible) {
      this.container.style.display = 'none';
    }
    
    console.log('Floating chat component initialized');
  }
  
  createChatInterface() {
    // Create main container
    this.container = document.createElement('div');
    this.container.id = this.options.containerId;
    this.container.className = 'chat-container floating-chat';
    this.container.style.opacity = this.options.transparency;
    this.container.style.backdropFilter = 'blur(8px)';
    this.container.style.width = this.options.width;
    this.container.style.maxHeight = this.options.maxHeight;
    
    // Position the chat
    if (this.options.position.bottom) {
      this.container.style.bottom = this.options.position.bottom;
    }
    if (this.options.position.right) {
      this.container.style.right = this.options.position.right;
    }
    if (this.options.position.top) {
      this.container.style.top = this.options.position.top;
    }
    if (this.options.position.left) {
      this.container.style.left = this.options.position.left;
    }
    
    // Apply theme
    if (this.options.theme === 'cosmic') {
      this.container.classList.add('cosmic-theme');
    }
    
    // Create header
    const header = document.createElement('div');
    header.className = 'chat-header';
    header.innerHTML = `
      <div class="chat-title">${this.options.title}</div>
      <div class="chat-controls">
        <button class="minimize-button"><i class="fas fa-minus"></i></button>
        <button class="close-button"><i class="fas fa-times"></i></button>
      </div>
    `;
    this.container.appendChild(header);
    
    // Add project selector if project-aware
    if (this.options.projectAware) {
      const projectSelectContainer = document.createElement('div');
      projectSelectContainer.className = 'project-select-container';
      projectSelectContainer.innerHTML = `
        <select id="floating-project-select" class="project-select">
          <option value="general">General Conversation</option>
          <option value="create-new">+ Create New Project</option>
        </select>
      `;
      this.container.appendChild(projectSelectContainer);
      this.projectSelect = projectSelectContainer.querySelector('#floating-project-select');
    }
    
    // Create messages container
    this.chatMessages = document.createElement('div');
    this.chatMessages.className = 'chat-messages';
    this.chatMessages.id = 'floating-chat-messages';
    this.container.appendChild(this.chatMessages);
    
    // Create input container
    const inputContainer = document.createElement('div');
    inputContainer.className = 'chat-input-container';
    inputContainer.innerHTML = `
      <input type="text" class="chat-input" id="floating-chat-input" placeholder="${this.options.placeholder}">
      <button class="chat-send-button" id="floating-chat-send-button">
        <i class="fas fa-paper-plane"></i>
      </button>
    `;
    this.container.appendChild(inputContainer);
    
    this.chatInput = inputContainer.querySelector('#floating-chat-input');
    this.sendButton = inputContainer.querySelector('#floating-chat-send-button');
    this.closeButton = header.querySelector('.close-button');
    this.minimizeButton = header.querySelector('.minimize-button');
    
    // Make draggable
    header.style.cursor = 'move';
    this.makeDraggable(header);
  }
  
  initChatCore() {
    // Initialize chat core with our container
    if (typeof MinervaChat !== 'undefined') {
      this.chatInstance = new MinervaChat({
        container: this.chatMessages,
        inputField: this.chatInput,
        sendButton: this.sendButton,
        useMemory: true,
        debug: false
      });
      
      // Add system welcome message
      this.addSystemMessage('How can I help you today?');
    } else {
      console.error('MinervaChat class not found. Make sure chat-core.js is loaded first.');
      this.addSystemMessage('Chat system initializing...');
      
      // Try to load chat core dynamically
      this.loadScript('/static/js/chat/chat-core.js')
        .then(() => {
          if (typeof MinervaChat !== 'undefined') {
            this.chatInstance = new MinervaChat({
              container: this.chatMessages,
              inputField: this.chatInput,
              sendButton: this.sendButton,
              useMemory: true
            });
            this.addSystemMessage('Chat system ready. How can I help you?');
          } else {
            this.addSystemMessage('Could not initialize chat system. Please refresh the page.');
          }
        })
        .catch(err => {
          console.error('Failed to load chat-core.js:', err);
          this.addSystemMessage('Error loading chat system. Please try again later.');
        });
    }
  }
  
  bindEvents() {
    // Close button
    if (this.closeButton) {
      this.closeButton.addEventListener('click', () => {
        this.hide();
      });
    }
    
    // Minimize button
    if (this.minimizeButton) {
      this.minimizeButton.addEventListener('click', () => {
        this.toggleMinimize();
      });
    }
    
    // Project select
    if (this.projectSelect) {
      this.projectSelect.addEventListener('change', (e) => {
        const projectId = e.target.value;
        
        if (projectId === 'create-new') {
          this.showCreateProjectDialog();
          // Reset to current project after showing dialog
          setTimeout(() => {
            this.updateProjectDropdown();
          }, 100);
        } else if (this.chatInstance) {
          this.chatInstance.switchProject(projectId);
        }
      });
      
      // Update project dropdown initially
      this.updateProjectDropdown();
    }
    
    // Chat input keypress
    if (this.chatInput) {
      this.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          if (this.chatInstance) {
            const message = this.chatInput.value.trim();
            if (message) {
              this.chatInstance.sendMessage(message);
              this.chatInput.value = '';
            }
          } else {
            this.addSystemMessage('Chat system is still initializing. Please wait a moment.');
          }
        }
      });
    }
    
    // Send button
    if (this.sendButton) {
      this.sendButton.addEventListener('click', () => {
        if (this.chatInstance) {
          const message = this.chatInput.value.trim();
          if (message) {
            this.chatInstance.sendMessage(message);
            this.chatInput.value = '';
          }
        } else {
          this.addSystemMessage('Chat system is still initializing. Please wait a moment.');
        }
      });
    }
  }
  
  makeDraggable(dragHandle) {
    if (!dragHandle) return;
    
    dragHandle.addEventListener('mousedown', (e) => {
      if (e.target.closest('.close-button') || e.target.closest('.minimize-button')) {
        return; // Don't start drag if clicking on buttons
      }
      
      this.isDragging = true;
      
      // Get initial positions
      const rect = this.container.getBoundingClientRect();
      this.dragOffset.x = e.clientX - rect.left;
      this.dragOffset.y = e.clientY - rect.top;
      
      // Add move and up listeners to document
      document.addEventListener('mousemove', this.handleMouseMove);
      document.addEventListener('mouseup', this.handleMouseUp);
      
      // Prevent text selection during drag
      e.preventDefault();
    });
    
    // Bind methods to this instance
    this.handleMouseMove = this.handleMouseMove.bind(this);
    this.handleMouseUp = this.handleMouseUp.bind(this);
  }
  
  handleMouseMove(e) {
    if (!this.isDragging) return;
    
    // Calculate new position
    const newLeft = e.clientX - this.dragOffset.x;
    const newTop = e.clientY - this.dragOffset.y;
    
    // Update position
    this.container.style.right = 'auto';
    this.container.style.bottom = 'auto';
    this.container.style.left = `${newLeft}px`;
    this.container.style.top = `${newTop}px`;
  }
  
  handleMouseUp() {
    this.isDragging = false;
    
    // Remove move and up listeners
    document.removeEventListener('mousemove', this.handleMouseMove);
    document.removeEventListener('mouseup', this.handleMouseUp);
  }
  
  show() {
    this.container.style.display = 'block';
    this.isVisible = true;
    
    // Un-minimize if minimized
    if (this.isMinimized) {
      this.toggleMinimize();
    }
  }
  
  hide() {
    this.container.style.display = 'none';
    this.isVisible = false;
  }
  
  toggleMinimize() {
    if (this.isMinimized) {
      // Restore
      this.chatMessages.style.display = 'flex';
      this.container.querySelector('.chat-input-container').style.display = 'flex';
      if (this.projectSelect) {
        this.projectSelect.parentElement.style.display = 'block';
      }
      this.container.style.height = this.options.height;
      this.minimizeButton.innerHTML = '<i class="fas fa-minus"></i>';
      this.isMinimized = false;
    } else {
      // Minimize
      this.chatMessages.style.display = 'none';
      this.container.querySelector('.chat-input-container').style.display = 'none';
      if (this.projectSelect) {
        this.projectSelect.parentElement.style.display = 'none';
      }
      this.container.style.height = 'auto';
      this.minimizeButton.innerHTML = '<i class="fas fa-plus"></i>';
      this.isMinimized = true;
    }
  }
  
  addSystemMessage(text) {
    const systemMsg = document.createElement('div');
    systemMsg.className = 'system-message';
    systemMsg.textContent = text;
    
    this.chatMessages.appendChild(systemMsg);
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }
  
  showCreateProjectDialog() {
    const projectName = prompt('Enter a name for the new project:');
    if (projectName && projectName.trim()) {
      if (this.chatInstance) {
        this.chatInstance.createProject(projectName.trim());
        this.updateProjectDropdown();
      } else {
        this.addSystemMessage('Chat system is not initialized. Unable to create project.');
      }
    }
  }
  
  updateProjectDropdown() {
    if (!this.projectSelect) return;
    
    // Get current value
    const currentValue = this.projectSelect.value;
    
    // Clear all options except create-new
    Array.from(this.projectSelect.options)
      .filter(option => option.value !== 'create-new')
      .forEach(option => this.projectSelect.removeChild(option));
    
    // Get projects from memory
    const projects = window.minervaProjects || {
      general: { name: 'General Conversation' }
    };
    
    // Add project options
    const createNewOption = this.projectSelect.querySelector('option[value="create-new"]');
    Object.entries(projects).forEach(([id, project]) => {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = project.name;
      
      // Add before create-new option
      if (createNewOption) {
        this.projectSelect.insertBefore(option, createNewOption);
      } else {
        this.projectSelect.appendChild(option);
      }
    });
    
    // Restore selection or set to active project
    if (this.chatInstance && this.chatInstance.activeProject) {
      this.projectSelect.value = this.chatInstance.activeProject;
    } else if (projects[currentValue]) {
      this.projectSelect.value = currentValue;
    }
  }
  
  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}

// Initialize floating chat when document is ready
document.addEventListener('DOMContentLoaded', function() {
  // Check if we should auto-initialize
  const autoInit = document.querySelector('meta[name="minerva-floating-chat"]');
  if (autoInit && autoInit.getAttribute('content') === 'auto') {
    window.floatingChat = new FloatingChatComponent({
      transparency: 0.85,
      title: 'Minerva Assistant',
      theme: 'cosmic'
    });
  }
  
  // Create global initializer function
  window.initFloatingChat = function(options) {
    window.floatingChat = new FloatingChatComponent(options);
    return window.floatingChat;
  };
  
  // Check if the Minerva Orb is being handled elsewhere (in index.html)
  const orbHandled = document.querySelector('meta[name="minerva-orb-handled"]');
  const minervaOrb = document.getElementById('minerva-portal');
  
  if (minervaOrb) {
    // Only add hover effects, do not add click handler as it's now handled in index.html
    console.log('Minerva Orb chat functionality disabled - now handled by dashboard overlay');
    
    // Add hover effect
    minervaOrb.addEventListener('mouseenter', function() {
      this.classList.add('hover');
      const label = document.querySelector('.minerva-orb-label');
      if (label) {
        label.textContent = 'Click to Open Minerva Dashboard';
      }
    });
    
    minervaOrb.addEventListener('mouseleave', function() {
      this.classList.remove('hover');
      const label = document.querySelector('.minerva-orb-label');
      if (label) {
        label.textContent = 'Minerva Portal';
      }
    });
  }
});
