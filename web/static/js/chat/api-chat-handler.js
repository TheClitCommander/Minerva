/**
 * Minerva API Chat Handler
 * Handles chat functionality with direct API connection and proper error display
 * NO FALLBACKS - only real API connections
 */

class ApiChatHandler {
  constructor(options = {}) {
    // Core DOM elements
    this.chatContainer = options.container || document.getElementById('chat-container');
    this.messagesContainer = options.messagesContainer || document.getElementById('chat-messages');
    this.inputField = options.inputField || document.getElementById('chat-input');
    this.sendButton = options.sendButton || document.getElementById('send-button');
    this.statusElement = options.statusElement || document.getElementById('chat-status');
    
    // Create API service
    this.apiService = new ApiChatService({
      apiUrl: options.apiUrl || '/api/chat',
      apiStatusUrl: options.apiStatusUrl || '/api/status',
      statusCallback: this.handleConnectionStatus.bind(this),
      messageCallback: this.handleApiMessage.bind(this),
      errorCallback: this.handleApiError.bind(this)
    });
    
    // Initialize if all required elements exist
    if (this.messagesContainer && this.inputField && this.sendButton) {
      this.init();
      console.log('✅ API Chat handler initialized');
    } else {
      console.error('Missing required chat elements', {
        messagesContainer: !!this.messagesContainer,
        inputField: !!this.inputField,
        sendButton: !!this.sendButton
      });
    }
  }
  
