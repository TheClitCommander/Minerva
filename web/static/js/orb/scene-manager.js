/**
 * Minerva SceneManager
 * Manages scene transitions and content display for the orb interface
 * Provides real, non-simulated UI transitions between different sections
 */

class SceneManager {
  constructor(options = {}) {
    // Core elements
    this.container = options.container || document.getElementById('orb-interface');
    this.sections = options.sections || {};
    this.activeSection = null;
    this.history = [];
    this.transitionDuration = options.transitionDuration || 300; // ms
    this.animationEnabled = options.animationEnabled !== false;
    
    // Animation direction (for slide animations)
    this.lastDirection = 'right';
    
    // Initialize
    this.init();
    
    // Log success
    console.log('✅ Minerva SceneManager initialized with sections:', Object.keys(this.sections));
  }
  
  /**
   * Initialize the SceneManager
   */
  init() {
    // Find all sections within the container if not provided
    if (Object.keys(this.sections).length === 0 && this.container) {
      const sectionElements = this.container.querySelectorAll('.orb-section');
      sectionElements.forEach(section => {
        // Extract the section name from the ID (strip either 'orb-' prefix or '-section' suffix)
        let id = section.id.replace('-section', '');
        id = id.replace('orb-', '');
        this.sections[id] = section;
      });
    }
    
    // Hide all sections initially
    for (const sectionName in this.sections) {
      if (this.sections[sectionName]) {
        this.sections[sectionName].style.display = 'none';
        this.sections[sectionName].setAttribute('aria-hidden', 'true');
      }
    }
    
    // Add custom event listener for scene changes
    window.addEventListener('minerva-scene-change', (event) => {
      if (event.detail && event.detail.scene) {
        this.showScene(event.detail.scene, event.detail.data);
      }
    });
    
    // Restore last active section from localStorage if available
    const lastSection = localStorage.getItem('minerva_last_section');
    if (lastSection && this.sections[lastSection]) {
      this.showScene(lastSection);
    } else if (this.sections['dashboard']) {
      // Default to dashboard
      this.showScene('dashboard');
    }
  }
  
  /**
   * Show a specific scene
   * @param {string} sceneName - Name of the scene to show
   * @param {object} data - Optional data to pass to the scene
   * @param {object} options - Transition options
   */
  showScene(sceneName, data = {}, options = {}) {
    // Check if the scene exists
    if (!this.sections[sceneName]) {
      console.error(`Scene "${sceneName}" not found!`);
      return false;
    }
    
    // Save to history
    if (this.activeSection && this.activeSection !== sceneName) {
      this.history.push(this.activeSection);
      // Keep history limited to 5 items
      if (this.history.length > 5) {
        this.history.shift();
      }
    }
    
    // Get scene element
    const sceneElement = this.sections[sceneName];
    
    // Prepare scene before showing (can be used for data loading)
    this._prepareScene(sceneName, data);
    
    // Hide current active scene
    if (this.activeSection && this.sections[this.activeSection]) {
      const activeElement = this.sections[this.activeSection];
      
      // Animate out the current scene
      if (this.animationEnabled && !options.immediate) {
        this._animateTransition(activeElement, sceneElement, options.direction || 'right');
      } else {
        // Immediate transition
        activeElement.style.display = 'none';
        activeElement.setAttribute('aria-hidden', 'true');
        sceneElement.style.display = 'block';
        sceneElement.setAttribute('aria-hidden', 'false');
      }
    } else {
      // No active scene, just show the new one
      sceneElement.style.display = 'block';
      sceneElement.setAttribute('aria-hidden', 'false');
    }
    
    // Update active section
    this.activeSection = sceneName;
    
    // Save current section to localStorage for persistence
    localStorage.setItem('minerva_last_section', sceneName);
    
    // Dispatch event that scene has changed
    const sceneChangeEvent = new CustomEvent('minerva-scene-changed', {
      detail: {
        scene: sceneName,
        data: data
      }
    });
    window.dispatchEvent(sceneChangeEvent);
    
    // Return success
    return true;
  }
  
  /**
   * Animate the transition between scenes
   * @private
   */
  _animateTransition(fromElement, toElement, direction) {
    this.lastDirection = direction;
    
    // Set initial states
    fromElement.style.position = 'absolute';
    fromElement.style.width = '100%';
    fromElement.style.transition = `transform ${this.transitionDuration}ms ease, opacity ${this.transitionDuration}ms ease`;
    fromElement.style.opacity = '1';
    
    toElement.style.position = 'absolute';
    toElement.style.width = '100%';
    toElement.style.display = 'block';
    toElement.style.transition = `transform ${this.transitionDuration}ms ease, opacity ${this.transitionDuration}ms ease`;
    toElement.style.opacity = '0';
    
    const directionMultiplier = direction === 'right' ? 1 : -1;
    
    // Set initial positions
    toElement.style.transform = `translateX(${20 * directionMultiplier}px)`;
    
    // Trigger animation
    setTimeout(() => {
      fromElement.style.transform = `translateX(${-20 * directionMultiplier}px)`;
      fromElement.style.opacity = '0';
      toElement.style.transform = 'translateX(0)';
      toElement.style.opacity = '1';
      
      // Clean up after animation
      setTimeout(() => {
        fromElement.style.display = 'none';
        fromElement.style.position = '';
        fromElement.style.transform = '';
        fromElement.style.transition = '';
        fromElement.style.opacity = '';
        fromElement.setAttribute('aria-hidden', 'true');
        
        toElement.style.position = '';
        toElement.style.transform = '';
        toElement.style.transition = '';
        toElement.setAttribute('aria-hidden', 'false');
      }, this.transitionDuration + 50);
    }, 20);
  }
  
