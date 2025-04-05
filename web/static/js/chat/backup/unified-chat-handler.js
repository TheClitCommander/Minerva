/**
 * MINERVA UNIFIED CHAT HANDLER
 * 
 * This script provides a robust, simplified chat implementation that works
 * regardless of the state of other scripts, while maintaining compatibility
 * with the conversation memory system and project context integration.
 */

(function() {
    // Initialize as soon as possible
    console.log('🔄 Initializing unified chat handler');
    
    // Constants
    const RETRY_INTERVAL = 500; // ms
    const MAX_RETRIES = 10;
    
    // State
    let retryCount = 0;
    let initialized = false;
    
    // Start initialization process
    initializeImmediately();
    document.addEventListener('DOMContentLoaded', initializeWhenReady);
    
    // Initialization functions
    function initializeImmediately() {
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            console.log('Document already interactive, initializing now');
            attemptInitialization();
        } else {
            console.log('Document not ready, will initialize on DOMContentLoaded');
        }
    }
    
    function initializeWhenReady() {
        console.log('DOMContentLoaded fired, initializing');
        attemptInitialization();
    }
    
    function attemptInitialization() {
        if (initialized) {
            console.log('Already initialized, skipping');
            return;
        }
        
        if (retryCount >= MAX_RETRIES) {
            console.error('Failed to initialize after maximum retries');
            return;
        }
        
        const chatElements = findChatElements();
        
        if (!chatElements.complete) {
            console.log(`Attempt ${retryCount + 1}/${MAX_RETRIES}: Chat elements not found, retrying in ${RETRY_INTERVAL}ms`);
            retryCount++;
            setTimeout(attemptInitialization, RETRY_INTERVAL);
            return;
        }
        
        // Elements found, initialize chat
        console.log('✅ Chat elements found, initializing chat functionality');
        setupChatHandlers(chatElements);
        initialized = true;
    }
    
    // Find all required chat elements
    function findChatElements() {
        const elements = {
            chatInput: document.getElementById('chat-input'),
            sendButton: document.getElementById('send-message'),
            chatMessages: document.getElementById('chat-messages'),
            complete: false
        };
        
        elements.complete = !!(elements.chatInput && elements.sendButton && elements.chatMessages);
        
        return elements;
    }
    
    // Set up chat handlers
    function setupChatHandlers(elements) {
        // Clear any existing event listeners by cloning elements
        try {
            const newSendButton = elements.sendButton.cloneNode(true);
            elements.sendButton.parentNode.replaceChild(newSendButton, elements.sendButton);
            elements.sendButton = newSendButton;
            
            const newChatInput = elements.chatInput.cloneNode(true);
            elements.chatInput.parentNode.replaceChild(newChatInput, elements.chatInput);
            elements.chatInput = newChatInput;
            
            console.log('Successfully replaced elements to clear existing handlers');
        } catch (error) {
            console.warn('Could not replace elements:', error);
            // Continue with original elements
        }
        
        // Add event listeners
        elements.sendButton.addEventListener('click', function() {
            handleSendMessage(elements);
        });
        
        elements.chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage(elements);
            }
        });
        
        // Add notification message
        displaySystemMessage(elements.chatMessages, 'Chat system initialized and ready', 'info');
        
        // Expose global functions for external access
        window.UnifiedChat = {
            sendMessage: function(message) {
                return handleSendMessage(elements, message);
            },
            displayMessage: function(message, isUser = false) {
                if (isUser) {
                    displayUserMessage(elements.chatMessages, message);
                } else {
                    displayBotResponse(elements.chatMessages, message);
                }
            }
        };
        
        console.log('Chat handlers initialized successfully');
    }
    
    // Handle sending a message
    function handleSendMessage(elements, overrideMessage = null) {
        const message = overrideMessage || elements.chatInput.value.trim();
        
        if (!message) {
            console.log('Empty message, not sending');
            return false;
        }
        
        console.log('Sending message:', message);
        
        // Clear input if not using override
        if (!overrideMessage) {
            elements.chatInput.value = '';
        }
        
        // Display user message
        displayUserMessage(elements.chatMessages, message);
        
        // Save to conversation memory systems
        saveToConversationMemory('user', message);
        
        // Try all available API methods to send the message
        const apiSent = tryAllApiMethods(message, elements.chatMessages);
        
        // If no API method worked, show fallback response
        if (!apiSent) {
            showFallbackResponse(elements.chatMessages, message);
        }
        
        return true;
    }
    
    // Send the message using a single, reliable API method
    function tryAllApiMethods(message, chatMessages) {
        console.log('Sending message via unified API method...');
        
        // Display typing indicator
        const typingIndicator = displayTypingIndicator(chatMessages);
        
        // PRIORITY 1: Use minervaAPI if available (preferred method)
        if (window.minervaAPI && typeof window.minervaAPI.sendMessage === 'function') {
            try {
                console.log('Using minervaAPI.sendMessage');
                window.minervaAPI.sendMessage(message)
                    .then(response => {
                        console.log('Response received from minervaAPI:', response);
                        removeTypingIndicator(chatMessages, typingIndicator);
                        
                        // Display the response
                        if (response && response.message) {
                            displayBotResponse(chatMessages, response.message, response.model_info);
                        } else if (response && response.error) {
                            showErrorMessage(chatMessages, `API Error: ${response.error}`);
                        } else {
                            displayBotResponse(chatMessages, 'I received your message but had trouble generating a response.');
                        }
                    })
                    .catch(error => {
                        console.error('Error from minervaAPI:', error);
                        removeTypingIndicator(chatMessages, typingIndicator);
                        showErrorMessage(chatMessages, 'Failed to get response from server: ' + error.message);
                    });
                return true;
            } catch (error) {
                console.error('Error using minervaAPI:', error);
            }
        }
        
        // FALLBACK 1: Use simulateThinkTankResponse (legacy method)
        if (typeof window.simulateThinkTankResponse === 'function') {
            try {
                console.log('Using simulateThinkTankResponse');
                window.simulateThinkTankResponse(message)
                    .then(response => {
                        console.log('Response received from simulateThinkTankResponse');
                        removeTypingIndicator(chatMessages, typingIndicator);
                    })
                    .catch(error => {
                        console.error('Error from simulateThinkTankResponse:', error);
                        removeTypingIndicator(chatMessages, typingIndicator);
                        showErrorMessage(chatMessages, 'Failed to get response from server: ' + error.message);
                    });
                return true;
            } catch (error) {
                console.error('Error calling simulateThinkTankResponse:', error);
                removeTypingIndicator(chatMessages, typingIndicator);
            }
        }
        
        // No API method worked - show fallback message
        console.log('No API method succeeded');
        removeTypingIndicator(chatMessages, typingIndicator);
        return false;
    }
    
    // Display functions
    function displayUserMessage(chatMessages, message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.innerHTML = `<p>${formatMessage(message)}</p>`;
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
    }
    
    function displayBotResponse(chatMessages, message, modelInfo = null) {
        const messageElement = document.createElement('div');
        messageElement.className = 'ai-message';
        
        let modelInfoHtml = '';
        if (modelInfo) {
            modelInfoHtml = `<div class="model-info">${JSON.stringify(modelInfo)}</div>`;
        }
        
        messageElement.innerHTML = `<p>${formatMessage(message)}</p>${modelInfoHtml}`;
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
        
        // Save to conversation memory
        saveToConversationMemory('assistant', message, modelInfo);
    }
    
    function displaySystemMessage(chatMessages, message, type = 'info') {
        const messageElement = document.createElement('div');
        messageElement.className = `system-message ${type}`;
        messageElement.innerHTML = `<p><em>${formatMessage(message)}</em></p>`;
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
    }
    
    function displayTypingIndicator(chatMessages) {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<p><em>Processing message...</em></p>';
        
        chatMessages.appendChild(indicator);
        scrollToBottom(chatMessages);
        
        return indicator;
    }
    
    function removeTypingIndicator(chatMessages, indicator) {
        if (indicator && indicator.parentNode === chatMessages) {
            chatMessages.removeChild(indicator);
        }
    }
    
    function showFallbackResponse(chatMessages, userMessage) {
        console.log('Showing fallback response');
        
        // Add a slight delay to simulate processing
        setTimeout(() => {
            const response = `I've received your message: "${userMessage}"

The server connection appears to be unavailable at the moment. Your message has been saved locally.

Please try refreshing the page or check your network connection.`;
            
            displayBotResponse(chatMessages, response);
        }, 1000);
    }
    
    function showErrorMessage(chatMessages, errorMessage) {
        const messageElement = document.createElement('div');
        messageElement.className = 'system-message error';
        messageElement.innerHTML = `<p><em>Error: ${formatMessage(errorMessage)}</em></p>`;
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
    }
    
    // Utility functions
    function formatMessage(text) {
        if (!text) return '';
        
        // Escape HTML
        text = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Handle URLs
        text = text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert line breaks to <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    function scrollToBottom(element) {
        element.scrollTop = element.scrollHeight;
    }
    
    function saveToConversationMemory(role, content, modelInfo = null) {
        try {
            if (!content) {
                console.warn('Attempted to save empty message to conversation memory');
                return;
            }
            
            console.log(`Saving ${role} message to conversation memory:`, content.substring(0, 30) + '...');
            
            // Prepare message object with consistent format
            const messageObject = {
                role: role,
                content: content,
                timestamp: new Date().toISOString(),
                model: modelInfo?.model || 'minerva-core'
            };
            
            // Add model info if provided
            if (modelInfo) {
                messageObject.model_info = modelInfo;
            }
            
            // PRIORITY 1: Use the enhanced conversation storage (primary system)
            if (window.enhancedConversationStorage) {
                console.log('Using enhanced conversation storage system');
                window.enhancedConversationStorage.addMessageToConversation(messageObject);
                return;
            }
            
            // FALLBACK 1: Use the integrated saveToConversationMemory global function
            if (typeof window.saveToConversationMemory === 'function') {
                console.log('Using global saveToConversationMemory function');
                window.saveToConversationMemory(role, content, modelInfo);
                return;
            }
            
            // FALLBACK 2: Use minervaMemory legacy array if it exists
            if (window.minervaMemory && Array.isArray(window.minervaMemory)) {
                console.log('Using legacy minervaMemory array');
                window.minervaMemory.push(messageObject);
                return;
            }
            
            // FALLBACK 3: Create minervaMemory if it doesn't exist
            if (!window.minervaMemory) {
                console.log('Creating new minervaMemory array');
                window.minervaMemory = [messageObject];
                return;
            }
            
            console.log('Message saved to conversation memory');
        } catch (error) {
            console.error('Error saving to conversation memory:', error);
        }
    }
})();
