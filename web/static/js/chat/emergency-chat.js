/**
 * CRITICAL EMERGENCY FIX FOR MINERVA CHAT
 * This script directly implements basic chat functionality
 * when the regular implementation fails
 */

(function() {
    console.log('🚨 EMERGENCY CHAT FIX LOADING');
    
    // Wait for DOM to fully load
    document.addEventListener('DOMContentLoaded', function() {
        console.log('💬 Initializing emergency chat functionality');
        initEmergencyChat();
    });
    
    // If DOM already loaded, run now
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        console.log('💬 DOM already loaded, initializing emergency chat now');
        setTimeout(initEmergencyChat, 100);
    }
    
    function initEmergencyChat() {
        console.log('Starting emergency chat initialization');
        
        // Find the primary chat elements
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-message');
        const chatMessages = document.getElementById('chat-messages');
        
        if (!chatInput || !sendButton || !chatMessages) {
            console.error('Could not find all required chat elements!');
            console.log('Chat input found:', !!chatInput);
            console.log('Send button found:', !!sendButton);
            console.log('Chat messages found:', !!chatMessages);
            return;
        }
        
        console.log('Found all required chat elements, setting up handlers');
        
        // Remove all existing handlers by replacing elements with clones
        const newChatInput = chatInput.cloneNode(true);
        chatInput.parentNode.replaceChild(newChatInput, chatInput);
        
        const newSendButton = sendButton.cloneNode(true);
        sendButton.parentNode.replaceChild(newSendButton, sendButton);
        
        // Add direct event handlers
        newSendButton.addEventListener('click', function(e) {
            e.preventDefault();
            sendMessageEmergency(newChatInput, chatMessages);
        });
        
        newChatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessageEmergency(newChatInput, chatMessages);
            }
        });
        
        console.log('✅ Emergency chat handlers initialized successfully');
        
        // Add a welcome message to indicate the chat is working
        const systemMessageElement = document.createElement('div');
        systemMessageElement.className = 'system-message';
        systemMessageElement.innerHTML = '<p><em>Emergency chat mode activated. Basic functionality restored.</em></p>';
        chatMessages.appendChild(systemMessageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function sendMessageEmergency(inputElement, messagesElement) {
        console.log('Emergency send function called');
        
        // Get message text
        const message = inputElement.value.trim();
        console.log('Message content:', message);
        
        if (!message) {
            console.log('Message is empty, not sending');
            return;
        }
        
        // Clear input
        inputElement.value = '';
        
        // Create and add user message to chat
        const userMessage = document.createElement('div');
        userMessage.className = 'user-message';
        userMessage.innerHTML = `<p>${message}</p>`;
        messagesElement.appendChild(userMessage);
        
        // Record message to conversation history if available
        try {
            if (window.minervaMemory) {
                window.minervaMemory.push({
                    role: 'user',
                    content: message,
                    timestamp: new Date().toISOString()
                });
            }
            
            // If we have conversation storage (for project context)
            if (window.conversationHistory) {
                window.conversationHistory.push({
                    role: 'user',
                    content: message
                });
            }
            
            // Try to get conversation ID for context
            const conversationId = localStorage.getItem('minerva_conversation_id') || 
                                  ('conv_' + Date.now());
            
            // Store it if not already set
            if (!localStorage.getItem('minerva_conversation_id')) {
                localStorage.setItem('minerva_conversation_id', conversationId);
            }
        } catch (error) {
            console.error('Error adding to conversation memory:', error);
        }
        
        // Scroll to bottom
        messagesElement.scrollTop = messagesElement.scrollHeight;
        
        console.log('Attempting to send message to API...');
        
        // Try to use existing API call functions if available
        let apiCallSuccessful = false;
        
        // Option 1: External send function
        if (typeof window.MinervaExternalSendMessage === 'function') {
            try {
                console.log('Using external send message function');
                window.MinervaExternalSendMessage();
                apiCallSuccessful = true;
            } catch (error) {
                console.error('Error using external send function:', error);
            }
        }
        
        // Option 2: Original send message function
        if (!apiCallSuccessful && typeof window.sendMessage === 'function') {
            try {
                console.log('Using window.sendMessage function');
                window.sendMessage();
                apiCallSuccessful = true;
            } catch (error) {
                console.error('Error using window.sendMessage:', error);
            }
        }
        
        // Option 3: simulateThinkTankResponse function
        if (!apiCallSuccessful && typeof window.simulateThinkTankResponse === 'function') {
            try {
                console.log('Using simulateThinkTankResponse function');
                window.simulateThinkTankResponse(message);
                apiCallSuccessful = true;
            } catch (error) {
                console.error('Error using simulateThinkTankResponse:', error);
            }
        }
        
        // Option 4: Add a fallback response if all else fails
        if (!apiCallSuccessful) {
            console.log('All API call attempts failed, showing fallback response');
            
            // Add system response after a delay to simulate processing
            setTimeout(function() {
                const systemResponse = document.createElement('div');
                systemResponse.className = 'ai-message';
                systemResponse.innerHTML = `
                    <p><em>I've received your message: "${message}"</em></p>
                    <p>The server connection appears to be unavailable at the moment. Your message has been saved locally.</p>
                    <p>Please try refreshing the page or check your network connection.</p>
                `;
                messagesElement.appendChild(systemResponse);
                messagesElement.scrollTop = messagesElement.scrollHeight;
                
                // Add to memory if available
                try {
                    if (window.minervaMemory) {
                        window.minervaMemory.push({
                            role: 'assistant',
                            content: systemResponse.textContent,
                            timestamp: new Date().toISOString()
                        });
                    }
                    
                    if (window.conversationHistory) {
                        window.conversationHistory.push({
                            role: 'assistant',
                            content: systemResponse.textContent
                        });
                    }
                } catch (error) {
                    console.error('Error adding response to conversation memory:', error);
                }
            }, 1000);
        }
        
        console.log('Emergency message send complete');
    }
})();
