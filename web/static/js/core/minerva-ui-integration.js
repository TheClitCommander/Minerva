/**
 * Minerva UI Integration Script
 * 
 * This script connects the chat interface with the orbital UI,
 * ensuring that conversations persist across different parts of Minerva
 * and providing project context awareness.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Minerva UI integration...');
    initChatIntegration();
    setupProjectConversion();
    connectOrbUIEvents();
});

// Initialize the chat integration across Minerva UI
function initChatIntegration() {
    // Detect which chat interface is present
    const standardChat = document.getElementById('chat-interface');
    const floatingChat = document.querySelector('.floating-chat-interface');
    const projectChat = document.querySelector('.project-chat-panel');
    
    // Set the active chat mode
    let activeChat = null;
    let chatMode = 'none';
    
    if (floatingChat) {
        activeChat = floatingChat;
        chatMode = 'floating';
        console.log('Floating chat mode detected');
    } else if (projectChat) {
        activeChat = projectChat;
        chatMode = 'project';
        console.log('Project chat mode detected');
    } else if (standardChat) {
        activeChat = standardChat;
        chatMode = 'standard';
        console.log('Standard chat mode detected');
    } else {
        console.warn('No chat interface detected');
        return;
    }
    
    // Store chat mode in session for persistence
    sessionStorage.setItem('minerva_chat_mode', chatMode);
    
    // Make appropriate chat draggable via the header
    if (chatMode === 'floating' || chatMode === 'standard') {
        const chatHeader = activeChat.querySelector('#chat-header');
        if (chatHeader && typeof makeDraggable === 'function') {
            makeDraggable(activeChat, chatHeader);
            console.log('Chat interface made draggable');
        }
    }
    
    // Load most recent conversation (global or project-specific)
    restoreConversation(chatMode);
}

// Restore conversation based on the current context
function restoreConversation(mode) {
    let chatMessages;
    
    if (mode === 'floating' || mode === 'standard') {
        chatMessages = document.querySelector('#chat-messages');
    } else if (mode === 'project') {
        chatMessages = document.querySelector('.project-chat-panel #chat-messages');
    }
    
    if (!chatMessages) {
        console.warn('Chat messages container not found');
        return;
    }
    
    // Get current project context if available
    const projectId = sessionStorage.getItem('minerva_active_project_id');
    const projectName = sessionStorage.getItem('minerva_active_project_name');
    
    // Set chat title based on context
    const chatTitle = document.getElementById('chat-title');
    if (chatTitle) {
        chatTitle.textContent = projectId ? `${projectName} Chat` : 'Minerva Space';
    }
    
    // Retrieve the appropriate chat history
    let chatHistory;
    if (projectId) {
        // Try to get project-specific history first
        chatHistory = localStorage.getItem(`minerva_project_${projectId}_chat`);
        if (!chatHistory) {
            // Fall back to global history if no project-specific history exists
            chatHistory = localStorage.getItem('minerva_global_chat');
        }
    } else {
        // Use global history when not in a project
        chatHistory = localStorage.getItem('minerva_global_chat');
    }
    
    // Parse and restore messages
    if (chatHistory) {
        try {
            const history = JSON.parse(chatHistory);
            if (history.messages && Array.isArray(history.messages)) {
                // Clear existing welcome message
                chatMessages.innerHTML = '';
                
                // Restore messages
                history.messages.forEach(msg => {
                    if (msg.type === 'user') {
                        const msgElement = document.createElement('div');
                        msgElement.className = 'user-message';
                        msgElement.textContent = msg.content;
                        chatMessages.appendChild(msgElement);
                    } else if (msg.type === 'ai') {
                        const msgElement = document.createElement('div');
                        msgElement.className = 'ai-message';
                        
                        // Create the response container
                        const responseContainer = document.createElement('div');
                        responseContainer.className = 'response-content';
                        responseContainer.innerHTML = msg.content;
                        msgElement.appendChild(responseContainer);
                        
                        // Add model info if available
                        if (msg.modelInfo) {
                            try {
                                const modelInfo = JSON.parse(msg.modelInfo);
                                const infoElement = document.createElement('div');
                                infoElement.className = 'model-info';
                                infoElement.setAttribute('data-model-info', msg.modelInfo);
                                
                                // Add model info display similar to addAIMessage function
                                let displayText = 'AI Response';
                                
                                if (modelInfo.primary_model) {
                                    displayText = modelInfo.primary_model;
                                } else if (modelInfo.model) {
                                    displayText = modelInfo.model;
                                }
                                
                                infoElement.innerHTML = `
                                    <span class="model-badge">${displayText}</span>
                                    <button class="model-info-toggle" title="Show model details">
                                        <i class="fas fa-info-circle"></i>
                                    </button>
                                `;
                                
                                msgElement.appendChild(infoElement);
                            } catch (e) {
                                console.error('Error parsing model info:', e);
                            }
                        }
                        
                        chatMessages.appendChild(msgElement);
                    }
                });
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
                
                console.log(`Restored ${history.messages.length} messages from ${projectId ? 'project' : 'global'} chat history`);
            }
        } catch (e) {
            console.error('Error restoring chat history:', e);
        }
    } else {
        // If no history, make sure we have the welcome message
        if (chatMessages.children.length === 0) {
            const welcomeMsg = document.createElement('div');
            welcomeMsg.className = 'system-message';
            welcomeMsg.textContent = 'Welcome to Minerva\'s Think Tank. How can I assist you today?';
            chatMessages.appendChild(welcomeMsg);
        }
    }
}

// Set up the ability to convert conversations to projects
function setupProjectConversion() {
    // Add project conversion button to the chat controls if not already present
    const chatControls = document.querySelector('#chat-controls');
    
    if (chatControls && !document.getElementById('convert-to-project')) {
        const convertBtn = document.createElement('button');
        convertBtn.id = 'convert-to-project';
        convertBtn.className = 'chat-control-btn';
        convertBtn.title = 'Convert to Project';
        convertBtn.innerHTML = '<i class="fas fa-folder-plus"></i>';
        
        convertBtn.addEventListener('click', function() {
            convertChatToProject();
        });
        
        chatControls.appendChild(convertBtn);
        console.log('Project conversion button added');
    }
}

// Convert the current chat to a new or existing project
function convertChatToProject() {
    // Get the chat messages from the active chat interface
    let chatMessages;
    const chatMode = sessionStorage.getItem('minerva_chat_mode');
    
    if (chatMode === 'floating' || chatMode === 'standard') {
        chatMessages = document.querySelector('#chat-messages');
    } else if (chatMode === 'project') {
        chatMessages = document.querySelector('.project-chat-panel #chat-messages');
    }
    
    if (!chatMessages || chatMessages.children.length <= 1) {
        // Only welcome message or empty chat
        alert('Please start a conversation before creating a project.');
        return;
    }
    
    // Extract chat history
    const messages = Array.from(chatMessages.children).map(msg => {
        const type = msg.classList.contains('user-message') ? 'user' : 
                   msg.classList.contains('ai-message') ? 'ai' : 'system';
        
        let modelInfo = null;
        if (type === 'ai') {
            const infoElement = msg.querySelector('.model-info');
            if (infoElement) {
                modelInfo = infoElement.getAttribute('data-model-info');
            }
        }
        
        return {
            type: type,
            content: msg.textContent || msg.innerText || '',
            modelInfo: modelInfo
        };
    });
    
    // Create project options dialog
    const dialog = document.createElement('div');
    dialog.className = 'project-creation-dialog';
    dialog.innerHTML = `
        <div class="dialog-header">
            <h3>Create New Project</h3>
            <button class="close-dialog"><i class="fas fa-times"></i></button>
        </div>
        <div class="dialog-content">
            <div class="form-group">
                <label for="project-name">Project Name:</label>
                <input type="text" id="project-name" placeholder="Enter project name">
            </div>
            <div class="form-group">
                <label>Project Type:</label>
                <div class="radio-group">
                    <label><input type="radio" name="project-type" value="new" checked> Create New Project</label>
                    <label><input type="radio" name="project-type" value="existing"> Add to Existing Project</label>
                </div>
            </div>
            <div class="form-group existing-projects" style="display:none;">
                <label for="existing-project">Select Project:</label>
                <select id="existing-project">
                    <option value="">Loading projects...</option>
                </select>
            </div>
            <div class="button-group">
                <button id="create-project-btn" class="primary-btn">Create Project</button>
                <button class="cancel-btn">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Set up dialog events
    const closeBtn = dialog.querySelector('.close-dialog');
    const cancelBtn = dialog.querySelector('.cancel-btn');
    const createBtn = dialog.querySelector('#create-project-btn');
    const projectTypeRadios = dialog.querySelectorAll('input[name="project-type"]');
    const existingProjectsDiv = dialog.querySelector('.existing-projects');
    const existingProjectSelect = dialog.querySelector('#existing-project');
    
    closeBtn.addEventListener('click', () => dialog.remove());
    cancelBtn.addEventListener('click', () => dialog.remove());
    
    // Toggle existing projects dropdown visibility
    projectTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'existing') {
                existingProjectsDiv.style.display = 'block';
                createBtn.textContent = 'Add to Project';
                // Load existing projects
                loadExistingProjects(existingProjectSelect);
            } else {
                existingProjectsDiv.style.display = 'none';
                createBtn.textContent = 'Create Project';
            }
        });
    });
    
    // Handle project creation/addition
    createBtn.addEventListener('click', function() {
        const projectName = document.getElementById('project-name').value.trim();
        const projectType = document.querySelector('input[name="project-type"]:checked').value;
        
        if (projectType === 'new' && !projectName) {
            alert('Please enter a project name');
            return;
        }
        
        if (projectType === 'existing' && !existingProjectSelect.value) {
            alert('Please select a project');
            return;
        }
        
        // Either create new project or add to existing
        if (projectType === 'new') {
            createNewProjectWithChat(projectName, messages);
        } else {
            addChatToExistingProject(existingProjectSelect.value, messages);
        }
        
        dialog.remove();
    });
}

// Load existing projects for the dropdown
function loadExistingProjects(selectElement) {
    // Clear the dropdown first
    selectElement.innerHTML = '<option value="">Loading projects...</option>';
    
    // In a real implementation, this would fetch projects from an API
    // For now, we'll use dummy data or localStorage
    const savedProjects = localStorage.getItem('minerva_projects');
    let projects = [];
    
    if (savedProjects) {
        try {
            projects = JSON.parse(savedProjects);
        } catch (e) {
            console.error('Error parsing saved projects:', e);
        }
    }
    
    // If no projects, show a message
    if (!projects.length) {
        selectElement.innerHTML = '<option value="">No existing projects</option>';
        return;
    }
    
    // Populate the dropdown
    selectElement.innerHTML = '<option value="">Select a project</option>';
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = project.name;
        selectElement.appendChild(option);
    });
}

// Create a new project with the current chat history
function createNewProjectWithChat(projectName, messages) {
    // Generate a unique project ID
    const projectId = 'project_' + Date.now();
    
    // Create project object
    const newProject = {
        id: projectId,
        name: projectName,
        createdAt: new Date().toISOString(),
        conversations: [{
            id: 'conv_' + Date.now(),
            title: 'Initial Conversation',
            messages: messages
        }]
    };
    
    // Save project to localStorage (in real implementation, this would be an API call)
    const savedProjects = localStorage.getItem('minerva_projects');
    let projects = [];
    
    if (savedProjects) {
        try {
            projects = JSON.parse(savedProjects);
        } catch (e) {
            console.error('Error parsing saved projects:', e);
        }
    }
    
    projects.push(newProject);
    localStorage.setItem('minerva_projects', JSON.stringify(projects));
    
    // Save project-specific chat history
    localStorage.setItem(`minerva_project_${projectId}_chat`, JSON.stringify({
        messages: messages,
        timestamp: Date.now(),
        projectId: projectId
    }));
    
    // Update session context
    sessionStorage.setItem('minerva_active_project_id', projectId);
    sessionStorage.setItem('minerva_active_project_name', projectName);
    
    // Update chat title
    const chatTitle = document.getElementById('chat-title');
    if (chatTitle) {
        chatTitle.textContent = `${projectName} Chat`;
    }
    
    // Add system message confirming project creation
    addSystemMessage(`Conversation converted to new project: ${projectName}`);
    
    // Trigger event for orbital UI to update (add new project orb)
    const event = new CustomEvent('projectCreated', {
        detail: {
            project: newProject
        }
    });
    document.dispatchEvent(event);
    
    console.log(`Created new project "${projectName}" with ID ${projectId}`);
}

// Add current chat to an existing project
function addChatToExistingProject(projectId, messages) {
    // Get the project data
    const savedProjects = localStorage.getItem('minerva_projects');
    let projects = [];
    let selectedProject = null;
    
    if (savedProjects) {
        try {
            projects = JSON.parse(savedProjects);
            selectedProject = projects.find(p => p.id === projectId);
        } catch (e) {
            console.error('Error parsing saved projects:', e);
        }
    }
    
    if (!selectedProject) {
        alert('Project not found');
        return;
    }
    
    // Add the conversation to the project
    const newConversation = {
        id: 'conv_' + Date.now(),
        title: 'New Conversation',
        messages: messages
    };
    
    selectedProject.conversations.push(newConversation);
    
    // Update localStorage
    localStorage.setItem('minerva_projects', JSON.stringify(projects));
    
    // Save project-specific chat history
    localStorage.setItem(`minerva_project_${projectId}_chat`, JSON.stringify({
        messages: messages,
        timestamp: Date.now(),
        projectId: projectId
    }));
    
    // Update session context
    sessionStorage.setItem('minerva_active_project_id', projectId);
    sessionStorage.setItem('minerva_active_project_name', selectedProject.name);
    
    // Update chat title
    const chatTitle = document.getElementById('chat-title');
    if (chatTitle) {
        chatTitle.textContent = `${selectedProject.name} Chat`;
    }
    
    // Add system message confirming
    addSystemMessage(`Conversation added to project: ${selectedProject.name}`);
    
    console.log(`Added conversation to project "${selectedProject.name}"`);
}

// Connect with the orbital UI events
function connectOrbUIEvents() {
    // Listen for project selection events from the orbital UI
    document.addEventListener('projectSelected', function(e) {
        if (e.detail && e.detail.projectId) {
            // Update active project context
            sessionStorage.setItem('minerva_active_project_id', e.detail.projectId);
            sessionStorage.setItem('minerva_active_project_name', e.detail.projectName || 'Project');
            
            // Restore the project-specific conversation
            restoreConversation(sessionStorage.getItem('minerva_chat_mode'));
            
            // Update project chat title
            const projectChatTitle = document.getElementById('project-chat-title');
            if (projectChatTitle) {
                projectChatTitle.textContent = `${e.detail.projectName || 'Project'} Chat`;
            }
        }
    });
    
    // Handle project chat button events
    const minimizeProjectChatBtn = document.getElementById('minimize-project-chat');
    const sendProjectMessageBtn = document.getElementById('send-project-message');
    const projectChatInput = document.getElementById('project-chat-input');
    const projectChatPanel = document.getElementById('project-chat-panel');
    
    if (minimizeProjectChatBtn && projectChatPanel) {
        minimizeProjectChatBtn.addEventListener('click', function() {
            projectChatPanel.classList.toggle('minimized');
            const icon = this.querySelector('i');
            if (icon) {
                if (projectChatPanel.classList.contains('minimized')) {
                    icon.classList.remove('fa-minus');
                    icon.classList.add('fa-expand');
                    this.setAttribute('title', 'Expand chat');
                } else {
                    icon.classList.remove('fa-expand');
                    icon.classList.add('fa-minus');
                    this.setAttribute('title', 'Minimize chat');
                }
            }
        });
    }
    
    // Set up project chat input and send button
    if (sendProjectMessageBtn && projectChatInput) {
        sendProjectMessageBtn.addEventListener('click', sendProjectMessage);
        projectChatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendProjectMessage();
            }
        });
    }
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * This function manages sending project-specific messages with proper context
     * Critical for project memory persistence and context awareness
     * See: /function_snapshots/ui/minerva-ui-integration.js
     *******************************************************************************/
    // Function to send a project chat message
    function sendProjectMessage() {
        const message = projectChatInput.value.trim();
        if (!message) return;
        
        // Get project context
        const projectId = sessionStorage.getItem('minerva_active_project_id');
        const projectName = sessionStorage.getItem('minerva_active_project_name');
        
        // Add message to project chat
        const projectChatMessages = document.getElementById('project-chat-messages');
        const msgElement = document.createElement('div');
        msgElement.className = 'user-message';
        msgElement.textContent = message;
        projectChatMessages.appendChild(msgElement);
        projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
        
        // Clear input
        projectChatInput.value = '';
        
        // Show loading indicator
        const loadingElement = document.createElement('div');
        loadingElement.className = 'loading-indicator';
        loadingElement.innerHTML = '<div class="dot-pulse"></div>';
        projectChatMessages.appendChild(loadingElement);
        projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
        
        // Make API call with project context
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                projectId: projectId,
                projectName: projectName,
                sessionId: localStorage.getItem('minerva_session_id')
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            const loadingIndicator = projectChatMessages.querySelector('.loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // Add AI response to project chat
            const aiElement = document.createElement('div');
            aiElement.className = 'ai-message';
            
            // Create the response container
            const responseContainer = document.createElement('div');
            responseContainer.className = 'response-content';
            responseContainer.innerHTML = data.response.replace(/\n/g, '<br>');
            aiElement.appendChild(responseContainer);
            
            // Add model info if available
            if (data.model_info) {
                const infoElement = document.createElement('div');
                infoElement.className = 'model-info';
                infoElement.setAttribute('data-model-info', JSON.stringify(data.model_info));
                
                // Display model info
                const primaryModel = data.model_info.primary_model || 'Think Tank';
                infoElement.innerHTML = `
                    <span class="model-badge">${primaryModel}</span>
                    <button class="model-info-toggle" title="Show model details">
                        <i class="fas fa-info-circle"></i>
                    </button>
                `;
                
                aiElement.appendChild(infoElement);
            }
            
            projectChatMessages.appendChild(aiElement);
            projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
            
            // Save to project-specific chat history
            saveProjectChatHistory(projectId);
        })
        .catch(error => {
            console.error('Error:', error);
            // Remove loading indicator
            const loadingIndicator = projectChatMessages.querySelector('.loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // Add error message
            const errorElement = document.createElement('div');
            errorElement.className = 'system-message error';
            errorElement.textContent = 'Error: Could not get response from Minerva. Please try again.';
            projectChatMessages.appendChild(errorElement);
            projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
        });
    }
}

