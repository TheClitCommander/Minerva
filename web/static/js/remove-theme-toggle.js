/**
 * Aggressive removal of theme toggle buttons
 * This script removes any theme toggle elements from the DOM
 * and prevents them from being recreated
 */

// Execute immediately when script loads
(function() {
    // First removal pass - runs immediately
    removeAllThemeToggles();
    
    // Second removal on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        removeAllThemeToggles();
        
        // Set up an observer to catch any dynamically added toggles
        setupToggleObserver();
        
        // Also run periodically to catch any toggles added through other means
        setInterval(removeAllThemeToggles, 1000);
    });
    
    // Function to remove all theme toggles
    function removeAllThemeToggles() {
        console.log('Running aggressive theme toggle removal');
        
        // By ID
        const toggleById = document.getElementById('theme-toggle');
        if (toggleById) {
            console.log('Found theme toggle by ID - removing');
            if (toggleById.parentNode) toggleById.parentNode.removeChild(toggleById);
        }
        
        // By class
        const toggleSelectors = [
            '.theme-toggle-btn',
            '.floating-theme-toggle',
            '.theme-toggle-container',
            'button[aria-label="Toggle theme"]',
            'button[title="Toggle light/dark mode"]'
        ];
        
        toggleSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                console.log('Found theme toggle by selector:', selector);
                if (element.parentNode) element.parentNode.removeChild(element);
            });
        });
        
        // Target the specific one in the DOM
        document.querySelectorAll('button.theme-toggle-btn.floating-theme-toggle').forEach(el => {
            console.log('Removing specific floating theme toggle');
            if (el.parentNode) el.parentNode.removeChild(el);
        });
    }
    
    // Set up a mutation observer to catch dynamically added toggles
    function setupToggleObserver() {
        const observer = new MutationObserver(function(mutations) {
            let shouldRemove = false;
            
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length) {
                    mutation.addedNodes.forEach(node => {
                        // Check if the added node is a theme toggle or contains one
                        if (node.id === 'theme-toggle' || 
                            (node.classList && node.classList.contains('theme-toggle-btn'))) {
                            shouldRemove = true;
                        } else if (node.querySelector) {
                            // Check if it contains any theme toggles
                            const hasToggle = node.querySelector('#theme-toggle, .theme-toggle-btn, .floating-theme-toggle');
                            if (hasToggle) shouldRemove = true;
                        }
                    });
                }
            });
            
            if (shouldRemove) {
                console.log('Observer detected new theme toggle - removing');
                removeAllThemeToggles();
            }
        });
        
        // Observe the entire document body
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    }
})();
