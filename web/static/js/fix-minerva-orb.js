// Direct orbit implementation for Minerva Portal
console.log("Loading direct orbit implementation");

// Add global tracking for chat orb dragging
window.chatOrbIsDragging = false;

// Initialize chat history array
let chatHistory = [];
const MAX_CHAT_HISTORY = 20;

// Try to load chat history from localStorage
try {
    const savedHistory = localStorage.getItem('minerva_chat_history');
    if (savedHistory) {
        chatHistory = JSON.parse(savedHistory);
    }
} catch (e) {
    console.error("Failed to load chat history:", e);
    chatHistory = [];
}

// Function to save chat history to localStorage
function saveChatHistory() {
    try {
        localStorage.setItem('minerva_chat_history', JSON.stringify(chatHistory));
    } catch (e) {
        console.error("Failed to save chat history:", e);
    }
}

// Function to add a message to chat history
function addMessageToHistory(text, sender) {
    chatHistory.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString()
    });
    
    // Trim history to max length
    if (chatHistory.length > MAX_CHAT_HISTORY) {
        chatHistory = chatHistory.slice(chatHistory.length - MAX_CHAT_HISTORY);
    }
    
    // Save to localStorage
    saveChatHistory();
}

document.addEventListener('DOMContentLoaded', function() {
    // Force create elements right away
    createOrbitalElements();
    
    // Setup key and click handlers
    setupEventHandlers();
    
    // Handle chat orb positioning and boundaries too
    setupChatOrbDragging();
    
    // Add chat functionality
    setupChatFunctionality();
    
    // Simple function to link the silver chat orb with the chat panel
    const chatOrb = document.getElementById('chat-orb');
    const chatPanel = document.getElementById('chat-panel');
    
    if (chatOrb && chatPanel) {
        // Make sure chat panel starts hidden - IMPORTANT!
        chatPanel.classList.remove('active');
        
        // Position the chat panel near the orb
        function positionChatPanelByOrb() {
            const orbRect = chatOrb.getBoundingClientRect();
            const panelRect = chatPanel.getBoundingClientRect();
            
            // Try positioning to the right of the orb
            let left = orbRect.right + 20;
            let top = orbRect.top - (panelRect.height/2) + (orbRect.height/2);
            
            // If not enough space on right, try left
            if (left + panelRect.width > window.innerWidth - 20) {
                left = orbRect.left - panelRect.width - 20;
            }
            
            // If not enough space on either side, position below
            if (left < 20 || left + panelRect.width > window.innerWidth - 20) {
                left = orbRect.left - (panelRect.width/2) + (orbRect.width/2);
                top = orbRect.bottom + 20;
            }
            
            // Ensure the panel stays within viewport
            left = Math.max(20, Math.min(left, window.innerWidth - panelRect.width - 20));
            top = Math.max(20, Math.min(top, window.innerHeight - panelRect.height - 20));
            
            // Apply position
            chatPanel.style.position = 'fixed';
            chatPanel.style.left = left + 'px';
            chatPanel.style.top = top + 'px';
            chatPanel.style.right = 'auto';
            chatPanel.style.bottom = 'auto';
        }
        
        // Add direct click handler on the orb to toggle chat visibility
        chatOrb.addEventListener('click', function(e) {
            // Only handle as click if we're not dragging
            if (!window.chatOrbIsDragging) {
                console.log("Toggling chat panel visibility");
                if (chatPanel.classList.contains('active')) {
                    chatPanel.classList.remove('active');
                } else {
                    chatPanel.classList.add('active');
                    positionChatPanelByOrb();

                    // If first time opening, connect to socket
                    if (!window.socketInitialized) {
                        initializeSocketConnection();
                    }
                }
                e.stopPropagation();
            }
        });
        
        // Close chat when clicking outside
        document.addEventListener('click', function(e) {
            if (chatPanel.classList.contains('active') && 
                !chatPanel.contains(e.target) && 
                e.target !== chatOrb) {
                chatPanel.classList.remove('active');
            }
        });
        
        // Watch for silver orb movement
        let lastOrbX = 0;
        let lastOrbY = 0;
        
        function checkOrbPosition() {
            const rect = chatOrb.getBoundingClientRect();
            if (Math.abs(rect.left - lastOrbX) > 5 || Math.abs(rect.top - lastOrbY) > 5) {
                lastOrbX = rect.left;
                lastOrbY = rect.top;
                
                if (chatPanel.classList.contains('active')) {
                    positionChatPanelByOrb();
                }
            }
            requestAnimationFrame(checkOrbPosition);
        }
        
        checkOrbPosition();
        
        // Reposition when window is resized
        window.addEventListener('resize', function() {
            if (chatPanel.classList.contains('active')) {
                positionChatPanelByOrb();
            }
        });
    }
    
    console.log("Orbital menu implementation loaded");
});

