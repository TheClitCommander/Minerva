/**
 * Minerva Orbital UI
 * Creates a central orb with orbiting menu items
 * Direct API connection, no fallbacks
 */

class MinervaOrbitalUI {
  constructor(options = {}) {
    // Configuration
    this.apiUrl = options.apiUrl || 'http://127.0.0.1:5505';
    this.containerId = options.containerId || 'minerva-orbital-ui';
    this.orbSize = options.orbSize || 120;
    this.menuItems = options.menuItems || [
      { id: 'dashboard', icon: 'fa-tachometer-alt', label: 'Dashboard' },
      { id: 'chat', icon: 'fa-comments', label: 'Chat' },
      { id: 'memory', icon: 'fa-brain', label: 'Memory' },
      { id: 'projects', icon: 'fa-project-diagram', label: 'Projects' }
    ];
    
    // State
    this.activeSection = 'dashboard';
    this.connected = false;
    
    // Initialize
    this.init();
  }
  
  init() {
    console.log('🚀 Initializing Minerva Orbital UI');
    
    // Get or create container
    this.container = document.getElementById(this.containerId);
    if (!this.container) {
      console.log('Creating Minerva Orbital UI container');
      this.container = document.createElement('div');
      this.container.id = this.containerId;
      document.body.appendChild(this.container);
    }
    
    // Create the UI
    this.createOrbitalUI();
    
    // Check API connection
    this.checkApiConnection();
    
    // Set up periodic connection checking
    setInterval(() => this.checkApiConnection(), 15000);
  }
  
  async checkApiConnection() {
    try {
      console.log('Checking API connection...');
      const response = await fetch(`${this.apiUrl}/api/status`);
      
      if (response.ok) {
        const data = await response.json();
        this.connected = true;
        this.updateConnectionStatus('connected');
        console.log('API connected:', data);
        return true;
      } else {
        this.connected = false;
        this.updateConnectionStatus('disconnected');
        console.error('API returned error status:', response.status);
        return false;
      }
    } catch (error) {
      this.connected = false;
      this.updateConnectionStatus('disconnected');
      console.error('Failed to connect to API:', error);
      return false;
    }
  }
  
