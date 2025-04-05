/**
 * Minerva Chat Interface
 * Handles chat interactions, project management, and model insights visualization
 * Includes WebSocket integration for real-time Think Tank AI responses
 */

// Add CSS styles for history dialog and memory status
const styleElement = document.createElement('style');
styleElement.textContent = `
    .memory-status {
        margin-left: 10px;
        padding: 4px 8px;
        border-radius: 4px;
        background-color: #f0f0f0;
        color: #666;
        font-size: 0.8em;
    }
    
    .memory-status.active {
        background-color: #d4edda;
        color: #155724;
    }
    
    .history-dialog {
        display: none;
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 80%;
        max-width: 600px;
        max-height: 80vh;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    .dialog-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background-color: #f8f9fa;
        border-bottom: 1px solid #e9ecef;
    }
    
    .dialog-header h3 {
        margin: 0;
        font-size: 1.2em;
    }
    
    .close-button {
        background: none;
        border: none;
        font-size: 1.2em;
        cursor: pointer;
        color: #666;
    }
    
    .dialog-content {
        padding: 16px;
        overflow-y: auto;
        flex: 1;
    }
    
    .dialog-footer {
        padding: 12px 16px;
        border-top: 1px solid #e9ecef;
        display: flex;
        justify-content: flex-end;
    }
    
    .history-item {
        padding: 12px;
        border-bottom: 1px solid #e9ecef;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .history-item:hover {
        background-color: #f8f9fa;
    }
    
    .history-item.current {
        background-color: #e9f5ff;
    }
    
    .history-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    
    .history-item h4 {
        margin: 0;
        font-size: 1em;
    }
    
    .timestamp {
        font-size: 0.8em;
        color: #6c757d;
    }
    
    .preview {
        margin: 0;
        color: #6c757d;
        font-size: 0.9em;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
`;