  /**
   * Go back to the previous scene
   */
  goBack() {
    if (this.history.length > 0) {
      const previousScene = this.history.pop();
      this.showScene(previousScene, {}, { direction: 'left' });
      return true;
    }
    return false;
  }
  
  /**
   * Prepare a scene before showing it
   * @private
   */
  _prepareScene(sceneName, data) {
    // Handle data loading or preparation based on scene
    switch (sceneName) {
      case 'dashboard':
        this._prepareDashboard(data);
        break;
      case 'chat':
        this._prepareChat(data);
        break;
      case 'memory':
        this._prepareMemory(data);
        break;
      case 'projects':
        this._prepareProjects(data);
        break;
    }
  }
  
  /**
   * Prepare dashboard scene
   * @private
   */
  _prepareDashboard(data) {
    // Update recent activity or stats
    const recentProjectsList = document.getElementById('recent-projects-list');
    if (recentProjectsList) {
      // Check if we need to update the projects list
      if (!recentProjectsList.dataset.loaded || data.forceRefresh) {
        try {
          // Get projects from localStorage
          const projects = JSON.parse(localStorage.getItem('minerva_projects') || '[]');
          
          if (projects.length > 0) {
            // Show only 3 most recent projects
            const recentProjects = projects.sort((a, b) => {
              return new Date(b.updated || b.created) - new Date(a.updated || a.created);
            }).slice(0, 3);
            
            recentProjectsList.innerHTML = '';
            
            recentProjects.forEach(project => {
              const projectItem = document.createElement('div');
              projectItem.className = 'recent-project-item';
              projectItem.innerHTML = `
                <span class="project-name">${project.title}</span>
                <button class="btn-view" data-project-id="${project.id}">View</button>
              `;
              
              // Add click event for viewing project
              const viewBtn = projectItem.querySelector('.btn-view');
              if (viewBtn) {
                viewBtn.addEventListener('click', () => {
                  this.showScene('projects', { selectedProject: project.id });
                });
              }
              
              recentProjectsList.appendChild(projectItem);
            });
            
            recentProjectsList.dataset.loaded = 'true';
          } else {
            recentProjectsList.innerHTML = '<p>No recent projects</p>';
          }
        } catch (e) {
          console.error('Error loading recent projects:', e);
          recentProjectsList.innerHTML = '<p>Error loading projects</p>';
        }
      }
    }
    
    // Update system stats
    this._updateSystemStats();
  }
  
  /**
   * Update system stats on dashboard
   * @private 
   */
  _updateSystemStats() {
    // Update API status
    const apiStatus = document.getElementById('api-status');
    if (apiStatus) {
      fetch('/api/status')
        .then(response => {
          if (response.ok) {
            apiStatus.textContent = 'Connected';
            apiStatus.className = 'status connected';
          } else {
            throw new Error('API returned error status');
          }
        })
        .catch(error => {
          apiStatus.textContent = 'Disconnected';
          apiStatus.className = 'status disconnected';
        });
    }
    
    // Update last updated timestamp
    const lastUpdate = document.getElementById('last-update');
    if (lastUpdate) {
      lastUpdate.textContent = new Date().toLocaleString();
    }
  }
  
  /**
   * Prepare chat scene
   * @private
   */
  _prepareChat(data) {
    // Focus on chat input when showing chat
    setTimeout(() => {
      const chatInput = document.getElementById('chat-input');
      if (chatInput) {
        chatInput.focus();
      }
    }, this.transitionDuration + 100);
  }
  
  /**
   * Prepare memory scene
   * @private
   */
  _prepareMemory(data) {
    // Load memories if not already loaded
    if (typeof window.loadMemories === 'function') {
      window.loadMemories();
    }
  }
  
  /**
   * Prepare projects scene
   * @private
   */
  _prepareProjects(data) {
    // Load projects if not already loaded
    if (typeof window.loadProjects === 'function') {
      window.loadProjects();
    }
    
    // Select a specific project if requested
    if (data && data.selectedProject) {
      // Highlight the selected project
      const projectItems = document.querySelectorAll('.project-item');
      projectItems.forEach(item => {
        const viewBtn = item.querySelector('.btn-view');
        if (viewBtn && viewBtn.dataset.projectId === data.selectedProject) {
          item.classList.add('selected');
          // Scroll to the selected project
          item.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
          item.classList.remove('selected');
        }
      });
    }
  }
}

// Make SceneManager available globally
window.SceneManager = SceneManager;
