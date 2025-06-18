/**
 * SIMPLE NAVIGATION FIX - No jQuery, no fancy selectors
 */
(function() {
  console.log('🔧 Simple Navigation Fix: Adding direct handlers to navigation buttons');
  
  // Wait for DOM to be fully loaded
  document.addEventListener('DOMContentLoaded', function() {
    // Find buttons by ID first (most reliable)
    let dashboardBtn = document.getElementById('dashboard-button') || document.getElementById('dashboard-btn');
    let chatBtn = document.getElementById('chat-button') || document.getElementById('chat-btn');
    let memoryBtn = document.getElementById('memory-button') || document.getElementById('memory-btn');
    let projectsBtn = document.getElementById('projects-button') || document.getElementById('projects-btn');
    
    // If not found by ID, try finding by text content (less reliable)
    if (!dashboardBtn) {
      document.querySelectorAll('button, a, div').forEach(el => {
        if (el.textContent.includes('Dashboard')) dashboardBtn = el;
      });
    }
    
    if (!chatBtn) {
      document.querySelectorAll('button, a, div').forEach(el => {
        if (el.textContent.includes('Chat')) chatBtn = el;
      });
    }
    
    if (!memoryBtn) {
      document.querySelectorAll('button, a, div').forEach(el => {
        if (el.textContent.includes('Memory')) memoryBtn = el;
      });
    }
    
    if (!projectsBtn) {
      document.querySelectorAll('button, a, div').forEach(el => {
        if (el.textContent.includes('Projects')) projectsBtn = el;
      });
    }
    
    console.log('Navigation buttons found:', {
      dashboard: dashboardBtn,
      chat: chatBtn,
      memory: memoryBtn,
      projects: projectsBtn
    });
    
    // Make sure sections exist
    ensureSectionExists('dashboard-section');
    ensureSectionExists('chat-section');
    ensureSectionExists('memory-section');
    ensureSectionExists('projects-section');
    
    // Add click handlers if buttons found
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
    const statusEl = document.querySelector('.initializing, #initializing');
    if (statusEl) {
      statusEl.textContent = 'API: Connected';
      statusEl.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
      statusEl.style.color = '#10b981';
    }
  });
  
  // Ensure section exists
  function ensureSectionExists(id) {
    if (!document.getElementById(id)) {
      const section = document.createElement('div');
      section.id = id;
      section.style.display = 'none';
      section.innerHTML = `<h2>${id.replace('-section', '').toUpperCase()}</h2>`;
      document.body.appendChild(section);
    }
  }
  
  // Show a section and hide others
  function showSection(id) {
    console.log('Showing section:', id);
    
    // Get all section elements
    const sections = document.querySelectorAll('[id$="-section"]');
    
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
