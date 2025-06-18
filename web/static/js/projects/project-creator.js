/**
 * Project Creator Module
 * Handles project creation functionality with intelligent suggestions and API integration
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get all required elements
  const projectBtn = document.createElement('button'); // Create a button to add to projects section
  projectBtn.className = 'create-project-btn';
  projectBtn.innerHTML = '<i class="fas fa-plus"></i> New Project';
  
  const modalOverlay = document.getElementById('project-modal-overlay');
  const closeBtn = document.getElementById('close-modal');
  const cancelBtn = document.getElementById('cancel-project');
  const createBtn = document.getElementById('create-project');
  const projectForm = document.getElementById('create-project-form');
  const projectNameInput = document.getElementById('project-name');
  const suggestionsContainer = document.getElementById('name-suggestions-container');
  const addObjectiveBtn = document.getElementById('add-objective-btn');
  const objectivesContainer = document.getElementById('objectives-container');
  
  // Add the "New Project" button to the projects section
  const projectsHeader = document.querySelector('#orb-projects h2');
  if (projectsHeader) {
    projectsHeader.parentNode.insertBefore(projectBtn, projectsHeader.nextSibling);
  }
  
  // Bind click event to new project button
  projectBtn.addEventListener('click', openModal);
  
  // Initialize event listeners
  initModalListeners();
  initFormHandlers();
  
  /**
   * Initialize modal event listeners
   */
  function initModalListeners() {
    // Open modal buttons
    document.querySelectorAll('.open-project-modal').forEach(btn => {
      btn.addEventListener('click', openModal);
    });
    
    // Close modal listeners
    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);
    
    // Close when clicking outside the modal
    modalOverlay.addEventListener('click', function(e) {
      if (e.target === modalOverlay) {
        closeModal();
      }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
        closeModal();
      }
    });
  }
  
  /**
   * Initialize form handlers and suggestions
   */
  function initFormHandlers() {
    // Project name input suggestions
    projectNameInput.addEventListener('input', generateNameSuggestions);
    
    // Add new objective
    addObjectiveBtn.addEventListener('click', addObjectiveRow);
    
    // Remove objective (delegate event for dynamically added buttons)
    objectivesContainer.addEventListener('click', function(e) {
      if (e.target.classList.contains('remove-objective') || e.target.closest('.remove-objective')) {
        const row = e.target.closest('.objective-row');
        if (row && objectivesContainer.querySelectorAll('.objective-row').length > 1) {
          row.remove();
        }
      }
    });
    
    // Form submission
    projectForm.addEventListener('submit', function(e) {
      e.preventDefault();
      createProject();
    });
    
    // Initialize with default suggestions
    generateNameSuggestions();
  }
  
  /**
   * Open the project modal
   */
  function openModal() {
    // Reset form before opening
    projectForm.reset();
    
    // Clear objectives except the first one
    const objectives = objectivesContainer.querySelectorAll('.objective-row');
    for (let i = 1; i < objectives.length; i++) {
      objectives[i].remove();
    }
    
    // Generate initial suggestions
    generateNameSuggestions();
    
    // Show the modal with animation
    modalOverlay.classList.add('active');
    
    // Focus the project name input
    setTimeout(() => {
      projectNameInput.focus();
    }, 300);
    
    // Announce for screen readers
    announceToScreenReader('Create project modal opened');
  }
  
  /**
   * Close the project modal
   */
  function closeModal() {
    modalOverlay.classList.remove('active');
    announceToScreenReader('Create project modal closed');
  }
  
  /**
   * Generate smart name suggestions based on current input and memory context
   */
  function generateNameSuggestions() {
    // Clear previous suggestions
    suggestionsContainer.innerHTML = '';
    
    // Get current input
    const currentInput = projectNameInput.value.trim().toLowerCase();
    
    // Base suggestions - evergreen good project types
    let suggestions = [
      'Minerva Integration',
      'API Documentation',
      'UI Enhancement',
      'Performance Optimization',
      'Data Analysis'
    ];
    
    // Add contextual suggestions based on memory if checkbox is checked
    if (document.getElementById('use-memory-context').checked) {
      try {
        // Try to get memories from localStorage for context
        const memories = JSON.parse(localStorage.getItem('minerva_memories') || '[]');
        const recentMemories = memories.slice(0, 3);
        
        // Extract keywords from memories
        recentMemories.forEach(memory => {
          const title = memory.title || '';
          if (title && !suggestions.includes(title)) {
            suggestions.push(title);
          }
          
          // Generate a project idea from memory content
          if (memory.content) {
            const words = memory.content.split(' ');
            // Take first 3-5 significant words
            if (words.length >= 3) {
              const projectIdea = words.slice(0, Math.min(5, words.length))
                .filter(word => word.length > 3)
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
              
              if (projectIdea && projectIdea.length > 10 && !suggestions.includes(projectIdea)) {
                suggestions.push(projectIdea);
              }
            }
          }
        });
        
        // Get chat context for more ideas
        const chatHistory = localStorage.getItem('minerva_chat_history');
        if (chatHistory) {
          // Extract potential project names from chat
          const parser = new DOMParser();
          const chatDoc = parser.parseFromString(chatHistory, 'text/html');
          const userMessages = chatDoc.querySelectorAll('.message.user');
          
          if (userMessages.length > 0) {
            // Use the most recent user message as potential project name
            const lastMessage = userMessages[userMessages.length - 1].textContent.trim();
            const words = lastMessage.split(' ');
            
            if (words.length >= 2) {
              const chatProjectIdea = words.slice(0, Math.min(4, words.length))
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
              
              if (chatProjectIdea && chatProjectIdea.length > 5 && !suggestions.includes(chatProjectIdea)) {
                suggestions.push(chatProjectIdea + ' Project');
              }
            }
          }
        }
      } catch (e) {
        console.warn('Error generating contextual project suggestions:', e);
      }
    }
    
    // Filter suggestions based on current input if any
    if (currentInput) {
      suggestions = suggestions.filter(suggestion => 
        suggestion.toLowerCase().includes(currentInput)
      );
    }
    
    // Limit to 5 suggestions
    suggestions = suggestions.slice(0, 5);
    
    // Add suggestions to DOM
    suggestions.forEach(suggestion => {
      const chip = document.createElement('span');
      chip.className = 'suggestion-chip';
      chip.textContent = suggestion;
      chip.addEventListener('click', () => {
        projectNameInput.value = suggestion;
        generateNameSuggestions(); // Regenerate after selection
      });
      suggestionsContainer.appendChild(chip);
    });
  }
  
  /**
   * Add a new objective input row
   */
  function addObjectiveRow() {
    const row = document.createElement('div');
    row.className = 'objective-row';
    row.innerHTML = `
      <input type="text" class="objective-input" placeholder="Enter an objective">
      <button type="button" class="remove-objective"><i class="fas fa-times"></i></button>
    `;
    objectivesContainer.appendChild(row);
    
    // Focus the new input
    row.querySelector('input').focus();
  }
  
  /**
   * Create a new project with form data
   */
  function createProject() {
    // Disable form during submission
    const formElements = projectForm.elements;
    for (let i = 0; i < formElements.length; i++) {
      formElements[i].disabled = true;
    }
    
    // Change button to loading state
    createBtn.innerHTML = '<span class="spinner"></span> Creating...';
    
    // Get form data
    const projectName = projectNameInput.value.trim();
    const projectDescription = document.getElementById('project-description').value.trim();
    
    // Get objectives
    const objectives = [];
    objectivesContainer.querySelectorAll('.objective-input').forEach(input => {
      const value = input.value.trim();
      if (value) {
        objectives.push(value);
      }
    });
    
    // Create project object
    const newProject = {
      id: generateProjectId(projectName),
      title: projectName,
      description: projectDescription,
      objectives: objectives,
      created: new Date().toISOString(),
      updated: new Date().toISOString()
    };
    
    // Try to create project via API
    fetch('/api/projects', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newProject)
    })
    .then(response => {
      if (response.ok) {
        return response.json().then(data => {
          showSuccessMessage(`Project "${projectName}" created successfully!`);
          closeModal();
          saveProjectLocally(data.project || newProject);
          reloadProjects(); // Refresh projects list
        });
      } else {
        throw new Error('Failed to create project');
      }
    })
    .catch(error => {
      console.warn('API call failed, using local storage fallback:', error);
      // Fallback to localStorage
      saveProjectLocally(newProject);
      showSuccessMessage(`Project "${projectName}" created (saved locally)`);
      closeModal();
      reloadProjects(); // Refresh projects list
    })
    .finally(() => {
      // Re-enable form
      for (let i = 0; i < formElements.length; i++) {
        formElements[i].disabled = false;
      }
      createBtn.innerHTML = '<span>Create Project</span>';
    });
  }
  
  /**
   * Generate a URL-friendly project ID
   */
  function generateProjectId(name) {
    return name.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-') // Replace spaces and non-alphanumeric chars with hyphens
      .replace(/^-|-$/g, '') // Remove leading and trailing hyphens
      + '-' + Math.floor(Date.now() / 1000).toString(36); // Add timestamp for uniqueness
  }
  
  /**
   * Save project to localStorage as fallback
   */
  function saveProjectLocally(project) {
    // Get existing projects
    const projects = JSON.parse(localStorage.getItem('minerva_projects') || '[]');
    
    // Add new project
    projects.push(project);
    
    // Save back to localStorage
    localStorage.setItem('minerva_projects', JSON.stringify(projects));
    
    console.log('Project saved to localStorage:', project.title);
  }
  
  /**
   * Reload the projects list after creation
   */
  function reloadProjects() {
    // If the loadProjects function exists, call it
    if (typeof loadProjects === 'function') {
      loadProjects();
    } else {
      console.warn('loadProjects function not found, cannot refresh');
      // Try to reload projects via DOM update
      const projectsList = document.getElementById('projects-list');
      if (projectsList) {
        projectsList.innerHTML = '<p class="loading">Refreshing projects...</p>';
        setTimeout(() => {
          try {
            const projects = JSON.parse(localStorage.getItem('minerva_projects') || '[]');
            if (projects.length > 0) {
              projectsList.innerHTML = '';
              projects.forEach(project => {
                const projectItem = document.createElement('div');
                projectItem.className = 'project-item';
                projectItem.innerHTML = `
                  <h3>${project.title}</h3>
                  <p>${project.description}</p>
                  <div class="project-actions">
                    <button class="btn-view"><i class="fas fa-eye"></i> View</button>
                  </div>
                `;
                projectsList.appendChild(projectItem);
              });
            } else {
              projectsList.innerHTML = '<p class="empty-state">No projects found.</p>';
            }
          } catch (e) {
            console.error('Error refreshing projects list:', e);
          }
        }, 500);
      }
    }
  }
  
  /**
   * Show success message toast
   */
  function showSuccessMessage(message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'success-toast';
    toast.innerHTML = `
      <i class="fas fa-check-circle"></i>
      <span>${message}</span>
    `;
    
    // Add styles
    toast.style.cssText = `
      position: fixed;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(16, 185, 129, 0.9);
      color: white;
      padding: 12px 20px;
      border-radius: 6px;
      font-size: 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      z-index: 10000;
      opacity: 0;
      transition: opacity 0.3s ease;
    `;
    
    // Add to body
    document.body.appendChild(toast);
    
    // Fade in
    setTimeout(() => {
      toast.style.opacity = '1';
    }, 10);
    
    // Remove after 4 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        if (document.body.contains(toast)) {
          document.body.removeChild(toast);
        }
      }, 300);
    }, 4000);
    
    // Announce for screen readers
    announceToScreenReader(message);
  }
  
  /**
   * Announce message to screen readers
   */
  function announceToScreenReader(message) {
    let announcer = document.getElementById('sr-announcer');
    
    if (!announcer) {
      announcer = document.createElement('div');
      announcer.id = 'sr-announcer';
      announcer.setAttribute('aria-live', 'polite');
      announcer.setAttribute('class', 'sr-only');
      announcer.style.cssText = 'position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0;';
      document.body.appendChild(announcer);
    }
    
    announcer.textContent = message;
  }
});
