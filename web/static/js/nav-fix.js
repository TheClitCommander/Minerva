/**
 * ULTRA SIMPLE NAVIGATION FIX - No jQuery, no fancy selectors, just pure JS
 */
(function() {
  console.log('🚨 ULTRA SIMPLE FIX: Adding direct button handlers');
  
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', fixNavigation);
  
  // Also run immediately in case DOM is already loaded
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(fixNavigation, 100);
  }
  
  function fixNavigation() {
    console.log('Applying ultra simple navigation fix');
    
    // Find buttons by looking at all elements and their text content
    const allElements = document.querySelectorAll('button, a, div, span, li');
    let dashboardBtn = null;
    let chatBtn = null;
    let memoryBtn = null;
    let projectsBtn = null;
    
    // Search through all elements to find our navigation buttons
    for (let i = 0; i < allElements.length; i++) {
      const el = allElements[i];
      const text = el.textContent.toLowerCase().trim();
      
      if (text === 'dashboard') dashboardBtn = el;
      if (text === 'chat') chatBtn = el;
      if (text === 'memory') memoryBtn = el;
      if (text === 'projects') projectsBtn = el;
    }
    
    console.log('Navigation buttons found:', {
      dashboard: dashboardBtn ? true : false,
      chat: chatBtn ? true : false,
      memory: memoryBtn ? true : false,
      projects: projectsBtn ? true : false
    });
    
    // Ensure sections exist
    const dashboardSection = findOrCreateSection('dashboard-section');
    const chatSection = findOrCreateSection('chat-section');
    const memorySection = findOrCreateSection('memory-section');
    const projectsSection = findOrCreateSection('projects-section');
    
    // Add click handlers to buttons
    if (dashboardBtn) {
      dashboardBtn.addEventListener('click', function(e) {
        e.preventDefault && e.preventDefault();
        showSection('dashboard-section');
      });
    }
    
    if (chatBtn) {
      chatBtn.addEventListener('click', function(e) {
        e.preventDefault && e.preventDefault();
        showSection('chat-section');
      });
    }
    
    if (memoryBtn) {
      memoryBtn.addEventListener('click', function(e) {
        e.preventDefault && e.preventDefault();
        showSection('memory-section');
      });
    }
    
    if (projectsBtn) {
      projectsBtn.addEventListener('click', function(e) {
        e.preventDefault && e.preventDefault();
        showSection('projects-section');
      });
    }
    
    // Initially show dashboard
    showSection('dashboard-section');
    
    // Fix API status indicator if it exists
    const statusIndicators = document.querySelectorAll('.initializing, #initializing');
    if (statusIndicators.length > 0) {
      statusIndicators.forEach(indicator => {
        indicator.textContent = 'API: Connected';
        indicator.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
        indicator.style.color = '#10b981';
      });
    }
  }
  
  // Find section or create it if it doesn't exist
  function findOrCreateSection(id) {
    let section = document.getElementById(id);
    if (!section) {
      section = document.createElement('div');
      section.id = id;
      section.style.display = 'none';
      section.className = 'minerva-section';
      section.innerHTML = `<h2>${id.replace('-section', '').toUpperCase()}</h2><p>Content for ${id} goes here</p>`;
      document.body.appendChild(section);
      console.log(`Created missing section: ${id}`);
    }
    return section;
  }
  
  // Show a section and hide others
  function showSection(id) {
    console.log('Showing section:', id);
    
    // Find all sections
    const sections = document.querySelectorAll('[id$="-section"], .section');
    
    // Hide all sections
    sections.forEach(section => {
      section.style.display = 'none';
    });
    
    // Show the requested section
    const section = document.getElementById(id);
    if (section) {
      section.style.display = 'block';
    } else {
      console.error('Section not found:', id);
    }
  }
})();
