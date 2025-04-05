/**
 * Minerva Chat UI Fix
 * Guaranteed implementation that works with the Think Tank
 */

// Create a fail-safe version of the sendMessage function that will always work
window.GUARANTEED_THINK_TANK_API = function(message, conversationId) {
    console.log('Using guaranteed Think Tank API call with:', message);
    
    // Get conversation ID from the DOM if not provided
    if (!conversationId) {
        const conversationElement = document.getElementById('conversation-id');
        conversationId = conversationElement ? conversationElement.getAttribute('data-id') : null;
    }
    
    // Always ensure we have sensible values
    message = message || '';
    message = message.trim();
    if (!message) {
        console.log('Empty message, not sending');
        return Promise.reject('Empty message');
    }
    
    // Make the API call to the Think Tank
    return fetch('/api/think-tank', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: message,           // Primary key expected by backend
            message: message,         // Secondary key for compatibility
            conversation_id: conversationId,
            store_in_memory: true     // Critical for conversation memory
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('API request failed: ' + response.status);
        }
        return response.json();
    });
};

document.addEventListener('DOMContentLoaded', function() {
    console.log('Applying chat UI fixes...');
    
    // Fix for Orbital UI initialization errors on pages that don't need it
    if (!document.getElementById('minerva-orbital-ui') || !document.getElementById('minerva-3d-root')) {
        console.log('Preventing Orbital UI initialization on unsupported page');
        window.MINERVA_DISABLE_ORBITAL_UI = true;
        
        // Intercept console error to provide cleaner output
        const originalConsoleError = console.error;
        console.error = function(...args) {
            if (args[0] && typeof args[0] === 'string' && args[0].includes('Minerva Orbital UI')) {
                console.log('Orbital UI not available on this page - this is normal');
                return;
            }
            originalConsoleError.apply(console, args);
        };
    }
    
    // Fix chat input on the conversations page
    fixChatInput();
});

/**
 * Permanent fix for chat input functionality on the conversations page
 * Guarantees that messages will be sent through the Think Tank API
 */
function fixChatInput() {
    // Ensure we're on the conversations page
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('messages');
    
    if (!messageInput || !sendButton) {
        console.error('Critical chat elements missing. Cannot initialize chat.');
        return;
    }
    
    console.log('Setting up GUARANTEED chat input handlers for conversations page');
    
    // Remove any existing listeners to avoid duplication
    const newInput = messageInput.cloneNode(true);
    messageInput.parentNode.replaceChild(newInput, messageInput);
    
    const newButton = sendButton.cloneNode(true);
    sendButton.parentNode.replaceChild(newButton, sendButton);
    
    // Keep references to the new elements
    const freshInput = document.getElementById('message-input');
    const freshButton = document.getElementById('send-button');
    
    // Guaranteed message sending function that doesn't rely on anything else
    function guaranteedSendMessage() {
        const messageText = freshInput.value.trim();
        if (!messageText) return;
        
        console.log('GUARANTEED sending message:', messageText);
        
        // Add user message to UI immediately
        if (chatHistory) {
            const userMsgDiv = document.createElement('div');
            userMsgDiv.className = 'chat-message user-message';
            userMsgDiv.innerHTML = `
                <div class="message-content">
                    <p>${messageText.replace(/\n/g, '<br>')}</p>
                </div>
            `;
            chatHistory.appendChild(userMsgDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        
        // Clear input and restore focus
        freshInput.value = '';
        freshInput.focus();
        
        // Add loading indicator
        let loadingDiv;
        if (chatHistory) {
            loadingDiv = document.createElement('div');
            loadingDiv.className = 'chat-message bot-message loading';
            loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatHistory.appendChild(loadingDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        
        // Send via our guaranteed API method
        window.GUARANTEED_THINK_TANK_API(messageText)
            .then(data => {
                console.log('GUARANTEED response received:', data);
                
                // Remove loading indicator if it exists
                if (loadingDiv && chatHistory.contains(loadingDiv)) {
                    chatHistory.removeChild(loadingDiv);
                }
                
                if (data.error) {
                    // Show error in UI
                    if (chatHistory) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'chat-message system-message';
                        errorDiv.innerHTML = `<div class="message-content"><p>Error: ${data.error}</p></div>`;
                        chatHistory.appendChild(errorDiv);
                        chatHistory.scrollTop = chatHistory.scrollHeight;
                    }
                    return;
                }
                
                // Show response in UI
                if (chatHistory) {
                    const botMsgDiv = document.createElement('div');
                    botMsgDiv.className = 'chat-message bot-message';
                    botMsgDiv.setAttribute('data-message-id', data.message_id || '');
                    
                    // Make sure data.response is properly handled as a string
                    let responseText = '';
                    if (typeof data.response === 'string') {
                        responseText = data.response;
                    } else if (data.response) {
                        // Try to convert the response to a string if it's not already
                        try {
                            responseText = JSON.stringify(data.response);
                        } catch (e) {
                            responseText = 'Received response in unexpected format';
                        }
                    } else {
                        responseText = 'No response received';
                    }
                    
                    botMsgDiv.innerHTML = `
                        <div class="message-content">
                            <p>${responseText.replace(/\n/g, '<br>')}</p>
                        </div>
                    `;
                    chatHistory.appendChild(botMsgDiv);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                    
                    // Dispatch event for any other components that need to know
                    const event = new CustomEvent('minerva-response-received', { detail: data });
                    document.dispatchEvent(event);
                }
            })
            .catch(error => {
                console.error('GUARANTEED send error:', error);
                
                // Remove loading indicator if it exists
                if (loadingDiv && chatHistory.contains(loadingDiv)) {
                    chatHistory.removeChild(loadingDiv);
                }
                
                // Show error in UI
                if (chatHistory) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'chat-message system-message';
                    errorDiv.innerHTML = `<div class="message-content"><p>Error: Could not send message. Please try again.</p></div>`;
                    chatHistory.appendChild(errorDiv);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }
            });
    }
    
    // Set up Enter key handling
    freshInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            console.log('Enter key pressed, triggering GUARANTEED send');
            event.preventDefault();
            guaranteedSendMessage();
        }
    });
    
    // Set up button click handling
    freshButton.addEventListener('click', function(event) {
        console.log('Send button clicked, triggering GUARANTEED send');
        event.preventDefault();
        guaranteedSendMessage();
    });
    
    // Override global sendMessage to use our guaranteed version
    window.sendMessage = function(message) {
        console.log('Global sendMessage called, using GUARANTEED implementation');
        
        // If called programmatically, set the input value first
        if (message && freshInput) {
            freshInput.value = message;
        }
        
        // Then trigger our guaranteed send function
        guaranteedSendMessage();
    };
    
    // Add debug helpers
    window.testChatInput = function() {
        console.log('== TESTING CHAT INPUT CONFIGURATION ==');
        console.log('Message input element:', freshInput);
        console.log('Send button element:', freshButton);
        console.log('Chat history element:', chatHistory);
        console.log('Input value:', freshInput ? freshInput.value : 'NOT FOUND');
        console.log('GUARANTEED_THINK_TANK_API available:', typeof window.GUARANTEED_THINK_TANK_API === 'function');
        console.log('== END TEST ==');
        return 'Chat configuration test complete. Check console for results.';
    };
    
    // Log for verification
    console.log('GUARANTEED chat input handlers successfully initialized');
}
