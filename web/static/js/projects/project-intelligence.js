/**
 * Minerva Project Intelligence Layer
 * 
 * Automatically detects and links conversations to relevant projects
 * based on context analysis, keywords, and semantic understanding.
 * 
 * This module serves as the brain for Minerva's project awareness,
 * allowing it to recognize when conversations are related to specific
 * projects and provide relevant context and suggestions.
 */

(function() {
    // Project Intelligence state
    const state = {
        activeProject: null,
        detectedProjects: [],
        confidenceThreshold: 0.6, // Minimum confidence to suggest a project link
        analysisTimeout: null,
        keywordCache: {},
        projectCache: null,
        lastAnalysisTime: 0,
        analysisDebounceTime: 2000, // ms to wait between analyses
        autoLinkEnabled: true, // User preference for auto-linking
    };

    /**
     * Initialize the Project Intelligence Layer
     * @param {Object} options - Configuration options
     */
    function initialize(options = {}) {
        console.log('Initializing Minerva Project Intelligence Layer');
        
        // Apply custom configuration if provided
        if (options.confidenceThreshold) state.confidenceThreshold = options.confidenceThreshold;
        if (options.autoLinkEnabled !== undefined) state.autoLinkEnabled = options.autoLinkEnabled;
        
        // Load user preferences from localStorage
        loadPreferences();
        
        // Set up event listeners
        setupEventListeners();
        
        // Initial project cache build
        refreshProjectCache();
        
        // Periodically refresh project cache
        setInterval(refreshProjectCache, 5 * 60 * 1000); // Every 5 minutes
        
        // Expose public API
        window.MinervaProjectIntelligence = {
            detectProjectsInConversation,
            getDetectedProjects,
            refreshProjectCache,
            linkConversationToProject,
            setAutoLinkEnabled,
            getActiveProject,
            isAutoLinkEnabled,
            setConfidenceThreshold,
            getConfidenceThreshold,
            manuallyOverrideProjectLink
        };
        
        // Register with MinervaApp if available
        if (window.MinervaApp) {
            window.MinervaApp.registerComponent('projectIntelligence', window.MinervaProjectIntelligence);
        }
        
        return window.MinervaProjectIntelligence;
    }
    
    /**
     * Load user preferences from localStorage
     */
    function loadPreferences() {
        const preferences = JSON.parse(localStorage.getItem('minerva_project_intelligence_prefs') || '{}');
        
        if (preferences.autoLinkEnabled !== undefined) {
            state.autoLinkEnabled = preferences.autoLinkEnabled;
        }
        
        if (preferences.confidenceThreshold) {
            state.confidenceThreshold = preferences.confidenceThreshold;
        }
    }
    
    /**
     * Save user preferences to localStorage
     */
    function savePreferences() {
        const preferences = {
            autoLinkEnabled: state.autoLinkEnabled,
            confidenceThreshold: state.confidenceThreshold
        };
        
        localStorage.setItem('minerva_project_intelligence_prefs', JSON.stringify(preferences));
    }
    
    /**
     * Set up event listeners for chat and UI interactions
     */
    function setupEventListeners() {
        // Listen for new messages in chat
        document.addEventListener('minerva:message:sent', handleNewMessage);
        document.addEventListener('minerva:message:received', handleNewMessage);
        
        // Listen for conversation changes
        document.addEventListener('minerva:conversation:changed', handleConversationChange);
        document.addEventListener('minerva:conversation:new', analyzeConversationContext);
        
        // Listen for project changes
        document.addEventListener('minerva:project:created', refreshProjectCache);
        document.addEventListener('minerva:project:updated', refreshProjectCache);
        document.addEventListener('minerva:project:deleted', refreshProjectCache);
    }
    
    /**
     * Refresh the project cache for faster analysis
     */
    function refreshProjectCache() {
        // Get projects from localStorage or through the API
        let projects = [];
        
        try {
            // Try to get projects from ProjectManager if available
            if (window.ProjectManager && window.ProjectManager.getProjects) {
                projects = window.ProjectManager.getProjects() || [];
            } else {
                // Fallback to localStorage
                const savedProjects = localStorage.getItem('minerva_projects');
                if (savedProjects) {
                    projects = JSON.parse(savedProjects) || [];
                }
            }
            
            // Process each project to extract keywords and other relevant data
            state.projectCache = projects.map(project => {
                // Extract keywords from project name, description, and tags
                const keywords = extractKeywords(project.name + ' ' + (project.description || ''));
                
                return {
                    id: project.id,
                    name: project.name,
                    description: project.description || '',
                    keywords: keywords,
                    created: project.created,
                    updated: project.updated,
                    tags: project.tags || [],
                    color: project.color
                };
            });
            
            console.log(`Project cache refreshed with ${state.projectCache.length} projects`);
        } catch (error) {
            console.error('Failed to refresh project cache:', error);
        }
    }
    
    /**
     * Extract keywords from text
     * @param {string} text - Text to extract keywords from
     * @returns {Array} Array of keywords
     */
    function extractKeywords(text) {
        if (!text) return [];
        
        // Cache lookup for performance
        if (state.keywordCache[text]) {
            return state.keywordCache[text];
        }
        
        // Remove special characters and split by spaces
        const words = text.toLowerCase()
            .replace(/[^\w\s]/g, ' ')
            .split(/\s+/)
            .filter(word => word.length > 2) // Filter out short words
            .filter(word => !isStopWord(word)); // Filter out common stop words
        
        // Get unique words
        const uniqueWords = [...new Set(words)];
        
        // Cache the result
        state.keywordCache[text] = uniqueWords;
        
        return uniqueWords;
    }
    
    /**
     * Check if a word is a common stop word
     * @param {string} word - Word to check
     * @returns {boolean} True if the word is a stop word
     */
    function isStopWord(word) {
        const stopWords = ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'they', 'them', 
                          'their', 'what', 'when', 'where', 'which', 'who', 'whom', 'how', 'why', 
                          'not', 'your', 'our', 'his', 'her', 'its', 'here', 'there', 'you'];
        
        return stopWords.includes(word);
    }
    
    /**
     * Handle new messages in the chat
     * @param {Event} event - Custom event with message data
     */
    function handleNewMessage(event) {
        // Debounce analysis to avoid excessive processing
        clearTimeout(state.analysisTimeout);
        
        // Only analyze if enough time has passed since last analysis
        const now = Date.now();
        if (now - state.lastAnalysisTime < state.analysisDebounceTime) {
            state.analysisTimeout = setTimeout(() => {
                analyzeConversationContext();
            }, state.analysisDebounceTime);
            return;
        }
        
        state.lastAnalysisTime = now;
        analyzeConversationContext();
    }
    
    /**
     * Handle conversation change event
     * @param {Event} event - Custom event with conversation data
     */
    function handleConversationChange(event) {
        // Reset detected projects for the new conversation
        state.detectedProjects = [];
        state.activeProject = null;
        
        // Analyze the new conversation
        analyzeConversationContext();
    }
    
    /**
     * Analyze the current conversation to detect relevant projects
     */
    function analyzeConversationContext() {
        if (!state.autoLinkEnabled || !state.projectCache || state.projectCache.length === 0) {
            return;
        }
        
        // Get chat history text
        const chatText = getChatHistoryText();
        if (!chatText) return;
        
        // Extract keywords from chat
        const chatKeywords = extractKeywords(chatText);
        if (chatKeywords.length === 0) return;
        
        // Detect relevant projects
        const projectMatches = detectProjectsInText(chatText, chatKeywords);
        
        // Update state with detected projects
        state.detectedProjects = projectMatches;
        
        // If we have a high-confidence match and auto-linking is enabled, suggest it
        const highConfidenceMatches = projectMatches.filter(match => 
            match.confidence >= state.confidenceThreshold
        ).sort((a, b) => b.confidence - a.confidence);
        
        if (highConfidenceMatches.length > 0) {
            // Get the highest confidence project
            const bestMatch = highConfidenceMatches[0];
            
            // If confidence is high enough, link automatically
            if (bestMatch.confidence >= state.confidenceThreshold) {
                if (state.activeProject !== bestMatch.id) {
                    state.activeProject = bestMatch.id;
                    
                    // Display project hint in the UI
                    displayProjectHint(bestMatch);
                    
                    // Dispatch event for other components
                    const event = new CustomEvent('minerva:project:detected', { 
                        detail: { 
                            project: bestMatch,
                            allDetected: highConfidenceMatches
                        } 
                    });
                    document.dispatchEvent(event);
                }
            }
        }
    }
    
    /**
     * Display a hint in the UI about the detected project
     * @param {Object} project - Detected project
     */
    function displayProjectHint(project) {
        // Make sure we have a container for the hint
        let hintContainer = document.getElementById('project-intelligence-hint');
        
        if (!hintContainer) {
            hintContainer = document.createElement('div');
            hintContainer.id = 'project-intelligence-hint';
            hintContainer.className = 'project-intelligence-hint';
            
            // Try to append it to the chat interface
            const chatControls = document.querySelector('.chat-controls') || document.querySelector('.message-input-container');
            if (chatControls) {
                chatControls.parentNode.insertBefore(hintContainer, chatControls);
            } else {
                // Fallback to appending to body
                document.body.appendChild(hintContainer);
            }
        }
        
        // Create hint content
        hintContainer.innerHTML = `
            <div class="hint-content">
                <i class="fas fa-project-diagram"></i>
                <span>This conversation seems related to project: <strong>${project.name}</strong></span>
                <div class="hint-actions">
                    <button class="link-project-btn" data-project-id="${project.id}">Link</button>
                    <button class="ignore-hint-btn">Ignore</button>
                </div>
            </div>
        `;
        
        // Add event listeners to buttons
        hintContainer.querySelector('.link-project-btn').addEventListener('click', () => {
            linkConversationToProject(project.id);
            hintContainer.style.display = 'none';
        });
        
        hintContainer.querySelector('.ignore-hint-btn').addEventListener('click', () => {
            hintContainer.style.display = 'none';
        });
        
        // Show the hint with animation
        hintContainer.style.display = 'block';
        
        // Auto-hide after 10 seconds if no action taken
        setTimeout(() => {
            if (hintContainer.style.display !== 'none') {
                hintContainer.style.display = 'none';
            }
        }, 10000);
    }
    
    /**
     * Get text from the chat history
     * @returns {string} Combined chat history text
     */
    function getChatHistoryText() {
        // Try to get messages from ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.getActiveConversationMessages) {
            const messages = window.ThinkTankAPI.getActiveConversationMessages();
            if (messages && messages.length) {
                return messages.map(msg => msg.content || '').join(' ');
            }
        }
        
        // Fallback to DOM scraping
        const chatHistory = document.querySelector('.chat-history') || document.getElementById('chat-history');
        if (!chatHistory) return '';
        
        // Extract text from message elements
        const messageElements = chatHistory.querySelectorAll('.message');
        if (!messageElements.length) return '';
        
        return Array.from(messageElements)
            .map(el => el.textContent || '')
            .join(' ');
    }
    
    /**
     * Detect projects that match the given text and keywords
     * @param {string} text - Full text to analyze
     * @param {Array} keywords - Extracted keywords from the text
     * @returns {Array} Array of matching projects with confidence scores
     */
    function detectProjectsInText(text, keywords) {
        if (!state.projectCache || !keywords.length) return [];
        
        const matches = state.projectCache.map(project => {
            // Calculate keyword match ratio
            const matchingKeywords = project.keywords.filter(
                keyword => keywords.includes(keyword)
            );
            
            // Simple confidence calculation based on keyword overlap
            const keywordRatio = matchingKeywords.length / project.keywords.length;
            
            // Add bonus for project name or exact phrases appearing in text
            let nameBonus = 0;
            if (text.toLowerCase().includes(project.name.toLowerCase())) {
                nameBonus = 0.3; // Significant boost for project name match
            }
            
            // Calculate final confidence score (0 to 1)
            const confidence = Math.min(keywordRatio + nameBonus, 1);
            
            return {
                id: project.id,
                name: project.name,
                description: project.description,
                confidence,
                matchingKeywords,
                color: project.color
            };
        }).filter(match => match.confidence > 0); // Filter out zero confidence matches
        
        // Sort by confidence, highest first
        return matches.sort((a, b) => b.confidence - a.confidence);
    }
    
    /**
     * Public method: Detect projects in a specific conversation
     * @param {string} conversationId - ID of the conversation to analyze
     * @returns {Promise} Promise resolving to array of matching projects
     */
    function detectProjectsInConversation(conversationId) {
        return new Promise((resolve, reject) => {
            try {
                // Get conversation messages from storage or API
                let conversationText = '';
                
                if (window.ThinkTankAPI && window.ThinkTankAPI.getConversationMessages) {
                    const messages = window.ThinkTankAPI.getConversationMessages(conversationId);
                    if (messages && messages.length) {
                        conversationText = messages.map(msg => msg.content || '').join(' ');
                    }
                } else {
                    // Try to get from localStorage
                    const conversations = JSON.parse(localStorage.getItem('minerva_conversations') || '{}');
                    const conversation = conversations.general?.find(c => c.id === conversationId) || 
                                        Object.values(conversations.projects || {}).flat().find(c => c.id === conversationId);
                    
                    if (conversation && conversation.messages) {
                        conversationText = conversation.messages.map(msg => msg.content || '').join(' ');
                    }
                }
                
                if (!conversationText) {
                    resolve([]);
                    return;
                }
                
                // Extract keywords and detect projects
                const keywords = extractKeywords(conversationText);
                const projectMatches = detectProjectsInText(conversationText, keywords);
                
                resolve(projectMatches);
            } catch (error) {
                console.error('Error detecting projects in conversation:', error);
                reject(error);
            }
        });
    }
    
    /**
     * Link a conversation to a project
     * @param {string} projectId - ID of the project to link
     * @param {string} conversationId - ID of the conversation to link (uses active if not provided)
     * @returns {boolean} Success status of the operation
     */
    function linkConversationToProject(projectId, conversationId) {
        const convId = conversationId || (window.ThinkTankAPI ? window.ThinkTankAPI.getActiveConversation() : null);
        
        if (!convId) {
            console.error('No active conversation to link');
            return false;
        }
        
        try {
            // Find project in cache
            const project = state.projectCache.find(p => p.id === projectId);
            if (!project) {
                console.error('Project not found:', projectId);
                return false;
            }
            
            // Set as active project
            state.activeProject = projectId;
            
            // Show visual indication of project link
            showProjectLinkIndicator(project);
            
            // Use the Conversation Manager API if available
            if (window.MinervaConversationManager) {
                const conversationManager = window.MinervaConversationManager;
                if (typeof conversationManager.assignConversationToProject === 'function') {
                    conversationManager.assignConversationToProject(convId, projectId);
                }
            }
            
            // Dispatch event for other components
            const event = new CustomEvent('minerva:conversation:linked', {
                detail: {
                    conversationId: convId,
                    projectId,
                    project
                }
            });
            document.dispatchEvent(event);
            
            return true;
        } catch (error) {
            console.error('Error linking conversation to project:', error);
            return false;
        }
    }
    
    /**
     * Show a visual indicator for the linked project
     * @param {Object} project - Project that was linked
     */
    function showProjectLinkIndicator(project) {
        // Create or update project link indicator
        let indicator = document.getElementById('linked-project-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'linked-project-indicator';
            indicator.className = 'linked-project-indicator';
            
            // Append to appropriate container
            const chatContainer = document.querySelector('.chat-container') || document.querySelector('.message-container');
            if (chatContainer) {
                chatContainer.appendChild(indicator);
            } else {
                document.body.appendChild(indicator);
            }
        }
        
        // Set project color if available
        const projectColor = project.color || '#5C8FEA';
        
        // Update indicator content
        indicator.innerHTML = `
            <div class="project-indicator-content" style="border-left: 3px solid ${projectColor}">
                <i class="fas fa-project-diagram" style="color: ${projectColor}"></i>
                <span>Linked to project: <strong>${project.name}</strong></span>
                <button class="change-project-btn" title="Change linked project">
                    <i class="fas fa-exchange-alt"></i>
                </button>
            </div>
        `;
        
        // Show with animation
        indicator.style.display = 'block';
        
        // Add event listener to change button
        indicator.querySelector('.change-project-btn').addEventListener('click', showProjectSelectionModal);
    }
    
    /**
     * Show a modal for manually selecting a project to link
     */
    function showProjectSelectionModal() {
        // Create modal if it doesn't exist
        let modal = document.getElementById('project-selection-modal');
        
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'project-selection-modal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Link Conversation to Project</h3>
                        <button class="close-modal">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="project-list"></div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            
            // Add event listener to close button
            modal.querySelector('.close-modal').addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }
        
        // Populate project list
        const projectList = modal.querySelector('.project-list');
        projectList.innerHTML = '';
        
        if (!state.projectCache || state.projectCache.length === 0) {
            projectList.innerHTML = '<p>No projects found. Create a project first.</p>';
        } else {
            state.projectCache.forEach(project => {
                const projectItem = document.createElement('div');
                projectItem.className = 'project-selection-item';
                projectItem.dataset.projectId = project.id;
                
                const isActive = project.id === state.activeProject;
                if (isActive) {
                    projectItem.classList.add('active');
                }
                
                projectItem.innerHTML = `
                    <div class="project-color" style="background-color: ${project.color || '#5C8FEA'}"></div>
                    <div class="project-info">
                        <h4>${project.name}</h4>
                        <p>${project.description || 'No description'}</p>
                    </div>
                    ${isActive ? '<div class="active-indicator"><i class="fas fa-check"></i></div>' : ''}
                `;
                
                // Add click event listener
                projectItem.addEventListener('click', () => {
                    linkConversationToProject(project.id);
                    modal.style.display = 'none';
                });
                
                projectList.appendChild(projectItem);
            });
        }
        
        // Show modal
        modal.style.display = 'flex';
    }
    
    /**
     * Manually override the project link with user selection
     * @param {string} projectId - ID of the project to link
     * @returns {boolean} Success status
     */
    function manuallyOverrideProjectLink(projectId) {
        return linkConversationToProject(projectId);
    }
    
    /**
     * Get currently detected projects for the active conversation
     * @returns {Array} Array of detected projects with confidence scores
     */
    function getDetectedProjects() {
        return [...state.detectedProjects];
    }
    
    /**
     * Get the currently active/linked project ID
     * @returns {string|null} ID of the active project or null
     */
    function getActiveProject() {
        return state.activeProject;
    }
    
    /**
     * Set whether auto-linking is enabled
     * @param {boolean} enabled - Whether auto-linking should be enabled
     */
    function setAutoLinkEnabled(enabled) {
        state.autoLinkEnabled = !!enabled;
        savePreferences();
    }
    
    /**
     * Check if auto-linking is enabled
     * @returns {boolean} Whether auto-linking is enabled
     */
    function isAutoLinkEnabled() {
        return state.autoLinkEnabled;
    }
    
    /**
     * Set the confidence threshold for auto-linking
     * @param {number} threshold - Confidence threshold (0-1)
     */
    function setConfidenceThreshold(threshold) {
        const validThreshold = Math.max(0, Math.min(1, threshold));
        state.confidenceThreshold = validThreshold;
        savePreferences();
    }
    
    /**
     * Get the current confidence threshold
     * @returns {number} Confidence threshold
     */
    function getConfidenceThreshold() {
        return state.confidenceThreshold;
    }
    
    // Initialize when the DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
