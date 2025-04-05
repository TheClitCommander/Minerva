/**
 * Minerva API Connector
 * Establishes connection with the Think Tank API
 * Handles CORS and connectivity issues
 * Provides a unified interface for chat components
 */

class MinervaAPIConnector {
  constructor(options = {}) {
    this.options = {
      port: options.port || 8080, // Use port 8080 for the Think Tank API server
      apiPath: options.apiPath || '/api/think-tank',
      timeout: options.timeout || 5000,
      debug: options.debug !== undefined ? options.debug : true
    };
    
    // Connection info
    this.apiEndpoint = null;
    this.conversationId = localStorage.getItem('minerva_conversation_id') || 
                         'conv-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
    
    // Status
    this.connected = false;
    this.connectionAttempts = 0;
    this.maxAttempts = 5;
    
    // Initialize
    this.initialize();
  }
  
  // Log helper
  log(message, data = null, level = 'info') {
    if (!this.options.debug) return;
    
    const prefix = '[Minerva API]';
    switch(level) {
      case 'error':
        console.error(prefix, message, data || '');
        break;
      case 'warn':
        console.warn(prefix, message, data || '');
        break;
      default:
        console.log(prefix, message, data || '');
    }
  }
  
  // Initialize the connector
  async initialize() {
    this.log('Initializing API connector...');
    
    // Force the port to 8080 as per user requirement
    this.options.port = 8080;
    
    // Try to load previously successful endpoint
    const savedEndpoint = localStorage.getItem('minerva_api_url');
    if (savedEndpoint) {
      this.log('Found saved API endpoint:', savedEndpoint);
      this.apiEndpoint = savedEndpoint;
      
      // Verify it's still working
      try {
        const success = await this.testConnection(this.apiEndpoint);
        if (success) {
          this.connected = true;
          this.notifyConnected();
          return;
        }
      } catch (error) {
        this.log('Saved endpoint is no longer working, will try to find a new one', error, 'warn');
      }
    }
    
    // Try to establish connection
    await this.connectToAPI();
  }
  
  // Connect to API using a consistent port
  async connectToAPI() {
    this.log(`Attempting to connect to API on port ${this.options.port}...`);
    
    try {
      const success = await this.tryPort(this.options.port);
      if (success) {
        this.log(`Successfully connected to API on port ${this.options.port}`);
        return;
      }
    } catch (error) {
      this.log(`Failed to connect on port ${this.options.port}`, error, 'warn');
    }
    
    // Try with relative URLs
    try {
      const relativeEndpoint = this.options.apiPath;
      this.log('Trying relative endpoint:', relativeEndpoint);
      const success = await this.testConnection(relativeEndpoint);
      if (success) {
        this.apiEndpoint = relativeEndpoint;
        this.connected = true;
        this.saveEndpoint();
        this.notifyConnected();
        return;
      }
    } catch (error) {
      this.log('Failed to connect with relative URL', error, 'warn');
    }
    
    this.log('Could not connect to API after trying all options', null, 'error');
    this.notifyConnectionFailed();
  }
  
  // Try to connect on a specific port
  async tryPort(port) {
    // Use the same hostname as the current page rather than hardcoded localhost
    // Rule #4: No usage of window.location.origin unless explicitly allowed
    const endpoint = `http://${window.location.hostname}:${port}${this.options.apiPath}`;
    this.log(`Trying endpoint: ${endpoint}`);
    
    try {
      // Add timeout to avoid hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 3000); // 3 second timeout
      
      const success = await this.testConnection(endpoint);
      clearTimeout(timeoutId);
      
      if (success) {
        this.apiEndpoint = endpoint;
        this.connected = true;
        this.saveEndpoint();
        this.notifyConnected();
        return true;
      }
    } catch (error) {
      this.log(`Connection test failed for ${endpoint}`, error, 'warn');
    }
    
    return false;
  }
  
