/**
 * Real Minerva Chat Handler
 * Direct implementation that connects to our actual API with no fallbacks
 */

class RealChatHandler {
  constructor() {
    // Get DOM elements
    this.chatInput = document.getElementById('chat-input');
    this.chatForm = document.getElementById('chat-form');
    this.chatHistory = document.getElementById('chat-history');
    this.statusIndicator = document.querySelector('.status-indicator');
    this.statusText = document.querySelector('.status-text');
    
    // Connect to the real API
    this.apiUrl = 'http://127.0.0.1:5505';
    
    // Bind methods
    this.sendMessage = this.sendMessage.bind(this);
    this.addMessageToChat = this.addMessageToChat.bind(this);
    this.checkApiStatus = this.checkApiStatus.bind(this);
    
    // Initialize
    this.init();
  }
  
  init() {
    console.log('🚀 Initializing Real Chat Handler - No Fallbacks');
    
    // Check API status immediately
    this.checkApiStatus();
    
    // Set up periodic status checks
    setInterval(this.checkApiStatus, 15000);
    
    // Set up event listeners
    if (this.chatForm) {
      this.chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        this.handleSubmit();
      });
    }
    
    // Welcome message
    this.addSystemMessage('Welcome to Minerva', 'info');
  }
  
  async checkApiStatus() {
    try {
      console.log('Checking API status...');
      const response = await fetch(`${this.apiUrl}/api/status`);
      
      if (response.ok) {
        const data = await response.json();
        this.updateConnectionStatus('connected');
        console.log('API Status:', data);
        return true;
      } else {
        this.updateConnectionStatus('disconnected');
        return false;
      }
    } catch (error) {
      console.error('API status check failed:', error);
      this.updateConnectionStatus('disconnected');
      return false;
    }
  }
  
  updateConnectionStatus(status) {
    // Update all status indicators on the page
    const indicators = document.querySelectorAll('.status-indicator');
    const textIndicators = document.querySelectorAll('.status-text');
    
    indicators.forEach(indicator => {
      indicator.classList.remove('connected', 'disconnected', 'initializing');
      indicator.classList.add(status);
    });
    
    textIndicators.forEach(text => {
      text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    });
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('minerva-api-status', { 
      detail: { status }
    }));
  }
  
  handleSubmit() {
    if (!this.chatInput) return;
    
    const message = this.chatInput.value.trim();
    if (!message) return;
    
    // Clear input
    this.chatInput.value = '';
    
    // Add user message to chat
    this.addMessageToChat(message, 'user');
    
    // Send to API
    this.sendMessage(message);
  }
  
  async sendMessage(message) {
    try {
      // Check connection first
      const isConnected = await this.checkApiStatus();
      if (!isConnected) {
        this.addSystemMessage('Cannot send message: API is disconnected', 'error');
        return;
      }
      
      // Send message to real API
      const response = await fetch(`${this.apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add response to chat
      this.addMessageToChat(data.response, 'minerva');
    } catch (error) {
      console.error('Failed to send message:', error);
      this.addSystemMessage(`Error: ${error.message}`, 'error');
    }
  }
  
  addMessageToChat(content, sender) {
    if (!this.chatHistory) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = content;
    
    messageContent.appendChild(messageText);
    messageElement.appendChild(messageContent);
    
    this.chatHistory.appendChild(messageElement);
    
    // Scroll to bottom
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
  }
  
  addSystemMessage(content, type = 'info') {
    if (!this.chatHistory) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message system ${type}`;
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = content;
    
    messageContent.appendChild(messageText);
    messageElement.appendChild(messageContent);
    
    this.chatHistory.appendChild(messageElement);
    
    // Scroll to bottom
    this.chatHistory.scrollTop = this.chatHistory.scrollHeight;
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  window.chatHandler = new RealChatHandler();
});
