/**
 * Minerva SceneManager - DIRECT DOM IMPLEMENTATION
 * This manager works with the actual DOM structure, not an idealized version
 */

class SceneManager {
  constructor() {
    // Core sections based on actual DOM
    this.sections = {};
    this.activeSection = null;
    this.initialized = false;
    
    // Initialize once DOM is loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initialize());
    } else {
      this.initialize();
    }
  }

  /**
   * Find all sections in the DOM and initialize the manager
   */
  initialize() {
    console.log('🔍 SceneManager: Scanning DOM for sections...');
    
    // Find sections based on various patterns we've seen in the DOM
    // This handles both section-* and *-section naming conventions
    const sectionSelectors = [
      '.dashboard-section, .chat-section, .memory-section, .projects-section',
      '#dashboard-section, #chat-section, #memory-section, #projects-section',
      '#dashboard, #chat, #memory, #projects',
      '[data-section=dashboard], [data-section=chat], [data-section=memory], [data-section=projects]'
    ];
    
    // Try all selector patterns
    let foundSections = [];
    for (const selector of sectionSelectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        foundSections = Array.from(elements);
        console.log(`✅ Found ${elements.length} sections using selector: ${selector}`);
        break;
      }
    }
    
    // If we still didn't find sections, try more aggressive approaches
    if (foundSections.length === 0) {
      // Look for any element that might be a section based on its ID or class
      const potentialSections = document.querySelectorAll('[id*=section], [id*=dashboard], [id*=chat], [id*=memory], [id*=projects], [class*=section]');
      if (potentialSections.length > 0) {
        foundSections = Array.from(potentialSections);
        console.log(`⚠️ Using fallback section detection: found ${potentialSections.length} potential sections`);
      } else {
        console.error('❌ No sections found in DOM using any detection method');
      }
    }
    
    // Process found sections
    foundSections.forEach(section => {
      const id = this.getSectionId(section);
      if (id) {
        this.sections[id] = section;
        // Initially hide all sections except dashboard
        if (id !== 'dashboard') {
          section.style.display = 'none';
        } else {
          // Make dashboard visible
          section.style.display = 'block';
          this.activeSection = 'dashboard';
        }
      }
    });
    
    console.log('📊 Registered sections:', Object.keys(this.sections));
    
    // Initialize menu items
    this.initMenuItems();
    
    // Set initialization flag
    this.initialized = true;
    
    // Dispatch event that sceneManager is ready
    window.dispatchEvent(new CustomEvent('scene-manager-ready', {
      detail: { 
        manager: this,
        sections: Object.keys(this.sections)
      }
    }));
  }
  
  /**
   * Get the section ID from an element based on various patterns
   */
  getSectionId(element) {
    // Try to determine section type from ID first
    const idPatterns = [
      /^(\w+)-section$/, // matches "dashboard-section"
      /^section-(\w+)$/, // matches "section-dashboard"
      /^(\w+)$/ // matches just "dashboard"
    ];
    
    for (const pattern of idPatterns) {
      const match = element.id ? element.id.match(pattern) : null;
      if (match && match[1]) {
        // Convert to standard format
        const id = match[1].toLowerCase();
        if (['dashboard', 'chat', 'memory', 'projects'].includes(id)) {
          return id;
        }
      }
    }
    
    // Try data attributes
    if (element.dataset && element.dataset.section) {
      return element.dataset.section.toLowerCase();
    }
    
    // Try classes
    if (element.classList) {
      for (const cls of element.classList) {
        if (cls.endsWith('-section')) {
          const id = cls.replace('-section', '');
          if (['dashboard', 'chat', 'memory', 'projects'].includes(id)) {
            return id;
          }
        }
        
        // Direct match to main section types
        if (['dashboard', 'chat', 'memory', 'projects'].includes(cls)) {
          return cls;
        }
      }
    }
    
    // Fallback: check if element contains any identifiable content
    const sectionTypes = ['dashboard', 'chat', 'memory', 'projects'];
    for (const type of sectionTypes) {
      if (element.innerHTML.toLowerCase().includes(type)) {
        console.log(`⚠️ Using content-based section detection for "${type}"`);
        return type;
      }
    }
    
    return null;
  }
  
  /**
   * Initialize menu item click handlers
   */
  initMenuItems() {
    console.log('🔍 SceneManager: Finding menu items...');
    
    // Look for menu items with various selectors
    const menuSelectors = [
      '.orb-menu-item',
      '[data-action]',
      'a[href="#dashboard"], a[href="#chat"], a[href="#memory"], a[href="#projects"]',
      'button[data-section], a[data-section]',
      '#orb-menu .menu-item, .orb-menu .menu-item'
    ];
    
    let menuItems = [];
    for (const selector of menuSelectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        menuItems = Array.from(elements);
        console.log(`✅ Found ${elements.length} menu items using selector: ${selector}`);
        break;
      }
    }
    
    // If we still don't have menu items, try more aggressive approaches
    if (menuItems.length === 0) {
      // Find any clickable element that might be a menu item
      const clickables = document.querySelectorAll('a, button');
      const potentialMenuItems = Array.from(clickables).filter(el => {
        const text = el.textContent.toLowerCase();
        return text.includes('dashboard') || text.includes('chat') || 
               text.includes('memory') || text.includes('projects');
      });
      
      if (potentialMenuItems.length > 0) {
        menuItems = potentialMenuItems;
        console.log(`⚠️ Using fallback menu detection: found ${potentialMenuItems.length} potential menu items`);
      } else {
        console.error('❌ No menu items found in DOM using any detection method');
      }
    }
    
    // Add click handlers to menu items
    menuItems.forEach(item => {
      // Try to determine which section this menu item corresponds to
      const action = item.getAttribute('data-action') || 
                     item.getAttribute('data-section') ||
                     item.getAttribute('href')?.replace('#', '');
      
      // Determine section from content if no data attributes present
      let section = action;
      if (!section) {
        const text = item.textContent.toLowerCase();
        if (text.includes('dashboard')) section = 'dashboard';
        else if (text.includes('chat')) section = 'chat';
        else if (text.includes('memory')) section = 'memory';
        else if (text.includes('projects')) section = 'projects';
      }
      
      if (section) {
        // Store section on the element
        item.setAttribute('data-section', section);
        
        // Add click handler
        item.addEventListener('click', (e) => {
          e.preventDefault();
          this.showSection(section);
          return false;
        });
        
        console.log(`✅ Added click handler for ${section} menu item`);
      }
    });
  }
  
  /**
   * Show a specific section and hide others
   */
  showSection(sectionId) {
    if (!this.initialized) {
      console.warn('⚠️ SceneManager not yet initialized');
      // Queue the action for after initialization
      window.addEventListener('scene-manager-ready', () => {
        this.showSection(sectionId);
      }, { once: true });
      return;
    }
    
    console.log(`🔄 Switching to section: ${sectionId}`);
    
    // Check if the section exists
    if (!this.sections[sectionId]) {
      console.error(`❌ Section "${sectionId}" not found`);
      return;
    }
    
    // Hide all sections
    Object.entries(this.sections).forEach(([id, section]) => {
      if (id !== sectionId) {
        // Apply transition out
        section.style.opacity = '0';
        section.style.transform = 'translateY(10px)';
        
        // Hide after transition
        setTimeout(() => {
          section.style.display = 'none';
        }, 300);
      }
    });
    
    // Show the selected section
    const section = this.sections[sectionId];
    section.style.display = 'block';
    section.style.opacity = '0';
    section.style.transform = 'translateY(10px)';
    
    // Trigger reflow to ensure transition applies
    void section.offsetWidth;
    
    // Apply transition in
    section.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    section.style.opacity = '1';
    section.style.transform = 'translateY(0)';
    
    // Update active section
    this.activeSection = sectionId;
    
    // Update menu item styles
    this.updateMenuStyles(sectionId);
    
    // Dispatch event that section changed
    window.dispatchEvent(new CustomEvent('section-changed', {
      detail: { section: sectionId }
    }));
    
    // Save to localStorage for persistence
    localStorage.setItem('minerva_active_section', sectionId);
    
    console.log(`✅ Section "${sectionId}" is now active`);
  }
  
  /**
   * Update menu item styles to reflect active section
   */
  updateMenuStyles(activeSection) {
    // Find all menu items
    const menuItems = document.querySelectorAll('[data-section]');
    
    menuItems.forEach(item => {
      const section = item.getAttribute('data-section');
      
      if (section === activeSection) {
        item.classList.add('active');
        // Add additional active styles
        item.style.fontWeight = 'bold';
        item.style.backgroundColor = 'rgba(99, 102, 241, 0.2)';
      } else {
        item.classList.remove('active');
        // Remove active styles
        item.style.fontWeight = '';
        item.style.backgroundColor = '';
      }
    });
  }
  
  /**
   * Get the active section
   */
  getActiveSection() {
    return this.activeSection;
  }
  
  /**
   * Restore the last active section from localStorage
   */
  restoreLastSection() {
    const lastSection = localStorage.getItem('minerva_active_section');
    if (lastSection && this.sections[lastSection]) {
      this.showSection(lastSection);
    }
  }
}

// Initialize the SceneManager
window.minervaSceneManager = new SceneManager();

// Make it globally available
console.log('🚀 SceneManager initialized and globally available as window.minervaSceneManager');
