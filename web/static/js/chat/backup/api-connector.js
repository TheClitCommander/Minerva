/**
 * Minerva API Connector
 * Establishes connection with the Think Tank API
 * Handles CORS and connectivity issues
 * Provides a unified interface for chat components
 */

class MinervaAPIConnector {
  constructor(options = {}) {
    this.options = {
      port: options.port || 8090, // Use port 8090 for the Think Tank API server
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
    const endpoint = `http://${window.location.hostname}:${port}${this.options.apiPath}`;
    this.log(`Trying endpoint: ${endpoint}`);
    
    try {
      const success = await this.testConnection(endpoint);
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
      const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);
      
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
      if (error.name === 'AbortError') {
        this.log(`Connection timed out for ${endpoint}`, null, 'warn');
      } else {
        this.log(`Connection error for ${endpoint}`, error, 'error');
        // Log more detailed CORS info
        this.log('This might be a CORS issue. Check server CORS headers and network tab for details.');
      }
      
      throw error;
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
  }
  
  // Send a message to the API
  async sendMessage(message, options = {}) {
    if (!this.connected) {
      // Try to connect first
      this.log('Not connected to API, attempting to reconnect...', null, 'warn');
      try {
        await this.connectToAPI();
        if (!this.connected) {
          throw new Error('Cannot send message: API is not connected');
        }
      } catch (error) {
        this.log('Failed to connect before sending message', error, 'error');
        return { error: 'Connection failed', details: error.message };
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
      this.log('Error sending message to API', error, 'error');
      return { error: 'API request failed', details: error.message };
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
  }
});
