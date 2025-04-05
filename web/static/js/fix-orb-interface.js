/**
 * Orb Interface Helper Functions
 * For fixing the section display issues in Minerva
 */

// Ensure these functions are available globally
window.ensureViewExists = function(viewId, title) {
    const contentDisplay = document.getElementById('content-display');
    if (!contentDisplay) {
        console.error('Content display element not found');
        return;
    }
    
    let viewElement = document.getElementById(viewId);
    if (!viewElement) {
        console.log(`Creating view container for ${viewId}`);
        viewElement = document.createElement('div');
        viewElement.id = viewId;
        viewElement.className = viewId;
        
        // Add default content
        viewElement.innerHTML = `
            <h1>${title || viewId}</h1>
            <p>Welcome to the ${title || viewId} section.</p>
            <div class="content-container"></div>
        `;
        
        // Add it to the content display
        contentDisplay.appendChild(viewElement);
        
        // Start hidden
        viewElement.classList.add('hidden');
    }
    
    return viewElement;
};

// Create the conversations view
window.createConversationsView = function() {
    const contentDisplay = document.getElementById('content-display');
    if (!contentDisplay) {
        console.error('Content display element not found');
        return;
    }
    
    // Create the view
    const conversationsView = document.createElement('div');
    conversationsView.id = 'conversations-view';
    conversationsView.className = 'conversations-view';
    
    // Add default structure
    conversationsView.innerHTML = `
        <h1>💬 Conversations & Logs</h1>
        <p>All your conversations are automatically saved here. You can rename, archive, or convert them to projects.</p>
        
        <div class="control-panel">
            <div class="search-container">
                <input type="text" id="conversation-search" placeholder="Search conversations...">
                <button id="search-button">Search</button>
            </div>
            <div class="filter-container">
                <select id="project-filter">
                    <option value="all">All Projects</option>
                    <option value="none">Unassigned</option>
                </select>
            </div>
            <div class="sort-container">
                <select id="sort-options">
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                    <option value="az">A-Z</option>
                    <option value="za">Z-A</option>
                </select>
            </div>
        </div>
        
        <div class="conversations-container" id="conversations-container">
            <div class="loading-conversations">Loading conversations...</div>
        </div>
        
        <div id="conversation-detail-view" class="hidden"></div>
    `;
    
    // Add it to the content display
    contentDisplay.appendChild(conversationsView);
    
    // Make sure the stylesheet is loaded
    if (!document.querySelector('link[href*="conversations-manager.css"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/css/conversations-manager.css';
        document.head.appendChild(link);
    }
    
    return conversationsView;
};

// Fix for updateContent function - this is called directly when view is ready
window.fixOrbInterface = function() {
    console.log('Fixing orb interface...');
    
    // Get the orb interface updateContent function
    const orbInterface = document.querySelector('#orbital-planet-container');
    if (!orbInterface) {
        console.error('Orb interface not found');
        return;
    }
    
    // Fix updateContent to ensure only one section is shown at a time
    if (typeof updateContent === 'function') {
        console.log('Original updateContent function found, overriding...');
        
        // Save original function for reference
        window._originalUpdateContent = updateContent;
        
        // Override with our fixed version
        window.updateContent = function(section) {
            console.log(`Fixed updateContent called for section: ${section}`);
            
            // Get content display
            const contentDisplay = document.getElementById('content-display');
            if (!contentDisplay) {
                console.error('Content display element not found');
                return;
            }
            
            // CRITICAL: Hide ALL sections first
            document.querySelectorAll('#content-display > div').forEach(div => {
                div.classList.add('hidden');
            });
            
            // Show only the requested section
            if (section === "conversations") {
                // Ensure conversations view exists
                if (!document.getElementById('conversations-view')) {
                    window.createConversationsView();
                }
                
                // Show conversations view
                const conversationsView = document.getElementById('conversations-view');
                if (conversationsView) {
                    conversationsView.classList.remove('hidden');
                    
                    // Initialize conversations manager
                    if (typeof window.initConversationsManager === 'function') {
                        window.initConversationsManager();
                    } else {
                        console.error('initConversationsManager function not found');
                    }
                }
            } else {
                // For other sections, create them if needed
                const sectionId = `${section}-view`;
                const sectionTitle = section.charAt(0).toUpperCase() + section.slice(1);
                
                window.ensureViewExists(sectionId, sectionTitle);
                const sectionView = document.getElementById(sectionId);
                
                if (sectionView) {
                    sectionView.classList.remove('hidden');
                    
                    // If we have content from old method, use it
                    if (window.sections && window.sections[section]) {
                        const contentContainer = sectionView.querySelector('.content-container');
                        if (contentContainer) {
                            contentContainer.innerHTML = window.sections[section];
                        } else {
                            sectionView.innerHTML = window.sections[section];
                        }
                    }
                }
            }
        };
    } else {
        console.error('updateContent function not found for override');
    }
};

// When the document is ready, run our fixes
document.addEventListener('DOMContentLoaded', function() {
    // Wait a moment to ensure all scripts are loaded
    setTimeout(() => {
        window.fixOrbInterface();
        
        // Create content display if it doesn't exist
        if (!document.getElementById('content-display')) {
            console.log('Creating content display...');
            const contentDisplay = document.createElement('div');
            contentDisplay.id = 'content-display';
            document.body.appendChild(contentDisplay);
        }
        
        // Make sure the conversations view exists
        if (!document.getElementById('conversations-view')) {
            window.createConversationsView();
        }
    }, 500);
});