// Save project-specific chat history
function saveProjectChatHistory(projectId) {
    if (!projectId) return;
    
    const projectChatMessages = document.getElementById('project-chat-messages');
    if (!projectChatMessages) return;
    
    const messages = Array.from(projectChatMessages.children).map(msg => {
        const type = msg.classList.contains('user-message') ? 'user' : 
                  msg.classList.contains('ai-message') ? 'ai' : 'system';
        
        let modelInfo = null;
        if (type === 'ai') {
            const infoElement = msg.querySelector('.model-info');
            if (infoElement) {
                modelInfo = infoElement.getAttribute('data-model-info');
            }
        }
        
        return {
            type: type,
            content: type === 'ai' ? msg.querySelector('.response-content').innerHTML : msg.textContent,
            modelInfo: modelInfo
        };
    });
    
    // Save to localStorage
    localStorage.setItem(`minerva_project_${projectId}_chat`, JSON.stringify({
        messages: messages,
        timestamp: Date.now(),
        projectId: projectId
    }));
}

// Add a system message to the chat
function addSystemMessage(message) {
    let chatMessages;
    const chatMode = sessionStorage.getItem('minerva_chat_mode');
    
    if (chatMode === 'floating' || chatMode === 'standard') {
        chatMessages = document.querySelector('#chat-messages');
    } else if (chatMode === 'project') {
        chatMessages = document.querySelector('.project-chat-panel #chat-messages');
    }
    
    if (!chatMessages) {
        console.warn('Chat messages container not found');
        return;
    }
    
    const msgElement = document.createElement('div');
    msgElement.className = 'system-message';
    msgElement.textContent = message;
    
    chatMessages.appendChild(msgElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Extend the global sendMessage function to ensure context is preserved
if (typeof window.sendMessage === 'function') {
    const originalSendMessage = window.sendMessage;
    
    window.sendMessage = function() {
        // Add project context to API calls
        const projectId = sessionStorage.getItem('minerva_active_project_id');
        const projectName = sessionStorage.getItem('minerva_active_project_name');
        
        if (projectId) {
            // Pass project context to the API
            window.projectContext = {
                projectId: projectId,
                projectName: projectName
            };
        }
        
        // Call the original function
        originalSendMessage.apply(this, arguments);
    };
}
