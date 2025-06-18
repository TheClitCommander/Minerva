/**
 * Clean Orb UI Implementation - Building on our stable foundation
 * 
 * Implements Minerva Master Ruleset principles:
 * - Rule #1: Progressive Enhancement
 * - Rule #4: Graceful fallbacks
 * - Rule #5: UI visibility and responsiveness
 */

// Main initialization function
function initOrb() {
  console.log("🔄 Initializing Clean Minerva Orb UI...");
  
  // Find or create core elements
  ensureBaseElements();
  
  // Initialize components
  initOrbButton();
  initOrbMenu();
  initOrbInterface();
  
  // Start API status checker
  initApiStatus();
  
  console.log("✅ Clean Orb UI initialized");
}

// Ensure all base elements exist
function ensureBaseElements() {
  // Find or create orb container
  let orbContainer = document.getElementById('orb-container');
  if (!orbContainer) {
    console.warn("Creating missing orb-container element");
    orbContainer = document.createElement('div');
    orbContainer.id = 'orb-container';
    orbContainer.className = 'orb-container';
    document.body.appendChild(orbContainer);
  }
  
  // Find or create orb visualization
  let orbVis = document.getElementById('orb-visualization');
  if (!orbVis) {
    console.warn("Creating missing orb-visualization element");
    orbVis = document.createElement('div');
    orbVis.id = 'orb-visualization';
    orbVis.className = 'orb-visualization';
    orbContainer.appendChild(orbVis);
  }
  
  // Find or create orb interface
  let orbInterface = document.getElementById('orb-interface');
  if (!orbInterface) {
    console.warn("Creating missing orb-interface element");
    orbInterface = document.createElement('div');
    orbInterface.id = 'orb-interface';
    orbInterface.className = 'orb-interface';
    orbContainer.appendChild(orbInterface);
    
    // Create required sections
    const sections = [
      { id: 'orb-dashboard', title: 'Dashboard' },
      { id: 'orb-chat', title: 'Chat' },
      { id: 'orb-memory', title: 'Memory' },
      { id: 'orb-projects', title: 'Projects' }
    ];
    
    sections.forEach(section => {
      if (!document.getElementById(section.id)) {
        const sectionElem = document.createElement('div');
        sectionElem.id = section.id;
        sectionElem.className = 'orb-section';
        sectionElem.innerHTML = `<h2>${section.title}</h2><div class="${section.id.replace('orb-', '')}-content"></div>`;
        orbInterface.appendChild(sectionElem);
      }
    });
  }
}

// Initialize the orb button
function initOrbButton() {
  let orbVis = document.getElementById('orb-visualization');
  let orbButton = document.getElementById('orb-button');
  
  if (!orbVis) {
    console.error("Orb visualization container not found");
    return;
  }
  
  // Create button if missing
  if (!orbButton) {
    orbButton = document.createElement('div');
    orbButton.id = 'orb-button';
    orbButton.className = 'orb-button pulse';
    orbVis.appendChild(orbButton);
  }
  
  // Create rings for visual effect
  const ringCount = orbVis.querySelectorAll('.orb-ring').length;
  if (ringCount < 2) {
    // Remove existing rings
    orbVis.querySelectorAll('.orb-ring').forEach(r => r.remove());
    
    // Create two rings
    for (let i = 0; i < 2; i++) {
      const ring = document.createElement('div');
      ring.className = 'orb-ring';
      ring.style.animationDelay = i === 0 ? '0s' : '1s';
      orbVis.appendChild(ring);
    }
  }
  
  // Add click handler
  orbButton.addEventListener('click', function(e) {
    toggleOrbMenu();
    toggleInterface();
    e.stopPropagation();
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    const isOrb = e.target.closest('#orb-container');
    if (!isOrb) {
      const menu = document.getElementById('orb-menu');
      if (menu && menu.classList.contains('active')) {
        toggleOrbMenu(false);
      }
    }
  });
}

