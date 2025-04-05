/**
 * Project Context Processor
 * This module enhances AI requests with project-specific context
 * and processes responses to ensure project awareness
 */

class ProjectContextProcessor {
    constructor() {
        this.initialized = false;
        this.settings = {
            enabled: true,
            enhancePrompts: true,
            debugMode: false
        };
        
        // Initialize from localStorage
        this.loadSettings();
    }
    
    /**
     * Initialize the processor and set up event listeners
     */
    init() {
        if (this.initialized) return;
        
        console.log('Initializing Project Context Processor');
        
        // Listen for new messages being sent
        document.addEventListener('minerva:message:sending', this.handleMessageSending.bind(this));
        
        // Listen for responses being received
        document.addEventListener('minerva:message:received', this.handleMessageReceived.bind(this));
        
        // Listen for project assignments
        document.addEventListener('minerva:conversation:assigned', this.handleConversationAssigned.bind(this));
        
        this.initialized = true;
    }
    
    /**
     * Load settings from localStorage
     */
    loadSettings() {
        try {
            const savedSettings = localStorage.getItem('minerva_project_context_processor');
            if (savedSettings) {
                const parsed = JSON.parse(savedSettings);
                this.settings = { ...this.settings, ...parsed };
            }
        } catch (e) {
            console.error('Failed to load Project Context Processor settings:', e);
        }
    }
    
    /**
     * Save settings to localStorage
     */
    saveSettings() {
        try {
            localStorage.setItem('minerva_project_context_processor', JSON.stringify(this.settings));
        } catch (e) {
            console.error('Failed to save Project Context Processor settings:', e);
        }
    }
    
    /**
     * Handle a message being sent to the AI
     * @param {CustomEvent} event - Event containing message details
     */
    handleMessageSending(event) {
        if (!this.settings.enabled) return;
        
        const message = event.detail.message;
        const conversationId = event.detail.conversationId;
        
        if (!message || !conversationId) return;
        
        // Enhance the message with project context if available
        this.enhanceMessageWithProjectContext(message, conversationId);
    }
    
    /**
     * Enhance a message with project context before it's sent
     * @param {Object} message - The message being sent
     * @param {String} conversationId - The conversation ID
     */
    enhanceMessageWithProjectContext(message, conversationId) {
        // Check if we have project context available
        if (!message.metadata) message.metadata = {};
        
        // Find if this conversation is linked to a project
        const projectId = this.getProjectForConversation(conversationId);
        if (!projectId) return;
        
        // Get project data
        const project = this.getProjectData(projectId);
        if (!project) return;
        
        // Add project context to the message metadata
        message.metadata.projectContext = {
            id: projectId,
            name: project.name,
            description: project.description,
            tags: project.tags || [],
            lastModified: project.lastModified
        };
        
        // In debug mode, also add a system message about the project context
        if (this.settings.debugMode && this.settings.enhancePrompts) {
            // Format project context information as a reminder
            const contextReminder = {
                role: 'system',
                content: `This conversation is linked to project: ${project.name}.\n\nProject description: ${project.description || 'No description available'}.\n\nProject tags: ${(project.tags || []).join(', ') || 'No tags'}`
            };
            
            // If message.preContext exists, add this reminder to it
            if (message.preContext && Array.isArray(message.preContext)) {
                message.preContext.push(contextReminder);
            } else {
                message.preContext = [contextReminder];
            }
            
            console.log('Enhanced message with project context:', projectId);
        }
    }
    
    /**
     * Handle a message received from the AI
     * @param {CustomEvent} event - Event containing message details
     */
    handleMessageReceived(event) {
        if (!this.settings.enabled) return;
        
        const message = event.detail.message;
        const conversationId = event.detail.conversationId;
        
        if (!message || !conversationId) return;
        
        // Check if we have a project context for this conversation
        const projectId = this.getProjectForConversation(conversationId);
        if (!projectId) return;
        
        // Add a visual indicator that project context was used with correct debug mode
        try {
            this.addProjectContextIndicator(message, projectId, this.settings.debugMode);
            console.log(`Added project context indicator for project ${projectId} to message`, message.elementId || 'unknown');
        } catch (error) {
            console.error('Error adding project context indicator:', error);
        }
    }
    
