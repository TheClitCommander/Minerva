/**
 * Minerva Think Tank Connector
 * 
 * A dedicated client for connecting the Minerva Chat interface to the Think Tank API
 * with robust fallback mechanisms, conversation memory, and project organization support.
 */

class MinervaThinkTankConnector {
    constructor(options = {}) {
        // Configuration
        this.config = {
            primaryEndpoint: '/api/think-tank',
            bridgeEndpoint: 'http://localhost:8090/api/think-tank',
            legacyEndpoint: '/api/chat/message',
            retryAttempts: 3,
            enableOfflineStorage: true,
            defaultTimeout: 30000,
            ...options
        };
        
        // Internal state
        this.conversationId = localStorage.getItem('minerva_conversation_id') || null;
        this.lastUsedEndpoint = localStorage.getItem('minerva_preferred_endpoint') || null;
        this.userId = localStorage.getItem('minerva_user_id') || ('user-' + Date.now());
        
        // Save user ID
        localStorage.setItem('minerva_user_id', this.userId);
        
        console.log('MinervaThinkTankConnector initialized', {
            conversationId: this.conversationId,
            preferredEndpoint: this.lastUsedEndpoint
        });
    }
    
    /**
     * Send a message to the Think Tank API with automatic fallback
     * 
     * @param {string} message - The user's message
     * @param {object} context - Optional context (project, etc.)
     * @param {function} onResponse - Callback for successful response
     * @param {function} onError - Callback for error
     * @param {function} onProgress - Callback for progress updates
     */
    sendMessage(message, context = {}, onResponse, onError, onProgress) {
        // Format context correctly
        const projectContext = context.projectId ? { project_id: context.projectId } : {};
        
        // Create the payload in the format expected by Think Tank
        const payload = {
            message: message,
            conversation_id: this.conversationId || ('conv-' + Date.now()),
            store_in_memory: true,
            client_version: '1.0.2',
            user_id: this.userId,
            ...projectContext
        };
        
        // Progress updates
        if (onProgress) {
            onProgress({ status: 'starting', message: 'Connecting to Think Tank...' });
        }
        
        // Determine endpoints to try in priority order
        let endpoints = this._prioritizeEndpoints();
        
        // Try sending to the first endpoint
        this._trySendToEndpoint(endpoints, 0, payload, onResponse, onError, onProgress);
    }
    
    /**
     * Prioritize endpoints based on previous success
     */
    _prioritizeEndpoints() {
        let endpoints = [
            this.config.bridgeEndpoint,   // Bridge is most reliable
            this.config.primaryEndpoint,  // Primary endpoint
            this.config.legacyEndpoint    // Legacy fallback
        ];
        
        // If we have a successful endpoint from before, try it first
        if (this.lastUsedEndpoint) {
            endpoints = endpoints.filter(e => e !== this.lastUsedEndpoint);
            endpoints.unshift(this.lastUsedEndpoint);
        }
        
        return endpoints;
    }
    
    /**
     * Try sending to an endpoint with automatic fallback
     */
    _trySendToEndpoint(endpoints, index, payload, onResponse, onError, onProgress, previousErrors = []) {
        // If we've exhausted all endpoints
        if (index >= endpoints.length) {
            console.error('All endpoints failed', previousErrors);
            
            // Store message for later retry if enabled
            if (this.config.enableOfflineStorage) {
                this._storeOfflineMessage(payload.message);
            }
            
            if (onError) {
                onError({
                    error: 'All connection attempts failed',
                    details: previousErrors,
                    offline: true
                });
            }
            return;
        }
        
        // Get the current endpoint
        const endpoint = endpoints[index];
        
        // Add slight delay between retries to prevent overwhelming the server
        const retryDelay = index * 300;
        
        // Progress update
        if (onProgress) {
            onProgress({
                status: 'connecting',
                message: `Connecting to endpoint ${index + 1}/${endpoints.length}...`, 
                endpoint
            });
        }
        
        // Timeout handling
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.defaultTimeout);
        
