/**
 * Minerva API Status Checker
 * Monitors API connections and visibly updates status indicators
 */

class ApiStatusChecker {
  constructor() {
    this.statusIndicators = [];
    this.isConnected = false;
    this.lastCheck = null;
    this.checkInterval = null;
    
    // Initialize once DOM is loaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.initialize());
    } else {
      this.initialize();
    }
  }
  
  /**
   * Initialize the API status checker
   */
  initialize() {
    console.log('🔍 ApiStatusChecker: Starting initialization...');
    
    // Find any existing status indicators
    const indicatorSelectors = [
      '#api-status',
      '.api-status',
      '[data-status="api"]',
      '.status-indicator',
      '#status-indicator'
    ];
    
    // Try each selector
    let found = false;
    for (const selector of indicatorSelectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        elements.forEach(element => this.statusIndicators.push(element));
        found = true;
        console.log(`✅ Found ${elements.length} status indicators with selector: ${selector}`);
      }
    }
    
    // If no indicators found, check if initialization banner exists
    if (!found) {
      const initBanner = document.querySelector('#initializing, .initializing, [data-status="initializing"]');
      if (initBanner) {
        // Register the banner as a status indicator
        this.statusIndicators.push(initBanner);
        console.log('⚠️ Using initialization banner as status indicator');
      } else {
        // Create a status indicator if none exists
        console.log('⚠️ No status indicators found, creating one...');
        this.createStatusIndicator();
      }
    }
    
    // Start checking API status
    this.checkApiStatus();
    
    // Set up periodic checks
    this.checkInterval = setInterval(() => {
      this.checkApiStatus();
    }, 10000); // Check every 10 seconds
    
    console.log('✅ ApiStatusChecker initialized');
  }
  
  /**
   * Create a status indicator if none exists
   */
  createStatusIndicator() {
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'api-status';
    statusIndicator.className = 'api-status checking';
    statusIndicator.textContent = 'Checking API...';
    
    // Find a good spot to add it
    const header = document.querySelector('header, .header, #header');
    if (header) {
      // Add to header
      header.appendChild(statusIndicator);
    } else {
      // Try to find the top navigation or any prominent UI element
      const nav = document.querySelector('nav, .navbar, #navbar');
      if (nav) {
        nav.appendChild(statusIndicator);
      } else {
        // Last resort: add to body
        document.body.insertBefore(statusIndicator, document.body.firstChild);
      }
    }
    
    // Add to our list of indicators
    this.statusIndicators.push(statusIndicator);
  }
  
  /**
   * Check API status and update indicators
   */
  async checkApiStatus() {
    // Update status indicators to checking state
    this.updateIndicators('checking', 'Checking API...');
    
    try {
      // Try to fetch API status - using both common endpoints
      const endpoints = ['/api/status', '/api/health', '/health', '/status'];
      
      let connected = false;
      for (const endpoint of endpoints) {
        try {
          const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
              'Accept': 'application/json'
            },
            // Short timeout to avoid long wait times
            signal: AbortSignal.timeout(2000)
          });
          
          if (response.ok) {
            connected = true;
            break;
          }
        } catch (endpointError) {
          console.log(`Endpoint ${endpoint} check failed:`, endpointError.message);
          // Continue to next endpoint
        }
      }
      
      // Update connection state
      this.isConnected = connected;
      this.lastCheck = new Date();
      
      // Update status indicators
      if (connected) {
        this.updateIndicators('connected', 'API Connected');
        console.log('✅ API is connected');
      } else {
        this.updateIndicators('disconnected', 'API Disconnected');
        console.log('⚠️ API is disconnected');
      }
      
      // Dispatch event for other components
      window.dispatchEvent(new CustomEvent('api-status-changed', {
        detail: {
          connected: this.isConnected,
          timestamp: this.lastCheck
        }
      }));
      
      return this.isConnected;
    } catch (error) {
      console.error('Error checking API status:', error);
      this.isConnected = false;
      this.lastCheck = new Date();
      this.updateIndicators('disconnected', 'API Error');
      
      // Dispatch event for other components
      window.dispatchEvent(new CustomEvent('api-status-changed', {
        detail: {
          connected: false,
          error: error.message,
          timestamp: this.lastCheck
        }
      }));
      
      return false;
    }
  }
  
  /**
   * Update all status indicators
   */
  updateIndicators(state, text) {
    this.statusIndicators.forEach(indicator => {
      // Remove existing state classes
      indicator.classList.remove('checking', 'connected', 'disconnected');
      
      // Add new state class
      indicator.classList.add(state);
      
      // Update text if element is not an icon-only indicator
      if (!indicator.classList.contains('icon-only')) {
        indicator.textContent = text;
      }
      
      // Update initialization banner if that's what we're using
      if (indicator.id === 'initializing' || indicator.classList.contains('initializing')) {
        if (state === 'connected') {
          indicator.style.backgroundColor = 'rgba(16, 185, 129, 0.2)';
          indicator.style.color = '#10b981';
        } else if (state === 'disconnected') {
          indicator.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
          indicator.style.color = '#ef4444';
        } else {
          indicator.style.backgroundColor = 'rgba(245, 158, 11, 0.2)';
          indicator.style.color = '#f59e0b';
        }
      }
    });
    
    // Also update document body with a data attribute for styling purposes
    document.body.setAttribute('data-api-status', state);
  }
  
  /**
   * Check if the API is connected
   */
  isApiConnected() {
    return this.isConnected;
  }
  
  /**
   * Get the timestamp of the last check
   */
  getLastCheckTime() {
    return this.lastCheck;
  }
}

// Initialize the API status checker
window.apiStatusChecker = new ApiStatusChecker();

// Export for module usage
console.log('🚀 ApiStatusChecker initialized and globally available as window.apiStatusChecker');
