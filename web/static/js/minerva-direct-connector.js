/**
 * Minerva Direct Connector
 * A simplified, robust connector for Minerva Assistant
 */

class MinervaDirectConnector {
    constructor(options = {}) {
        this.config = {
            debug: true,
            // Connect directly to Think Tank API endpoint
            primaryEndpoint: '/api/think-tank',  // Local API endpoint within the same domain
            fallbackEndpoint: '/api/chat/message',
            retryAttempts: 2, // Increased for better reliability
            storeConversations: true, // Enable conversation memory
            ...options
        };
        
        this.conversationId = localStorage.getItem('minerva_conversation_id') || null;
        this.userId = localStorage.getItem('minerva_user_id') || `user-${Date.now()}`;
        this.projectId = localStorage.getItem('minerva_current_project') || 'default';
        
        // Initialize conversation history
        this.conversationHistory = this._loadConversationHistory();
        
        // Save user ID for consistency
        localStorage.setItem('minerva_user_id', this.userId);
        
        this.debugLog('Minerva Direct Connector initialized', {
            conversationId: this.conversationId,
            userId: this.userId
        });
    }
    
    debugLog(...args) {
        if (this.config.debug) {
            console.log('[MinervaConnector]', ...args);
            
            // Update debug panel if it exists
            const debugPanel = document.getElementById('debug-output');
            if (debugPanel) {
                const message = args.map(arg => 
                    typeof arg === 'object' ? JSON.stringify(arg) : arg
                ).join(' ');
                debugPanel.innerHTML += `<br>${message}`;
                debugPanel.scrollTop = debugPanel.scrollHeight;
            }
        }
    }
    
    /**
     * Set the project context
     */
    setProject(projectId) {
        if (projectId) {
            this.projectId = projectId;
            localStorage.setItem('minerva_current_project', projectId);
            this.debugLog(`Project set to: ${projectId}`);
            return true;
        }
        return false;
    }

