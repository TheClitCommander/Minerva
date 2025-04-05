/**
 * Minerva Chat Diagnostics
 * Helper script to diagnose and fix chat initialization issues
 */

// Run diagnostics when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log("MINERVA DIAGNOSTICS: Running chat system diagnostics...");
    setTimeout(runDiagnostics, 1000);
    setTimeout(runDiagnostics, 3000); // Run again after elements should be created
});

// Run diagnostics and fix common issues
function runDiagnostics() {
    console.log("Running Minerva Chat Element Diagnostics...");
    
    // Check floating chat container
    const floatingChatContainer = document.getElementById('floating-chat-container');
    console.log("Floating chat container:", floatingChatContainer ? "FOUND" : "MISSING");
    
    // Check chat elements
    const floatingChatInput = document.getElementById('floating-chat-input');
    const chatInput = document.getElementById('chat-input');
    const floatingChatMessages = document.getElementById('floating-chat-messages');
    const chatMessages = document.getElementById('chat-messages');
    const floatingChatSendButton = document.getElementById('floating-chat-send-button');
    const chatSendButton = document.getElementById('chat-send-button');
    
    console.log("Chat elements diagnostic:");
    console.log("- floating-chat-input:", floatingChatInput ? "FOUND" : "MISSING");
    console.log("- chat-input:", chatInput ? "FOUND" : "MISSING");
    console.log("- floating-chat-messages:", floatingChatMessages ? "FOUND" : "MISSING");
    console.log("- chat-messages:", chatMessages ? "FOUND" : "MISSING");
    console.log("- floating-chat-send-button:", floatingChatSendButton ? "FOUND" : "MISSING");
    console.log("- chat-send-button:", chatSendButton ? "FOUND" : "MISSING");
    
    // Check elements by class (fallback method)
    const inputsByClass = document.querySelectorAll('.chat-input');
    const messagesByClass = document.querySelectorAll('.chat-messages');
    const buttonsByClass = document.querySelectorAll('.chat-send-button');
    
    console.log("Elements by class:");
    console.log("- .chat-input:", inputsByClass.length, "found");
    console.log("- .chat-messages:", messagesByClass.length, "found");
    console.log("- .chat-send-button:", buttonsByClass.length, "found");
    
    // Try to fix missing elements
    if (!floatingChatContainer && !document.getElementById('chat-container')) {
        console.log("FIXING: Creating missing chat container");
        createChatContainer();
    }
    
    // Fix API connection settings
    fixApiSettings();
    
    // Check global references
    if (window.chatInput) {
        console.log("Global chatInput reference:", "SET");
    } else {
        console.log("Global chatInput reference:", "MISSING");
    }
    
    if (window.sendButton) {
        console.log("Global sendButton reference:", "SET");
    } else {
        console.log("Global sendButton reference:", "MISSING");
    }
    
    if (window.chatMessages) {
        console.log("Global chatMessages reference:", "SET");
    } else {
        console.log("Global chatMessages reference:", "MISSING");
    }
    
    // Ensure initialization function exists
    if (typeof initializeChatSystem === 'function') {
        console.log("initializeChatSystem function:", "EXISTS");
    } else {
        console.log("initializeChatSystem function:", "MISSING");
    }
    
    // Check if floating chat component exists
    if (typeof FloatingChatComponent === 'function') {
        console.log("FloatingChatComponent class:", "EXISTS");
    } else {
        console.log("FloatingChatComponent class:", "MISSING");
    }
    
    // Check server connection
    checkServerConnection();
}

// Create a basic chat container if it doesn't exist
function createChatContainer() {
    const container = document.createElement('div');
    container.id = 'floating-chat-container';
    container.className = 'floating-chat-container';
    container.style.position = 'fixed';
    container.style.bottom = '20px';
    container.style.right = '20px';
    container.style.width = '350px';
    container.style.maxHeight = '500px';
    container.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
    container.style.borderRadius = '8px';
    container.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
    container.style.overflow = 'hidden';
    container.style.zIndex = '9999';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.transition = 'all 0.3s ease';
    
    // Add container to body
    document.body.appendChild(container);
    
    console.log("Created floating chat container");
    
    // Add basic chat elements
    createChatElements(container);
}

