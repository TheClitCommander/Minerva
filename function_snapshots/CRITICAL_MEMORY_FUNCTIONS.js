/**
 * MINERVA CRITICAL MEMORY FUNCTIONS
 * 
 * This file documents the critical memory and conversation persistence functions
 * that must be maintained throughout development. These functions handle:
 * 1. Preventing duplicate responses in the chat interface
 * 2. Ensuring project context is maintained 
 * 3. Preserving conversation memory across sessions
 * 
 * DO NOT MODIFY THESE FUNCTIONS WITHOUT THOROUGH TESTING
 */

/**
 * Fixed handleThinkTankResponse Function
 * This function was modified to fix the issue with duplicate responses
 * The key change was to ensure that AI responses are added only once
 */
function handleThinkTankResponse(data) {
    // Check for valid response
    if (!data || !data.response) {
        console.error('Invalid response from Think Tank API:', data);
        return;
    }
    
    // Extract response text
    const responseText = data.response;
    const messageId = data.message_id || generateUniqueId();
    let modelInfo = null;
    
    // Process model information if available
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

/**
 * Fixed sendProjectMessage Function
 * Handles sending messages with project context and ensuring responses are displayed correctly
 */
function sendProjectMessage() {
    const message = projectChatInput.value.trim();
    if (!message) return;
    
    // Get project context
    const projectId = sessionStorage.getItem('minerva_active_project_id');
    const projectName = sessionStorage.getItem('minerva_active_project_name');
    
    // Add message to project chat
    const projectChatMessages = document.getElementById('project-chat-messages');
    const msgElement = document.createElement('div');
    msgElement.className = 'user-message';
    msgElement.textContent = message;
    projectChatMessages.appendChild(msgElement);
    projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
    
    // Clear input
    projectChatInput.value = '';
    
    // Show loading indicator
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading-indicator';
    loadingElement.innerHTML = '<div class="dot-pulse"></div>';
    projectChatMessages.appendChild(loadingElement);
    projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
    
    // Make API call with project context
    fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            projectId: projectId,
            projectName: projectName,
            sessionId: localStorage.getItem('minerva_session_id')
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        const loadingIndicator = projectChatMessages.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Add AI response to project chat - ONLY ONCE
        const aiElement = document.createElement('div');
        aiElement.className = 'ai-message';
        
        // Add project context tag if available
        if (projectName) {
            const contextTag = document.createElement('span');
            contextTag.className = 'project-context-tag';
            contextTag.innerHTML = `<i class="fas fa-project-diagram"></i> ${projectName}`;
            aiElement.appendChild(contextTag);
        }
        
        // Format message with markdown if needed
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (typeof renderMarkdown === 'function') {
            messageContent.innerHTML = renderMarkdown(data.response);
        } else {
            messageContent.textContent = data.response;
        }
        
        aiElement.appendChild(messageContent);
        projectChatMessages.appendChild(aiElement);
        projectChatMessages.scrollTop = projectChatMessages.scrollHeight;
        
        // Update project context in memory system
        updateProjectMemoryContext(projectId, message, data.response);
    })
    .catch(error => {
        // Remove loading indicator
        const loadingIndicator = projectChatMessages.querySelector('.loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
        
        // Display error message
        const errorElement = document.createElement('div');
        errorElement.className = 'system-message error';
        errorElement.textContent = 'Error communicating with Minerva. Please try again.';
        projectChatMessages.appendChild(errorElement);
        console.error('API error:', error);
    });
}

/**
 * Functions for maintaining conversation memory across sessions and projects
 */

// Store session context in localStorage for persistence
function storeSessionContext(sessionId, conversationHistory) {
    try {
        localStorage.setItem(`minerva_session_${sessionId}`, JSON.stringify(conversationHistory));
        console.log(`Session context stored for session ${sessionId}`);
        return true;
    } catch (error) {
        console.error('Failed to store session context:', error);
        return false;
    }
}

// Retrieve session context from localStorage
function getSessionContext(sessionId) {
    try {
        const storedContext = localStorage.getItem(`minerva_session_${sessionId}`);
        if (storedContext) {
            return JSON.parse(storedContext);
        }
        return null;
    } catch (error) {
        console.error('Failed to retrieve session context:', error);
        return null;
    }
}

// Update project-specific memory context
function updateProjectMemoryContext(projectId, userMessage, aiResponse) {
    if (!projectId) return;
    
    try {
        // Retrieve existing project context or initialize new one
        let projectContext = JSON.parse(localStorage.getItem(`minerva_project_${projectId}`) || '[]');
        
        // Add the new conversation exchange
        projectContext.push({
            role: 'user',
            content: userMessage,
            timestamp: new Date().toISOString()
        });
        
        projectContext.push({
            role: 'assistant',
            content: aiResponse,
            timestamp: new Date().toISOString()
        });
        
        // Store updated context
        localStorage.setItem(`minerva_project_${projectId}`, JSON.stringify(projectContext));
        console.log(`Updated project context for project ${projectId}`);
    } catch (error) {
        console.error('Failed to update project memory context:', error);
    }
}

// Get project-specific memory context
function getProjectMemoryContext(projectId) {
    if (!projectId) return null;
    
    try {
        const projectContext = localStorage.getItem(`minerva_project_${projectId}`);
        if (projectContext) {
            return JSON.parse(projectContext);
        }
        return [];
    } catch (error) {
        console.error('Failed to retrieve project memory context:', error);
        return [];
    }
}

/**
 * Instructions for preserving these critical functions:
 * 
 * 1. Always maintain the fixed response handling logic to prevent duplications
 * 2. Ensure project context is properly stored and retrieved 
 * 3. Preserve session persistence mechanisms
 * 4. When modifying UI components, don't change these core memory functions
 * 5. Run thorough testing after any related changes
 */
