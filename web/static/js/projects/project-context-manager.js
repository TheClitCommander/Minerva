/**
 * Minerva Project Context Manager
 * Handles the context switching between projects and conversation to project conversion
 */

(function() {
    // Initialize when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        initializeProjectManager();
    });

    // Project manager state
    const state = {
        currentProject: null,
        projects: [],
        conversationCache: {}
    };

    // DOM elements
    let projectsContainer;
    let createProjectBtn;
    let newProjectModal;
    let projectChat;
    let projectChatTitle;
    let projectChatHistory;
    let projectChatInput;
    let projectSendButton;
    let integratedChat;

    /**
     * Initialize the project manager
     */
    function initializeProjectManager() {
        // Find DOM elements
        projectsContainer = document.getElementById('projects-container');
        createProjectBtn = document.getElementById('create-project-btn');
        newProjectModal = document.getElementById('new-project-modal');
        projectChat = document.getElementById('project-chat');
        projectChatTitle = document.getElementById('project-chat-title');
        projectChatHistory = document.getElementById('project-chat-history');
        projectChatInput = document.getElementById('project-chat-input');
        projectSendButton = document.getElementById('project-send-button');
        integratedChat = document.getElementById('integrated-chat');

        // Set up event listeners
        createProjectBtn?.addEventListener('click', showCreateProjectModal);
        document.querySelector('.close-modal')?.addEventListener('click', hideCreateProjectModal);
        document.getElementById('cancel-project')?.addEventListener('click', hideCreateProjectModal);
        document.getElementById('create-project')?.addEventListener('click', createNewProject);
        
        // Project chat controls
        document.getElementById('minimize-project-chat')?.addEventListener('click', minimizeProjectChat);
        document.getElementById('close-project-chat')?.addEventListener('click', closeProjectChat);
        projectSendButton?.addEventListener('click', sendProjectMessage);
        
        // Load projects from localStorage
        loadProjects();
        
        // Set up navigation event listeners
        setupNavigationListeners();
    }

    /**
     * Setup navigation event listeners for showing projects view
     */
    function setupNavigationListeners() {
        const navItems = document.querySelectorAll('.nav-item');
        const viewSections = document.querySelectorAll('.view-section');
        
        navItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get the view to show
                const viewToShow = this.getAttribute('data-view');
                
                // Hide all view sections
                viewSections.forEach(section => {
                    section.classList.add('hidden');
                });
                
                // Remove active class from all nav items
                navItems.forEach(navItem => {
                    navItem.classList.remove('active');
                });
                
                // Add active class to clicked nav item
                this.classList.add('active');
                
                // Show the orbital UI by default
                const orbitalContainer = document.getElementById('minerva-orbital-ui');
                orbitalContainer.classList.remove('hidden');
                
                // If projects view, show projects grid and hide orbital UI
                if (viewToShow === 'projects') {
                    const projectsGrid = document.getElementById('projects-grid');
                    projectsGrid.classList.remove('hidden');
                    orbitalContainer.classList.add('hidden');
                } 
                // If think tank view, show think tank metrics and hide orbital UI
                else if (viewToShow === 'think-tank') {
                    const thinkTankView = document.getElementById('think-tank-view');
                    thinkTankView.classList.remove('hidden');
                    orbitalContainer.classList.add('hidden');
                }
                // If settings view, show settings and hide orbital UI  
                else if (viewToShow === 'settings') {
                    const settingsView = document.getElementById('settings-view');
                    settingsView.classList.remove('hidden');
                    orbitalContainer.classList.add('hidden');
                }
            });
        });
    }

    /**
     * Load projects from localStorage
     */
    function loadProjects() {
        try {
            const projectsData = localStorage.getItem('minerva_projects');
            if (projectsData) {
                state.projects = JSON.parse(projectsData);
                renderProjects();
            }
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }

    /**
     * Save projects to localStorage
     */
    function saveProjects() {
        try {
            localStorage.setItem('minerva_projects', JSON.stringify(state.projects));
        } catch (error) {
            console.error('Error saving projects:', error);
        }
    }

    /**
     * Render projects in the projects container
     */
    function renderProjects() {
        if (!projectsContainer) return;
        
        projectsContainer.innerHTML = '';
        
        if (state.projects.length === 0) {
            projectsContainer.innerHTML = `
                <div class="empty-projects holographic">
                    <p>No projects yet. Create your first project to get started.</p>
                </div>
            `;
            return;
        }
        
        state.projects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card holographic';
            projectCard.setAttribute('data-project-id', project.id);
            
            projectCard.innerHTML = `
                <h3>${project.name}</h3>
                <p>${project.description || 'No description'}</p>
                <div class="project-meta">
                    <span class="project-type ${project.type}">${project.type}</span>
                    <span class="project-date">${formatDate(project.createdAt)}</span>
                </div>
            `;
            
            projectCard.addEventListener('click', () => {
                openProject(project);
            });
            
            projectsContainer.appendChild(projectCard);
        });
    }

    /**
     * Format date for display
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date
     */
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }

    /**
     * Show the create project modal
     */
    function showCreateProjectModal() {
        newProjectModal.classList.remove('hidden');
    }

    /**
     * Hide the create project modal
     */
    function hideCreateProjectModal() {
        newProjectModal.classList.add('hidden');
    }

    /**
     * Create a new project
     */
    function createNewProject() {
        const projectName = document.getElementById('project-name').value.trim();
        const projectDescription = document.getElementById('project-description').value.trim();
        const projectType = document.getElementById('project-type').value;
        const createFromConversation = document.getElementById('create-from-conversation').checked;
        
        if (!projectName) {
            alert('Please enter a project name');
            return;
        }
        
        // Create project object
        const newProject = {
            id: 'project-' + Date.now(),
            name: projectName,
            description: projectDescription,
            type: projectType,
            createdAt: new Date().toISOString(),
            conversations: []
        };
        
        // Add current conversation if option is checked
        if (createFromConversation) {
            const chatHistory = document.getElementById('chat-history');
            if (chatHistory) {
                const messages = getMessagesFromChatHistory(chatHistory);
                if (messages.length > 0) {
                    newProject.conversations.push({
                        id: 'conv-' + Date.now(),
                        messages: messages,
                        createdAt: new Date().toISOString()
                    });
                }
            }
        }
        
        // Add to projects array
        state.projects.push(newProject);
        
        // Save to localStorage
        saveProjects();
        
        // Render projects
        renderProjects();
        
        // Hide modal
        hideCreateProjectModal();
        
        // Reset form
        document.getElementById('project-name').value = '';
        document.getElementById('project-description').value = '';
        
        // Update orbital UI
        updateOrbitalProjectsList();
        
        // Open the project
        openProject(newProject);
    }

    /**
     * Extract messages from chat history DOM
     * @param {HTMLElement} chatHistory - Chat history container
     * @returns {Array} Array of message objects
     */
    function getMessagesFromChatHistory(chatHistory) {
        const messages = [];
        const messageElements = chatHistory.querySelectorAll('.message');
        
        messageElements.forEach(element => {
            const isUser = element.classList.contains('user-message');
            const content = element.querySelector('.message-content').textContent.trim();
            const timestamp = new Date().toISOString();
            
            if (content) {
                messages.push({
                    role: isUser ? 'user' : 'assistant',
                    content: content,
                    timestamp: timestamp
                });
            }
        });
        
        return messages;
    }

    /**
     * Update the orbital UI with the current projects
     */
    function updateOrbitalProjectsList() {
        // This will be implemented to update the 3D orbital UI
        // Dispatch an event that the orb-ui can listen for
        const projectsUpdateEvent = new CustomEvent('minerva-update-projects', {
            detail: {
                projects: state.projects
            }
        });
        
        const orbContainer = document.getElementById('minerva-orbital-ui');
        if (orbContainer) {
            const root = orbContainer.querySelector('#minerva-3d-root');
            if (root) {
                root.dispatchEvent(projectsUpdateEvent);
            }
        }
    }

    /**
     * Open a project and show the project chat
     * @param {Object} project - Project object
     */
    function openProject(project) {
        state.currentProject = project;
        
        // Set session storage for project context
        sessionStorage.setItem('current_project_id', project.id);
        sessionStorage.setItem('current_project_name', project.name);
        
        // Update project chat title
        projectChatTitle.textContent = `Project: ${project.name}`;
        
        // Load project conversations
        loadProjectConversations(project);
        
        // Show project chat
        projectChat.classList.remove('hidden');
        
        // Update the orbital view to focus on this project
        focusProjectInOrbitalView(project);
    }

    /**
     * Load project conversations into the project chat
     * @param {Object} project - Project object
     */
    function loadProjectConversations(project) {
        projectChatHistory.innerHTML = '';
        
        if (!project.conversations || project.conversations.length === 0) {
            // Add welcome message
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'message bot-message welcome-message';
            welcomeMsg.innerHTML = `
                <div class="message-content">
                    <p>Welcome to the "${project.name}" project. Ask questions specific to this project context.</p>
                </div>
            `;
            projectChatHistory.appendChild(welcomeMsg);
            return;
        }
        
        // Get the most recent conversation
        const conversation = project.conversations[project.conversations.length - 1];
        
        // Add messages to the chat
        conversation.messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = `message ${message.role === 'user' ? 'user-message' : 'bot-message'}`;
            
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>${message.content}</p>
                </div>
                <div class="message-timestamp">${formatTime(message.timestamp)}</div>
            `;
            
            projectChatHistory.appendChild(messageElement);
        });
        
        // Scroll to bottom
        projectChatHistory.scrollTop = projectChatHistory.scrollHeight;
    }

    /**
     * Format time for display
     * @param {string} timeString - ISO time string
     * @returns {string} Formatted time
     */
    function formatTime(timeString) {
        const date = new Date(timeString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Focus on a project in the orbital view
     * @param {Object} project - Project object
     */
    function focusProjectInOrbitalView(project) {
        // Dispatch an event that the orb-ui can listen for
        const focusEvent = new CustomEvent('minerva-focus-project', {
            detail: {
                projectId: project.id
            }
        });
        
        const orbContainer = document.getElementById('minerva-orbital-ui');
        if (orbContainer) {
            const root = orbContainer.querySelector('#minerva-3d-root');
            if (root) {
                root.dispatchEvent(focusEvent);
            }
        }
    }

    /**
     * Send a message in the project chat
     */
    function sendProjectMessage() {
        if (!projectChatInput || !state.currentProject) return;
        
        const message = projectChatInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addProjectMessage(message, 'user');
        
        // Clear input
        projectChatInput.value = '';
        
        // Show typing indicator
        const typingIndicator = document.getElementById('project-typing-indicator');
        typingIndicator.classList.remove('hidden');
        
        // Send message to API with project context
        sendMessageToAPIWithProjectContext(message, state.currentProject);
    }

    /**
     * Add a message to the project chat
     * @param {string} message - Message text
     * @param {string} role - Message role (user or assistant)
     */
    function addProjectMessage(message, role) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${role === 'user' ? 'user-message' : 'bot-message'}`;
        
        const timestamp = new Date().toISOString();
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
            </div>
            <div class="message-timestamp">${formatTime(timestamp)}</div>
        `;
        
        projectChatHistory.appendChild(messageElement);
        projectChatHistory.scrollTop = projectChatHistory.scrollHeight;
        
        // Store message in project conversations
        if (state.currentProject) {
            if (!state.currentProject.conversations || state.currentProject.conversations.length === 0) {
                state.currentProject.conversations = [{
                    id: 'conv-' + Date.now(),
                    messages: [],
                    createdAt: timestamp
                }];
            }
            
            const currentConversation = state.currentProject.conversations[state.currentProject.conversations.length - 1];
            
            currentConversation.messages.push({
                role: role,
                content: message,
                timestamp: timestamp
            });
            
            // Save projects
            saveProjects();
        }
    }

    /**
     * Send a message to the API with project context
     * @param {string} message - Message text
     * @param {Object} project - Project object
     */
    function sendMessageToAPIWithProjectContext(message, project) {
        // Create request with project context
        const requestData = {
            message: message,
            session_id: sessionStorage.getItem('minerva_session_id') || null,
            user_id: localStorage.getItem('minerva_user_id') || 'user_' + Date.now().toString(36),
            project_id: project.id,
            project_name: project.name,
            project_context: project.description || '',
            store_in_memory: true,
            include_model_info: true
        };
        
        // Get model selection
        const modelCheckboxes = document.querySelectorAll('.model-selection input[type="checkbox"]');
        const selectedModels = [];
        
        modelCheckboxes.forEach(checkbox => {
            if (checkbox.checked && checkbox.dataset.model) {
                selectedModels.push(checkbox.dataset.model);
            }
        });
        
        if (selectedModels.length > 0) {
            requestData.models = selectedModels;
        }
        
        const blendEnabled = document.getElementById('blend-models').checked;
        requestData.blend = blendEnabled;
        
        // Send API request
        fetch('/api/think-tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Hide typing indicator
            const typingIndicator = document.getElementById('project-typing-indicator');
            typingIndicator.classList.add('hidden');
            
            // Add response to chat
            if (data.response) {
                addProjectMessage(data.response, 'assistant');
            } else {
                addProjectMessage('Sorry, I encountered an error processing your request.', 'assistant');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Hide typing indicator
            const typingIndicator = document.getElementById('project-typing-indicator');
            typingIndicator.classList.add('hidden');
            
            // Add error message
            addProjectMessage(`Sorry, I had trouble connecting to the Think Tank. Please try again. Error: ${error.message}`, 'assistant');
        });
    }

    /**
     * Minimize the project chat
     */
    function minimizeProjectChat() {
        projectChat.classList.toggle('minimized');
    }

    /**
     * Close the project chat
     */
    function closeProjectChat() {
        projectChat.classList.add('hidden');
        state.currentProject = null;
        sessionStorage.removeItem('current_project_id');
        sessionStorage.removeItem('current_project_name');
    }

    /**
     * Get current project context
     * @returns {Object|null} Project context object or null if no project is active
     */
    function getProjectContext() {
        const projectId = sessionStorage.getItem('current_project_id');
        const projectName = sessionStorage.getItem('current_project_name');
        
        if (!projectId || !projectName) {
            return null;
        }
        
        // Find the project in the state
        const project = state.projects.find(p => p.id === projectId);
        
        if (!project) {
            return null;
        }
        
        return {
            projectId: projectId,
            projectName: projectName,
            description: project.description || ''
        };
    }

    // Expose functions to window
    window.ProjectManager = {
        createProject: createNewProject,
        openProject: openProject,
        getProjectContext: getProjectContext,
        sendProjectMessage: sendProjectMessage
    };
})();