document.head.appendChild(styleElement);

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-button');
    const chatHistory = document.getElementById('chat-history');
    const createProjectBtn = document.getElementById('create-project-btn');
    const projectsContainer = document.getElementById('projects-container');
    const connectionStatus = document.getElementById('connection-status');
    
    // Add history button to chat controls if it doesn't exist
    const chatControls = document.querySelector('.chat-controls');
    if (chatControls && !document.getElementById('history-button')) {
        const historyButton = document.createElement('button');
        historyButton.id = 'history-button';
        historyButton.className = 'chat-control-button';
        historyButton.innerHTML = '<i class="fas fa-history"></i> History';
        chatControls.appendChild(historyButton);
        
        // Add memory status indicator
        const memoryStatus = document.createElement('span');
        memoryStatus.id = 'memory-status';
        memoryStatus.className = 'memory-status';
        memoryStatus.textContent = localStorage.getItem('minerva_memory_enabled') === 'true' ? 'Memory: On' : 'Memory: Off';
        if (localStorage.getItem('minerva_memory_enabled') === 'true') {
            memoryStatus.classList.add('active');
        }
        chatControls.appendChild(memoryStatus);
    }
    
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
    
        // Make chat windows draggable
    function makeChatsMovable() {
        console.log('Initializing draggable chat functionality');
        
        const integratedChat = document.getElementById('integrated-chat');
        const integratedChatHeader = document.querySelector('#integrated-chat .chat-header');
        
        const projectChat = document.getElementById('project-chat');
        const projectChatHeader = document.querySelector('#project-chat .chat-header');
        
        if (integratedChat && integratedChatHeader) {
            console.log('Making integrated chat draggable');
            // Ensure chat containers have position styles that work with absolute positioning
            integratedChat.style.position = 'fixed';
            integratedChat.style.bottom = 'auto';
            integratedChat.style.right = 'auto';
            if (!integratedChat.style.top) integratedChat.style.top = '100px';
            if (!integratedChat.style.left) integratedChat.style.left = 'auto';
            
            makeDraggable(integratedChat, integratedChatHeader);
        } else {
            console.warn('Could not find integrated chat elements');
        }
        
        if (projectChat && projectChatHeader) {
            console.log('Making project chat draggable');
            // Ensure chat containers have position styles that work with absolute positioning
            projectChat.style.position = 'fixed';
            projectChat.style.bottom = 'auto';
            projectChat.style.right = 'auto';
            projectChat.style.left = 'auto';
            if (!projectChat.style.top) projectChat.style.top = '100px';
            if (!projectChat.style.left) projectChat.style.left = '280px';
            
            makeDraggable(projectChat, projectChatHeader);
        } else {
            console.warn('Could not find project chat elements');
        }
    }
    
    // Generic function to make an element draggable
    function makeDraggable(element, dragHandle) {
        if (!element || !dragHandle) {
            console.warn('Cannot initialize draggable: missing element or handle');
            return;
        }
        
        console.log('Setting up draggable for:', element.id);
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        
        // Make handle visibly draggable
        dragHandle.style.cursor = 'move';
        dragHandle.title = 'Drag to move';
        
        // Remove any existing listeners
        dragHandle.onmousedown = null;
        
        // Add new listeners
        dragHandle.onmousedown = dragMouseDown;
        
        function dragMouseDown(e) {
            console.log('Mouse down on draggable element:', element.id);
            e = e || window.event;
            e.preventDefault();
            
            // Get the mouse cursor position at startup
            pos3 = e.clientX;
            pos4 = e.clientY;
            
            // Add active dragging class
            element.classList.add('dragging');
            
            // Set up move and release handlers
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
            const newTop = (element.offsetTop - pos2);
            const newLeft = (element.offsetLeft - pos1);
            
            console.log(`Dragging ${element.id} to:`, newTop, newLeft);
            
            // Don't allow the chat to be moved completely off-screen
            const minVisible = 40; // Minimum pixels that must remain visible
            const maxTop = window.innerHeight - minVisible;
            const maxLeft = window.innerWidth - minVisible;
            
            element.style.top = Math.max(0, Math.min(newTop, maxTop)) + 'px';
            element.style.left = Math.max(0, Math.min(newLeft, maxLeft)) + 'px';
            element.style.bottom = 'auto'; // Remove bottom positioning when dragged
            element.style.right = 'auto'; // Remove right positioning when dragged
        }
        
        function closeDragElement() {
            console.log('Drag ended for:', element.id);
            // Stop moving when mouse button is released
            document.onmouseup = null;
            document.onmousemove = null;
            element.classList.remove('dragging');
        }
    }

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
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * Toggles the visibility of model details in the chat interface
     * Critical for visualizing Think Tank model contributions
     * See: /function_snapshots/chat/minerva-chat.js
     *******************************************************************************/
    window.toggleModelDetails = function(button) {
        const detailsContainer = button.nextElementSibling;
        const isHidden = detailsContainer.classList.contains('hidden');
        
        // Toggle visibility
        if (isHidden) {
            detailsContainer.classList.remove('hidden');
            button.textContent = 'Hide model details';
            
            // Find the details content container
            const detailsContent = detailsContainer.querySelector('.model-details-content');
            if (detailsContent && !detailsContent.querySelector('.model-rankings') && !detailsContent.querySelector('.model-chart')) {
                // Find the closest message to get model info
                const messageElement = button.closest('.message');
                const messageId = messageElement.dataset.messageId;
                
                // Try to find model info in our session cache
                if (messageId && sessionModelInfo[messageId]) {
                    const modelInfo = sessionModelInfo[messageId];
                    
                    // If the details aren't already populated (might be pre-populated in addBotMessage)
                    if (!detailsContent.innerHTML.trim()) {
                        // Create visualization of model performance based on the available data
                        if (modelInfo.rankings && modelInfo.rankings.length > 0) {
                            // Detailed visualization with the enhanced rankings UI
                            createModelRankingsVisualization(detailsContent, modelInfo);
                        } else {
                            // Simple info display if no rankings are available
                            detailsContent.innerHTML = `
                                <div class="simple-model-info">
                                    <p><strong>Primary Model:</strong> ${modelInfo.primary_model || 'Unknown'}</p>
                                    <p><strong>Models Used:</strong> ${modelInfo.models_used?.join(', ') || 'Information not available'}</p>
                                </div>
                            `;
                        }
                    }
                } else {
                    detailsContent.innerHTML = '<p>Detailed model information not available for this message.</p>';
                }
            }
        } else {
            detailsContainer.classList.add('hidden');
            button.textContent = 'View model details';
        }
    };
    
    // Helper function to create visual model rankings display
    function createModelRankingsVisualization(container, modelInfo) {
        if (!modelInfo.rankings || modelInfo.rankings.length === 0) {
            container.innerHTML = '<p>No model ranking information available.</p>';
            return;
        }
        
        let html = '<div class="model-rankings">';
        
        // Create bar chart visualization of model rankings
        modelInfo.rankings.forEach(rank => {
            const formattedName = rank.model
                .replace('gpt-4', 'GPT-4')
                .replace('claude-3', 'Claude 3')
                .replace('gemini', 'Gemini')
                .replace('-', ' ');
                
            const score = (rank.score * 100).toFixed(1);
            const barWidth = Math.max(score, 5); // Minimum width for visibility
            
            html += `
                <div class="rank-item">
                    <div class="rank-model">${formattedName}</div>
                    <div class="rank-bar-container">
                        <div class="rank-bar" style="width: ${barWidth}%"></div>
                        <span class="rank-score">${score}%</span>
                    </div>
                    <div class="rank-reason">${rank.reason || 'Contributing model'}</div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    // Cache for storing model info by message ID
    const sessionModelInfo = {};
    
    // Chat functionality
    function addUserMessage(message) {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message animate-in';
        
        // Format message with Markdown if available
        let formattedMessage = message;
        if (window.MarkdownFormatter) {
            formattedMessage = MarkdownFormatter.formatMessage(message);
        } else if (window.marked && typeof window.marked === 'function') {
            try {
                formattedMessage = window.marked(message);
                // Use DOMPurify if available
                if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
                    formattedMessage = DOMPurify.sanitize(formattedMessage);
                }
            } catch (e) {
                console.warn('Error parsing markdown:', e);
                // Fall back to basic formatting
                formattedMessage = message.replace(/\n/g, '<br>');
            }
        } else {
            // Basic formatting if marked isn't available
            formattedMessage = message.replace(/\n/g, '<br>');
        }
        
        messageElement.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-time">${timestamp}</div>
        `;
        chatHistory.appendChild(messageElement);
        
        // Add a slight bounce animation
        messageElement.style.animationName = 'message-bounce-in';
        messageElement.style.animationDuration = '0.5s';
        messageElement.style.animationTimingFunction = 'cubic-bezier(0.17, 0.89, 0.32, 1.49)';
        
        // Use our animation utilities if available
        if (window.MinervaAnimation) {
            MinervaAnimation.enhanceMessageElement(messageElement);
        } else {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * Core function for displaying AI responses with Think Tank multi-model information
     * Critical for visualizing Think Tank model contributions and blending
     * See: /function_snapshots/chat/minerva-chat.js
     *******************************************************************************/
    function addBotMessage(message, modelInfo) {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message animate-in';
        messageElement.dataset.messageId = Date.now().toString();
        
        // Add a slide-in animation
        messageElement.style.animationName = 'message-slide-in';
        messageElement.style.animationDuration = '0.4s';
        messageElement.style.animationTimingFunction = 'ease-out';
        
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
                
                // Get models used from rankings or models_used
                const modelsUsed = modelInfo.models_used || [];
                
                // Determine if there are rankings available
                if (modelInfo.rankings && modelInfo.rankings.length > 0) {
                    topModel = modelInfo.rankings[0].model;
                    // Format model name for better display
                    const formattedModelName = topModel
                        .replace('gpt-4', 'GPT-4')
                        .replace('claude-3', 'Claude 3')
                        .replace('gemini', 'Gemini')
                        .replace('-', ' ');
                    topModel = formattedModelName;
                    modelCount = modelInfo.rankings.length;
                } else if (modelInfo.primary_model) {
                    // If no rankings but we have a primary model
                    topModel = modelInfo.primary_model
                        .replace('gpt-4', 'GPT-4')
                        .replace('claude-3', 'Claude 3')
                        .replace('gemini', 'Gemini')
                        .replace('-', ' ');
                    modelCount = modelsUsed.length || 1;
                }
                
                // Determine if this is a blended response
                const isBlended = (modelInfo.blended || (modelsUsed.length > 1));
                
                if (isBlended) {
                    // Get blending strategy in a user-friendly format
                    const strategyName = modelInfo.blending?.strategy || 'custom';
                    blendingInfo = `Using Think Tank blending: ${strategyName}`;
                } else {
                    blendingInfo = 'Using single model response';
                }
                
                // Generate model visualization for the detailed view
                let modelDetailsHtml = '';
                
                if (modelInfo.rankings && modelInfo.rankings.length > 0) {
                    modelDetailsHtml += '<div class="model-rankings">';
                    
                    // Process each model ranking with visualization
                    modelInfo.rankings.forEach(rank => {
                        const formattedName = rank.model
                            .replace('gpt-4', 'GPT-4')
                            .replace('claude-3', 'Claude 3')
                            .replace('gemini', 'Gemini')
                            .replace('-', ' ');
                            
                        const score = (rank.score * 100).toFixed(1);
                        const barWidth = Math.max(score, 5); // Minimum width for visibility
                        
                        modelDetailsHtml += `
                            <div class="rank-item">
                                <div class="rank-model">${formattedName}</div>
                                <div class="rank-bar-container">
                                    <div class="rank-bar" style="width: ${barWidth}%"></div>
                                    <span class="rank-score">${score}%</span>
                                </div>
                                <div class="rank-reason">${rank.reason || 'Contributing model'}</div>
                            </div>
                        `;
                    });
                    
                    modelDetailsHtml += '</div>';
                }
                
                // Create enhanced model info section with visualization capabilities
                modelInfoHtml = `
                    <div class="message-model-info">
                        <div class="model-summary">
                            <div><strong>Primary model:</strong> ${topModel}</div>
                            <div>${blendingInfo}</div>
                            <div><small>${modelCount} models contributing</small></div>
                        </div>
                        ${isBlended ? '<div class="blended-indicator">Blended Response</div>' : ''}
                        <button class="model-details-toggle" onclick="toggleModelDetails(this)">View model details</button>
                        <div class="model-details hidden">
                            <div id="model-details-${messageElement.dataset.messageId}" class="model-details-content">
                                ${modelDetailsHtml}
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error creating model info UI:', error);
                // Simple fallback in case of error
                modelInfoHtml = `<div class="message-model-info"><div>Think Tank response</div></div>`;
            }
        }
        
        // Format message with Markdown using our formatter
        let formattedMessage = message;
        if (window.MarkdownFormatter) {
            formattedMessage = MarkdownFormatter.formatMessage(message);
        } else if (window.marked && typeof window.marked === 'function') {
            try {
                formattedMessage = window.marked(message);
                // Use DOMPurify if available
                if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
                    formattedMessage = DOMPurify.sanitize(formattedMessage);
                }
            } catch (e) {
                console.warn('Error parsing markdown:', e);
                // Fall back to basic formatting
                formattedMessage = message.replace(/\n/g, '<br>');
            }
        } else {
            // Basic formatting if marked isn't available
            formattedMessage = message.replace(/\n/g, '<br>');
        }
        
        messageElement.innerHTML = `
            <div class="message-content">${formattedMessage}</div>
            <div class="message-time">${timestamp}</div>
            ${modelInfoHtml}
        `;
        chatHistory.appendChild(messageElement);
        
        // Use our animation utilities if available
        if (window.MinervaAnimation) {
            MinervaAnimation.enhanceMessageElement(messageElement);
        } else {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * Core chat function that handles sending messages while preserving context
     * Critical for the entire chat system functionality
     * See: /function_snapshots/chat/minerva-chat.js
     *******************************************************************************/
    function sendMessage() {
        console.log('sendMessage function called');
        const message = chatInput.value.trim();
        console.log('Message from input field:', message);
        
        if (!message) {
            console.log('Message empty, not sending');
            return;
        }
        
        // Clear input immediately to prevent double-sends
        chatInput.value = '';
        
        // Add user message to chat display
        addUserMessage(message);
        console.log('User message added to chat');
        
        // Clear welcome message if it exists
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        // Create message object for event emission
        const messageObj = {
            content: message,
            metadata: {}
        };
        
        // Get active conversation ID
        const conversationId = localStorage.getItem('minerva_conversation_id');
        console.log('Current conversation ID:', conversationId);
        
        try {
            // Emit event for project context processing
            if (conversationId) {
                const messageEvent = new CustomEvent('minerva:message:sending', {
                    detail: {
                        message: messageObj,
                        conversationId: conversationId
                    }
                });
                document.dispatchEvent(messageEvent);
                console.log('Emitted minerva:message:sending event for project context processing');
            }
            
            // Send to backend using our Think Tank API
            // Use the enhanced message object that might have been modified by project context processor
            console.log('Calling sendMessageToAPI with message object:', messageObj);
            sendMessageToAPI(messageObj);
        } catch (error) {
            console.error('Error in sendMessage function:', error);
            // Add an error message to the chat so user knows something went wrong
            addSystemMessage('Error sending message: ' + error.message, 'error');
        }
    }
    
    // Expose sendMessage to window object for external access
    window.MinervaExternalSendMessage = sendMessage;
    
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
        
        // Project message response handling
        socket.on('project_message_response', (data) => {
            console.log('Received project message response:', data);
            
            // Hide typing indicator
            const projectTypingIndicator = document.getElementById('project-typing-indicator');
            if (projectTypingIndicator) {
                projectTypingIndicator.classList.add('hidden');
            }
            
            if (data.message) {
                // Add the response to the project chat
                addProjectChatMessage(data.message, 'bot', data.timestamp || new Date().toISOString());
                
                // Store model info for this message if available
                if (data.message_id && data.model_info) {
                    sessionModelInfo[data.message_id] = data.model_info;
                }
            } else if (data.error) {
                // Handle errors
                addProjectChatMessage(`Error: ${data.error}`, 'system');
            }
        });
        
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
    /*******************************************************************************
 * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
 * This function handles Think Tank responses and ensures messages aren't duplicated
 * Critical for maintaining conversation persistence
 * See: /function_snapshots/chat/minerva-chat.js
 *******************************************************************************/
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
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * Core message sending function that preserves conversation memory and context
     * Critical for the entire chat system functionality
     * See: /function_snapshots/chat/minerva-chat.js
     *******************************************************************************/
    function sendMessageToAPI(userMessage) {
        // Original variables that must be preserved
        let messageContent = userMessage;
        let projectContext = null;
        
        console.log('sendMessageToAPI called with:', userMessage);
        
        // Handle enhanced message objects (from project context processing) without breaking original flow
        if (typeof userMessage === 'object') {
            if (userMessage.content) {
                messageContent = userMessage.content;
                // Store project context if available but don't disrupt the flow
                if (userMessage.metadata && userMessage.metadata.projectContext) {
                    projectContext = userMessage.metadata.projectContext;
                    console.log('Project context detected:', projectContext);
                }
            } else {
                console.warn('Message object missing content property:', userMessage);
                // Fallback to stringify the object if it has no content property
                try {
                    messageContent = JSON.stringify(userMessage);
                } catch (e) {
                    messageContent = 'Error processing message';
                    console.error('Error stringifying message object:', e);
                }
            }
        }
        
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
            message: messageContent,
            session_id: sessionId,
            user_id: userId,
            message_id: messageId,
            model_preference: selectedModel,
            enable_web_research: webResearchEnabled,
            research_depth: researchDepth,
            mode: 'think_tank',
            project_id: projectId,
            branch_id: activeBranch || 'main',
            include_model_info: true,
            store_in_memory: true,  // Critical for conversation persistence
            optimize_context: true,  // Enable context optimization
            context_depth: 15,      // Maximum context depth for optimization
            conversation_id: localStorage.getItem('minerva_conversation_id') || null  // Ensure conversation memory
        };
        
        // Include project context if available - use original format to avoid breaking things
        if (projectContext) {
            payload.project_context = projectContext;
            console.log('Including project context in API request:', projectContext);
        }
        
        // Log current conversation ID
        console.log('Using conversation ID:', payload.conversation_id);
        
        // Apply context optimization if ThinkTankAPI is available and conversation exists
        const conversationId = payload.conversation_id;
        if (window.thinkTankAPI && conversationId && window.thinkTankAPI.optimizeConversationContext) {
            try {
                console.log('Optimizing conversation context for better performance...');
                
                // This will happen asynchronously - we don't wait for it to complete
                // before sending the initial message, as the backend will handle optimization as well
                window.thinkTankAPI.optimizeConversationContext(conversationId, {
                    maxMessages: payload.context_depth || 15,
                    recentMessagesToKeep: 7,
                    includeSummary: true
                }).then(optimizedContext => {
                    console.log(`Context optimization complete. Using ${optimizedContext.length} optimized messages.`);
                    // The optimized context is now available for use in the Think Tank
                }).catch(error => {
                    console.error('Error during context optimization:', error);
                    // Proceed with standard context handling on error
                });
            } catch (e) {
                console.warn('Context optimization unavailable:', e);
            }
        }
        
        // Log the enhanced payload
        console.log('Sending message with options:', payload);
        
        // Try to use WebSockets first, then fallback to REST API
        // Note: Currently WebSockets may not be fully connected
        if (socket && isConnected) {
            console.log('Sending via WebSocket...');
            
            // Set a timeout in case the socket doesn't respond
            const socketTimeout = setTimeout(() => {
                console.log('WebSocket timeout, falling back to REST API');
                fallbackToRESTAPI(payload);
            }, 1500);
            
            // Listen for the acknowledgement from the socket
            socket.emit('chat_message', payload, (ack) => {
                // Socket has acknowledged the message
                clearTimeout(socketTimeout);
                
                if (ack && ack.status === 'received') {
                    console.log('Socket successfully received message');
                } else {
                    console.log('Socket acknowledged but reported an issue, using fallback');
                    fallbackToRESTAPI(payload);
                }
            });
        } else {
            // Use the REST API directly
            console.log('Using REST API direct connection');
            fallbackToRESTAPI(payload);
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
    
    /*******************************************************************************
     * PROTECTED FUNCTION - DO NOT MODIFY WITHOUT TESTING
     * Fallback REST API handler that ensures Think Tank responses are properly processed
     * Critical for maintaining conversation memory and context
     * See: /function_snapshots/chat/minerva-chat.js
     *******************************************************************************/
    function fallbackToRESTAPI(payload) {
        console.log('Using Think Tank REST API');
        
        // Ensure store_in_memory is set for conversation persistence
        if (!payload.store_in_memory) {
            payload.store_in_memory = true;
        }
        
        // Add system message to indicate processing status
        const processingElement = document.querySelector('.message.system.processing');
        if (!processingElement) {
            // Use thinkTankAPI's endpoint if available, otherwise use the current endpoint
            const apiEndpoint = window.thinkTankAPI ? window.thinkTankAPI.apiUrl : currentApiEndpoint;
            addSystemMessage(`Processing with Think Tank API at ${apiEndpoint}...`, 'processing');
        }
        
        // Ensure conversation_id is included for memory persistence
        if (!payload.conversation_id && localStorage.getItem('minerva_conversation_id')) {
            payload.conversation_id = localStorage.getItem('minerva_conversation_id');
            console.log('Using existing conversation ID:', payload.conversation_id);
        }
        
                // Use the endpoint that was found to be working, or fall back through the list
        let currentApiEndpoint = localStorage.getItem('minerva_api_endpoint') || API_ENDPOINTS[0];
        
        console.log(`Attempting API endpoint: ${currentApiEndpoint}`);
        
        // Add timeout to fetch to prevent long waits on unreachable endpoints
        const fetchWithTimeout = (url, options, timeout = 5000) => {
            return Promise.race([
                fetch(url, options),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Request timeout')), timeout)
                )
            ]);
        };
        
        fetchWithTimeout(currentApiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            mode: 'cors',  // Enable CORS for cross-domain requests
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
            
            // Remove any processing status messages
            const processingMessages = document.querySelectorAll('.message.system.processing');
            processingMessages.forEach(msg => msg.remove());
            
            // The API returns response content in data.response
            const responseContent = data.response || 'No response from AI';
            
            // Store/update conversation_id in localStorage if returned
            if (data.conversation_id) {
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
                console.log(`Conversation ID saved: ${data.conversation_id}`);
            }
            
            // Handle memory status if present in the response
            if (data.memory_status) {
                console.log('Memory system status:', data.memory_status);
                
                // Update memory status in localStorage
                localStorage.setItem('minerva_memory_enabled', data.memory_status.memory_enabled);
                
                // Update memory status indicator if it exists
                const memoryStatus = document.getElementById('memory-status');
                if (memoryStatus) {
                    memoryStatus.textContent = data.memory_status.memory_enabled ? 'Memory: On' : 'Memory: Off';
                    if (data.memory_status.memory_enabled) {
                        memoryStatus.classList.add('active');
                    } else {
                        memoryStatus.classList.remove('active');
                    }
                }
            }
            
            // Update memory status if available
            if (data.memory_status) {
                console.log('Memory status:', data.memory_status);
                // Store memory status for UI features
                localStorage.setItem('minerva_memory_enabled', data.memory_status.memory_enabled);
                
                // If we're using a memory system, update the UI
                if (data.memory_status.memory_enabled) {
                    const memoryStatusElement = document.getElementById('memory-status');
                    if (memoryStatusElement) {
                        memoryStatusElement.textContent = 'Memory: On';
                        memoryStatusElement.classList.add('active');
                    }
                }
            }
            
            // Add bot response to chat with model_info if available
            addBotMessage(responseContent, data.model_info);
            
            // Update analytics
            updateAnalyticsFromAPI();
            
            console.log('Successfully received and processed Think Tank response via REST API', data);
        })
        .catch(error => {
            console.error('Think Tank API Error:', error);
            hideTypingIndicator();
            
            // Remove any processing status messages
            const processingMessages = document.querySelectorAll('.message.system.processing');
            processingMessages.forEach(msg => msg.remove());
            
            // Add more detailed debugging information
            let errorMessage = 'Sorry, there was an error connecting to the Think Tank.';
            
            // Show a more specific error message based on the error
            if (error.message.includes('Failed to fetch') || error.message.includes('Request timeout')) {
                errorMessage = 'Network error: Could not connect to the server. Trying fallback endpoint...';
                
                // Try next endpoint in list
                const currentIndex = API_ENDPOINTS.indexOf(currentApiEndpoint);
                if (currentIndex < API_ENDPOINTS.length - 1) {
                    const nextEndpoint = API_ENDPOINTS[currentIndex + 1];
                    console.log(`Trying next endpoint: ${nextEndpoint}`);
                    localStorage.setItem('minerva_api_endpoint', nextEndpoint);
                    
                    // Try again with new endpoint
                    addSystemMessage(`Switching to backup API endpoint at ${nextEndpoint}`, 'info');
                    fallbackToRESTAPI(payload);
                    return;
                } else if (currentIndex === API_ENDPOINTS.length - 1) {
                    // We've tried all endpoints, use mock response
                    errorMessage = 'All API endpoints failed. Using offline mode.';
                    
                    // Create mock response
                    const mockResponse = {
                        response: "I'm operating in offline mode. The Think Tank service appears to be unavailable right now, but I'll do my best to assist you with basic functionality.",
                        conversation_id: payload.conversation_id || 'offline-' + Date.now(),
                        model_info: { models: [{ name: 'offline-mode', contribution: 100 }] }
                    };
                    
                    // Store mock response in local storage for later recovery
                    const offlineMessages = JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
                    offlineMessages.push({
                        role: 'user',
                        content: payload.message,
                        timestamp: Date.now()
                    });
                    offlineMessages.push({
                        role: 'assistant',
                        content: mockResponse.response,
                        timestamp: Date.now() + 1000
                    });
                    localStorage.setItem('minerva_offline_messages', JSON.stringify(offlineMessages));
                    
                    // Display mock response
                    addBotMessage(mockResponse.response, mockResponse.model_info);
                    return;
                }
            } else if (error.message.includes('API error: 404')) {
                errorMessage = 'The chat API endpoint could not be found. Trying another endpoint...';
                // Try next endpoint
                tryNextEndpoint(payload);
                return;
            } else if (error.message.includes('API error: 500')) {
                errorMessage = 'The server encountered an internal error. Trying another endpoint...';
                // Try next endpoint
                tryNextEndpoint(payload);
                return;
            }
            
            // Log more detailed diagnostics
            console.log('Request payload was:', payload);
            console.log('API URL was:', currentApiEndpoint);
            
            // Show error message
            addSystemMessage(errorMessage, 'error');
        });
    }
    
    // Show typing indicator in chat
    function showTypingIndicator() {
        // Remove any existing typing indicators
        hideTypingIndicator();
        
        let typingIndicator;
        
        // Use our enhanced animation if available
        if (window.MinervaAnimation) {
            typingIndicator = MinervaAnimation.createTypingIndicator();
            typingIndicator.className = 'typing-indicator message bot-message';
        } else {
            typingIndicator = document.createElement('div');
            typingIndicator.className = 'typing-indicator message bot-message';
            typingIndicator.innerHTML = `
                <div class="typing-dots">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                </div>
            `;
        }
        
        chatHistory.appendChild(typingIndicator);
        
        // Ensure the typing indicator is visible
        if (window.MinervaAnimation) {
            MinervaAnimation.ensureElementInView(typingIndicator);
        } else {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
    }
    
    // Hide typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator');
        if (typingIndicator) {
            // Add a fade-out class if animations are available
            if (window.MinervaAnimation) {
                typingIndicator.classList.add('hidden');
                // Remove after animation completes
                setTimeout(() => {
                    if (typingIndicator && typingIndicator.parentNode) {
                        typingIndicator.parentNode.removeChild(typingIndicator);
                    }
                }, 300);
            } else {
                typingIndicator.remove();
            }
        }
    }
    
    // Add system message (for errors, notifications, etc.) with status-based styling
    function addSystemMessage(message, status = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const messageElement = document.createElement('div');
        messageElement.className = `message system-message status-${status} animate-in`;
        
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
        
        // Add fade-in animation
        messageElement.style.animationName = 'message-fade-in';
        messageElement.style.animationDuration = '0.3s';
        messageElement.style.animationTimingFunction = 'ease-in';
        
        // Auto-remove system messages after a delay (unless they're errors)
        if (status !== 'error') {
            setTimeout(() => {
                messageElement.style.animationName = 'message-fade-out';
                messageElement.style.animationDuration = '0.5s';
                messageElement.style.animationFillMode = 'forwards';
                
                // Remove from DOM after animation completes
                setTimeout(() => {
                    if (messageElement.parentNode) {
                        messageElement.parentNode.removeChild(messageElement);
                    }
                }, 500);
            }, 5000); // Show for 5 seconds before fading out
        }
        
        // Use our animation utilities if available
        if (window.MinervaAnimation) {
            MinervaAnimation.enhanceMessageElement(messageElement);
        } else {
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
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
    
    // Initialize draggable chat functionality
    makeChatsMovable();
    
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
    
    // Load conversation history from API using the Think Tank API
    async function loadConversationHistory(conversationId) {
        try {
            // Clear chat 
            clearChat();
            
            // Show loading message
            addSystemMessage('Loading conversation history...');
            
            // Use ThinkTankAPI to retrieve conversation if available
            if (window.thinkTankAPI) {
                // Set active conversation first
                window.thinkTankAPI.setActiveConversation(conversationId);
                const conversation = await window.thinkTankAPI.loadConversation(conversationId);
                const messages = conversation.messages || [];
                
                // Remove loading message
                const loadingMessages = document.querySelectorAll('.message.system');
                loadingMessages.forEach(msg => {
                    if (msg.textContent.includes('Loading conversation history')) {
                        msg.remove();
                    }
                });
                
                if (!messages || messages.length === 0) {
                    // No messages, show welcome message
                    const welcomeElement = document.createElement('div');
                    welcomeElement.className = 'welcome-message text-center p-5';
                    welcomeElement.innerHTML = `
                        <h3>Start a new conversation</h3>
                        <p class="text-muted">Type a message below to begin chatting with Minerva</p>
                    `;
                    chatHistory.appendChild(welcomeElement);
                    return;
                }
                
                // Show conversation summary if available or generate one
                displayConversationSummary(conversation, conversationId);
                
                // Add messages to chat
                messages.forEach(msg => {
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
                        // Add bot message with model info if available
                        const messageElement = document.createElement('div');
                        messageElement.className = 'message bot-message';
                        
                        let modelInfoHtml = '';
                        if (msg.model_info && msg.model_info.models) {
                            // Create model contribution visualization
                            modelInfoHtml = '<div class="model-info"><div class="model-blend">';
                            
                            msg.model_info.models.forEach(model => {
                                const percentage = model.contribution || 0;
                                const modelColor = getModelColor(model.name);
                                
                                modelInfoHtml += `
                                    <div class="model-contribution" 
                                        style="width: ${percentage}%; background-color: ${modelColor};" 
                                        title="${model.name}: ${percentage}%">
                                    </div>
                                `;
                            });
                            
                            modelInfoHtml += '</div><div class="model-labels">';
                            
                            // Add model labels
                            msg.model_info.models.forEach(model => {
                                if (model.contribution > 10) { // Only show labels for significant contributions
                                    const modelColor = getModelColor(model.name);
                                    modelInfoHtml += `
                                        <span class="model-label" style="color: ${modelColor};">
                                            ${model.name} (${Math.round(model.contribution)}%)
                                        </span>
                                    `;
                                }
                            });
                            
                            modelInfoHtml += '</div></div>';
                        }
                        
                        messageElement.innerHTML = `
                            <div class="bot-content">${msg.content}</div>
                            ${modelInfoHtml}
                            <div class="message-time">${formatTimestamp(msg.timestamp)}</div>
                        `;
                        
                        chatHistory.appendChild(messageElement);
                    } else if (msg.role === 'system') {
                        // Add system message
                        addSystemMessage(msg.content);
                    }
                });
                
                // Scroll to bottom after loading all messages
                chatHistory.scrollTop = chatHistory.scrollHeight;
                return true;
            } else {
                // Fallback to traditional fetch if ThinkTankAPI is not available
                fetch(`/api/chat/conversations/${conversationId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`API error: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Remove loading messages
                        const loadingMessages = document.querySelectorAll('.message.system');
                        loadingMessages.forEach(msg => {
                            if (msg.textContent.includes('Loading conversation history')) {
                                msg.remove();
                            }
                        });
                        
                        // If no messages, show welcome message
                        if (!data.messages || data.messages.length === 0) {
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
                    });
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
            addSystemMessage(`Error loading conversation history: ${error.message}`, 'error');
            return false;
        }
    }
    
    // Format timestamp for display
    function formatTimestamp(timestamp) {
        try {
            if (!(timestamp instanceof Date)) {
                const date = new Date(timestamp);
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch (e) {
            console.error('Invalid date format:', e);
            return timestamp || 'Unknown time';
        }
    }
    
    /**
     * Display a conversation summary at the top of the chat
     * @param {Object} conversation - The complete conversation object
     * @param {string} conversationId - The conversation ID
     */
    async function displayConversationSummary(conversation, conversationId) {
        if (!conversation || !chatHistory) return;
        
        // Create summary container
        const summaryContainer = document.createElement('div');
        summaryContainer.className = 'conversation-summary';
        summaryContainer.id = 'conversation-summary';
        
        // Check if the conversation already has a summary
        let summary = conversation.summary;
        let keyPoints = [];
        
        // If no summary exists, generate one
        if (!summary && window.thinkTankAPI && window.thinkTankAPI.summarizeConversation) {
            // Show loading indicator in the summary container
            summaryContainer.innerHTML = `
                <div class="summary-header">
                    <h3>Conversation Summary</h3>
                    <div class="summary-controls">
                        <button id="refresh-summary" title="Refresh Summary">
                            <i class="fas fa-sync-alt"></i>
                        </button>
                        <button id="toggle-summary" title="Toggle Summary">
                            <i class="fas fa-chevron-up"></i>
                        </button>
                    </div>
                </div>
                <div class="summary-content">
                    <div class="summary-loading">Generating conversation summary...</div>
                </div>
            `;
            
            // Add to the chat before loading messages
            chatHistory.insertBefore(summaryContainer, chatHistory.firstChild);
            
            try {
                // Generate summary asynchronously
                const summaryResult = await window.thinkTankAPI.summarizeConversation(conversationId);
                summary = summaryResult.summary;
                keyPoints = summaryResult.keyPoints || [];
            } catch (error) {
                console.error('Error generating summary:', error);
                summary = 'Could not generate a summary for this conversation.';
                keyPoints = ['Error occurred during summarization'];
            }
        } else if (!summary) {
            // No API available and no existing summary
            summary = 'Summary not available';
            keyPoints = [];
        } else {
            // Use existing summary
            summary = summary.summary || 'No summary available';
            keyPoints = summary.keyPoints || [];
        }
        
        // Create HTML for the summary container
        const keyPointsHTML = keyPoints && keyPoints.length ? 
            `<div class="key-points">
                <h4>Key Points</h4>
                <ul>${keyPoints.map(point => `<li>${point}</li>`).join('')}</ul>
            </div>` : '';
        
        // Update or create the summary container
        summaryContainer.innerHTML = `
            <div class="summary-header">
                <h3>Conversation Summary</h3>
                <div class="summary-controls">
                    <button id="refresh-summary" title="Refresh Summary">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                    <button id="toggle-summary" title="Toggle Summary">
                        <i class="fas fa-chevron-up"></i>
                    </button>
                </div>
            </div>
            <div class="summary-content">
                <div class="summary-text">${summary}</div>
                ${keyPointsHTML}
            </div>
        `;
        
        // If the summary container isn't already in the DOM, add it
        if (!document.getElementById('conversation-summary')) {
            chatHistory.insertBefore(summaryContainer, chatHistory.firstChild);
        }
        
        // Add event listeners for summary controls
        document.getElementById('refresh-summary').addEventListener('click', () => refreshConversationSummary(conversationId));
        document.getElementById('toggle-summary').addEventListener('click', toggleSummaryVisibility);
    }
    
    /**
     * Refresh the conversation summary
     * @param {string} conversationId - The conversation ID
     */
    async function refreshConversationSummary(conversationId) {
        if (!window.thinkTankAPI || !window.thinkTankAPI.summarizeConversation) {
            return;
        }
        
        const summaryContent = document.querySelector('#conversation-summary .summary-content');
        if (!summaryContent) return;
        
        // Show loading state
        summaryContent.innerHTML = '<div class="summary-loading">Refreshing summary...</div>';
        
        try {
            // Generate a fresh summary
            const summaryResult = await window.thinkTankAPI.summarizeConversation(conversationId, true);
            
            // Create HTML for the updated summary
            const summary = summaryResult.summary || 'No summary available';
            const keyPoints = summaryResult.keyPoints || [];
            
            const keyPointsHTML = keyPoints && keyPoints.length ? 
                `<div class="key-points">
                    <h4>Key Points</h4>
                    <ul>${keyPoints.map(point => `<li>${point}</li>`).join('')}</ul>
                </div>` : '';
            
            // Update the summary content
            summaryContent.innerHTML = `
                <div class="summary-text">${summary}</div>
                ${keyPointsHTML}
            `;
        } catch (error) {
            console.error('Error refreshing summary:', error);
            summaryContent.innerHTML = '<div class="summary-error">Could not refresh summary. Please try again later.</div>';
        }
    }
    
    /**
     * Toggle the visibility of the summary content
     */
    function toggleSummaryVisibility() {
        const summaryContent = document.querySelector('#conversation-summary .summary-content');
        const toggleButton = document.getElementById('toggle-summary');
        
        if (!summaryContent || !toggleButton) return;
        
        // Toggle the content visibility
        if (summaryContent.classList.contains('collapsed')) {
            summaryContent.classList.remove('collapsed');
            toggleButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
        } else {
            summaryContent.classList.add('collapsed');
            toggleButton.innerHTML = '<i class="fas fa-chevron-down"></i>';
        }
    }
    
    // Helper function to get color for model visualizations
    function getModelColor(modelName) {
        // Define a color map for common models
        const colorMap = {
            'gpt-4': '#10a37f',
            'gpt-3.5': '#74aa9c',
            'claude': '#8e44ad',
            'claude-2': '#9b59b6',
            'llama': '#e67e22',
            'gemini': '#3498db',
            'mistral': '#c0392b',
            'default': '#95a5a6'
        };
        
        // Check if model name contains any of the keys
        for (const key in colorMap) {
            if (modelName && modelName.toLowerCase().includes(key.toLowerCase())) {
                return colorMap[key];
            }
        }
        
        // Return default color if no match
        return colorMap.default;
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
    
    // Add message to project chat
    function addProjectChatMessage(message, sender, timestamp = new Date().toISOString()) {
        console.log(`Adding ${sender} message to project chat:`, message);
        
        // Get the project chat history container
        const projectChatHistory = document.getElementById('project-chat-history');
        if (!projectChatHistory) {
            console.error('Project chat history container not found');
            return;
        }
        
        // Create new message element
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        // Format the time
        const messageTime = new Date(timestamp);
        const timeString = messageTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Set message content based on sender type
        if (sender === 'user') {
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>${message}</p>
                </div>
                <div class="message-timestamp">${timeString}</div>
            `;
        } else if (sender === 'bot') {
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>${message}</p>
                </div>
                <div class="message-timestamp">${timeString}</div>
            `;
        } else {
            // System message
            messageElement.innerHTML = `
                <div class="message-content">
                    <p><em>${message}</em></p>
                </div>
            `;
        }
        
        // Add to chat history
        projectChatHistory.appendChild(messageElement);
        
        // Scroll to bottom
        projectChatHistory.scrollTop = projectChatHistory.scrollHeight;
        
        // Hide typing indicator if it's a bot message
        if (sender === 'bot') {
            const typingIndicator = document.getElementById('project-typing-indicator');
            if (typingIndicator) {
                typingIndicator.classList.add('hidden');
            }
        }
    }
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    // Enhanced Enter key handler for the main chat
    if (chatInput) {
        console.log('Attaching enhanced keydown handler to main chat input field');
        
        // Remove any existing event listeners to prevent duplicates
        chatInput.removeEventListener('keydown', handleMainChatKeyDown);
        
        // Define the keydown handler function separately so we can reference it
        function handleMainChatKeyDown(e) {
            console.log('Key pressed in main chat input field:', e.key, 'keyCode:', e.keyCode);
            if ((e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey) {
                console.log('Enter key pressed in main chat, sending message');
                e.preventDefault();
                e.stopPropagation();
                sendMessage();
                return false;
            }
        }
        
        // Add the event listener
        chatInput.addEventListener('keydown', handleMainChatKeyDown);
    } else {
        console.error('Main chat input not found!');
    }
    
    // Fix to ensure chat functionalities are set up on both home page and portal page
    function initializeMinervaChats() {
        console.log('🔄 Initializing Minerva Chat components');
        
        // Setup main floating chat if it exists
        initializeMainChat();
        
        // Setup project-specific chat if it exists
        initializeProjectChat();
        
        // Make all chat windows draggable after a short delay to ensure DOM is ready
        setTimeout(makeChatsMovable, 500);
        
        console.log('✅ Minerva Chat initialization complete');
    }
    
    // Main chat initialization
    function initializeMainChat() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        
        if (!chatInput || !sendButton) {
            console.log('Main chat components not found on this page');
            return;
        }
        
        console.log('Setting up main chat handlers');
        
        // Check Think Tank API availability
        checkThinkTankAPIAvailability();
        
        // Add welcome message
        addSystemMessage('Welcome to Minerva Think Tank. How can I help you today?');
        
        // Clear any existing event listeners by cloning
        const newChatInput = chatInput.cloneNode(true);
        if (chatInput.parentNode) {
            chatInput.parentNode.replaceChild(newChatInput, chatInput);
        }
        
        const newSendButton = sendButton.cloneNode(true);
        if (sendButton.parentNode) {
            sendButton.parentNode.replaceChild(newSendButton, sendButton);
        }
        
        // Main chat function - exposed to window for global access
        window.sendMessage = function() {
            const messageInput = document.getElementById('chat-input');
            const message = messageInput.value.trim();
            
            if (!message) {
                console.log('Empty message, not sending');
                return;
            }
            
            console.log('Sending message:', message);
            
            // Add user message to chat
            addUserMessage(message);
            
            // Clear input
            messageInput.value = '';
            
            // Focus back on input
            messageInput.focus();
            
            // Show typing indicator
            showTypingIndicator();
            
            // Update connection status if present
            const connectionStatus = document.getElementById('connection-status');
            if (connectionStatus) {
                connectionStatus.textContent = 'Sending...';
                connectionStatus.style.color = '#ffcc66';
            }
            
            // Prepare payload with conversation memory
            const payload = {
                message: message,
                conversation_id: localStorage.getItem('minerva_conversation_id') || null,
                store_in_memory: true, // Enable conversation memory
                include_model_info: true // Get model info for display
            };
            
            // Try multiple API endpoints with fallback logic
            sendWithFallbacks(payload)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                // Hide typing indicator
                hideTypingIndicator();
                
                // Update connection status
                if (connectionStatus) {
                    connectionStatus.textContent = 'Connected';
                    connectionStatus.style.color = '#66ffaa';
                }
                
                // Process response
                const responseContent = data.response || 'No response from Think Tank';
                
                // Store/update conversation_id for memory persistence
                if (data.conversation_id) {
                    localStorage.setItem('minerva_conversation_id', data.conversation_id);
                    console.log(`Conversation ID saved: ${data.conversation_id}`);
                }
                
                // Add bot response to chat with model info if available
                addBotMessage(responseContent, data.model_info);
                
                console.log('Successfully received Think Tank response', data);
            })
            .catch(error => {
                console.error(`Error with API endpoint ${currentApiEndpoint}:`, error);
                
                // Try the next API endpoint in the list
                const currentIndex = API_ENDPOINTS.indexOf(currentApiEndpoint);
                if (currentIndex < API_ENDPOINTS.length - 1) {
                    const nextEndpoint = API_ENDPOINTS[currentIndex + 1];
                    console.log(`Trying next endpoint: ${nextEndpoint}`);
                    localStorage.setItem('minerva_api_endpoint', nextEndpoint);
                    
                    // Retry with next endpoint
                    fetch(nextEndpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        mode: 'cors',
                        body: JSON.stringify(payload)
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Hide typing indicator
                        hideTypingIndicator();
                        
                        // Update connection status
                        if (connectionStatus) {
                            connectionStatus.textContent = `Connected to ${nextEndpoint}`;
                            connectionStatus.style.color = '#66ffaa';
                        }
                        
                        // Process response
                        const responseContent = data.response || 'No response from Think Tank';
                        
                        // Store/update conversation_id for memory persistence
                        if (data.conversation_id) {
                            localStorage.setItem('minerva_conversation_id', data.conversation_id);
                            console.log(`Conversation ID saved: ${data.conversation_id}`);
                        }
                        
                        // Add bot response to chat with model info if available
                        addBotMessage(responseContent, data.model_info);
                        
                        console.log('Successfully received Think Tank response from fallback endpoint', data);
                    })
                    .catch(finalError => {
                        // All endpoints failed
                        handleAllApiFailure(payload, finalError, connectionStatus);
                    });
                } else {
                    // All endpoints failed
                    handleAllApiFailure(payload, error, connectionStatus);
                }
            });
        };
        
        // Add click event for send button
        newSendButton.addEventListener('click', function(e) {
            console.log('Send button clicked');
            e.preventDefault();
            window.sendMessage();
        });
        
        // Enhanced Enter key handler
        newChatInput.addEventListener('keydown', function(e) {
            console.log('Key pressed:', e.key);
            if ((e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey) {
                console.log('Enter key pressed, sending message');
                e.preventDefault();
                e.stopPropagation();
                window.sendMessage();
                return false;
            }
        });
    }
    
    // Project chat initialization
    function initializeProjectChat() {
        const projectChatInput = document.getElementById('project-chat-input');
        const projectSendButton = document.getElementById('project-send-button');
        
        if (!projectChatInput || !projectSendButton) {
            console.log('Project chat components not found on this page');
            return;
        }
        
        console.log('Setting up project chat handlers');
        
        // Clear any existing event listeners by cloning
        const newProjectChatInput = projectChatInput.cloneNode(true);
        if (projectChatInput.parentNode) {
            projectChatInput.parentNode.replaceChild(newProjectChatInput, projectChatInput);
        }
        
        const newProjectSendButton = projectSendButton.cloneNode(true);
        if (projectSendButton.parentNode) {
            projectSendButton.parentNode.replaceChild(newProjectSendButton, projectSendButton);
        }
        
        // Project chat send function - exposed to window for global access
        window.sendProjectMessage = function() {
            const messageInput = document.getElementById('project-chat-input');
            const message = messageInput.value.trim();
            
            if (!message) {
                console.log('Empty message, not sending');
                return;
            }
            
            console.log('Sending project chat message:', message);
            
            // Get the active project info - try multiple selector patterns
            let projectId = null;
            const projectCard = document.querySelector('.active-project');
            if (projectCard && projectCard.dataset.projectId) {
                projectId = projectCard.dataset.projectId;
            } else {
                // Try another selector for project ID
                const projectIdElement = document.getElementById('project-id');
                if (projectIdElement) {
                    projectId = projectIdElement.value;
                }
            }
            
            if (!projectId) {
                console.error('No project ID found');
                // Get the first project as fallback
                const firstProject = document.querySelector('[data-project-id]');
                if (firstProject) {
                    projectId = firstProject.dataset.projectId;
                    console.log('Using first available project:', projectId);
                }
            }
            
            if (projectId) {
                // Add user message to chat
                addProjectChatMessage(message, 'user');
                
                // Clear input
                messageInput.value = '';
                
                // Focus back on input
                messageInput.focus();
                
                // Show typing indicator
                const typingIndicator = document.getElementById('project-typing-indicator');
                if (typingIndicator) {
                    typingIndicator.classList.remove('hidden');
                }
                
                // Send message to server
                if (socket && isConnected) {
                    socket.emit('project_message', {
                        message: message,
                        project_id: projectId,
                        session_id: sessionId
                    });
                } else {
                    console.warn('Socket not connected, falling back to API');
                    // Fallback to API implementation
                    fetch('/api/project/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            project_id: projectId,
                            message: message,
                            session_id: sessionId
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Project message API response:', data);
                        if (data.message) {
                            addProjectChatMessage(data.message, 'bot');
                        } else if (data.error) {
                            addProjectChatMessage(`Error: ${data.error}`, 'system');
                        }
                        
                        if (typingIndicator) {
                            typingIndicator.classList.add('hidden');
                        }
                    })
                    .catch(error => {
                        console.error('Error sending project message:', error);
                        addProjectChatMessage(`Error: ${error.message}`, 'system');
                        
                        if (typingIndicator) {
                            typingIndicator.classList.add('hidden');
                        }
                    });
                }
            } else {
                console.error('No project selected');
                addProjectChatMessage('Please select a project first.', 'system');
            }
        };
        
        // Add click event for project send button
        newProjectSendButton.addEventListener('click', function(e) {
            console.log('Project send button clicked');
            e.preventDefault();
            window.sendProjectMessage();
        });
        
        // Enhanced Enter key handler for project chat
        newProjectChatInput.addEventListener('keydown', function(e) {
            console.log('Key pressed in project chat:', e.key);
            if ((e.key === 'Enter' || e.keyCode === 13) && !e.shiftKey) {
                console.log('Enter key pressed in project chat');
                e.preventDefault();
                e.stopPropagation();
                window.sendProjectMessage();
                return false;
            }
        });
    }
    
    createProjectBtn.addEventListener('click', createNewProject);
    
    // Initialize all chat components
    initializeMinervaChats();
    
    // Initialize Animation utilities if available
    if (window.MinervaAnimation) {
        MinervaAnimation.initialize();
    }
    
    // Initialize Markdown formatter if available
    if (window.MarkdownFormatter) {
        try {
            // Initialize with main chat input
            MarkdownFormatter.initialize({
                inputSelector: '#chat-input',
                previewContainerId: 'markdown-preview-container',
                toolbarContainerId: 'formatting-toolbar'
            });
            
            console.log('Markdown formatter initialized for main chat');
            
            // Also initialize for project chat if it exists
            const projectChatInput = document.querySelector('#project-chat-input');
            if (projectChatInput) {
                MarkdownFormatter.initialize({
                    inputSelector: '#project-chat-input',
                    previewContainerId: 'project-markdown-preview',
                    toolbarContainerId: 'project-formatting-toolbar'
                });
                console.log('Markdown formatter initialized for project chat');
            }
        } catch (error) {
            console.error('Failed to initialize Markdown formatter:', error);
        }
    }
});

// Setup history button functionality
function setupHistoryButton() {
    // Add event listener for history button
    const historyButton = document.getElementById('history-button');
    if (historyButton) {
        historyButton.removeEventListener('click', showConversationHistory);
        historyButton.addEventListener('click', showConversationHistory);
    }
}

// Show conversation history dialog
async function showConversationHistory() {
    try {
        // Create or show dialog
        let historyDialog = document.getElementById('history-dialog');
        
        if (!historyDialog) {
            // Create dialog if it doesn't exist
            historyDialog = document.createElement('div');
            historyDialog.id = 'history-dialog';
            historyDialog.className = 'history-dialog';
            historyDialog.innerHTML = `
                <div class="dialog-header">
                    <h3>Conversation History</h3>
                    <button class="close-button"><i class="fas fa-times"></i></button>
                </div>
                <div class="dialog-content">
                    <div class="history-list">
                        <p class="loading">Loading conversation history...</p>
                    </div>
                </div>
                <div class="dialog-footer">
                    <button id="new-conversation" class="btn btn-primary">New Conversation</button>
                </div>
            `;
            document.body.appendChild(historyDialog);
            
            // Add event listeners
            historyDialog.querySelector('.close-button').addEventListener('click', () => {
                historyDialog.style.display = 'none';
            });
            
            historyDialog.querySelector('#new-conversation').addEventListener('click', () => {
                // Create new conversation
                if (window.thinkTankAPI) {
                    const newId = window.thinkTankAPI.generateConversationId();
                    window.thinkTankAPI.setActiveConversation(newId);
                    localStorage.setItem('minerva_conversation_id', newId);
                    clearChat();
                    addSystemMessage('Started a new conversation');
                    historyDialog.style.display = 'none';
                }
            });
        }
        
        // Show dialog
        historyDialog.style.display = 'block';
        
        // Load conversation history
        const historyList = historyDialog.querySelector('.history-list');
        historyList.innerHTML = '<p class="loading">Loading conversation history...</p>';
        
        // Fetch recent conversations
        if (window.thinkTankAPI) {
            const conversations = await window.thinkTankAPI.getRecentConversations(20);
            
            if (conversations && conversations.length > 0) {
                historyList.innerHTML = '';
                conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    
                    // Mark current conversation
                    if (conv.id === localStorage.getItem('minerva_conversation_id')) {
                        item.classList.add('current');
                    }
                    
                    const title = conv.title || `Conversation ${conv.id.substring(0, 8)}`;
                    const date = new Date(conv.timestamp || Date.now()).toLocaleString();
                    const preview = conv.preview || 'No preview available';
                    
                    item.innerHTML = `
                        <div class="history-item-header">
                            <h4>${title}</h4>
                            <span class="timestamp">${date}</span>
                        </div>
                        <p class="preview">${preview}</p>
                    `;
                    
                    item.addEventListener('click', () => {
                        // Load this conversation
                        window.thinkTankAPI.setActiveConversation(conv.id);
                        localStorage.setItem('minerva_conversation_id', conv.id);
                        loadConversationHistory(conv.id);
                        historyDialog.style.display = 'none';
                    });
                    
                    historyList.appendChild(item);
                });
            } else {
                historyList.innerHTML = '<p class="empty">No conversation history found</p>';
            }
        } else {
            historyList.innerHTML = '<p class="error">Think Tank API is not available</p>';
        }
    } catch (error) {
        console.error('Error showing conversation history:', error);
        const historyDialog = document.getElementById('history-dialog');
        if (historyDialog) {
            const historyList = historyDialog.querySelector('.history-list');
            if (historyList) {
                historyList.innerHTML = `<p class="error">Error loading history: ${error.message}</p>`;
            }
        }
    }
}

// API endpoints to try in order of preference
const API_ENDPOINTS = [
    'http://localhost:8080/api/think-tank',  // Local server endpoint (primary)
    'http://localhost:7070/api/think-tank',  // ThinkTank server (use when available)
    '/api/think-tank-mock'                   // Mock fallback endpoint
];

// Function to try the next endpoint in the list
function tryNextEndpoint(payload) {
    const currentApiEndpoint = localStorage.getItem('minerva_api_endpoint') || API_ENDPOINTS[0];
    const currentIndex = API_ENDPOINTS.indexOf(currentApiEndpoint);
    
    if (currentIndex < API_ENDPOINTS.length - 1) {
        const nextEndpoint = API_ENDPOINTS[currentIndex + 1];
        console.log(`Switching to next API endpoint: ${nextEndpoint}`);
        localStorage.setItem('minerva_api_endpoint', nextEndpoint);
        
        // Try again with the new endpoint
        fallbackToRESTAPI(payload);
        return true;
    }
    return false;
}

// Check if any Think Tank API is available by trying all endpoints
function checkThinkTankAPIAvailability() {
    console.log('Checking Think Tank API availability across multiple endpoints');
    const connectionIndicator = document.getElementById('connection-status');
    
    // First, check if we already have a valid connection from ThinkTankAPI
    if (window.thinkTankAPI && window.thinkTankAPI.isConnected()) {
        console.log('ThinkTankAPI connection already established');
        updateConnectionStatus('Connected to Think Tank', true);
        
        // Initialize the history button event listener
        setupHistoryButton();
        
        // Once connected, check if we need to load a specific conversation
        const conversationId = localStorage.getItem('minerva_conversation_id');
        if (conversationId) {
            console.log(`Found stored conversation ID: ${conversationId}`);  
            window.thinkTankAPI.setActiveConversation(conversationId);
            loadConversationHistory(conversationId);
        }
        return;
    }
    
    if (connectionIndicator) {
        connectionIndicator.textContent = 'Checking connection...';
        connectionIndicator.style.color = '#ffcc66';
    }
    
    // Store the working API endpoint in localStorage
    let currentEndpointIndex = 0;
    
    function tryNextEndpoint() {
        if (currentEndpointIndex >= API_ENDPOINTS.length) {
            // All endpoints failed
            console.error('All API endpoints failed');
            if (connectionIndicator) {
                connectionIndicator.textContent = 'All API connections failed';
                connectionIndicator.style.color = '#ff6666';
            }
            addSystemMessage('Could not connect to any Think Tank API. Using local processing only.', 'error');
            return;
        }
        
        const endpoint = API_ENDPOINTS[currentEndpointIndex];
        console.log(`Trying endpoint: ${endpoint}`);
        
        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            mode: 'cors',
            body: JSON.stringify({
                message: 'system_check',
                conversation_id: localStorage.getItem('minerva_conversation_id') || null
            })
        })
        .then(response => {
            if (response.ok) {
                console.log(`Think Tank API is available at ${endpoint}`);
                // Save working endpoint for future use
                localStorage.setItem('minerva_api_endpoint', endpoint);
                
                if (connectionIndicator) {
                    connectionIndicator.textContent = 'Connected to Think Tank';
                    connectionIndicator.style.color = '#66ffaa';
                }
                
                addSystemMessage(`Successfully connected to Think Tank API at ${endpoint}. Conversation memory is active.`, 'success');
                return response.json();
            } else {
                throw new Error(`API responded with status: ${response.status}`);
            }
        })
        .then(data => {
            console.log('System check response:', data);
            // Store conversation ID if provided
            if (data && data.conversation_id) {
                localStorage.setItem('minerva_conversation_id', data.conversation_id);
                console.log('Conversation ID initialized:', data.conversation_id);
            }
            
            // Initialize the history button functionality after successful connection
            setupHistoryButton();
            
            // Check if memory system is enabled in the response
            if (data && data.memory_status) {
                console.log('Memory status:', data.memory_status);
                localStorage.setItem('minerva_memory_enabled', data.memory_status.memory_enabled);
                
                // Update memory status indicator
                const memoryStatus = document.getElementById('memory-status');
                if (memoryStatus) {
                    memoryStatus.textContent = data.memory_status.memory_enabled ? 'Memory: On' : 'Memory: Off';
                    if (data.memory_status.memory_enabled) {
                        memoryStatus.classList.add('active');
                    } else {
                        memoryStatus.classList.remove('active');
                    }
                }
            }
        })
        .catch(error => {
            console.error(`Think Tank API check failed for ${endpoint}:`, error);
            // Try the next endpoint
            currentEndpointIndex++;
            tryNextEndpoint();
        });
    }
    
    // Start trying endpoints
    tryNextEndpoint();
}

// Helper function to send message with fallback mechanisms
function sendWithFallbacks(payload) {
    const currentApiEndpoint = localStorage.getItem('minerva_api_endpoint') || API_ENDPOINTS[0];
    console.log(`Attempting to send message to ${currentApiEndpoint}`);
    
    return new Promise((resolve, reject) => {
        fetch(currentApiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            mode: 'cors',
            body: JSON.stringify(payload)
        })
        .then(resolve)
        .catch(error => {
            console.error(`Error with endpoint ${currentApiEndpoint}:`, error);
            
            // Try next endpoint
            const currentIndex = API_ENDPOINTS.indexOf(currentApiEndpoint);
            if (currentIndex < API_ENDPOINTS.length - 1) {
                const nextEndpoint = API_ENDPOINTS[currentIndex + 1];
                console.log(`Trying next endpoint: ${nextEndpoint}`);
                localStorage.setItem('minerva_api_endpoint', nextEndpoint);
                
                fetch(nextEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    mode: 'cors',
                    body: JSON.stringify(payload)
                })
                .then(resolve)
                .catch(nextError => {
                    console.error(`Error with fallback endpoint ${nextEndpoint}:`, nextError);
                    reject(nextError);
                });
            } else {
                reject(error);
            }
        });
    });
}

// Handle the case when all API attempts fail
function handleAllApiFailure(payload, error, connectionStatus) {
    console.error('All API attempts failed:', error);
    
    // Hide typing indicator
    hideTypingIndicator();
    
    // Update connection status
    if (connectionStatus) {
        connectionStatus.textContent = 'All API Connections Failed';
        connectionStatus.style.color = '#ff6666';
    }
    
    // Provide fallback response from local storage if available
    let fallbackResponse = "I'm sorry, but I'm currently having trouble connecting to the Think Tank server. Your message was saved locally.";
    
    // Add error as system message and response as bot message
    addSystemMessage(`Error connecting to all Think Tank endpoints: ${error.message}`, 'error');
    addBotMessage(fallbackResponse);
    
    // Save the user's message locally
    const chatHistory = JSON.parse(localStorage.getItem('minerva_offline_messages') || '[]');
    chatHistory.push({
        message: payload.message,
        timestamp: Date.now(),
        conversation_id: payload.conversation_id
    });
    localStorage.setItem('minerva_offline_messages', JSON.stringify(chatHistory));
    
    // Let the user know their message was saved
    addSystemMessage('Your message has been saved locally and will be processed when connection is restored.', 'info');
}
