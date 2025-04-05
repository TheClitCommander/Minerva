/**
 * Think Tank Direct Connection
 * A simplified, reliable connection to the Think Tank API with conversation memory support
 */

class ThinkTankAPI {
  constructor() {
    // The API base endpoint
    this.baseUrl = 'http://localhost:8989/api';
    this.apiUrl = `${this.baseUrl}/think-tank`;
    
    // Initialize conversation ID from localStorage or create a new one
    this.conversationId = localStorage.getItem('minerva_conversation_id') || this.generateConversationId();
    
    // Memory feature flags - these will be updated on the first API response
    this.memoryEnabled = true;
    this.contextDepth = 10;
    
    console.log('ThinkTank API initialized with conversation ID:', this.conversationId);
  }
  
  /**
   * Generate a new conversation ID with a timestamp prefix
   * @returns {string} A new conversation ID
   */
  generateConversationId() {
    return 'conv-' + Date.now() + '-' + Math.random().toString(36).substring(2, 10);
  }
  
  /**
   * Send a message to the Think Tank API
   * @param {string} message - The message to send
   * @param {object} options - Additional options
   * @returns {Promise} - A promise that resolves with the API response
   */
  async sendMessage(message, options = {}) {
    console.log('Sending message to Think Tank API:', message);
    
    // Construct the payload with the message and conversation ID
    const payload = {
      message: message,
      conversation_id: this.conversationId,
      store_in_memory: true,
      context_depth: this.contextDepth,
      ...options
    };
    
    try {
      // Make the API request
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(payload)
      });
      
      // Check if the request was successful
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      // Parse the response
      const data = await response.json();
      
      // Update conversation ID if present in the response
      if (data.conversation_id) {
        this.conversationId = data.conversation_id;
        localStorage.setItem('minerva_conversation_id', data.conversation_id);
      }
      
      // Update memory feature flags based on the response
      if (data.memory_status) {
        this.memoryEnabled = data.memory_status.memory_enabled;
        console.log(`Memory system enabled: ${this.memoryEnabled}`);
      }
      
      console.log('Received response from Think Tank API:', data);
      
      return data;
    } catch (error) {
      console.error('Error sending message to Think Tank API:', error);
      throw error;
    }
  }
  
  /**
   * Check if the API is available
   * @returns {Promise<boolean>} - A promise that resolves with true if the API is available
   */
  async checkAvailability() {
    try {
      // Try a simple POST request to the main API endpoint instead of looking for a health endpoint
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: 'ping',
          conversation_id: 'health-check-' + Date.now()
        })
      });
      
      return response.ok;
    } catch (error) {
      console.error('Error checking API availability:', error);
      return false;
    }
  }
  
  /**
   * Get the current conversation history
   * @param {number} contextDepth - Optional limit on how many messages to retrieve
   * @returns {Promise<Array>} - A promise that resolves with the conversation history
   */
  async getConversationHistory(contextDepth) {
    if (!this.memoryEnabled) {
      console.warn('Memory system is not enabled');
      return [];
    }
    
    try {
      const url = `${this.baseUrl}/conversations/${this.conversationId}${
        contextDepth ? `?context_depth=${contextDepth}` : ''
      }`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.messages || [];
    } catch (error) {
      console.error('Error retrieving conversation history:', error);
      return [];
    }
  }
  
  /**
   * Get list of recent conversations
   * @param {number} limit - Maximum number of conversations to retrieve
   * @returns {Promise<Array>} - A promise that resolves with the list of conversations
   */
  async getRecentConversations(limit = 10) {
    if (!this.memoryEnabled) {
      console.warn('Memory system is not enabled');
      return [];
    }
    
    try {
      const url = `${this.baseUrl}/conversations?limit=${limit}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.conversations || [];
    } catch (error) {
      console.error('Error retrieving recent conversations:', error);
      return [];
    }
  }
  
  /**
   * Update conversation title
   * @param {string} title - New title for the conversation
   * @param {string} conversationId - Optional conversation ID (uses current if not provided)
   * @returns {Promise<boolean>} - A promise that resolves with true if update was successful
   */
  async updateConversationTitle(title, conversationId = null) {
    if (!this.memoryEnabled) {
      console.warn('Memory system is not enabled');
      return false;
    }
    
    const targetId = conversationId || this.conversationId;
    
    try {
      const url = `${this.baseUrl}/conversations/${targetId}`;
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ title })
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.status === 'success';
    } catch (error) {
      console.error('Error updating conversation title:', error);
      return false;
    }
  }
  
  /**
   * Delete a conversation
   * @param {string} conversationId - Optional conversation ID (uses current if not provided)
   * @param {boolean} permanent - Whether to permanently delete the conversation
   * @returns {Promise<boolean>} - A promise that resolves with true if deletion was successful
   */
  async deleteConversation(conversationId = null, permanent = false) {
    if (!this.memoryEnabled) {
      console.warn('Memory system is not enabled');
      return false;
    }
    
    const targetId = conversationId || this.conversationId;
    
    try {
      const url = `${this.baseUrl}/conversations/${targetId}${permanent ? '?permanent=true' : ''}`;
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // If we deleted the current conversation, generate a new one
      if (targetId === this.conversationId) {
        this.conversationId = this.generateConversationId();
        localStorage.setItem('minerva_conversation_id', this.conversationId);
      }
      
      return data.status === 'success';
    } catch (error) {
      console.error('Error deleting conversation:', error);
      return false;
    }
  }
  
  /**
   * Search conversations by query term
   * @param {string} query - Search term
   * @param {number} limit - Maximum number of results to retrieve
   * @returns {Promise<Array>} - A promise that resolves with search results
   */
  async searchConversations(query, limit = 10) {
    if (!this.memoryEnabled) {
      console.warn('Memory system is not enabled');
      return [];
    }
    
    try {
      const url = `${this.baseUrl}/conversations/search/${encodeURIComponent(query)}?limit=${limit}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      
      const data = await response.json();
      return data.results || [];
    } catch (error) {
      console.error('Error searching conversations:', error);
      return [];
    }
  }
  
  /**
   * Set the active conversation ID
   * @param {string} conversationId - The conversation ID to set as active
   */
  setActiveConversation(conversationId) {
    this.conversationId = conversationId;
    localStorage.setItem('minerva_conversation_id', conversationId);
    console.log('Active conversation set to:', conversationId);
  }
}

// Create a global instance
window.thinkTankAPI = new ThinkTankAPI();
