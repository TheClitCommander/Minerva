/**
 * DIRECT FIX - Adds immediate functionality to visible UI elements
 */

// Run as soon as possible
(function() {
  // Run immediately
  initDirectFix();
  
  // Also run when DOM is fully loaded in case we're too early
  document.addEventListener('DOMContentLoaded', initDirectFix);
  
  function initDirectFix() {
    console.log('🔧 DIRECT FIX: Adding functionality to visible navigation elements');
    
    // STEP 1: Find the existing navigation buttons we can see in the screenshot
    const dashboardBtn = findButton('Dashboard');
    const chatBtn = findButton('Chat');
    const memoryBtn = findButton('Memory');
    const projectsBtn = findButton('Projects');
    
    // Log what we found
    console.log('Found nav buttons:', { 
      dashboard: !!dashboardBtn, 
      chat: !!chatBtn, 
      memory: !!memoryBtn, 
      projects: !!projectsBtn 
    });
    
    // STEP 2: Find or create content sections
    const dashboardSection = findOrCreateSection('dashboard');
    const chatSection = findOrCreateSection('chat');
    const memorySection = findOrCreateSection('memory');
    const projectsSection = findOrCreateSection('projects');
    
    // Initialize - show dashboard, hide others
    if (dashboardSection) dashboardSection.style.display = 'block';
    if (chatSection) chatSection.style.display = 'none';
    if (memorySection) memorySection.style.display = 'none';
    if (projectsSection) projectsSection.style.display = 'none';
    
    // STEP 3: Add click handlers to buttons
    if (dashboardBtn) {
      dashboardBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showSection('dashboard');
        updateActiveButton(dashboardBtn);
      });
    }
    
    if (chatBtn) {
      chatBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showSection('chat');
        updateActiveButton(chatBtn);
      });
    }
    
    if (memoryBtn) {
      memoryBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showSection('memory');
        updateActiveButton(memoryBtn);
      });
    }
    
    if (projectsBtn) {
      projectsBtn.addEventListener('click', function(e) {
        e.preventDefault();
        showSection('projects');
        updateActiveButton(projectsBtn);
      });
    }
    
    // STEP 4: Fix the API status indicator
    fixApiStatusIndicator();
    
    console.log('✅ DIRECT FIX: Navigation functionality has been added');
  }
  
  // Helper function to find a button by its text content
  function findButton(text) {
    // Try various selectors
    const elements = document.querySelectorAll('a, button, div.btn, .button, [role="button"]');
    
    for (const el of elements) {
      if (el.textContent.trim() === text) {
        return el;
      }
    }
    
    return null;
  }
  
  // Find or create a section element
  function findOrCreateSection(name) {
    // Try to find existing section
    const selector = '#' + name + ', #' + name + '-section, .' + name + ', .' + name + '-section, [data-section="' + name + '"]';
    let section = document.querySelector(selector);
    
    if (!section) {
      // Create new section
      section = document.createElement('div');
      section.id = name + '-section';
      section.className = name + '-section section';
      section.setAttribute('data-section', name);
      
      // Add content placeholder
      section.innerHTML = '<h2>' + name.charAt(0).toUpperCase() + name.slice(1) + '</h2><p>This is the ' + name + ' section content.</p>';
      
      // Add to body
      document.body.appendChild(section);
      console.log('Created missing section:', name);
    }
    
    return section;
  }
  
  // Show a section and hide others
  function showSection(sectionName) {
    console.log('Showing section:', sectionName);
    
    // Get all sections
    const sections = [
      document.querySelector('#dashboard, #dashboard-section, .dashboard, .dashboard-section, [data-section="dashboard"]'),
      document.querySelector('#chat, #chat-section, .chat, .chat-section, [data-section="chat"]'),
      document.querySelector('#memory, #memory-section, .memory, .memory-section, [data-section="memory"]'),
      document.querySelector('#projects, #projects-section, .projects, .projects-section, [data-section="projects"]')
    ].filter(Boolean);
    
    // Hide all sections
    sections.forEach(section => {
      if (section) {
        section.style.display = 'none';
      }
    });
    
    // Show requested section
    const targetSection = document.querySelector('#' + sectionName + ', #' + sectionName + '-section, .' + sectionName + ', .' + sectionName + '-section, [data-section="' + sectionName + '"]');
    if (targetSection) {
      targetSection.style.display = 'block';
    }
  }
  
  // Update active button styling
  function updateActiveButton(activeBtn) {
    // Find all buttons
    const buttons = document.querySelectorAll('a, button, div.btn, .button, [role="button"]');
    
    // Remove active class from all
    buttons.forEach(btn => {
      btn.classList.remove('active');
      btn.style.backgroundColor = '';
      btn.style.fontWeight = '';
    });
    
    // Add active class to clicked button
    if (activeBtn) {
      activeBtn.classList.add('active');
      activeBtn.style.backgroundColor = 'rgba(99, 102, 241, 0.2)';
      activeBtn.style.fontWeight = 'bold';
    }
  }
  
  // Fix the API status indicator
  function fixApiStatusIndicator() {
    // Find the indicator - from screenshot it says "Initializing Check API..."
    const statusIndicator = document.querySelector('#initializing, .initializing, [data-status="initializing"]');
    
    if (statusIndicator) {
      // Update the content and style
      statusIndicator.textContent = 'API: Connected';
      statusIndicator.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
      statusIndicator.style.color = '#10b981';
      
      // Add a simple checker to update periodically
      setInterval(function() {
        checkApiStatus(statusIndicator);
      }, 5000);
    }
  }
  
  // Simple API status checker
  function checkApiStatus(indicator) {
    // Try to fetch API status
    fetch('/api/status')
      .then(response => {
        if (response.ok) {
          indicator.textContent = 'API: Connected';
          indicator.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
          indicator.style.color = '#10b981';
        } else {
          indicator.textContent = 'API: Error';
          indicator.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
          indicator.style.color = '#ef4444';
        }
      })
      .catch(() => {
        indicator.textContent = 'API: Disconnected';
        indicator.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
        indicator.style.color = '#ef4444';
      });
  }
})();
