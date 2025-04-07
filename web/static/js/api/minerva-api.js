/**
 * Minerva API Client - Robust API connection with proper fallbacks
 * Building on our successful integration approach
 */

class MinervaAPI {
  constructor(options = {}) {
    this.baseURL = options.baseURL || this.determineBaseURL();
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 2000;
    this.fallbackEnabled = options.fallbackEnabled !== false;
    this.debug = options.debug || false;
    this.connectionStatus = 'unknown'; // unknown, online, limited, offline
    
    // Store active requests to avoid duplication
    this.activeRequests = new Map();
    
    // Initialize event listeners for connection status
    this.initEventListeners();
    
    // Log initialization
    this.log('Minerva API client initialized');
    
    // Check connection immediately
    this.checkConnection();
  }
  
  /**
   * Determine the base URL dynamically based on current location
   */
  determineBaseURL() {
    // Use relative URLs - ensures we connect to the same server the UI is served from
    return '';
  }
  
  /**
   * Initialize event listeners for connection status
   */
  initEventListeners() {
    // Listen for online/offline events
    window.addEventListener('online', () => this.checkConnection());
    window.addEventListener('offline', () => {
      this.connectionStatus = 'offline';
      this.emitStatusChange();
    });
    
    // Periodic connection check (every 30 seconds)
    setInterval(() => this.checkConnection(), 30000);
  }
  
  /**
   * Check API connection status
   */
  async checkConnection() {
    try {
      const result = await this.get('/api/think-tank', { _noRetry: true, _noFallback: true });
      
      if (result && result.status === 'success') {
        this.connectionStatus = 'online';
      } else {
        this.connectionStatus = 'limited';
      }
    } catch (error) {
      // Check if it's a network error or API error
      if (error.code === 'NETWORK_ERROR') {
        this.connectionStatus = 'offline';
      } else {
        this.connectionStatus = 'limited';
      }
      
      this.log('API connection check failed:', error);
    }
    
    this.emitStatusChange();
    return this.connectionStatus;
  }
  
  /**
   * Emit status change event
   */
  emitStatusChange() {
    const event = new CustomEvent('minerva-api-status', { 
      detail: { status: this.connectionStatus } 
    });
    window.dispatchEvent(event);
    
    this.log('API Status:', this.connectionStatus);
  }
  
  /**
   * Generate a request ID
   */
  generateRequestId(endpoint, params) {
    return `${endpoint}:${JSON.stringify(params || {})}`;
  }
  
