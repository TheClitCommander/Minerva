/**
 * Response Feedback System - Client-side JavaScript
 * 
 * Adds simple feedback buttons (helpful/not helpful) to AI responses
 * and collects user feedback to improve the system.
 */

class ResponseFeedbackSystem {
    constructor() {
        this.initEventListeners();
        this.sessionId = this.getSessionId();
    }
    
    /**
     * Initialize event listeners for the feedback system
     */
    initEventListeners() {
        // Add feedback buttons to each AI message
        document.addEventListener('DOMContentLoaded', () => {
            this.addFeedbackButtonsToMessages();
            
            // Watch for new messages and add feedback buttons
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                            this.addFeedbackButtonsToMessages();
                        }
                    });
                });
                
                observer.observe(chatContainer, { childList: true, subtree: true });
            }
        });
    }
    
    /**
     * Add feedback buttons to all AI messages that don't already have them
     */
    addFeedbackButtonsToMessages() {
        const aiMessages = document.querySelectorAll('.ai-message');
        
        aiMessages.forEach(message => {
            // Skip if this message already has feedback buttons
            if (message.querySelector('.message-feedback')) {
                return;
            }
            
            const messageId = message.getAttribute('data-message-id') || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
            if (!message.getAttribute('data-message-id')) {
                message.setAttribute('data-message-id', messageId);
            }
            
            // Create feedback container
            const feedbackContainer = document.createElement('div');
            feedbackContainer.className = 'message-feedback';
            feedbackContainer.innerHTML = `
                <div class="feedback-question">Was this response helpful?</div>
                <div class="feedback-buttons">
                    <button class="feedback-button feedback-helpful" data-value="helpful">
                        <svg width="16" height="16" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z"/>
                        </svg>
                        Helpful
                    </button>
                    <button class="feedback-button feedback-not-helpful" data-value="not_helpful">
                        <svg width="16" height="16" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v1.91l.01.01L1 14c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/>
                        </svg>
                        Not Helpful
                    </button>
                </div>
                <div class="feedback-reason-container" style="display: none;">
                    <textarea class="feedback-reason" placeholder="Please tell us why (optional)..."></textarea>
                    <button class="feedback-submit">Submit</button>
                </div>
                <div class="feedback-thank-you" style="display: none;">
                    Thank you for your feedback!
                </div>
            `;
            
            // Add event listeners to the buttons
            const helpfulButton = feedbackContainer.querySelector('.feedback-helpful');
            const notHelpfulButton = feedbackContainer.querySelector('.feedback-not-helpful');
            const reasonContainer = feedbackContainer.querySelector('.feedback-reason-container');
            const reasonTextarea = feedbackContainer.querySelector('.feedback-reason');
            const submitButton = feedbackContainer.querySelector('.feedback-submit');
            const thankYouMessage = feedbackContainer.querySelector('.feedback-thank-you');
            
            helpfulButton.addEventListener('click', () => {
                this.handleFeedbackSelection(messageId, 'helpful', reasonContainer, helpfulButton, notHelpfulButton);
            });
            
            notHelpfulButton.addEventListener('click', () => {
                this.handleFeedbackSelection(messageId, 'not_helpful', reasonContainer, helpfulButton, notHelpfulButton);
            });
            
            submitButton.addEventListener('click', () => {
                const reason = reasonTextarea.value.trim();
                this.submitFeedback(messageId, feedbackContainer.getAttribute('data-selected-feedback'), reason);
                reasonContainer.style.display = 'none';
                thankYouMessage.style.display = 'block';
            });
            
            // Find the message tools container or create one
            let toolsContainer = message.querySelector('.message-tools');
            if (!toolsContainer) {
                toolsContainer = document.createElement('div');
                toolsContainer.className = 'message-tools';
                message.appendChild(toolsContainer);
            }
            
            // Add the feedback container to the message
            message.appendChild(feedbackContainer);
        });
    }
    
    /**
     * Handle when a user selects a feedback option
     * 
     * @param {string} messageId - ID of the message
     * @param {string} feedbackValue - 'helpful' or 'not_helpful'
     * @param {HTMLElement} reasonContainer - Container for the reason textarea
     * @param {HTMLElement} helpfulButton - The helpful button element
     * @param {HTMLElement} notHelpfulButton - The not helpful button element
     */
    handleFeedbackSelection(messageId, feedbackValue, reasonContainer, helpfulButton, notHelpfulButton) {
        // Store the selected feedback value
        reasonContainer.parentElement.setAttribute('data-selected-feedback', feedbackValue);
        
        // Update button styling
        helpfulButton.classList.remove('selected');
        notHelpfulButton.classList.remove('selected');
        
        if (feedbackValue === 'helpful') {
            helpfulButton.classList.add('selected');
        } else {
            notHelpfulButton.classList.add('selected');
        }
        
        // Show the reason container
        reasonContainer.style.display = 'block';
        
        // If user clicked "Helpful" and doesn't provide a reason after 3 seconds, auto-submit
        if (feedbackValue === 'helpful') {
            this.autoSubmitTimeout = setTimeout(() => {
                if (reasonContainer.querySelector('.feedback-reason').value.trim() === '') {
                    this.submitFeedback(messageId, feedbackValue, '');
                    reasonContainer.style.display = 'none';
                    reasonContainer.parentElement.querySelector('.feedback-thank-you').style.display = 'block';
                }
            }, 3000);
        } else {
            // Clear any existing timeout if user selected "Not Helpful"
            if (this.autoSubmitTimeout) {
                clearTimeout(this.autoSubmitTimeout);
            }
        }
    }
    
    /**
     * Get the current session/conversation ID from the page
     * 
     * @returns {string|null} The session ID or null if not found
     */
    getSessionId() {
        // Try to get from URL parameters first
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('conversation_id') || urlParams.get('session_id');
        if (sessionId) return sessionId;
        
        // Try to get from data attributes
        const conversationContainer = document.querySelector('[data-conversation-id]');
        if (conversationContainer) {
            return conversationContainer.getAttribute('data-conversation-id');
        }
        
        // Finally check for any global variables
        if (typeof conversationId !== 'undefined') {
            return conversationId;
        }
        
        return null;
    }
    
    /**
     * Extract model information from the message element
     * 
     * @param {HTMLElement} messageElement - The message DOM element
     * @returns {Object} Object with model information
     */
    getModelInfo(messageElement) {
        const modelInfo = {};
        
        // Try to extract from data attributes first (most accurate)
        if (messageElement.hasAttribute('data-model')) {
            modelInfo.model = messageElement.getAttribute('data-model');
        }
        
        if (messageElement.hasAttribute('data-model-version')) {
            modelInfo.model_version = messageElement.getAttribute('data-model-version');
        }
        
        // Try to extract from model badge if present
        if (!modelInfo.model) {
            const modelBadge = messageElement.querySelector('.model-badge');
            if (modelBadge) {
                modelInfo.model = modelBadge.textContent.trim();
            }
        }
        
        // Try to extract from class names as last resort
        if (!modelInfo.model) {
            const classList = Array.from(messageElement.classList);
            const modelClass = classList.find(cls => cls.startsWith('model-'));
            if (modelClass) {
                modelInfo.model = modelClass.replace('model-', '');
            }
        }
        
        return modelInfo;
    }
    
    /**
     * Submit feedback to the server
     * 
     * @param {string} messageId - ID of the message
     * @param {string} feedbackValue - 'helpful' or 'not_helpful'
     * @param {string} reason - Optional feedback reason
     */
    submitFeedback(messageId, feedbackValue, reason) {
        // Get message content and query
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        let messageContent = '';
        let queryContent = '';
        
        if (messageElement) {
            const contentElement = messageElement.querySelector('.message-content');
            if (contentElement) {
                messageContent = contentElement.textContent;
            }
            
            // Find the previous user message
            let prevElement = messageElement.previousElementSibling;
            while (prevElement) {
                if (prevElement.classList.contains('user-message')) {
                    const userContentElement = prevElement.querySelector('.message-content');
                    if (userContentElement) {
                        queryContent = userContentElement.textContent;
                    }
                    break;
                }
                prevElement = prevElement.previousElementSibling;
            }
        }
        
        // Get model information
        const modelInfo = messageElement ? this.getModelInfo(messageElement) : {};
        
        // Prepare feedback data
        const feedbackData = {
            response_id: messageId,  // Use response_id to match the API expectations
            message_id: messageId,   // Keep for backwards compatibility
            session_id: this.sessionId,
            feedback: feedbackValue,
            reason: reason,
            query: queryContent,
            response: messageContent,
            timestamp: new Date().toISOString(),
            ...modelInfo  // Spread the model info
        };
        
        // Send feedback to server
        fetch('/api/submit_feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback submitted successfully:', data);
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
        });
    }
}

