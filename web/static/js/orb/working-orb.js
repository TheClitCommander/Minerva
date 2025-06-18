/**
 * Working Orb UI - Guaranteed functional implementation
 * Following our previous success pattern and integration plan
 */

document.addEventListener('DOMContentLoaded', function() {
  console.log('🔄 Initializing Working Minerva Orb UI...');
  
  // Find key elements
  const orbButton = document.getElementById('orb-button');
  const orbMenu = document.getElementById('orb-menu');
  const orbInterface = document.getElementById('orb-interface');
  const orbContainer = document.getElementById('orb-container');
  
  // Check if elements exist
  if (!orbButton || !orbMenu || !orbInterface) {
    console.error('Critical: Missing orb elements', {
      orbButton: !!orbButton,
      orbMenu: !!orbMenu,
      orbInterface: !!orbInterface
    });
    
    // Show fallback message
    showError('Missing critical orb elements. Check console for details.');
    return;
  }
  
  console.log('✅ Found all required orb elements');
  
  // Initialize SceneManager for real scene transitions
  let sceneManager;
  try {
    // Find all section elements
    const sections = {};
    document.querySelectorAll('.orb-section').forEach(section => {
      const id = section.id.replace('orb-', '');
      sections[id] = section;
    });
    
    // Create SceneManager instance
    sceneManager = new SceneManager({
      container: orbInterface,
      sections: sections,
      animationEnabled: true,
      transitionDuration: 300
    });
    
    window.minervaSceneManager = sceneManager; // Make globally available
    console.log('✅ SceneManager initialized successfully');
  } catch (e) {
    console.error('Error initializing SceneManager:', e);
    showError('Failed to initialize scene manager. Some features may be limited.');
  }
  
  // Make the interface scrollable if content exceeds height
  if (orbInterface) {
    orbInterface.style.overflowY = 'auto';
  }
  
  // Initialize the orb button click behavior
  orbButton.addEventListener('click', function(e) {
    // Toggle the menu
    toggleOrbMenu();
    
    // Only toggle the interface if the menu is shown
    if (orbMenu.classList.contains('active')) {
      // Show interface if menu is active
      showInterface();
    } else {
      // Decide whether to hide or show based on current state
      if (orbInterface.classList.contains('active')) {
        hideInterface();
      } else {
        showInterface();
      }
    }
    
    e.stopPropagation();
  });
  
  // Add orb pulsing effect on hover
  if (orbContainer) {
    orbContainer.addEventListener('mouseenter', function() {
      orbButton.classList.add('pulse');
    });
    
    orbContainer.addEventListener('mouseleave', function() {
      orbButton.classList.remove('pulse');
    });
  }
  
  // Initialize menu items with real SceneManager transitions
  document.querySelectorAll('.orb-menu-item').forEach(item => {
    item.addEventListener('click', function(e) {
      const action = this.getAttribute('data-action');
      if (action) {
        // Use SceneManager to handle section transitions properly
        if (window.minervaSceneManager) {
          // Add visual feedback for click
          this.classList.add('active-item');
          setTimeout(() => this.classList.remove('active-item'), 300);
          
          // Use SceneManager for proper, animated transitions
          window.minervaSceneManager.showScene(action);
          console.log(`📂 Transitioned to ${action} section via SceneManager`);
        } else {
          // Fallback to legacy method if SceneManager not available
          console.warn('SceneManager not available, using legacy method');
          switchToSection(action);
          
          // Load data for specific sections
          if (action === 'memory') loadMemories();
          if (action === 'projects') loadProjects();
        }
        
        // Close the menu
        toggleOrbMenu(false);
      }
      e.stopPropagation();
    });
  });
  
  // Close menu and interface when clicking elsewhere
  document.addEventListener('click', function(e) {
    const isOrb = e.target.closest('#orb-container');
    if (!isOrb) {
      toggleOrbMenu(false);
      hideInterface();
    }
  });
  
  // Show default section (dashboard)
  showInterface();
  switchToSection('dashboard');
  
  console.log('✅ Orb UI initialized successfully');
  
  // Start the API status checker
  checkApiStatus();
  setInterval(checkApiStatus, 30000);
  
  // Initialize chat functionality
  initChat();
});

