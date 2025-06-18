/**
 * Minerva Chat Interface
 * Handles chat interactions, project management, and model insights visualization
 * Includes WebSocket integration for real-time Think Tank AI responses
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const createProjectBtn = document.getElementById('create-project-btn');
    const projectsContainer = document.getElementById('projects-container');
    const connectionStatus = document.getElementById('connection-status');
    
    // WebSocket initialization
    let socket;
    let sessionId = localStorage.getItem('minerva_session_id') || null;
    let userId = localStorage.getItem('minerva_user_id') || 'user_' + Date.now().toString(36);
    let isConnected = false;
    
    // Session and user tracking
    let activeModels = ['gpt-4', 'claude-3', 'gemini', 'llama-3']; // Available models
    let selectedModel = localStorage.getItem('minerva_selected_model') || 'blend';
    let webResearchEnabled = localStorage.getItem('minerva_web_research') === 'true' || false;
    let researchDepth = localStorage.getItem('minerva_research_depth') || 'medium';
    
    // Initialize WebSocket connection
    function initializeWebSocket() {
        // Close any existing connection
        if (socket) {
            socket.close();
        }
        
        // Create a new connection
        socket = io.connect(window.location.origin, {
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });
        
        // Set up event handlers
        setupSocketEventHandlers();
        
        // Join or create session after connection
        socket.on('connect', () => {
            joinChatSession();
        });
        
        return socket;
    }
    
    // Join or create a chat session
    function joinChatSession() {
        if (!isConnected) return;
        
        console.log('Joining chat session with ID:', sessionId);
        
        socket.emit('join_session', {
            session_id: sessionId,
            user_id: userId
        });
        
        addSystemMessage('Connecting to Minerva Think Tank...', 'info');
    }
    
    // Think Tank performance metrics (these would come from the API in production)
    const thinkTankMetrics = {
        blendingPercentage: 87.5,
        rankAccuracy: 92.3,
        routingEfficiency: 95.1,
        modelUsage: {
            'gpt-4': 42,
            'claude-3': 35,
            'gemini': 15,
            'llama-3': 8
        },
        queryTypes: {
            'technical': 35,
            'creative': 25,
            'factual': 30,
            'procedural': 10
        }
    };
    
    // Update performance metrics with real-time data
    function updatePerformanceMetrics() {
        // Update performance metrics in the UI
        document.getElementById('blending-percentage').innerText = thinkTankMetrics.blendingPercentage.toFixed(1) + '%';
        document.getElementById('rank-accuracy').innerText = thinkTankMetrics.rankAccuracy.toFixed(1) + '%';
        document.getElementById('routing-efficiency').innerText = thinkTankMetrics.routingEfficiency.toFixed(1) + '%';
        
        // Update model usage chart if element exists
        const modelUsageElement = document.getElementById('model-usage-chart');
        if (modelUsageElement && thinkTankMetrics.modelUsage) {
            createModelUsageChart(modelUsageElement, thinkTankMetrics.modelUsage);
        }
        
        // Update query type distribution if element exists
        const queryTypeElement = document.getElementById('query-type-chart');
        if (queryTypeElement && thinkTankMetrics.queryTypes) {
            createQueryTypeChart(queryTypeElement, thinkTankMetrics.queryTypes);
        }
    }
    
    // Initialize performance metrics and add toggle function for model details
    updatePerformanceMetrics();
    
    // Function to toggle model details visibility
    window.toggleModelDetails = function(button) {
        const detailsContainer = button.nextElementSibling;
        const isHidden = detailsContainer.classList.contains('hidden');
        
        // Toggle visibility
        if (isHidden) {
            detailsContainer.classList.remove('hidden');
            button.textContent = 'Hide model details';
            
            // Find the details content container
            const detailsContent = detailsContainer.querySelector('.model-details-content');
            if (detailsContent && !detailsContent.innerHTML.trim()) {
                // Find the closest message to get model info
                const messageElement = button.closest('.message');
                const messageId = messageElement.dataset.messageId;
                
                // Try to find model info in our session cache
                if (messageId && sessionModelInfo[messageId]) {
                    const modelInfo = sessionModelInfo[messageId];
                    // Create visualization of model performance
                    createModelPerformanceChart(detailsContent, modelInfo);
                } else {
                    detailsContent.innerHTML = '<p>Detailed model information not available for this message.</p>';
                }
            }
        } else {
            detailsContainer.classList.add('hidden');
            button.textContent = 'Show model details';
        }
    };
    
    // Cache for storing model info by message ID
    const sessionModelInfo = {};
    
    // Chat functionality
    function addUserMessage(message) {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `
            <div>${message}</div>
            <div class="message-time">${timestamp}</div>
        `;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    function addBotMessage(message, modelInfo) {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.dataset.messageId = Date.now().toString();
        
        let modelInfoHtml = '';
        if (modelInfo) {
            try {
                // Safely extract top model information
                let topModel = 'Unknown';
                let blendingInfo = 'No blending information available';
                let modelCount = 0;
                
                // Store model info in session cache for visualization
                if (typeof sessionModelInfo !== 'undefined') {
                    sessionModelInfo[messageElement.dataset.messageId] = modelInfo;
                }
                
                if (modelInfo.rankings && modelInfo.rankings.length > 0) {
                    topModel = modelInfo.rankings[0].model;
                    // Show a more user-friendly model name (remove path/version if present)
                    const simplifiedModelName = topModel.split('/').pop().replace(/-\d+$/, '');
                    topModel = simplifiedModelName;
                    modelCount = modelInfo.rankings.length;
                }
                
                if (modelInfo.blended) {
                    // Get blending strategy in a user-friendly format
                    const strategyName = modelInfo.blending?.strategy || 'custom';
                    blendingInfo = `Using Think Tank blending: ${strategyName}`;
                } else {
                    blendingInfo = 'Using top model response';
                }
                
                // Create enhanced model info section with visualization capabilities
                modelInfoHtml = `
                    <div class="message-model-info">
                        <div class="model-summary">
                            <div><strong>Top model:</strong> ${topModel}</div>
                            <div>${blendingInfo}</div>
                            <div><small>${modelCount} models evaluated</small></div>
                        </div>
                        ${modelInfo.blended ? '<div class="blended-indicator">Blended Response</div>' : ''}
                        <button class="model-details-toggle" onclick="toggleModelDetails(this)">Show model details</button>
                        <div class="model-details hidden">
                            <div id="model-details-${messageElement.dataset.messageId}" class="model-details-content"></div>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error creating model info UI:', error);
                // Simple fallback in case of error
                modelInfoHtml = `<div class="message-model-info"><div>Think Tank response</div></div>`;
            }
        }
        
        messageElement.innerHTML = `
            <div>${message}</div>
            <div class="message-time">${timestamp}</div>
            ${modelInfoHtml}
        `;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Clear input
        chatInput.value = '';
        
        // Add user message to chat
        addUserMessage(message);
        
        // Clear welcome message if it exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Send to backend using our Think Tank API
        sendMessageToAPI(message);
    }
    
    // Set up WebSocket event handlers
    function setupSocketEventHandlers() {
        // Connection events
        socket.on('connect', () => {
            console.log('WebSocket connected successfully');
            isConnected = true;
            updateConnectionStatus('Connected', true);
        });
        
        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            isConnected = false;
            updateConnectionStatus('Disconnected', false);
        });
        
        socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            isConnected = false;
            updateConnectionStatus('Connection Error', false);
        });
        
        // Session management
        socket.on('session_joined', (data) => {
            console.log('Joined session:', data);
            sessionId = data.session_id;
            localStorage.setItem('minerva_session_id', sessionId);
            
            // Add system message to confirm session connection
            addSystemMessage(`Connected to Minerva Think Tank session: ${sessionId.substring(0, 8)}...`, 'success');
            
            // Load previous messages if any
            if (data.messages && data.messages.length > 0) {
                loadChatHistory(data.messages);
            }
        });
        
        // Think Tank response handlers
        socket.on('ai_response', handleThinkTankResponse);
        
        // System messages (errors, notifications)
        socket.on('system_message', (data) => {
            console.log('System message:', data);
            const status = data.status || 'info';
            addSystemMessage(data.message, status);
        });
        
        // Processing updates for better UX
        socket.on('processing_update', (data) => {
            console.log('Processing update:', data);
            updateProcessingStatus(data.step);
        });
        
        // Error handling
        socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            hideTypingIndicator();
            addSystemMessage(data.message || 'An error occurred with the Think Tank service.', 'error');
        });
    }
    
    // Load chat history from server response
    function loadChatHistory(messages) {
        console.log('Loading chat history:', messages);
        // Clear existing messages first
        chatHistory.innerHTML = '';
        
        // Add each message to the chat history
        messages.forEach(msg => {
            if (msg.sender_type === 'user') {
                addUserMessage(msg.content);
            } else if (msg.sender_type === 'ai') {
                // Extract model info from metadata if available
                const modelInfo = msg.metadata || null;
                addBotMessage(msg.content, modelInfo);
            } else if (msg.sender_type === 'system') {
                addSystemMessage(msg.content, msg.metadata?.status || 'info');
            }
        });
    }
    
    // Handle Think Tank responses from different event types with enhanced model info handling
    function handleThinkTankResponse(data) {
        console.log('Received Think Tank response:', data);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Handle different response formats
        let responseText = '';
        let modelInfo = null;
        let messageId = data.session_id || Date.now().toString();
        
        // Extract response text
        if (data.response) {
            responseText = data.response;
        } else if (data.text) {
            responseText = data.text;
        } else if (data.content) {
            responseText = data.content;
        } else if (data.message) {
            responseText = data.message;
        } else {
            responseText = 'Received an empty response from the Think Tank.';
        }
        
        // Extract and process model information
        if (data.model_info) {
            modelInfo = data.model_info;
            
            // Store model info in session cache for later visualization
            sessionModelInfo[messageId] = modelInfo;
            
            // Process metrics from model info
            if (typeof processModelInfo === 'function') {
                processModelInfo(modelInfo);
            }
        }
        
        // Verify the response belongs to our session
        if (data.session_id && data.session_id !== sessionId) {
            console.log('Ignoring response for different session:', data.session_id);
            return;
        }
        
        // Add bot message with enhanced model information - ONLY ADD THE MESSAGE ONCE
        if (typeof addBotMessageWithModelInfo === 'function') {
            // Use the enhanced version if available
            addBotMessageWithModelInfo(document.getElementById('chat-messages'), responseText, modelInfo, messageId);
        } else {
            // Fallback to basic message rendering
            addBotMessage(responseText, modelInfo);
        }
        
        // Update analytics data
        if (typeof updateAnalyticsFromAPI === 'function') {
            updateAnalyticsFromAPI();
        }
        
        // Update analytics if available
        if (data.model_info) {
            if (typeof updateModelMetrics === 'function') {
                updateModelMetrics(data.model_info);
            }
            
            // Update model visualizations
            if (typeof updateModelPerformanceVisualizations === 'function') {
                updateModelPerformanceVisualizations(data.model_info);
            }
            
            // Log detailed model evaluation for analysis
            if (typeof logModelEvaluation === 'function') {
                logModelEvaluation(data.model_info);
            }
        }
        
        // Update UI to show Think Tank is ready for next query
        if (typeof updateThinkTankReadyState === 'function') {
            updateThinkTankReadyState();
        }
    }
    
    // Update the connection status indicator with detailed information
    function updateConnectionStatus(status, isConnected) {
        if (connectionStatus) {
            connectionStatus.textContent = status;
            connectionStatus.className = isConnected ? 'connected' : 'disconnected';
            
            // Update Think Tank status in UI
            const thinkTankStatus = document.getElementById('think-tank-status');
            if (thinkTankStatus) {
                thinkTankStatus.textContent = isConnected ? 'ONLINE' : 'OFFLINE';
                thinkTankStatus.className = isConnected ? 'status-online' : 'status-offline';
            }
            
            // Log connection status for debugging
            console.log(`Think Tank connection status: ${status} (${isConnected ? 'connected' : 'disconnected'})`);
        }
    }
    
    // Update the processing status for better UX
    function updateProcessingStatus(step) {
        // You can implement a progress bar or step indicator here
        console.log('Processing step:', step);
    }
    
    // Send message to the Think Tank via WebSocket with enhanced payload
    function sendMessageToAPI(userMessage) {
        // Show typing indicator
        showTypingIndicator();
        
        // Get active project and branch if any
        const activeProject = document.querySelector('.active-project');
        const projectId = activeProject ? activeProject.dataset.projectId : null;
        const activeBranch = activeProject ? 
            activeProject.querySelector('.branch-node[style*="font-weight: bold"]')?.textContent : 'main';
        
        // Generate a unique message ID
        const messageId = 'msg_' + Date.now() + '_' + Math.floor(Math.random() * 1000);
        
        // Get model preference from UI if it exists
        if (document.getElementById('model-select')) {
            selectedModel = document.getElementById('model-select').value;
            localStorage.setItem('minerva_selected_model', selectedModel);
        }
        
        // Get web research options from UI if they exist
        if (document.getElementById('web-research-toggle')) {
            webResearchEnabled = document.getElementById('web-research-toggle').checked;
            localStorage.setItem('minerva_web_research', webResearchEnabled);
        }
        
        if (document.getElementById('research-depth')) {
            researchDepth = document.getElementById('research-depth').value;
            localStorage.setItem('minerva_research_depth', researchDepth);
        }
        
        // Add appropriate system message based on settings
        let processingMsg = 'Processing with Think Tank';
        if (selectedModel !== 'blend') {
            processingMsg += ` using ${selectedModel} model`;
        } else {
            processingMsg += ' using blended multi-model approach';
        }
        
        if (webResearchEnabled) {
            processingMsg += ' with web research';
        }
        
        addSystemMessage(processingMsg + '...', 'processing');
        
        // Update UI to show connection is active
        updateConnectionStatus('Processing', true);
        
        // Prepare enhanced payload with model selection and web research options
        const payload = {
            message: userMessage,
            session_id: sessionId,
            user_id: userId,
            message_id: messageId,
            model_preference: selectedModel,
            enable_web_research: webResearchEnabled,
            research_depth: researchDepth,
            mode: 'think_tank',
            project_id: projectId,
            branch_id: activeBranch || 'main',
            include_model_info: true
        };
        
        // Log the enhanced payload
        console.log('Sending message with options:', payload);
        
        // First ensure we have a connection
        if (!socket || !isConnected) {
            console.log('Socket not connected, initializing...');
            socket = initializeWebSocket();
            
            // Wait a bit for the connection to establish
            setTimeout(() => {
                if (isConnected) {
                    emitChatMessage(payload);
                } else {
                    console.warn('WebSocket connection failed, using fallback');
                    fallbackToRESTAPI(payload);
                }
            }, 1000);
        } else {
            // Use the WebSocket connection
            emitChatMessage(payload);
        }
    }
    
    // Emit the chat message via WebSocket
    function emitChatMessage(payload) {
        console.log('Sending message via WebSocket:', payload);
        
        // Add system message to indicate we're using the Think Tank
        addSystemMessage('Processing with Think Tank...');
        
        // Emit the message event
        socket.emit('chat_message', payload);
        
        // Set a timeout for fallback in case WebSocket response takes too long
        setTimeout(() => {
            // If we haven't received a response yet and the typing indicator is still showing
            if (document.querySelector('.typing-indicator')) {
                console.log('WebSocket response timeout, checking connection...');
                
                // Check if we've lost connection
                if (!isConnected) {
                    fallbackToRESTAPI(payload);
                }
            }
        }, 10000); // 10 second timeout
    }
    
    // Fallback to REST API if WebSocket fails
    function fallbackToRESTAPI(payload) {
        console.log('Falling back to REST API');
        
        fetch('/api/process_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
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
            hideTypingIndicator();
            
            // The API returns response content in data.response
            const responseContent = data.response || 'No response from AI';
            
            // Add bot response to chat with model_info if available
            addBotMessage(responseContent, data.model_info);
            
            // Update analytics
            updateAnalyticsFromAPI();
            
            console.log('Successfully received and processed chat response via REST API', data);
        })
        .catch(error => {
            console.error('Chat API Error:', error);
            hideTypingIndicator();
            
            // Add more detailed debugging information
            let errorMessage = 'Sorry, there was an error connecting to the Think Tank.';
            
            // Show a more specific error message based on the error
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Network error: Could not connect to the server. Please check your connection.';
            } else if (error.message.includes('API error: 404')) {
                errorMessage = 'The chat API endpoint could not be found. This is likely a server configuration issue.';
            } else if (error.message.includes('API error: 500')) {
                errorMessage = 'The server encountered an internal error processing your message.';
            }
            
            // Log more detailed diagnostics
            console.log('Request payload was:', payload);
            console.log('API URL was:', '/api/process_message');
            
            // Show error message
            addSystemMessage(errorMessage);
        });
    }
    
    // Show typing indicator in chat
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator message bot-message';
        typingIndicator.innerHTML = `
            <div class="typing-dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        chatHistory.appendChild(typingIndicator);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Add system message (for errors, notifications, etc.) with status-based styling
    function addSystemMessage(message, status = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = `message system-message status-${status}`;
        
        // Choose icon based on status
        let icon = 'info-circle';
        if (status === 'error') icon = 'exclamation-triangle';
        else if (status === 'processing') icon = 'sync fa-spin';
        else if (status === 'success') icon = 'check-circle';
        
        messageElement.innerHTML = `
            <div class="system-notification">
                <i class="fas fa-${icon} me-2"></i>
                ${message}
            </div>
            <div class="message-time">${timestamp}</div>
        `;
        chatHistory.appendChild(messageElement);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Template responses for simulation
    function generateCodeResponse() {
        return `Here's a Python function to solve this problem:

\`\`\`python
def process_data(data_list):
    """
    Process a list of data items and return aggregated results.
    
    Args:
        data_list (list): List of data points to process
        
    Returns:
        dict: Processed results with statistics
    """
    if not data_list:
        return {"error": "Empty data list provided"}
        
    results = {
        "total": len(data_list),
        "sum": sum(data_list),
        "average": sum(data_list) / len(data_list),
        "min": min(data_list),
        "max": max(data_list)
    }
    
    return results
\`\`\`

This function takes a list of numeric data, validates it's not empty, and returns a dictionary with some basic statistical analysis. You can extend it by adding more statistical measures as needed.`;
    }
    
    function generateComparisonResponse() {
        return `When comparing these options, several key differences emerge:

**Option A:**
- More cost-effective upfront
- Simpler implementation
- Less scalable for future growth
- Limited customization options

**Option B:**
- Higher initial investment
- More complex setup
- Excellent scalability
- Extensive customization capabilities

For your specific situation, Option B likely provides better long-term value despite the higher upfront cost, especially if you anticipate growth in the next 1-2 years. The scalability will prevent you from needing to migrate to a new solution later.`;
    }
    
    function generateFactualResponse() {
        return `The process of photosynthesis converts light energy into chemical energy in plants and some other organisms. It occurs primarily in the chloroplasts of plant cells, specifically in structures called thylakoids.

The basic equation for photosynthesis is:
6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂

This process occurs in two main stages:
1. **Light-dependent reactions**: These occur in the thylakoid membrane and convert light energy into chemical energy (ATP and NADPH)
2. **Light-independent reactions** (Calvin cycle): These occur in the stroma and use the chemical energy produced in the first stage to create glucose molecules

Photosynthesis is crucial for life on Earth as it produces oxygen and serves as the primary entry point for energy into most ecosystems.`;
    }
    
    function generateGeneralResponse() {
        return `That's an interesting question. Based on current understanding, there are multiple approaches you could consider.

First, it's important to establish clear objectives before proceeding. This helps ensure that whatever solution you implement aligns with your overall goals.

Consider starting with a small-scale implementation to test assumptions and gather feedback. This iterative approach often yields better results than attempting to build the complete solution all at once.

Would you like me to explore any specific aspect of this topic in more detail?`;
    }
    
    // Update analytics from API data with enhanced error handling for real AI integration
    function updateAnalyticsFromAPI() {
        // Fetch analytics data from our endpoint
        fetch('/api/think_tank/analytics')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received analytics data:', data);
                
                // Update Think Tank metrics from API data
                if (data.think_tank_metrics) {
                    // Update basic metrics
                    thinkTankMetrics.blendingPercentage = data.think_tank_metrics.blending_percentage || thinkTankMetrics.blendingPercentage;
                    thinkTankMetrics.rankAccuracy = data.think_tank_metrics.rank_accuracy || thinkTankMetrics.rankAccuracy;
                    thinkTankMetrics.routingEfficiency = data.think_tank_metrics.routing_efficiency || thinkTankMetrics.routingEfficiency;
                    
                    // Update model usage data
                    if (data.think_tank_metrics.model_usage) {
                        thinkTankMetrics.modelUsage = data.think_tank_metrics.model_usage;
                        console.log('Updated model usage data:', thinkTankMetrics.modelUsage);
                    }
                    
                    // Update query type data
                    if (data.think_tank_metrics.query_types) {
                        thinkTankMetrics.queryTypes = data.think_tank_metrics.query_types;
                        console.log('Updated query type data:', thinkTankMetrics.queryTypes);
                    }
                    
                    // Add capability profiles if available
                    if (data.think_tank_metrics.model_capabilities) {
                        thinkTankMetrics.modelCapabilities = data.think_tank_metrics.model_capabilities;
                        console.log('Updated model capabilities:', thinkTankMetrics.modelCapabilities);
                    }
                }
                
                // Update display
                updatePerformanceMetrics();
                
                // If we have charts initialized, update them too
                if (typeof updateAnalyticsCharts === 'function') {
                    updateAnalyticsCharts(data);
                }
            })
            .catch(error => {
                console.error('Error updating analytics:', error);
            });
    }
    
    // Project management functionality
    function createNewProject() {
        // Show dialog to get project name
        const projectName = prompt('Enter project name:', `Project ${document.querySelectorAll('.project-card').length + 1}`);
        if (!projectName) return; // User cancelled
        
        const projectDescription = prompt('Enter project description (optional):', '');
        
        // Call API to create project
        fetch('/api/chat/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: projectName,
                description: projectDescription || ''
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(project => {
            // Create project card in UI
            const projectCol = document.createElement('div');
            projectCol.className = 'col-md-4 mb-3';
            
            projectCol.innerHTML = `
                <div class="project-card" data-project-id="${project.id}">
                    <div class="project-header d-flex justify-content-between">
                        <h5>${project.name}</h5>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-link dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu dropdown-menu-end">
                                <li><a class="dropdown-item rename-project" href="#">Rename</a></li>
                                <li><a class="dropdown-item archive-project" href="#">Archive</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item text-danger delete-project" href="#">Delete</a></li>
                            </ul>
                        </div>
                    </div>
                    <p class="project-description">${project.description || 'New project with 0 conversations'}</p>
                    <div class="project-branches" id="project-${project.id}-branches">
                        <div class="branch-node">Main Thread</div>
                    </div>
                </div>
            `;
            
            projectsContainer.appendChild(projectCol);
            
            // Select the new project
            setTimeout(() => {
                projectCol.querySelector('.project-card').click();
            }, 100);
        })
        .catch(error => {
            console.error('Error creating project:', error);
            alert(`Failed to create project: ${error.message}`);
        });
    }
    
    // Add click event to project cards for project selection
    projectsContainer.addEventListener('click', function(e) {
        const projectCard = e.target.closest('.project-card');
        if (!projectCard) return;
        
        // Remove active class from all projects
        document.querySelectorAll('.project-card').forEach(card => {
            card.classList.remove('active-project');
            card.style.borderColor = '#e0e0e0';
        });
        
        // Add active class to selected project
        projectCard.classList.add('active-project');
        projectCard.style.borderColor = '#007bff';
        projectCard.style.borderWidth = '2px';
        
        const projectId = projectCard.dataset.projectId;
        console.log('Selected project:', projectId);
        
        // Load project branches
        loadProjectBranches(projectId);
    });
    
    // Load project branches from API
    function loadProjectBranches(projectId) {
        fetch(`/api/chat/projects/${projectId}/branches`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Get branches container
                const branchesContainer = document.querySelector(`#project-${projectId}-branches`);
                if (!branchesContainer) return;
                
                // Clear existing branches
                branchesContainer.innerHTML = '';
                
                // Add branches
                data.branches.forEach(branch => {
                    const branchNode = document.createElement('div');
                    branchNode.className = 'branch-node';
                    branchNode.textContent = branch;
                    branchesContainer.appendChild(branchNode);
                });
                
                // Select the main branch by default
                const mainBranch = branchesContainer.querySelector('.branch-node');
                if (mainBranch) {
                    mainBranch.click();
                }
            })
            .catch(error => {
                console.error('Error loading branches:', error);
            });
    }
    
    // Add click event to branch nodes to load a conversation
    projectsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('branch-node')) {
            const branchNode = e.target;
            const projectCard = branchNode.closest('.project-card');
            const projectId = projectCard.dataset.projectId;
            const branchName = branchNode.textContent;
            
            console.log(`Loading branch "${branchName}" from project ${projectId}`);
            
            // Add visual feedback
            document.querySelectorAll('.branch-node').forEach(node => {
                node.style.fontWeight = 'normal';
                node.style.backgroundColor = '#f8f9fa';
            });
            
            branchNode.style.fontWeight = 'bold';
            branchNode.style.backgroundColor = '#e9ecef';
            
            // Clear chat and show loading indicator
            clearChat();
            addSystemMessage(`Loading conversation from "${branchName}" in Project ${projectId}...`);
            
            // Load conversation history
            const conversationId = `${projectId}_${branchName}`;
            loadConversationHistory(conversationId);
        }
    });
    
    // Load conversation history from API
    function loadConversationHistory(conversationId) {
        fetch(`/api/chat/conversations/${conversationId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Clear chat again (in case messages were added while loading)
                clearChat();
                
                // If no messages, show welcome message
                if (data.messages.length === 0) {
                    const welcomeElement = document.createElement('div');
                    welcomeElement.className = 'welcome-message text-center p-5';
                    welcomeElement.innerHTML = `
                        <h3>Start a new conversation</h3>
                        <p class="text-muted">Type a message below to begin chatting with Minerva</p>
                    `;
                    chatHistory.appendChild(welcomeElement);
                    return;
                }
                
                // Add messages to chat
                data.messages.forEach(msg => {
                    if (msg.role === 'user') {
                        // Add user message
                        const messageElement = document.createElement('div');
                        messageElement.className = 'message user-message';
                        messageElement.innerHTML = `
                            <div>${msg.content}</div>
                            <div class="message-time">${formatTimestamp(msg.timestamp)}</div>
                        `;
                        chatHistory.appendChild(messageElement);
                    } else if (msg.role === 'assistant') {
                        // Add bot message
                        const messageElement = document.createElement('div');
                        messageElement.className = 'message bot-message';
                        
                        let modelInfoHtml = '';
                        if (msg.model_info) {
                            const topModel = msg.model_info.rankings[0]?.model || 'unknown';
                            const blendingInfo = msg.model_info.blending ? 
                                `Using Think Tank blending: ${msg.model_info.blending.strategy}` : 
                                'Using top model response';
                            
                            modelInfoHtml = `
                                <div class="message-model-info">
                                    <div><strong>Top model:</strong> ${topModel}</div>
                                    <div>${blendingInfo}</div>
                                </div>
                            `;
                        }
                        
                        messageElement.innerHTML = `
                            <div>${msg.content}</div>
                            <div class="message-time">${formatTimestamp(msg.timestamp)}</div>
                            ${modelInfoHtml}
                        `;
                        chatHistory.appendChild(messageElement);
                    }
                });
                
                // Scroll to bottom
                chatHistory.scrollTop = chatHistory.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading conversation:', error);
                addSystemMessage(`Error loading conversation: ${error.message}`);
            });
    }
    
    // Format timestamp for display
    function formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        } catch (e) {
            return timestamp || 'Unknown time';
        }
    }
    
    // Clear chat and add system message
    function clearChat() {
        chatHistory.innerHTML = '';
    }
    
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'text-center p-3';
        messageElement.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>${message}
            </div>
        `;
        chatHistory.appendChild(messageElement);
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    createProjectBtn.addEventListener('click', createNewProject);
});
