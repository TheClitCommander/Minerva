/**
 * Minerva OrbMenuHandler
 * Directly connects the orb menu items to the SceneManager with visual feedback
 */

class OrbMenuHandler {
  constructor() {
    // Core elements based on what's actually in the DOM
    this.orbContainer = null;
    this.orbButton = null;
    this.orbMenu = null;
    this.menuItems = [];
    this.isMenuOpen = false;
    
    // Initialize once DOM is loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initialize());
    } else {
      this.initialize();
    }
  }
  
  /**
   * Initialize the orb menu handler
   */
  initialize() {
    console.log('🔍 OrbMenuHandler: Finding orb elements...');
    
    // Find the orb container using various selectors based on the screenshot
    const orbContainerSelectors = [
      '#orb-container',
      '.orb-container',
      '.minerva-orbital-ui'
    ];
    
    // Find the first matching element
    for (const selector of orbContainerSelectors) {
      const element = document.querySelector(selector);
      if (element) {
        this.orbContainer = element;
        console.log(`✅ Found orb container with selector: ${selector}`);
        break;
      }
    }
    
    // If we still don't have a container, use more aggressive approaches
    if (!this.orbContainer) {
      // Try to find by content or structure
      document.querySelectorAll('div').forEach(div => {
        if (div.querySelector('button, a') && 
            (div.innerHTML.includes('orb') || div.innerHTML.includes('Dashboard') || 
             div.innerHTML.includes('Chat') || div.innerHTML.includes('Memory') ||
             div.innerHTML.includes('Projects'))) {
          this.orbContainer = div;
          console.log('⚠️ Using fallback container detection based on content');
        }
      });

      // If all else fails, create a container
      if (!this.orbContainer) {
        const nav = document.querySelector('nav');
        if (nav) {
          this.orbContainer = nav;
          console.log('⚠️ Using navigation element as orb container');
        } else {
          console.error('❌ No orb container found in DOM. Creating one...');
          this.orbContainer = document.createElement('div');
          this.orbContainer.id = 'orb-container';
          this.orbContainer.className = 'orb-container';
          document.body.appendChild(this.orbContainer);
        }
      }
    }
    
    // Find the orb button
    this.orbButton = this.orbContainer.querySelector('#orb-button, .orb-button, button');
    if (!this.orbButton) {
      console.log('⚠️ No orb button found, using first clickable element');
      this.orbButton = this.orbContainer.querySelector('a, button, [role="button"]');
    }
    
    // Find the orb menu - look for a list of navigation items
    this.orbMenu = this.orbContainer.querySelector('#orb-menu, .orb-menu, ul, nav');
    
    // If we can't find a menu, the container might be the menu
    if (!this.orbMenu && this.orbContainer.querySelectorAll('a, button').length > 1) {
      this.orbMenu = this.orbContainer;
      console.log('⚠️ Using container as menu since it contains multiple clickable elements');
    }
    
    // Find menu items directly from the screenshot - based on the actual menu buttons shown
    this.menuItems = Array.from(document.querySelectorAll('.btn-dashboard, .btn-chat, .btn-memory, .btn-projects'));
    
    // If no specific classes, find by content
    if (this.menuItems.length === 0) {
      // Find all menu items based on content
      const allClickables = document.querySelectorAll('a, button, [role="button"]');
      this.menuItems = Array.from(allClickables).filter(el => {
        const text = el.textContent.toLowerCase();
        return text.includes('dashboard') || text.includes('chat') || 
               text.includes('memory') || text.includes('projects');
      });
      
      console.log(`✅ Found ${this.menuItems.length} menu items based on content`);
    }
    
    // Set data attributes for all menu items
    this.menuItems.forEach(item => {
      const text = item.textContent.toLowerCase();
      let section = null;
      
      if (text.includes('dashboard')) section = 'dashboard';
      else if (text.includes('chat')) section = 'chat';
      else if (text.includes('memory')) section = 'memory';
      else if (text.includes('projects')) section = 'projects';
      
      if (section) {
        item.setAttribute('data-section', section);
      }
    });
    
    // Apply initial menu styles
    this.applyMenuStyles();
    
    // Set up click handlers
    this.setupClickHandlers();
    
    // Set up hover animations for orb
    this.setupOrbAnimations();
    
    console.log('✅ OrbMenuHandler initialized with', this.menuItems.length, 'menu items');
  }
  
  /**
   * Apply initial menu styles for better visual feedback
   */
  applyMenuStyles() {
    // Ensure the orb button has proper styling
    if (this.orbButton) {
      // Add styles only if it doesn't already have them
      if (!this.orbButton.style.transition) {
        this.orbButton.style.transition = 'all 0.3s ease';
      }
      
      // Add cursor pointer if not set
      if (this.orbButton.style.cursor !== 'pointer') {
        this.orbButton.style.cursor = 'pointer';
      }
    }
    
    // Style menu items for better interaction
    this.menuItems.forEach(item => {
      // Only add styles if not already styled
      if (!item.style.transition) {
        item.style.transition = 'all 0.2s ease';
      }
      
      if (item.style.cursor !== 'pointer') {
        item.style.cursor = 'pointer';
      }
    });
    
    // Handle menu item hover effects
    this.menuItems.forEach(item => {
      item.addEventListener('mouseenter', () => {
        item.style.transform = 'scale(1.05)';
        item.style.backgroundColor = 'rgba(99, 102, 241, 0.1)';
      });
      
      item.addEventListener('mouseleave', () => {
        item.style.transform = 'scale(1)';
        // Only remove background if not active
        if (!item.classList.contains('active')) {
          item.style.backgroundColor = '';
        }
      });
    });
  }
  
  /**
   * Set up click handlers for menu interaction
   */
  setupClickHandlers() {
    // Handle orb button click
    if (this.orbButton) {
      this.orbButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleMenu();
        return false;
      });
    }
    
    // Handle menu item clicks
    this.menuItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Get section from data attribute
        const section = item.getAttribute('data-section');
        
        if (section) {
          // Switch to this section using SceneManager
          if (window.minervaSceneManager) {
            window.minervaSceneManager.showSection(section);
            
            // Close menu after selection
            if (this.isMenuOpen) {
              this.toggleMenu(false);
            }
            
            // Update active state
            this.updateActiveMenuItem(section);
          } else {
            console.error('❌ SceneManager not available');
          }
        }
        
        return false;
      });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (this.isMenuOpen && 
          !this.orbContainer.contains(e.target) && 
          !this.orbButton.contains(e.target) && 
          (!this.orbMenu || !this.orbMenu.contains(e.target))) {
        this.toggleMenu(false);
      }
    });
    
    // Listen for section changes from SceneManager
    window.addEventListener('section-changed', (e) => {
      if (e.detail && e.detail.section) {
        this.updateActiveMenuItem(e.detail.section);
      }
    });
  }
  
  /**
   * Update the active menu item based on the current section
   */
  updateActiveMenuItem(activeSection) {
    this.menuItems.forEach(item => {
      const section = item.getAttribute('data-section');
      
      if (section === activeSection) {
        item.classList.add('active');
        item.style.fontWeight = 'bold';
        item.style.backgroundColor = 'rgba(99, 102, 241, 0.2)';
      } else {
        item.classList.remove('active');
        item.style.fontWeight = '';
        item.style.backgroundColor = '';
      }
    });
  }
  
  /**
   * Toggle the orb menu visibility
   */
  toggleMenu(state = null) {
    // If state is provided, use it, otherwise toggle
    const shouldShow = state !== null ? state : !this.isMenuOpen;
    
    if (shouldShow) {
      // Show menu
      if (this.orbMenu && this.orbMenu !== this.orbContainer) {
        this.orbMenu.style.display = 'block';
        // Trigger animation
        setTimeout(() => {
          this.orbMenu.style.opacity = '1';
          this.orbMenu.style.transform = 'scale(1)';
        }, 10);
      }
      
      // Apply active class to the orb button
      if (this.orbButton) {
        this.orbButton.classList.add('active');
      }
      
      // Animate menu items in sequence
      this.menuItems.forEach((item, index) => {
        setTimeout(() => {
          item.style.opacity = '1';
          item.style.transform = 'translateY(0)';
        }, 50 * index);
      });
      
      this.isMenuOpen = true;
    } else {
      // Hide menu
      if (this.orbMenu && this.orbMenu !== this.orbContainer) {
        this.orbMenu.style.opacity = '0';
        this.orbMenu.style.transform = 'scale(0.95)';
        setTimeout(() => {
          this.orbMenu.style.display = 'none';
        }, 300);
      }
      
      // Remove active class from orb button
      if (this.orbButton) {
        this.orbButton.classList.remove('active');
      }
      
      // Hide menu items
      this.menuItems.forEach(item => {
        item.style.opacity = '0.7';
        item.style.transform = 'translateY(10px)';
      });
      
      this.isMenuOpen = false;
    }
  }
  
  /**
   * Set up hover animations for the orb
   */
  setupOrbAnimations() {
    if (this.orbButton) {
      this.orbButton.addEventListener('mouseenter', () => {
        this.orbButton.classList.add('pulse');
      });
      
      this.orbButton.addEventListener('mouseleave', () => {
        this.orbButton.classList.remove('pulse');
      });
    }
  }
}

// Initialize the orb menu handler
window.orbMenuHandler = new OrbMenuHandler();

// Export for module usage
console.log('🚀 OrbMenuHandler initialized and globally available as window.orbMenuHandler');