    /**
     * Add a visual indicator that project context was used in a response
     * @param {Object} message - The message object
     * @param {String} projectId - The project ID
     * @param {Boolean} debugMode - Whether to show debug details
     */
    addProjectContextIndicator(message, projectId, debugMode = false) {
        // First check if we have a valid message
        if (!message) {
            console.error('Invalid message object provided to addProjectContextIndicator');
            return;
        }

        // Get the message DOM element - fallback to finding it by other means if elementId is missing
        let messageElement = null;
        if (message.elementId) {
            messageElement = document.getElementById(message.elementId);
        }
        
        // If we couldn't find the element by ID, try to find the latest AI message
        if (!messageElement) {
            const aiMessages = document.querySelectorAll('.ai-message');
            if (aiMessages && aiMessages.length > 0) {
                messageElement = aiMessages[aiMessages.length - 1];
                console.log('Found message element using fallback method');
            }
        }
        
        // If we still don't have an element, we can't continue
        if (!messageElement) {
            console.error('Could not find message element to add project context indicator');
            return;
        }
        
        // Get project data with safety checks
        const project = this.getProjectData(projectId);
        if (!project) {
            console.error(`Project data not found for ID: ${projectId}`);
            return;
        }
        
        // Add a project context indicator to the message
        const indicator = document.createElement('div');
        indicator.className = 'project-context-indicator';
        
        // Create basic content common to both modes with safe rendering
        const projectName = project.name || 'Unknown Project';
        let indicatorContent = `
            <span class="project-context-icon">🔍</span>
            <span class="project-context-text">Project context: ${projectName}</span>
        `;
        
        // Add additional debug details if in debug mode
        if (debugMode) {
            // Safe handling of project properties
            const description = project.description || 'None';
            const tags = (project.tags && project.tags.length) ? project.tags.join(', ') : 'None';
            const lastModified = project.lastModified ? new Date(project.lastModified).toLocaleString() : 'Unknown';
            
            indicatorContent += `
            <div class="project-context-details">
                <div><strong>Description:</strong> ${description}</div>
                <div><strong>Tags:</strong> ${tags}</div>
                <div><strong>Last modified:</strong> ${lastModified}</div>
            </div>
            `;
        }
        
        indicator.innerHTML = indicatorContent;
        
        // Insert at the top of the message
        const messageContent = messageElement.querySelector('.message-content');
        if (messageContent) {
            messageContent.insertBefore(indicator, messageContent.firstChild);
        }
    }
    
    /**
     * Handle a conversation being assigned to a project
     * @param {CustomEvent} event - Event containing assignment details
     */
    handleConversationAssigned(event) {
        const { conversationId, projectId } = event.detail;
        
        if (!conversationId || !projectId) return;
        
        // If in debug mode, show a notification
        if (this.settings.debugMode) {
            this.showAssignmentNotification(conversationId, projectId);
        }
    }
    
    /**
     * Show a notification when a conversation is assigned to a project
     * @param {String} conversationId - The conversation ID
     * @param {String} projectId - The project ID
     */
    showAssignmentNotification(conversationId, projectId) {
        const project = this.getProjectData(projectId);
        if (!project) return;
        
        // Create a system message notification
        if (window.minervaChat && typeof window.minervaChat.addSystemMessage === 'function') {
            const message = `This conversation has been linked to project: ${project.name}`;
            window.minervaChat.addSystemMessage(message, {
                type: 'info',
                autoFade: true,
                fadeDelay: 5000
            });
        }
    }
    
    /**
     * Get the project ID for a conversation
     * @param {String} conversationId - The conversation ID
     * @returns {String|null} - Project ID or null if not found
     */
    getProjectForConversation(conversationId) {
        // Check conversation manager first
        if (window.conversationManager) {
            const result = window.conversationManager.findConversationById(conversationId);
            if (result && result.conversation && result.conversation.project) {
                return result.conversation.project;
            }
        }
        
        // Fallback: Check localStorage directly
        try {
            const conversations = JSON.parse(localStorage.getItem('minerva_conversations') || '{}');
            
            // Search in general conversations
            if (conversations.general && Array.isArray(conversations.general)) {
                const conversation = conversations.general.find(c => c.id === conversationId);
                if (conversation && conversation.project) {
                    return conversation.project;
                }
            }
            
            // Search in project-specific conversations
            if (conversations.projects) {
                for (const projectId in conversations.projects) {
                    if (Array.isArray(conversations.projects[projectId])) {
                        const conversation = conversations.projects[projectId].find(c => c.id === conversationId);
                        if (conversation) {
                            return projectId;
                        }
                    }
                }
            }
        } catch (e) {
            console.error('Error finding project for conversation:', e);
        }
        
        return null;
    }
    
    /**
     * Get project data by ID
     * @param {String} projectId - The project ID
     * @returns {Object|null} - Project data or null if not found
     */
    getProjectData(projectId) {
        // Check if we have the project in window.minervaProjects
        if (window.minervaProjects && window.minervaProjects[projectId]) {
            return window.minervaProjects[projectId];
        }
        
        // Fallback: Check localStorage directly
        try {
            const projects = JSON.parse(localStorage.getItem('minerva_projects') || '{}');
            if (projects[projectId]) {
                return projects[projectId];
            }
        } catch (e) {
            console.error('Error getting project data:', e);
        }
        
        return null;
    }
    
    /**
     * Toggle debug mode
     * @param {Boolean} enabled - Whether debug mode should be enabled
     */
    setDebugMode(enabled) {
        this.settings.debugMode = !!enabled;
        this.saveSettings();
        console.log(`Project Context Processor debug mode ${enabled ? 'enabled' : 'disabled'}`);
    }
    
    /**
     * Enable or disable the processor
     * @param {Boolean} enabled - Whether the processor should be enabled
     */
    setEnabled(enabled) {
        this.settings.enabled = !!enabled;
        this.saveSettings();
        console.log(`Project Context Processor ${enabled ? 'enabled' : 'disabled'}`);
    }
}

// Create global instance
window.projectContextProcessor = new ProjectContextProcessor();

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.projectContextProcessor) {
        window.projectContextProcessor.init();
    }
});