  updateConnectionStatus(status) {
    // Update orb status indicator
    const statusIndicator = document.querySelector('.orb-status');
    if (statusIndicator) {
      statusIndicator.className = 'orb-status ' + status;
      
      // Update text if present
      const statusText = statusIndicator.querySelector('.status-text');
      if (statusText) {
        statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
      }
    }
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('minerva-api-status', { 
      detail: { status }
    }));
  }
  
  createOrbitalUI() {
    // Create container with cosmic styling
    this.container.className = 'orbital-ui-container';
    
    // Create central orb
    const orb = document.createElement('div');
    orb.className = 'minerva-orb';
    orb.innerHTML = `
      <div class="orb-inner">M</div>
      <div class="orb-status initializing">
        <span class="status-text">Initializing</span>
      </div>
    `;
    this.container.appendChild(orb);
    
    // Create orbiting menu items
    this.createRadialOrbitalMenu();
    
    // Create content sections
    this.createContentSections();
    
    // Add event for opening chat
    orb.addEventListener('click', () => this.toggleSection('chat'));
  }
  
  createRadialOrbitalMenu() {
    if (!this.container || this.menuItems.length === 0) return;
    
    // Get the central orb for positioning reference
    const centralOrb = this.container.querySelector('.minerva-orb');
    if (!centralOrb) {
      console.error('Central orb not found');
      return;
    }
    
    // Get container dimensions
    const containerRect = this.container.getBoundingClientRect();
    const centerX = containerRect.width / 2;
    const centerY = containerRect.height / 2;
    
    // Calculate orbital radius - make it responsive
    const radius = Math.min(containerRect.width, containerRect.height) * 0.35;
    
    // Position each menu item in a circle around the orb
    this.menuItems.forEach((item, index) => {
      // Calculate angle based on item index and total count
      const angleInRadians = (index / this.menuItems.length) * Math.PI * 2;
      
      // Calculate position using trigonometry
      const x = centerX + radius * Math.cos(angleInRadians) - item.offsetWidth / 2;
      const y = centerY + radius * Math.sin(angleInRadians) - item.offsetHeight / 2;
      
      // Apply position
      item.style.position = 'absolute';
      item.style.left = `${x}px`;
      item.style.top = `${y}px`;
      
      // Store original position for animations
      item.dataset.orbitalAngle = angleInRadians;
      item.dataset.orbitalRadius = radius;
      
      // Add hover effect
      item.classList.add('orbital-item-animated');
    });
  }
  
  createContentSections() {
    // Create container for content sections
    const sectionsContainer = document.createElement('div');
    sectionsContainer.className = 'content-sections';
    this.container.appendChild(sectionsContainer);
    
    // Create each section
    this.menuItems.forEach(item => {
      const section = document.createElement('div');
      section.className = 'content-section';
      section.id = `section-${item.id}`;
      section.style.display = 'none'; // Hide initially
      
      // Add basic structure based on section type
      switch (item.id) {
        case 'dashboard':
          section.innerHTML = `
            <h2><i class="fas ${item.icon}"></i> ${item.label}</h2>
            <div class="dashboard-stats">
              <div class="stat">
                <div class="stat-value">4</div>
                <div class="stat-label">Projects</div>
              </div>
              <div class="stat">
                <div class="stat-value">12</div>
                <div class="stat-label">Memories</div>
              </div>
              <div class="stat">
                <div class="stat-value">3</div>
                <div class="stat-label">Active Tasks</div>
              </div>
            </div>
            <div class="activity-feed">
              <h3>Recent Activity</h3>
              <div class="activity-items" id="activity-items">
                <div class="activity-item">Loading activity...</div>
              </div>
            </div>
          `;
          break;
          
        case 'chat':
          section.innerHTML = `
            <div class="chat-container" id="chat-container">
              <div class="chat-header">
                <h2><i class="fas ${item.icon}"></i> ${item.label}</h2>
                <div class="chat-controls">
                  <button class="minimize-button"><i class="fas fa-minus"></i></button>
                  <button class="close-button"><i class="fas fa-times"></i></button>
                </div>
              </div>
              <div class="chat-messages" id="chat-messages">
                <div class="message system">
                  <div class="message-content">
                    <div class="message-text">Welcome to Minerva. How can I assist you today?</div>
                  </div>
                </div>
              </div>
              <div class="chat-input-container">
                <form id="chat-form">
                  <input type="text" id="chat-input" placeholder="Type your message..." autocomplete="off">
                  <button type="submit"><i class="fas fa-paper-plane"></i></button>
                </form>
              </div>
            </div>
          `;
          
          // Set up chat handlers after the section is displayed
          section.addEventListener('display', () => {
            this.setupChatHandlers(section);
          });
          break;
          
        case 'memory':
          section.innerHTML = `
            <h2><i class="fas ${item.icon}"></i> ${item.label}</h2>
            <div class="memory-controls">
              <input type="text" id="memory-search" placeholder="Search memories...">
              <button class="new-memory-button"><i class="fas fa-plus"></i> New Memory</button>
            </div>
            <div class="memory-items" id="memory-items">
              <div class="memory-item">Loading memories...</div>
            </div>
          `;
          
          // Set up memory handlers after the section is displayed
          section.addEventListener('display', () => {
            this.loadMemories();
          });
          break;
          
        case 'projects':
          section.innerHTML = `
            <h2><i class="fas ${item.icon}"></i> ${item.label}</h2>
            <div class="project-controls">
              <button class="new-project-button"><i class="fas fa-plus"></i> New Project</button>
            </div>
            <div class="project-items" id="project-items">
              <div class="project-item">Loading projects...</div>
            </div>
          `;
          
          // Set up project handlers after the section is displayed
          section.addEventListener('display', () => {
            this.loadProjects();
          });
          break;
      }
      
      sectionsContainer.appendChild(section);
    });
    
    // Show dashboard by default
    this.toggleSection('dashboard');
  }
  
  toggleSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    // Show the selected section
    const targetSection = document.getElementById(`section-${sectionId}`);
    if (targetSection) {
      targetSection.style.display = 'block';
      this.activeSection = sectionId;
      
      // Trigger display event
      targetSection.dispatchEvent(new Event('display'));
      
      // Update active menu item
      this.updateActiveMenuItem(sectionId);
    }
  }
  
  updateActiveMenuItem(sectionId) {
    // Remove active class from all menu items
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
      item.classList.remove('active');
    });
    
    // Add active class to selected menu item
    const activeItem = document.querySelector(`.menu-item[data-section="${sectionId}"]`);
    if (activeItem) {
      activeItem.classList.add('active');
    }
  }
  
  setupChatHandlers(chatSection) {
    const form = chatSection.querySelector('#chat-form');
    const input = chatSection.querySelector('#chat-input');
    const messages = chatSection.querySelector('#chat-messages');
    
    // Make chat container draggable
    this.makeDraggable(chatSection.querySelector('.chat-container'), chatSection.querySelector('.chat-header'));
    
    // Set up minimize and close buttons
    const minimizeBtn = chatSection.querySelector('.minimize-button');
    const closeBtn = chatSection.querySelector('.close-button');
    
    if (minimizeBtn) {
      minimizeBtn.addEventListener('click', () => {
        const container = chatSection.querySelector('.chat-container');
        container.classList.toggle('minimized');
      });
    }
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.toggleSection('dashboard');
      });
    }
    
    // Set up form submission
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = input.value.trim();
        if (!message) return;
        
        // Clear input
        input.value = '';
        
        // Add user message
        this.addChatMessage(messages, message, 'user');
        
        // Send to API and get response
        await this.sendChatMessage(messages, message);
      });
    }
  }
  
  makeDraggable(element, handle) {
    if (!element || !handle) return;
    
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    handle.addEventListener('mousedown', dragMouseDown);
    
    function dragMouseDown(e) {
      e.preventDefault();
      // Get mouse position at startup
      pos3 = e.clientX;
      pos4 = e.clientY;
      document.addEventListener('mouseup', closeDragElement);
      document.addEventListener('mousemove', elementDrag);
    }
    
    function elementDrag(e) {
      e.preventDefault();
      // Calculate new position
      pos1 = pos3 - e.clientX;
      pos2 = pos4 - e.clientY;
      pos3 = e.clientX;
      pos4 = e.clientY;
      // Set element's new position
      element.style.top = (element.offsetTop - pos2) + "px";
      element.style.left = (element.offsetLeft - pos1) + "px";
    }
    
    function closeDragElement() {
      // Stop moving when mouse button is released
      document.removeEventListener('mouseup', closeDragElement);
      document.removeEventListener('mousemove', elementDrag);
    }
  }
  
  addChatMessage(messagesContainer, text, sender) {
    if (!messagesContainer) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    messageElement.innerHTML = `
      <div class="message-content">
        <div class="message-text">${text}</div>
      </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  async sendChatMessage(messagesContainer, message) {
    try {
      // Check connection first
      const isConnected = await this.checkApiConnection();
      if (!isConnected) {
        this.addChatMessage(messagesContainer, 'Cannot send message: API is disconnected', 'system error');
        return;
      }
      
      // Send to API
      const response = await fetch(`${this.apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      this.addChatMessage(messagesContainer, data.response, 'minerva');
    } catch (error) {
      console.error('Failed to send message:', error);
      this.addChatMessage(messagesContainer, `Error: ${error.message}`, 'system error');
    }
  }
  
  async loadMemories() {
    const memoryItems = document.getElementById('memory-items');
    if (!memoryItems) return;
    
    try {
      const response = await fetch(`${this.apiUrl}/api/memories`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const memories = await response.json();
      
      // Clear existing content
      memoryItems.innerHTML = '';
      
      // Add each memory
      if (memories.length === 0) {
        memoryItems.innerHTML = '<div class="memory-item empty">No memories found. Create a new memory to get started.</div>';
      } else {
        memories.forEach(memory => {
          const memoryElement = document.createElement('div');
          memoryElement.className = 'memory-item';
          memoryElement.innerHTML = `
            <div class="memory-header">
              <div class="memory-type">${memory.type || 'Memory'}</div>
              <div class="memory-date">${new Date().toLocaleDateString()}</div>
            </div>
            <div class="memory-text">${memory.text}</div>
          `;
          memoryItems.appendChild(memoryElement);
        });
      }
    } catch (error) {
      console.error('Failed to load memories:', error);
      memoryItems.innerHTML = `<div class="memory-item error">Error loading memories: ${error.message}</div>`;
    }
  }
  
  async loadProjects() {
    const projectItems = document.getElementById('project-items');
    if (!projectItems) return;
    
    try {
      const response = await fetch(`${this.apiUrl}/api/projects`);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const projects = await response.json();
      
      // Clear existing content
      projectItems.innerHTML = '';
      
      // Add each project
      if (projects.length === 0) {
        projectItems.innerHTML = '<div class="project-item empty">No projects found. Create a new project to get started.</div>';
      } else {
        projects.forEach(project => {
          const projectElement = document.createElement('div');
          projectElement.className = 'project-item';
          projectElement.innerHTML = `
            <div class="project-header">
              <div class="project-name">${project.name}</div>
              <div class="project-status">${project.status}</div>
            </div>
            <div class="project-actions">
              <button class="open-project-button">Open</button>
            </div>
          `;
          projectItems.appendChild(projectElement);
        });
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
      projectItems.innerHTML = `<div class="project-item error">Error loading projects: ${error.message}</div>`;
    }
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  window.orbitalUI = new MinervaOrbitalUI({
    apiUrl: 'http://127.0.0.1:5505'
  });
});