  /**
   * Initialize the chat handler
   */
  init() {
    // Load previous conversations
    this.loadChatHistory();
    
    // Add event listeners
    this.sendButton.addEventListener('click', this.sendMessage.bind(this));
    
    this.inputField.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });
    
    // Start periodic connection checking
    this.apiService.startConnectionChecking(15000); // Check every 15 seconds
    
    // Add network status listeners
    window.addEventListener('online', () => {
      this.apiService.checkConnection();
      this.addStatusMessage('Network connection restored. Reconnecting to Think Tank...');
    });
    
    window.addEventListener('offline', () => {
      this.updateConnectionStatus(false);
      this.addStatusMessage('Network connection lost. Messages will not be sent until connection is restored.');
    });
  }
  
  /**
   * Send a message to the API
   */
  async sendMessage() {
    const message = this.inputField.value.trim();
    if (!message) return;
    
    // Add user message to the chat
    this.addMessageToChat(message, 'user');
    
    // Clear input field
    this.inputField.value = '';
    
    // Save the message to chat history
    this.saveChatHistory(message, null);
    
    // Add typing indicator
    const typingIndicator = this.addTypingIndicator();
    
    try {
      // Check connection first
      const isConnected = await this.apiService.checkConnection();
      
      if (!isConnected) {
        throw new Error('Cannot send message: API is not connected');
      }
      
      // Send message to API - no fallbacks
      const response = await this.apiService.sendMessage(message);
      
      // Remove typing indicator
      if (typingIndicator) typingIndicator.remove();
      
      // Process the response
      if (response && response.response) {
        this.addMessageToChat(response.response, 'minerva');
        this.saveChatHistory(null, response.response);
      } else {
        throw new Error('Invalid response from API');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Remove typing indicator
      if (typingIndicator) typingIndicator.remove();
      
      // Show error message to user
      this.addErrorMessage(error.message);
      
      // Update connection status
      this.updateConnectionStatus(false);
    }
  }
  
  /**
   * Add a message to the chat UI
   * @param {string} text - Message text
   * @param {string} sender - Message sender ('user', 'minerva', 'system')
   * @returns {HTMLElement} - The created message element
   */
  addMessageToChat(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    
    // Convert URLs to clickable links
    const linkedText = this.linkifyText(text);
    
    if (linkedText !== text) {
      messageText.innerHTML = linkedText;
    } else {
      messageText.textContent = text;
    }
    
    messageDiv.appendChild(messageText);
    this.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    this.scrollToBottom();
    
    return messageDiv;
  }
  
  /**
   * Add a system status message
   * @param {string} text - Status message text
   */
  addStatusMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    messageDiv.appendChild(messageText);
    this.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    this.scrollToBottom();
    
    return messageDiv;
  }
  
  /**
   * Add an error message
   * @param {string} errorText - Error message text
   */
  addErrorMessage(errorText) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message error';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.innerHTML = `
      <strong>Error:</strong> ${errorText}<br>
      <em>Please check your connection or try again later.</em>
    `;
    
    messageDiv.appendChild(messageText);
    this.messagesContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    this.scrollToBottom();
    
    return messageDiv;
  }
  
  /**
   * Add typing indicator to the chat
   */
  addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message minerva typing';
    indicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    this.messagesContainer.appendChild(indicator);
    
    // Scroll to bottom
    this.scrollToBottom();
    
    return indicator;
  }
  
  /**
   * Convert text with URLs to clickable links
   * @param {string} text - Text to linkify
   * @returns {string} - HTML with clickable links
   */
  linkifyText(text) {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
  }
  
  /**
   * Scroll the chat to the bottom
   */
  scrollToBottom() {
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
  
  /**
   * Handle connection status updates
   * @param {object} status - Connection status object
   */
  handleConnectionStatus(status) {
    this.updateConnectionStatus(status.connected, status.status);
  }
  
  /**
   * Update the connection status UI
   * @param {boolean} connected - Whether connected to API
   * @param {string} statusText - Status text to display
   */
  updateConnectionStatus(connected, statusText = null) {
    if (!this.statusElement) return;
    
    this.statusElement.className = connected ? 'status connected' : 'status disconnected';
    this.statusElement.textContent = statusText || (connected ? 'Connected' : 'Disconnected');
    
    // Toggle connection indicator
    if (this.chatContainer) {
      if (connected) {
        this.chatContainer.classList.remove('offline');
        this.chatContainer.classList.add('online');
      } else {
        this.chatContainer.classList.remove('online');
        this.chatContainer.classList.add('offline');
      }
    }
  }
  
  /**
   * Handle API message response
   * @param {object} data - API response data
   */
  handleApiMessage(data) {
    // Update connection status
    this.updateConnectionStatus(true);
  }
  
  /**
   * Handle API error
   * @param {Error} error - Error object
   */
  handleApiError(error) {
    console.error('API error:', error);
    this.updateConnectionStatus(false);
  }
  
  /**
   * Save chat history to localStorage
   * @param {string|null} userMessage - User message to save
   * @param {string|null} minervaMessage - Minerva message to save
   */
  saveChatHistory(userMessage = null, minervaMessage = null) {
    try {
      // Get existing chat history
      const chatHistory = JSON.parse(localStorage.getItem('minerva_chat_history') || '[]');
      
      // Add new messages
      if (userMessage) {
        chatHistory.push({
          sender: 'user',
          text: userMessage,
          timestamp: new Date().toISOString()
        });
      }
      
      if (minervaMessage) {
        chatHistory.push({
          sender: 'minerva',
          text: minervaMessage,
          timestamp: new Date().toISOString()
        });
      }
      
      // Limit history size to 100 messages
      if (chatHistory.length > 100) {
        chatHistory.splice(0, chatHistory.length - 100);
      }
      
      // Save to localStorage
      localStorage.setItem('minerva_chat_history', JSON.stringify(chatHistory));
    } catch (e) {
      console.error('Error saving chat history:', e);
    }
  }
  
  /**
   * Load chat history from localStorage
   */
  loadChatHistory() {
    try {
      const chatHistory = JSON.parse(localStorage.getItem('minerva_chat_history') || '[]');
      
      // Clear the chat container first
      this.messagesContainer.innerHTML = '';
      
      // Add welcome message if no history
      if (chatHistory.length === 0) {
        this.addStatusMessage('Welcome to Minerva Chat. Type a message to get started.');
        return;
      }
      
      // Add each message to the chat
      chatHistory.forEach(message => {
        this.addMessageToChat(message.text, message.sender);
      });
      
      // Scroll to bottom
      this.scrollToBottom();
    } catch (e) {
      console.error('Error loading chat history:', e);
      this.messagesContainer.innerHTML = '';
      this.addStatusMessage('Error loading chat history. Starting a new conversation.');
    }
  }
  
  /**
   * Clear chat history
   */
  clearChatHistory() {
    localStorage.removeItem('minerva_chat_history');
    this.messagesContainer.innerHTML = '';
    this.addStatusMessage('Chat history cleared. Starting a new conversation.');
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Create global instance
  window.apiChatHandler = new ApiChatHandler();
});