        // Wait for the retry delay
        setTimeout(() => {
            console.log(`Attempting connection to: ${endpoint} (attempt ${index + 1}/${endpoints.length})`);
            
            // Make the request
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': payload.conversation_id,
                    'Access-Control-Allow-Origin': '*'
                },
                mode: 'cors',
                body: JSON.stringify(payload),
                signal: controller.signal
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                clearTimeout(timeoutId);
                console.log("Think Tank API response:", data);
                
                // Store successful endpoint
                this.lastUsedEndpoint = endpoint;
                localStorage.setItem('minerva_preferred_endpoint', endpoint);
                
                // Store conversation ID
                if (data.conversation_id) {
                    this.conversationId = data.conversation_id;
                    localStorage.setItem('minerva_conversation_id', data.conversation_id);
                }
                
                // Process any offline messages if this was successful
                if (this.config.enableOfflineStorage) {
                    this._processOfflineMessages();
                }
                
                // Format the response
                const processedResponse = this._processResponse(data);
                
                // Call success callback
                if (onResponse) {
                    onResponse(processedResponse);
                }
            })
            .catch(error => {
                console.error(`Error with endpoint ${endpoint}:`, error);
                previousErrors.push({ endpoint, error: error.message });
                
                // Try the next endpoint
                this._trySendToEndpoint(
                    endpoints, 
                    index + 1, 
                    payload, 
                    onResponse, 
                    onError, 
                    onProgress,
                    previousErrors
                );
            });
        }, retryDelay);
    }
    
    /**
     * Process the Think Tank response into a standard format
     */
    _processResponse(data) {
        // Extract the main response text
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
        } else if (data.response) {
            // Try to stringify object if needed
            try {
                responseText = JSON.stringify(data.response);
            } catch (e) {
                responseText = "Received response in unexpected format";
            }
        } else {
            responseText = "No response received from server";
        }
        
        // Extract model info
        let modelInfo = null;
        if (data.think_tank_result && data.think_tank_result.model_info) {
            modelInfo = data.think_tank_result.model_info;
        } else if (data.model_info) {
            modelInfo = data.model_info;
        } else if (data.models) {
            modelInfo = { primary_model: Array.isArray(data.models) ? data.models[0] : data.models };
        } else {
            modelInfo = { primary_model: "Think Tank" };
        }
        
        // Check if this conversation can be turned into a project
        const canCreateProject = data.can_create_project || false;
        
        // Return standardized response
        return {
            response: responseText,
            modelInfo: modelInfo,
            conversationId: data.conversation_id || this.conversationId,
            canCreateProject: canCreateProject,
            raw: data // Include raw data for special handling
        };
    }
    
    /**
     * Store message for offline processing
     */
    _storeOfflineMessage(message) {
        const offlineMessages = JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
        offlineMessages.push({
            type: 'user',
            content: message,
            timestamp: Date.now()
        });
        localStorage.setItem('minerva_offline_messages', JSON.stringify(offlineMessages));
        console.log('Stored message for offline processing', message);
    }
    
    /**
     * Check and process any stored offline messages
     */
    _processOfflineMessages() {
        const offlineMessages = JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
        if (offlineMessages.length > 0) {
            console.log(`Found ${offlineMessages.length} offline messages to process`);
            // We don't process them automatically to prevent spam
            // Just notify that they exist
            return offlineMessages;
        }
        return [];
    }
    
    /**
     * Get any stored offline messages
     */
    getOfflineMessages() {
        return JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
    }
    
    /**
     * Clear offline messages
     */
    clearOfflineMessages() {
        localStorage.removeItem('minerva_offline_messages');
    }
    
    /**
     * Create a new conversation
     */
    createNewConversation() {
        this.conversationId = 'conv-' + Date.now();
        localStorage.setItem('minerva_conversation_id', this.conversationId);
        return this.conversationId;
    }
}

// Export globally if in browser
if (typeof window !== 'undefined') {
    window.MinervaThinkTankConnector = MinervaThinkTankConnector;
}
