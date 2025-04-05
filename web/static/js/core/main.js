/**
 * Minerva AI - Main JavaScript
 * 
 * This file contains common JavaScript functionality used across the Minerva web interface.
 */

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Minerva AI web interface initialized');
    
    // Setup for theme toggling
    setupThemeToggle();
    
    // Initialize tooltips
    initTooltips();
    
    // Setup event listeners
    setupEventListeners();
});

/**
 * Set up theme toggle functionality
 */
function setupThemeToggle() {
    const themeSelect = document.getElementById('theme-select');
    
    if (themeSelect) {
        // First, check for saved preference
        const savedTheme = localStorage.getItem('minerva-theme');
        
        if (savedTheme) {
            themeSelect.value = savedTheme;
            applyTheme(savedTheme);
        } else {
            // No saved preference, check for system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (prefersDark) {
                themeSelect.value = 'dark';
                applyTheme('dark');
            }
        }
        
        // Listen for changes
        themeSelect.addEventListener('change', function() {
            const theme = this.value;
            localStorage.setItem('minerva-theme', theme);
            applyTheme(theme);
        });
    }
}

/**
 * Apply the selected theme
 * @param {string} theme - The theme to apply ('light', 'dark', or 'system')
 */
function applyTheme(theme) {
    const body = document.body;
    
    // Remove existing theme classes
    body.classList.remove('dark-mode');
    
    if (theme === 'dark') {
        body.classList.add('dark-mode');
    } else if (theme === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            body.classList.add('dark-mode');
        }
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Setup global event listeners
 */
function setupEventListeners() {
    // Listen for system dark mode changes if using system theme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        const savedTheme = localStorage.getItem('minerva-theme');
        if (savedTheme === 'system') {
            applyTheme('system');
        }
    });
    
    // Setup API key display toggle listeners
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
}

/**
 * Create a notification toast
 * 
 * @param {string} message - The notification message
 * @param {string} type - The notification type ('success', 'error', 'warning', 'info')
 * @param {number} duration - Duration in milliseconds before auto-hiding (default: 3000ms)
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create a unique ID for the toast
    const toastId = 'toast-' + Date.now();
    
    // Map type to Bootstrap color class
    const typeClassMap = {
        'success': 'bg-success text-white',
        'error': 'bg-danger text-white',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const typeIconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    
    const typeClass = typeClassMap[type] || typeClassMap.info;
    const typeIcon = typeIconMap[type] || typeIconMap.info;
    
    // Create toast HTML
    const toastHtml = `
        <div id="${toastId}" class="toast ${typeClass}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="fas ${typeIcon} me-2"></i>
                <strong class="me-auto">Minerva AI</strong>
                <small>Just now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add the toast to the container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });
    
    toast.show();
    
    // Remove the toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        this.remove();
    });
}
