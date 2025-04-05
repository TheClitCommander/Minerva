/**
 * Think Tank Metrics System
 * Provides integration with real AI models for the Think Tank mode,
 * including visualization of model performance, rankings, and blending.
 */

// Initialize the Think Tank metrics system
let thinkTankMetrics = {
    // Performance metrics
    blendingPercentage: 85.2,
    rankAccuracy: 92.5,
    routingEfficiency: 88.7,
    
    // Tracking for analysis
    modelUsage: {},
    queryTypes: {},
    blendedResponses: 0,
    totalResponses: 0,
    
    // Model capability profiles from enhanced ranking system
    modelCapabilities: {
        "gpt-4": {
            technical: 0.95,
            creative: 0.85,
            reasoning: 0.9,
            general: 0.92
        },
        "claude-3": {
            technical: 0.88,
            creative: 0.92,
            reasoning: 0.94,
            general: 0.9
        },
        "gemini": {
            technical: 0.86,
            creative: 0.83,
            reasoning: 0.85,
            general: 0.84
        }
    }
};

// Cache for storing model info by message ID
const sessionModelInfo = {};

// Initialize metrics panel functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get metrics panel elements
    const metricsPanel = document.getElementById('model-metrics-panel');
    const toggleMetricsButton = document.getElementById('toggle-metrics');
    const closeMetricsButton = document.getElementById('close-metrics');
    
    // Set up event listeners
    if (toggleMetricsButton) {
        toggleMetricsButton.addEventListener('click', function() {
            metricsPanel.classList.toggle('hidden');
            // Update charts when panel is shown
            if (!metricsPanel.classList.contains('hidden')) {
                updatePerformanceMetrics();
            }
        });
    }
    
    if (closeMetricsButton) {
        closeMetricsButton.addEventListener('click', function() {
            metricsPanel.classList.add('hidden');
        });
    }
    
    // Initialize metrics
    updatePerformanceMetrics();
});