// Initialize the feedback system
const responseFeedbackSystem = new ResponseFeedbackSystem();

// Add styles for the feedback system
document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style');
    style.textContent = `
        .message-feedback {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        
        .feedback-question {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .feedback-buttons {
            display: flex;
            gap: 10px;
        }
        
        .feedback-button {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 5px 10px;
            border: 1px solid #ddd;
            background: #f5f5f5;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .feedback-button:hover {
            background: #e9e9e9;
        }
        
        .feedback-button.selected {
            background: #e1f5fe;
            border-color: #03a9f4;
            color: #0277bd;
        }
        
        .feedback-helpful.selected {
            background: #e8f5e9;
            border-color: #4caf50;
            color: #2e7d32;
        }
        
        .feedback-not-helpful.selected {
            background: #ffebee;
            border-color: #f44336;
            color: #c62828;
        }
        
        .feedback-reason-container {
            margin-top: 10px;
        }
        
        .feedback-reason {
            width: 100%;
            min-height: 60px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 5px;
            font-family: inherit;
        }
        
        .feedback-submit {
            padding: 5px 15px;
            background: #2196f3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .feedback-thank-you {
            margin-top: 10px;
            padding: 8px;
            background: #e8f5e9;
            border-radius: 4px;
            color: #2e7d32;
            text-align: center;
        }
    `;
    document.head.appendChild(style);
});
