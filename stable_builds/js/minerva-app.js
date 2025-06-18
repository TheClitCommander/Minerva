/**
 * Minerva App Core
 * Manages the main application functionality and coordinates between modules
 * Includes project tracking, state management, and UI coordination
 */

class MinervaApp {
  constructor(options = {}) {
    // Core settings
    this.debugMode = options.debug || false;
    this.appVersion = '1.0.0';
    
    // Components (will be initialized if available)
    this.chatSystem = null;
    this.zoomManager = null;
    this.visualizationSystem = null;
    
    // State tracking
    this.isInitialized = false;
    this.activeProject = localStorage.getItem('minerva_active_project') || 'general';
    
    // Initialize as soon as DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initialize());
    } else {
      this.initialize();
    }
  }
  
  // Initialize all systems
  initialize() {
    console.log(`Initializing Minerva App v${this.appVersion}`);
    
    // Initialize zoom manager if available
    this.initZoomManager();
    
    // Initialize chat system if available
    this.initChatSystem();
    
    // Initialize visualization if available
    this.initVisualization();
    
    // Set up project handling
    this.initProjectSystem();
    
    // Mark as initialized
    this.isInitialized = true;
    console.log('Minerva App initialization complete');
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('minerva-initialized', { 
      detail: { version: this.appVersion } 
    }));
  }
  
  initZoomManager() {
    try {
      // Check if zoom manager script is loaded
      if (typeof ZoomManager !== 'undefined') {
        this.zoomManager = new ZoomManager();
        console.log('Zoom Manager initialized');
        return true;
      } else {
        // Try to dynamically load the script
        this.loadScript('/static/js/core/zoom-manager.js')
          .then(() => {
            if (typeof ZoomManager !== 'undefined') {
              this.zoomManager = new ZoomManager();
              console.log('Zoom Manager initialized (async)');
            }
          })
          .catch(err => console.error('Failed to load Zoom Manager:', err));
      }
    } catch (error) {
      console.error('Error initializing Zoom Manager:', error);
    }
    return false;
  }
  
  initChatSystem() {
    try {
      // Check if chat system script is loaded
      if (typeof MinervaChat !== 'undefined') {
        this.chatSystem = new MinervaChat({
          activeProject: this.activeProject,
          debug: this.debugMode
        });
        console.log('Chat System initialized');
        return true;
      } else {
        // Try to dynamically load the script
        this.loadScript('/static/js/chat/chat-core.js')
          .then(() => {
            if (typeof MinervaChat !== 'undefined') {
              this.chatSystem = new MinervaChat({
                activeProject: this.activeProject,
                debug: this.debugMode
              });
              console.log('Chat System initialized (async)');
            }
          })
          .catch(err => console.error('Failed to load Chat System:', err));
      }
    } catch (error) {
      console.error('Error initializing Chat System:', error);
    }
    return false;
  }
  
  initVisualization() {
    // Only initialize if THREE.js is available
    if (typeof THREE === 'undefined') {
      console.log('THREE.js not available, skipping visualization');
      return false;
    }
    
    try {
      // Check for container
      const container = document.getElementById('orbital-planet-container') || 
                       document.getElementById('minerva-orbital-ui');
      
      if (!container) {
        console.log('Visualization container not found');
        return false;
      }
      
      // Initialize visualization appropriate for this UI
      if (typeof initPlanetVisualization !== 'undefined') {
        // Connect the visualization with zoom manager if available
        if (this.zoomManager) {
          // Subscribe to zoom changes
          this.zoomManager.subscribe((zoomLevel) => {
            // Update camera based on zoom level if the globals are available
            if (typeof camera !== 'undefined' && typeof controls !== 'undefined') {
              const baseZ = 5; // Base Z position at zoom 1.0
              camera.position.z = baseZ / zoomLevel;
              controls.update();
            }
          });
        }
        
        console.log('Visualization system initialized');
        return true;
      }
    } catch (error) {
      console.error('Error initializing Visualization:', error);
    }
    return false;
  }
  
  initProjectSystem() {
    // Initialize projects if not exists
    if (!window.minervaProjects) {
      window.minervaProjects = {
        general: { name: 'General Conversation', conversations: [] }
      };
      localStorage.setItem('minervaProjects', JSON.stringify(window.minervaProjects));
    }
    
    // Set up project selection if available
    const projectSelect = document.getElementById('project-select');
    if (projectSelect) {
      // Update project dropdown with available projects
      this.updateProjectDropdown(projectSelect);
      
      // Add event listener for project changes
      projectSelect.addEventListener('change', (e) => {
        const projectId = e.target.value;
        
        if (projectId === 'create-new') {
          this.showCreateProjectDialog();
        } else {
          this.switchProject(projectId);
        }
      });
    }
    
    // Set up create project button if available
    const createProjectBtn = document.getElementById('create-project-btn');
    if (createProjectBtn) {
      createProjectBtn.addEventListener('click', () => {
        this.showCreateProjectDialog();
      });
    }
    
    console.log('Project system initialized');
    return true;
  }
  
  updateProjectDropdown(dropdown) {
    if (!dropdown) return false;
    
    // Clear existing projects (except create new)
    Array.from(dropdown.options)
      .filter(option => option.value !== 'create-new')
      .forEach(option => dropdown.removeChild(option));
    
    // Add all projects
    const createNewOption = dropdown.querySelector('option[value="create-new"]');
    Object.entries(window.minervaProjects).forEach(([id, project]) => {
      const option = document.createElement('option');
      option.value = id;
      option.textContent = project.name;
      
      // Insert before the "Create New" option
      if (createNewOption) {
        dropdown.insertBefore(option, createNewOption);
      } else {
        dropdown.appendChild(option);
      }
    });
    
    // Select current project
    dropdown.value = this.activeProject;
    
    return true;
  }
  
  switchProject(projectId) {
    if (!projectId || !window.minervaProjects[projectId]) return false;
    
    // Update active project
    this.activeProject = projectId;
    localStorage.setItem('minerva_active_project', projectId);
    
    // Use chat system if available
    if (this.chatSystem) {
      this.chatSystem.switchProject(projectId);
    } else {
      // Fallback handling if chat system not available
      window.minervaMemory = [...(window.minervaProjects[projectId].conversations || [])];
      
      // Clear chat display and add welcome message
      const chatMessages = document.getElementById('chat-messages');
      if (chatMessages) {
        chatMessages.innerHTML = '';
        
        const systemMsg = document.createElement('div');
        systemMsg.className = 'system-message';
        systemMsg.textContent = `Switched to project: ${window.minervaProjects[projectId].name}. How can I help with this project?`;
        chatMessages.appendChild(systemMsg);
      }
    }
    
    console.log(`Switched to project: ${projectId}`);
    return true;
  }
  
  showCreateProjectDialog() {
    const projectName = prompt('Enter a name for the new project:');
    if (projectName && projectName.trim()) {
      this.createProject(projectName.trim());
    }
  }
  
  createProject(projectName) {
    if (!projectName) return null;
    
    const projectId = 'proj-' + Date.now();
    window.minervaProjects[projectId] = {
      name: projectName,
      conversations: [...(window.minervaMemory || [])], // Copy current conversation
      created: new Date().toISOString()
    };
    
    // Save to local storage
    localStorage.setItem('minervaProjects', JSON.stringify(window.minervaProjects));
    
    // Update project dropdown
    const projectSelect = document.getElementById('project-select');
    if (projectSelect) {
      this.updateProjectDropdown(projectSelect);
    }
    
    // Switch to new project
    this.switchProject(projectId);
    
    return projectId;
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

// Initialize Minerva App
document.addEventListener('DOMContentLoaded', () => {
  // Create global instance
  window.minervaApp = new MinervaApp({
    debug: true
  });
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MinervaApp };
}