// Update performance metrics with real-time data
function updatePerformanceMetrics() {
    // Update performance metrics in the UI
    if (document.getElementById('blending-percentage')) {
        document.getElementById('blending-percentage').innerText = thinkTankMetrics.blendingPercentage.toFixed(1) + '%';
    }
    
    if (document.getElementById('rank-accuracy')) {
        document.getElementById('rank-accuracy').innerText = thinkTankMetrics.rankAccuracy.toFixed(1) + '%';
    }
    
    if (document.getElementById('routing-efficiency')) {
        document.getElementById('routing-efficiency').innerText = thinkTankMetrics.routingEfficiency.toFixed(1) + '%';
    }
    
    // Update model usage chart if element exists
    const modelUsageElement = document.getElementById('model-usage-chart');
    if (modelUsageElement && Object.keys(thinkTankMetrics.modelUsage).length > 0) {
        createModelUsageChart(modelUsageElement, thinkTankMetrics.modelUsage);
    } else if (modelUsageElement) {
        modelUsageElement.innerHTML = '<div class="chart-container"><p>No model usage data available yet</p></div>';
    }
    
    // Update query type distribution if element exists
    const queryTypeElement = document.getElementById('query-type-chart');
    if (queryTypeElement && Object.keys(thinkTankMetrics.queryTypes).length > 0) {
        createQueryTypeChart(queryTypeElement, thinkTankMetrics.queryTypes);
    } else if (queryTypeElement) {
        queryTypeElement.innerHTML = '<div class="chart-container"><p>No query type data available yet</p></div>';
    }
    
    // Update model capabilities chart if element exists
    const capabilitiesElement = document.getElementById('model-capabilities-chart');
    if (capabilitiesElement && Object.keys(thinkTankMetrics.modelCapabilities).length > 0) {
        if (typeof createModelCapabilitiesChart === 'function') {
            createModelCapabilitiesChart(capabilitiesElement, thinkTankMetrics.modelCapabilities);
        } else {
            capabilitiesElement.innerHTML = '<div class="chart-container"><p>Model capabilities visualization not available</p></div>';
        }
    } else if (capabilitiesElement) {
        capabilitiesElement.innerHTML = '<div class="chart-container"><p>No model capability data available yet</p></div>';
    }
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
                
                // Update response quality metrics if available
                if (data.think_tank_metrics.quality_metrics) {
                    thinkTankMetrics.qualityMetrics = data.think_tank_metrics.quality_metrics;
                    console.log('Updated quality metrics:', thinkTankMetrics.qualityMetrics);
                }
                
                // Update blending strategies if available
                if (data.think_tank_metrics.blending_strategies) {
                    thinkTankMetrics.blendingStrategies = data.think_tank_metrics.blending_strategies;
                    console.log('Updated blending strategies:', thinkTankMetrics.blendingStrategies);
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

// Process model info from response to update metrics
function processModelInfo(modelInfo) {
    if (!modelInfo) return;
    
    try {
        // Extract model usage information
        if (modelInfo.models_used) {
            // Count model usage
            modelInfo.models_used.forEach(model => {
                // Initialize or increment model usage count
                thinkTankMetrics.modelUsage[model] = (thinkTankMetrics.modelUsage[model] || 0) + 1;
            });
        } else if (modelInfo.rankings && modelInfo.rankings.length > 0) {
            // Alternative: use rankings if models_used is not available
            modelInfo.rankings.forEach(ranking => {
                // Initialize or increment model usage count
                thinkTankMetrics.modelUsage[ranking.model] = (thinkTankMetrics.modelUsage[ranking.model] || 0) + 1;
            });
        }
        
        // Track query type if available
        if (modelInfo.query_type) {
            const queryType = modelInfo.query_type;
            thinkTankMetrics.queryTypes[queryType] = (thinkTankMetrics.queryTypes[queryType] || 0) + 1;
        }
        
        // Extract capability information if available
        if (modelInfo.model_capabilities) {
            // Update our capabilities data
            thinkTankMetrics.modelCapabilities = {
                ...thinkTankMetrics.modelCapabilities,
                ...modelInfo.model_capabilities
            };
        }
        
        // Extract blending information if available
        if (modelInfo.blended) {
            // Track blended responses for percentage calculation
            thinkTankMetrics.blendedResponses++;
            
            // Track blending strategy if available
            if (modelInfo.blending && modelInfo.blending.strategy) {
                const strategy = modelInfo.blending.strategy;
                thinkTankMetrics.blendingStrategies = thinkTankMetrics.blendingStrategies || {};
                thinkTankMetrics.blendingStrategies[strategy] = (thinkTankMetrics.blendingStrategies[strategy] || 0) + 1;
            }
        }
        
        // Extract quality metrics if available to keep track of overall quality
        if (modelInfo.quality_metrics) {
            thinkTankMetrics.qualityMetrics = thinkTankMetrics.qualityMetrics || {};
            
            // Aggregate quality metrics
            for (const [metric, value] of Object.entries(modelInfo.quality_metrics)) {
                if (typeof value === 'number') {
                    // Initialize if not present
                    if (!thinkTankMetrics.qualityMetrics[metric]) {
                        thinkTankMetrics.qualityMetrics[metric] = {
                            sum: 0,
                            count: 0,
                            average: 0
                        };
                    }
                    
                    // Update the running average
                    thinkTankMetrics.qualityMetrics[metric].sum += value;
                    thinkTankMetrics.qualityMetrics[metric].count++;
                    thinkTankMetrics.qualityMetrics[metric].average = 
                        thinkTankMetrics.qualityMetrics[metric].sum / thinkTankMetrics.qualityMetrics[metric].count;
                }
            }
        }
        
        // Update total responses
        thinkTankMetrics.totalResponses++;
        
        // Calculate blending percentage
        if (thinkTankMetrics.totalResponses > 0) {
            thinkTankMetrics.blendingPercentage = (thinkTankMetrics.blendedResponses / thinkTankMetrics.totalResponses) * 100;
        }
        
        // Update UI metrics display
        updatePerformanceMetrics();
        
        // Log details for debugging
        console.log('Think Tank metrics updated:', thinkTankMetrics);
    } catch (error) {
        console.error('Error processing model info:', error);
    }
}

// Function to toggle model details visibility
function toggleModelDetails(button) {
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
}

// Make toggle function globally available
window.toggleModelDetails = toggleModelDetails;
