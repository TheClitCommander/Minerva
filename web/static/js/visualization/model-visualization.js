/**
 * Model Visualization Functions for Think Tank
 * Provides visualization components for AI model performance metrics, rankings, 
 * and blending information to support real AI integration.
 */

// Model usage visualization
function createModelUsageChart(container, modelData) {
    if (!container) return;
    
    // Create a visualization (in production, would use Chart.js or D3.js)
    let html = '<div class="chart-container"><h4>Model Usage</h4>';
    
    // Calculate total for percentage
    const total = Object.values(modelData).reduce((sum, count) => sum + count, 0);
    if (total === 0) {
        container.innerHTML = '<div class="chart-container"><p>No model usage data available</p></div>';
        return;
    }
    
    // Create bars for each model
    for (const [model, count] of Object.entries(modelData)) {
        const percentage = ((count / total) * 100).toFixed(1);
        // Get the model name without path
        const modelName = model.split('/').pop().replace(/-\d+$/, ''); 
        
        html += `
            <div class="chart-item">
                <div class="chart-label">${modelName}</div>
                <div class="chart-bar-container">
                    <div class="chart-bar" style="width: ${percentage}%;"></div>
                    <span class="chart-value">${percentage}% (${count})</span>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Query type distribution visualization
function createQueryTypeChart(container, queryData) {
    if (!container) return;
    
    // Create a visualization
    let html = '<div class="chart-container"><h4>Query Types</h4>';
    
    // Calculate total for percentage
    const total = Object.values(queryData).reduce((sum, count) => sum + count, 0);
    if (total === 0) {
        container.innerHTML = '<div class="chart-container"><p>No query type data available</p></div>';
        return;
    }
    
    // Create bars for each query type
    for (const [type, count] of Object.entries(queryData)) {
        const percentage = ((count / total) * 100).toFixed(1);
        
        // Capitalize the query type
        const queryType = type.charAt(0).toUpperCase() + type.slice(1);
        
        html += `
            <div class="chart-item">
                <div class="chart-label">${queryType}</div>
                <div class="chart-bar-container">
                    <div class="chart-bar" style="width: ${percentage}%;"></div>
                    <span class="chart-value">${percentage}% (${count})</span>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// Create model capabilities visualization based on model profiles
function createModelCapabilitiesChart(container, capabilitiesData) {
    if (!container || !capabilitiesData) {
        if (container) {
            container.innerHTML = '<p>No capability data available</p>';
        }
        return;
    }
    
    let html = '<div class="capabilities-chart"><h4>Model Capabilities</h4>';
    
    // Create a grid to show capabilities for each model
    html += '<div class="capabilities-grid">';
    
    for (const [modelName, capabilities] of Object.entries(capabilitiesData)) {
        // Format model name for display
        const displayName = modelName.split('/').pop().replace(/-\d+$/, '');
        
        html += `<div class="capability-card">
            <h5>${displayName}</h5>
            <div class="capability-metrics">`;
            
        // Add capability metrics
        for (const [capability, score] of Object.entries(capabilities)) {
            const percentage = (score * 100).toFixed(0);
            const capabilityName = capability.charAt(0).toUpperCase() + capability.slice(1);
            
            html += `
                <div class="capability-item">
                    <div class="capability-label">${capabilityName}</div>
                    <div class="capability-bar-container">
                        <div class="capability-bar" style="width: ${percentage}%;"></div>
                        <span class="capability-value">${percentage}%</span>
                    </div>
                </div>
            `;
        }
        
        html += '</div></div>';
    }
    
    html += '</div></div>';
    container.innerHTML = html;
}

// Model performance ranking visualization
function createModelPerformanceChart(container, modelInfo) {
    if (!container || !modelInfo || !modelInfo.rankings) {
        if (container) {
            container.innerHTML = '<p>No model ranking information available</p>';
        }
        return;
    }
    
    // Create a visualization of model performance rankings
    let html = '<div class="model-rankings"><h4>Model Rankings</h4><table class="model-rankings-table">';
    html += '<thead><tr><th>Model</th><th>Score</th><th>Reasoning</th></tr></thead><tbody>';
    
    // Sort rankings by score (descending)
    const sortedRankings = [...modelInfo.rankings].sort((a, b) => b.score - a.score);
    
    // Add rows for each model
    for (const ranking of sortedRankings) {
        const modelName = ranking.model.split('/').pop().replace(/-\d+$/, ''); // Get model name without path/version
        const score = typeof ranking.score === 'number' ? 
            (ranking.score * 100).toFixed(1) + '%' : 
            ranking.score || 'N/A';
        const reason = ranking.reason || 'No reasoning provided';
        
        html += `
            <tr>
                <td>${modelName}</td>
                <td class="text-center">${score}</td>
                <td>${reason}</td>
            </tr>
        `;
    }
    
    html += '</tbody></table></div>';
    
    // Add blending information if available
    if (modelInfo.blended && modelInfo.blending_info) {
        html += `
            <div class="blending-details">
                <h4>Blending Information</h4>
                <div class="blending-strategy">
                    <strong>Strategy:</strong> ${modelInfo.blending_info.strategy || 'Custom'}
                </div>
                <div class="blending-contributions">
                    <strong>Model Contributions:</strong>
                    <ul>
        `;
        
        // Add contribution details
        if (modelInfo.blending_info.contributions) {
            for (const [model, contribution] of Object.entries(modelInfo.blending_info.contributions)) {
                const modelName = model.split('/').pop().replace(/-\d+$/, '');
                html += `<li>${modelName}: ${contribution.percentage}% (${contribution.sections.join(', ')})</li>`;
            }
        }
        
        html += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Add quality metrics if available
    if (modelInfo.quality_metrics) {
        html += `
            <div class="quality-metrics">
                <h4>Quality Metrics</h4>
                <table class="metrics-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Add metrics rows
        for (const [metric, value] of Object.entries(modelInfo.quality_metrics)) {
            const metricName = metric.replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
                
            const displayValue = typeof value === 'number' ? 
                (value * 100).toFixed(1) + '%' : 
                value.toString();
                
            html += `
                <tr>
                    <td>${metricName}</td>
                    <td>${displayValue}</td>
                </tr>
            `;
        }
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// Enhanced user-facing bot message response
function addBotMessageWithModelInfo(chatHistory, message, modelInfo, messageId) {
    const timestamp = new Date().toLocaleTimeString();
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message';
    messageElement.dataset.messageId = messageId || Date.now().toString();
    
    let modelInfoHtml = '';
    if (modelInfo) {
        try {
            // Safely extract top model information
            let topModel = 'Unknown';
            let blendingInfo = 'Standard response';
            let modelCount = 0;
            
            if (modelInfo.rankings && modelInfo.rankings.length > 0) {
                topModel = modelInfo.rankings[0].model;
                // Show a more user-friendly model name
                const simplifiedModelName = topModel.split('/').pop().replace(/-\d+$/, '');
                topModel = simplifiedModelName;
                modelCount = modelInfo.rankings.length;
            }
            
            if (modelInfo.blended) {
                // Get blending strategy in a user-friendly format
                const strategyName = modelInfo.blending_info?.strategy || 'custom';
                blendingInfo = `Think Tank blending: ${strategyName}`;
            } else {
                blendingInfo = 'Single model response';
            }
            
            // Create enhanced model info section
            modelInfoHtml = `
                <div class="message-model-info">
                    <div class="model-summary">
                        <div><strong>Primary model:</strong> ${topModel}</div>
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
            
            // Store model info for later use
            if (window.sessionModelInfo) {
                window.sessionModelInfo[messageElement.dataset.messageId] = modelInfo;
            }
        } catch (error) {
            console.error('Error formatting model info:', error);
            modelInfoHtml = '<div class="message-model-info">Model information unavailable</div>';
        }
    }
    
    // Format the message with the correct structure
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-text">${message}</div>
            ${modelInfoHtml}
        </div>
        <div class="message-time">${timestamp}</div>
    `;
    
    // Add to chat history and scroll
    chatHistory.appendChild(messageElement);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return messageElement;
}
