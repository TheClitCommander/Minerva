/**
 * Minerva Orbital UI - Project Integration
 * 
 * This script handles project selection within the orbital UI
 * and connects it with the chat system, enabling contextual conversations
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Orbital UI project integration...');
    initProjectOrbIntegration();
});

// Initialize the project orb integration
function initProjectOrbIntegration() {
    // Set up project orb click handlers in the orbital UI
    setupProjectOrbHandlers();
    
    // Set up project creation from the UI
    setupProjectCreationHandler();
    
    // Listen for projectCreated events from the chat system
    document.addEventListener('projectCreated', function(e) {
        if (e.detail && e.detail.project) {
            // Create a new orb in the orbital UI for the project
            createProjectOrb(e.detail.project);
        }
    });
}

// Set up handlers for project orbs in the orbital UI
function setupProjectOrbHandlers() {
    // This will be called when orbital UI creates project orbs
    document.addEventListener('orbCreated', function(e) {
        if (e.detail && e.detail.orbElement && e.detail.orbData && e.detail.orbData.type === 'project') {
            const orbElement = e.detail.orbElement;
            const projectData = e.detail.orbData;
            
            // Add click handler to select the project
            orbElement.addEventListener('click', function() {
                // Set the active project in session
                sessionStorage.setItem('minerva_active_project_id', projectData.id);
                sessionStorage.setItem('minerva_active_project_name', projectData.name);
                
                // Dispatch project selected event for the chat system
                const event = new CustomEvent('projectSelected', {
                    detail: {
                        projectId: projectData.id,
                        projectName: projectData.name
                    }
                });
                document.dispatchEvent(event);
                
                // Update UI to show project is selected
                document.querySelectorAll('.project-orb').forEach(orb => {
                    orb.classList.remove('active-project');
                });
                orbElement.classList.add('active-project');
                
                // Set the project detail title
                const projectDetailTitle = document.getElementById('project-detail-title');
                if (projectDetailTitle) {
                    projectDetailTitle.textContent = projectData.name;
                }
                
                // Show the project detail view
                showProjectDetailView(projectData);
            });
        }
    });
    
    // Back button handler for project detail view
    const backToOrbitalBtn = document.getElementById('back-to-orbital');
    if (backToOrbitalBtn) {
        backToOrbitalBtn.addEventListener('click', function() {
            hideProjectDetailView();
            
            // Clear active project context
            sessionStorage.removeItem('minerva_active_project_id');
            sessionStorage.removeItem('minerva_active_project_name');
            
            // Notify chat system of context change
            const event = new CustomEvent('projectSelected', {
                detail: {
                    projectId: null,
                    projectName: null
                }
            });
            document.dispatchEvent(event);
        });
    }
}

// Set up project creation from the orbital UI
function setupProjectCreationHandler() {
    // Project button in the main chat interface
    const projectButton = document.getElementById('project-button');
    if (projectButton) {
        projectButton.addEventListener('click', function() {
            showProjectManagementPanel();
        });
    }
}

// Show the project management panel
function showProjectManagementPanel() {
    // Check if panel already exists
    let projectPanel = document.getElementById('project-management-panel');
    
    if (!projectPanel) {
        // Create the panel
        projectPanel = document.createElement('div');
        projectPanel.id = 'project-management-panel';
        projectPanel.className = 'side-panel';
        
        projectPanel.innerHTML = `
            <div class="panel-header">
                <h3>Project Management</h3>
                <button id="close-project-panel" class="close-button"><i class="fas fa-times"></i></button>
            </div>
            <div class="panel-content">
                <div class="panel-section">
                    <h4>Create New Project</h4>
                    <div class="input-group">
                        <input type="text" id="new-project-name" placeholder="Project Name">
                        <button id="create-new-project" class="primary-btn">Create</button>
                    </div>
                </div>
                <div class="panel-section">
                    <h4>Your Projects</h4>
                    <div id="project-list" class="project-list">
                        <!-- Projects will be populated here -->
                        <div class="no-projects-message">No projects yet. Create one above!</div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(projectPanel);
        
        // Set up event handlers
        const closeBtn = document.getElementById('close-project-panel');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                projectPanel.classList.add('hidden');
            });
        }
        
        const createBtn = document.getElementById('create-new-project');
        const nameInput = document.getElementById('new-project-name');
        
        if (createBtn && nameInput) {
            createBtn.addEventListener('click', function() {
                const projectName = nameInput.value.trim();
                if (projectName) {
                    createNewProject(projectName);
                    nameInput.value = '';
                } else {
                    alert('Please enter a project name');
                }
            });
            
            nameInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    createBtn.click();
                }
            });
        }
        
        // Load existing projects
        loadProjects();
    } else {
        // Refresh project list
        loadProjects();
        
        // Show the panel if hidden
        projectPanel.classList.remove('hidden');
    }
}

// Create a new project
function createNewProject(projectName) {
    // Generate a unique project ID
    const projectId = 'project_' + Date.now();
    
    // Create project object
    const newProject = {
        id: projectId,
        name: projectName,
        createdAt: new Date().toISOString(),
        conversations: []
    };
    
    // Save project to localStorage
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
    
    // Create orb in orbital UI
    createProjectOrb(newProject);
    
    // Refresh project list
    loadProjects();
    
    // Set as active project
    sessionStorage.setItem('minerva_active_project_id', projectId);
    sessionStorage.setItem('minerva_active_project_name', projectName);
    
    // Notify chat system
    const event = new CustomEvent('projectSelected', {
        detail: {
            projectId: projectId,
            projectName: projectName
        }
    });
    document.dispatchEvent(event);
    
    console.log(`Created new project "${projectName}" with ID ${projectId}`);
}

// Load projects into the project management panel
function loadProjects() {
    const projectList = document.getElementById('project-list');
    if (!projectList) return;
    
    // Clear current list
    projectList.innerHTML = '';
    
    // Get projects from localStorage
    const savedProjects = localStorage.getItem('minerva_projects');
    let projects = [];
    
    if (savedProjects) {
        try {
            projects = JSON.parse(savedProjects);
        } catch (e) {
            console.error('Error parsing saved projects:', e);
        }
    }
    
    // Display projects or no projects message
    if (projects.length === 0) {
        projectList.innerHTML = '<div class="no-projects-message">No projects yet. Create one above!</div>';
        return;
    }
    
    // Sort projects by creation date (newest first)
    projects.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    
    // Add projects to list
    projects.forEach(project => {
        const projectItem = document.createElement('div');
        projectItem.className = 'project-item';
        
        // Format date
        const createdDate = new Date(project.createdAt);
        const formattedDate = createdDate.toLocaleDateString();
        
        projectItem.innerHTML = `
            <div class="project-item-name">${project.name}</div>
            <div class="project-item-date">${formattedDate}</div>
            <div class="project-item-actions">
                <button class="project-action select-project" data-project-id="${project.id}" title="Open project">
                    <i class="fas fa-folder-open"></i>
                </button>
                <button class="project-action delete-project" data-project-id="${project.id}" title="Delete project">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        projectList.appendChild(projectItem);
        
        // Set up action buttons
        const selectBtn = projectItem.querySelector('.select-project');
        const deleteBtn = projectItem.querySelector('.delete-project');
        
        if (selectBtn) {
            selectBtn.addEventListener('click', function() {
                const projectId = this.getAttribute('data-project-id');
                const projectData = projects.find(p => p.id === projectId);
                
                if (projectData) {
                    // Close project panel
                    const projectPanel = document.getElementById('project-management-panel');
                    if (projectPanel) {
                        projectPanel.classList.add('hidden');
                    }
                    
                    // Set active project
                    sessionStorage.setItem('minerva_active_project_id', projectId);
                    sessionStorage.setItem('minerva_active_project_name', projectData.name);
                    
                    // Notify chat system
                    const event = new CustomEvent('projectSelected', {
                        detail: {
                            projectId: projectId,
                            projectName: projectData.name
                        }
                    });
                    document.dispatchEvent(event);
                    
                    // Find and activate the project orb
                    const projectOrbs = document.querySelectorAll('.project-orb');
                    let orbFound = false;
                    
                    projectOrbs.forEach(orb => {
                        if (orb.getAttribute('data-project-id') === projectId) {
                            orb.click(); // Simulate click on the orb
                            orbFound = true;
                        }
                    });
                    
                    // If orb not found (maybe not created yet), create it
                    if (!orbFound) {
                        createProjectOrb(projectData);
                        
                        // Show project detail view
                        showProjectDetailView(projectData);
                    }
                }
            });
        }
        
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                const projectId = this.getAttribute('data-project-id');
                const projectData = projects.find(p => p.id === projectId);
                
                if (projectData && confirm(`Are you sure you want to delete the project "${projectData.name}"?`)) {
                    // Remove from array
                    const updatedProjects = projects.filter(p => p.id !== projectId);
                    
                    // Save updated list
                    localStorage.setItem('minerva_projects', JSON.stringify(updatedProjects));
                    
                    // Remove project-specific chat history
                    localStorage.removeItem(`minerva_project_${projectId}_chat`);
                    
                    // Remove project orb if exists
                    const projectOrbs = document.querySelectorAll('.project-orb');
                    projectOrbs.forEach(orb => {
                        if (orb.getAttribute('data-project-id') === projectId) {
                            orb.remove();
                        }
                    });
                    
                    // If this was the active project, clear context
                    if (sessionStorage.getItem('minerva_active_project_id') === projectId) {
                        sessionStorage.removeItem('minerva_active_project_id');
                        sessionStorage.removeItem('minerva_active_project_name');
                        
                        // Hide project detail view if open
                        hideProjectDetailView();
                        
                        // Notify chat system
                        const event = new CustomEvent('projectSelected', {
                            detail: {
                                projectId: null,
                                projectName: null
                            }
                        });
                        document.dispatchEvent(event);
                    }
                    
                    // Refresh project list
                    loadProjects();
                }
            });
        }
    });
}

// Create a project orb in the orbital UI
function createProjectOrb(projectData) {
    if (!projectData || !projectData.id || !projectData.name) return;
    
    // This function assumes there's a mechanism in orbital UI to add orbs
    // If such a mechanism exists, call it - for now we'll implement a basic version
    
    // Check if orb container exists
    let orbContainer = document.querySelector('.orb-container');
    if (!orbContainer) {
        // Create a basic orb container if it doesn't exist
        orbContainer = document.createElement('div');
        orbContainer.className = 'orb-container';
        document.body.appendChild(orbContainer);
    }
    
    // Check if this project already has an orb
    const existingOrb = document.querySelector(`.project-orb[data-project-id="${projectData.id}"]`);
    if (existingOrb) {
        return; // Orb already exists
    }
    
    // Create a new project orb
    const projectOrb = document.createElement('div');
    projectOrb.className = 'orb project-orb';
    projectOrb.setAttribute('data-project-id', projectData.id);
    projectOrb.setAttribute('data-orb-type', 'project');
    projectOrb.setAttribute('title', projectData.name);
    
    // Add a project icon or first letter of project name
    projectOrb.innerHTML = `
        <div class="orb-icon">
            <i class="fas fa-folder-open"></i>
        </div>
        <div class="orb-label">${projectData.name}</div>
    `;
    
    // Add to orbital UI
    orbContainer.appendChild(projectOrb);
    
    // Add click handler
    projectOrb.addEventListener('click', function() {
        // Set the active project
        sessionStorage.setItem('minerva_active_project_id', projectData.id);
        sessionStorage.setItem('minerva_active_project_name', projectData.name);
        
        // Update UI to show project is selected
        document.querySelectorAll('.project-orb').forEach(orb => {
            orb.classList.remove('active-project');
        });
        projectOrb.classList.add('active-project');
        
        // Notify chat system
        const event = new CustomEvent('projectSelected', {
            detail: {
                projectId: projectData.id,
                projectName: projectData.name
            }
        });
        document.dispatchEvent(event);
        
        // Show project detail view
        showProjectDetailView(projectData);
    });
    
    // Dispatch orbCreated event for any other components that need to know
    const event = new CustomEvent('orbCreated', {
        detail: {
            orbElement: projectOrb,
            orbData: {
                type: 'project',
                ...projectData
            }
        }
    });
    document.dispatchEvent(event);
    
    return projectOrb;
}

// Show the project detail view
function showProjectDetailView(projectData) {
    const projectDetailView = document.getElementById('project-detail-view');
    const orbitalView = document.querySelector('.orbital-container');
    
    if (projectDetailView && orbitalView) {
        // Hide orbital view
        orbitalView.classList.add('hidden');
        
        // Update project title
        const detailTitle = projectDetailView.querySelector('.detail-view-title');
        if (detailTitle) {
            detailTitle.textContent = projectData.name;
        }
        
        // Load project content
        const detailContent = projectDetailView.querySelector('.detail-view-content');
        if (detailContent) {
            // Here we could load more project-specific content
            // For now we just ensure the chat panel is visible
            const projectChatPanel = detailContent.querySelector('.project-chat-panel');
            if (projectChatPanel) {
                projectChatPanel.classList.remove('hidden');
            }
        }
        
        // Show project detail view
        projectDetailView.classList.remove('hidden');
    }
}

// Hide the project detail view
function hideProjectDetailView() {
    const projectDetailView = document.getElementById('project-detail-view');
    const orbitalView = document.querySelector('.orbital-container');
    
    if (projectDetailView && orbitalView) {
        // Hide project detail view
        projectDetailView.classList.add('hidden');
        
        // Show orbital view
        orbitalView.classList.remove('hidden');
    }
}

// Initialize - load projects from localStorage and create orbs
function initializeProjectOrbs() {
    const savedProjects = localStorage.getItem('minerva_projects');
    let projects = [];
    
    if (savedProjects) {
        try {
            projects = JSON.parse(savedProjects);
        } catch (e) {
            console.error('Error parsing saved projects:', e);
        }
    }
    
    // Create orbs for each project
    projects.forEach(project => {
        createProjectOrb(project);
    });
    
    // Check if there's an active project in session
    const activeProjectId = sessionStorage.getItem('minerva_active_project_id');
    if (activeProjectId) {
        const activeProject = projects.find(p => p.id === activeProjectId);
        if (activeProject) {
            // Find and activate the project orb
            const projectOrbs = document.querySelectorAll('.project-orb');
            let orbFound = false;
            
            projectOrbs.forEach(orb => {
                if (orb.getAttribute('data-project-id') === activeProjectId) {
                    // Add active class
                    orb.classList.add('active-project');
                    orbFound = true;
                    
                    // Show project detail view
                    showProjectDetailView(activeProject);
                }
            });
            
            // If orb not found but we have active project, create it
            if (!orbFound) {
                const newOrb = createProjectOrb(activeProject);
                if (newOrb) {
                    newOrb.classList.add('active-project');
                    showProjectDetailView(activeProject);
                }
            }
        }
    }
}

// Call initialization when document is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a short time to ensure orbital UI is initialized
    setTimeout(initializeProjectOrbs, 500);
});
