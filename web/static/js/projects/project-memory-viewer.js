/**
 * Project Memory Viewer
 * Display project context in the chat interface (objectives, tasks, logs)
 * Following Minerva Master Ruleset (Rule #3 for Project Organization)
 */

class ProjectMemoryViewer {
    constructor() {
        this.isVisible = false;
        this.currentProject = null;
        this.currentDialog = null;
        this.taskSuggestions = [];
        this.suggestionText = '';
        this.viewerElement = null;
        this.toggleElement = null;
        this.projectData = null;
        this.suggestionElement = null;
        this.activeSuggestion = null;
        
        // Initialize on DOM load
        this.init();
    }
    
    /**
     * Initialize the viewer
     */
    init() {
        // Create the DOM elements when document is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createElements());
        } else {
            this.createElements();
        }
        
        // Watch for session changes that might affect active project
        window.addEventListener('minervaSessionChanged', (e) => {
            if (e.detail && e.detail.activeProject) {
                this.loadProject(e.detail.activeProject);
            }
        });
        
        // Listen for manual project links
        window.addEventListener('projectLinked', (e) => {
            if (e.detail && e.detail.projectName) {
                this.loadProject(e.detail.projectName);
            }
        });
        
        // Listen for AI responses that might contain intent suggestions
        window.addEventListener('aiResponseReceived', (e) => {
            if (e.detail && e.detail.metadata && e.detail.metadata.intent_suggestion) {
                this.showIntentSuggestion(e.detail.metadata.intent_suggestion);
            }
        });
    }
    
    /**
     * Create the viewer elements and append to DOM
     */
    createElements() {
        // Check if elements already exist
        if (document.getElementById('project-memory-viewer')) {
            return;
        }
        
        // Create main viewer container
        this.viewerElement = document.createElement('div');
        this.viewerElement.id = 'project-memory-viewer';
        this.viewerElement.className = 'project-memory-viewer';
        
        // Create toggle button
        this.toggleElement = document.createElement('div');
        this.toggleElement.id = 'project-memory-toggle';
        this.toggleElement.className = 'project-memory-toggle';
        this.toggleElement.innerHTML = '<i class="fas fa-project-diagram"></i>';
        this.toggleElement.title = 'Toggle Project Memory Viewer';
        this.toggleElement.addEventListener('click', () => this.toggle());
        
        // Create suggestion element (initially hidden)
        this.suggestionElement = document.createElement('div');
        this.suggestionElement.id = 'project-intent-suggestion';
        this.suggestionElement.className = 'project-intent-suggestion';
        this.suggestionElement.style.display = 'none';
        
        // Add elements to DOM
        document.body.appendChild(this.viewerElement);
        document.body.appendChild(this.toggleElement);
        document.body.appendChild(this.suggestionElement);
        
        // Populate initial structure (empty state)
        this.renderEmptyState();
        
        // Check if there's already an active project in session
        this.checkActiveProject();
    }
    
    /**
     * Check if there's an active project in the current session
     */
    checkActiveProject() {
        // Try to get from sessionStorage first
        let activeProject = null;
        
        try {
            // Look in session data
            const sessionData = JSON.parse(sessionStorage.getItem('minervaSessionData') || '{}');
            activeProject = sessionData.activeProject;
            
            // If not found, check URL for project parameter
            if (!activeProject && window.location.search) {
                const urlParams = new URLSearchParams(window.location.search);
                activeProject = urlParams.get('project');
            }
            
            if (activeProject) {
                this.loadProject(activeProject);
            }
        } catch (error) {
            console.error('Error checking active project:', error);
        }
    }
    
    /**
     * Load a project's data and display in the viewer
     * @param {string} projectName - Name of the project to load
     */
    loadProject(projectName) {
        if (!projectName) return;
        
        this.currentProject = projectName;
        
        // Show loading state
        this.renderLoadingState();
        
        // Fetch project context from API
        fetch(`/api/projects/${encodeURIComponent(projectName)}/context`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load project data');
                }
                return response.json();
            })
            .then(data => {
                this.projectData = data;
                this.renderProjectData();
                this.showViewer();
                
                // After loading the project data, get task suggestions
                this.loadTaskSuggestions();
            })
            .catch(error => {
                console.error('Error loading project context:', error);
                this.renderError('Failed to load project data. Please try again.');
            });
    }
    
    /**
     * Load task suggestions from the API
     */
    loadTaskSuggestions() {
        if (!this.currentProject) return;
        
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/suggest_next_tasks`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.suggestions) {
                    this.taskSuggestions = data.suggestions;
                    this.suggestionText = data.suggestion_text || '';
                    this.renderTaskSuggestions();
                } else if (data.error) {
                    console.error('Error loading task suggestions:', data.error);
                }
            })
            .catch(error => {
                console.error('Error loading task suggestions:', error);
            });
    }
    
    /**
     * Render loading state
     */
    renderLoadingState() {
        if (!this.viewerElement) return;
        
        this.viewerElement.innerHTML = `
            <div class="project-memory-header">
                <div class="project-memory-title">
                    <i class="fas fa-spinner fa-spin"></i>
                    Loading Project...
                </div>
                <div class="project-memory-actions">
                    <button class="project-memory-action-button" title="Close" onclick="projectMemoryViewer.hide()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="project-memory-content">
                <div class="project-memory-empty">
                    <i class="fas fa-spinner fa-spin"></i>
                    <p>Loading project data...</p>
                </div>
            </div>
        `;
    }
    
    /**
     * Render error state
     * @param {string} errorMessage - Error message to display
     */
    renderError(errorMessage) {
        if (!this.viewerElement) return;
        
        this.viewerElement.innerHTML = `
            <div class="project-memory-header">
                <div class="project-memory-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error
                </div>
                <div class="project-memory-actions">
                    <button class="project-memory-action-button" title="Retry" onclick="projectMemoryViewer.loadProject('${this.currentProject}')">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button class="project-memory-action-button" title="Close" onclick="projectMemoryViewer.hide()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="project-memory-content">
                <div class="project-memory-empty">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>${errorMessage}</p>
                </div>
            </div>
        `;
    }
    
    /**
     * Render empty state (no project selected)
     */
    renderEmptyState() {
        if (!this.viewerElement) return;
        
        this.viewerElement.innerHTML = `
            <div class="project-memory-header">
                <div class="project-memory-title">
                    <i class="fas fa-project-diagram"></i>
                    Project Memory
                </div>
                <div class="project-memory-actions">
                    <button class="project-memory-action-button" title="Close" onclick="projectMemoryViewer.hide()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="project-memory-content">
                <div class="project-memory-empty">
                    <i class="fas fa-info-circle"></i>
                    <p>No active project selected. Link this conversation to a project to see context details.</p>
                </div>
            </div>
        `;
    }
    
    /**
     * Render project data
     */
    renderProjectData() {
        if (!this.viewerElement || !this.projectData) return;
        
        const objectives = this.projectData.objectives || [];
        const tasks = this.projectData.task_queue || [];
        const logs = this.projectData.logs || [];
        const notes = this.projectData.notes || [];
        
        // If we have a suggestion active, make sure it's for this project
        if (this.activeSuggestion && 
            this.currentProject && 
            this.activeSuggestion.project_name && 
            this.activeSuggestion.project_name !== this.currentProject) {
            this.hideSuggestion();
        }
        
        let html = `
            <div class="project-memory-header">
                <div class="project-memory-title">
                    <i class="fas fa-project-diagram"></i>
                    ${this.currentProject}
                </div>
                <div class="project-memory-actions">
                    <button class="project-memory-action-button" title="Edit in Dashboard" onclick="window.open('/projects?project=${encodeURIComponent(this.currentProject)}', '_blank')">
                        <i class="fas fa-external-link-alt"></i>
                    </button>
                    <button class="project-memory-action-button" title="Refresh" onclick="projectMemoryViewer.loadProject('${this.currentProject}')">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button class="project-memory-action-button" title="Close" onclick="projectMemoryViewer.hide()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="project-memory-content">
        `;
        
        // Objectives section
        if (objectives.length > 0) {
            html += `
                <div class="project-memory-section">
                    <div class="project-memory-section-title">
                        <i class="fas fa-bullseye"></i> Objectives
                    </div>
                    <ul class="project-memory-list">
                        ${objectives.map(objective => `<li>${objective}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Task suggestions section
        html += `
            <div id="task-suggestion-container" class="task-suggestion-container"></div>
        `;
        
        // Tasks section
        if (tasks.length > 0) {
            html += `
                <div class="project-memory-section">
                    <div class="project-memory-section-title">
                        <i class="fas fa-tasks"></i> Tasks
                        <div class="project-memory-task-legend">
                            <span class="priority-badge high">🔥 High</span>
                            <span class="priority-badge medium">🟡 Medium</span>
                            <span class="priority-badge low">⚪️ Low</span>
                        </div>
                    </div>
                    <div class="project-memory-list">
                        ${tasks.map((task, index) => {
                            // Handle both string and object formats
                            const isTaskObject = typeof task === 'object' && task !== null;
                            const isCompleted = isTaskObject && (task.completed || task.done);
                            const taskText = isTaskObject ? (task.text || task.task) : task;
                            
                            // Get task priority if available
                            let priorityBadge = '';
                            if (isTaskObject && task.priority) {
                                const priorityClass = task.priority.toLowerCase();
                                let priorityIcon = '⚪️';
                                
                                if (priorityClass === 'high') priorityIcon = '🔥';
                                else if (priorityClass === 'medium') priorityIcon = '🟡';
                                
                                priorityBadge = `<span class="priority-badge ${priorityClass}">${priorityIcon} ${task.priority}</span>`;
                            }
                            
                            // Get deadline if available
                            let deadlineBadge = '';
                            if (isTaskObject && task.deadline) {
                                try {
                                    const deadlineDate = new Date(task.deadline);
                                    const now = new Date();
                                    
                                    // Check if deadline is valid
                                    if (!isNaN(deadlineDate.getTime())) {
                                        const isOverdue = deadlineDate < now;
                                        const dateOptions = { month: 'short', day: 'numeric', year: 'numeric' };
                                        const formattedDate = deadlineDate.toLocaleDateString(undefined, dateOptions);
                                        
                                        deadlineBadge = `<span class="deadline-badge ${isOverdue ? 'overdue' : ''}">
                                            <i class="far fa-calendar-alt"></i> ${formattedDate}
                                        </span>`;
                                    }
                                } catch (e) {
                                    console.error('Error parsing deadline', e);
                                }
                            }
                            
                            // Get dependencies if available
                            let dependenciesSection = '';
                            if (isTaskObject && task.dependencies && task.dependencies.length > 0) {
                                dependenciesSection = `
                                    <div class="task-dependencies">
                                        <i class="fas fa-link"></i> Depends on: 
                                        <span class="dependency-list">${task.dependencies.join(', ')}</span>
                                    </div>
                                `;
                            }
                            
                            // Task edit buttons
                            const editButtons = `
                                <div class="task-edit-buttons">
                                    <button class="task-edit-button" title="Set Priority" onclick="projectMemoryViewer.showTaskPriorityDialog(${index})">
                                        <i class="fas fa-flag"></i>
                                    </button>
                                    <button class="task-edit-button" title="Set Deadline" onclick="projectMemoryViewer.showTaskDeadlineDialog(${index})">
                                        <i class="far fa-calendar-alt"></i>
                                    </button>
                                    <button class="task-edit-button" title="Add Dependency" onclick="projectMemoryViewer.showTaskDependencyDialog(${index})">
                                        <i class="fas fa-link"></i>
                                    </button>
                                </div>
                            `;
                            
                            return `
                                <div class="project-memory-task ${isCompleted ? 'completed' : ''}" data-task-index="${index}">
                                    <div class="task-main-content">
                                        <div class="project-memory-task-checkbox" onclick="projectMemoryViewer.toggleTaskStatus(${index})">
                                            ${isCompleted ? '<i class="fas fa-check"></i>' : ''}
                                        </div>
                                        <div class="project-memory-task-text">${taskText}</div>
                                        <div class="task-badges">
                                            ${priorityBadge}
                                            ${deadlineBadge}
                                        </div>
                                        ${editButtons}
                                    </div>
                                    ${dependenciesSection}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // Recent logs section (last 5)
        if (logs.length > 0) {
            const recentLogs = logs.slice(-5).reverse();
            html += `
                <div class="project-memory-section">
                    <div class="project-memory-section-title">
                        <i class="fas fa-history"></i> Recent Activity
                    </div>
                    <div class="project-memory-list">
                        ${recentLogs.map(log => {
                            // Try to extract timestamp if it's in a known format
                            let logText = log;
                            let timestamp = '';
                            
                            // Check if log is in format "[2023-04-06] Log message"
                            const timestampMatch = typeof log === 'string' && log.match(/^\[(.*?)\](.*)/);
                            if (timestampMatch) {
                                timestamp = timestampMatch[1];
                                logText = timestampMatch[2].trim();
                            }
                            
                            return `
                                <div class="project-memory-log">
                                    <div class="project-memory-log-text">${logText}</div>
                                    ${timestamp ? `<div class="project-memory-log-time">${timestamp}</div>` : ''}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            `;
        }
        
        // Notes section
        if (notes.length > 0) {
            html += `
                <div class="project-memory-section">
                    <div class="project-memory-section-title">
                        <i class="fas fa-sticky-note"></i> Notes
                    </div>
                    <ul class="project-memory-list">
                        ${notes.map(note => `<li>${note}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        // Close content div
        html += `</div>`;
        
        // Set HTML
        this.viewerElement.innerHTML = html;
    }
    
    /**
     * Toggle viewer visibility
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    /**
     * Show the viewer and toggle button
     */
    showViewer() {
        if (!this.viewerElement || !this.toggleElement) return;
        
        // Show toggle button
        this.toggleElement.classList.add('visible');
        
        // Adjust chat container if it exists
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.classList.add('with-project-memory');
        }
    }
    
    /**
     * Show viewer
     */
    show() {
        if (!this.viewerElement) return;
        if (!this.currentProject) {
            this.checkActiveProject();
        }
        
        this.viewerElement.classList.add('visible');
        this.isVisible = true;
    }
    
    /**
     * Hide viewer
     */
    hide() {
        if (!this.viewerElement) return;
        
        this.viewerElement.classList.remove('visible');
        this.isVisible = false;
        
        // Adjust chat container if it exists
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.classList.remove('with-project-memory');
        }
    }
    
    /**
     * Show an intent suggestion banner
     * @param {Object} suggestion - The suggestion object from AI
     */
    showIntentSuggestion(suggestion) {
        if (!this.suggestionElement || !suggestion) return;
        
        // Save the active suggestion
        this.activeSuggestion = suggestion;
        
        // Create suggestion UI
        this.suggestionElement.innerHTML = `
            <div class="suggestion-content">
                <div class="suggestion-icon">
                    <i class="fas ${this.getSuggestionIcon(suggestion.action_type)}"></i>
                </div>
                <div class="suggestion-text">${suggestion.suggestion}</div>
                <div class="suggestion-actions">
                    <button class="suggestion-action accept" onclick="projectMemoryViewer.handleIntentSuggestion(true)">
                        <i class="fas fa-check"></i> Yes
                    </button>
                    <button class="suggestion-action reject" onclick="projectMemoryViewer.handleIntentSuggestion(false)">
                        <i class="fas fa-times"></i> No
                    </button>
                </div>
            </div>
        `;
        
        // Show the suggestion
        this.suggestionElement.style.display = 'block';
        
        // Add animation class
        setTimeout(() => {
            this.suggestionElement.classList.add('visible');
        }, 10);
    }
    
    /**
     * Get appropriate icon for suggestion type
     * @param {string} actionType - The type of action suggested
     * @returns {string} - Font Awesome icon class
     */
    getSuggestionIcon(actionType) {
        switch (actionType) {
            case 'add_task':
                return 'fa-tasks';
            case 'mark_task_done':
                return 'fa-check-circle';
            case 'add_log':
                return 'fa-history';
            case 'add_note':
                return 'fa-sticky-note';
            default:
                return 'fa-lightbulb';
        }
    }
    
    /**
     * Handle user response to intent suggestion
     * @param {boolean} accepted - Whether the user accepted the suggestion
     */
    handleIntentSuggestion(accepted) {
        if (!this.activeSuggestion) return;
        
        if (accepted) {
            // User accepted the suggestion - update project context
            this.updateProjectContext(
                this.activeSuggestion.action_type,
                this.activeSuggestion.content,
                this.activeSuggestion.project_name || this.currentProject
            );
        } else {
            // User rejected - just hide the suggestion
            this.hideSuggestion();
        }
    }
    
    /**
     * Hide the active suggestion
     */
    hideSuggestion() {
        if (!this.suggestionElement) return;
        
        this.suggestionElement.style.display = 'none';
        this.suggestionElement.classList.remove('visible');
        this.activeSuggestion = null;
    }
    
    /**
     * Update project context with a new item based on suggestion
     * @param {string} actionType - Type of action (add_task, mark_task_done, etc.)
     * @param {string} content - Content of the item to add/update
     * @param {string} projectName - Name of the project to update
     */
    updateProjectContext(actionType, content, projectName) {
        if (!projectName || !actionType || !content) {
            console.error('Missing required parameters for project context update');
            this.showToast('Error: Missing required information for project update.', 'error');
            this.hideSuggestion();
            return;
        }
        
        // Show feedback that we're processing
        this.suggestionElement.classList.add('processing');
        const originalButtonsHtml = this.suggestionElement.querySelector('.suggestion-actions').innerHTML;
        this.suggestionElement.querySelector('.suggestion-actions').innerHTML = 
            '<span class="processing-indicator"><i class="fas fa-spinner fa-spin"></i> Processing...</span>';
        
        // Make API call to update project context
        fetch(`/api/projects/${encodeURIComponent(projectName)}/context/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: actionType,
                content: content
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to update project context: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - show confirmation and refresh project data
            this.showToast(`Successfully updated project context!`, 'success');
            
            // If the current project matches, refresh it
            if (this.currentProject === projectName) {
                this.projectData = data.updated_context; 
                this.renderProjectData();
            }
            
            // Hide the suggestion
            setTimeout(() => {
                this.hideSuggestion();
            }, 500);
        })
        .catch(error => {
            console.error('Error updating project context:', error);
            
            // Restore buttons and show error
            this.suggestionElement.classList.remove('processing');
            this.suggestionElement.querySelector('.suggestion-actions').innerHTML = originalButtonsHtml;
            
            // Show error toast
            this.showToast(`Failed to update project: ${error.message}`, 'error');
        });
    }
    
    /**
     * Show a toast notification
     * @param {string} message - Message to display
     * @param {string} type - Type of toast (success, error, info)
     */
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `project-memory-toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            </div>
            <div class="toast-message">${message}</div>
        `;
        
        // Add to DOM
        document.body.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.classList.add('visible');
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    /**
     * Toggle the completion status of a task
     * @param {number} taskIndex - Index of the task
     */
    toggleTaskStatus(taskIndex) {
        if (!this.currentProject) return;
        
        // Send API request to toggle task status
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/tasks/${taskIndex}/toggle`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to toggle task status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - refresh project data
            if (data.success && data.tasks) {
                this.projectData.task_queue = data.tasks;
                this.renderProjectData();
                this.showToast('Task status updated!', 'success');
            }
        })
        .catch(error => {
            console.error('Error updating task status:', error);
            this.showToast(`Failed to update task: ${error.message}`, 'error');
        });
    }
    
    /**
     * Show dialog for setting task priority
     * @param {number} taskIndex - Index of the task
     */
    showTaskPriorityDialog(taskIndex) {
        const task = this.projectData.task_queue[taskIndex];
        const taskText = typeof task === 'object' ? task.text : task;
        
        // Create modal element
        const modal = this.createDialog('Set Task Priority', `
            <p>Set priority for task: <strong>${taskText}</strong></p>
            <div class="dialog-priority-options">
                <button class="priority-option high" data-priority="High">
                    🔥 High
                </button>
                <button class="priority-option medium" data-priority="Medium">
                    🟡 Medium
                </button>
                <button class="priority-option low" data-priority="Low">
                    ⚪️ Low
                </button>
            </div>
        `);
        
        // Add event listeners to priority buttons
        const priorityButtons = modal.querySelectorAll('.priority-option');
        priorityButtons.forEach(button => {
            button.addEventListener('click', () => {
                const priority = button.getAttribute('data-priority');
                this.updateTaskPriority(taskIndex, priority);
                this.closeDialog();
            });
        });
    }
    
    /**
     * Show dialog for setting task deadline
     * @param {number} taskIndex - Index of the task
     */
    showTaskDeadlineDialog(taskIndex) {
        const task = this.projectData.task_queue[taskIndex];
        const taskText = typeof task === 'object' ? task.text : task;
        const currentDeadline = (typeof task === 'object' && task.deadline) 
            ? task.deadline.substr(0, 10) // Get YYYY-MM-DD part
            : new Date().toISOString().substr(0, 10); // Today's date
        
        // Create modal element
        const modal = this.createDialog('Set Task Deadline', `
            <p>Set deadline for task: <strong>${taskText}</strong></p>
            <div class="dialog-form">
                <input type="date" id="task-deadline-input" value="${currentDeadline}">
                <div class="dialog-buttons">
                    <button id="set-deadline-button" class="dialog-primary-button">Save Deadline</button>
                    <button id="remove-deadline-button" class="dialog-secondary-button">Remove Deadline</button>
                </div>
            </div>
        `);
        
        // Add event listeners
        document.getElementById('set-deadline-button').addEventListener('click', () => {
            const deadline = document.getElementById('task-deadline-input').value;
            if (deadline) {
                this.updateTaskDeadline(taskIndex, deadline);
            }
            this.closeDialog();
        });
        
        document.getElementById('remove-deadline-button').addEventListener('click', () => {
            this.updateTaskDeadline(taskIndex, null);
            this.closeDialog();
        });
    }
    
    /**
     * Show dialog for adding task dependency
     * @param {number} taskIndex - Index of the task
     */
    showTaskDependencyDialog(taskIndex) {
        const task = this.projectData.task_queue[taskIndex];
        const taskText = typeof task === 'object' ? task.text : task;
        const currentDependencies = (typeof task === 'object' && task.dependencies) 
            ? task.dependencies 
            : [];
            
        // Get other tasks that could be dependencies
        const otherTasks = this.projectData.task_queue
            .map((t, i) => ({ index: i, text: typeof t === 'object' ? t.text : t }))
            .filter((t, i) => i !== taskIndex); // Filter out the current task
        
        // Create modal element
        const modal = this.createDialog('Add Task Dependency', `
            <p>Add dependency for task: <strong>${taskText}</strong></p>
            <div class="dialog-form">
                <select id="dependency-select">
                    <option value="">Select a task...</option>
                    ${otherTasks.map(t => `<option value="${t.text}">${t.text}</option>`).join('')}
                </select>
                <button id="add-dependency-button" class="dialog-primary-button">Add Dependency</button>
            </div>
            
            <div class="current-dependencies">
                <h4>Current Dependencies:</h4>
                ${currentDependencies.length > 0 ? 
                    `<ul>${currentDependencies.map(dep => 
                        `<li>${dep} <button class="remove-dependency" data-dependency="${dep}">×</button></li>`
                    ).join('')}</ul>` : 
                    '<p>No dependencies set</p>'
                }
            </div>
        `);
        
        // Add event listener for adding dependency
        document.getElementById('add-dependency-button').addEventListener('click', () => {
            const select = document.getElementById('dependency-select');
            const dependency = select.value;
            
            if (dependency) {
                this.addTaskDependency(taskIndex, dependency);
                this.closeDialog();
            } else {
                this.showToast('Please select a task', 'error');
            }
        });
        
        // Add event listeners for removing dependencies
        const removeButtons = modal.querySelectorAll('.remove-dependency');
        removeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const dependency = button.getAttribute('data-dependency');
                this.removeTaskDependency(taskIndex, dependency);
                this.closeDialog();
            });
        });
    }
    
    /**
     * Update task priority
     * @param {number} taskIndex - Index of the task
     * @param {string} priority - Priority level (High, Medium, Low)
     */
    updateTaskPriority(taskIndex, priority) {
        if (!this.currentProject) return;
        
        // Send API request to update task priority
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/context/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'update_task_priority',
                task_index: taskIndex,
                priority: priority
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to update task priority: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - refresh project data
            if (data.success && data.updated_context) {
                this.projectData = data.updated_context;
                this.renderProjectData();
                this.showToast(`Task priority set to ${priority}!`, 'success');
            }
        })
        .catch(error => {
            console.error('Error updating task priority:', error);
            this.showToast(`Failed to update task: ${error.message}`, 'error');
        });
    }
    
    /**
     * Update task deadline
     * @param {number} taskIndex - Index of the task
     * @param {string} deadline - Deadline date (YYYY-MM-DD) or null to remove
     */
    updateTaskDeadline(taskIndex, deadline) {
        if (!this.currentProject) return;
        
        // Send API request to update task deadline
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/context/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'set_task_deadline',
                task_index: taskIndex,
                deadline: deadline
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to update task deadline: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - refresh project data
            if (data.success && data.updated_context) {
                this.projectData = data.updated_context;
                this.renderProjectData();
                
                const message = deadline ? 
                    `Task deadline set to ${new Date(deadline).toLocaleDateString()}!` : 
                    'Task deadline removed!';
                    
                this.showToast(message, 'success');
            }
        })
        .catch(error => {
            console.error('Error updating task deadline:', error);
            this.showToast(`Failed to update task: ${error.message}`, 'error');
        });
    }
    
    /**
     * Add task dependency
     * @param {number} taskIndex - Index of the task
     * @param {string} dependency - Name of the task this depends on
     */
    addTaskDependency(taskIndex, dependency) {
        if (!this.currentProject) return;
        
        // Send API request to add task dependency
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/context/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action_type: 'add_task_dependency',
                task_index: taskIndex,
                dependency: dependency
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to add task dependency: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - refresh project data
            if (data.success && data.updated_context) {
                this.projectData = data.updated_context;
                this.renderProjectData();
                this.showToast(`Dependency added: ${dependency}`, 'success');
            }
        })
        .catch(error => {
            console.error('Error adding task dependency:', error);
            this.showToast(`Failed to update task: ${error.message}`, 'error');
        });
    }
    
    /**
     * Remove task dependency
     * @param {number} taskIndex - Index of the task
     * @param {string} dependency - Name of the dependency to remove
     */
    removeTaskDependency(taskIndex, dependency) {
        if (!this.currentProject || !this.projectData) return;
        
        // Get the current task
        const task = this.projectData.task_queue[taskIndex];
        if (!task || typeof task !== 'object' || !task.dependencies) {
            this.showToast('Task does not have dependencies to remove', 'error');
            return;
        }
        
        // Filter out the dependency to remove
        const updatedDependencies = task.dependencies.filter(dep => dep !== dependency);
        
        // Update the task with API call
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/tasks/${taskIndex}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dependencies: updatedDependencies
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to remove dependency: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Success - refresh project data
            if (data.success && data.tasks) {
                this.projectData.task_queue = data.tasks;
                this.renderProjectData();
                this.showToast(`Dependency removed: ${dependency}`, 'success');
            }
        })
        .catch(error => {
            console.error('Error removing dependency:', error);
            this.showToast(`Failed to update task: ${error.message}`, 'error');
        });
    }
    
    /**
     * Create a modal dialog
     * @param {string} title - Dialog title
     * @param {string} content - Dialog HTML content
     * @returns {HTMLElement} - The dialog element
     */
    createDialog(title, content) {
        // Remove any existing dialogs
        this.closeDialog();
        
        // Create overlay and dialog
        const overlay = document.createElement('div');
        overlay.className = 'project-memory-dialog-overlay';
        
        const dialog = document.createElement('div');
        dialog.className = 'project-memory-dialog';
        dialog.innerHTML = `
            <div class="dialog-header">
                <div class="dialog-title">${title}</div>
                <button class="dialog-close-button">&times;</button>
            </div>
            <div class="dialog-content">
                ${content}
            </div>
        `;
        
        // Add close button event listener
        dialog.querySelector('.dialog-close-button').addEventListener('click', () => {
            this.closeDialog();
        });
        
        // Add to DOM
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        // Add visible class after a short delay for animation
        setTimeout(() => {
            overlay.classList.add('visible');
        }, 10);
        
        // Save reference to current dialog
        this.currentDialog = overlay;
        
        return dialog;
    }
    
    /**
     * Close the current dialog
     */
    closeDialog() {
        if (this.currentDialog) {
            this.currentDialog.classList.remove('visible');
            
            // Remove from DOM after animation completes
            setTimeout(() => {
                if (this.currentDialog && this.currentDialog.parentNode) {
                    this.currentDialog.parentNode.removeChild(this.currentDialog);
                }
                this.currentDialog = null;
            }, 300);
        }
    }
    
    /**
     * Render task suggestions in the suggestion container
     */
    renderTaskSuggestions() {
        const container = document.getElementById('task-suggestion-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // If no suggestions available, don't render anything
        if (!this.taskSuggestions || this.taskSuggestions.length === 0) {
            return;
        }
        
        // Get the top suggestion
        const topSuggestion = this.taskSuggestions[0];
        const task = topSuggestion.task;
        const reasons = topSuggestion.reasons || [];
        const isBlocked = topSuggestion.is_blocked;
        const blockingTasks = topSuggestion.blocking_tasks || [];
        
        // Get task info
        const taskText = typeof task === 'object' ? (task.text || task.task) : task;
        const taskIndex = this.findTaskIndex(taskText);
        
        // Generate HTML
        let html = `
            <div class="suggestion-card ${isBlocked ? 'blocked' : ''}">
                <div class="suggestion-header">
                    <div class="suggestion-title">
                        <i class="fas fa-lightbulb"></i> Minerva Suggests:
                    </div>
                    <button class="suggestion-refresh" onclick="projectMemoryViewer.loadTaskSuggestions()">
                        <i class="fas fa-sync"></i>
                    </button>
                </div>
                <div class="suggestion-content">
                    <div class="suggested-task">${taskText}</div>
        `;
        
        // Add reasoning
        if (reasons.length > 0) {
            html += `
                <div class="suggestion-reasoning">
                    <span class="reason-label">Why:</span> ${reasons.join(', ')}
                </div>
            `;
        }
        
        // Add AI-generated suggestion text if available
        if (this.suggestionText) {
            html += `
                <div class="suggestion-explanation">
                    ${this.suggestionText}
                </div>
            `;
        }
        
        // Add blocking info if relevant
        if (isBlocked && blockingTasks.length > 0) {
            html += `
                <div class="suggestion-blocked-by">
                    <span class="blocked-label"><i class="fas fa-ban"></i> Blocked by:</span>
                    <ul class="blocked-tasks-list">
                        ${blockingTasks.slice(0, 3).map(bt => `<li>${bt}</li>`).join('')}
                        ${blockingTasks.length > 3 ? 
                          `<li>...and ${blockingTasks.length - 3} more</li>` : ''}
                    </ul>
                </div>
            `;
        }
        
        // Add action buttons
        html += `
                </div>
                <div class="suggestion-actions">
        `;
        
        // Only show Accept button if not blocked and task index is found
        if (!isBlocked && taskIndex !== -1) {
            html += `
                    <button class="suggestion-action-button accept" 
                            onclick="projectMemoryViewer.markTaskActive(${taskIndex})">
                        <i class="fas fa-check"></i> Accept & Start
                    </button>
            `;
        }
        
        // Show Edit button for all suggestions
        if (taskIndex !== -1) {
            html += `
                    <button class="suggestion-action-button edit" 
                            onclick="projectMemoryViewer.showTaskPriorityDialog(${taskIndex})">
                        <i class="fas fa-edit"></i> Reprioritize
                    </button>
            `;
        }
        
        // Show "View All" button if we have multiple suggestions
        if (this.taskSuggestions.length > 1) {
            html += `
                    <button class="suggestion-action-button view-all" 
                            onclick="projectMemoryViewer.showAllSuggestions()">
                        <i class="fas fa-list"></i> View All Suggestions
                    </button>
            `;
        }
        
        html += `
                </div>
            </div>
        `;
        
        // Render to container
        container.innerHTML = html;
    }
    
    /**
     * Find the index of a task in the task queue by its text
     * @param {string} taskText - The text of the task to find
     * @returns {number} - The index of the task, or -1 if not found
     */
    findTaskIndex(taskText) {
        if (!this.projectData || !this.projectData.task_queue) return -1;
        
        for (let i = 0; i < this.projectData.task_queue.length; i++) {
            const task = this.projectData.task_queue[i];
            const text = typeof task === 'object' ? (task.text || task.task) : task;
            
            if (text === taskText) {
                return i;
            }
        }
        
        return -1;
    }
    
    /**
     * Mark a task as the active one
     * @param {number} taskIndex - Index of the task to mark as active
     */
    markTaskActive(taskIndex) {
        if (!this.currentProject) return;
        
        fetch(`/api/projects/${encodeURIComponent(this.currentProject)}/tasks/${taskIndex}/mark_active`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to mark task as active: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update the task queue with the new active task
                this.projectData.task_queue = data.tasks;
                this.renderProjectData();
                
                // Show success message
                const taskText = typeof this.projectData.task_queue[taskIndex] === 'object' 
                    ? this.projectData.task_queue[taskIndex].text 
                    : this.projectData.task_queue[taskIndex];
                    
                this.showToast(`Now working on: ${taskText}`, 'success');
            }
        })
        .catch(error => {
            console.error('Error marking task as active:', error);
            this.showToast(`Failed to mark task as active: ${error.message}`, 'error');
        });
    }
    
    /**
     * Show dialog with all task suggestions
     */
    showAllSuggestions() {
        if (!this.taskSuggestions || this.taskSuggestions.length === 0) return;
        
        // Create content for dialog
        let content = `
            <div class="all-suggestions-container">
                <p>Here are all task suggestions ranked by priority:</p>
                <div class="suggestions-list">
        `;
        
        // Add each suggestion
        this.taskSuggestions.forEach((suggestion, index) => {
            const task = suggestion.task;
            const reasons = suggestion.reasons || [];
            const taskText = typeof task === 'object' ? (task.text || task.task) : task;
            const taskIndex = this.findTaskIndex(taskText);
            const isBlocked = suggestion.is_blocked;
            
            content += `
                <div class="suggestion-list-item ${isBlocked ? 'blocked' : ''}">
                    <div class="suggestion-list-rank">#${index + 1}</div>
                    <div class="suggestion-list-content">
                        <div class="suggestion-list-task">${taskText}</div>
                        <div class="suggestion-list-reason">${reasons.join(', ')}</div>
                    </div>
                    <div class="suggestion-list-actions">
            `;
            
            if (!isBlocked && taskIndex !== -1) {
                content += `
                        <button onclick="projectMemoryViewer.markTaskActive(${taskIndex}); projectMemoryViewer.closeDialog();">
                            <i class="fas fa-check"></i>
                        </button>
                `;
            }
            
            if (taskIndex !== -1) {
                content += `
                        <button onclick="projectMemoryViewer.showTaskPriorityDialog(${taskIndex}); projectMemoryViewer.closeDialog();">
                            <i class="fas fa-edit"></i>
                        </button>
                `;
            }
            
            content += `
                    </div>
                </div>
            `;
        });
        
        content += `
                </div>
            </div>
        `;
        
        // Create modal dialog
        this.createDialog('All Task Suggestions', content);
    }
}

// Initialize on load
const projectMemoryViewer = new ProjectMemoryViewer();

// Export the instance
window.projectMemoryViewer = projectMemoryViewer;
