/**
 * Minerva Chat Integration
 * Embeds the chat functionality directly into the Minerva UI
 * Supports both floating chat on homepage and project-specific panels
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("Initializing Minerva Chat Integration...");
    
    // Look for chat container with multiple possible IDs 
    let inputField = document.getElementById("minerva-chat-input");
    let sendButton = document.getElementById("minerva-send-btn");
    let chatMessages = document.getElementById("minerva-chat-messages") || 
                    document.getElementById("chat-messages") || 
                    document.querySelector(".minerva-chat-messages");
    
    // Log initial element detection
    console.log('Chat elements initialization:',
        '\n- Input field found:', !!inputField, 
        '\n- Send button found:', !!sendButton, 
        '\n- Chat messages container found:', !!chatMessages);
    
    // Create fallback elements if needed
    if (!chatMessages) {
        console.error("Critical: Chat container not found!");
        // Create fallback container
        const chatContainer = document.querySelector("#minerva-floating-chat");
        if (chatContainer) {
            const fallbackMessages = document.createElement('div');
            fallbackMessages.id = "minerva-chat-messages";
            fallbackMessages.className = "minerva-chat-messages";
            fallbackMessages.style.cssText = "height: calc(100% - 110px); overflow-y: auto; padding: 15px; background-color: #f8f9fa;";
            chatContainer.appendChild(fallbackMessages);
            chatMessages = fallbackMessages;
            console.log("Created fallback chat container");
        }
    }
    
    // Create fallback input field if needed
    if (!inputField) {
        console.error("Critical: Chat input not found!");
        const chatContainer = document.querySelector("#minerva-floating-chat .minerva-chat-input-container");
        if (chatContainer) {
            const fallbackInput = document.createElement('textarea');
            fallbackInput.id = "minerva-chat-input";
            fallbackInput.className = "minerva-chat-input";
            fallbackInput.placeholder = "Type your message here...";
            fallbackInput.style.cssText = "flex: 1; border: 1px solid #ced4da; border-radius: 20px; padding: 10px; resize: none; outline: none;";
            chatContainer.prepend(fallbackInput);
            inputField = fallbackInput;
            console.log("Created fallback input field");
        }
    }
    
    // Create fallback send button if needed
    if (!sendButton) {
        console.error("Critical: Send button not found!");
        const chatContainer = document.querySelector("#minerva-floating-chat .minerva-chat-input-container");
        if (chatContainer) {
            const fallbackButton = document.createElement('button');
            fallbackButton.id = "minerva-send-btn";
            fallbackButton.className = "minerva-send-btn";
            fallbackButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            fallbackButton.style.cssText = "background-color: #7952b3; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; margin-left: 10px; cursor: pointer;";
            chatContainer.appendChild(fallbackButton);
            sendButton = fallbackButton;
            console.log("Created fallback send button");
        }
    }
    
    // Test the API response to see if it's working
    testApiResponse();

    // Check if we're on a project page by URL
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    const projectName = urlParams.get('name') || 'Unnamed Project';
    
    // Get stored conversation ID or create a new one
    let conversationId = localStorage.getItem('minerva_conversation_id') || 'conv_' + Date.now();
    
    // Initialize floating chat if needed
    initializeFloatingChat();

    if (!inputField || !sendButton) {
        console.error("Chat input or send button not found!");
        return;
    }

    function sendMessage() {
        const message = inputField.value.trim();
        if (message === "") return;
        
        // Display user message in chat
        displayMessage(message, "user");
        
        // Send to API
        sendMessageToAPI(message);
        
        // Clear input after sending
        inputField.value = "";
    }

    inputField.addEventListener("keypress", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);
    
    /**
     * Send message to Think Tank API
     */
    function sendMessageToAPI(message) {
        console.log("Sending message to Think Tank API:", message); // Debugging log
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Prepare payload
        const payload = {
            query: message,
            conversation_id: conversationId
        };
        
        // Add project context if in project mode
        if (projectId) {
            payload.project_id = projectId;
            payload.project_name = projectName;
            payload.context = 'project';
        }

        // Log the payload for debugging
        console.log('Sending payload to Think Tank API:', payload);

        console.log('### STARTING THINK TANK API REQUEST ###');
        console.log('Request URL: /api/think-tank');
        console.log('Request Payload:', JSON.stringify(payload, null, 2));
        
        fetch("/api/think-tank", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json" 
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            console.log('### API RESPONSE RECEIVED ###');
            console.log('Think Tank API status:', response.status, response.statusText);
            console.log('Response headers:', [...response.headers.entries()]);
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} - ${response.statusText}`);
            }
            
            // Get raw text first to handle potential JSON parsing issues
            return response.text().then(text => {
                console.log('### RAW API RESPONSE ###');
                console.log('Response length:', text.length);
                console.log('Raw response text FULL:', text);
                console.log('Response type:', typeof text);
                
                // Try to determine if it's JSON
                if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
                    console.log('Response appears to be JSON format');
                    try {
                        // Try to parse as JSON
                        const jsonData = JSON.parse(text);
                        console.log('Parsed JSON successfully:', jsonData);
                        return jsonData;
                    } catch (e) {
                        console.warn('PARSE ERROR - Response looks like JSON but failed to parse:', e);
                        console.warn('First 100 chars of problematic JSON:', text.substring(0, 100));
                        // Return the raw text if parsing fails
                        return { raw_response: text, parse_error: e.message };
                    }
                } else {
                    console.log('Response does not appear to be JSON format');
                    return { raw_response: text };
                }
            });
        })
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator(typingIndicator);
            
            console.log('Think Tank API response received:', typeof data === 'object' ? JSON.stringify(data, null, 2).substring(0, 500) + '...' : data); 
            console.log("🚨 RAW API RESPONSE:", data);
            console.log("📢 Extracted Response (Before Display):", data.responses ? data.responses["gpt-4o"] || data.responses[Object.keys(data.responses)[0]] : "No response found");
            
            // SIMPLIFIED RESPONSE EXTRACTION
            let responseText = null;
            let modelInfo = data.model_info || {};
            
            // Log exactly what we received to help with debugging
            console.log('Response type:', typeof data);
            if (typeof data === 'object') {
                console.log('Response keys:', Object.keys(data).join(', '));
            }
            
            // ULTRA-SIMPLIFIED DIRECT RESPONSE HANDLING
            // This completely replaces the complex extraction logic with something much more direct
            
            // Always store conversation ID to maintain chat memory
            if (data.conversation_id) {
                console.log('Saving conversation ID:', data.conversation_id);
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
            }
            
            // Direct extraction of response - try all possible locations
            let message = null;
            let primaryModel = null;
            
            // APPROACH 1: Check if responses object exists (multi-model format)
            if (data.responses && typeof data.responses === 'object') {
                console.log('Found responses object with keys:', Object.keys(data.responses));
                
                // Just take the first model's response
                const models = Object.keys(data.responses);
                if (models.length > 0) {
                    primaryModel = models[0];
                    message = data.responses[primaryModel];
                    console.log(`Using response from model: ${primaryModel}`);
                }
            }
            
            // APPROACH 2: Try other common response fields if no message yet
            if (!message) {
                const possibleFields = ['raw_response', 'response', 'text', 'message', 'content', 'answer'];
                
                for (const field of possibleFields) {
                    if (data[field] && typeof data[field] === 'string') {
                        message = data[field];
                        console.log(`Found response in field: ${field}`);
                        break;
                    }
                }
            }
            
            // APPROACH 3: Last resort - check if data itself is a string
            if (!message && typeof data === 'string') {
                message = data;
                console.log('Using raw string data as response');
            }
            
            // APPROACH 4: Extreme fallback - use a mock response to prevent error
            if (!message) {
                message = "I apologize, but I couldn't generate a proper response at this time. Please try asking again or rephrase your question.";
                console.log('Using fallback response message');
            }
            
            console.log('Final message to display:', message.substring(0, 100) + '...');
            
            // DIRECT DISPLAY - Bypass all complex display logic with enhanced container detection
            // Try multiple selectors and fallback methods to find the right container
            const containerSelectors = [
                'minerva-chat-messages',     // Primary ID
                'chat-messages',             // Alternative ID
                'chatMessages',              // Alternative ID
                '.minerva-chat-messages',    // Class-based selectors
                '.chat-messages',
                '.chat-container .messages',  // Nested selectors
                '.chat-window .message-list'
            ];
            
            // Try to find the container using multiple methods
            let container = null;
            
            // Method 1: Try ID-based selectors
            for (const selector of containerSelectors) {
                if (selector.startsWith('.')) {
                    // Class selector
                    const elements = document.querySelectorAll(selector);
                    if (elements && elements.length > 0) {
                        container = elements[0];
                        console.log(`Found chat container using class selector: ${selector}`);
                        break;
                    }
                } else {
                    // ID selector
                    const element = document.getElementById(selector);
                    if (element) {
                        container = element;
                        console.log(`Found chat container using ID: ${selector}`);
                        break;
                    }
                }
            }
            
            // Method 2: If still not found, look for any container that might be the chat
            if (!container) {
                const possibleContainers = document.querySelectorAll('.chat, .messages, .message-container');
                if (possibleContainers.length > 0) {
                    container = possibleContainers[0];
                    console.log('Found potential chat container using generic class selector');
                }
            }
            
            // Method 3: Last resort - find the first visible container element that might work
            if (!container) {
                const mainContent = document.querySelector('main') || document.body;
                if (mainContent) {
                    container = mainContent;
                    console.log('Using main content area as fallback container');
                }
            }
            
            if (container) {
                console.log('Creating message element with enhanced visibility');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'ai-message chat-message';
                // Add multiple CSS properties to ensure visibility across all themes
                messageDiv.style.cssText = 'display: block !important; visibility: visible !important; ' +
                                          'background: #f7f7f9; color: #333; padding: 15px; ' +
                                          'margin: 10px 0; border-radius: 10px; border-left: 4px solid #007bff; ' + 
                                          'font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; ' +
                                          'opacity: 1 !important; max-height: none !important; overflow: visible !important;';
                
                // Format the message with paragraphs and ensure special characters are handled
                const formattedMsg = message.split('\n').map(p => {
                    // Sanitize the paragraph content to prevent XSS
                    const sanitizedText = p
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;")
                        .replace(/"/g, "&quot;")
                        .replace(/'/g, "&#039;");
                    return sanitizedText ? `<p>${sanitizedText}</p>` : '';
                }).join('');
                
                messageDiv.innerHTML = formattedMsg || '<p>Message received but contains no text.</p>';
                
                // Add model info if available
                if (primaryModel) {
                    const modelLabel = document.createElement('div');
                    modelLabel.className = 'model-info';
                    modelLabel.style.cssText = 'font-size: 0.8em; color: #6c757d; margin-top: 8px;';
                    modelLabel.textContent = `Model: ${primaryModel}`;
                    messageDiv.appendChild(modelLabel);
                }
                
                // Add metadata to better track the message element
                messageDiv.dataset.timestamp = Date.now();
                messageDiv.dataset.messageType = 'ai-response';
                
                // Add to container and scroll
                container.appendChild(messageDiv);
                // Try to scroll to the new message
                try {
                    container.scrollTop = container.scrollHeight;
                } catch (e) {
                    console.warn('Error scrolling container:', e);
                    // Alternative scroll method
                    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
                
                console.log('Message successfully added to chat window');
                
                // Offer project conversion if applicable
                if (!projectId && data.can_create_project) {
                    addProjectConversionOption(conversationId || data.conversation_id);
                }
            } else {
                console.error('Could not find any suitable chat container!');
                // Use fallback method - create a floating message that will be visible no matter what
                forceDisplayMessage(message, 'ai', primaryModel);
            }
        })
        .catch(error => {
            console.error("Error in Think Tank API:", error);
            removeTypingIndicator(typingIndicator);
            
            // Display error message
            displayMessage(`Error: ${error.message}. Falling back to local response.`, "system");
            
            // Fall back to mock response after a brief delay
            setTimeout(() => {
                handleWithMockResponse(message);
            }, 1000);
        });
    }

    /**
     * Display a message in the chat window
     */
    function displayMessage(text, sender, modelInfo = null) {
        // Start with clear marker for debugging
        console.log('### DISPLAY MESSAGE FUNCTION CALLED ###');
        console.log(`Displaying message: sender=${sender}, text length=${text ? text.length : 0}`);
        console.log('Message content (first 50 chars):', text ? text.substring(0, 50) + '...' : 'null or empty');
        console.log('Model info:', JSON.stringify(modelInfo, null, 2));
        
        // Debug: Check if chat-messages element exists
        if (!chatMessages) {
            console.error('CRITICAL ERROR: chat-messages container not found in DOM');
            // Try to find it again
            const altChatMessages = document.getElementById('chat-messages') || document.getElementById('chat-history');
            if (altChatMessages) {
                console.log('Found alternative chat container:', altChatMessages.id);
                // Use this container instead
                chatMessages = altChatMessages;
            } else {
                // Create a debug output on the page to show the error
                const body = document.body;
                const debugAlert = document.createElement('div');
                debugAlert.style.cssText = 'position: fixed; top: 10px; right: 10px; background: red; color: white; padding: 10px; z-index: 9999;';
                debugAlert.textContent = 'Chat container not found - check console';
                body.appendChild(debugAlert);
                console.error('No suitable chat container found anywhere in the DOM!');
                return null;
            }
        }
        
        console.log('Chat container found:', chatMessages.id);
        
        try {
            // Create message container with improved styling
            console.log('Creating message div element');
            const messageDiv = document.createElement("div");
            messageDiv.className = `${sender}-message`;
            console.log('Set class name:', messageDiv.className);
            
            // Apply inline styles for better visibility
            if (sender === 'user') {
                messageDiv.style.cssText = 'background-color: #e3f2fd; color: #0d47a1; padding: 10px; border-radius: 10px; margin: 10px 0 10px auto; max-width: 80%; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: block; visibility: visible !important;';
                console.log('Applied user message styling');
            } else if (sender === 'ai') {
                messageDiv.style.cssText = 'background-color: #f0f4ff; color: #333; padding: 10px; border-radius: 10px; margin: 10px auto 10px 0; max-width: 80%; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: block; visibility: visible !important;';
                console.log('Applied AI message styling');
            } else { // system message
                messageDiv.style.cssText = 'background-color: #ffecb3; color: #495057; padding: 10px; border-radius: 10px; margin: 10px auto; width: 90%; font-size: 0.9rem; text-align: center; display: block; visibility: visible !important;';
                console.log('Applied system message styling');
            }
            
            console.log('Message element created with styles');
            
            // Different handling for AI vs user/system messages
            if (sender === 'ai') {
                console.log('Processing AI message content');
                // Create a content container for AI messages with formatted text
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                
                // Support simple markdown-like formatting
                console.log('Formatting text with markdown');
                let formattedText = 'No content';
                
                try {
                    if (text) {
                        formattedText = text
                            .replace(/\n/g, '<br>')
                            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                            .replace(/\*([^*]+)\*/g, '<em>$1</em>');
                        console.log('Text formatted successfully');
                    } else {
                        console.warn('Text is null or undefined, using placeholder');
                    }
                } catch (e) {
                    console.error('Error formatting text:', e);
                    formattedText = text || 'Error formatting message';
                }
                                
                try {
                    console.log('Setting innerHTML');
                    messageContent.innerHTML = formattedText;
                    console.log('innerHTML set successfully');
                } catch (e) {
                    console.error('Error setting innerHTML:', e);
                    messageContent.textContent = text || 'Error displaying formatted message';
                }
                
                messageDiv.appendChild(messageContent);
                console.log('Message content appended to message div');
                
                // Add model info if available
                if (modelInfo) {
                    console.log('Adding model info');
                    const modelInfoDiv = document.createElement('div');
                    modelInfoDiv.className = 'model-info';
                    modelInfoDiv.style.cssText = 'font-size: 0.75rem; color: #6c757d; margin-top: 5px; font-style: italic;';
                    modelInfoDiv.textContent = `Powered by ${modelInfo.primary_model || 'Think Tank'}`;
                    messageDiv.appendChild(modelInfoDiv);
                    console.log('Model info added');
                }
            } else {
                // For user and system messages, use simple text content
                console.log('Setting text content for user/system message');
                messageDiv.textContent = text || '';
                console.log('Text content set');
            }
            
            // Add to debug output element if it exists
            const debugOutput = document.getElementById('debug-output');
            if (debugOutput) {
                debugOutput.innerHTML += `<div><strong>${sender}</strong>: ${text ? text.substring(0, 30) + '...' : 'empty'}</div>`;
                console.log('Added to debug output element');
            } else {
                console.log('No debug-output element found');
            }
            
            // Check if messageDiv has content before appending
            console.log('Message div before appending:', messageDiv.outerHTML.substring(0, 100) + '...');
            
            console.log('Appending message to chat container');
            try {
                chatMessages.appendChild(messageDiv);
                console.log('Message successfully appended to chat container');
            } catch (e) {
                console.error('CRITICAL ERROR appending message to chat container:', e);
                return null;
            }
            
            // Force reflow to ensure proper rendering
            console.log('Forcing reflow');
            void messageDiv.offsetWidth;
            
            // Check if element is visible with computed styles
            try {
                const computed = window.getComputedStyle(messageDiv);
                console.log('Computed style - display:', computed.display);
                console.log('Computed style - visibility:', computed.visibility);
                console.log('Computed style - opacity:', computed.opacity);
                
                // Force visibility with !important to bypass any CSS issues
                messageDiv.style.cssText += '; display: block !important; visibility: visible !important; opacity: 1 !important;';
                console.log('Forced visibility on message element');
            } catch (e) {
                console.error('Error getting computed styles:', e);
            }
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            console.log('Message displayed and scrolled into view');
            
            return messageDiv; // Return for testing purposes
        } catch (error) {
            console.error('CRITICAL ERROR in displayMessage function:', error);
            return null;
        }
    }

    /**
     * Create a debug display of API response for diagnostics
     * This creates a floating panel showing the detailed API response
     */
    function createApiDebugDisplay(data) {
        // Get or create a debug container
        let debugContainer = document.getElementById('api-debug-container');
        if (!debugContainer) {
            debugContainer = document.createElement('div');
            debugContainer.id = 'api-debug-container';
            debugContainer.style.cssText = 'position: fixed; bottom: 10px; right: 10px; background: #f0f0f0; ' + 
                                           'border: 2px solid #333; padding: 15px; z-index: 9999; max-width: 80%; ' + 
                                           'max-height: 50%; overflow: auto; font-family: monospace;';
            document.body.appendChild(debugContainer);
        }
        
        // Clear previous content
        debugContainer.innerHTML = '<h3>Think Tank API Debug Results</h3>';
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.textContent = `Test run at: ${new Date().toLocaleTimeString()}`;
        timestamp.style.margin = '5px 0 15px';
        debugContainer.appendChild(timestamp);
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.textContent = 'Close';
        closeBtn.style.cssText = 'position: absolute; top: 10px; right: 10px; padding: 5px;';
        closeBtn.onclick = () => debugContainer.remove();
        debugContainer.appendChild(closeBtn);
        
        try {
            // Create formatted response display
            const responseType = document.createElement('div');
            responseType.innerHTML = `<strong>Response Type:</strong> ${typeof data}`;
            debugContainer.appendChild(responseType);
            
            if (typeof data === 'object') {
                // Show available keys
                const keysDiv = document.createElement('div');
                keysDiv.innerHTML = `<strong>Available Keys:</strong> ${Object.keys(data).join(', ')}`;
                debugContainer.appendChild(keysDiv);
                
                // Show responses if available
                if (data.responses) {
                    const modelsDiv = document.createElement('div');
                    modelsDiv.innerHTML = `<strong>Models:</strong> ${Object.keys(data.responses).join(', ')}`;
                    debugContainer.appendChild(modelsDiv);
                    
                    // Display first model's response
                    const modelName = Object.keys(data.responses)[0];
                    if (modelName) {
                        const responseDiv = document.createElement('div');
                        responseDiv.innerHTML = `<strong>${modelName} Response:</strong><br><pre>${data.responses[modelName]}</pre>`;
                        debugContainer.appendChild(responseDiv);
                    }
                }
                
                // Show direct response fields if present
                const directFields = ['response', 'message', 'text', 'content', 'answer'];
                for (const field of directFields) {
                    if (data[field]) {
                        const fieldDiv = document.createElement('div');
                        fieldDiv.innerHTML = `<strong>Direct ${field}:</strong><br><pre>${data[field]}</pre>`;
                        debugContainer.appendChild(fieldDiv);
                    }
                }
                
                // Add raw data in expandable section
                const rawData = document.createElement('details');
                rawData.innerHTML = `<summary>Raw Response Data</summary><pre>${JSON.stringify(data, null, 2)}</pre>`;
                debugContainer.appendChild(rawData);
            } else {
                // Just display the data as is
                const contentDiv = document.createElement('div');
                contentDiv.innerHTML = `<strong>Content:</strong><br><pre>${data}</pre>`;
                debugContainer.appendChild(contentDiv);
            }
            
            // Add direct test buttons
            const buttonContainer = document.createElement('div');
            buttonContainer.style.marginTop = '15px';
            debugContainer.appendChild(buttonContainer);
            
            // Button to force message display
            const forceDisplayBtn = document.createElement('button');
            forceDisplayBtn.textContent = 'Force Display Message';
            forceDisplayBtn.style.cssText = 'margin-top: 10px; padding: 5px 10px; background: #007bff; ' + 
                                            'color: white; border: none; border-radius: 4px; margin-right: 10px;';
            forceDisplayBtn.onclick = () => {
                let message = 'This is a test message forced into the chat UI.';
                if (typeof data === 'object') {
                    if (data.responses) {
                        const modelName = Object.keys(data.responses)[0];
                        if (modelName && data.responses[modelName]) {
                            message = data.responses[modelName];
                        }
                    } else if (data.response) {
                        message = data.response;
                    }
                }
                forceDisplayMessage(message, 'ai');
            };
            buttonContainer.appendChild(forceDisplayBtn);
            
            // Button to test displayMessage
            const testDisplayBtn = document.createElement('button');
            testDisplayBtn.textContent = 'Test displayMessage()';
            testDisplayBtn.style.cssText = 'margin-top: 10px; padding: 5px 10px; background: #28a745; ' + 
                                           'color: white; border: none; border-radius: 4px;';
            testDisplayBtn.onclick = () => {
                try {
                    displayMessage('This is a test of the displayMessage function.', 'ai');
                } catch (e) {
                    alert('Error in displayMessage: ' + e.message);
                    console.error('displayMessage error:', e);
                }
            };
            buttonContainer.appendChild(testDisplayBtn);
        } catch (e) {
            // Handle any display errors
            const errorDiv = document.createElement('div');
            errorDiv.innerHTML = `<strong>Error displaying results:</strong> ${e.message}`;
            errorDiv.style.color = 'red';
            debugContainer.appendChild(errorDiv);
        }
    }

    /**
     * EMERGENCY FIX: Direct test of the API with guaranteed display
     * Run this in the console with: emergencyAPITest()
     */
    /**
     * DIRECT ERROR TRACKING: Find where the error message is being triggered
     * This adds a tracker to all error message assignments in the code
     */
    function directErrorTracking() {
        console.log('🔍 INITIATING DIRECT ERROR TRACKING');
        
        // Create a tracking report container
        let trackerContainer = document.getElementById('error-tracker-container');
        if (!trackerContainer) {
            trackerContainer = document.createElement('div');
            trackerContainer.id = 'error-tracker-container';
            trackerContainer.style.cssText = 'position: fixed; top: 10px; left: 10px; background: #ffffff; border: 2px solid #f44336; ' +
                                           'padding: 15px; z-index: 9999; max-width: 90%; max-height: 80%; overflow: auto; ' +
                                           'box-shadow: 0 0 15px rgba(0,0,0,0.2); font-family: monospace;';
            document.body.appendChild(trackerContainer);
            
            // Add title and close button
            const headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;';
            
            const title = document.createElement('h3');
            title.textContent = 'Error Message Tracking';
            title.style.margin = '0';
            headerDiv.appendChild(title);
            
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'Close';
            closeBtn.onclick = () => trackerContainer.remove();
            headerDiv.appendChild(closeBtn);
            
            trackerContainer.appendChild(headerDiv);
            
            // Add description
            const description = document.createElement('p');
            description.textContent = 'Monitoring for "Sorry, I encountered an error processing your request" message generation';
            trackerContainer.appendChild(description);
            
            // Create log area
            const logArea = document.createElement('div');
            logArea.id = 'error-tracker-log';
            logArea.style.cssText = 'background: #f5f5f5; padding: 10px; border: 1px solid #ddd; height: 200px; overflow-y: auto;';
            trackerContainer.appendChild(logArea);
        }
        
        // Add an entry to the log
        function addTrackingLog(message) {
            const logArea = document.getElementById('error-tracker-log');
            if (logArea) {
                const entry = document.createElement('div');
                entry.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
                entry.style.borderBottom = '1px solid #eee';
                entry.style.padding = '5px 0';
                logArea.appendChild(entry);
                logArea.scrollTop = logArea.scrollHeight;
            }
        }
        
        // Override console.error to catch error logs
        const originalConsoleError = console.error;
        console.error = function(...args) {
            originalConsoleError.apply(console, args);
            
            // Check if any argument contains our error message
            const errorStringified = args.map(arg => String(arg)).join(' ');
            if (errorStringified.includes('Sorry, I encountered an error')) {
                addTrackingLog(`Console error containing target message: ${errorStringified.substring(0, 100)}...`);
            }
        };
        
        // Monitor all responseText assignments
        addTrackingLog('Setting up monitoring for error message assignments');
        
        // Test a direct API call
        addTrackingLog('Initiating test API call');
        
        // Make a test API call with header that will show in logs
        fetch('/api/think-tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Debug-Tracking': 'error-message-trace'
            },
            body: JSON.stringify({
                query: 'Test message for error tracking',
                conversation_id: 'error_track_' + Date.now()
            })
        })
        .then(response => {
            addTrackingLog(`API Status: ${response.status} ${response.statusText}`);
            return response.text();
        })
        .then(text => {
            try {
                const data = JSON.parse(text);
                addTrackingLog(`API Response keys: ${Object.keys(data).join(', ')}`);
                
                // Try to extract message using the same logic as the main code
                let message = null;
                
                // Check for responses object (multi-model format)
                if (data.responses && typeof data.responses === 'object') {
                    const models = Object.keys(data.responses);
                    addTrackingLog(`Found responses with models: ${models.join(', ')}`);
                    
                    if (models.length > 0) {
                        const primaryModel = models[0];
                        message = data.responses[primaryModel];
                        addTrackingLog(`Using response from model: ${primaryModel}`);
                    }
                }
                
                // Try other common response fields if no message yet
                if (!message) {
                    const possibleFields = ['raw_response', 'response', 'text', 'message', 'content', 'answer'];
                    
                    for (const field of possibleFields) {
                        if (data[field] && typeof data[field] === 'string') {
                            message = data[field];
                            addTrackingLog(`Found response in field: ${field}`);
                            break;
                        }
                    }
                }
                
                // Try direct string
                if (!message && typeof data === 'string') {
                    message = data;
                    addTrackingLog('Using raw string data as response');
                }
                
                // Final result
                if (message) {
                    addTrackingLog(`Successfully extracted message: ${message.substring(0, 50)}...`);
                    forceDisplayMessage(message, 'ai');
                } else {
                    addTrackingLog('❌ COULD NOT EXTRACT MESSAGE - this is likely the source of the error!');
                    forceDisplayMessage('No message could be extracted from the API response. This indicates the API response format does not match what the code expects.', 'system');
                }
                
                // Show raw response in tracking panel
                const rawResponseDiv = document.createElement('details');
                rawResponseDiv.innerHTML = `<summary>Raw API Response</summary><pre>${JSON.stringify(data, null, 2)}</pre>`;
                document.getElementById('error-tracker-log').appendChild(rawResponseDiv);
                
            } catch (e) {
                addTrackingLog(`Error parsing API response: ${e.message}`);
                forceDisplayMessage(`API Parse Error: ${e.message}\n\nFirst 100 chars of response:\n${text.substring(0, 100)}`, 'system');
            }
        })
        .catch(error => {
            addTrackingLog(`API Call Error: ${error.message}`);
            forceDisplayMessage(`API Call Failed: ${error.message}`, 'system');
        });
        
        // Add some specific tests
        setTimeout(() => {
            addTrackingLog('Testing displayMessage function');
            try {
                displayMessage('Test message via standard display function', 'ai');
                addTrackingLog('✅ displayMessage function executed without errors');
            } catch (e) {
                addTrackingLog(`❌ displayMessage ERROR: ${e.message}`);
                forceDisplayMessage(`displayMessage function error: ${e.message}`, 'system');
            }
        }, 2000);
        
        return 'Error tracking initialized. Check the panel in the top-left corner for results.';
    }

    function emergencyAPITest() {
        console.log('### EMERGENCY API TEST INITIATED ###');
        
        // Show a status message in the chat
        const statusMsg = document.createElement('div');
        statusMsg.style.cssText = 'display: block !important; background: #2196F3; color: white; padding: 15px; ' +
                               'margin: 10px 0; border-radius: 10px; position: relative; z-index: 9999;';
        statusMsg.innerHTML = '<strong>EMERGENCY TEST:</strong> Testing API directly...';
        
        // Try to find the chat container by multiple possible IDs
        const container = document.getElementById('minerva-chat-messages') || 
                        document.querySelector('.chat-messages') || 
                        document.querySelector('[class*="chat"][class*="message"]');
                        
        if (container) {
            container.appendChild(statusMsg);
            container.scrollTop = container.scrollHeight;
        } else {
            // If we can't find the container, create a floating message
            statusMsg.style.position = 'fixed';
            statusMsg.style.bottom = '20px';
            statusMsg.style.right = '20px';
            statusMsg.style.zIndex = '9999';
            document.body.appendChild(statusMsg);
        }
        
        // Make a direct API call with minimal payload
        fetch('/api/think-tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: 'Hello, this is an emergency test',
                conversation_id: 'emergency_test_' + Date.now()
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('### EMERGENCY API RESPONSE ###', data);
            
            // Create response display element
            const responseDiv = document.createElement('div');
            responseDiv.style.cssText = 'display: block !important; background: #4CAF50; color: white; padding: 15px; ' +
                                    'margin: 10px 0; border-radius: 10px; font-family: monospace; white-space: pre-wrap; ' +
                                    'position: relative; z-index: 9999; max-height: 300px; overflow-y: auto;';
            
            // Format and display the raw response
            responseDiv.innerHTML = '<strong>API RESPONSE:</strong><br>' + 
                                  JSON.stringify(data, null, 2)
                                  .replace(/\n/g, '<br>')
                                  .replace(/ /g, '&nbsp;');
            
            // Add to container or body
            if (container) {
                container.appendChild(responseDiv);
                container.scrollTop = container.scrollHeight;
            } else {
                responseDiv.style.position = 'fixed';
                responseDiv.style.bottom = '100px';
                responseDiv.style.right = '20px';
                responseDiv.style.zIndex = '9999';
                document.body.appendChild(responseDiv);
            }
            
            // Try to extract and show the model response directly
            let modelResponse = null;
            
            // Try different possible response formats
            if (data.responses) {
                const modelKeys = Object.keys(data.responses);
                if (modelKeys.length > 0) {
                    modelResponse = data.responses[modelKeys[0]];
                }
            } else if (data.response) {
                modelResponse = data.response;
            } else if (data.message) {
                modelResponse = data.message;
            }
            
            if (modelResponse) {
                // Show the actual model response
                const aiMsg = document.createElement('div');
                aiMsg.style.cssText = 'display: block !important; background: #673AB7; color: white; padding: 15px; ' +
                                    'margin: 10px 0; border-radius: 10px; position: relative; z-index: 9999;';
                aiMsg.innerHTML = '<strong>EXTRACTED AI RESPONSE:</strong><br>' + modelResponse;
                
                if (container) {
                    container.appendChild(aiMsg);
                    container.scrollTop = container.scrollHeight;
                } else {
                    aiMsg.style.position = 'fixed';
                    aiMsg.style.bottom = '180px';
                    aiMsg.style.right = '20px';
                    aiMsg.style.zIndex = '9999';
                    document.body.appendChild(aiMsg);
                }
            }
        })
        .catch(error => {
            console.error('API Test Error:', error);
            
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.style.cssText = 'display: block !important; background: #F44336; color: white; padding: 15px; ' +
                                    'margin: 10px 0; border-radius: 10px; position: relative; z-index: 9999;';
            errorDiv.innerHTML = '<strong>API ERROR:</strong><br>' + error.message;
            
            if (container) {
                container.appendChild(errorDiv);
                container.scrollTop = container.scrollHeight;
            } else {
                errorDiv.style.position = 'fixed';
                errorDiv.style.bottom = '20px';
                errorDiv.style.right = '20px';
                errorDiv.style.zIndex = '9999';
                document.body.appendChild(errorDiv);
            }
        });
        
        return 'Emergency API test initiated - check console for results';
    }

    /**
     * Force display a message in the chat (direct DOM manipulation)
     * This is a fallback method if the regular displayMessage function fails
     * @param {string} text - The message text to display
     * @param {string} sender - The sender of the message (ai, user, system)
     * @param {string} [modelName] - Optional model name information
     */
    function forceDisplayMessage(text, sender, modelName = null) {
        console.log('### FORCING MESSAGE DISPLAY ###');
        console.log(`Forcing display of message: ${text ? text.substring(0, 50) + (text.length > 50 ? '...' : '') : 'undefined or null'}`);
        
        // Try all possible containers - exhaustive search
        const possibleContainers = [
            document.getElementById('minerva-chat-messages'),
            document.getElementById('chat-messages'),
            document.querySelector('.minerva-chat-messages'),
            document.querySelector('.chat-messages'),
            document.querySelector('#chat-interface .messages'),
            document.querySelector('#chat-interface #chat-messages'),
            document.querySelector('[id$="-chat-messages"]'), // Any ID ending with -chat-messages
            document.querySelector('[class*="chat"][class*="message"]') // Any class containing both "chat" and "message"
        ];
        
        let container = null;
        
        // Find the first valid container
        for (const c of possibleContainers) {
            if (c) {
                container = c;
                console.log('Found chat container:', c.id || c.className || 'unnamed container');
                break;
            }
        }
        
        if (!container) {
            console.error('CRITICAL: No chat container found to force display message!');  
            
            // Create a diagnostic report in the DOM
            const diagnosticReport = document.createElement('div');
            diagnosticReport.id = 'diagnostic-report';
            diagnosticReport.style.cssText = 'position: fixed; top: 10px; left: 10px; right: 10px; background: #f44336; ' + 
                                          'color: white; padding: 15px; border-radius: 5px; z-index: 9999; max-height: 80vh; ' + 
                                          'overflow-y: auto; font-family: monospace;';
            
            // Show all elements that might be potential containers
            let report = '<h3>⚠️ CHAT CONTAINER NOT FOUND - DOM DIAGNOSTIC</h3>';
            report += '<p>No suitable chat message container found. Here are all potential elements:</p><ul>';
            
            const chatRelatedElements = document.querySelectorAll('[id*="chat"], [class*="chat"], [id*="message"], [class*="message"]');
            for (const el of chatRelatedElements) {
                report += `<li>Element: &lt;${el.tagName.toLowerCase()}&gt; | ID: ${el.id || 'none'} | Class: ${el.className || 'none'} | Visible: ${el.offsetParent !== null}</li>`;
            }
            report += '</ul>';
            
            // Create a last resort container
            report += '<p>Creating emergency container for message...</p>';
            diagnosticReport.innerHTML = report;
            document.body.appendChild(diagnosticReport);
            
            // Add close button
            const closeBtn = document.createElement('button');
            closeBtn.textContent = 'Close';
            closeBtn.style.cssText = 'position: absolute; top: 10px; right: 10px; padding: 5px;';
            closeBtn.onclick = () => diagnosticReport.remove();
            diagnosticReport.appendChild(closeBtn);
            
            // Create emergency container
            container = document.createElement('div');
            container.id = 'emergency-chat-container';
            container.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); ' + 
                                     'width: 80%; max-width: 500px; height: 300px; background: white; border: 1px solid #333; ' + 
                                     'padding: 20px; z-index: 9999; overflow: auto; box-shadow: 0 0 20px rgba(0,0,0,0.3);';
            
            const containerHeader = document.createElement('div');
            containerHeader.innerHTML = '<h3>Emergency Chat Window</h3><p>Created because regular chat container not found</p>';
            containerHeader.style.marginBottom = '15px';
            container.appendChild(containerHeader);
            
            document.body.appendChild(container);
            console.log('Created emergency container for messages');
        }
        
        // Create message element with guaranteed visibility styles
        const div = document.createElement('div');
        div.className = `${sender}-message`;
        div.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important; ' + 
                          'margin: 10px 0; padding: 12px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); ' +
                          'font-family: system-ui, -apple-system, sans-serif; line-height: 1.4; word-break: break-word; ' +
                          'max-width: 90%;';
        
        // Style based on sender
        if (sender === 'user') {
            div.style.backgroundColor = '#e3f2fd';
            div.style.color = '#0d47a1';
            div.style.marginLeft = 'auto';
            div.style.marginRight = '10px';
            div.style.textAlign = 'right';
        } else if (sender === 'ai') {
            div.style.backgroundColor = '#f0f4ff';
            div.style.color = '#333';
            div.style.marginRight = 'auto';
            div.style.marginLeft = '10px';
            div.style.borderLeft = '4px solid #1890ff';
        } else { // system message
            div.style.backgroundColor = '#fff7e6';
            div.style.color = '#d46b08';
            div.style.margin = '10px auto';
            div.style.width = '85%';
            div.style.textAlign = 'center';
            div.style.fontWeight = 'bold';
            div.style.border = '2px solid #fa8c16';
        }

        // Format and add the text content
        if (text && typeof text === 'string') {
            // Convert newlines to paragraph elements for better formatting
            const formattedText = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
                .replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
                
            div.innerHTML = formattedText.split('\n').map(line => 
                line.trim() ? `<p>${line}</p>` : '<br>'
            ).join('');
        } else {
            div.textContent = 'Empty message or non-string content';
        }
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.style.cssText = 'font-size: 0.75rem; color: #999; margin-top: 5px; text-align: right;';
        timestamp.textContent = new Date().toLocaleTimeString();
        div.appendChild(timestamp);
        
        // Append to container
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        
        console.log('✅ Message successfully forced into UI');
        return div;
    }
    
    /**
     * Fix for direct API testing with a test query
     * IMPORTANT: This will show the raw API response in the UI
     */
    function fixChatAPI() {
        console.log('### DIRECT API FIX APPLIED ###');
        // Test message
        const testMessage = 'Generate a test response';
        const debugOutput = document.getElementById("debug-output");
        
        if (debugOutput) {
            debugOutput.innerHTML = '<strong>Testing API directly - please wait...</strong>';
        }
        
        // Direct API call
        fetch('/api/think-tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: testMessage,
                conversation_id: 'test_' + Date.now()
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('### DIRECT API RESPONSE ###', data);
            
            // Show raw response in UI
            const container = document.getElementById('minerva-chat-messages');
            
            if (container) {
                // Create a clear message element
                const div = document.createElement('div');
                div.className = 'system-message';
                div.style.cssText = 'display: block !important; background: #4caf50; color: white; padding: 15px; ' +
                                  'margin: 10px 0; border-radius: 10px; font-family: monospace; white-space: pre-wrap;';
                
                // Format the response for display
                const responseText = typeof data === 'object' ? 
                    JSON.stringify(data, null, 2) : 
                    String(data);
                    
                div.textContent = "API TEST RESPONSE:\n" + responseText;
                container.appendChild(div);
                
                // Update debug output
                if (debugOutput) {
                    debugOutput.innerHTML = '<strong>API RESPONSE RECEIVED - Check the chat window</strong>';
                }
                
                // Show a helpful message about how to fix
                setTimeout(() => {
                    const fixDiv = document.createElement('div');
                    fixDiv.className = 'system-message';
                    fixDiv.style.cssText = 'display: block !important; background: #ff9800; color: white; padding: 15px; ' +
                                        'margin: 10px 0; border-radius: 10px;';
                    fixDiv.innerHTML = "<strong>DIAGNOSTIC REPORT:</strong><br>" +
                                      "API is working, but response format may not match what the code expects.<br>" +
                                      "Check if responses are nested in a 'responses' object or directly in the response.";
                    container.appendChild(fixDiv);
                }, 1000);
            } else {
                console.error('Cannot find chat messages container');
                alert('API Response received but cannot find chat container to display it.');
            }
        })
        .catch(error => {
            console.error('API Test Error:', error);
            
            // Show error in UI if possible
            const container = document.getElementById('minerva-chat-messages');
            if (container) {
                const div = document.createElement('div');
                div.className = 'system-message';
                div.style.cssText = 'display: block !important; background: #f44336; color: white; padding: 15px; ' +
                                  'margin: 10px 0; border-radius: 10px;';
                div.textContent = "API ERROR: " + error.message;
                container.appendChild(div);
            }
            
            if (debugOutput) {
                debugOutput.innerHTML = '<strong>ERROR: API call failed - ' + error.message + '</strong>';
            }
        });
    }

    /**
     * Test API response functionality
     * This function makes a direct API call to verify the API is working
     */
    function testApiResponse() {
        console.log("### TESTING API RESPONSE ###");
        const debugOutput = document.getElementById("debug-output");
        if (debugOutput) {
            debugOutput.innerHTML = '<strong>Debug:</strong> Testing API connection...';
        }
        
        fetch("/api/think-tank", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({
                query: "Test message from Think Tank API",
                conversation_id: "debug_" + Date.now()
            })
        })
        .then(response => {
            console.log("### API TEST RESPONSE STATUS ###", response.status);
            if (debugOutput) {
                debugOutput.innerHTML += `<div>API Status: ${response.status}</div>`;
            }
            return response.text();
        })
        .then(text => {
            console.log("### DEBUG API RESPONSE TEXT ###");
            console.log(text.substring(0, 1000) + (text.length > 1000 ? '...' : ''));
            
            try {
                const data = JSON.parse(text);
                console.log("🚨 RAW API TEST RESPONSE:", data);
                console.log("### DEBUG API RESPONSE PARSED ###");
                console.log("Available keys:", Object.keys(data).join(', '));
                
                // Create a debug display in UI for visual debugging
                createApiDebugDisplay(data);
                
                if (debugOutput) {
                    debugOutput.innerHTML += `<div>API Response: ${JSON.stringify(data).substring(0, 50)}...</div>`;
                }
                
                // Try to extract a response message using the same logic as in actual chat
                let extractedMessage = "No message found";
                
                // Approach 1: Check for responses object
                if (data.responses && typeof data.responses === 'object') {
                    const models = Object.keys(data.responses);
                    if (models.length > 0) {
                        const primaryModel = models[0];
                        extractedMessage = data.responses[primaryModel];
                        console.log(`📢 Extracted Test Response (from model ${primaryModel}):`, 
                            extractedMessage ? extractedMessage.substring(0, 100) + '...' : 'undefined or empty');
                    }
                }
                
                // Approach 2: Try other common response fields
                if (!extractedMessage || extractedMessage === "No message found") {
                    const possibleFields = ['raw_response', 'response', 'text', 'message', 'content', 'answer'];
                    for (const field of possibleFields) {
                        if (data[field] && typeof data[field] === 'string') {
                            extractedMessage = data[field];
                            console.log(`📢 Extracted Test Response (from field ${field}):`, 
                                extractedMessage.substring(0, 100) + '...');
                            break;
                        }
                    }
                }
                
                // Now try to display this in the chat UI as a real message
                forceDisplayMessage(extractedMessage, 'ai');
                
            } catch (e) {
                console.error("Error parsing API response:", e);
                if (debugOutput) {
                    debugOutput.innerHTML += `<div>API Parse Error: ${e.message}</div>`;
                }
                // Even on parse error, try to display the raw text
                forceDisplayMessage("API PARSE ERROR: " + e.message + "\n\nRaw Response:\n" + text.substring(0, 500), 'system');
            }
        })
        .catch(error => {
            console.error("Test API call failed:", error);
            if (debugOutput) {
                debugOutput.innerHTML += `<div>API Test Failed: ${error.message}</div>`;
            }
            forceDisplayMessage("API TEST FAILED: " + error.message, 'system');
        });
    }
    
    /**
     * Handle message with mock response for testing
     */
    function handleWithMockResponse(message) {
        const lowerMessage = message.toLowerCase();
        let response;
        let modelInfo = {
            primary_model: 'Think Tank Blend',
            contributors: ['gpt-4', 'claude-3', 'gemini-pro', 'llama-3']
        };
        
        // Generate appropriate response based on user message
        if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage === 'hey') {
            response = "Hello! I'm Minerva, your AI assistant. How can I help you today?";
        } else if (lowerMessage.includes('name')) {
            response = "I'm Minerva, an AI assistant designed to help with a variety of tasks.";
        } else if (lowerMessage.includes('project') || lowerMessage.includes('minerva')) {
            response = "Minerva is a multi-model AI system that combines the strengths of different language models to provide better responses. I can help you with research, answering questions, and organizing information.";
        } else if (lowerMessage.includes('think tank')) {
            response = "The Think Tank is Minerva's core processing system. It evaluates queries across multiple AI models and combines their strengths for better answers. This multi-model approach allows for more robust responses than any single model could provide.";
        } else if (lowerMessage.includes('help')) {
            response = "I can help with a variety of tasks, including answering questions, providing information, organizing projects, and more. Just let me know what you need assistance with.";
        } else if (lowerMessage.includes('thanks') || lowerMessage.includes('thank you')) {
            response = "You're welcome! If you need any further assistance, don't hesitate to ask.";
        } else if (lowerMessage.includes('code') || lowerMessage.includes('python') || lowerMessage.includes('javascript')) {
            response = "Here's a simple example of code that might help with your task:\n```javascript\nfunction processData(input) {\n  const result = input.map(item => {\n    return { processed: item.value * 2 };\n  });\n  return result;\n}\n```\nYou can modify this based on your specific requirements.";
            modelInfo.primary_model = 'gpt-4';
        } else if (lowerMessage.includes('data') || lowerMessage.includes('analyze')) {
            response = "For data analysis, I recommend following these steps:\n1. Clean and preprocess your data\n2. Explore data through visualization\n3. Apply appropriate statistical methods\n4. Interpret results with domain knowledge\n5. Document your findings\n\nIs there a specific part of this process you need help with?";
        } else {
            // Default response
            response = "I understand you're asking about '" + message + "'. While I'm in testing mode right now with limited capabilities, in the full version I would be able to provide a comprehensive answer by drawing on multiple AI models. Is there something specific about this topic you'd like to explore?";
        }
        
        // Add a small delay for more natural feeling
        setTimeout(() => {
            displayMessage(response, "ai", modelInfo);
        }, 1000);
    }
    
    /**
     * Add a typing indicator to the chat
     */
    function addTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return indicator;
    }
    
    /**
     * Remove typing indicator
     */
    function removeTypingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }
    
    /**
     * Add project conversion option
     */
    function addProjectConversionOption(conversationId) {
        const conversionDiv = document.createElement('div');
        conversionDiv.className = 'project-conversion';
        conversionDiv.innerHTML = `
            <p>Would you like to convert this conversation to a project?</p>
            <div class="project-conversion-controls">
                <input type="text" placeholder="Project name" id="project-name-input">
                <button id="create-project-btn">Create Project</button>
            </div>
        `;
        
        chatMessages.appendChild(conversionDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
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
            
            fetch('/api/projects/create-from-conversation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    project_name: projectName
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to create project');
                return response.json();
            })
            .then(data => {
                displayMessage(`Successfully created project "${projectName}". Redirecting...`, 'system');
                
                if (data.project_url) {
                    setTimeout(() => {
                        window.location.href = data.project_url;
                    }, 1500);
                }
            })
            .catch(error => {
                console.error('Error creating project:', error);
                createBtn.textContent = 'Create Project';
                createBtn.disabled = false;
                displayMessage('Failed to create project. Please try again.', 'system');
            });
        });
    }
    
    /**
     * Initialize floating chat on the homepage
     */
    function initializeFloatingChat() {
        // Only create floating chat if we're not in project mode
        if (projectId) return;
        
        // Check if floating chat already exists
        let chatContainer = document.getElementById('minerva-floating-chat');
        
        if (!chatContainer) {
            chatContainer = document.createElement('div');
            chatContainer.id = 'minerva-floating-chat';
            chatContainer.className = 'minerva-floating-chat';
            document.body.appendChild(chatContainer);
            
            // Create chat header
            const header = document.createElement('div');
            header.className = 'chat-header';
            header.innerHTML = `
                <div class="chat-title">Minerva Assistant</div>
                <div class="chat-controls">
                    <button class="minimize-btn">–</button>
                    <button class="close-btn">×</button>
                </div>
            `;
            chatContainer.appendChild(header);
            
            // Create messages container if it doesn't exist
            if (!document.getElementById('chat-messages')) {
                const messagesContainer = document.createElement('div');
                messagesContainer.id = 'chat-messages';
                messagesContainer.className = 'chat-messages';
                chatContainer.appendChild(messagesContainer);
            }
            
            // Create input container
            const inputContainer = document.createElement('div');
            inputContainer.className = 'chat-input-container';
            inputContainer.innerHTML = `
                <textarea id="chat-input" placeholder="Type a message..."></textarea>
                <button id="chat-send-button">Send</button>
            `;
            chatContainer.appendChild(inputContainer);
            
            // Add event listeners to header buttons
            const minimizeBtn = header.querySelector('.minimize-btn');
            const closeBtn = header.querySelector('.close-btn');
            
            minimizeBtn.addEventListener('click', () => {
                chatContainer.classList.toggle('minimized');
                minimizeBtn.textContent = chatContainer.classList.contains('minimized') ? '+' : '–';
            });
            
            closeBtn.addEventListener('click', () => {
                chatContainer.style.display = 'none';
                // Create the toggle button if it doesn't exist
                if (!document.getElementById('chat-toggle')) {
                    const toggleBtn = document.createElement('button');
                    toggleBtn.id = 'chat-toggle';
                    toggleBtn.innerHTML = '<i class="fas fa-comments"></i>';
                    document.body.appendChild(toggleBtn);
                    
                    toggleBtn.addEventListener('click', () => {
                        chatContainer.style.display = 'flex';
                        toggleBtn.style.display = 'none';
                    });
                } else {
                    document.getElementById('chat-toggle').style.display = 'block';
                }
            });
            
            // Make header draggable
            makeDraggable(chatContainer, header);
            
            // Show welcome message
            setTimeout(() => {
                displayMessage('Welcome to Minerva. How can I assist you today?', 'system');
            }, 500);
        }
    }
    
    /**
     * Make an element draggable
     */
    function makeDraggable(element, handle) {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        handle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
            element.style.bottom = 'auto';
            element.style.right = 'auto';
        }
        
        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }
});

class MinervaChatIntegration {
    constructor(options = {}) {
        this.options = {
            floatingChatId: 'minerva-floating-chat',
            projectPanelId: 'minerva-project-chat',
            apiEndpoint: '/api/think-tank',
            defaultPosition: 'bottom-right',
            ...options
        };
        
        // Chat state
        this.conversationId = localStorage.getItem('minerva_conversation_id') || null;
        this.isProjectMode = !!this.options.projectId;
        this.isMobileView = window.innerWidth < 768;
        this.isMinimized = false;
        
        // Initialize based on context
        if (this.isProjectMode) {
            this.initProjectPanel();
        } else {
            this.initFloatingChat();
        }
        
        // Handle responsiveness
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }
    
    /**
     * Initialize floating chat for homepage
     */
    initFloatingChat() {
        // Create container if it doesn't exist
        let container = document.getElementById(this.options.floatingChatId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.floatingChatId;
            container.className = 'minerva-floating-chat';
            document.body.appendChild(container);
        }
        
        this.chatContainer = container;
        
        // Set styles for floating chat
        this.applyStyles(container, {
            position: 'fixed',
            width: this.isMobileView ? '85%' : '350px',
            height: this.isMobileView ? '60%' : '500px',
            zIndex: '9999',
            transition: 'all 0.3s ease',
            boxShadow: '0 5px 20px rgba(0, 0, 0, 0.2)',
            borderRadius: '10px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        });
        
        // Position the chat
        this.positionChat(container);
        
        // Create chat interface
        this.createChatInterface(container);
        
        // Make draggable
        this.makeDraggable(container);
        
        // Create toggle button
        this.createToggleButton();
    }
    
    /**
     * Initialize project panel
     */
    initProjectPanel() {
        // Find project container
        const projectContainer = document.querySelector('.project-content') || document.body;
        
        // Create container if it doesn't exist
        let container = document.getElementById(this.options.projectPanelId);
        if (!container) {
            container = document.createElement('div');
            container.id = this.options.projectPanelId;
            container.className = 'minerva-project-panel';
            projectContainer.appendChild(container);
        }
        
        this.chatContainer = container;
        
        // Set styles for project panel
        this.applyStyles(container, {
            width: '100%',
            height: '200px',
            marginTop: '20px',
            borderRadius: '10px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        });
        
        // Create chat interface
        this.createChatInterface(container, true);
    }
    
    /**
     * Create chat interface
     */
    createChatInterface(container, isProjectPanel = false) {
        // Create header
        const header = document.createElement('div');
        header.className = 'chat-header';
        this.applyStyles(header, {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '10px 15px',
            backgroundColor: 'rgba(30, 41, 59, 0.8)',
            cursor: isProjectPanel ? 'default' : 'move',
            userSelect: 'none'
        });
        
        // Create title
        const title = document.createElement('div');
        title.className = 'chat-title';
        title.textContent = isProjectPanel ? `Project Chat: ${this.options.projectName || 'Unnamed Project'}` : 'Minerva Assistant';
        this.applyStyles(title, {
            fontWeight: 'bold',
            color: '#e2e8f0',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
        });
        
        // Create controls
        const controls = document.createElement('div');
        controls.className = 'chat-controls';
        this.applyStyles(controls, {
            display: 'flex',
            alignItems: 'center'
        });
        
        // Add minimize button for floating chat
        if (!isProjectPanel) {
            const minimizeBtn = document.createElement('button');
            minimizeBtn.className = 'chat-button minimize-btn';
            minimizeBtn.innerHTML = '–';
            minimizeBtn.title = 'Minimize';
            this.applyStyles(minimizeBtn, {
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px',
                marginLeft: '5px',
                padding: '2px 5px',
                borderRadius: '3px',
                transition: 'all 0.2s ease'
            });
            
            minimizeBtn.addEventListener('click', () => this.toggleMinimize());
            controls.appendChild(minimizeBtn);
            this.minimizeBtn = minimizeBtn;
        }
        
        // Add close button for floating chat
        if (!isProjectPanel) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'chat-button close-btn';
            closeBtn.innerHTML = '×';
            closeBtn.title = 'Close';
            this.applyStyles(closeBtn, {
                background: 'none',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                fontSize: '14px',
                marginLeft: '5px',
                padding: '2px 5px',
                borderRadius: '3px',
                transition: 'all 0.2s ease'
            });
            
            closeBtn.addEventListener('click', () => this.toggleVisibility());
            controls.appendChild(closeBtn);
        }
        
        // Assemble header
        header.appendChild(title);
        header.appendChild(controls);
        container.appendChild(header);
        
        // Create messages container
        const messagesContainer = document.createElement('div');
        messagesContainer.className = 'chat-messages';
        messagesContainer.id = isProjectPanel ? 'project-chat-messages' : 'floating-chat-messages';
        this.applyStyles(messagesContainer, {
            flex: '1',
            overflowY: 'auto',
            padding: '15px',
            color: '#e2e8f0'
        });
        container.appendChild(messagesContainer);
        this.messagesContainer = messagesContainer;
        
        // Add welcome message
        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'system-message';
        welcomeMsg.textContent = isProjectPanel 
            ? `Welcome to the ${this.options.projectName || 'project'} chat. How can I assist with this project?` 
            : 'Welcome to Minerva. How can I assist you today?';
        this.applyStyles(welcomeMsg, {
            padding: '10px',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderRadius: '8px',
            marginBottom: '10px',
            textAlign: 'center'
        });
        messagesContainer.appendChild(welcomeMsg);
        
        // Create input container
        const inputContainer = document.createElement('div');
        inputContainer.className = 'chat-input-container';
        this.applyStyles(inputContainer, {
            padding: '10px',
            borderTop: '1px solid rgba(100, 116, 139, 0.2)',
            display: 'flex'
        });
        container.appendChild(inputContainer);
        
        // Create input field
        const input = document.createElement('textarea');
        input.className = 'chat-input';
        input.placeholder = 'Type a message...';
        input.id = isProjectPanel ? 'project-chat-input' : 'floating-chat-input';
        this.applyStyles(input, {
            flex: '1',
            padding: '8px',
            borderRadius: '5px',
            border: '1px solid rgba(100, 116, 139, 0.3)',
            backgroundColor: 'rgba(30, 41, 59, 0.5)',
            color: '#e2e8f0',
            resize: 'none',
            maxHeight: '100px',
            minHeight: '38px'
        });
        inputContainer.appendChild(input);
        this.inputField = input;
        
        // Create send button
        const sendBtn = document.createElement('button');
        sendBtn.className = 'send-btn';
        sendBtn.textContent = 'Send';
        this.applyStyles(sendBtn, {
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            padding: '8px 12px',
            marginLeft: '8px',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease'
        });
        inputContainer.appendChild(sendBtn);
        this.sendButton = sendBtn;
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Send button event
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key to send
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }
    
    /**
     * Send a message
     */
    sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;
        
        // Add user message
        this.addMessageToChat(message, 'user');
        
        // Clear input
        this.inputField.value = '';
        
        // Show loading indicator
        const loadingIndicator = this.addLoadingIndicator();
        
        // Store conversation ID if not already set
        if (!this.conversationId) {
            this.conversationId = 'conv_' + Date.now();
            localStorage.setItem('minerva_conversation_id', this.conversationId);
        }
        
        // Wait a realistic time before response
        setTimeout(() => {
            // Remove loading indicator
            this.removeLoadingIndicator(loadingIndicator);
            
            try {
                // Try to use the server API first
                if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    // Prepare payload for real API
                    const payload = {
                        message: message,
                        conversation_id: this.conversationId,
                        store_in_memory: true
                    };
                    
                    // Add project context if in project mode
                    if (this.isProjectMode && this.options.projectId) {
                        payload.project_id = this.options.projectId;
                        payload.context = 'project';
                    }
                    
                    // Make API call
                    fetch(this.options.apiEndpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`API error: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Think Tank API class response:', data); // Debug log
                        
                        // Extract the response based on the available structure
                        let responseText = '';
                        let modelInfo = data.model_info || {};
                        
                        // Handle different response formats
                        if (data.response) {
                            // Direct response field
                            responseText = data.response;
                        } else if (data.responses && typeof data.responses === 'object') {
                            // Responses object with model outputs
                            const modelNames = Object.keys(data.responses);
                            if (modelNames.length > 0) {
                                responseText = data.responses[modelNames[0]];
                                // Update model info if available
                                if (data.processing_stats && !modelInfo.primary_model) {
                                    modelInfo = {
                                        primary_model: modelNames[0],
                                        processing_time: data.processing_stats.total_time
                                    };
                                }
                            }
                        } else if (data.message) {
                            // Message field
                            responseText = data.message;
                        } else {
                            // Fallback message
                            responseText = 'Sorry, I encountered an error processing your request.';
                            console.error('Unexpected response format:', data);
                        }
                        
                        // Add AI response
                        this.addMessageToChat(responseText, 'ai', modelInfo);
                        
                        // Update conversation ID if provided
                        if (data.conversation_id) {
                            this.conversationId = data.conversation_id;
                            localStorage.setItem('minerva_conversation_id', this.conversationId);
                        }
                        
                        // Offer project conversion if applicable
                        if (!this.isProjectMode && data.can_create_project) {
                            this.addProjectConversionOption(this.conversationId);
                        }
                    })
                    .catch(error => {
                        console.error('API error:', error);
                        // Fall back to mock response
                        this.handleWithMockResponse(message);
                    });
                } else {
                    // Use mock responses for testing
                    this.handleWithMockResponse(message);
                }
            } catch (error) {
                console.error('Error in chat processing:', error);
                this.handleWithMockResponse(message);
            }
        }, 800);
    }
    
    /**
     * Handle message with mock response for testing
     */
    handleWithMockResponse(message) {
        const lowerMessage = message.toLowerCase();
        let response;
        let modelInfo = {
            primary_model: 'Think Tank Blend',
            contributors: ['gpt-4', 'claude-3', 'gemini-pro', 'llama-3']
        };
        
        // Generate appropriate response based on user message
        if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage === 'hey') {
            response = "Hello! I'm Minerva, your AI assistant. How can I help you today?";
        } else if (lowerMessage.includes('name')) {
            response = "I'm Minerva, an AI assistant designed to help with a variety of tasks.";
        } else if (lowerMessage.includes('project') || lowerMessage.includes('minerva')) {
            response = "Minerva is a multi-model AI system that combines the strengths of different language models to provide better responses. I can help you with research, answering questions, and organizing information.";
        } else if (lowerMessage.includes('think tank')) {
            response = "The Think Tank is Minerva's core processing system. It evaluates queries across multiple AI models and combines their strengths for better answers. This multi-model approach allows for more robust responses than any single model could provide.";
        } else if (lowerMessage.includes('help')) {
            response = "I can help with a variety of tasks, including answering questions, providing information, organizing projects, and more. Just let me know what you need assistance with.";
        } else if (lowerMessage.includes('thanks') || lowerMessage.includes('thank you')) {
            response = "You're welcome! If you need any further assistance, don't hesitate to ask.";
        } else if (lowerMessage.includes('code') || lowerMessage.includes('python') || lowerMessage.includes('javascript')) {
            response = "Here's a simple example of code that might help with your task:\n```javascript\nfunction processData(input) {\n  const result = input.map(item => {\n    return { processed: item.value * 2 };\n  });\n  return result;\n}\n```\nYou can modify this based on your specific requirements.";
            modelInfo.primary_model = 'gpt-4';
        } else if (lowerMessage.includes('data') || lowerMessage.includes('analyze')) {
            response = "For data analysis, I recommend following these steps:\n1. Clean and preprocess your data\n2. Explore data through visualization\n3. Apply appropriate statistical methods\n4. Interpret results with domain knowledge\n5. Document your findings\n\nIs there a specific part of this process you need help with?";
        } else {
            // Default response
            response = "I understand you're asking about '" + message + "'. While I'm in testing mode right now with limited capabilities, in the full version I would be able to provide a comprehensive answer by drawing on multiple AI models. Is there something specific about this topic you'd like to explore?";
        }
        
        // Hide typing indicator and add response after a short delay
        setTimeout(() => {
            this.hideTypingIndicator();
            this.addMessageToChat(response, 'ai', modelInfo);
            
            // Store conversation ID if not already set
            if (!this.conversationId) {
                this.conversationId = 'mock-' + Date.now();
                localStorage.setItem('minerva_conversation_id', this.conversationId);
            }
            
            // Simulate offering project conversion
            if (message.length > 50 && !this.isProjectMode) {
                setTimeout(() => {
                    this.addProjectConversionOption(this.conversationId);
                }, 1000);
            }
        }, 1000);
    }
        

    
    /**
     * Add a message to the chat
     */
    addMessageToChat(message, sender, modelInfo = null) {
        const messageElement = document.createElement('div');
        
        if (sender === 'user') {
            messageElement.className = 'user-message';
            this.applyStyles(messageElement, {
                textAlign: 'right',
                marginLeft: 'auto',
                marginRight: '0',
                maxWidth: '80%',
                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                borderRadius: '10px 10px 0 10px',
                padding: '10px',
                marginBottom: '10px',
                wordWrap: 'break-word'
            });
            messageElement.textContent = message;
        } else if (sender === 'ai') {
            messageElement.className = 'ai-message';
            this.applyStyles(messageElement, {
                textAlign: 'left',
                marginRight: 'auto',
                marginLeft: '0',
                maxWidth: '80%',
                backgroundColor: 'rgba(30, 41, 59, 0.5)',
                borderRadius: '10px 10px 10px 0',
                padding: '10px',
                marginBottom: '10px',
                wordWrap: 'break-word'
            });
            
            if (modelInfo) {
                const messageContentElement = document.createElement('div');
                messageContentElement.textContent = message;
                messageElement.appendChild(messageContentElement);
                
                const modelInfoElement = document.createElement('div');
                modelInfoElement.className = 'model-info';
                this.applyStyles(modelInfoElement, {
                    fontSize: '10px',
                    color: '#94a3b8',
                    marginTop: '5px',
                    textAlign: 'left'
                });
                
                let modelText = 'Think Tank';
                if (typeof modelInfo === 'object' && modelInfo.primary_model) {
                    modelText = modelInfo.primary_model;
                } else if (Array.isArray(modelInfo)) {
                    modelText = modelInfo.join(', ');
                } else if (typeof modelInfo === 'string') {
                    modelText = modelInfo;
                }
                
                modelInfoElement.textContent = `Powered by ${modelText}`;
                messageElement.appendChild(modelInfoElement);
            } else {
                messageElement.textContent = message;
            }
        } else {
            messageElement.className = 'system-message';
            this.applyStyles(messageElement, {
                backgroundColor: 'rgba(234, 88, 12, 0.1)',
                borderRadius: '8px',
                padding: '10px',
                marginBottom: '10px',
                textAlign: 'center'
            });
            messageElement.textContent = message;
        }
        
        this.messagesContainer.appendChild(messageElement);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    /**
     * Add project conversion option
     */
    addProjectConversionOption(conversationId) {
        const conversionOption = document.createElement('div');
        conversionOption.className = 'project-conversion-option';
        this.applyStyles(conversionOption, {
            padding: '10px',
            margin: '10px 0',
            backgroundColor: 'rgba(130, 59, 246, 0.1)',
            borderRadius: '8px',
            fontSize: '14px',
            textAlign: 'center'
        });
        
        conversionOption.innerHTML = `
            <div>Would you like to convert this conversation to a project?</div>
            <div style="margin-top: 8px; display: flex; justify-content: center; gap: 10px;">
                <input type="text" placeholder="Project name" class="project-name-input" style="padding: 5px; border-radius: 4px; border: 1px solid rgba(100, 116, 139, 0.3); background-color: rgba(30, 41, 59, 0.5); color: #e2e8f0;">
                <button class="create-project-btn" style="background-color: #8B5CF6; color: white; border: none; border-radius: 4px; padding: 5px 10px; cursor: pointer;">Create</button>
            </div>
        `;
        
        this.messagesContainer.appendChild(conversionOption);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        // Add event listener to create project button
        const createButton = conversionOption.querySelector('.create-project-btn');
        const nameInput = conversionOption.querySelector('.project-name-input');
        
        createButton.addEventListener('click', () => {
            const projectName = nameInput.value.trim();
            if (!projectName) {
                alert('Please enter a project name');
                return;
            }
            
            // Show loading state
            createButton.textContent = 'Creating...';
            createButton.disabled = true;
            
            // Call API to create project from conversation
            fetch('/api/projects/create-from-conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    project_name: projectName
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Failed to create project');
                return response.json();
            })
            .then(data => {
                // Remove conversion option
                this.messagesContainer.removeChild(conversionOption);
                
                // Add success message
                this.addMessageToChat(`Successfully created project "${projectName}". You can now continue this conversation in the project context.`, 'system');
                
                // Redirect to the project page if we have a URL
                if (data.project_url) {
                    this.addMessageToChat(`Redirecting to project page...`, 'system');
                    setTimeout(() => {
                        window.location.href = data.project_url;
                    }, 1500);
                }
            })
            .catch(error => {
                console.error('Error creating project:', error);
                createButton.textContent = 'Create';
                createButton.disabled = false;
                alert('Failed to create project. Please try again.');
            });
        });
    }
    
    /**
     * Add loading indicator
     */
    addLoadingIndicator() {
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.id = 'loading-' + Date.now();
        this.applyStyles(loadingIndicator, {
            padding: '10px',
            margin: '5px 0',
            backgroundColor: 'rgba(30, 41, 59, 0.4)',
            borderRadius: '8px',
            textAlign: 'center'
        });
        
        const dots = document.createElement('div');
        dots.className = 'typing-dots';
        dots.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        loadingIndicator.appendChild(dots);
        
        this.messagesContainer.appendChild(loadingIndicator);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        return loadingIndicator;
    }
    
    /**
     * Remove loading indicator
     */
    removeLoadingIndicator(loadingIndicator) {
        if (loadingIndicator && this.messagesContainer.contains(loadingIndicator)) {
            this.messagesContainer.removeChild(loadingIndicator);
        }
    }
    
    /**
     * Create toggle button for floating chat
     */
    createToggleButton() {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'chat-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-comments"></i>';
        this.applyStyles(toggleBtn, {
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: '50px',
            height: '50px',
            borderRadius: '50%',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
            cursor: 'pointer',
            zIndex: '9998',
            display: 'none',
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: '20px'
        });
        
        toggleBtn.addEventListener('click', () => {
            this.toggleVisibility();
        });
        
        document.body.appendChild(toggleBtn);
        this.toggleButton = toggleBtn;
    }
    
    /**
     * Toggle visibility of floating chat
     */
    toggleVisibility() {
        this.chatContainer.style.display = this.chatContainer.style.display === 'none' ? 'flex' : 'none';
        this.toggleButton.style.display = this.chatContainer.style.display === 'none' ? 'flex' : 'none';
    }
    
    /**
     * Toggle minimized state of floating chat
     */
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            this.chatContainer.style.height = '50px';
            this.messagesContainer.style.display = 'none';
            this.chatContainer.querySelector('.chat-input-container').style.display = 'none';
            this.minimizeBtn.innerHTML = '□';
            this.minimizeBtn.title = 'Expand';
        } else {
            this.chatContainer.style.height = this.isMobileView ? '60%' : '500px';
            this.messagesContainer.style.display = 'block';
            this.chatContainer.querySelector('.chat-input-container').style.display = 'flex';
            this.minimizeBtn.innerHTML = '–';
            this.minimizeBtn.title = 'Minimize';
        }
    }
    
    /**
     * Handle window resize event
     */
    handleResize() {
        this.isMobileView = window.innerWidth < 768;
        
        if (this.isProjectMode) return; // Project panel doesn't need resize handling
        
        if (this.isMobileView) {
            this.chatContainer.style.width = '85%';
            this.chatContainer.style.height = this.isMinimized ? '50px' : '60%';
        } else {
            this.chatContainer.style.width = '350px';
            this.chatContainer.style.height = this.isMinimized ? '50px' : '500px';
        }
    }
    
    /**
     * Position the floating chat
     */
    positionChat(container) {
        // Clear all positions
        container.style.top = 'auto';
        container.style.bottom = 'auto';
        container.style.left = 'auto';
        container.style.right = 'auto';
        
        // Set position based on option
        switch(this.options.defaultPosition) {
            case 'bottom-right':
                container.style.bottom = '20px';
                container.style.right = '20px';
                break;
            case 'bottom-left':
                container.style.bottom = '20px';
                container.style.left = '20px';
                break;
            case 'top-right':
                container.style.top = '20px';
                container.style.right = '20px';
                break;
            case 'top-left':
                container.style.top = '20px';
                container.style.left = '20px';
                break;
            default:
                container.style.bottom = '20px';
                container.style.right = '20px';
        }
    }
    
    /**
     * Make an element draggable
     */
    makeDraggable(element) {
        const header = element.querySelector('.chat-header');
        if (!header) return;
        
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        header.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            e = e || window.event;
            
            // Skip if clicking on a button
            if (e.target.tagName === 'BUTTON' || e.target.parentElement.tagName === 'BUTTON') {
                return;
            }
            
            e.preventDefault();
            
            // Get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            // Add dragging class
            element.classList.add('dragging');
            
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        
        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            
            // Calculate the new cursor position
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            // Set the element's new position
            element.style.top = (element.offsetTop - pos2) + "px";
            element.style.left = (element.offsetLeft - pos1) + "px";
            
            // When manually positioned, clear automatic positioning
            element.style.bottom = 'auto';
            element.style.right = 'auto';
        }
        
        function closeDragElement() {
            // Stop moving when mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
            
            // Remove dragging class
            element.classList.remove('dragging');
        }
    }
    
    /**
     * Helper to apply styles to an element
     */
    applyStyles(element, styles) {
        for (const [property, value] of Object.entries(styles)) {
            element.style[property] = value;
        }
    }
}

// Initialize when window is fully loaded to ensure all DOM elements are ready
window.addEventListener('load', () => {
    console.log('Initializing Minerva Chat Integration...');
    
    // Check if we're on a project page by URL
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    const projectName = urlParams.get('name') || 'Unnamed Project';
    
    // Get chat options from data attributes if present
    const chatConfigElement = document.getElementById('minerva-chat-config');
    let chatOptions = {};
    
    if (chatConfigElement) {
        try {
            chatOptions = JSON.parse(chatConfigElement.dataset.config || '{}');
        } catch (e) {
            console.error('Error parsing chat config:', e);
        }
    }
    
    // Merge with project info if available
    if (projectId) {
        chatOptions.projectId = projectId;
        chatOptions.projectName = projectName;
    }
    
    // Add a small delay to ensure the DOM is fully ready
    setTimeout(() => {
        try {
            // Initialize chat integration
            window.minervaChat = new MinervaChatIntegration(chatOptions);
            console.log('Minerva Chat Integration initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Minerva Chat:', error);
        }
    }, 500);
});