function createOrbitalElements() {
    console.log("Creating orbital elements");
    
    // Get the Minerva orb element
    const minervaOrb = document.getElementById('minerva-portal');
    if (!minervaOrb) {
        console.error('Could not find minerva-portal element');
        return;
    }
    
    // Get orb position
    const rect = minervaOrb.getBoundingClientRect();
    const centerX = rect.left + rect.width/2;
    const centerY = rect.top + rect.height/2;
    
    // Create container for orbitals if needed
    let orbitalContainer = document.getElementById('orbital-container');
    if (!orbitalContainer) {
        orbitalContainer = document.createElement('div');
        orbitalContainer.id = 'orbital-container';
        orbitalContainer.style.position = 'fixed';
        orbitalContainer.style.zIndex = '900';
        document.body.appendChild(orbitalContainer);
    }
    
    // Position container - ensure it's precisely centered
    orbitalContainer.style.left = centerX + 'px';
    orbitalContainer.style.top = centerY + 'px';
    
    // Add CSS if needed
    addOrbitStyles();
    
    // Create orbital items
    const items = [
        { icon: 'tachometer-alt', label: 'Dashboard', color: '#6e4cf8' },
        { icon: 'project-diagram', label: 'Projects', color: '#4c8af8' },
        { icon: 'brain', label: 'Memory', color: '#f84cce' },
        { icon: 'comment-dots', label: 'Conversations', color: '#4cf8a3' },
        { icon: 'robot', label: 'Bots', color: '#f8814c' }
    ];
    
    // Clear existing orbitals
    orbitalContainer.innerHTML = '';
    
    // Create each item
    items.forEach((item, index) => {
        const orbital = document.createElement('div');
        orbital.className = 'minerva-orbital';
        orbital.style.backgroundColor = item.color;
        
        // Calculate position in a perfect circle
        // Start from the top (270 degrees) and go clockwise
        const radius = 180; // Distance from center to orbital
        const totalItems = items.length;
        const angleIncrement = (2 * Math.PI) / totalItems;
        const startAngle = Math.PI * 1.5; // Start from top (270 degrees)
        const angle = startAngle + (index * angleIncrement);
        
        // Calculate x and y coordinates
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        
        // Set position using CSS variables for animation
        orbital.style.setProperty('--x', `${x}px`);
        orbital.style.setProperty('--y', `${y}px`);
        orbital.style.transform = `translate(${x}px, ${y}px)`;
        
        // Add icon
        orbital.innerHTML = `<i class="fas fa-${item.icon}"></i><span>${item.label}</span>`;
        
        // Add click handler
        orbital.addEventListener('click', function() {
            alert(`${item.label} selected!`);
        });
        
        // Add to container
        orbitalContainer.appendChild(orbital);
    });
    
    // Initially hide the orbital menu
    orbitalContainer.style.display = 'none';
    
    console.log("Created orbital elements:", items.length);
}

function addOrbitStyles() {
    // Only add styles once
    if (document.getElementById('minerva-orbit-styles')) return;
    
    // Create style element
    const style = document.createElement('style');
    style.id = 'minerva-orbit-styles';
    style.textContent = `
        #orbital-container {
            transform: translate(-50%, -50%);
            pointer-events: none;
            width: 0;
            height: 0;
        }
        
        .minerva-orbital {
            position: absolute;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            cursor: pointer;
            pointer-events: auto;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275),
                        box-shadow 0.3s ease;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
            z-index: 950;
            animation: float 5s infinite ease-in-out;
            font-size: 20px;
            transform-origin: center center;
            margin-left: -30px;
            margin-top: -30px;
        }
        
        .minerva-orbital i {
            filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.5));
        }
        
        .minerva-orbital span {
            position: absolute;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
            white-space: nowrap;
        }
        
        .minerva-orbital:hover {
            transform: scale(1.2) !important;
            box-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
        }
        
        .minerva-orbital:hover span {
            opacity: 1;
        }
        
        @keyframes float {
            0% { transform: translate(var(--x), var(--y)) scale(1); }
            50% { transform: translate(var(--x), var(--y)) translateY(-15px) scale(1.05); }
            100% { transform: translate(var(--x), var(--y)) scale(1); }
        }
        
        .space-instruction {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.5s ease;
            z-index: 1200;
            pointer-events: none;
        }
        
        .space-instruction.visible {
            opacity: 0.8;
        }
    `;
    
    // Add to head
    document.head.appendChild(style);
}

