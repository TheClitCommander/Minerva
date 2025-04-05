/**
 * Minerva Chat Connector
 * 
 * This script provides a connection layer between the Minerva chat interface
 * and the Think Tank API, ensuring reliable connections and real answers.
 */

// Configuration for the chat connector
const CHAT_CONFIG = {
    // Available endpoints to try (in order of preference)
    endpoints: [
        // First try the standard Think Tank API on the main server
        "/api/think-tank",
        // Then try our dedicated chat bridge server (running on port 8090)
        "http://localhost:8090/api/think-tank",
        // Fall back to legacy chat endpoint if needed
        "/api/chat/message",
        "http://localhost:8090/api/chat/message"
    ],
    // Debug mode for development
    debug: false,
    // Retry settings
    maxRetries: 3,
    retryDelay: 500,
    // Model preferences
    modelPreferences: {
        priority: ["gpt-4o", "claude-3-opus", "gpt-4"],
        complexity: 0.7
    }
};

/**
 * Send a message to the Think Tank API with automatic fallback and retry
 * 
 * @param {string} message - The user message to send
 * @param {string} conversationId - The conversation ID for persistence
 * @param {function} onSuccess - Callback for successful responses
 * @param {function} onError - Callback for errors
 * @param {function} onTyping - Callback for typing indicator
 */
function sendMessageToThinkTank(message, conversationId, onSuccess, onError, onTyping) {
    // Show typing indicator
    if (onTyping) onTyping(true);
    
    // Save the original conversation ID
    const originalConversationId = conversationId || ('conv-' + Date.now());
    
    // Create the payload
    const payload = {
        message: message,
        conversation_id: originalConversationId,
        store_in_memory: true,
        client_version: '1.0.2',
        model_preferences: CHAT_CONFIG.modelPreferences
    };
    
    // Log if in debug mode
    if (CHAT_CONFIG.debug) {
        console.log("Sending message to Think Tank:", message);
        console.log("Payload:", payload);
    }
    
    // Try endpoints sequentially with retry logic
    tryEndpoint(0, 0);
    
    // Function to try an endpoint with retry capability
    function tryEndpoint(endpointIndex, retryCount) {
        // If we've tried all endpoints, call the error handler
        if (endpointIndex >= CHAT_CONFIG.endpoints.length) {
            if (onTyping) onTyping(false);
            if (onError) onError("All endpoints failed. The server may be unavailable.");
            saveMessageLocally(message, originalConversationId);
            return;
        }
        
        // Get the current endpoint
        const apiUrl = CHAT_CONFIG.endpoints[endpointIndex];
        
        if (CHAT_CONFIG.debug) {
            console.log(`Trying endpoint ${endpointIndex} (${apiUrl}), attempt ${retryCount + 1}`);
        }
        
        // Make the API call
        fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Session-ID": originalConversationId
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Log if in debug mode
            if (CHAT_CONFIG.debug) {
                console.log("Think Tank response:", data);
            }
            
            // If we got a successful response, save this endpoint as preferred
            localStorage.setItem('minerva_preferred_endpoint', apiUrl);
            
            // Process the response
            if (onTyping) onTyping(false);
            if (onSuccess) onSuccess(data);
        })
        .catch(error => {
            console.error(`Error with endpoint ${apiUrl}:`, error);
            
            // If we have retries left for this endpoint, retry
            if (retryCount < CHAT_CONFIG.maxRetries) {
                setTimeout(() => {
                    tryEndpoint(endpointIndex, retryCount + 1);
                }, CHAT_CONFIG.retryDelay);
            } else {
                // Otherwise, try the next endpoint
                tryEndpoint(endpointIndex + 1, 0);
            }
        });
    }
}

/**
 * Extract the response text from a Think Tank API response
 * 
 * @param {object} data - The API response data
 * @returns {string} The extracted response text
 */
function extractResponseText(data) {
    // Handle different response formats
    if (data.response && typeof data.response === 'string') {
        return data.response;
    } else if (data.think_tank_result && data.think_tank_result.response) {
        return data.think_tank_result.response;
    } else if (data.blended_response) {
        return data.blended_response;
    } else if (data.message) {
        return data.message;
    } else if (data.text || data.content || data.answer) {
        return data.text || data.content || data.answer;
    }
    
    // If no response found, return a fallback
    return "Sorry, I couldn't generate a response at this time.";
}

/**
 * Extract model information from a Think Tank API response
 * 
 * @param {object} data - The API response data
 * @returns {object} The extracted model information
 */
function extractModelInfo(data) {
    // Handle different model info formats
    let modelInfo = data.model_info || {};
    
    if (data.think_tank_result && data.think_tank_result.model_info) {
        modelInfo = data.think_tank_result.model_info;
    }
    
    return modelInfo;
}

/**
 * Save a message locally for offline use
 * 
 * @param {string} message - The user message
 * @param {string} conversationId - The conversation ID
 */
function saveMessageLocally(message, conversationId) {
    // Get existing stored messages
    let storedMessages = JSON.parse(localStorage.getItem('minerva_offline_messages') || '{}');
    
    // Initialize conversation if it doesn't exist
    if (!storedMessages[conversationId]) {
        storedMessages[conversationId] = [];
    }
    
    // Add the new message
    storedMessages[conversationId].push({
        text: message,
        timestamp: Date.now(),
        sender: 'user'
    });
    
    // Save back to local storage
    localStorage.setItem('minerva_offline_messages', JSON.stringify(storedMessages));
    console.log("Message saved locally for offline use");
}

// Export the functions for use in other scripts
window.MinervaChat = {
    sendMessage: sendMessageToThinkTank,
    extractResponseText: extractResponseText,
    extractModelInfo: extractModelInfo,
    config: CHAT_CONFIG
};
