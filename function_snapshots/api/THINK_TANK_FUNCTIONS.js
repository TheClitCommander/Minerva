/**
 * Minerva Think Tank - Critical Functions
 * 
 * This file contains snapshots of all critical Think Tank functions
 * that are essential to preserving Minerva's multi-model blending capabilities.
 * 
 * DO NOT MODIFY THESE FUNCTIONS WITHOUT EXTENSIVE TESTING
 */

// Orbital UI integration function
function updateOrbitalUI(modelInfo) {
    // Find the 3D UI container
    const container = document.getElementById('minerva-orbital-ui');
    if (!container) return;
    
    // Check if we have MinervaUI loaded
    if (typeof window.MinervaUI !== 'undefined') {
        // Get the root element where React is mounted
        const root = container.querySelector('#minerva-3d-root');
        if (!root) return;
        
        // Format model data for the UI
        const thinkTankData = formatModelDataForUI(modelInfo);
        
        // Dispatch event to update the UI
        // This avoids directly manipulating React state from outside
        const updateEvent = new CustomEvent('minerva-update-think-tank', {
            detail: {
                thinkTankData: thinkTankData,
                blendingInfo: modelInfo.blending || null,
                minervaState: 'processing'
            }
        });
        
        root.dispatchEvent(updateEvent);
        
        // Show temporary message for user
        console.log('Updated orbital UI with model data');
        
        // Animate the UI to show processing
        animateThinkTankProcessing();
    }
}

// Format model data for the UI display
function formatModelDataForUI(modelInfo) {
    // Default if no model info
    if (!modelInfo || !modelInfo.rankings) {
        return getDefaultModelData();
    }
    
    // Convert rankings to UI format
    return modelInfo.rankings.map(ranking => {
        return {
            name: ranking.model,
            score: parseFloat(ranking.score) * 10, // Convert to 0-10 scale
            metrics: {
                quality: Math.round(ranking.quality_score * 100) || 85,
                relevance: Math.round(ranking.relevance_score * 100) || 80,
                technical: Math.round(ranking.technical_score * 100) || 75,
                creativity: Math.round(ranking.creativity_score * 100) || 70,
                reasoning: Math.round(ranking.reasoning_score * 100) || 85
            }
        };
    });
}

// Core Think Tank response handler
function handleThinkTankResponse(data) {
    console.log('Received Think Tank response:', data);
    
    // Hide typing indicator
    document.getElementById('typing-indicator').classList.add('hidden');
    
    // Check for valid response
    if (!data || !data.response) {
        console.error('Invalid response from Think Tank API:', data);
        return;
    }
    
    // Check if we already have this message (prevent duplicates)
    const responseText = data.response.trim();
    const lastMessage = getLastMessageElement();
    
    if (lastMessage && lastMessage.classList.contains('bot-message')) {
        const lastMessageText = lastMessage.querySelector('.message-content').textContent.trim();
        if (lastMessageText === responseText) {
            console.warn('Duplicate message detected, ignoring');
            return;
        }
    }
    
    // Extract and format model information
    let modelInfo = null;
    if (data.model_info) {
        modelInfo = data.model_info;
        // Cache the model info for later use
        if (data.message_id) {
            sessionModelInfo[data.message_id] = modelInfo;
        }
    }
    
    // Create and add bot message with model info
    addBotMessageWithModelInfo(responseText, modelInfo, data.message_id);
    
    // Update analytics
    if (modelInfo) {
        updateModelMetrics(modelInfo);
    }
    
    // Store in memory if requested
    if (data.store_in_memory === true) {
        const conversationData = {
            user_message: lastUserMessage,
            bot_message: responseText,
            model_info: modelInfo,
            timestamp: new Date().toISOString()
        };
        
        storeConversationInMemory(conversationData);
    }
}

// Process data with the Think Tank server
function sendMessageToAPI(userMessage) {
    // Format API request
    const apiRequest = {
        message: userMessage,
        session_id: sessionId,
        user_id: userId,
        model: selectedModel,
        web_research: webResearchEnabled,
        research_depth: researchDepth,
        store_in_memory: true,
        include_model_info: true
    };
    
    // Add project context if present
    const projectContext = getProjectContext();
    if (projectContext) {
        apiRequest.project_id = projectContext.projectId;
        apiRequest.project_name = projectContext.projectName;
        apiRequest.project_context = projectContext.description;
    }
    
    console.log('Sending API request:', apiRequest);
    
    // Show typing indicator
    document.getElementById('typing-indicator').classList.remove('hidden');
    
    // API request
    fetch('/api/think-tank', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiRequest)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('API response:', data);
        handleThinkTankResponse(data);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('typing-indicator').classList.add('hidden');
        addBotMessage(`Sorry, I had trouble connecting to the Think Tank. Please try again. Error: ${error.message}`);
    });
}

/**
 * Apply model blending weights (for Think Tank)
 * @param {Array} responses - Model responses
 * @param {Array} weights - Model weights
 * @returns {Object} Blended response
 */
function blendModelResponses(responses, weights) {
    // Calculate weighted scores
    const scoredResponses = responses.map((response, i) => ({
        text: response.text,
        model: response.model,
        score: calculateResponseScore(response) * weights[i]
    }));
    
    // Sort by score
    scoredResponses.sort((a, b) => b.score - a.score);
    
    // Return highest scoring response with blending metadata
    return {
        text: scoredResponses[0].text,
        primary_model: scoredResponses[0].model,
        blending_info: {
            model_scores: scoredResponses.map(r => ({
                model: r.model,
                score: r.score
            })),
            weights: weights
        }
    };
}

// Model quality assessment function
function calculateResponseScore(response) {
    // Complex scoring based on multiple factors
    const coherence = assessCoherence(response.text);
    const relevance = assessRelevance(response.text, response.query);
    const completeness = assessCompleteness(response.text);
    const technicalAccuracy = assessTechnicalAccuracy(response.text);
    
    // Weighted average of all factors
    return (
        coherence * 0.25 +
        relevance * 0.3 +
        completeness * 0.25 +
        technicalAccuracy * 0.2
    );
}

// Cache for historical Think Tank responses
const thinkTankResponseCache = {
    // Store the last N model responses
    maxSize: 50,
    responses: [],
    
    // Add a new response to the cache
    add(response) {
        this.responses.unshift(response);
        if (this.responses.length > this.maxSize) {
            this.responses.pop();
        }
    },
    
    // Get responses for a specific model
    getByModel(modelName) {
        return this.responses.filter(r => r.model === modelName);
    },
    
    // Get all stored responses
    getAll() {
        return [...this.responses];
    },
    
    // Clear the cache
    clear() {
        this.responses = [];
    }
};