function setupEventHandlers() {
    // Get the Minerva orb element
    const minervaOrb = document.getElementById('minerva-portal');
    if (!minervaOrb) return;
    
    // Create space instruction element
    let spaceInstruction = document.createElement('div');
    spaceInstruction.className = 'space-instruction';
    spaceInstruction.textContent = 'Press SPACE to toggle orbital menu';
    document.body.appendChild(spaceInstruction);
    
    // Add click handler to toggle orbital menu
    minervaOrb.addEventListener('click', function(e) {
        // Only handle as a click if not dragging
        if (isDragging) return;
        
        const orbitalContainer = document.getElementById('orbital-container');
        if (!orbitalContainer) return;
        
        // Toggle visibility
        if (orbitalContainer.style.display === 'none') {
            orbitalContainer.style.display = 'block';
            spaceInstruction.classList.add('visible');
            setTimeout(() => {
                spaceInstruction.classList.remove('visible');
            }, 3000);
        } else {
            orbitalContainer.style.display = 'none';
        }
    });
    
    // Add space key handler
    document.addEventListener('keydown', function(e) {
        if (e.key === ' ' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
            e.preventDefault();
            
            const orbitalContainer = document.getElementById('orbital-container');
            if (!orbitalContainer) return;
            
            // Toggle visibility
            if (orbitalContainer.style.display === 'none') {
                orbitalContainer.style.display = 'block';
            } else {
                orbitalContainer.style.display = 'none';
            }
        }
    });
    
    // Track window resize to reposition
    window.addEventListener('resize', function() {
        const minervaOrb = document.getElementById('minerva-portal');
        const orbitalContainer = document.getElementById('orbital-container');
        if (!minervaOrb || !orbitalContainer) return;
        
        const rect = minervaOrb.getBoundingClientRect();
        orbitalContainer.style.left = (rect.left + rect.width/2) + 'px';
        orbitalContainer.style.top = (rect.top + rect.height/2) + 'px';
        
        // Also ensure the orb is still within boundaries after resize
        keepInBounds(minervaOrb);
    });
    
    // Handle orb dragging with boundary constraints
    let isDragging = false;
    let didDrag = false;
    let offsetX, offsetY;
    
    minervaOrb.addEventListener('mousedown', function(e) {
        isDragging = true;
        didDrag = false;
        minervaOrb.classList.add('dragging');
        
        const rect = minervaOrb.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        
        didDrag = true;
        
        // Calculate new position
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        
        // Apply boundary constraints
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const orbWidth = minervaOrb.offsetWidth;
        const orbHeight = minervaOrb.offsetHeight;
        
        // Ensure the orb stays within the viewport with padding
        const padding = 10;
        const boundedX = Math.max(padding, Math.min(x, viewportWidth - orbWidth - padding));
        const boundedY = Math.max(padding, Math.min(y, viewportHeight - orbHeight - padding));
        
        // Set orb position
        minervaOrb.style.left = boundedX + 'px';
        minervaOrb.style.top = boundedY + 'px';
        
        // Update orbital container position
        const orbitalContainer = document.getElementById('orbital-container');
        if (orbitalContainer) {
            orbitalContainer.style.left = (boundedX + minervaOrb.offsetWidth/2) + 'px';
            orbitalContainer.style.top = (boundedY + minervaOrb.offsetHeight/2) + 'px';
        }
    });
    
    document.addEventListener('mouseup', function() {
        if (!isDragging) return;
        
        isDragging = false;
        minervaOrb.classList.remove('dragging');
        
        // Save position to localStorage for persistence
        try {
            const rect = minervaOrb.getBoundingClientRect();
            localStorage.setItem('minerva_position', JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {
            console.error('Failed to save position:', e);
        }
    });
    
    // Add touch support for mobile
    minervaOrb.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) return;
        
        isDragging = true;
        window.chatOrbIsDragging = true; // Set global flag
        minervaOrb.classList.add('dragging');
        
        const touch = e.touches[0];
        const rect = minervaOrb.getBoundingClientRect();
        offsetX = touch.clientX - rect.left;
        offsetY = touch.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('touchmove', function(e) {
        if (!isDragging || e.touches.length !== 1) return;
        
        didDrag = true;
        
        const touch = e.touches[0];
        
        // Calculate new position
        const x = touch.clientX - offsetX;
        const y = touch.clientY - offsetY;
        
        // Apply boundary constraints
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const orbWidth = minervaOrb.offsetWidth;
        const orbHeight = minervaOrb.offsetHeight;
        
        // Ensure the orb stays within the viewport with padding
        const padding = 10;
        const boundedX = Math.max(padding, Math.min(x, viewportWidth - orbWidth - padding));
        const boundedY = Math.max(padding, Math.min(y, viewportHeight - orbHeight - padding));
        
        // Set orb position
        minervaOrb.style.left = boundedX + 'px';
        minervaOrb.style.top = boundedY + 'px';
        
        // Update orbital container position
        const orbitalContainer = document.getElementById('orbital-container');
        if (orbitalContainer) {
            orbitalContainer.style.left = (boundedX + minervaOrb.offsetWidth/2) + 'px';
            orbitalContainer.style.top = (boundedY + minervaOrb.offsetHeight/2) + 'px';
        }
    }, { passive: false });
    
    document.addEventListener('touchend', function() {
        if (!isDragging) return;
        
        isDragging = false;
        window.chatOrbIsDragging = false; // Reset global flag
        minervaOrb.classList.remove('dragging');
        
        // Save position to localStorage for persistence
        try {
            const rect = minervaOrb.getBoundingClientRect();
            localStorage.setItem('minerva_position', JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {
            console.error('Failed to save position:', e);
        }
    });
    
    // Restore saved position on load
    try {
        const savedPosition = localStorage.getItem('minerva_position');
        if (savedPosition) {
            const position = JSON.parse(savedPosition);
            minervaOrb.style.left = position.left + 'px';
            minervaOrb.style.top = position.top + 'px';
            minervaOrb.classList.remove('centered');
            
            // Make sure it's within bounds
            keepInBounds(minervaOrb);
        }
    } catch (e) {
        console.error('Failed to restore position:', e);
    }
}

function setupChatOrbDragging() {
    const chatOrb = document.getElementById('chat-orb');
    if (!chatOrb) return;
    
    // Reset to default position (bottom right corner)
    function resetToBottomRight() {
        chatOrb.style.bottom = '30px';
        chatOrb.style.right = '30px';
        chatOrb.style.left = 'auto';
        chatOrb.style.top = 'auto';
    }
    
    // Start with default position
    resetToBottomRight();
    
    let isDragging = false;
    let offsetX, offsetY;
    
    chatOrb.addEventListener('mousedown', function(e) {
        isDragging = true;
        window.chatOrbIsDragging = true; // Set global flag
        chatOrb.classList.add('dragging');
        
        const rect = chatOrb.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;
        
        // Apply position
        chatOrb.style.left = x + 'px';
        chatOrb.style.top = y + 'px';
        chatOrb.style.right = 'auto';
        chatOrb.style.bottom = 'auto';
        
        // If the chat panel is open, reposition it to follow the orb
        const chatPanel = document.getElementById('chat-panel');
        if (chatPanel && chatPanel.classList.contains('active')) {
            positionChatPanelNearOrb();
        }
        
        keepInBounds(chatOrb);
    });
    
    document.addEventListener('mouseup', function() {
        if (!isDragging) return;
        
        isDragging = false;
        window.chatOrbIsDragging = false; // Reset global flag
        chatOrb.classList.remove('dragging');
        
        // Save position to localStorage for persistence
        try {
            const rect = chatOrb.getBoundingClientRect();
            localStorage.setItem('chat_orb_position', JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {
            console.error('Failed to save chat orb position:', e);
        }
    });
    
    // Add touch support for mobile
    chatOrb.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) return;
        
        isDragging = true;
        window.chatOrbIsDragging = true; // Set global flag
        chatOrb.classList.add('dragging');
        
        const touch = e.touches[0];
        const rect = chatOrb.getBoundingClientRect();
        offsetX = touch.clientX - rect.left;
        offsetY = touch.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('touchmove', function(e) {
        if (!isDragging || e.touches.length !== 1) return;
        
        const touch = e.touches[0];
        
        // Calculate new position
        const x = touch.clientX - offsetX;
        const y = touch.clientY - offsetY;
        
        // Set orb position
        chatOrb.style.left = x + 'px';
        chatOrb.style.top = y + 'px';
        chatOrb.style.right = 'auto';
        chatOrb.style.bottom = 'auto';
        
        // If the chat panel is open, reposition it to follow the orb
        const chatPanel = document.getElementById('chat-panel');
        if (chatPanel && chatPanel.classList.contains('active')) {
            positionChatPanelNearOrb();
        }
        
        keepInBounds(chatOrb);
        
        e.preventDefault();
    }, { passive: false });
    
    document.addEventListener('touchend', function() {
        if (!isDragging) return;
        
        isDragging = false;
        window.chatOrbIsDragging = false; // Reset global flag
        chatOrb.classList.remove('dragging');
        
        // Save position to localStorage for persistence
        try {
            const rect = chatOrb.getBoundingClientRect();
            localStorage.setItem('chat_orb_position', JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {
            console.error('Failed to save chat orb position:', e);
        }
    });
    
    // Reset position button
    const resetBtn = document.createElement('button');
    resetBtn.id = 'reset-chat-orb';
    resetBtn.innerHTML = '<i class="fas fa-home"></i>';
    resetBtn.title = 'Reset chat to bottom right';
    resetBtn.style.position = 'fixed';
    resetBtn.style.bottom = '5px';
    resetBtn.style.right = '5px';
    resetBtn.style.width = '30px';
    resetBtn.style.height = '30px';
    resetBtn.style.borderRadius = '50%';
    resetBtn.style.background = 'rgba(100, 100, 100, 0.3)';
    resetBtn.style.color = 'white';
    resetBtn.style.border = 'none';
    resetBtn.style.display = 'none';
    resetBtn.style.alignItems = 'center';
    resetBtn.style.justifyContent = 'center';
    resetBtn.style.cursor = 'pointer';
    resetBtn.style.zIndex = '900';
    document.body.appendChild(resetBtn);
    
    resetBtn.addEventListener('click', function() {
        resetToBottomRight();
        localStorage.removeItem('chat_orb_position');
        resetBtn.style.display = 'none';
        
        // Reposition chat panel if it's open
        const chatPanel = document.getElementById('chat-panel');
        if (chatPanel && chatPanel.classList.contains('active')) {
            positionChatPanelNearOrb();
        }
    });
    
    // Restore saved position on load (only if exists)
    try {
        const savedPosition = localStorage.getItem('chat_orb_position');
        if (savedPosition) {
            const position = JSON.parse(savedPosition);
            chatOrb.style.left = position.left + 'px';
            chatOrb.style.top = position.top + 'px';
            chatOrb.style.bottom = 'auto';
            chatOrb.style.right = 'auto';
            
            // Show reset button when chat orb has been moved
            resetBtn.style.display = 'flex';
            
            // Make sure it's within bounds
            keepInBounds(chatOrb);
        }
    } catch (e) {
        console.error('Failed to restore chat orb position:', e);
        // Reset to default position if there's an error
        resetToBottomRight();
    }
}

// Function to keep an element within the bounds of the viewport
function keepInBounds(element) {
    if (!element) return;
    
    // Get element dimensions
    const rect = element.getBoundingClientRect();
    const elementWidth = rect.width;
    const elementHeight = rect.height;
    
    // Get viewport dimensions
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Define padding from edges
    const padding = 10;
    
    // Calculate bounds
    let x = rect.left;
    let y = rect.top;
    
    // Apply constraints
    if (x < padding) {
        x = padding;
    } else if (x + elementWidth > viewportWidth - padding) {
        x = viewportWidth - elementWidth - padding;
    }
    
    if (y < padding) {
        y = padding;
    } else if (y + elementHeight > viewportHeight - padding) {
        y = viewportHeight - elementHeight - padding;
    }
    
    // Update position only if needed
    if (x !== rect.left || y !== rect.top) {
        element.style.left = x + 'px';
        element.style.top = y + 'px';
        element.style.right = 'auto';
        element.style.bottom = 'auto';
    }
}

function setupChatFunctionality() {
    console.log("Setting up chat functionality");
    
    // Get elements
    const chatOrb = document.getElementById('chat-orb');
    const chatPanel = document.getElementById('chat-panel');
    const closeBtn = document.getElementById('close-chat-btn');
    const sendBtn = document.getElementById('send-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (!chatOrb || !chatPanel) {
        console.error("Chat elements not found");
        return;
    }
    
    // Make sure initial state is correct - ALWAYS start with panel closed
    chatPanel.classList.remove('active');
    
    // Add connection status indicator
    const statusIndicator = document.createElement('div');
    statusIndicator.id = 'connection-status';
    statusIndicator.className = 'connection-status disconnected';
    statusIndicator.title = 'Connection Status';
    statusIndicator.innerHTML = '<span class="status-dot"></span>';
    
    // Add the status indicator to the header
    const headerElement = chatPanel.querySelector('.chat-header');
    if (headerElement) {
        headerElement.appendChild(statusIndicator);
    }
    
    // Add clear button to chat panel
    const clearBtn = document.createElement('button');
    clearBtn.id = 'clear-chat-btn';
    clearBtn.innerHTML = '🗑️';
    clearBtn.title = 'Clear chat history';
    clearBtn.style.marginRight = '10px';
    clearBtn.style.background = 'none';
    clearBtn.style.border = 'none';
    clearBtn.style.color = 'rgba(255, 255, 255, 0.7)';
    clearBtn.style.cursor = 'pointer';
    clearBtn.style.fontSize = '16px';
    
    // Insert before close button
    if (closeBtn && closeBtn.parentNode) {
        closeBtn.parentNode.insertBefore(clearBtn, closeBtn);
    }
    
    // Variables for socket connection and message handling
    let socket = null;
    let socketConnected = false;
    let lastMessageTime = 0;
    
    // Add chat styles
    addChatStyles();
    
    // Try to connect socket
    socket = connectSocket();
    socketConnected = !!socket;
    
    // Update the click handler to use the function-scoped isDragging variable
    chatOrb.addEventListener('click', function(e) {
        // Only handle as a click if not dragging
        if (!isDragging) {
            console.log("Opening chat panel");
            chatPanel.classList.add('active');
            
            // Position the chat panel relative to the chat orb's current position
            positionChatPanelNearOrb();
            
            // Focus on the input after a brief delay to allow animation
            setTimeout(() => {
                chatInput.focus();
                
                // Load chat history if messages container is empty
                if (chatMessages.children.length === 0 && chatHistory.length > 0) {
                    loadChatHistory();
                }
                
                // Scroll to the bottom of messages
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 300);
            
            e.stopPropagation();
            
            // Try to connect to AI backend immediately when chat opens
            if (!socket || !socketConnected) {
                socket = connectSocket();
                socketConnected = !!socket;
                console.log("Attempting to connect to AI backend...");
                
                // Add a small delay to show connecting status before potentially switching to simulation
                setTimeout(() => {
                    if (!socketConnected) {
                        updateConnectionStatus('simulation-mode');
                        console.log("Using simulated responses as AI backend is not available");
                    } else {
                        updateConnectionStatus('ai-mode');
                        console.log("Connected to AI Think Tank backend");
                    }
                }, 2000);
            }
            
            // If no history and not initialized, show welcome message
            if (chatMessages.children.length === 0) {
                // Add typing indicator
                addTypingIndicator();
                
                // Show appropriate welcome message based on connection status
                setTimeout(() => {
                    removeTypingIndicator();
                    if (socketConnected) {
                        const welcomeMessage = "Hello! I'm Minerva, powered by the AI Think Tank. How can I assist you today?";
                        addChatMessage(welcomeMessage, 'bot');
                        updateConnectionStatus('ai-mode');
                    } else {
                        const offlineMessage = "Hello! I'm Minerva, currently operating in offline mode with local knowledge. I'll try to help you as best I can.";
                        addChatMessage(offlineMessage, 'bot');
                        updateConnectionStatus('simulation-mode');
                    }
                    localStorage.setItem('chat_initialized', 'true');
                }, 1000);
            }
        }
    });
    
    // Close button event
    closeBtn.addEventListener('click', function() {
        chatPanel.classList.remove('active');
    });
    
    // Allow clicking outside to close
    document.addEventListener('click', function(e) {
        if (chatPanel.classList.contains('active') && 
            !chatPanel.contains(e.target) && 
            e.target !== chatOrb && 
            !chatOrb.contains(e.target)) {
            chatPanel.classList.remove('active');
        }
    });
    
    // Clear button functionality
    clearBtn.addEventListener('click', function() {
        chatMessages.innerHTML = '';
        chatHistory = [];
        saveChatHistory();
        
        // Show cleared message
        addChatMessage("Chat history cleared", 'system');
    });
    
    // Send message on button click
    sendBtn.addEventListener('click', sendChatMessage);
    
    // Send message on enter key
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Set up MutationObserver to watch for chat panel becoming visible/hidden
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const isActive = chatPanel.classList.contains('active');
                
                // Update notification when chat is closed
                if (!isActive) {
                    updateChatNotification();
                }
            }
        });
    });
    
    // Start observing chat panel
    observer.observe(chatPanel, { attributes: true });
}

// Function to update connection status indicator
function updateConnectionStatus(status) {
    const statusIndicator = document.getElementById('connection-status');
    if (!statusIndicator) return;
    
    // Remove all existing classes
    statusIndicator.classList.remove('connected', 'connecting', 'disconnected', 'ai-mode', 'simulation-mode');
    
    // Add the appropriate class
    statusIndicator.classList.add(status);
    
    // Update the title and content
    let statusTitle = '';
    let statusContent = '<span class="status-dot"></span>';
    
    switch(status) {
        case 'connected':
            statusTitle = 'Connected to AI Think Tank';
            statusContent += '<span class="status-text">AI Connected</span>';
            break;
        case 'connecting':
            statusTitle = 'Connecting to AI Think Tank...';
            statusContent += '<span class="status-text">Connecting...</span>';
            break;
        case 'disconnected':
            statusTitle = 'Disconnected from AI - Using local knowledge';
            statusContent += '<span class="status-text">Offline Mode</span>';
            break;
        case 'ai-mode':
            statusTitle = 'Using AI Think Tank for responses';
            statusContent += '<span class="status-text">AI Think Tank</span>';
            break;
        case 'simulation-mode':
            statusTitle = 'Using simulated responses';
            statusContent += '<span class="status-text">Local Knowledge</span>';
            break;
    }
    
    statusIndicator.title = statusTitle;
    statusIndicator.innerHTML = statusContent;
}

// Function to position the chat panel near the orb
function positionChatPanelNearOrb() {
    const chatOrb = document.getElementById('chat-orb');
    const chatPanel = document.getElementById('chat-panel');
    
    if (!chatOrb || !chatPanel) return;
    
    // Get dimensions
    const orbRect = chatOrb.getBoundingClientRect();
    const panelRect = chatPanel.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    // Default position: to the left of the orb
    let left = orbRect.left - panelRect.width - 20;
    let top = orbRect.top - (panelRect.height / 2) + (orbRect.height / 2);
    
    // If not enough space on the left, position to the right
    if (left < 10) {
        left = orbRect.right + 20;
    }
    
    // If not enough space on the right either, position above or below
    if (left + panelRect.width > viewportWidth - 10) {
        left = orbRect.left - (panelRect.width / 2) + (orbRect.width / 2);
        top = orbRect.top - panelRect.height - 20;
        
        // If not enough space above, position below
        if (top < 10) {
            top = orbRect.bottom + 20;
        }
    }
    
    // Ensure the panel doesn't go off-screen
    left = Math.max(10, Math.min(left, viewportWidth - panelRect.width - 10));
    top = Math.max(10, Math.min(top, viewportHeight - panelRect.height - 10));
    
    // Apply the position
    chatPanel.style.left = `${left}px`;
    chatPanel.style.top = `${top}px`;
}

// Add a function to create and add the Socket.IO client library
function addSocketIOClient() {
    // Check if we already added the script
    if (document.getElementById('socketio-client')) {
        return;
    }
    
    // Create Socket.IO client script
    const script = document.createElement('script');
    script.id = 'socketio-client';
    script.src = 'https://cdn.socket.io/4.6.0/socket.io.min.js';
    script.integrity = 'sha384-c79GN5VsunZvi+Q/WObgk2in0CbZsHnjEqvFxC5DxHn9lTfNce2WW6h2pH6u/kF+';
    script.crossOrigin = 'anonymous';
    
    // Add to document
    document.head.appendChild(script);
    console.log("Added Socket.IO client library from CDN");
}

// Add chat panel structure with a draggable header
function createChatPanel() {
    // Check if panel already exists
    if (document.getElementById('chat-panel')) {
        return document.getElementById('chat-panel');
    }
    
    // Create the main panel
    const panel = document.createElement('div');
    panel.id = 'chat-panel';
    panel.classList.add('chat-animation');
    
    // Create the header with drag handle
    const header = document.createElement('div');
    header.className = 'chat-header';
    header.style.padding = '10px 15px';
    header.style.background = 'rgba(50, 50, 70, 0.7)';
    header.style.borderTopLeftRadius = '10px';
    header.style.borderTopRightRadius = '10px';
    header.style.display = 'flex';
    header.style.justifyContent = 'space-between';
    header.style.alignItems = 'center';
    header.style.cursor = 'move';
    
    // Add title
    const title = document.createElement('div');
    title.textContent = 'Minerva Chat';
    title.style.fontWeight = 'bold';
    
    // Add close button
    const closeBtn = document.createElement('button');
    closeBtn.id = 'close-chat-btn';
    closeBtn.innerHTML = '×';
    closeBtn.style.background = 'none';
    closeBtn.style.border = 'none';
    closeBtn.style.color = 'white';
    closeBtn.style.fontSize = '20px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.padding = '0 5px';
    closeBtn.title = 'Close chat';
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // Create messages container
    const messagesContainer = document.createElement('div');
    messagesContainer.id = 'chat-messages';
    messagesContainer.style.flex = '1';
    messagesContainer.style.padding = '10px';
    messagesContainer.style.overflowY = 'auto';
    messagesContainer.style.display = 'flex';
    messagesContainer.style.flexDirection = 'column';
    messagesContainer.style.gap = '10px';
    
    // Create input area
    const inputArea = document.createElement('div');
    inputArea.style.padding = '10px';
    inputArea.style.display = 'flex';
    inputArea.style.borderTop = '1px solid rgba(255, 255, 255, 0.1)';
    
    const chatInput = document.createElement('input');
    chatInput.id = 'chat-input';
    chatInput.type = 'text';
    chatInput.placeholder = 'Ask Minerva something...';
    chatInput.style.flex = '1';
    chatInput.style.padding = '8px 12px';
    chatInput.style.borderRadius = '20px';
    chatInput.style.border = 'none';
    chatInput.style.background = 'rgba(40, 40, 60, 0.6)';
    chatInput.style.color = 'white';
    
    const sendBtn = document.createElement('button');
    sendBtn.id = 'send-chat-btn';
    sendBtn.innerHTML = '→';
    sendBtn.style.marginLeft = '10px';
    sendBtn.style.width = '36px';
    sendBtn.style.height = '36px';
    sendBtn.style.borderRadius = '50%';
    sendBtn.style.border = 'none';
    sendBtn.style.background = 'rgba(110, 76, 248, 0.8)';
    sendBtn.style.color = 'white';
    sendBtn.style.fontWeight = 'bold';
    sendBtn.style.cursor = 'pointer';
    
    inputArea.appendChild(chatInput);
    inputArea.appendChild(sendBtn);
    
    // Assemble the panel
    panel.appendChild(header);
    panel.appendChild(messagesContainer);
    panel.appendChild(inputArea);
    
    // Add to the document
    document.body.appendChild(panel);
    
    // Make the header draggable for repositioning the chat panel
    let isDragging = false;
    let dragOffsetX, dragOffsetY;
    
    function startDrag(e) {
        if (e.target === closeBtn) return;
        const x = e.clientX || (e.touches && e.touches[0].clientX);
        const y = e.clientY || (e.touches && e.touches[0].clientY);
        
        if (!x || !y) return;
        
        isDragging = true;
        const rect = panel.getBoundingClientRect();
        dragOffsetX = x - rect.left;
        dragOffsetY = y - rect.top;
        
        panel.style.transition = 'none';
        e.preventDefault();
    }
    
    function doDrag(e) {
        if (!isDragging) return;
        
        const x = e.clientX || (e.touches && e.touches[0].clientX);
        const y = e.clientY || (e.touches && e.touches[0].clientY);
        
        if (!x || !y) return;
        
        const newLeft = x - dragOffsetX;
        const newTop = y - dragOffsetY;
        
        panel.style.left = newLeft + 'px';
        panel.style.top = newTop + 'px';
        panel.style.bottom = 'auto';
        panel.style.right = 'auto';
        
        keepInBounds(panel);
        e.preventDefault();
    }
    
    function endDrag() {
        if (!isDragging) return;
        isDragging = false;
        panel.style.transition = '';
    }
    
    // Mouse events
    header.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', endDrag);
    
    // Touch events
    header.addEventListener('touchstart', startDrag);
    document.addEventListener('touchmove', doDrag, { passive: false });
    document.addEventListener('touchend', endDrag);
    
    return panel;
}

// Add touch support for the chat orb
function addChatOrbTouchSupport() {
    const chatOrb = document.getElementById('chat-orb');
    if (!chatOrb) return;
    
    let isDragging = false;
    let offsetX, offsetY;
    
    chatOrb.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) return;
        
        isDragging = true;
        chatOrb.classList.add('dragging');
        
        const touch = e.touches[0];
        const rect = chatOrb.getBoundingClientRect();
        offsetX = touch.clientX - rect.left;
        offsetY = touch.clientY - rect.top;
        
        e.preventDefault();
    });
    
    document.addEventListener('touchmove', function(e) {
        if (!isDragging || e.touches.length !== 1) return;
        
        const touch = e.touches[0];
        
        // Calculate new position
        const x = touch.clientX - offsetX;
        const y = touch.clientY - offsetY;
        
        // Set orb position
        chatOrb.style.left = x + 'px';
        chatOrb.style.top = y + 'px';
        chatOrb.style.right = 'auto';
        chatOrb.style.bottom = 'auto';
        
        // If the chat panel is open, reposition it to follow the orb
        const chatPanel = document.getElementById('chat-panel');
        if (chatPanel && chatPanel.classList.contains('active')) {
            positionChatPanelNearOrb();
        }
        
        keepInBounds(chatOrb);
        
        e.preventDefault();
    }, { passive: false });
    
    document.addEventListener('touchend', function() {
        if (!isDragging) return;
        
        isDragging = false;
        chatOrb.classList.remove('dragging');
        
        // Save position
        const rect = chatOrb.getBoundingClientRect();
        const position = {
            left: rect.left,
            top: rect.top
        };
        localStorage.setItem('chat-orb-position', JSON.stringify(position));
    });
}

