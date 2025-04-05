/**
 * Think Tank API Interface
 * A global interface to the ThinkTank functionality, including conversation memory
 * This creates a single entry point for accessing conversation history and project data
 */

// Create global ThinkTankAPI object
window.ThinkTankAPI = (function() {
    // Private variables
    let activeConversationId = null;
    const API_BASE_URL = '/api';

    // Initialize from localStorage if available
    if (localStorage.getItem('minerva_conversation_id')) {
        activeConversationId = localStorage.getItem('minerva_conversation_id');
    }

    /**
     * Make an API request with appropriate error handling
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} - Response promise
     */
    async function apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('ThinkTankAPI Error:', error);
            throw error;
        }
    }

    // Return public API
    return {
        /**
         * Set the active conversation ID
         * @param {string} conversationId - Conversation ID
         */
        setActiveConversation: function(conversationId) {
            activeConversationId = conversationId;
            localStorage.setItem('minerva_conversation_id', conversationId);
            console.log('ThinkTankAPI: Active conversation set to', conversationId);
        },
        
        /**
         * Get the active conversation ID
         * @returns {string} - Active conversation ID
         */
        getActiveConversation: function() {
            return activeConversationId;
        },
        
        /**
         * Get conversation history for a specific conversation
         * @param {string} conversationId - Conversation ID to retrieve
         * @returns {Promise<Array>} - Array of message objects
         */
        getConversationHistory: async function(conversationId) {
            try {
                const id = conversationId || activeConversationId;
                
                if (!id) {
                    console.warn('ThinkTankAPI: No conversation ID provided');
                    return [];
                }
                
                return await apiRequest(`/conversations/${id}`);
            } catch (error) {
                console.error('Error getting conversation history:', error);
                return [];
            }
        },
        
        /**
         * Get all conversations
         * @returns {Promise<Array>} - Array of conversation objects
         */
        getAllConversations: async function() {
            try {
                return await apiRequest('/conversations');
            } catch (error) {
                console.error('Error getting all conversations:', error);
                return [];
            }
        },
        
        /**
         * Create a new conversation
         * @param {Object} options - Initial conversation data
         * @returns {Promise<Object>} - New conversation object
         */
        createConversation: async function(options = {}) {
            try {
                const data = await apiRequest('/conversations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(options)
                });
                
                if (data.id) {
                    this.setActiveConversation(data.id);
                }
                
                return data;
            } catch (error) {
                console.error('Error creating conversation:', error);
                throw error;
            }
        },
        
        /**
         * Update a conversation
         * @param {string} conversationId - Conversation ID to update
         * @param {Object} data - Updated conversation data
         * @returns {Promise<Object>} - Updated conversation object
         */
        updateConversation: async function(conversationId, data) {
            try {
                const id = conversationId || activeConversationId;
                
                if (!id) {
                    throw new Error('No conversation ID provided');
                }
                
                return await apiRequest(`/conversations/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
            } catch (error) {
                console.error('Error updating conversation:', error);
                throw error;
            }
        },
        
        /**
         * Delete a conversation
         * @param {string} conversationId - Conversation ID to delete
         * @returns {Promise<boolean>} - Success status
         */
        deleteConversation: async function(conversationId) {
            try {
                const id = conversationId || activeConversationId;
                
                if (!id) {
                    throw new Error('No conversation ID provided');
                }
                
                await apiRequest(`/conversations/${id}`, {
                    method: 'DELETE'
                });
                
                // If deleting the active conversation, clear it
                if (id === activeConversationId) {
                    activeConversationId = null;
                    localStorage.removeItem('minerva_conversation_id');
                }
                
                return true;
            } catch (error) {
                console.error('Error deleting conversation:', error);
                throw error;
            }
        },
        
        /**
         * Add a message to the current conversation
         * @param {Object} message - Message object to add
         * @param {Object} options - Additional options
         * @param {boolean} options.includeProjectContext - Whether to include project context
         * @returns {Promise<Object>} - Updated conversation
         */
        addMessage: async function(message, options = {}) {
            try {
                const { includeProjectContext = true } = options;
                
                if (!activeConversationId) {
                    // Create a new conversation if none exists
                    const newConversation = await this.createConversation({
                        messages: [message]
                    });
                    
                    return newConversation;
                }
                
                // Check if conversation is linked to a project and we should include project context
                let projectContext = null;
                
                // First check if project context was already added to the message by project-context-processor
                if (message.metadata && message.metadata.projectContext) {
                    projectContext = message.metadata.projectContext;
                    console.log('Using existing project context from message metadata:', projectContext);
                }
                // Otherwise, try to add it if includeProjectContext is true
                else if (includeProjectContext) {
                    try {
                        // Try to get conversation info to check if it's linked to a project
                        const conversationInfo = await this.getConversationHistory(activeConversationId);
                        if (conversationInfo && conversationInfo.project) {
                            const projectId = conversationInfo.project;
                            
                            // Get project data if available in memory (window.minervaProjects)
                            if (window.minervaProjects && window.minervaProjects[projectId]) {
                                const project = window.minervaProjects[projectId];
                                projectContext = {
                                    id: projectId,
                                    name: project.name,
                                    description: project.description,
                                    tags: project.tags || []
                                };
                                
                                // Add project context to the message
                                if (!message.metadata) message.metadata = {};
                                message.metadata.projectContext = projectContext;
                                
                                console.log(`Adding project context for ${project.name} to message`);
                            }
                        }
                    } catch (error) {
                        console.error('Error retrieving project context:', error);
                        // Continue without project context rather than failing the entire message
                    }
                }
                
                // Add to existing conversation
                return await apiRequest(`/conversations/${activeConversationId}/messages`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(message)
                });
            } catch (error) {
                console.error('Error adding message:', error);
                throw error;
            }
        },
        
        /**
         * Get all projects
         * @returns {Promise<Array>} - Array of project objects
         */
        getAllProjects: async function() {
            try {
                return await apiRequest('/projects');
            } catch (error) {
                console.error('Error getting projects:', error);
                return [];
            }
        },
        
        /**
         * Create a new project
         * @param {Object} projectData - Project data
         * @returns {Promise<Object>} - New project object
         */
        createProject: async function(projectData) {
            try {
                return await apiRequest('/projects', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });
            } catch (error) {
                console.error('Error creating project:', error);
                throw error;
            }
        },
        
        /**
         * Convert a conversation to a project
         * @param {string} conversationId - Conversation ID
         * @param {Object} projectData - New project data
         * @returns {Promise<Object>} - New project object
         */
        conversationToProject: async function(conversationId, projectData) {
            try {
                const id = conversationId || activeConversationId;
                
                if (!id) {
                    throw new Error('No conversation ID provided');
                }
                
                return await apiRequest(`/conversations/${id}/to-project`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });
            } catch (error) {
                console.error('Error converting conversation to project:', error);
                throw error;
            }
        },
        
        /**
         * Get project conversation history
         * @param {string} projectId - Project ID
         * @returns {Promise<Array>} - Array of conversations in this project
         */
        getProjectConversations: async function(projectId) {
            try {
                return await apiRequest(`/projects/${projectId}/conversations`);
            } catch (error) {
                console.error('Error getting project conversations:', error);
                return [];
            }
        },
        
        /**
         * Update a project
         * @param {string} projectId - Project ID to update
         * @param {Object} projectData - New project data
         * @returns {Promise<Object>} - Updated project object
         */
        updateProject: async function(projectId, projectData) {
            try {
                if (!projectId) {
                    throw new Error('No project ID provided');
                }
                
                return await apiRequest(`/projects/${projectId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(projectData)
                });
            } catch (error) {
                console.error('Error updating project:', error);
                throw error;
            }
        },
        
        /**
         * Delete a project
         * @param {string} projectId - Project ID to delete
         * @returns {Promise<boolean>} - Success status
         */
        deleteProject: async function(projectId) {
            try {
                if (!projectId) {
                    throw new Error('No project ID provided');
                }
                
                await apiRequest(`/projects/${projectId}`, {
                    method: 'DELETE'
                });
                
                return true;
            } catch (error) {
                console.error('Error deleting project:', error);
                throw error;
            }
        },
        
        /**
         * Add a conversation to a project
         * @param {string} projectId - Project ID
         * @param {string} conversationId - Conversation ID to add
         * @returns {Promise<Object>} - Updated project object
         */
        addConversationToProject: async function(projectId, conversationId) {
            try {
                if (!projectId || !conversationId) {
                    throw new Error('Project ID and conversation ID are required');
                }
                
                return await apiRequest(`/projects/${projectId}/conversations`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ conversationId })
                });
            } catch (error) {
                console.error('Error adding conversation to project:', error);
                throw error;
            }
        },
        
        /**
         * Assign a conversation to a project (or reassign to a different project)
         * @param {string} conversationId - Conversation ID to assign
         * @param {string} projectId - Project ID to assign to
         * @returns {Promise<Object>} - Updated conversation object
         */
        assignConversationToProject: async function(conversationId, projectId) {
            try {
                if (!conversationId) {
                    throw new Error('Conversation ID is required');
                }
                
                return await apiRequest(`/conversations/${conversationId}/project`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ projectId })
                });
            } catch (error) {
                console.error('Error assigning conversation to project:', error);
                throw error;
            }
        },
        
        /**
         * Generate a title for a conversation based on its content
         * @param {string} conversationId - ID of the conversation to generate title for
         * @param {boolean} updateConversation - Whether to update the conversation with the new title
         * @returns {Promise<string>} - Generated title
         */
        generateConversationTitle: async function(conversationId, updateConversation = true) {
            try {
                if (!conversationId) {
                    throw new Error('Conversation ID is required');
                }
                
                // Get conversation if not already in memory
                let conversation;
                if (conversationId === activeConversationId && currentConversation) {
                    conversation = currentConversation;
                } else {
                    conversation = await this.loadConversation(conversationId);
                }
                
                // Make sure the conversation has messages
                if (!conversation || !conversation.messages || conversation.messages.length < 1) {
                    return 'Untitled Conversation';
                }
                
                // Extract content from first few messages for title generation
                const titleContent = conversation.messages
                    .slice(0, Math.min(3, conversation.messages.length))
                    .map(msg => msg.content || msg.message || '')
                    .join(' ')
                    .substring(0, 500); // Limit to 500 chars to avoid excessively long requests
                
                // Request title generation from backend
                const response = await apiRequest(`/conversations/generate-title`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        conversationId,
                        content: titleContent
                    })
                });
                
                const generatedTitle = response.title || 'Untitled Conversation';
                
                // Update the conversation with the new title if requested
                if (updateConversation && conversationId) {
                    await this.updateConversation(conversationId, { title: generatedTitle });
                    
                    // Update local conversation if it's the active one
                    if (conversationId === activeConversationId && currentConversation) {
                        currentConversation.title = generatedTitle;
                    }
                }
                
                return generatedTitle;
            } catch (error) {
                console.error('Error generating conversation title:', error);
                return 'Untitled Conversation';
            }
        },
        
        /**
         * Generate a summary for a conversation
         * @param {string} conversationId - ID of the conversation to summarize
         * @param {boolean} updateConversation - Whether to update the conversation with the summary
         * @returns {Promise<Object>} - Object with summary and key points
         */
        summarizeConversation: async function(conversationId, updateConversation = true) {
            try {
                if (!conversationId) {
                    throw new Error('Conversation ID is required');
                }
                
                // Get conversation if not already in memory
                let conversation;
                if (conversationId === activeConversationId && currentConversation) {
                    conversation = currentConversation;
                } else {
                    conversation = await this.loadConversation(conversationId);
                }
                
                // Make sure the conversation has enough messages to summarize
                if (!conversation || !conversation.messages || conversation.messages.length < 3) {
                    return { 
                        summary: 'This conversation is too short to summarize.', 
                        keyPoints: ['Not enough content for key points']
                    };
                }
                
                // Extract all message content for summary generation
                const conversationContent = conversation.messages
                    .map(msg => {
                        const role = msg.role || (msg.isUser ? 'user' : 'assistant');
                        const content = msg.content || msg.message || '';
                        return `${role}: ${content}`;
                    })
                    .join('\n\n')
                    .substring(0, 5000); // Limit to 5000 chars to avoid excessively long requests
                
                // Request summary generation from backend
                const response = await apiRequest(`/conversations/summarize`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        conversationId,
                        content: conversationContent
                    })
                });
                
                const summary = {
                    summary: response.summary || 'No summary available.',
                    keyPoints: response.keyPoints || []
                };
                
                // Update the conversation with the summary if requested
                if (updateConversation && conversationId) {
                    await this.updateConversation(conversationId, { summary: summary });
                    
                    // Update local conversation if it's the active one
                    if (conversationId === activeConversationId && currentConversation) {
                        currentConversation.summary = summary;
                    }
                }
                
                return summary;
            } catch (error) {
                console.error('Error generating conversation summary:', error);
                return { 
                    summary: 'Could not generate summary.', 
                    keyPoints: ['Error occurred during summarization']
                };
            }
        },
        
        /**
         * Optimize conversation context for AI by intelligently handling long conversations
         * - Keeps recent messages intact
         * - Summarizes older message chunks to reduce context window usage
         * - Maintains critical context while reducing token usage
         * 
         * @param {string} conversationId - ID of the conversation to optimize
         * @param {Object} options - Options for context optimization
         * @param {number} options.maxMessages - Maximum number of full messages to include (default: 10)
         * @param {number} options.recentMessagesToKeep - Number of most recent messages to always keep intact (default: 6)
         * @param {boolean} options.includeSummary - Whether to include conversation summary in context (default: true)
         * @returns {Promise<Array>} - Optimized messages array for context window
         */
        optimizeConversationContext: async function(conversationId, options = {}) {
            try {
                if (!conversationId) {
                    throw new Error('Conversation ID is required');
                }
                
                // Default options
                const {
                    maxMessages = 10,
                    recentMessagesToKeep = 6,
                    includeSummary = true
                } = options;
                
                // Get conversation if not already in memory
                let conversation;
                if (conversationId === activeConversationId && currentConversation) {
                    conversation = currentConversation;
                } else {
                    conversation = await this.loadConversation(conversationId);
                }
                
                if (!conversation || !conversation.messages || conversation.messages.length === 0) {
                    return [];
                }
                
                const messages = [...conversation.messages];
                
                // If conversation is short enough, just return all messages
                if (messages.length <= maxMessages) {
                    return messages;
                }
                
                // Get or generate conversation summary if needed
                let conversationSummary = '';
                if (includeSummary) {
                    if (!conversation.summary) {
                        // Generate summary if it doesn't exist
                        const summaryResult = await this.summarizeConversation(conversationId);
                        conversationSummary = summaryResult.summary;
                    } else {
                        conversationSummary = conversation.summary.summary || '';
                    }
                }
                
                // Keep the first message (often contains important context/instructions)
                const firstMessage = messages[0];
                
                // Keep the most recent messages intact
                const recentMessages = messages.slice(-recentMessagesToKeep);
                
                // Calculate how many middle messages we can include
                const middleMessageCount = maxMessages - recentMessagesToKeep - 1; // -1 for first message
                
                // Determine which middle messages to keep or summarize
                let optimizedContext = [];
                
                // Add first message
                optimizedContext.push(firstMessage);
                
                // Add summary as a system message if available
                if (conversationSummary && includeSummary) {
                    optimizedContext.push({
                        role: 'system',
                        content: `Previous conversation summary: ${conversationSummary}`,
                        isMemory: true,
                        timestamp: new Date().toISOString()
                    });
                }
                
                // Add middle messages or their summary depending on length
                if (messages.length - recentMessagesToKeep - 1 > middleMessageCount) {
                    // Too many middle messages, need to summarize
                    // Take a portion of the middle messages that fit our budget
                    if (middleMessageCount > 0) {
                        // Spaced sampling to get representative messages from the middle
                        const middleMessages = messages.slice(1, -recentMessagesToKeep);
                        const step = Math.max(1, Math.floor(middleMessages.length / middleMessageCount));
                        
                        for (let i = 0; i < middleMessageCount && i * step < middleMessages.length; i++) {
                            optimizedContext.push(middleMessages[i * step]);
                        }
                    }
                } else {
                    // We can include all middle messages
                    optimizedContext = optimizedContext.concat(messages.slice(1, -recentMessagesToKeep));
                }
                
                // Add recent messages
                optimizedContext = optimizedContext.concat(recentMessages);
                
                return optimizedContext;
            } catch (error) {
                console.error('Error optimizing conversation context:', error);
                // In case of error, return the unmodified messages if available
                if (conversationId === activeConversationId && currentConversation && currentConversation.messages) {
                    return currentConversation.messages;
                }
                return [];
            }
        }
    };
})();
