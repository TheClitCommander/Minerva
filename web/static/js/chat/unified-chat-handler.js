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
            chatMessages: document.getElementById('chat-history'), // Updated to match actual DOM ID
            complete: false
        };
        
        // Log found elements to help with debugging
        console.log('Chat elements found:', {
            chatInput: !!elements.chatInput,
            sendButton: !!elements.sendButton,
            chatMessages: !!elements.chatMessages
        });
        
        elements.complete = !!(elements.chatInput && elements.sendButton && elements.chatMessages);
        
        // If not all elements are found, try alternate element IDs (for backward compatibility)
        if (!elements.complete) {
            console.log('Not all chat elements found, trying alternates...');
            
            // Try alternate IDs for chat-history
            if (!elements.chatMessages) {
                elements.chatMessages = document.getElementById('chat-messages') || 
                                        document.querySelector('.chat-history') ||
                                        document.querySelector('.chat-messages');
                console.log('Alternate chat messages container found:', !!elements.chatMessages);
            }
            
            // Try alternate IDs for send button
            if (!elements.sendButton) {
                elements.sendButton = document.querySelector('#chat-input-container button') ||
                                    document.querySelector('.send-button') ||
                                    document.querySelector('button[type="submit"]');
                console.log('Alternate send button found:', !!elements.sendButton);
            }
            
            // Update completion status
            elements.complete = !!(elements.chatInput && elements.sendButton && elements.chatMessages);
        }
        
        return elements;
    }
    
    // Set up chat handlers
    function setupChatHandlers(elements) {
        // CRITICAL FIX: Force removal of all duplicate welcome messages (Rule #17)
        const welcomeMessages = elements.chatMessages.querySelectorAll('.message.system.info');
        if (welcomeMessages.length > 0) {
            console.log(`Found ${welcomeMessages.length} welcome messages, removing all but the first (Rule #17)`);
            // Keep only the first welcome message
            for (let i = 1; i < welcomeMessages.length; i++) {
                welcomeMessages[i].parentNode.removeChild(welcomeMessages[i]);
            }
        }
        
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
        
        // Re-check for welcome messages after removing duplicates
        const existingWelcomes = elements.chatMessages.querySelectorAll('.message.system.info');
        if (existingWelcomes.length === 0) {
            console.log('No welcome message found, adding one');
            // Only add if no welcome message exists
            displaySystemMessage(elements.chatMessages, 'Welcome to Minerva Assistant. I\'m connected to the Think Tank API and ready to help.', 'info');
        } else {
            console.log('Using existing welcome message, not adding another one');
        }
        
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
        
        // Create metadata object with timestamp and source info (Rule #19)
        const metadata = {
            timestamp: new Date().toISOString(),
            source: 'direct',
            synced: false,
            projectContext: getCurrentProjectContext()
        };
        
        // Generate unique ID for the message (Rule #18)
        metadata.id = generateMessageId('user');
        
        // Display user message with metadata
        displayUserMessage(elements.chatMessages, message, metadata);
        
        // Save to conversation memory systems with enhanced metadata
        saveToConversationMemory('user', message, null, metadata);
        
        // Force the UI to update and show the message immediately
        setTimeout(() => {
            // Try all available API methods to send the message
            const apiSent = tryAllApiMethods(message, elements.chatMessages, metadata);
            
            // If no API method worked, show fallback response
            if (!apiSent) {
                showFallbackResponse(elements.chatMessages, message, metadata);
            }
        }, 100); // Small delay to ensure user message renders first
        
        return true;
    }
    
    // Send the message using a single, reliable API method
    function tryAllApiMethods(message, chatMessages, metadata) {
        console.log('Sending message via unified API method...');
        
        // Check API availability - this is critical for allowing fallback to work
        const apiAvailable = window.thinkTankApiStatus?.available === true;
        
        // If API is known to be down, skip the API attempts and immediately use fallback
        if (!apiAvailable) {
            console.warn('API is known to be offline, using fallback immediately (Rule #4)');
            return false; // This will trigger the fallback response
        }
        
        // Display typing indicator
        const typingIndicator = displayTypingIndicator(chatMessages);
        
        // PRIORITY 1: Use minervaAPI if available (preferred method)
        if (window.minervaAPI && typeof window.minervaAPI.sendMessage === 'function') {
            try {
                console.log('Using minervaAPI.sendMessage');
                
                // Create a timeout to ensure we don't wait forever
                let responseReceived = false;
                const timeoutPromise = new Promise((resolve) => {
                    setTimeout(() => {
                        if (!responseReceived) {
                            console.warn('API response timeout exceeded, using fallback (Rule #4)');
                            removeTypingIndicator(chatMessages, typingIndicator);
                            resolve({ timedOut: true });
                        }
                    }, 5000); // 5 second timeout
                });
                
                // Race the API call against the timeout
                Promise.race([
                    window.minervaAPI.sendMessage(message),
                    timeoutPromise
                ])
                .then(response => {
                    responseReceived = true;
                    console.log('Response received:', response);
                    removeTypingIndicator(chatMessages, typingIndicator);
                    
                    // Handle timeout case
                    if (response && response.timedOut) {
                        // This will be handled by the caller with showFallbackResponse
                        return;
                    }
                    
                    // Display the response
                    if (response && response.message) {
                        displayBotResponse(chatMessages, response.message, response.model_info, {
                            ...metadata,
                            id: generateMessageId('assistant'),
                            source: 'ThinkTank',
                            timestamp: new Date().toISOString()
                        });
                        return true;
                    } else if (response && response.error) {
                        showErrorMessage(chatMessages, `API Error: ${response.error}`);
                        return false;
                    } else {
                        displayBotResponse(chatMessages, 'I received your message but had trouble generating a response.', null, {
                            id: generateMessageId('assistant'),
                            source: 'fallback',
                            timestamp: new Date().toISOString()
                        });
                        return true;
                    }
                })
                .catch(error => {
                    console.error('Error from minervaAPI:', error);
                    removeTypingIndicator(chatMessages, typingIndicator);
                    showErrorMessage(chatMessages, 'Failed to get response from server: ' + error.message);
                    return false; // Ensure fallback happens on error
                });
                
                return true;
            } catch (error) {
                console.error('Error using minervaAPI:', error);
                removeTypingIndicator(chatMessages, typingIndicator);
                return false; // Ensure fallback happens on error
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
    function displayUserMessage(chatMessages, message, metadata = {}) {
        // Generate a unique message ID if not provided (Rule #17 & #18)
        const messageId = metadata.id || generateMessageId('user');
        
        // Check if message with this ID already exists (Rule #17)
        if (document.getElementById(messageId)) {
            console.log(`Message with ID ${messageId} already exists, not rendering duplicate`);
            return;
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.id = messageId; // Set ID for duplicate prevention (Rule #17)
        
        // Add data attributes for metadata (Rule #19)
        messageElement.dataset.timestamp = metadata.timestamp || new Date().toISOString();
        messageElement.dataset.source = metadata.source || 'direct';
        if (metadata.projectContext) messageElement.dataset.projectContext = metadata.projectContext;
        
        // Build message HTML
        messageElement.innerHTML = `<p>${formatMessage(message)}</p>`;
        
        // Add time indicator if not present
        if (!messageElement.querySelector('.message-time')) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = formatTimestamp(metadata.timestamp || new Date());
            messageElement.appendChild(timeDiv);
        }
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
        
        // Auto-generate title if this is one of the first 3 messages (Rule #13)
        attemptTitleGeneration();
    }
    
    function displayBotResponse(chatMessages, message, modelInfo = null, metadata = {}) {
        // Generate a unique message ID if not provided (Rule #17 & #18)
        const messageId = metadata.id || generateMessageId('assistant');
        
        // Check if message with this ID already exists (Rule #17)
        if (document.getElementById(messageId)) {
            console.log(`Message with ID ${messageId} already exists, not rendering duplicate`);
            return;
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = 'ai-message';
        messageElement.id = messageId; // Set ID for duplicate prevention (Rule #17)
        
        // Add data attributes for metadata (Rule #19)
        messageElement.dataset.timestamp = metadata.timestamp || new Date().toISOString();
        messageElement.dataset.source = metadata.source || (modelInfo ? 'ThinkTank' : 'fallback');
        messageElement.dataset.model = (modelInfo?.model || metadata.model || 'minerva-core');
        messageElement.dataset.synced = (metadata.synced === true).toString();
        if (metadata.projectContext) messageElement.dataset.projectContext = metadata.projectContext;
        
        // Format model info display
        let modelInfoHtml = '';
        if (modelInfo || metadata.model) {
            const modelName = modelInfo?.model || metadata.model || 'Minerva Core';
            modelInfoHtml = `<div class="model-info">${modelName}</div>`;
        }
        
        // Add sync status indicator if needed
        let syncStatusHtml = '';
        if (metadata.source !== 'fallback' && metadata.synced === false) {
            syncStatusHtml = `<div class="sync-status pending">Pending Sync</div>`;
        }
        
        messageElement.innerHTML = `<p>${formatMessage(message)}</p>${modelInfoHtml}${syncStatusHtml}`;
        
        // Add time indicator if not present
        if (!messageElement.querySelector('.message-time')) {
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = formatTimestamp(metadata.timestamp || new Date());
            messageElement.appendChild(timeDiv);
        }
        
        chatMessages.appendChild(messageElement);
        scrollToBottom(chatMessages);
        
        // Save to conversation memory - already done by caller in most cases
        if (metadata.skipMemorySave !== true) {
            saveToConversationMemory('assistant', message, modelInfo, metadata);
        }
        
        // Auto-generate title if this is one of the first 3 messages (Rule #13)
        attemptTitleGeneration();
    }
    
    function displaySystemMessage(chatMessages, message, type = 'info') {
        // Generate a unique ID for this message to prevent duplicates (Rule #17)
        const messageId = `system-${type}-${Date.now()}`;
        
        // SUPER AGGRESSIVE check for duplicate welcome messages
        if (type === 'info' && message.includes('Welcome to Minerva')) {
            // Check if we already have a welcome message
            const existingWelcomes = chatMessages.querySelectorAll('.message.system.info, .system-message.info');
            if (existingWelcomes.length > 0) {
                console.log('Welcome message already exists, not adding another duplicate (Rule #17)');
                return; // Don't add another welcome message
            }
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message system ${type}`;
        messageElement.dataset.messageId = messageId;
        
        // Add formatted message content with better structure
        messageElement.innerHTML = `<div class="message-content">
            <div class="message-text">${formatMessage(message)}</div>
            <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
        </div>`;
        
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
    
    function showFallbackResponse(chatMessages, userMessage, userMetadata = {}) {
        console.log('Showing fallback response per Rule #4');
        
        // Add a slight delay to simulate processing
        setTimeout(() => {
            // Generate a response based on the user message
            let response;
            
            // Check if the message looks like a greeting
            if (/^(hi|hello|hey|greetings|howdy)/i.test(userMessage.trim())) {
                response = `Hello! I'm operating in offline mode right now, but I can still help with basic responses. The Think Tank API appears to be unavailable, but your messages are being saved locally and will sync when connection is restored.

What would you like to know about?`;
            }
            // Check if it's a question
            else if (/\?$/.test(userMessage.trim())) {
                response = `Thanks for your question. I'm currently working in offline mode as the Think Tank API is unavailable.

Your question has been saved and will be processed when the connection is restored. In the meantime, please try refreshing the page or checking your network connection.`;
            }
            // Default response
            else {
                response = `I've received your message: "${userMessage}"

I'm currently in offline mode as the Think Tank API is unavailable. Your message has been saved locally and will be processed when the connection is restored.

Is there anything specific you'd like me to help with once we're back online?`;
            }
            
            // Create metadata for fallback response (Rule #19)
            const metadata = {
                id: generateMessageId('assistant'),
                timestamp: new Date().toISOString(),
                source: 'fallback',
                model: 'fallback-system',
                synced: false,
                projectContext: userMetadata.projectContext || getCurrentProjectContext()
            };
            
            // Save to conversation memory
            saveToConversationMemory('assistant', response, { model: 'fallback-system' }, metadata);
            
            // Display the response
            displayBotResponse(chatMessages, response, null, metadata);
        }, 1000);
    }
    
    function showErrorMessage(chatMessages, errorObj) {
        // Generate a unique ID for this message
        const messageId = `error-${Date.now()}`;
        
        // Create a properly formatted error object
        let errorMessage = '';
        let errorDetails = {};
        
        // Handle different types of error inputs
        if (typeof errorObj === 'string') {
            errorMessage = errorObj;
        } else if (errorObj instanceof Error) {
            errorMessage = errorObj.message || 'An unknown error occurred';
            errorDetails = {
                name: errorObj.name,
                stack: errorObj.stack
            };
        } else if (errorObj && typeof errorObj === 'object') {
            // Already an error object
            errorMessage = errorObj.message || JSON.stringify(errorObj);
            errorDetails = errorObj;
        } else {
            errorMessage = 'An unknown error occurred';
        }
        
        console.log('Showing error message:', errorMessage, errorDetails);
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message system error';
        messageElement.dataset.messageId = messageId;
        
        // Check if it's a network error and provide more user-friendly message
        if (errorMessage.includes('Failed to fetch') || 
            errorMessage.includes('NetworkError') || 
            errorMessage.includes('Error connecting to Think Tank API')) {
            
            messageElement.innerHTML = `<div class="message-content">
                <div class="message-text">Think Tank API is currently offline. Your messages are being saved locally and will sync when connection is restored.</div>
                <div class="message-note">Using fallback mode per Rule #4</div>
                <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>`;
            messageElement.className = 'message system warning';
        } else {
            // Format a more user-friendly error message
            const userFriendlyMessage = errorMessage
                .replace('Error: Error:', 'Error:')
                .replace('Error connecting to Think Tank API:', '')
                .trim();
                
            messageElement.innerHTML = `<div class="message-content">
                <div class="message-text">Error: ${formatMessage(userFriendlyMessage || 'An unknown error occurred')}</div>
                <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
            </div>`;
        }
        
        // Check if we already have this error message to prevent duplicates (Rule #17)
        const existingErrors = chatMessages.querySelectorAll('.message.system.error, .message.system.warning');
        let isDuplicate = false;
        
        existingErrors.forEach(existingError => {
            const existingText = existingError.textContent.trim();
            const newText = messageElement.textContent.trim();
            
            if (existingText === newText) {
                isDuplicate = true;
                // Update timestamp on existing error instead of adding duplicate
                const timeElement = existingError.querySelector('.message-time');
                if (timeElement) {
                    timeElement.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                }
            }
        });
        
        if (!isDuplicate) {
            chatMessages.appendChild(messageElement);
            scrollToBottom(chatMessages);
        }
    }
    
    // Utility functions
    function formatMessage(text) {
        if (!text) return '[No message]';
        
        // Handle non-string types by converting to string
        if (typeof text !== 'string') {
            try {
                // If it's an object with properties, stringify it
                if (typeof text === 'object' && text !== null) {
                    // Check if it's an empty object
                    if (Object.keys(text).length === 0) {
                        return 'The API is currently offline. Please try again later.';
                    } else if (text.message) {
                        text = text.message;
                    } else {
                        text = JSON.stringify(text);
                    }
                } else {
                    text = String(text);
                }
            } catch (e) {
                console.warn('Error formatting message:', e);
                text = String(text);
            }
        }
        
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
    
    // Function to fix duplicate messages and improve error formatting (Rules #10, #17)
    function fixChatHistoryElements(chatHistory) {
        if (!chatHistory) return;
        
        console.log('Fixing chat history elements (Rule #17 - prevent duplicates)');
        
        // Find welcome messages and remove duplicates
        const welcomeMessages = chatHistory.querySelectorAll('.message.system.info');
        if (welcomeMessages.length > 1) {
            console.log(`Found ${welcomeMessages.length} welcome messages, removing duplicates (Rule #17)`);
            // Keep only the first welcome message
            for (let i = 1; i < welcomeMessages.length; i++) {
                welcomeMessages[i].remove();
            }
        }
        
        // Find user messages and deduplicate based on content
        const userMessages = chatHistory.querySelectorAll('.message.user-message');
        const userMessageMap = new Map(); // Map to track unique content
        
        userMessages.forEach(message => {
            const messageText = message.querySelector('.message-text')?.textContent || '';
            const messageKey = messageText.trim();
            
            if (userMessageMap.has(messageKey)) {
                console.log(`Found duplicate user message: "${messageKey.substring(0, 20)}...", removing`);
                message.remove();
            } else {
                userMessageMap.set(messageKey, message);
            }
        });
        
        // Improve error messages (Rule #10)
        const errorMessages = chatHistory.querySelectorAll('.message.system.error');
        errorMessages.forEach(message => {
            if (message.textContent.includes('Failed to fetch')) {
                message.innerHTML = `<div class="message-content">
                    <div class="message-text">Think Tank API is currently offline. Your messages are being saved locally and will sync when connection is restored.</div>
                    <div class="message-note">Using fallback mode per Rule #4</div>
                </div>`;
                message.className = 'message system warning';
            }
        });
        
        // Improve current messages with proper data attributes (Rule #18, Rule #19)
        const allMessages = chatHistory.querySelectorAll('.message');
        allMessages.forEach((message, index) => {
            // Add unique ID if missing
            if (!message.id && !message.dataset.messageId) {
                const type = message.classList.contains('user-message') ? 'user' : 
                          message.classList.contains('ai-message') ? 'assistant' : 'system';
                message.dataset.messageId = `legacy-${type}-${index}-${Date.now()}`;
            }
            
            // Add timestamp if missing
            if (!message.dataset.timestamp) {
                message.dataset.timestamp = new Date().toISOString();
            }
        });
    }
    
    function saveToConversationMemory(role, content, modelInfo = null, metadata = {}) {
        try {
            if (!content) {
                console.warn('Attempted to save empty message to conversation memory');
                return;
            }
            
            console.log(`Saving ${role} message to conversation memory:`, content.substring(0, 30) + '...');
            
            // Generate a unique ID if not present (Rule #18)
            const messageId = metadata.id || generateMessageId(role);
            
            // Prepare message object with expanded metadata format (Rule #19)
            const messageObject = {
                id: messageId,
                role: role,
                content: content,
                timestamp: metadata.timestamp || new Date().toISOString(),
                model: modelInfo?.model || metadata.model || 'minerva-core',
                source: metadata.source || (modelInfo ? 'ThinkTank' : 'fallback'),
                synced: metadata.synced === true, // Default to false (Rule #20)
                projectContext: metadata.projectContext || getCurrentProjectContext()
            };
            
            // Add auto-generated title flag if present (Rule #13)
            if (metadata.autoGeneratedTitle === true) {
                messageObject.autoGeneratedTitle = true;
            }
            
            // Add model info if provided
            if (modelInfo) {
                messageObject.model_info = modelInfo;
            }
            
            // PRIORITY 1: Use the enhanced conversation storage (primary system - Rule #2)
            if (window.enhancedConversationStorage) {
                console.log('Using enhanced conversation storage system');
                
                // Initialize messages array if not exist
                if (!window.enhancedConversationStorage.messages) {
                    window.enhancedConversationStorage.messages = [];
                }
                
                // Add message
                window.enhancedConversationStorage.messages.push(messageObject);
                
                // If we have a custom method, call it too
                if (typeof window.enhancedConversationStorage.addMessageToConversation === 'function') {
                    window.enhancedConversationStorage.addMessageToConversation(messageObject);
                }
                
                // Attempt to generate title if needed (Rule #13)
                if (window.enhancedConversationStorage.messages.length <= 3 && !window.enhancedConversationStorage.title) {
                    attemptTitleGeneration();
                }
                
                return messageObject;
            }
            
            // FALLBACK 1: Use the integrated saveToConversationMemory global function
            if (typeof window.saveToConversationMemory === 'function') {
                console.log('Using global saveToConversationMemory function');
                window.saveToConversationMemory(role, content, modelInfo);
                return messageObject;
            }
            
            // FALLBACK 2: Use minervaMemory legacy array if it exists
            if (window.minervaMemory && Array.isArray(window.minervaMemory)) {
                console.log('Using legacy minervaMemory array');
                window.minervaMemory.push(messageObject);
                return messageObject;
            }
            
            // FALLBACK 3: Create minervaMemory if it doesn't exist
            if (!window.minervaMemory) {
                console.log('Creating new minervaMemory array');
                window.minervaMemory = [messageObject];
                return messageObject;
            }
            
            console.log('Message saved to conversation memory');
            return messageObject;
        } catch (error) {
            console.error('Error saving to conversation memory:', error);
            return null;
        }
    }
    
    // Utility functions for enhanced chat system (Rules #13, #17, #18, #19)
    
    // Generate unique message ID (Rule #18)
    function generateMessageId(role) {
        return `chat-${role}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
    }
    
    // Format timestamp for display
    function formatTimestamp(timestamp) {
        const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    // Get current project context
    function getCurrentProjectContext() {
        // Try to get from URL or page context
        const projectName = window.currentProjectName || '';
        const projectId = window.currentProjectId || '';
        
        if (projectName || projectId) {
            return projectName || projectId;
        }
        
        // Try to infer from URL
        const projectMatch = window.location.pathname.match(/\/projects\/(\w+)/);
        return projectMatch ? projectMatch[1] : '';
    }
    
    // Auto-generate title from first messages (Rule #13)
    function attemptTitleGeneration() {
        // Only run if we have enhanced storage and no title yet
        if (!window.enhancedConversationStorage || 
            window.enhancedConversationStorage.title ||
            window.enhancedConversationStorage.autoGeneratedTitle === true) {
            return;
        }
        
        // Need at least 3 messages to generate a meaningful title
        const messages = window.enhancedConversationStorage.messages || [];
        if (messages.length < 3) {
            return;
        }
        
        console.log('Generating auto-title from first messages (Rule #13)');
        
        // Extract and combine first 3 messages for title generation
        const firstMessages = messages.slice(0, 3);
        let titleText = '';
        
        if (firstMessages[0] && firstMessages[0].content) {
            // Use first user message as primary title source
            const firstUserMessage = firstMessages.find(m => m.role === 'user');
            if (firstUserMessage) {
                // Extract first sentence or first 30 chars
                let titleBase = firstUserMessage.content;
                const firstSentenceMatch = titleBase.match(/^([^.!?\r\n]+[.!?])/); 
                
                if (firstSentenceMatch) {
                    titleText = firstSentenceMatch[1].trim();
                } else if (titleBase.length > 30) {
                    titleText = titleBase.substring(0, 30).trim() + '...';
                } else {
                    titleText = titleBase.trim();
                }
            }
        }
        
        // Fallback if no good title found
        if (!titleText || titleText.length < 5) {
            const dateStr = new Date().toLocaleDateString();
            titleText = `Conversation (${dateStr})`;
        }
        
        // Store the auto-generated title
        window.enhancedConversationStorage.title = titleText;
        window.enhancedConversationStorage.autoGeneratedTitle = true;
        
        // Update title in UI if needed
        const titleElements = document.querySelectorAll('.conversation-title, .chat-title');
        titleElements.forEach(el => {
            if (!el.dataset.userEdited) {
                el.textContent = titleText;
                el.dataset.autoGenerated = 'true';
            }
        });
        
        console.log('Auto-generated title:', titleText);
        
        // Notify any listeners about title change
        if (typeof window.onConversationTitleChanged === 'function') {
            window.onConversationTitleChanged(titleText, true);
        }
        
        return titleText;
    }
})();
