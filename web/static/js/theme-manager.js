/**
 * Minerva Theme Manager
 * Handles theme switching between light and dark modes
 */

const ThemeManager = (function() {
    // Theme constants
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';
    const STORAGE_KEY = 'minerva_theme_preference';
    
    // DOM Elements that will be populated when initialized
    let themeToggleButton = null;
    
    /**
     * Initialize the theme system
     */
    function initialize() {
        console.log('🎨 ThemeManager: Initializing theme system');
        
        // First load the saved theme or detect user preference
        loadSavedTheme();
        
        // Remove any existing theme toggle buttons
        const existingToggle = document.getElementById('theme-toggle');
        if (existingToggle && existingToggle.parentNode) {
            console.log('🎨 ThemeManager: Removing theme toggle button');
            existingToggle.parentNode.removeChild(existingToggle);
        }
        
        // Find and remove any floating theme toggles
        document.querySelectorAll('.floating-theme-toggle').forEach(el => {
            if (el.parentNode) {
                el.parentNode.removeChild(el);
            }
        });
        
        // Theme toggle creation disabled as per user request
        
        // Listen for system preference changes
        if (window.matchMedia) {
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
            try {
                // For modern browsers
                prefersDarkScheme.addEventListener('change', (e) => {
                    console.log('🎨 ThemeManager: System preference changed to:', e.matches ? 'dark' : 'light');
                    // Only update if user hasn't manually set a preference
                    if (!localStorage.getItem(STORAGE_KEY)) {
                        setTheme(e.matches ? THEME_DARK : THEME_LIGHT, false);
                    }
                });
            } catch (error) {
                // Fallback for older browsers
                prefersDarkScheme.addListener((e) => {
                    console.log('🎨 ThemeManager: System preference changed (legacy) to:', e.matches ? 'dark' : 'light');
                    if (!localStorage.getItem(STORAGE_KEY)) {
                        setTheme(e.matches ? THEME_DARK : THEME_LIGHT, false);
                    }
                });
            }
        }
        
        // Apply theme once more to ensure it's properly applied
        const currentTheme = document.documentElement.getAttribute('data-theme') || THEME_DARK;
        console.log('🎨 ThemeManager: Final theme initialization with:', currentTheme);
        setTheme(currentTheme, false);
    }
    
    /**
     * Load saved theme from localStorage or detect from system
     */
    function loadSavedTheme() {
        const savedTheme = localStorage.getItem(STORAGE_KEY);
        
        if (savedTheme) {
            // User has a saved preference
            setTheme(savedTheme);
        } else if (window.matchMedia) {
            // Detect system preference if available
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
            setTheme(prefersDarkScheme.matches ? THEME_DARK : THEME_LIGHT, false);
        } else {
            // Default to dark theme
            setTheme(THEME_DARK, false);
        }
    }
    
    /**
     * Create the theme toggle button and add it to the DOM
     */
    function createThemeToggle() {
        console.log('Theme toggle creation has been disabled as per user request');
        return null; // Do nothing - toggle is disabled
    }
    
    /**
     * Update the theme toggle button icon based on current theme
     */
    function updateToggleIcon() {
        if (!themeToggleButton) return;
        
        const currentTheme = document.documentElement.getAttribute('data-theme') || THEME_DARK;
        
        if (currentTheme === THEME_LIGHT) {
            // Show moon icon for switching to dark mode
            themeToggleButton.innerHTML = '<i class="fas fa-moon"></i>';
        } else {
            // Show sun icon for switching to light mode
            themeToggleButton.innerHTML = '<i class="fas fa-sun"></i>';
        }
    }
    
    /**
     * Refresh the chat interface theme styling
     * This ensures all chat elements properly reflect the current theme
     * @param {string} theme - The current theme ('light' or 'dark')
     */
    function refreshChatTheme(theme) {
        try {
            console.log(`🎨 ThemeManager: Refreshing chat theme to ${theme}`);
            
            if (!theme) {
                theme = document.documentElement.getAttribute('data-theme') || THEME_DARK;
                console.log(`🎨 ThemeManager: No theme specified, using current: ${theme}`);
            }
            
            // Select common element patterns in Minerva UI
            const selectors = [
                // Main containers
                '#chat-interface', '#chat-messages', '#chat-input-container',
                '#conversation-container', '#sidebar', '#minerva-dashboard',
                '#think-tank-interface', '#minerva-main', '#minerva-app',
                '#project-interface', '#concept-map', '#orb-interface',
                '.minerva-panel', '.minerva-container', '.minerva-card',
                
                // Chat elements
                '.message-container', '.user-message', '.ai-message',
                '.system-message', '.message', '.conversation-item',
                '.chat-input', '.chat-control', '.chat-header',
                
                // Common UI elements
                '.header', '.footer', '.navbar', '.sidebar',
                '.card', '.panel', '.dialog', '.modal'
            ];
            
            // Get all elements matching our selectors
            const elementsToTheme = selectors.flatMap(selector => {
                return Array.from(document.querySelectorAll(selector) || []);
            }).filter(Boolean); // Remove null/undefined
            
            // Apply theme class to each element
            elementsToTheme.forEach(element => {
                if (element) {
                    element.classList.remove('theme-dark', 'theme-light');
                    element.classList.add(`theme-${theme}`);
                    
                    // Additionally ensure the element has a data-theme attribute
                    element.setAttribute('data-theme', theme);
                }
            });
            
            // Apply to dynamic content containers that might not have specific class
            const contentContainers = document.querySelectorAll('main, section, [role="main"]');
            contentContainers.forEach(container => {
                if (container) {
                    container.setAttribute('data-theme', theme);
                }
            });
            
            // Update any theme-specific images (if they follow our naming convention)
            const themeImages = document.querySelectorAll('img[src*="-light."], img[src*="-dark."]');
            themeImages.forEach(img => {
                const currentSrc = img.getAttribute('src');
                // Replace the theme in the filename
                const newSrc = currentSrc.replace(
                    theme === THEME_LIGHT ? '-dark.' : '-light.', 
                    `-${theme}.`
                );
                if (newSrc !== currentSrc) {
                    img.setAttribute('src', newSrc);
                }
            });
            
            console.log(`Refreshed chat theme to: ${theme} (${elementsToTheme.length} elements updated)`);
        } catch (error) {
            console.error('Error refreshing chat theme:', error);
        }
    }
    
    /**
     * Set up event listeners for the theme toggle button
     */
    function setupEventListeners() {
        if (!themeToggleButton) return;
        
        themeToggleButton.addEventListener('click', toggleTheme);
    }
    
    /**
     * Toggle between light and dark themes
     */
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || THEME_DARK;
        const newTheme = currentTheme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        
        setTheme(newTheme, true);
    }
    
    /**
     * Set the theme to light or dark
     * @param {string} theme - 'light' or 'dark'
     * @param {boolean} savePreference - Whether to save this preference
     */
    function setTheme(theme, savePreference = true) {
        console.log(`🎨 ThemeManager: Applying theme: ${theme}`);
        
        // Validate theme value
        if (theme !== THEME_DARK && theme !== THEME_LIGHT) {
            console.warn(`🎨 ThemeManager: Invalid theme value: ${theme}, defaulting to ${THEME_DARK}`);
            theme = THEME_DARK;
        }
        
        // Add transition class for smooth change
        document.body.classList.add('theme-transition');
        
        // Set the theme attribute on html element (root element)
        document.documentElement.setAttribute('data-theme', theme);
        document.body.setAttribute('data-theme', theme);
        
        // Add or remove the dark-mode class on the body (for legacy support)
        if (theme === THEME_DARK) {
            document.body.classList.add('dark-mode');
            document.documentElement.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
            document.documentElement.classList.remove('dark-mode');
        }
        
        // Also set a body class for components that might use it
        document.body.classList.remove('theme-dark', 'theme-light');
        document.body.classList.add(`theme-${theme}`);
        
        // Add a class to specific containers that might need direct styling
        // Update key major containers
        const themeContainers = [
            document.getElementById('chat-interface'),
            document.getElementById('main-container'),
            document.getElementById('minerva-dashboard'),
            document.getElementById('app-container'),
            document.getElementById('minerva-app'),
            document.getElementById('minerva-main'),
            document.querySelector('main'),
            document.querySelector('.app-container')
        ];
        
        themeContainers.forEach(container => {
            if (container) {
                container.classList.remove('theme-dark', 'theme-light');
                container.classList.add(`theme-${theme}`);
                container.setAttribute('data-theme', theme);
            }
        });
        
        // Save the theme preference if requested
        if (savePreference) {
            localStorage.setItem(STORAGE_KEY, theme);
            console.log(`🎨 ThemeManager: Saved theme preference: ${theme}`);
        }
        
        // Update the toggle button icon
        updateToggleIcon();
        
        // Force refresh any chat interface elements
        refreshChatTheme(theme);
        
        // Remove transition class after animation completes
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 400);
        
        // Dispatch event for other components
        window.dispatchEvent(new CustomEvent('minerva-theme-changed', {
            detail: { theme: theme }
        }));
        
        // Remove transition class after transition completes
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 500);
        
        // Dispatch event for other components to react to theme change
        const event = new CustomEvent('minerva-theme-changed', { detail: { theme } });
        document.dispatchEvent(event);
        
        console.log(`🎨 ThemeManager: Theme application complete: ${theme}`);
        
        // Return the applied theme
        return theme;
    }
    
    // Public API
    return {
        initialize,
        toggleTheme,
        setTheme,
        getCurrentTheme: () => document.documentElement.getAttribute('data-theme') || THEME_DARK
    };
})();

// Initialize the theme manager both on DOMContentLoaded and immediately
// This ensures it works regardless of when the script is loaded
document.addEventListener('DOMContentLoaded', ThemeManager.initialize);

// Also initialize immediately if the document is already loaded
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    console.log('Document already loaded, initializing theme manager now');
    ThemeManager.initialize();
}
