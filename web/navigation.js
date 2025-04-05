/**
 * Minerva Navigation System
 * Provides unified navigation between different Minerva UI components
 * while maintaining conversation persistence.
 */

// Initialize the navigation system
document.addEventListener('DOMContentLoaded', function() {
    console.log("Initializing Minerva navigation system");
    setupNavigationLinks();
    setupProjectNavigation();
});

// Setup main navigation links
function setupNavigationLinks() {
    const navLinks = [
        { name: 'Home', url: '/', icon: 'home' },
        { name: 'Memories', url: '/memories', icon: 'brain' },
        { name: 'Projects', url: '/dashboard', icon: 'project-diagram' },
        { name: 'Settings', url: '/settings', icon: 'cog' },
        { name: 'Analytics', url: '/analytics', icon: 'chart-bar' }
    ];
    
    // Create navigation bar if it doesn't exist
    if (!document.getElementById('minerva-nav')) {
        const navBar = document.createElement('div');
        navBar.id = 'minerva-nav';
        navBar.className = 'minerva-navigation';
        navBar.innerHTML = '<div class="nav-container"></div>';
        document.body.appendChild(navBar);
        
        const navContainer = navBar.querySelector('.nav-container');
        navLinks.forEach(link => {
            const navItem = document.createElement('a');
            navItem.href = link.url;
            navItem.className = 'nav-item';
            navItem.innerHTML = `<i class="fas fa-${link.icon}"></i> ${link.name}`;
            navItem.addEventListener('click', function(e) {
                // Save current conversation state before navigation
                if (window.minervaChat && window.minervaChat.saveConversationState) {
                    window.minervaChat.saveConversationState();
                }
            });
            navContainer.appendChild(navItem);
        });
    }
}

// Setup project-specific navigation
function setupProjectNavigation() {
    // Load and display projects
    fetch('/api/projects/all')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.projects) {
                // Initialize project switcher if in project context
                if (window.location.pathname.includes('/projects/') ||
                    window.location.pathname.includes('/dashboard')) {
                    createProjectSwitcher(data.projects);
                }
            }
        })
        .catch(err => console.error('Error loading projects:', err));
}

// Create project switcher UI
function createProjectSwitcher(projects) {
    if (!document.getElementById('project-switcher')) {
        const switcher = document.createElement('div');
        switcher.id = 'project-switcher';
        switcher.className = 'project-switcher';
        
        const currentProject = getCurrentProjectFromUrl();
        const dropdown = document.createElement('select');
        dropdown.addEventListener('change', function() {
            window.location.href = `/projects/${this.value}`;
        });
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select Project';
        dropdown.appendChild(defaultOption);
        
        // Add project options
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            if (project.id === currentProject) {
                option.selected = true;
            }
            dropdown.appendChild(option);
        });
        
        switcher.appendChild(dropdown);
        
        // Add to document
        const target = document.querySelector('.card-header') || document.body;
        target.prepend(switcher);
    }
}

// Extract current project ID from URL
function getCurrentProjectFromUrl() {
    const path = window.location.pathname;
    const matches = path.match(/\/projects\/([^\/]+)/);
    return matches ? matches[1] : null;
}

// Global navigation API
window.MinervaNavigation = {
    navigateTo: function(url, preserveChat = true) {
        // Save chat state if preserving
        if (preserveChat && window.minervaChat && window.minervaChat.saveConversationState) {
            window.minervaChat.saveConversationState();
        }
        window.location.href = url;
    },
    
    openProject: function(projectId) {
        window.location.href = `/projects/${projectId}`;
    },
    
    createProjectFromChat: function() {
        // Get current conversation
        const conversationId = localStorage.getItem('minerva_conversation_id');
        if (!conversationId) {
            alert('No active conversation to convert to project');
            return;
        }
        
        // Prompt for project name
        const projectName = prompt('Enter project name:', 'Project from Chat');
        if (!projectName) return;
        
        // Create project API call
        fetch('/api/projects/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: projectName,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Project created successfully!');
                window.location.href = `/projects/${data.project_id}`;
            } else {
                alert('Failed to create project: ' + data.message);
            }
        })
        .catch(err => {
            console.error('Error creating project:', err);
            alert('Error creating project');
        });
    }
};
