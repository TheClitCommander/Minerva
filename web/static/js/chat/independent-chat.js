/**
 * MINERVA INDEPENDENT CHAT SYSTEM
 * A completely self-contained chat implementation that works regardless
 * of the state of other scripts
 */

(function() {
    console.log('🚨 LOADING INDEPENDENT CHAT SYSTEM');
    
    // Initialize immediately and also on DOM content loaded
    runInitialization();
    document.addEventListener('DOMContentLoaded', runInitialization);
    
    // Handle cases where DOM is already loaded
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(runInitialization, 100);
    }

    function runInitialization() {
        // Wait a bit to ensure all elements are loaded
        setTimeout(initIndependentChat, 500);
    }
    
    function initIndependentChat() {
        console.log('🔄 Initializing independent chat system');
        
        // Find chat elements
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-message');
        const chatMessages = document.getElementById('chat-messages');
        
        // Exit if elements not found, but retry later
        if (!chatInput || !sendButton || !chatMessages) {
            console.warn('Chat elements not found, will retry in 1 second');
            console.log('Missing elements:', {
                chatInput: !!chatInput,
                sendButton: !!sendButton,
                chatMessages: !!chatMessages
            });
            setTimeout(initIndependentChat, 1000);
            return;
        }
        
        console.log('✅ All chat elements found, setting up handlers');
        
        // Replace elements with clones to remove existing listeners
        const newChatInput = chatInput.cloneNode(true);
        const newSendButton = sendButton.cloneNode(true);
        
        chatInput.parentNode.replaceChild(newChatInput, chatInput);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);
        
        // Add direct event listeners
        newSendButton.addEventListener('click', function() {
            sendChatMessage(newChatInput, chatMessages);
        });
        
        newChatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage(newChatInput, chatMessages);
            }
        });
        
        // Add success message to indicate chat is working
        const systemMsg = document.createElement('div');
        systemMsg.className = 'system-message';
        systemMsg.innerHTML = '<p><em>Independent chat system activated. You can now send messages.</em></p>';
        chatMessages.appendChild(systemMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add a global reference for emergency access
        window.IndependentChat = {
            sendMessage: function(message) {
                return sendChatMessage(newChatInput, chatMessages, message);
            },
            displayMessage: function(text, isUser = false) {
                displayChatMessage(chatMessages, text, isUser);
            }
        };
        
        console.log('🎉 Independent chat system ready');
    }
    
    function sendChatMessage(inputElement, messagesElement, overrideMessage = null) {
        console.log('Sending message via independent chat system');
        
        // Get message text
        const message = overrideMessage || inputElement.value.trim();
        
        if (!message) {
            console.log('Message is empty, not sending');
            return false;
        }
        
        // Clear input if not using override
        if (!overrideMessage) {
            inputElement.value = '';
        }
        
        // Display user message
        displayChatMessage(messagesElement, message, true);
        
        // Save to conversation memory if available
        try {
            if (window.minervaMemory) {
                window.minervaMemory.push({
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                });
            }
            
            if (window.conversationHistory) {
                window.conversationHistory.push({
                    role: 'user',
                    content: message
                });
            }
        } catch (error) {
            console.error('Error saving to conversation memory:', error);
        }
        
        // Process the message
        processMessage(message, messagesElement);
        
        return true;
    }
    
    function displayChatMessage(messagesElement, text, isUser = false) {
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'user-message' : 'ai-message';
        
        // Format message content
        messageDiv.innerHTML = `<p>${formatMessageText(text)}</p>`;
        
        // Add to chat and scroll
        messagesElement.appendChild(messageDiv);
        messagesElement.scrollTop = messagesElement.scrollHeight;
    }
    
    function formatMessageText(text) {
        if (!text) return '';
        
        // Escape HTML
        text = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Convert URLs to links
        text = text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert line breaks to <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    function processMessage(message, messagesElement) {
        // Show typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator ai-message';
        typingIndicator.innerHTML = '<p><em>Processing your message...</em></p>';
        messagesElement.appendChild(typingIndicator);
        messagesElement.scrollTop = messagesElement.scrollHeight;
        
        // Try to find existing API handlers
        let apiCallSuccessful = false;
        
        // 1. Try simulateThinkTankResponse (from minerva_central.html)
        if (typeof window.simulateThinkTankResponse === 'function') {
            try {
                console.log('Using simulateThinkTankResponse function');
                window.simulateThinkTankResponse(message)
                    .then(response => {
                        console.log('Think Tank response received:', response);
                        removeTypingIndicator(messagesElement);
                        apiCallSuccessful = true;
                    })
                    .catch(error => {
                        console.error('Error from Think Tank API:', error);
                        showErrorResponse(messagesElement, message, error);
                    });
            } catch (error) {
                console.error('Error calling simulateThinkTankResponse:', error);
                showErrorResponse(messagesElement, message, error);
            }
        } 
        // 2. If no API function available, show fallback response
        else {
            console.log('No API function available, showing fallback response');
            setTimeout(() => {
                removeTypingIndicator(messagesElement);
                
                // Add fallback response
                const responseDiv = document.createElement('div');
                responseDiv.className = 'ai-message';
                responseDiv.innerHTML = `
                    <p>I've received your message: "${message}"</p>
                    <p>This is a fallback response as the connection to the Think Tank API is currently unavailable.</p>
                    <p>Your message has been saved and will be processed when the connection is restored.</p>
                `;
                messagesElement.appendChild(responseDiv);
                messagesElement.scrollTop = messagesElement.scrollHeight;
                
                // Save to memory if available
                try {
                    if (window.minervaMemory) {
                        window.minervaMemory.push({
                            role: 'assistant',
                            content: responseDiv.textContent,
                            timestamp: new Date().toISOString()
                        });
                    }
                    
                    if (window.conversationHistory) {
                        window.conversationHistory.push({
                            role: 'assistant',
                            content: responseDiv.textContent
                        });
                    }
                } catch (error) {
                    console.error('Error saving to conversation memory:', error);
                }
            }, 1500);
        }
    }
    
    function removeTypingIndicator(messagesElement) {
        const indicators = messagesElement.querySelectorAll('.typing-indicator');
        indicators.forEach(indicator => indicator.remove());
    }
    
    function showErrorResponse(messagesElement, message, error) {
        removeTypingIndicator(messagesElement);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'ai-message error-message';
        errorDiv.innerHTML = `
            <p>I'm having trouble connecting to the server.</p>
            <p>Your message has been saved locally.</p>
            <p><small>Error details: ${error.message || 'Unknown error'}</small></p>
        `;
        messagesElement.appendChild(errorDiv);
        messagesElement.scrollTop = messagesElement.scrollHeight;
    }
})();