  /**
   * Make an API request with retries and fallbacks
   */
  async request(method, endpoint, options = {}) {
    const { 
      params, 
      body, 
      headers = {},
      _attempt = 1,
      _noRetry = false,
      _noFallback = false
    } = options;
    
    // Create a unique request ID to prevent duplicates
    const requestId = this.generateRequestId(endpoint, params);
    
    // Check if this request is already in progress
    if (this.activeRequests.has(requestId)) {
      return this.activeRequests.get(requestId);
    }
    
    // Build URL with query parameters
    let url = `${this.baseURL}${endpoint}`;
    if (params) {
      const queryParams = new URLSearchParams(params).toString();
      url = `${url}?${queryParams}`;
    }
    
    // Build request options
    const requestOptions = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers
      }
    };
    
    // Add request body if needed
    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      requestOptions.body = JSON.stringify(body);
    }
    
    // Create a promise for this request
    const requestPromise = (async () => {
      try {
        // Make the request
        this.log(`API ${method} ${url} (Attempt ${_attempt}/${this.maxRetries})`);
        const response = await fetch(url, requestOptions);
        
        // Handle HTTP errors
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
          throw {
            status: response.status,
            message: errorData.message || `HTTP error ${response.status}`,
            code: 'HTTP_ERROR',
            data: errorData
          };
        }
        
        // Parse response
        const data = await response.json();
        return data;
      } catch (error) {
        // Determine error type
        const isNetworkError = error.name === 'TypeError' && error.message === 'Failed to fetch';
        const formattedError = {
          message: error.message || 'Unknown error',
          code: isNetworkError ? 'NETWORK_ERROR' : (error.code || 'API_ERROR'),
          originalError: error,
          endpoint,
          attempt: _attempt
        };
        
        // Retry logic for network errors if retries are allowed
        if ((isNetworkError || error.status >= 500) && _attempt < this.maxRetries && !_noRetry) {
          this.log(`Retrying after error: ${formattedError.message}`);
          
          // Wait before retry
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * _attempt));
          
          // Retry the request
          return this.request(method, endpoint, {
            ...options,
            _attempt: _attempt + 1
          });
        }
        
        // Use fallback if available
        if (this.fallbackEnabled && !_noFallback) {
          const fallbackData = await this.getFallbackData(endpoint, options);
          if (fallbackData) {
            this.log('Using fallback data for:', endpoint);
            return {
              ...fallbackData,
              _fromFallback: true
            };
          }
        }
        
        // Rethrow the error if no fallback or retries worked
        throw formattedError;
      } finally {
        // Remove from active requests
        this.activeRequests.delete(requestId);
      }
    })();
    
    // Store the request promise
    this.activeRequests.set(requestId, requestPromise);
    
    return requestPromise;
  }
  
  /**
   * Get fallback data for an endpoint
   */
  async getFallbackData(endpoint, options) {
    // Implement fallback data sources
    // This could be from localStorage, default templates, etc.
    
    // Example fallbacks for common endpoints
    const fallbacks = {
      '/api/think-tank': {
        status: 'success',
        message: 'Using offline mode',
        features: ['basic_chat', 'memory'],
        mode: 'offline'
      },
      '/api/chat': {
        messages: [],
        status: 'offline',
        canRespond: false
      },
      '/api/projects': {
        projects: [],
        status: 'offline'
      },
      '/api/memory': {
        memories: [],
        status: 'offline'
      }
    };
    
    // Check for exact endpoint match
    if (fallbacks[endpoint]) {
      return fallbacks[endpoint];
    }
    
    // Check for pattern matches
    if (endpoint.startsWith('/api/chat/')) {
      return {
        message: "I'm currently in offline mode. I'll remember your message and sync when online.",
        status: 'offline',
        timestamp: new Date().toISOString()
      };
    }
    
    // No fallback available
    return null;
  }
  
  /**
   * GET request helper
   */
  async get(endpoint, options = {}) {
    return this.request('GET', endpoint, options);
  }
  
  /**
   * POST request helper
   */
  async post(endpoint, body, options = {}) {
    return this.request('POST', endpoint, { ...options, body });
  }
  
  /**
   * PUT request helper
   */
  async put(endpoint, body, options = {}) {
    return this.request('PUT', endpoint, { ...options, body });
  }
  
  /**
   * DELETE request helper
   */
  async delete(endpoint, options = {}) {
    return this.request('DELETE', endpoint, options);
  }
  
  /**
   * Send a chat message to the API
   */
  async sendChatMessage(message, conversationId = null, options = {}) {
    const endpoint = conversationId 
      ? `/api/chat/${conversationId}` 
      : '/api/chat';
      
    return this.post(endpoint, { message }, options);
  }
  
  /**
   * Get projects from the API
   */
  async getProjects(options = {}) {
    return this.get('/api/projects', options);
  }
  
  /**
   * Get memories from the API
   */
  async getMemories(options = {}) {
    return this.get('/api/memory', options);
  }
  
  /**
   * Debug logging
   */
  log(...args) {
    if (this.debug) {
      console.log('[Minerva API]', ...args);
    }
  }
}

// Create a global instance
window.minervaAPI = new MinervaAPI({ debug: true });

// Export the class and instance
const api = window.minervaAPI;
export { MinervaAPI, api };