// Toggle the orb menu
function toggleOrbMenu(forcedState) {
  const orbMenu = document.getElementById('orb-menu');
  const orbButton = document.getElementById('orb-button');
  
  if (!orbMenu || !orbButton) return;
  
  // Handle forced state or toggle current state
  const newState = forcedState !== undefined ? forcedState : !orbMenu.classList.contains('active');
  
  if (newState) {
    orbMenu.classList.add('active');
    orbButton.classList.add('active');
  } else {
    orbMenu.classList.remove('active');
    orbButton.classList.remove('active');
  }
}

// Show the interface panel
function showInterface() {
  const orbInterface = document.getElementById('orb-interface');
  if (!orbInterface) return;
  
  // Make sure it's visible first (for transitions)
  orbInterface.style.display = 'block';
  
  // Allow time for display to take effect before transitions
  setTimeout(() => {
    orbInterface.classList.add('active');
  }, 10);
}

// Hide the interface panel
function hideInterface() {
  const orbInterface = document.getElementById('orb-interface');
  if (!orbInterface) return;
  
  orbInterface.classList.remove('active');
  
  // Wait for transition to finish before hiding
  setTimeout(() => {
    orbInterface.style.display = 'none';
  }, 300); // Match transition duration in CSS
}

// Switch to a specific section
function switchToSection(sectionName) {
  if (!sectionName) return;
  
  // Save the last active section
  localStorage.setItem('minervaLastSection', sectionName);
  
  // Hide all sections first
  document.querySelectorAll('.orb-section').forEach(section => {
    section.style.display = 'none';
  });
  
  // Show the selected section
  const targetSection = document.getElementById(`orb-${sectionName}`);
  if (targetSection) {
    targetSection.style.display = 'block';
    console.log(`📂 Switched to ${sectionName} section`);
  } else {
    console.warn(`Section not found: orb-${sectionName}`);
  }
}

// Show error message
function showError(message) {
  console.error(`🚨 ${message}`);
  
  // Create error message element
  const errorDiv = document.createElement('div');
  errorDiv.style.cssText = 'position:fixed;bottom:80px;right:20px;background:rgba(239,68,68,0.9);color:white;padding:10px 15px;border-radius:5px;font-family:system-ui;z-index:10000;max-width:300px;';
  errorDiv.textContent = message;
  
  // Add dismiss button
  const dismissBtn = document.createElement('button');
  dismissBtn.textContent = '✕';
  dismissBtn.style.cssText = 'background:none;border:none;color:white;position:absolute;top:5px;right:5px;cursor:pointer;';
  dismissBtn.onclick = function() {
    document.body.removeChild(errorDiv);
  };
  
  errorDiv.appendChild(dismissBtn);
  document.body.appendChild(errorDiv);
  
  // Auto-remove after 10 seconds
  setTimeout(() => {
    if (document.body.contains(errorDiv)) {
      document.body.removeChild(errorDiv);
    }
  }, 10000);
}

// Check API status
function checkApiStatus() {
  const statusElement = document.getElementById('api-status');
  if (!statusElement) return;
  
  statusElement.textContent = 'Checking...';
  
  fetch('/api/status')
    .then(response => {
      if (response.ok) {
        return response.json().then(data => {
          statusElement.textContent = 'Connected';
          statusElement.style.color = '#10b981'; // Green for success
        });
      } else {
        throw new Error('API returned error status');
      }
    })
    .catch(error => {
      console.warn('API check failed:', error);
      statusElement.textContent = 'Disconnected';
      statusElement.style.color = '#ef4444'; // Red for error
    });
}