// Initialize the orb menu
function initOrbMenu() {
  let orbVis = document.getElementById('orb-visualization');
  let orbMenu = document.getElementById('orb-menu');
  
  if (!orbVis) {
    console.error("Orb visualization container not found");
    return;
  }
  
  // Create menu if missing
  if (!orbMenu) {
    orbMenu = document.createElement('div');
    orbMenu.id = 'orb-menu';
    orbMenu.className = 'orb-menu';
    orbVis.appendChild(orbMenu);
    
    // Create menu items
    const menuItems = [
      { action: 'dashboard', icon: 'fa-home', text: 'Dashboard' },
      { action: 'chat', icon: 'fa-comment-alt', text: 'Chat' },
      { action: 'memory', icon: 'fa-brain', text: 'Memory' },
      { action: 'projects', icon: 'fa-folder', text: 'Projects' }
    ];
    
    menuItems.forEach(item => {
      const menuItem = document.createElement('div');
      menuItem.className = 'orb-menu-item';
      menuItem.setAttribute('data-action', item.action);
      menuItem.innerHTML = `
        <i class="fas ${item.icon}"></i>
        <span>${item.text}</span>
      `;
      
      // Add click handler
      menuItem.addEventListener('click', function(e) {
        const action = this.getAttribute('data-action');
        if (action) {
          switchSection(action);
          toggleOrbMenu(false);
        }
        e.stopPropagation();
      });
      
      orbMenu.appendChild(menuItem);
    });
  } else {
    // Add click handlers to existing menu items
    orbMenu.querySelectorAll('.orb-menu-item').forEach(item => {
      item.addEventListener('click', function(e) {
        const action = this.getAttribute('data-action');
        if (action) {
          switchSection(action);
          toggleOrbMenu(false);
        }
        e.stopPropagation();
      });
    });
  }
}

// Initialize the orb interface
function initOrbInterface() {
  const orbInterface = document.getElementById('orb-interface');
  if (!orbInterface) {
    console.error("Orb interface not found");
    return;
  }
  
  // Set default active section
  const lastSection = localStorage.getItem('minervaLastSection') || 'dashboard';
  switchSection(lastSection);
}

// Toggle the orb menu
function toggleOrbMenu(forcedState) {
  const orbMenu = document.getElementById('orb-menu');
  const orbButton = document.getElementById('orb-button');
  
  if (!orbMenu || !orbButton) {
    console.error("Orb menu elements not found");
    return;
  }
  
  // If forcedState is provided, use it; otherwise toggle
  const newState = (forcedState !== undefined) 
    ? forcedState 
    : !orbMenu.classList.contains('active');
  
  if (newState) {
    orbMenu.classList.add('active');
    orbButton.classList.add('active');
  } else {
    orbMenu.classList.remove('active');
    orbButton.classList.remove('active');
  }
}

// Toggle the interface visibility
function toggleInterface() {
  const orbInterface = document.getElementById('orb-interface');
  
  if (!orbInterface) {
    console.error("Orb interface not found");
    return;
  }
  
  if (orbInterface.classList.contains('active')) {
    orbInterface.classList.remove('active');
    setTimeout(() => {
      orbInterface.style.display = 'none';
    }, 300); // Match transition duration in CSS
  } else {
    orbInterface.style.display = 'block';
    setTimeout(() => {
      orbInterface.classList.add('active');
    }, 10);
  }
}

// Switch between sections
function switchSection(target) {
  if (!target) return;
  
  // Store selected section
  localStorage.setItem('minervaLastSection', target);
  
  // Hide all sections
  document.querySelectorAll('.orb-section').forEach(section => {
    section.style.display = 'none';
  });
  
  // Show target section
  const targetSection = document.getElementById(`orb-${target}`);
  if (targetSection) {
    targetSection.style.display = 'block';
  } else {
    console.warn(`Section ${target} not found`);
  }
}

// Initialize API status checker
function initApiStatus() {
  // Create or find status indicator
  let statusElem = document.querySelector('.minerva-status');
  
  if (!statusElem) {
    statusElem = document.createElement('div');
    statusElem.className = 'minerva-status';
    document.getElementById('orb-container')?.appendChild(statusElem);
  }
  
  // Check API status initially and every 30 seconds
  checkApiStatus();
  setInterval(checkApiStatus, 30000);
}

// Check API status
function checkApiStatus() {
  fetch('/api/status', { method: 'GET' })
    .then(response => {
      if (!response.ok) throw new Error('API server not responding');
      return response.json();
    })
    .then(data => {
      updateStatus('online', 'API Connected');
    })
    .catch(error => {
      console.warn('API check failed:', error);
      updateStatus('offline', 'API Disconnected');
    });
}

// Update status indicator
function updateStatus(status, message) {
  const statusElem = document.querySelector('.minerva-status');
  if (!statusElem) return;
  
  // Update class and content
  statusElem.className = `minerva-status ${status}`;
  statusElem.innerHTML = `
    <span class="status-icon"></span>
    <span class="status-text">${message}</span>
  `;
  
  // Dispatch event for other components
  window.dispatchEvent(new CustomEvent('minerva-status-change', {
    detail: { status, message }
  }));
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', initOrb);

// Fallback init for when DOMContentLoaded has already fired
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  setTimeout(initOrb, 100);
}
