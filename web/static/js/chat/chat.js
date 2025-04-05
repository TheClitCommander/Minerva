/**
 * Minerva Chat Interface
 * Handles chat functionality and integration with API Analytics 
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('messages');
    
    // Initialize conversation state with memory persistence
    let conversationId = localStorage.getItem('minerva_conversation_id') || ('conv-' + Date.now());
    let messageCount = parseInt(localStorage.getItem('minerva_message_count') || '0');
    
    // Store conversation ID for persistence
    localStorage.setItem('minerva_conversation_id', conversationId);
    
    console.log('Chat initialized with conversation ID:', conversationId);
    console.log('Message count:', messageCount);
    
    // Analytics dashboard connection - for displaying real-time metrics when available
    let analyticsData = {
        requestCount: 0,
        responseTime: 0,
        lastModelUsed: '',
        modelRankings: []
    };
    
    // Function to fetch current analytics data
    async function updateAnalytics() {
        try {
            const response = await fetch('http://127.0.0.1:5005/api/stats');
            if (response.ok) {
                const data = await response.json();
                analyticsData = {
                    requestCount: data.total_requests || 0,
                    responseTime: data.average_latency || 0,
                    lastModelUsed: data.last_model_used || 'Unknown',
                    modelRankings: data.model_rankings || []
                };
                
                // Update analytics panel if it exists
                updateAnalyticsPanel();
            }
        } catch (error) {
            console.log('Analytics dashboard may not be available:', error);
        }
    }
    
    // Update the analytics panel with current data
    function updateAnalyticsPanel() {
        const panel = document.getElementById('analytics-panel');
        if (!panel) return;
        
        const requestCounter = document.getElementById('request-counter');
        const responseTimeEl = document.getElementById('response-time');
        const modelUsedEl = document.getElementById('model-used');
        
        if (requestCounter) requestCounter.textContent = analyticsData.requestCount;
        if (responseTimeEl) responseTimeEl.textContent = `${analyticsData.responseTime.toFixed(2)}ms`;
        if (modelUsedEl) modelUsedEl.textContent = analyticsData.lastModelUsed;
    }
    
    // Initial analytics update
    updateAnalytics();
    
    // Periodically update analytics (every 10 seconds)
    setInterval(updateAnalytics, 10000);
    
    // Function to add a message to the UI
    function addMessage(role, content, messageId = null) {
        console.log(`Adding ${role} message to chat`);
        
        // For the conversations page, we need to adapt to its expected message format
        // The conversations page expects messages with class "message user" or "message assistant"
        const messageDiv = document.createElement('div');
        
        // Map our internal roles to the expected HTML classes
        let cssClass = '';
        if (role === 'user') {
            cssClass = 'message user';
        } else if (role === 'bot' || role === 'assistant') {
            cssClass = 'message assistant';
        } else {
            cssClass = 'message system';
        }
        
        messageDiv.className = cssClass;
        
        if (messageId) {
            messageDiv.setAttribute('data-message-id', messageId);
        }
        
        // Ensure content is always a string before formatting
        let formattedContent;
        if (content === null || content === undefined) {
            formattedContent = 'No response content';
        } else if (typeof content === 'string') {
            formattedContent = content;
        } else if (typeof content === 'object') {
            try {
                formattedContent = JSON.stringify(content);
            } catch (e) {
                formattedContent = 'Unable to display response (object conversion error)';
            }
        } else {
            formattedContent = String(content);
        }
        
        console.log('Content type:', typeof content, 'Formatted as:', formattedContent);
        
        // Simple markdown-like formatting
        // Bold
        formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Handle code blocks
        formattedContent = formattedContent.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        formattedContent = formattedContent.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Create message content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = formattedContent;
        messageDiv.appendChild(contentDiv);
        
        // Add model info for bot messages
        if ((role === 'bot' || role === 'assistant') && messageId) {
            const infoDiv = document.createElement('div');
            infoDiv.className = 'model-info';
            infoDiv.innerHTML = `<span class="model-badge">Think Tank</span>`;
            messageDiv.appendChild(infoDiv);
        }
        
        // Add to chat history
        if (chatHistory) {
            chatHistory.appendChild(messageDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
        } else {
            console.error('Chat history container not found!');
        }
        
        // Remove welcome message if present
        const welcomeMsg = document.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }
    }
    
    // Function to handle feedback
    function handleFeedback(e) {
        const feedbackType = e.currentTarget.getAttribute('data-type');
        const messageId = e.currentTarget.getAttribute('data-message-id');
        
        // Highlight selected button
        e.currentTarget.classList.add('selected');
        
        // Remove selection from other button
        const otherType = feedbackType === 'thumbs-up' ? 'thumbs-down' : 'thumbs-up';
        const otherButton = e.currentTarget.parentNode.querySelector(`[data-type="${otherType}"]`);
        if (otherButton) {
            otherButton.classList.remove('selected');
        }
        
        // Send feedback to server
        fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId,
                feedback_type: feedbackType
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Feedback submitted:', data);
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
        });
    }
    
    // Function to show model information
    function showModelInfo(e) {
        const messageId = e.currentTarget.getAttribute('data-message-id');
        const messageEl = document.querySelector(`.message[data-message-id="${messageId}"]`);
        
        // Check if model info panel already exists
        let infoPanel = messageEl.querySelector('.model-info-panel');
        
        if (infoPanel) {
            // Toggle visibility if already exists
            infoPanel.style.display = infoPanel.style.display === 'none' ? 'block' : 'none';
            return;
        }
        
        // Create info panel
        infoPanel = document.createElement('div');
        infoPanel.className = 'model-info-panel';
        infoPanel.innerHTML = '<div class="loading">Loading model information...</div>';
        messageEl.appendChild(infoPanel);
        
        // Fetch model information
        fetch(`/api/model_info/${messageId}`)
            .then(response => response.json())
            .then(data => {
                let infoHtml = '<div class="model-info-content">';
                
                if (data.model_info) {
                    // Primary model used
                    infoHtml += `<h4>Primary Model: ${data.model_info.primary_model || 'Unknown'}</h4>`;
                    
                    // Model rankings if available
                    if (data.model_info.rankings && data.model_info.rankings.length > 0) {
                        infoHtml += '<h4>Model Rankings:</h4><ol>';
                        data.model_info.rankings.forEach(rank => {
                            infoHtml += `<li><strong>${rank.model}</strong>: Score ${rank.score.toFixed(2)}`;
                            if (rank.reasoning) {
                                infoHtml += `<br><small>${rank.reasoning}</small>`;
                            }
                            infoHtml += '</li>';
                        });
                        infoHtml += '</ol>';
                    }
                    
                    // Blending information if available
                    if (data.model_info.blending) {
                        infoHtml += '<h4>Response Blending:</h4>';
                        infoHtml += `<p>Strategy: ${data.model_info.blending.strategy || 'Standard'}</p>`;
                        
                        if (data.model_info.blending.contributions) {
                            infoHtml += '<ul>';
                            Object.entries(data.model_info.blending.contributions).forEach(([model, percentage]) => {
                                infoHtml += `<li>${model}: ${percentage}%</li>`;
                            });
                            infoHtml += '</ul>';
                        }
                    }
                } else {
                    infoHtml += '<p>No detailed model information available for this response.</p>';
                }
                
                infoHtml += '</div>';
                infoPanel.innerHTML = infoHtml;
            })
            .catch(error => {
                infoPanel.innerHTML = '<div class="error">Error loading model information.</div>';
                console.error('Error fetching model info:', error);
            });
    }
    
    // Function to send a message - made globally accessible and locked to use Think Tank
    window.sendMessage = function(message) {
        if (!message.trim()) return;
        
        console.log('Processing message:', message);
        
        // Clear input (ensure we reference the current input element)
        const currentInput = document.getElementById('message-input');
        if (currentInput) {
            currentInput.value = '';
            // Put focus back in the input
            currentInput.focus();
        }
        
        // Add user message to UI
        addMessage('user', message);
        
        // Increment message count and check for project conversion
        messageCount++;
        localStorage.setItem('minerva_message_count', messageCount);
        
        // Check if we should offer project conversion (after 3 messages)
        if (messageCount >= 3 && !document.querySelector('.project-conversion')) {
            offerProjectConversion();
        }
        
        // Add loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message bot-message loading';
        loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        chatHistory.appendChild(loadingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Send message to Think Tank API
        fetch('/api/think-tank', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                conversation_id: conversationId,
                store_in_memory: true
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            chatHistory.removeChild(loadingDiv);
            console.log('Received data from Think Tank API:', data);
            
            if (data.error) {
                // Show error message
                addMessage('system', `Error: ${data.error}`);
                return;
            }
            
            // Extract the response based on the available structure
            let responseText = '';
            
            // Handle different response formats
            if (data.response) {
                // Direct response field
                responseText = data.response;
            } else if (data.responses && typeof data.responses === 'object') {
                // Responses object with model outputs
                // Extract the first available model response
                const modelNames = Object.keys(data.responses);
                if (modelNames.length > 0) {
                    responseText = data.responses[modelNames[0]];
                }
            } else if (data.message) {
                // Message field
                responseText = data.message;
            } else {
                // Fallback to stringifying the data
                responseText = 'Sorry, I encountered an error processing your request.';
                console.error('Unexpected response format:', data);
            }
            
            // Add assistant response to UI
            addMessage('bot', responseText, data.message_id);
            
            // Dispatch event for Think Tank Bridge to visualize model data if available
            if (data.model_info || data.processing_stats) {
                const event = new CustomEvent('minerva-response-received', {
                    detail: data
                });
                document.dispatchEvent(event);
            }
            
            // Update analytics
            updateAnalytics();
        })
        .catch(error => {
            // Remove loading indicator
            chatHistory.removeChild(loadingDiv);
            
            // Show error message
            addMessage('system', `Error: Could not send message. ${error.message}`);
            console.error('Error sending message:', error);
        });
    }
    
    // Event listener for send button
    if (sendButton) {
        // Remove existing listeners by cloning
        const newSendButton = sendButton.cloneNode(true);
        if (sendButton.parentNode) {
            sendButton.parentNode.replaceChild(newSendButton, sendButton);
        }
        
        // Add listener to the new button
        newSendButton.addEventListener('click', function(e) {
            console.log('Send button clicked');
            e.preventDefault();
            e.stopPropagation();
            const currentInput = document.getElementById('message-input');
            if (currentInput) {
                sendMessage(currentInput.value);
            }
        });
    } else {
        console.error('Send button not found!');
    }
    
    // Event listener for Enter key - Direct implementation as per user instruction
    document.getElementById("message-input").addEventListener("keydown", function(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            console.log('Enter key pressed, preventing default');
            event.preventDefault();
            document.getElementById("send-button").click();
        }
    });
    
    // Function to offer project conversion after 3 messages
    function offerProjectConversion() {
        const conversionDiv = document.createElement('div');
        conversionDiv.className = 'chat-message system-message project-conversion';
        conversionDiv.innerHTML = `
            <div class="message-content">
                <p>Would you like to convert this conversation to a project?</p>
                <div class="project-form">
                    <input type="text" id="project-name" class="form-control" placeholder="Enter project name">
                    <button id="create-project-btn" class="btn btn-primary">Create Project</button>
                </div>
            </div>
        `;
        chatHistory.appendChild(conversionDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Add event listener for project creation
        document.getElementById('create-project-btn').addEventListener('click', createProject);
    }
    
    // Function to create a project from conversation
    function createProject() {
        const projectName = document.getElementById('project-name').value.trim();
        if (!projectName) return;
        
        // Create project with conversation ID
        fetch('/api/create-project', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_name: projectName,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove conversion prompt
            const conversionDiv = document.querySelector('.project-conversion');
            if (conversionDiv) {
                conversionDiv.remove();
            }
            
            // Add confirmation message
            const confirmDiv = document.createElement('div');
            confirmDiv.className = 'chat-message system-message';
            confirmDiv.innerHTML = `
                <div class="message-content">
                    <p>✅ Project "${projectName}" created successfully!</p>
                </div>
            `;
            chatHistory.appendChild(confirmDiv);
            chatHistory.scrollTop = chatHistory.scrollHeight;
            
            // Update projects list if available
            refreshProjectsList();
        })
        .catch(error => {
            console.error('Error creating project:', error);
            alert('Failed to create project. Please try again.');
        });
    }
    
    // Function to refresh projects list if it exists
    function refreshProjectsList() {
        const projectsContainer = document.getElementById('projects-container');
        if (!projectsContainer) return;
        
        fetch('/api/projects')
            .then(response => response.json())
            .then(data => {
                // Update projects container with new data
                if (data.projects && Array.isArray(data.projects)) {
                    // Implementation depends on your projects HTML structure
                    console.log('Projects refreshed with new data');
                }
            })
            .catch(error => {
                console.error('Error refreshing projects:', error);
            });
    }
    
    // Initialize the chat
    processInitialMessages();
    
    // Make functions available globally (for debugging)
    window.minervaChat = {
        addMessage,
        sendMessage,
        updateAnalytics
    };
});
