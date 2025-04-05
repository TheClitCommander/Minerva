/**
 * Project Context Debugger
 * A simple UI to toggle and debug project context integration
 */

class ProjectContextDebugger {
    constructor() {
        this.initialized = false;
        this.container = null;
        this.debugPanelVisible = false;
    }

    /**
     * Initialize the debugger
     */
    init() {
        if (this.initialized) return;
        
        this.createDebugPanel();
        this.setupEventListeners();
        
        this.initialized = true;
        console.log('Project Context Debugger initialized');
    }
    
    /**
     * Create the debug panel UI
     */
    createDebugPanel() {
        // Create container
        this.container = document.createElement('div');
        this.container.className = 'project-context-debug-panel';
        this.container.innerHTML = `
            <div class="project-debug-header">
                <h3>Project Context Controls</h3>
                <button class="close-debug-panel">×</button>
            </div>
            <div class="project-debug-controls">
                <div class="control-group">
                    <label for="project-context-enabled">
                        <input type="checkbox" id="project-context-enabled" ${window.projectContextProcessor?.settings?.enabled ? 'checked' : ''}>
                        Enable Project Context
                    </label>
                    <p class="control-description">
                        When enabled, AI responses will include relevant project context
                    </p>
                </div>
                <div class="control-group">
                    <label for="project-context-debug">
                        <input type="checkbox" id="project-context-debug" ${window.projectContextProcessor?.settings?.debugMode ? 'checked' : ''}>
                        Debug Mode
                    </label>
                    <p class="control-description">
                        When enabled, detailed project information will be shown in context indicators
                    </p>
                </div>
                <div class="project-debug-status">
                    <p>Status: <span id="project-context-status">${this.getStatusText()}</span></p>
                </div>
            </div>
        `;
        
        // Add toggle button
        const toggleButton = document.createElement('button');
        toggleButton.className = 'project-context-debug-toggle';
        toggleButton.textContent = '🔧 Context';
        toggleButton.title = 'Toggle Project Context Debug Panel';
        
        // Add to document
        document.body.appendChild(toggleButton);
        document.body.appendChild(this.container);
        
        // Set initial visibility
        this.container.style.display = 'none';
        this.debugPanelVisible = false;
    }
    
    /**
     * Setup event listeners for the debug panel
     */
    setupEventListeners() {
        // Find the toggle button
        const toggleButton = document.querySelector('.project-context-debug-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => this.toggleDebugPanel());
        }
        
        // Close button
        const closeButton = this.container.querySelector('.close-debug-panel');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.toggleDebugPanel(false));
        }
        
        // Enable/disable context
        const enableToggle = this.container.querySelector('#project-context-enabled');
        if (enableToggle && window.projectContextProcessor) {
            enableToggle.addEventListener('change', (e) => {
                window.projectContextProcessor.setEnabled(e.target.checked);
                this.updateStatus();
            });
        }
        
        // Debug mode toggle
        const debugToggle = this.container.querySelector('#project-context-debug');
        if (debugToggle && window.projectContextProcessor) {
            debugToggle.addEventListener('change', (e) => {
                window.projectContextProcessor.setDebugMode(e.target.checked);
                this.updateStatus();
            });
        }
    }
    
    /**
     * Toggle the debug panel visibility
     * @param {Boolean} [show] - Force show/hide, or toggle if not provided
     */
    toggleDebugPanel(show) {
        if (typeof show === 'boolean') {
            this.debugPanelVisible = show;
        } else {
            this.debugPanelVisible = !this.debugPanelVisible;
        }
        
        this.container.style.display = this.debugPanelVisible ? 'block' : 'none';
        this.updateStatus();
    }
    
    /**
     * Update status text and controls
     */
    updateStatus() {
        const statusElement = this.container.querySelector('#project-context-status');
        if (statusElement) {
            statusElement.textContent = this.getStatusText();
        }
        
        // Update checkboxes to match current settings
        if (window.projectContextProcessor) {
            const enabledCheckbox = this.container.querySelector('#project-context-enabled');
            if (enabledCheckbox) {
                enabledCheckbox.checked = window.projectContextProcessor.settings.enabled;
            }
            
            const debugCheckbox = this.container.querySelector('#project-context-debug');
            if (debugCheckbox) {
                debugCheckbox.checked = window.projectContextProcessor.settings.debugMode;
            }
        }
    }
    
    /**
     * Get status text based on current settings
     * @returns {String} Status text
     */
    getStatusText() {
        if (!window.projectContextProcessor) {
            return 'Project Context Processor not available';
        }
        
        const { enabled, debugMode } = window.projectContextProcessor.settings;
        
        if (enabled) {
            return debugMode ? 
                'Active with debug information' : 
                'Active (normal mode)';
        } else {
            return 'Disabled';
        }
    }
}

// Create global instance
window.projectContextDebugger = new ProjectContextDebugger();

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.projectContextDebugger) {
        setTimeout(() => {
            window.projectContextDebugger.init();
        }, 1000); // Short delay to ensure other components are loaded
    }
});
