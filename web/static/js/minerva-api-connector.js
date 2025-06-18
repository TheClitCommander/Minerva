/**
 * Minerva API Connector
 * Real implementation connecting to the actual backend API
 * No fallbacks, no simulations, only real connections
 */

(function() {
  // Configuration
  const API_CONFIG = {
    statusUrl: 'http://127.0.0.1:5505/api/status',
    chatUrl: 'http://127.0.0.1:5505/api/chat',
    projectsUrl: 'http://127.0.0.1:5505/api/projects',
    memoriesUrl: 'http://127.0.0.1:5505/api/memories'
  };

  // Global API status state
  let apiStatus = {
    connected: false,
    lastCheck: null
  };

  /**
   * Check connection to the API
   * @returns {Promise<boolean>} Connection status
   */
  async function checkApiConnection() {
    try {
      console.log('Checking API connection to:', API_CONFIG.statusUrl);
      const response = await fetch(API_CONFIG.statusUrl);
      
      if (response.ok) {
        const data = await response.json();
        console.log('API connected, status:', data);
        apiStatus.connected = true;
        apiStatus.lastCheck = new Date();
        updateUIConnectionStatus('connected');
        return true;
      } else {
        console.error('API returned error status:', response.status);
        apiStatus.connected = false;
        updateUIConnectionStatus('disconnected');
        return false;
      }
    } catch (error) {
      console.error('API connection error:', error);
      apiStatus.connected = false;
      updateUIConnectionStatus('disconnected');
      return false;
    }
  }

  /**
   * Send a chat message to the API
   * @param {string} message The message to send
   * @returns {Promise<object>} The API response
   */
  async function sendChatMessage(message) {
    if (!apiStatus.connected) {
      await checkApiConnection();
      
      if (!apiStatus.connected) {
        throw new Error('Cannot send message: API is not connected');
      }
    }

    const response = await fetch(API_CONFIG.chatUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ message })
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * Update all UI elements showing connection status
   * @param {string} status The connection status (connected|disconnected)
   */
  function updateUIConnectionStatus(status) {
    // Find all status indicators on the page
    const statusElements = document.querySelectorAll('.status-indicator, .status, .connection-status');
    
    statusElements.forEach(element => {
      // Remove existing status classes
      element.classList.remove('connected', 'disconnected', 'initializing');
      
      // Add new status class
      element.classList.add(status);
      
      // If there's a text element inside, update that too
      const textElement = element.querySelector('.status-text');
      if (textElement) {
        textElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
      }
      // If this element itself displays text
      else if (element.classList.contains('status-text')) {
        element.textContent = status.charAt(0).toUpperCase() + status.slice(1);
      }
    });

    // Dispatch event for other components to react to
    window.dispatchEvent(new CustomEvent('minerva-api-status', { 
      detail: { status }
    }));
  }

  /**
   * Start periodic connection checking
   * @param {number} interval Interval in milliseconds
   */
  function startConnectionMonitoring(interval = 15000) {
    // Perform initial check
    checkApiConnection();
    
    // Set up periodic checking
    setInterval(checkApiConnection, interval);
  }

  // Export functions to window
  window.MinervaAPI = {
    checkConnection: checkApiConnection,
    sendChatMessage: sendChatMessage,
    getStatus: () => apiStatus,
    config: API_CONFIG
  };

  // Initialize on DOM content loaded
  document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Minerva API Connector');
    startConnectionMonitoring();
  });
})();
