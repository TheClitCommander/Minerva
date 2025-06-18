/**
 * Minerva API Chat Service
 * Direct API connection to chat backend with no fallbacks or simulated responses
 */

class ApiChatService {
  constructor(options = {}) {
    // Configuration
    this.apiUrl = options.apiUrl || '/api/chat';
    this.apiStatusUrl = options.apiStatusUrl || '/api/status';
    this.statusCallback = options.statusCallback || null;
    this.messageCallback = options.messageCallback || null;
    this.errorCallback = options.errorCallback || null;
    
    // Internal state
    this.connected = false;
    this.connecting = false;
    this.connectionCheck = null;
    
    // Check connection on initialization
    this.checkConnection();
  }
  
  /**
   * Check connection to the API
   * @returns {Promise<boolean>} - Connection status
   */
  async checkConnection() {
    if (this.connecting) return this.connected;
    
    this.connecting = true;
    
    try {
      const response = await fetch(this.apiStatusUrl, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        },
        // Short timeout to avoid long wait times
        signal: AbortSignal.timeout(3000)
      });
      
      this.connected = response.ok;
      
      // Call status callback if provided
      if (this.statusCallback) {
        this.statusCallback({
          connected: this.connected,
          status: this.connected ? 'connected' : 'disconnected'
        });
      }
      
      console.log(`🔌 API connection check: ${this.connected ? 'Connected' : 'Disconnected'}`);
    } catch (error) {
      this.connected = false;
      
      if (this.statusCallback) {
        this.statusCallback({
          connected: false,
          status: 'disconnected',
          error: error.message
        });
      }
      
      console.warn('API connection check failed:', error);
    }
    
    this.connecting = false;
    return this.connected;
  }
  
  /**
   * Start periodic connection checking
   * @param {number} interval - Check interval in milliseconds
   */
  startConnectionChecking(interval = 30000) {
    if (this.connectionCheck) {
      clearInterval(this.connectionCheck);
    }
    
    this.connectionCheck = setInterval(() => {
      this.checkConnection();
    }, interval);
    
    return this;
  }
  
  /**
   * Stop periodic connection checking
   */
  stopConnectionChecking() {
    if (this.connectionCheck) {
      clearInterval(this.connectionCheck);
      this.connectionCheck = null;
    }
    
    return this;
  }
  
  /**
   * Send a message to the API
   * @param {string} message - The message to send
   * @param {object} context - Optional context information
   * @returns {Promise} - Promise that resolves with the response
   */
  async sendMessage(message, context = {}) {
    // Ensure message is not empty
    if (!message || typeof message !== 'string' || message.trim() === '') {
      throw new Error('Message cannot be empty');
    }
    
    // Always check connection first
    const isConnected = await this.checkConnection();
    if (!isConnected) {
      throw new Error('Cannot send message: API is not connected');
    }
    
    // Prepare request body
    const requestBody = {
      message: message,
      timestamp: new Date().toISOString(),
      ...context
    };
    
    try {
      // Send the request to the API without any fallbacks
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
      
      // Check if the response is ok
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      // Parse the response
      const data = await response.json();
      
      // Call message callback if provided
      if (this.messageCallback) {
        this.messageCallback(data);
      }
      
      return data;
    } catch (error) {
      // Call error callback if provided
      if (this.errorCallback) {
        this.errorCallback(error);
      }
      
      // Re-throw the error for handling by the caller
      throw error;
    }
  }
  
  /**
   * Set callbacks for the service
   * @param {object} callbacks - Callback functions
   */
  setCallbacks(callbacks = {}) {
    if (callbacks.status) this.statusCallback = callbacks.status;
    if (callbacks.message) this.messageCallback = callbacks.message;
    if (callbacks.error) this.errorCallback = callbacks.error;
    
    return this;
  }
}

// Make the service available globally
window.ApiChatService = ApiChatService;