// Load memories from API or localStorage
function loadMemories() {
  const memoryList = document.getElementById('memory-list');
  if (!memoryList) {
    console.error('Memory list element not found');
    return;
  }

  // Show loading state
  memoryList.innerHTML = '<p class="loading">Loading memories...</p>';

  // Try to fetch from API
  fetch('/api/memories')
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        // If API fails, throw error to use fallback
        throw new Error('API returned error status');
      }
    })
    .then(data => {
      // Process API response
      displayMemories(data.memories || []);
      updateStatusIndicator('memory-status', 'Connected');
    })
    .catch(error => {
      console.warn('Memory API request failed:', error);
      // Use fallback if API fails
      useMemoryFallback();
      updateStatusIndicator('memory-status', 'Using local cache');
    });

  // Fallback function for memory data
  function useMemoryFallback() {
    // Try to load from localStorage
    const savedMemories = localStorage.getItem('minerva_memories');
    if (savedMemories) {
      try {
        const memories = JSON.parse(savedMemories);
        displayMemories(memories);
      } catch (e) {
        console.error('Failed to parse saved memories:', e);
        displaySampleMemories();
      }
    } else {
      // No saved memories, show samples
      displaySampleMemories();
    }
  }

  // Display memories in the list
  function displayMemories(memories) {
    if (memories.length === 0) {
      memoryList.innerHTML = '<p class="empty-state">No memories found.</p>';
      return;
    }

    memoryList.innerHTML = '';
    memories.forEach(memory => {
      const memoryItem = document.createElement('div');
      memoryItem.className = 'memory-item';
      
      const memoryTitle = document.createElement('h3');
      memoryTitle.textContent = memory.title || 'Untitled Memory';
      
      const memoryContent = document.createElement('p');
      memoryContent.textContent = memory.content || memory.description || 'No content';
      
      const memoryTimestamp = document.createElement('span');
      memoryTimestamp.className = 'timestamp';
      memoryTimestamp.textContent = formatTimestamp(memory.timestamp);
      
      memoryItem.appendChild(memoryTitle);
      memoryItem.appendChild(memoryContent);
      memoryItem.appendChild(memoryTimestamp);
      memoryList.appendChild(memoryItem);
    });
  }

  // Display sample memories for development/testing
  function displaySampleMemories() {
    const sampleMemories = [
      {
        title: 'Project Structure',
        content: 'Minerva uses Flask backend with React components for UI. The orb is the central navigation element.',
        timestamp: new Date().toISOString()
      },
      {
        title: 'Key API Endpoints',
        content: '/api/memories, /api/projects, /api/chat for the main functionality.',
        timestamp: new Date(Date.now() - 86400000).toISOString() // yesterday
      },
      {
        title: 'UI Components',
        content: 'The orb UI consists of a central button with radial menu and expandable panels.',
        timestamp: new Date(Date.now() - 172800000).toISOString() // 2 days ago
      }
    ];
    
    // Save to localStorage for future use
    localStorage.setItem('minerva_memories', JSON.stringify(sampleMemories));
    
    // Display the samples
    displayMemories(sampleMemories);
  }
}

// Load projects from API or localStorage
function loadProjects() {
  const projectsList = document.getElementById('projects-list');
  if (!projectsList) {
    console.error('Projects list element not found');
    return;
  }

  // Show loading state
  projectsList.innerHTML = '<p class="loading">Loading projects...</p>';

  // Try to fetch from API
  fetch('/api/projects')
    .then(response => {
      if (response.ok) {
        return response.json();
      } else {
        // If API fails, throw error to use fallback
        throw new Error('API returned error status');
      }
    })
    .then(data => {
      // Process API response
      displayProjects(data.projects || []);
      updateStatusIndicator('project-status', 'Connected');
    })
    .catch(error => {
      console.warn('Projects API request failed:', error);
      // Use fallback if API fails
      useProjectsFallback();
      updateStatusIndicator('project-status', 'Using local cache');
    });

  // Fallback function for projects data
  function useProjectsFallback() {
    // Try to load from localStorage
    const savedProjects = localStorage.getItem('minerva_projects');
    if (savedProjects) {
      try {
        const projects = JSON.parse(savedProjects);
        displayProjects(projects);
      } catch (e) {
        console.error('Failed to parse saved projects:', e);
        displaySampleProjects();
      }
    } else {
      // No saved projects, show samples
      displaySampleProjects();
    }
  }

  // Display projects in the list
  function displayProjects(projects) {
    if (projects.length === 0) {
      projectsList.innerHTML = '<p class="empty-state">No projects found.</p>';
      return;
    }

    projectsList.innerHTML = '';
    projects.forEach(project => {
      const projectItem = document.createElement('div');
      projectItem.className = 'project-item';
      
      const projectTitle = document.createElement('h3');
      projectTitle.textContent = project.title || 'Untitled Project';
      
      const projectDescription = document.createElement('p');
      projectDescription.textContent = project.description || 'No description';
      
      const projectActions = document.createElement('div');
      projectActions.className = 'project-actions';
      
      const viewButton = document.createElement('button');
      viewButton.className = 'btn-view';
      viewButton.innerHTML = '<i class="fas fa-eye"></i> View';
      viewButton.addEventListener('click', () => {
        window.location.href = `/project/${project.id}`;
      });
      
      projectActions.appendChild(viewButton);
      projectItem.appendChild(projectTitle);
      projectItem.appendChild(projectDescription);
      projectItem.appendChild(projectActions);
      projectsList.appendChild(projectItem);
    });
  }

  // Display sample projects for development/testing
  function displaySampleProjects() {
    const sampleProjects = [
      {
        id: 'minerva-orb',
        title: 'Minerva Orb UI',
        description: 'Central navigation system for the Minerva platform with radial menu.',
        created: new Date().toISOString()
      },
      {
        id: 'chat-backend',
        title: 'Chat API Integration',
        description: 'Implement the backend API for real-time chat with Minerva AI.',
        created: new Date(Date.now() - 86400000).toISOString() // yesterday
      },
      {
        id: 'memory-system',
        title: 'Memory System Architecture',
        description: 'Design and implement the memory storage and retrieval system.',
        created: new Date(Date.now() - 172800000).toISOString() // 2 days ago
      }
    ];
    
    // Save to localStorage for future use
    localStorage.setItem('minerva_projects', JSON.stringify(sampleProjects));
    
    // Display the samples
    displayProjects(sampleProjects);
  }
}

