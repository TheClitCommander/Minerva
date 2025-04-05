/**
 * Project Manager for Minerva
 * Handles project creation, editing, and conversation-to-project conversion
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the project conversion UI if present
    initializeProjectConversion();
    
    // Listen for project organization events
    document.body.addEventListener('click', function(event) {
        // Handle project management button clicks
        if (event.target.closest('#create-project-from-conversation')) {
            showProjectConversionDialog();
        }
    });
});

/**
 * Initialize the project conversion UI
 */
function initializeProjectConversion() {
    // Add conversion button to the chat interface if not already present
    const chatInterface = document.querySelector('.chat-controls');
    
    if (chatInterface && !document.getElementById('create-project-from-conversation')) {
        const projectButton = document.createElement('button');
        projectButton.id = 'create-project-from-conversation';
        projectButton.className = 'project-btn';
        projectButton.innerHTML = '<i class="fas fa-project-diagram"></i> Create Project';
        projectButton.title = 'Convert this conversation to a project';
        
        // Add button to the chat interface
        chatInterface.appendChild(projectButton);
    }
}

/**
 * Show the dialog to convert a conversation to a project
 */
function showProjectConversionDialog() {
    // Get the active conversation ID
    const conversationId = window.ThinkTankAPI ? 
        window.ThinkTankAPI.getActiveConversation() : 
        localStorage.getItem('minerva_conversation_id');
    
    if (!conversationId) {
        showNotification('No active conversation to convert', 'error');
        return;
    }
    
    // Check if the dialog exists, if not create it
    let dialog = document.getElementById('project-conversion-dialog');
    
    if (!dialog) {
        dialog = document.createElement('div');
        dialog.id = 'project-conversion-dialog';
        dialog.className = 'modal-dialog';
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Create Project from Conversation</h3>
                    <button class="close-button" onclick="this.parentElement.parentElement.parentElement.style.display='none'">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="project-name">Project Name:</label>
                        <input type="text" id="project-name" placeholder="Enter project name">
                    </div>
                    <div class="form-group">
                        <label for="project-description">Description (optional):</label>
                        <textarea id="project-description" placeholder="Brief description of the project"></textarea>
                    </div>
                    <div class="form-actions">
                        <button id="convert-conversation-btn" class="primary-btn">Create Project</button>
                        <button class="cancel-btn" onclick="this.parentElement.parentElement.parentElement.parentElement.style.display='none'">Cancel</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);
        
        // Add event listener for the convert button
        document.getElementById('convert-conversation-btn').addEventListener('click', convertConversationToProject);
    }
    
    // Show the dialog
    dialog.style.display = 'flex';
}

/**
 * Convert a conversation to a project
 */
