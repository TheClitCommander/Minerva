/**
 * Minerva Think Tank Model Metrics
 * Displays model rankings, scores, and blending information from the Minerva Think Tank
 */

// Initialize the model metrics panel
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Minerva Model Metrics Panel...');
    createMetricsPanel();
    
    // Sample data for initial display
    const sampleModelInfo = {
        models: [
            { name: 'GPT-4', score: 0.92, color: '#19c37d', reason: 'Best overall quality and coherence' },
            { name: 'Claude-3', score: 0.89, color: '#9c5ddb', reason: 'Strong reasoning and technical accuracy' },
            { name: 'Gemini', score: 0.85, color: '#4285f4', reason: 'Good factual accuracy' }
        ],
        selected_model: 'GPT-4',
        blending_info: {
            method: 'weighted',
            contributors: ['GPT-4', 'Claude-3'],
            sections: [
                { model: 'GPT-4', weight: 0.6, contribution: 'Main analysis and structure' },
                { model: 'Claude-3', weight: 0.4, contribution: 'Technical details and examples' }
            ]
        }
    };
    
    // Initial update with sample data
    updateModelMetricsPanel(sampleModelInfo);
});

// Create the model metrics panel in the DOM
function createMetricsPanel() {
    if (!document.querySelector('.model-info-panel')) {
        const panel = document.createElement('div');
        panel.className = 'model-info-panel';
        panel.innerHTML = `
            <div class="model-info-title">Model Rankings</div>
            <div class="model-rankings"></div>
            <div class="model-info-title" style="margin-top: 12px;">Response Blending</div>
            <div class="blend-info"></div>
            <div class="panel-toggle">×</div>
        `;
        document.body.appendChild(panel);
        
        // Add toggle functionality
        const toggle = panel.querySelector('.panel-toggle');
        toggle.addEventListener('click', function() {
            panel.classList.toggle('minimized');
            toggle.textContent = panel.classList.contains('minimized') ? '+' : '×';
        });
    }
}

// Process model info from Think Tank response
function processModelInfo(modelInfo) {
    console.log('Processing model info:', modelInfo);
    if (!modelInfo || (!modelInfo.models && !modelInfo.rankings)) return;
    
    // Convert from potential API format to our display format if needed
    const displayModelInfo = convertModelInfoToDisplayFormat(modelInfo);
    updateModelMetricsPanel(displayModelInfo);
}

// Convert API model info to display format if needed
function convertModelInfoToDisplayFormat(modelInfo) {
    // Already in the right format
    if (modelInfo.models) return modelInfo;
    
    // Convert from API format
    const displayInfo = {
        models: [],
        blending_info: {
            method: modelInfo.blending_method || 'unknown',
            contributors: []
        }
    };
    
    // Convert rankings to models array
    if (modelInfo.rankings) {
        displayInfo.models = modelInfo.rankings.map(rank => ({
            name: rank.model_name,
            score: rank.score || rank.quality_score || 0.5,
            color: getModelColor(rank.model_name),
            reason: rank.reason || rank.selection_reason
        }));
    }
    
    // Extract blending info
    if (modelInfo.blending_info) {
        displayInfo.blending_info = {
            method: modelInfo.blending_info.method || 'weighted',
            contributors: modelInfo.blending_info.contributors || [],
            sections: modelInfo.blending_info.sections || []
        };
    }
    
    return displayInfo;
}

// Get standard color for a model
function getModelColor(modelName) {
    const modelColors = {
        'gpt-4': '#19c37d',
        'gpt-3.5': '#10a37f',
        'claude-3': '#9c5ddb',
        'claude-instant': '#8a5cca',
        'gemini': '#4285f4',
        'gemini-pro': '#4285f4',
        'llama-3': '#e37400',
        'mistral': '#00a3bf'
    };
    
    // Normalize model name for matching
    const normalizedName = modelName.toLowerCase();
    
    // Find matching color
    for (const [key, color] of Object.entries(modelColors)) {
        if (normalizedName.includes(key)) {
            return color;
        }
    }
    
    // Default color if no match
    return '#6366f1';
}

// Update model metrics panel with real data
function updateModelMetricsPanel(modelInfo) {
    if (!modelInfo) return;
    
    // Get or create the panel
    let metricsPanel = document.querySelector('.model-info-panel');
    if (!metricsPanel) {
        createMetricsPanel();
        metricsPanel = document.querySelector('.model-info-panel');
    }
    
    // Update model rankings
    if (modelInfo.models && modelInfo.models.length > 0) {
        const rankingsElement = metricsPanel.querySelector('.model-rankings');
        if (rankingsElement) {
            let rankingsHTML = '';
            modelInfo.models.forEach((model, index) => {
                const scorePercent = (model.score * 100).toFixed(0);
                rankingsHTML += `
                    <div class="model-score">
                        <span>${model.name}</span>
                        <span>${scorePercent}%</span>
                    </div>
                    <div class="model-score-bar">
                        <div class="model-score-fill" style="width: ${scorePercent}%; background-color: ${model.color || '#6366f1'};"></div>
                    </div>
                    ${model.reason ? `<div class="model-reason">${model.reason}</div>` : ''}
                `;
            });
            rankingsElement.innerHTML = rankingsHTML;
        }
    }
    
    // Update blending info
    if (modelInfo.blending_info) {
        const blendElement = metricsPanel.querySelector('.blend-info');
        if (blendElement) {
            const blending = modelInfo.blending_info;
            let blendHTML = `<div>Method: ${blending.method || 'N/A'}</div>`;
            
            if (blending.contributors && blending.contributors.length) {
                blendHTML += `<div>Contributors: ${blending.contributors.join(', ')}</div>`;
            }
            
            if (blending.sections && blending.sections.length) {
                blendHTML += `<div class="blend-sections">`;
                blending.sections.forEach(section => {
                    const weight = section.weight ? `(${(section.weight * 100).toFixed(0)}%)` : '';
                    blendHTML += `<div class="blend-section">
                        <span class="blend-model" style="color: ${getModelColor(section.model)}">${section.model}</span> ${weight}
                        ${section.contribution ? `<span class="blend-contribution">${section.contribution}</span>` : ''}
                    </div>`;
                });
                blendHTML += `</div>`;
            }
            
            blendElement.innerHTML = blendHTML;
        }
    }
}