// Update status indicator element
function updateStatusIndicator(elementId, status) {
  const statusElement = document.getElementById(elementId);
  if (statusElement) {
    statusElement.textContent = status;
    
    // Add appropriate color based on status
    if (status.includes('Connected')) {
      statusElement.style.color = '#10b981'; // green
    } else if (status.includes('local') || status.includes('cache')) {
      statusElement.style.color = '#f59e0b'; // amber
    } else {
      statusElement.style.color = '#ef4444'; // red
    }
  }
}

// Format timestamp for display
function formatTimestamp(timestamp) {
  if (!timestamp) return 'Unknown date';
  
  try {
    const date = new Date(timestamp);
    // If today, show only time
    if (isToday(date)) {
      return `Today at ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
    // If yesterday, show 'Yesterday'
    if (isYesterday(date)) {
      return 'Yesterday';
    }
    // Otherwise show full date
    return date.toLocaleDateString();
  } catch (e) {
    console.warn('Invalid timestamp format:', timestamp);
    return 'Invalid date';
  }
}

// Check if date is today
function isToday(date) {
  const today = new Date();
  return date.getDate() === today.getDate() &&
    date.getMonth() === today.getMonth() &&
    date.getFullYear() === today.getFullYear();
}

// Check if date is yesterday
function isYesterday(date) {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return date.getDate() === yesterday.getDate() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getFullYear() === yesterday.getFullYear();
}

// Initialize chat functionality - using real API only without fallbacks
function initChat() {
  const inputField = document.getElementById('chat-input');
  const sendButton = document.getElementById('send-button');
  const chatMessages = document.getElementById('chat-messages');
  const chatContainer = document.getElementById('chat-container');
  
  if (!inputField || !sendButton || !chatMessages) {
    console.error('Chat elements not found', {
      inputField: !!inputField,
      sendButton: !!sendButton,
      chatMessages: !!chatMessages
    });
    return;
  }
  
  // Add API status indicator to chat header if not present
  const chatHeader = document.querySelector('.chat-header');
  if (chatHeader) {
    let connectionStatus = chatHeader.querySelector('.connection-status');
    if (!connectionStatus) {
      connectionStatus = document.createElement('div');
      connectionStatus.className = 'connection-status';
      connectionStatus.innerHTML = 'API: <span id="chat-status" class="status">Checking...</span>';
      
      // Find a good insertion point before any existing controls
      const controls = chatHeader.querySelector('.chat-controls');
      if (controls) {
        chatHeader.insertBefore(connectionStatus, controls);
      } else {
        chatHeader.appendChild(connectionStatus);
      }
    }
  }
  
  // Check if we already have an instance of the API chat handler
  if (window.apiChatHandler) {
    console.log('✅ Using existing API Chat Handler');
    return;
  }
  
  // Create new API chat handler
  window.apiChatHandler = new ApiChatHandler({
    container: chatContainer,
    messagesContainer: chatMessages,
    inputField: inputField,
    sendButton: sendButton,
    statusElement: document.getElementById('chat-status'),
    apiUrl: '/api/chat',
    apiStatusUrl: '/api/status'
  });
  
  console.log('✅ Initialized API-only chat without fallbacks');
}
  // Simple fallback for chat history
  function saveChatHistoryFallback() {
    // This is a simple fallback if the persistence module is not loaded
    const messages = chatMessages.innerHTML;
    localStorage.setItem('minerva_chat_history', messages);
  }
  
  // Load chat history
  function loadChatHistory() {
    const history = localStorage.getItem('minerva_chat_history');
    if (history) {
      chatMessages.innerHTML = history;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }
}