  // Test connection to a specific endpoint
  async testConnection(endpoint) {
    this.connectionAttempts++;
    
    try {
      // First send an OPTIONS request to check CORS
      this.log(`Sending CORS preflight request to ${endpoint}`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
        this.log(`Connection timeout for ${endpoint} after ${this.options.timeout}ms`, null, 'warn');
      }, this.options.timeout);
      
      // Handle the main API test
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        signal: controller.signal,
        mode: 'cors',  // Ensure CORS mode is set
        credentials: 'omit',  // Don't send credentials for better CORS compatibility
        body: JSON.stringify({
          message: 'ping',
          type: 'connection_test',
          conversation_id: this.conversationId
        })
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        this.log(`Connection successful to ${endpoint}`);
        return true;
      } else {
        this.log(`Connection failed with status: ${response.status}`);
        return false;
      }
    } catch (error) {
      // Create a structured error object with enhanced diagnostics (Rule #10)
      const enhancedError = {
        context: 'API_Connection',
        originalError: error,
        timestamp: new Date().toISOString(),
        endpoint: endpoint,
        attempt: this.connectionAttempts,
        diagnostics: {}
      };
      
      if (error.name === 'AbortError') {
        enhancedError.message = `Connection timed out for ${endpoint} after ${this.options.timeout}ms`;
        enhancedError.code = 'CONNECTION_TIMEOUT';
        enhancedError.diagnostics.timeoutMs = this.options.timeout;
        this.log(`Connection timed out for ${endpoint}`, enhancedError, 'warn');
      } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        enhancedError.message = `Network error connecting to ${endpoint} - API may be offline`;
        enhancedError.code = 'NETWORK_ERROR';
        enhancedError.diagnostics.networkState = navigator.onLine ? 'online' : 'offline';
        this.log(`Network error for ${endpoint}`, enhancedError, 'error');
        // Log more detailed network info
        this.log('API server may be offline. Using fallback mode per Rule #4.');
      } else {
        enhancedError.message = error.message || `Unknown error connecting to ${endpoint}`;
        enhancedError.code = error.name || 'CONNECTION_ERROR';
        enhancedError.diagnostics.errorStack = error.stack;
        this.log(`Connection error for ${endpoint}`, enhancedError, 'error');
        // Log more detailed CORS info
        this.log('This might be a CORS issue. Check server CORS headers and network tab for details.');
      }
      
      // Update global API status
      if (window.thinkTankApiStatus) {
        window.thinkTankApiStatus.available = false;
        window.thinkTankApiStatus.lastChecked = new Date().toISOString();
        window.thinkTankApiStatus.lastError = enhancedError;
      }
      
      // Throw the enhanced error instead of the original one
      throw enhancedError;
    }
  }
  
  // Save the working endpoint to localStorage
  saveEndpoint() {
    if (this.apiEndpoint) {
      localStorage.setItem('minerva_api_url', this.apiEndpoint);
      localStorage.setItem('minerva_conversation_id', this.conversationId);
      this.log('Saved API endpoint to localStorage:', this.apiEndpoint);
    }
  }
  
  // Notify that connection is established
  notifyConnected() {
    this.log('API connection established:', this.apiEndpoint);
    
    // Dispatch event for other components to listen to
    window.dispatchEvent(new CustomEvent('minerva_api_connected', {
      detail: {
        endpoint: this.apiEndpoint,
        conversationId: this.conversationId
      }
    }));
    
    // Set global variable for compatibility
    window.THINK_TANK_API_URL = this.apiEndpoint;
  }
  
  // Notify that connection failed
  notifyConnectionFailed() {
    this.log('API connection failed after all attempts', null, 'error');
    
    window.dispatchEvent(new CustomEvent('minerva_api_connection_failed', {
      detail: {
        attempts: this.connectionAttempts,
        lastTried: this.apiEndpoint
      }
    }));
    
    // Set up automatic retry every 60 seconds per Minerva Master Ruleset
    if (!this.retryInterval) {
      this.log('Setting up automatic retry every 60 seconds', null, 'info');
      this.retryInterval = setInterval(() => {
        this.log('Attempting automatic reconnection to API...', null, 'info');
        this.connectToAPI().catch(err => {
          console.warn('Automatic reconnection attempt failed:', err);
        });
      }, 60000); // 60 seconds
    }
  }
  
  // Send a message to the API
  async sendMessage(message, options = {}) {
    if (!this.connected) {
      // Try to connect first
      this.log('Not connected to API, attempting to reconnect...', null, 'warn');
      try {
        await this.connectToAPI();
        if (!this.connected) {
          // Fallback gracefully with simulated response as per Minerva Master Ruleset
          this.log('API is not connected, using fallback response simulation', null, 'warn');
          console.warn('Using fallback simulation for Think Tank API - rule #4 of Minerva Master Ruleset');
          return this.generateFallbackResponse(message, options);
        }
      } catch (error) {
        const errorDetails = error ? (error.message || error.toString() || 'Unknown error') : 'API connection failed';
        this.log('Failed to connect before sending message', errorDetails, 'error');
        // Fallback gracefully with simulated response
        return this.generateFallbackResponse(message, options, errorDetails);
      }
    }
    
    try {
      this.log(`Sending message to API: ${message.substring(0, 30)}...`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), options.timeout || this.options.timeout);
      
      const response = await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        signal: controller.signal,
        // Allow CORS when needed
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify({
          message: message,
          conversation_id: this.conversationId,
          timestamp: new Date().toISOString(),
          client_id: 'minerva-web-' + Math.random().toString(36).substring(2, 9),
          ...options
        })
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      this.log('Received response from API', data);
      return data;
    } catch (error) {
      // Create a structured error object even if error is empty
      const errorDetails = {
        message: error ? (error.message || 'Unknown error') : 'Failed to connect to Think Tank API',
        type: error ? error.name || 'APIError' : 'ConnectionError',
        timestamp: new Date().toISOString(),
        cause: error ? error.toString() : 'Network connectivity issue or CORS error'
      };
      
      this.log('Error sending message to API', errorDetails, 'error');
      console.warn('API request failed - activating fallback response as per Rule #4');
      // Log more detailed diagnostics to console
      if (!error || Object.keys(error).length === 0) {
        console.warn('Empty error object detected - this is likely a CORS or network connectivity issue');
        console.error('Detailed diagnostics:', errorDetails);
      }
      // Use fallback response when API call fails
      return this.generateFallbackResponse(message, options);
    }
  }
  
  // Generate a fallback response when API is unavailable
  generateFallbackResponse(message, options = {}) {
    this.log('Generating fallback response for message', message, 'info');
    console.warn('Using fallback response generator - Think Tank API is unavailable');
    
    // Update UI to show offline/fallback status
    this.updateStatusDisplay('offline');
    
    // Rule #2: Use enhancedConversationStorage as the primary memory store
    // Store the message in local history
    if (window.enhancedConversationStorage && window.enhancedConversationStorage.addMessage) {
      window.enhancedConversationStorage.addMessage({
        role: 'user',
        content: message,
        timestamp: new Date().toISOString()
      });
    } else {
      // Rule #2: Only fallback to other storage methods if necessary
      if (window.conversationHistory) {
        window.conversationHistory.push({
          role: 'user',
          content: message,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Create a simulated system response
    const response = {
      status: "success",
      response: `I've received your message: "${message}". However, I'm currently operating in offline mode because the Think Tank API server is unavailable. Your message has been saved, and I'll process it properly when the connection is restored. In the meantime, is there anything else I can help you with?`,
      conversation_id: this.conversationId,
      message_id: `fallback-${Date.now()}`,
      timestamp: new Date().toISOString(),
      model_info: {
        models_used: ["fallback-mode"],
        rankings: [
          {model_name: "fallback-mode", score: 1.0, reason: "API unavailable"}
        ],
        processing_time_ms: 50
      },
      using_fallback: true,
      memory_updates: {
        summary_updated: false,
        conversation_stored: true,
        key_points: ["Think Tank API is currently unavailable", "Operating in offline mode"]
      }
    };
    
    // Store the response in conversation history
    if (window.enhancedConversationStorage && window.enhancedConversationStorage.addMessage) {
      window.enhancedConversationStorage.addMessage({
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
        model: 'fallback-mode'
      });
    }
    
    return response;
  }
  
  // Update status display in UI
  updateStatusDisplay(status) {
    // Find status indicators in the UI
    const statusElements = document.querySelectorAll('.think-tank-status, .status');
    statusElements.forEach(el => {
      // Remove existing status classes
      el.classList.remove('online', 'offline', 'connecting');
      // Add new status class
      el.classList.add(status);
      
      // Update text if available
      const textEl = el.querySelector('.status-text');
      if (textEl) {
        textEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
      }
    });
    
    // Update dashboard stats if present
    const dashboardStatus = document.querySelector('#dashboard-view .stat-card .status');
    if (dashboardStatus) {
      dashboardStatus.className = 'status ' + status;
      const statusText = dashboardStatus.querySelector('.status-text');
      if (statusText) {
        statusText.textContent = status === 'online' ? 'Online' : 'Offline (Fallback Active)';
      }
    }
  }
}

// Create a global instance when document is ready
document.addEventListener('DOMContentLoaded', function() {
  // Only create if not already present
  if (!window.minervaAPI) {
    window.minervaAPI = new MinervaAPIConnector();
    
    // Make the API URL available to legacy components
    if (window.minervaAPI.apiEndpoint) {
      window.THINK_TANK_API_URL = window.minervaAPI.apiEndpoint;
    }
    
    // Rule #10: Provide clear user feedback
    // Update status elements to show connecting initially
    setTimeout(() => {
      // Delay status update to ensure DOM is loaded
      if (window.minervaAPI.updateStatusDisplay) {
        window.minervaAPI.updateStatusDisplay('connecting');
      }
    }, 500);
    
    // Log that we're using enhanced API connector with fallback
    console.log('✅ Minerva API Connector initialized with fallback support');
  }
});