// Function to load chat history into the chat panel
function loadChatHistory() {
    if (chatHistory && chatHistory.length > 0) {
        // Clear current messages
        chatMessages.innerHTML = '';
        
        // Add history messages with a system divider
        const divider = document.createElement('div');
        divider.className = 'message system-message';
        divider.innerHTML = '--- Previous Conversation ---';
        chatMessages.appendChild(divider);
        
        // Add each message from history
        chatHistory.forEach(msg => {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${msg.sender}-message`;
            
            // Format the message with same rules as addChatMessage
            let formattedText = msg.text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            
            messageDiv.innerHTML = formattedText;
            
            // Add timestamp
            if (msg.timestamp) {
                const timestamp = document.createElement('div');
                timestamp.className = 'message-timestamp';
                const date = new Date(msg.timestamp);
                timestamp.textContent = date.getHours().toString().padStart(2, '0') + ':' + 
                                      date.getMinutes().toString().padStart(2, '0');
                messageDiv.appendChild(timestamp);
            }
            
            chatMessages.appendChild(messageDiv);
        });
        
        // Divider for new messages
        const newDivider = document.createElement('div');
        newDivider.className = 'message system-message';
        newDivider.innerHTML = '--- New Session ---';
        chatMessages.appendChild(newDivider);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

// Add typing indicator
function addTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    // Remove any existing indicator first
    removeTypingIndicator();
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(indicator);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const indicators = document.querySelectorAll('.typing-indicator');
    indicators.forEach(function(indicator) {
        indicator.remove();
    });
}

// Check for notification dot
function updateChatNotification() {
    // Create notification dot if it doesn't exist
    const chatOrb = document.getElementById('chat-orb');
    if (!chatOrb) return;
    
    let notificationDot = chatOrb.querySelector('.chat-notification');
    if (!notificationDot) {
        notificationDot = document.createElement('div');
        notificationDot.className = 'chat-notification';
        chatOrb.appendChild(notificationDot);
    }
    
    // Only show if there are messages and panel is not active
    const chatPanel = document.getElementById('chat-panel');
    if (chatHistory.length > 0 && chatPanel && !chatPanel.classList.contains('active')) {
        notificationDot.classList.add('active');
    } else {
        notificationDot.classList.remove('active');
    }
}

// Add chat styles
function addChatStyles() {
    if (document.getElementById('chat-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'chat-styles';
    style.textContent = `
        #chat-panel {
            display: none;
            position: fixed;
            width: 350px;
            height: 450px;
            background-color: #1a1a2e;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            flex-direction: column;
            transition: all 0.3s ease;
            opacity: 0;
            transform: scale(0.95);
        }
        
        #chat-panel.active {
            display: flex;
            opacity: 1;
            transform: scale(1);
        }
        
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background-color: rgba(30, 30, 50, 0.8);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }
        
        .chat-header h3 {
            margin: 0;
            color: white;
            font-size: 16px;
        }
        
        #chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .message {
            padding: 10px 14px;
            border-radius: 18px;
            max-width: 80%;
            position: relative;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(135deg, #6e48e8, #5038c8);
            align-self: flex-end;
            color: white;
        }
        
        .bot-message {
            background: linear-gradient(135deg, #3c3c5a, #28284e);
            align-self: flex-start;
            color: white;
        }
        
        .system-message {
            background: rgba(255, 150, 0, 0.2);
            align-self: center;
            color: #ffb700;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
        }
        
        .timestamp {
            position: absolute;
            bottom: 2px;
            right: 8px;
            font-size: 9px;
            opacity: 0.7;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .chat-input-container {
            display: flex;
            padding: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        #chat-input {
            flex: 1;
            padding: 10px 15px;
            border: none;
            border-radius: 20px;
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            outline: none;
        }
        
        #send-chat-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #6e48e8;
            color: white;
            border: none;
            margin-left: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .typing-indicator {
            display: flex;
            align-items: center;
            align-self: flex-start;
            background: rgba(60, 60, 90, 0.5);
            padding: 10px 15px;
            border-radius: 18px;
        }
        
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background: white;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            opacity: 0.4;
            animation: pulse 1.5s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes pulse {
            0%, 100% { transform: translateY(0px); opacity: 0.4; }
            50% { transform: translateY(-5px); opacity: 0.8; }
        }
        
        .connection-status {
            display: flex;
            align-items: center;
            font-size: 11px;
            color: white;
            margin-right: 10px;
        }
        
        .connection-status .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        .connection-status.connected .dot {
            background-color: #4CAF50;
        }
        
        .connection-status.connecting .dot {
            background-color: #FFC107;
            animation: blink 1s infinite;
        }
        
        .connection-status.disconnected .dot {
            background-color: #F44336;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
    `;
    
    document.head.appendChild(style);
}

function initializeSocketConnection() {
    console.log("Initializing socket connection to AI backend");
    
    // Ensure we only run this once
    window.socketInitialized = true;
    
    // Dynamically load Socket.IO from CDN to ensure correct version
    const script = document.createElement('script');
    script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
    script.integrity = 'sha384-/KNQL8Nu5gCHLqwqfQjA689Hhoqgi2S84SNUxC3roTe4EhJ9AfLkp8QiQcU8AMzI';
    script.crossOrigin = 'anonymous';
    document.head.appendChild(script);
    
    script.onload = function() {
        console.log("Socket.IO client loaded, connecting to server");
        
        // Use the correct socket.io connection format
        const socket = io();
        
        // Track socket connection status
        socket.on('connect', function() {
            console.log('Successfully connected to Minerva server');
            updateConnectionStatus('connected');
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from Minerva server');
            updateConnectionStatus('disconnected');
        });
        
        socket.on('connect_error', function(error) {
            console.error('Socket connection error:', error);
            updateConnectionStatus('disconnected');
        });
        
        // Handle chat messages
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-chat-btn');
        
        if (chatInput && sendBtn) {
            // Send button click handler
            sendBtn.addEventListener('click', function() {
                sendMessage(socket, chatInput.value);
                chatInput.value = '';
            });
            
            // Enter key handler
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage(socket, chatInput.value);
                    chatInput.value = '';
                }
            });
        }
        
        // Welcome message
        addChatMessage("Hello! I'm Minerva, how can I help you today?", 'bot');
        
        // Store the socket globally
        window.minervaSocket = socket;
    };
}

// Function to send message to server
function sendMessage(socket, message) {
    if (!message.trim()) return;
    
    console.log('Sending message:', message);
    
    // Add the message to the chat display
    addChatMessage(message, 'user');
    
    // Show typing indicator
    addTypingIndicator();
    
    // Send to server - use simple string format as the server expects
    socket.emit('message', message);
    
    // Handle response from server
    socket.once('response', function(data) {
        removeTypingIndicator();
        const responseText = typeof data === 'string' ? data : 
                             (data.text || data.response || data.message || JSON.stringify(data));
        addChatMessage(responseText, 'bot');
    });
    
    // Fallback if no response in 10 seconds
    setTimeout(function() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            removeTypingIndicator();
            addChatMessage("I didn't receive a response from the server. Please try again.", 'system');
        }
    }, 10000);
}

// Update connection status visual indicator
function updateConnectionStatus(status) {
    const panel = document.getElementById('chat-panel');
    if (!panel) return;
    
    panel.dataset.connectionStatus = status;
    
    const statusIndicator = document.getElementById('connection-status') || 
                           document.createElement('div');
    
    if (!statusIndicator.id) {
        statusIndicator.id = 'connection-status';
        const header = panel.querySelector('.chat-header');
        if (header) header.appendChild(statusIndicator);
    }
    
    statusIndicator.className = 'connection-status ' + status;
    
    switch(status) {
        case 'connected':
            statusIndicator.innerHTML = '<span class="dot"></span> Connected to AI';
            break;
        case 'connecting':
            statusIndicator.innerHTML = '<span class="dot"></span> Connecting...';
            break;
        case 'disconnected':
            statusIndicator.innerHTML = '<span class="dot"></span> Offline';
            break;
    }
}

// Add message to chat
function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + sender + '-message';
    
    // Format message: handle basic markdown
    message = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/`(.*?)`/g, '<code>$1</code>')
                    .replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = message;
    
    // Add timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    const now = new Date();
    timestamp.textContent = now.getHours().toString().padStart(2, '0') + ':' + 
                           now.getMinutes().toString().padStart(2, '0');
    messageDiv.appendChild(timestamp);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}