// Create basic chat elements in the container
function createChatElements(container) {
    // Create header
    const header = document.createElement('div');
    header.className = 'chat-header';
    header.style.padding = '10px';
    header.style.backgroundColor = '#4a4a9e';
    header.style.color = 'white';
    header.style.fontWeight = 'bold';
    header.style.cursor = 'move';
    header.textContent = 'Minerva Chat';
    container.appendChild(header);
    
    // Create messages container
    const messages = document.createElement('div');
    messages.id = 'floating-chat-messages';
    messages.className = 'chat-messages';
    messages.style.padding = '10px';
    messages.style.height = '300px';
    messages.style.overflowY = 'auto';
    container.appendChild(messages);
    
    // Create input container
    const inputContainer = document.createElement('div');
    inputContainer.className = 'chat-input-container';
    inputContainer.style.display = 'flex';
    inputContainer.style.padding = '10px';
    inputContainer.style.borderTop = '1px solid #eee';
    
    // Create input field
    const input = document.createElement('input');
    input.type = 'text';
    input.id = 'floating-chat-input';
    input.className = 'chat-input';
    input.placeholder = 'Type your message...';
    input.style.flex = '1';
    input.style.padding = '8px';
    input.style.border = '1px solid #ddd';
    input.style.borderRadius = '4px';
    input.style.marginRight = '8px';
    inputContainer.appendChild(input);
    
    // Create send button
    const button = document.createElement('button');
    button.id = 'floating-chat-send-button';
    button.className = 'chat-send-button';
    button.textContent = 'Send';
    button.style.padding = '8px 12px';
    button.style.backgroundColor = '#4a4a9e';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.cursor = 'pointer';
    inputContainer.appendChild(button);
    
    container.appendChild(inputContainer);
    
    console.log("Created chat elements in container");
    
    // Try to initialize the chat system
    if (typeof initializeChatSystem === 'function') {
        setTimeout(initializeChatSystem, 500);
    }
}

// Fix API connection settings
function fixApiSettings() {
    // Make sure we're not in simulation mode unless specifically requested
    if (window.SIMULATION_MODE === undefined) {
        window.SIMULATION_MODE = false;
        console.log("FIXING: Set SIMULATION_MODE to false explicitly");
    }
    
    // Reset API attempt counter to give connections a fresh start
    try {
        localStorage.setItem('minerva_server_attempts', '0');
        console.log("FIXING: Reset API attempt counter");
    } catch (e) {
        console.warn("Could not reset API attempt counter:", e);
    }
}

// Check if the server is running
function checkServerConnection() {
    console.log("Checking server connection...");
    
    // Try multiple endpoints to see which one responds
    const endpoints = [
        '/api/think-tank',
        '/api/chat/message',
        '/api/status',
        'http://localhost:8080/api/think-tank',
        'http://localhost:8080/api/chat/message'
    ];
    
    // Use a minimal ping payload
    const payload = {
        message: "ping",
        type: "system_check"
    };
    
    let anySuccess = false;
    
    // Try each endpoint
    endpoints.forEach(endpoint => {
        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (response.ok) {
                console.log(`✅ SERVER CONNECTION SUCCESS: ${endpoint} is available`);
                anySuccess = true;
                
                // Store this as the last successful endpoint
                localStorage.setItem('minerva_last_endpoint', endpoint);
            } else {
                console.log(`❌ SERVER CONNECTION ERROR: ${endpoint} returned ${response.status}`);
            }
        })
        .catch(error => {
            console.log(`❌ SERVER CONNECTION ERROR: ${endpoint} - ${error.message}`);
        });
    });
    
    // Show diagnostic message on the page after checking
    setTimeout(() => {
        if (!anySuccess && typeof displayMessage === 'function') {
            try {
                displayMessage("Minerva Diagnostics: Unable to connect to any API endpoint. Please check if the server is running at http://localhost:8080", "system");
            } catch (e) {
                console.error("Could not display diagnostic message:", e);
            }
        }
    }, 3000);
}
