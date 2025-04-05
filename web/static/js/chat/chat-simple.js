/**
 * Enhanced Minerva Chat Integration
 * Supports conversation memory and project conversion
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("Initializing Enhanced Minerva Chat Integration...");
    
    // DOM Elements
    const inputField = document.getElementById("chat-input");
    const sendButton = document.getElementById("chat-send-button");
    const chatBox = document.getElementById("chat-messages");

    // Conversation State
    let conversationId = localStorage.getItem('minerva_conversation_id') || null;
    let messageCount = 0;
    
    // Display welcome message
    setTimeout(() => {
        displayMessage("Welcome to Minerva. How can I help you today?", "system");
    }, 500);

    if (!inputField || !sendButton) {
        console.error("Chat input or send button not found!");
        return;
    }

    function sendMessage() {
        const message = inputField.value.trim();
        if (message === "") return;
        
        // Add user message to chat
        displayMessage(message, "user");
        
        // Send to API with conversation memory
        sendMessageToAPI(message);
        
        // Clear input after sending
        inputField.value = "";
        
        // Increment message count
        messageCount++;
    }

    inputField.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);
});

// Debug mode - set to true for additional debug information
const DEBUG_MODE = true;

function sendMessageToAPI(message) {
    console.log("Sending message:", message); // Debugging log
    
    // Show typing indicator
    const typingIndicator = addTypingIndicator();
    
    // Get or create conversation ID for persistence
    let conversationId = localStorage.getItem('minerva_conversation_id') || ('conv-' + Date.now());
    
    // Create payload object that works with multiple server implementations
    const payload = {
        message: message,
        conversation_id: conversationId,
        store_in_memory: true, // Enable conversation memory
        client_version: '1.0.2', // Add client version for tracking
        model_preferences: {
            priority: ["gpt-4o", "claude-3-opus", "gpt-4"], // Prioritize best models
            complexity: 0.7, // Set reasonably high complexity for good responses
            include_detailed_rankings: DEBUG_MODE // Include details in debug mode
        }
    };
    
    console.log("Request payload:", payload); // Log the request payload for debugging
    
    // Adaptive API connection strategy:
    // Try multiple endpoints in the order most likely to succeed
    // Each server implementation uses slightly different endpoints
    
    // First check if we should use relative or absolute paths
    const useRelativePath = (window.location.hostname === "localhost" || 
                            window.location.hostname === "127.0.0.1");
    
    // Track server connection attempts 
    let serverAttempts = localStorage.getItem('minerva_server_attempts') || '0';
    let attemptCount = parseInt(serverAttempts);
    const lastSuccessfulEndpoint = localStorage.getItem('minerva_last_endpoint') || '';
    
    // Prepare endpoints to try (in order of preference)
    let endpoints = [
        // If we had a successful endpoint before, try it first
        lastSuccessfulEndpoint,
        // Think Tank direct endpoint
        useRelativePath ? "/api/think-tank" : "http://localhost:8080/api/think-tank",
        // Legacy chat endpoint
        useRelativePath ? "/api/chat/message" : "http://localhost:8080/api/chat/message",
        // Bridge server fallback (if running)
        "http://localhost:8080/api/chat/message",
    ].filter(e => e); // Filter out empty strings
    
    // Remove duplicates
    endpoints = [...new Set(endpoints)];
    
    // If we've had multiple failed attempts, show a helpful message
    if (attemptCount > 2) {
        displayMessage("Trying to connect to Minerva server...", "system");
    }
    
    // Select the endpoint to try
    let apiUrl = endpoints[0];
    console.log("Using API URL:", apiUrl);
    
    // If in debug mode, add a diagnostic message
    if (DEBUG_MODE) {
        displayMessage(`[Debug] Connecting to endpoint: ${apiUrl}`, "system");
    }
    
    // Save attempt count for connection tracking
    localStorage.setItem('minerva_server_attempts', (attemptCount + 1).toString());
    
    fetch(apiUrl, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-Session-ID": conversationId
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        console.log("Response status:", response.status, response.statusText); // Log response status
        if (!response.ok) {
            // Try the next endpoint if this one failed
            if (endpoints.length > 1) {
                // Remove the failed endpoint and try the next one
                endpoints.shift();
                const nextEndpoint = endpoints[0];
                console.log(`Retrying with next endpoint: ${nextEndpoint}`);
                
                // Remove typing indicator for failed attempt
                removeTypingIndicator(typingIndicator);
                
                // Call recursively with the same message but different endpoint
                if (DEBUG_MODE) {
                    displayMessage(`[Debug] Retrying with endpoint: ${nextEndpoint}`, "system");
                }
                
                // Short delay before retry to avoid rapid requests
                setTimeout(() => {
                    sendMessageToAPI(message);
                }, 500);
                
                // Don't proceed with the current request
                throw new Error("Retrying with next endpoint");
            }
            
            throw new Error(`API error: ${response.status} - ${response.statusText}`);
        }
        
        // Success! Reset connection attempts and save successful endpoint
        localStorage.setItem('minerva_server_attempts', '0');
        localStorage.setItem('minerva_last_endpoint', apiUrl);
        
        return response.json();
    })
    .then(data => {
        // Remove typing indicator
        removeTypingIndicator(typingIndicator);
        console.log("Full API response:", data); // Log the full response for debugging
        
        // Store conversation ID if received from server, otherwise use the one we generated
        if (data.conversation_id) {
            localStorage.setItem('minerva_conversation_id', data.conversation_id);
            console.log("Saved conversation ID from server:", data.conversation_id);
            conversationId = data.conversation_id;
        } else if (!localStorage.getItem('minerva_conversation_id')) {
            localStorage.setItem('minerva_conversation_id', conversationId);
            console.log("Saved local conversation ID:", conversationId);
        }
        
        // Log memory information if present (important for conversation memory)
        if (data.memory_id || data.memory_info) {
            console.log("Memory information received:", { 
                memory_id: data.memory_id, 
                memory_info: data.memory_info 
            });
        }
        
        if (DEBUG_MODE) {
            displayMessage(`[Debug] Conversation ID: ${conversationId}`, "system");
            if (data.memory_id) {
                displayMessage(`[Debug] Memory ID: ${data.memory_id}`, "system");
            }
        }
        
        // ENHANCED Think Tank Response Handling
        // Based on the structure of think_tank_server.py and think_tank_consolidated.py responses
        let aiResponse = null;
        let modelInfo = null;
        
        // Check for the standard Think Tank response (from think_tank_server.py)
        if (data.response && typeof data.response === 'string' && data.response.trim() !== "") {
            console.log("Think Tank direct response format received");
            aiResponse = data.response;
            modelInfo = data.model_info || {};
        }
        // Check for web-based Think Tank multi-model response
        else if (data.think_tank_result && data.think_tank_result.response) {
            console.log("Think Tank result object format received");
            aiResponse = data.think_tank_result.response;
            modelInfo = data.think_tank_result.model_info || data.model_info || {};
        }
        // Check for blended_response (when using processor.response_blender)
        else if (data.blended_response) {
            console.log("Blended response format received");
            aiResponse = data.blended_response;
            modelInfo = data.model_info || {};
        }
        // Try other possible fields from different Think Tank implementations
        else if (data.message || data.text || data.content || data.answer) {
            console.log("Alternative response format received");
            aiResponse = data.message || data.text || data.content || data.answer;
            modelInfo = data.model_info || {};
        }
        
        // Add model information if available
        if (modelInfo) {
            console.log("Model information received:", modelInfo);
            
            // Create a compact representation of model info for the UI
            let modelDescription = "";
            if (modelInfo.model_used) {
                modelDescription = `Model: ${modelInfo.model_used}`;
            } else if (modelInfo.selected_model) {
                modelDescription = `Model: ${modelInfo.selected_model}`;
            } else if (modelInfo.blended_models && modelInfo.blended_models.length) {
                // For multi-model blended responses
                modelDescription = `Using ${modelInfo.blended_models.length} models`;
            }
            
            if (DEBUG_MODE && modelDescription) {
                displayMessage(`[Debug] ${modelDescription}`, "system");
            }
        }
        
        // Display response if we have one
        if (aiResponse && aiResponse.trim() !== "") {
            console.log("Displaying Think Tank response:", aiResponse);
            displayMessage(aiResponse, "ai", modelInfo);
            
            // Offer project conversion after 3 messages
            const messageCount = parseInt(localStorage.getItem('minerva_message_count') || '0') + 1;
            localStorage.setItem('minerva_message_count', messageCount);
            
            if (messageCount >= 3 && !document.querySelector('.project-conversion')) {
                addProjectConversionOption(conversationId);
            }
        } 
        // Error handling
        else if (data.error) {
            console.error("API returned error:", data.error);
            displayMessage(`Sorry, there was an issue: ${data.error}`, "system");
        } 
        // Fallback response for empty replies
        else {
            console.error("No response content found in any expected fields");
            
            // Try fallback to memory information if available
            if (data.memory_info && data.memory_info.summary) {
                displayMessage("I've stored that information in my memory: " + data.memory_info.summary, "ai");
            } else {
                // Create a reasonable fallback response
                displayMessage("I've received your message and will try to process it. However, the Think Tank connection needs to be checked. Please try a different question or check the server status.", "ai");
                
                if (DEBUG_MODE) {
                    setTimeout(() => {
                        displayMessage("Tip: If you're seeing this message, the Think Tank server might not be responding correctly. Check your server logs and ensure the Think Tank API is properly configured.", "system");
                    }, 800);
                }
            }
        }
    })
    .catch(error => {
        console.error("Error in Think Tank API:", error);
        removeTypingIndicator(typingIndicator);
        // Track connection failures for better error messaging
        const failCount = parseInt(localStorage.getItem('minerva_connection_fails') || '0') + 1;
        localStorage.setItem('minerva_connection_fails', failCount.toString());
        
        // Store the message locally even when server is unavailable
        // This maintains conversation flow and memory when offline
        saveMessageLocally(message, conversationId);
        
        // If we're retrying with a different endpoint, don't show error yet
        if (error.message === "Retrying with next endpoint") {
            return; // Exit early, the retry will happen separately
        }
        
        // Check if we've exhausted all endpoints
        if (failCount > 3) {
            // After multiple failures, show a more helpful message
            displayMessage(
                `I'm having trouble connecting to the Minerva server. Your message was saved locally.\n\n` +
                `Try refreshing the page or check if the Think Tank server is running at ${window.location.hostname}:8080.`, 
                "system"
            );
        } else {
            // First few failures get a simpler message
            displayMessage(`I'm having trouble connecting to the server. Your message was saved locally.`, "system");
        }
        
        // Provide specific development guidance if in dev environment
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            setTimeout(() => {
                displayMessage("[Debug] To fix this connection issue, make sure the Think Tank server is running. Try starting the server with 'python simple_bridge_server.py' in the /Users/bendickinson/Desktop/Minerva/web directory.", "system");
            }, 1000);
        }
    });
}

function displayMessage(text, sender, modelInfo = null) {
    const chatBox = document.getElementById("chat-messages");
    if (!chatBox) return;
    
    const messageDiv = document.createElement("div");
    messageDiv.className = sender + "-message";
    
    if (sender === 'ai' && modelInfo) {
        // Add model info for AI responses
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        messageDiv.appendChild(messageContent);
        
        const modelInfoDiv = document.createElement('div');
        modelInfoDiv.className = 'model-info';
        modelInfoDiv.textContent = `Powered by ${modelInfo.primary_model || 'Think Tank'}`;
        messageDiv.appendChild(modelInfoDiv);
    } else {
        messageDiv.textContent = text;
    }
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addTypingIndicator() {
    const chatBox = document.getElementById("chat-messages");
    if (!chatBox) return null;
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    chatBox.appendChild(indicator);
    chatBox.scrollTop = chatBox.scrollHeight;
    return indicator;
}

function removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.parentNode.removeChild(indicator);
    }
}

function addProjectConversionOption(conversationId) {
    const chatBox = document.getElementById("chat-messages");
    if (!chatBox) return;
    
    // Check if project conversion option already exists to avoid duplicates
    if (document.querySelector('.project-conversion')) return;
    
    const conversionDiv = document.createElement('div');
    conversionDiv.className = 'project-conversion';
    conversionDiv.innerHTML = `
        <p>Would you like to convert this conversation to a project?</p>
        <div class="project-conversion-controls">
            <input type="text" placeholder="Project name" id="project-name-input">
            <button id="create-project-btn">Create Project</button>
            <button id="dismiss-project-btn">Continue Chat</button>
        </div>
    `;
    
    chatBox.appendChild(conversionDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Auto-focus the input field
    setTimeout(() => {
        const inputField = document.getElementById('project-name-input');
        if (inputField) inputField.focus();
    }, 100);
    
    // Add event listener to dismiss button
    document.getElementById('dismiss-project-btn').addEventListener('click', () => {
        conversionDiv.remove();
    });
    
    // Add event listener to create project button
    document.getElementById('create-project-btn').addEventListener('click', () => {
        const projectName = document.getElementById('project-name-input').value.trim();
        if (!projectName) {
            alert('Please enter a project name');
            return;
        }
        
        const createBtn = document.getElementById('create-project-btn');
        createBtn.textContent = 'Creating...';
        createBtn.disabled = true;
        
        // Determine correct API endpoint
        let apiUrl = '/api/projects/create-from-conversation';
        if (window.location.port === '52952') {
            apiUrl = '/api/projects/create-from-conversation';
        } else {
            apiUrl = 'http://127.0.0.1:52952/api/projects/create-from-conversation';
        }
        
        // Save current conversation to ensure all messages are preserved
        localStorage.setItem(`minerva_conversation_${conversationId}_name`, projectName);
        
        fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: conversationId,
                project_name: projectName,
                include_memory: true // Ensure all conversation memory is included
            })
        })
        .then(response => {
            if (!response.ok) throw new Error(`Failed to create project: ${response.status}`);
            return response.json();
        })
        .then(data => {
            displayMessage(`Successfully created project "${projectName}". Redirecting...`, 'system');
            
            if (data.project_url) {
                setTimeout(() => {
                    window.location.href = data.project_url;
                }, 1500);
            } else if (data.id || data.project_id) {
                // If no URL was provided but we have a project ID, construct a URL
                const projectId = data.id || data.project_id;
                setTimeout(() => {
                    window.location.href = `/project/${projectId}`;
                }, 1500);
            }
        })
        .catch(error => {
            console.error('Error creating project:', error);
            createBtn.textContent = 'Create Project';
            createBtn.disabled = false;
            displayMessage(`Failed to create project: ${error.message}. Please try again.`, 'system');
        });
    });
}
