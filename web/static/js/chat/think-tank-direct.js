/**
 * Think Tank Direct Connection
 * A simplified, reliable connection to the Think Tank API
 * This is a direct implementation that works with the Minerva chat interface
 */

class ThinkTankConnection {
  constructor(options = {}) {
    // Core settings
    this.apiUrl = options.apiUrl || 'http://localhost:7070/api/think-tank';
    this.mockUrl = options.mockUrl || 'http://localhost:8080/api/think-tank-mock';
    this.localUrl = options.localUrl || '/api/think-tank-mock';
    
    // Container elements
    this.messagesContainer = options.messagesContainer || document.getElementById('chat-history');
    this.statusIndicator = options.statusIndicator || document.getElementById('connection-status');
    
    // State tracking
    this.conversationId = localStorage.getItem('minerva_conversation_id') || ('conv-' + Date.now());
    this.lastMessageTimestamp = Date.now();
    this.isConnected = false;
    this.failedAttempts = 0;
    this.maxRetries = options.maxRetries || 2;
    
    // Bind methods
    this.sendMessage = this.sendMessage.bind(this);
    this.checkConnection = this.checkConnection.bind(this);
    
    // Initialize
    this.initialize();
  }
  
  initialize() {
    console.log('Initializing Think Tank Direct Connection');
    // Store connection ID in localStorage
    localStorage.setItem('minerva_connection_id', 'direct-' + Date.now());
    
    // Check connection on startup
    this.checkConnection()
      .then(connected => {
        if (connected) {
          this.updateStatus('Connected to Think Tank', 'connected');
        } else {
          this.updateStatus('Using fallback mode', 'warning');
        }
      });
  }
  
  async checkConnection() {
    try {
      console.log(`Testing connection to Think Tank API at ${this.apiUrl}`);
      const response = await fetch(this.apiUrl + '/health', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        mode: 'cors'
      });
      
      if (response.ok) {
        this.isConnected = true;
        return true;
      }
    } catch (error) {
      console.warn('Think Tank API health check failed:', error.message);
    }
    
    try {
      // Try mock endpoint as fallback
      console.log(`Testing connection to mock API at ${this.mockUrl}`);
      const mockResponse = await fetch(this.mockUrl + '/health', { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (mockResponse.ok) {
        this.isConnected = true;
        this.apiUrl = this.mockUrl; // Switch to mock URL
        return true;
      }
    } catch (mockError) {
      console.warn('Mock API health check failed:', mockError.message);
    }
    
    // If both fail, set to use local mock API
    this.apiUrl = this.localUrl;
    this.isConnected = false;
    return false;
  }
  
  updateStatus(message, type = 'info') {
    console.log(`Think Tank status: ${message}`);
    
    if (this.statusIndicator) {
      this.statusIndicator.textContent = message;
      
      // Clear existing classes
      this.statusIndicator.classList.remove('connected', 'warning', 'error', 'info');
      
      // Add appropriate class
      this.statusIndicator.classList.add(type);
    }
    
    // Add system message to chat if available
    if (this.messagesContainer && type !== 'info') {
      const systemMsg = document.createElement('div');
      systemMsg.className = `message system ${type}`;
      systemMsg.textContent = message;
      this.messagesContainer.appendChild(systemMsg);
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }
  
  async sendMessage(message, options = {}) {
    if (!message || message.trim() === '') return null;
    
    // Show typing indicator if function is available
    if (typeof showTypingIndicator === 'function') {
      showTypingIndicator();
    }
    
    // Prepare request payload
    const payload = {
      message: message,
      conversation_id: this.conversationId,
      timestamp: Date.now(),
      client_version: '1.1.0',
      store_in_memory: true,
      ...options
    };
    
    console.log(`Sending message to Think Tank API at ${this.apiUrl}`);
    this.updateStatus('Processing message...', 'info');
    
    try {
      // Call API with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        mode: 'cors',
        signal: controller.signal,
        body: JSON.stringify(payload)
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Reset failure counter on success
      this.failedAttempts = 0;
      this.isConnected = true;
      
      // Store conversation ID if present
      if (data.conversation_id) {
        this.conversationId = data.conversation_id;
        localStorage.setItem('minerva_conversation_id', data.conversation_id);
      }
      
      this.updateStatus('Connected to Think Tank', 'connected');
      
      // Hide typing indicator if function is available
      if (typeof hideTypingIndicator === 'function') {
        hideTypingIndicator();
      }
      
      return data;
    } catch (error) {
      console.error('Think Tank API Error:', error);
      this.failedAttempts++;
      
      // Try to reconnect or fall back if too many failures
      if (this.failedAttempts >= this.maxRetries) {
        await this.switchToFallback();
      }
      
      // Create fallback response
      const fallbackResponse = this.createFallbackResponse(message);
      
      // Hide typing indicator if function is available
      if (typeof hideTypingIndicator === 'function') {
        hideTypingIndicator();
      }
      
      this.updateStatus('Using fallback mode', 'warning');
      return fallbackResponse;
    }
  }
  
  async switchToFallback() {
    console.log('Too many failures, switching to fallback mode');
    
    // Try to check connection again
    const connected = await this.checkConnection();
    
    if (!connected) {
      // If still not connected, use local mock
      this.apiUrl = this.localUrl;
      this.updateStatus('Using local fallback mode', 'warning');
    }
  }
  
  createFallbackResponse(message) {
    // Create a simple response when API fails
    return {
      response: `I received your message: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}"
      
I'm currently operating in offline mode since I can't reach the Think Tank. I'll do my best to assist you with basic functionality, but advanced capabilities may be limited until connection is restored.`,
      conversation_id: this.conversationId,
      timestamp: Date.now(),
      model_info: {
        models: [
          { name: 'offline-fallback', contribution: 100 }
        ]
      }
    };
  }
}

// Register globally
window.ThinkTankConnection = ThinkTankConnection;

console.log('Think Tank Direct Connection module loaded');