async function convertConversationToProject() {
    const nameInput = document.getElementById('project-name');
    const descriptionInput = document.getElementById('project-description');
    
    if (!nameInput || !nameInput.value.trim()) {
        showNotification('Please enter a project name', 'error');
        return;
    }
    
    const projectData = {
        name: nameInput.value.trim(),
        description: descriptionInput ? descriptionInput.value.trim() : ''
    };
    
    // Get the active conversation ID
    const conversationId = window.ThinkTankAPI ? 
        window.ThinkTankAPI.getActiveConversation() : 
        localStorage.getItem('minerva_conversation_id');
    
    if (!conversationId) {
        showNotification('No active conversation to convert', 'error');
        return;
    }
    
    try {
        // Use ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.conversationToProject) {
            const project = await window.ThinkTankAPI.conversationToProject(conversationId, projectData);
            
            // Close the dialog
            document.getElementById('project-conversion-dialog').style.display = 'none';
            
            // Clear inputs
            nameInput.value = '';
            if (descriptionInput) descriptionInput.value = '';
            
            // Show success message
            showNotification('Project created successfully', 'success');
            
            // Redirect to the project page if it exists
            if (project && project.id) {
                setTimeout(() => {
                    window.location.href = `dashboard.html?project=${project.id}`;
                }, 1500);
            }
        } else {
            // Fallback to traditional fetch
            const response = await fetch(`/api/conversations/${conversationId}/to-project`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(projectData)
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create project: ${response.status}`);
            }
            
            const project = await response.json();
            
            // Close the dialog
            document.getElementById('project-conversion-dialog').style.display = 'none';
            
            // Clear inputs
            nameInput.value = '';
            if (descriptionInput) descriptionInput.value = '';
            
            // Show success message
            showNotification('Project created successfully', 'success');
            
            // Redirect to the project page if it exists
            if (project && project.id) {
                setTimeout(() => {
                    window.location.href = `dashboard.html?project=${project.id}`;
                }, 1500);
            }
        }
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project. Please try again.', 'error');
    }
}

/**
 * Show a notification message
 * @param {string} message - Message to show
 * @param {string} type - Type of notification (default, error, success)
 */
function showNotification(message, type = 'default') {
    // Create notification element if it doesn't exist
    let notification = document.getElementById('notification');
    
    if (!notification) {
        notification = document.createElement('div');
        notification.id = 'notification';
        document.body.appendChild(notification);
        
        // Add styles if not already defined in CSS
        if (!document.querySelector('style#notification-styles')) {
            const styleEl = document.createElement('style');
            styleEl.id = 'notification-styles';
            styleEl.textContent = `
                #notification {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 5px;
                    background-color: #333;
                    color: white;
                    z-index: 1000;
                    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
                    transition: opacity 0.3s, bottom 0.3s;
                    opacity: 0;
                }
                #notification.visible {
                    opacity: 1;
                }
                #notification.default {
                    background-color: #333;
                }
                #notification.error {
                    background-color: #d9534f;
                }
                #notification.success {
                    background-color: #5cb85c;
                }
            `;
            document.head.appendChild(styleEl);
        }
    }
    
    // Set content and type
    notification.textContent = message;
    notification.className = type;
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('visible');
    }, 10);
    
    // Hide after 3 seconds
    setTimeout(() => {
        notification.classList.remove('visible');
    }, 3000);
}

/**
 * Create a new project
 */
async function createNewProject() {
    const nameInput = document.getElementById('new-project-name');
    
    if (!nameInput || !nameInput.value.trim()) {
        showNotification('Please enter a project name', 'error');
        return;
    }
    
    const projectName = nameInput.value.trim();
    
    try {
        // Use ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.createProject) {
            await window.ThinkTankAPI.createProject({
                name: projectName
            });
        } else {
            // Fallback to traditional fetch
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: projectName
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create project: ${response.status}`);
            }
        }
        
        // Clear input
        nameInput.value = '';
        
        // Reload projects
        if (typeof loadProjectsForOrganizer === 'function') {
            loadProjectsForOrganizer();
        }
        
        if (typeof loadProjectsList === 'function') {
            loadProjectsList();
        }
        
        // Show success message
        showNotification('Project created successfully', 'success');
    } catch (error) {
        console.error('Error creating project:', error);
        showNotification('Failed to create project. Please try again.', 'error');
    }
}

/**
 * Delete a project
 * @param {string} projectId - ID of the project to delete
 */
async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project? All conversations in this project will be moved to General.')) {
        return;
    }
    
    try {
        // Use ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.deleteProject) {
            await window.ThinkTankAPI.deleteProject(projectId);
            
            // Reload projects
            if (typeof loadProjectsForOrganizer === 'function') {
                loadProjectsForOrganizer();
            }
            
            if (typeof loadProjectsList === 'function') {
                loadProjectsList();
            }
            
            // Show success message
            showNotification('Project deleted successfully', 'success');
        } else {
            // Show a message that this feature requires the API
            showNotification('Project deletion requires the ThinkTankAPI to be available', 'error');
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        showNotification('Failed to delete project. Please try again.', 'error');
    }
}

/**
 * Rename a project
 * @param {string} projectId - ID of the project to rename
 */
async function renameProject(projectId) {
    const newName = prompt('Enter new project name:', '');
    
    if (!newName || !newName.trim()) {
        return;
    }
    
    try {
        // Use ThinkTankAPI if available
        if (window.ThinkTankAPI && window.ThinkTankAPI.updateProject) {
            await window.ThinkTankAPI.updateProject(projectId, {
                name: newName.trim()
            });
            
            // Reload projects
            if (typeof loadProjectsForOrganizer === 'function') {
                loadProjectsForOrganizer();
            }
            
            if (typeof loadProjectsList === 'function') {
                loadProjectsList();
            }
            
            // Show success message
            showNotification('Project renamed successfully', 'success');
        } else {
            // Show a message that this feature requires the API
            showNotification('Project renaming requires the ThinkTankAPI to be available', 'error');
        }
    } catch (error) {
        console.error('Error renaming project:', error);
        showNotification('Failed to rename project. Please try again.', 'error');
    }
}

// Make functions globally available
window.createNewProject = createNewProject;
window.deleteProject = deleteProject;
window.renameProject = renameProject;
window.showProjectConversionDialog = showProjectConversionDialog;
