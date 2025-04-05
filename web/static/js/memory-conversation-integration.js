/**
 * Minerva Memory and Conversation Integration
 * Handles the integration of memory and conversation management with the main Minerva UI
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Memory and Conversation Integration...');
    
    // References to UI elements
    const memoryPanel = document.getElementById('memory-manager-container');
    const conversationPanel = document.getElementById('conversation-manager-container');
    const memoriesBtn = document.getElementById('memories-btn');
    const conversationsBtn = document.getElementById('conversations-btn');
    const dashboardBtn = document.getElementById('dashboard-btn');
    const dashboard = document.getElementById('minerva-dashboard');
    
    // Check if we have all required elements
    if (!memoryPanel || !conversationPanel) {
        console.error('Memory or Conversation container not found!');
        return;
    }
    
    // Add close buttons to panels
    function addCloseButton(panel) {
        if (!panel.querySelector('.close-panel')) {
            // Create header div to contain the title and close button
            const headerDiv = document.createElement('div');
            headerDiv.className = 'panel-header';
            
            // Add title
            const title = document.createElement('h2');
            title.className = 'panel-title';
            title.textContent = panel.id === 'memory-manager-container' ? 'Memory Manager' : 'Conversation Manager';
            headerDiv.appendChild(title);
            
            // Create close button
            const closeButton = document.createElement('button');
            closeButton.className = 'close-panel';
            closeButton.innerHTML = '&times;';
            closeButton.setAttribute('title', 'Close Panel');
            
            closeButton.addEventListener('click', function() {
                // Hide this panel
                panel.classList.add('hidden');
                
                // Show dashboard
                if (dashboard) {
                    dashboard.classList.remove('hidden');
                }
                
                // Update active button
                if (dashboardBtn) {
                    // Remove active from all buttons
                    document.querySelectorAll('#minerva-bottom-nav .nav-button').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    
                    // Set dashboard as active
                    dashboardBtn.classList.add('active');
                }
            });
            
            // Add close button to header
            headerDiv.appendChild(closeButton);
            
            // Add header to panel (only when showing the panel for the first time)
            panel.insertBefore(headerDiv, panel.firstChild);
        }
    }
    
    // Don't add close buttons on page load
    // We'll add them when the panels are shown instead
    
    // Initialize Memory Manager
    function initializeMemoryManager() {
        if (typeof MinervaMemoryManager !== 'undefined') {
            if (!window.memoryManager) {
                window.memoryManager = new MinervaMemoryManager({
                    container: memoryPanel,
                    activeProject: window.activeProject || 'general'
                });
                console.log('Memory Manager initialized');
            }
        } else {
            console.error('MinervaMemoryManager class not found');
        }
    }
    
    // Initialize Conversation Manager
    function initializeConversationManager() {
        if (typeof MinervaConversationManager !== 'undefined') {
            if (!window.conversationManager) {
                window.conversationManager = new MinervaConversationManager({
                    container: conversationPanel,
                    activeProject: window.activeProject || 'general',
                    memoryManager: window.memoryManager
                });
                console.log('Conversation Manager initialized');
            }
        } else {
            console.error('MinervaConversationManager class not found');
        }
    }
    
    // Add event handlers for memory and conversation buttons
    if (memoriesBtn) {
        memoriesBtn.addEventListener('click', function() {
            // Hide other panels
            if (dashboard) dashboard.classList.add('hidden');
            conversationPanel.classList.add('hidden');
            
            // Show memory panel
            memoryPanel.classList.remove('hidden');
            
            // Add close button if it doesn't exist yet
            addCloseButton(memoryPanel);
            
            // Initialize if not already done
            initializeMemoryManager();
            
            // Update active state
            document.querySelectorAll('#minerva-bottom-nav .nav-button').forEach(btn => {
                btn.classList.remove('active');
            });
            memoriesBtn.classList.add('active');
        });
    }
    
    if (conversationsBtn) {
        conversationsBtn.addEventListener('click', function() {
            // Hide other panels
            if (dashboard) dashboard.classList.add('hidden');
            memoryPanel.classList.add('hidden');
            
            // Show conversation panel
            conversationPanel.classList.remove('hidden');
            
            // Add close button if it doesn't exist yet
            addCloseButton(conversationPanel);
            
            // Initialize if not already done
            initializeConversationManager();
            
            // Update active state
            document.querySelectorAll('#minerva-bottom-nav .nav-button').forEach(btn => {
                btn.classList.remove('active');
            });
            conversationsBtn.classList.add('active');
        });
    }
    
    // Also ensure memory and conversation panels are hidden when dashboard is shown
    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', function() {
            // This is a safe way to add our functionality without disturbing existing code
            memoryPanel.classList.add('hidden');
            conversationPanel.classList.add('hidden');
        });
    }
    
    // Initialize both managers on page load
    setTimeout(function() {
        initializeMemoryManager();
        initializeConversationManager();
    }, 1000);
    
    console.log('Memory and Conversation Integration initialized');
});