    /**
     * Send message directly to Think Tank API
     * This method can be called with either (message, onSuccess, onError) or 
     * (message, context, onSuccess, onError) signature to maintain backward compatibility
     */
    sendMessage(message, contextOrCallback, onSuccessOrNull, onErrorOrNull) {
        let context = {};
        let onSuccess = null;
        let onError = null;
        
        // Detect if the second parameter is a context object or a callback function
        if (typeof contextOrCallback === 'function') {
            // It's a callback function (message, onSuccess, onError)
            onSuccess = contextOrCallback;
            onError = onSuccessOrNull;
        } else if (typeof contextOrCallback === 'object' && contextOrCallback !== null) {
            // It's a context object (message, context, onSuccess, onError)
            context = contextOrCallback;
            onSuccess = onSuccessOrNull;
            onError = onErrorOrNull;
        } else if (contextOrCallback === undefined) {
            // No second argument was provided
            onSuccess = null;
            onError = null;
        }
        
        // Validate the message
        if (!message || !message.trim()) {
            if (onError) onError({ error: 'Empty message' });
            return;
        }
        
        this.debugLog(`Sending message: ${message}`, context);
        
        // Add to conversation history
        const userMessage = {
            role: 'user',
            content: message,
            timestamp: Date.now(),
            id: `msg-${Date.now()}`
        };
        
        // Store the user message in history
        this._addToConversationHistory(userMessage);
        
        // Use project ID from context if provided
        if (context && context.projectId) {
            this.setProject(context.projectId);
        }
        
        // Prepare payload
        const payload = {
            message: message,
            conversation_id: this.conversationId || `conv-${Date.now()}`,
            store_in_memory: true,
            client_version: '1.0.2',
            user_id: this.userId,
            project_id: this.projectId
        };
        
        // Directly use the bridge server endpoint
        const endpoint = this.config.primaryEndpoint;
        this.debugLog(`Sending to endpoint: ${endpoint}`);
        
        // Log full request details for debugging
        this.debugLog(`Request payload:`, JSON.stringify(payload));
        
        // Enhanced fetch to the bridge server with more explicit CORS handling
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // Explicitly use 'cors' mode for cross-origin requests
            mode: 'cors',
            credentials: 'omit',  // Don't send credentials for this API
            body: JSON.stringify(payload)
        })
        .then(response => {
            this.debugLog(`Response status:`, response.status);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.debugLog('Success response:', data);
            
            // Store conversation ID
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
            }
            
            // Process the response
            const processedResponse = this._processResponse(data);
            
            // Call success callback
            if (onSuccess) {
                onSuccess(processedResponse);
            }
        })
        .catch(error => {
            this.debugLog(`Error with endpoint ${endpoint}:`, error);
            console.error('Detailed error:', error);
            
            // Store message offline
            this._storeOfflineMessage(message);
            
            if (onError) {
                onError({
                    error: error.message || 'Unknown error',
                    offline: true
                });
            }
        });
    }
    
    /**
     * Try sending to multiple endpoints
     */
    _tryEndpoints(endpoints, payload, onSuccess, onError, currentIndex = 0) {
        if (currentIndex >= endpoints.length) {
            this.debugLog('All endpoints failed');
            
            // Store message offline
            this._storeOfflineMessage(payload.message);
            
            if (onError) {
                onError({
                    error: 'All endpoints failed',
                    offline: true
                });
            }
            return;
        }
        
        const endpoint = endpoints[currentIndex];
        this.debugLog(`Trying endpoint ${currentIndex + 1}/${endpoints.length}: ${endpoint}`);
        
        // Log full request details for debugging
        this.debugLog(`Request payload:`, JSON.stringify(payload));
        
        // Create timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            this.debugLog(`Timeout occurred for endpoint: ${endpoint}`);
            controller.abort();
        }, 15000); // 15 second timeout
        
        // Log detailed fetch information
        this.debugLog(`Starting fetch to: ${endpoint}`);
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': payload.conversation_id
                // Removed Access-Control-Allow-Origin header which should be set by the server, not the client
            },
            mode: 'cors', // This is important for cross-origin requests
            body: JSON.stringify(payload),
            signal: controller.signal,
            credentials: 'same-origin' // This might help with cookies if needed
        })
        .then(response => {
            clearTimeout(timeoutId);
            this.debugLog(`Response received from ${endpoint}:`, {
                status: response.status,
                statusText: response.statusText,
                headers: Array.from(response.headers.entries())
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            this.debugLog('Success response:', data);
            
            // Store conversation ID
            if (data.conversation_id) {
                this.conversationId = data.conversation_id;
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
            }
            
            // Process the response
            const processedResponse = this._processResponse(data);
            
            // Call success callback
            if (onSuccess) {
                onSuccess(processedResponse);
            }
        })
        .catch(error => {
            clearTimeout(timeoutId);
            
            // Enhanced error logging
            let errorDetails = {
                message: error.message,
                name: error.name,
                stack: error.stack
            };
            
            if (error.name === 'AbortError') {
                errorDetails.reason = 'Request timed out after 15 seconds';
            } else if (error.name === 'TypeError') {
                errorDetails.reason = 'Network error - check if server is accessible';
            }
            
            this.debugLog(`Error with endpoint ${endpoint}:`, errorDetails);
            console.error('Detailed error:', error);
            
            // Try next endpoint with a slight delay
            this.debugLog(`Will try next endpoint in 300ms...`);
            setTimeout(() => {
                this._tryEndpoints(endpoints, payload, onSuccess, onError, currentIndex + 1);
            }, 300);
        });
    }
    
    /**
     * Process the Think Tank response into a standard format
     */
    _processResponse(data) {
        this.debugLog('Processing response data:', data);
        
        // Extract text
        let responseText = null;
        if (typeof data.response === 'string') {
            responseText = data.response;
        } else if (data.think_tank_result && data.think_tank_result.response) {
            responseText = data.think_tank_result.response;
        } else if (data.blended_response) {
            responseText = data.blended_response;
        } else if (data.message) {
            responseText = data.message;
        } else if (data.text || data.content || data.answer) {
            responseText = data.text || data.content || data.answer;
        } else {
            responseText = "Received response in unknown format";
        }
        
        // Extract model info
        let modelInfo = null;
        if (data.model_info) {
            modelInfo = data.model_info;
        } else if (data.think_tank_result && data.think_tank_result.model_info) {
            modelInfo = data.think_tank_result.model_info; 
        } else {
            modelInfo = { primary_model: "Think Tank" };
        }
        
        // Extract conversation ID
        let conversationId = null;
        if (data.conversation_id) {
            conversationId = data.conversation_id;
        } else if (data.conversationId) {
            conversationId = data.conversationId;
        }
        
        // Debug the extracted values
        this.debugLog('Extracted values:', {
            responseText,
            modelInfo,
            conversationId
        });
        
        // Build a response object that's compatible with the floating chat interface
        const response = {
            // Standard fields expected by our connector
            text: responseText,
            response: responseText, // Duplicate for compatibility
            conversationId: conversationId || data.conversation_id || this.conversationId, // Important for the UI
            modelInfo: modelInfo,
            model_info: modelInfo, // Duplicate for compatibility
            conversation_id: data.conversation_id || this.conversationId, // Duplicate for compatibility
            raw: data,
            
            // Additional fields used by the floating chat
            status: data.status || 'success',
            canCreateProject: true,  // Allow project creation functionality
            
            // Memory-related fields
            memory_id: data.memory_id || null,
            memory_info: data.memory_info || {}
        };
        
        this.debugLog('Processed response:', response);
        return response;
    }
    
    /**
     * Store message for offline processing
     */
    _storeOfflineMessage(message) {
        const offlineMessages = JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
        offlineMessages.push({
            message,
            timestamp: Date.now()
        });
        localStorage.setItem('minerva_offline_messages', JSON.stringify(offlineMessages));
        this.debugLog('Stored message offline for future sending');
    }
    
    /**
     * Get offline messages
     */
    getOfflineMessages() {
        return JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
    }
    
    /**
     * Clear offline messages
     */
    clearOfflineMessages() {
        localStorage.removeItem('minerva_offline_messages');
        this.debugLog('Cleared offline messages');
    }
    
    /**
     * Get conversation history
     */
    getConversationHistory() {
        return this.conversationHistory;
    }
    
    /**
     * Set current project
     */
    setProject(projectId) {
        this.projectId = projectId;
        localStorage.setItem('minerva_current_project', projectId);
        
        // Load conversation history for this project
        this.conversationHistory = this._loadConversationHistory();
        
        // Create a new conversation ID for this project if needed
        if (!this.conversationId || this.conversationId.indexOf(projectId) === -1) {
            this.conversationId = `${projectId}-conv-${Date.now()}`;
            localStorage.setItem('minerva_conversation_id', this.conversationId);
        }
        
        this.debugLog(`Switched to project: ${projectId}`);
        return this.conversationHistory;
    }
    
    /**
     * Convert current conversation to a project
     */
    convertToProject(projectName) {
        // Generate a project ID
        const projectId = `project-${Date.now()}`;
        
        // Get existing projects
        const projects = JSON.parse(localStorage.getItem('minerva_projects') || '[]');
        
        // Create new project
        const newProject = {
            id: projectId,
            name: projectName,
            created: Date.now(),
            conversations: [this.conversationId]
        };
        
        // Add project
        projects.push(newProject);
        localStorage.setItem('minerva_projects', JSON.stringify(projects));
        
        // Switch to this project
        this.setProject(projectId);
        
        this.debugLog(`Converted conversation to project: ${projectName}`);
        return newProject;
    }
    
    /**
     * Load conversation history from storage
     */
    _loadConversationHistory() {
        const key = `minerva_conversation_${this.conversationId || 'default'}`;
        return JSON.parse(localStorage.getItem(key) || '[]');
    }
    
    /**
     * Add message to conversation history
     */
    _addToConversationHistory(message) {
        if (!this.config.storeConversations) return;
        
        // Add message to history
        this.conversationHistory.push(message);
        
        // Store in localStorage
        const key = `minerva_conversation_${this.conversationId || 'default'}`;
        localStorage.setItem(key, JSON.stringify(this.conversationHistory));
        
        this.debugLog(`Added message to history. Total: ${this.conversationHistory.length}`);
    }
}

// Make available globally
if (typeof window !== 'undefined') {
    window.MinervaDirectConnector = MinervaDirectConnector;
}
