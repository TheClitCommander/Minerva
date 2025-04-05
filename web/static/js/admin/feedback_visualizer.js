/**
 * Feedback Visualizer for Admin Dashboard
 * 
 * This module creates visualizations of user feedback data for the admin dashboard.
 * It fetches feedback data from the server and creates charts using Chart.js.
 */

class FeedbackVisualizer {
    constructor(options = {}) {
        this.containerSelector = options.containerSelector || '#feedback-charts';
        this.apiEndpoint = options.apiEndpoint || '/api/admin/feedback_stats';
        this.timeRange = options.timeRange || 'last30days';
        this.charts = {};
        this.data = null;
    }

    /**
     * Initialize the visualizer and load data
     */
    async init() {
        try {
            // Create container elements if they don't exist
            this.createContainerElements();
            
            // Show loading state
            this.showLoading();
            
            // Fetch data
            await this.fetchData();
            
            // Render charts
            this.renderCharts();
            
            // Add event listeners for time range selectors
            this.setupEventListeners();
            
            return true;
        } catch (error) {
            console.error('Error initializing feedback visualizer:', error);
            this.showError(error.message);
            return false;
        }
    }
    
    /**
     * Create container elements for charts
     */
    createContainerElements() {
        const container = document.querySelector(this.containerSelector);
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Create controls
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'feedback-controls';
        controlsDiv.innerHTML = `
            <div class="time-range-selector">
                <label>Time Range:</label>
                <select id="feedback-time-range">
                    <option value="last7days">Last 7 Days</option>
                    <option value="last30days" selected>Last 30 Days</option>
                    <option value="last90days">Last 90 Days</option>
                    <option value="alltime">All Time</option>
                </select>
            </div>
        `;
        container.appendChild(controlsDiv);
        
        // Create status area
        const statusDiv = document.createElement('div');
        statusDiv.id = 'feedback-status';
        container.appendChild(statusDiv);
        
        // Create chart containers
        const chartGrid = document.createElement('div');
        chartGrid.className = 'feedback-chart-grid';
        
        // Event for data loaded - to notify parent components
        if (this.data) {
            document.dispatchEvent(new CustomEvent('feedback-data-loaded', { 
                detail: this.data 
            }));
        }
        
        // Overall feedback chart
        const overallDiv = document.createElement('div');
        overallDiv.className = 'chart-container';
        overallDiv.innerHTML = `
            <h3>Overall Feedback</h3>
            <canvas id="overall-feedback-chart"></canvas>
        `;
        chartGrid.appendChild(overallDiv);
        
        // Model comparison chart
        const modelComparisonDiv = document.createElement('div');
        modelComparisonDiv.className = 'chart-container';
        modelComparisonDiv.innerHTML = `
            <h3>Model Comparison</h3>
            <canvas id="model-comparison-chart"></canvas>
        `;
        chartGrid.appendChild(modelComparisonDiv);
        
        // Feedback over time chart
        const timeSeriesDiv = document.createElement('div');
        timeSeriesDiv.className = 'chart-container wide';
        timeSeriesDiv.innerHTML = `
            <h3>Feedback Over Time</h3>
            <canvas id="feedback-time-series-chart"></canvas>
        `;
        chartGrid.appendChild(timeSeriesDiv);
        
        // Feedback by query type
        const queryTypeDiv = document.createElement('div');
        queryTypeDiv.className = 'chart-container';
        queryTypeDiv.innerHTML = `
            <h3>Feedback by Query Type</h3>
            <canvas id="query-type-chart"></canvas>
        `;
        chartGrid.appendChild(queryTypeDiv);
        
        // Feedback reasons (word cloud or bar chart)
        const reasonsDiv = document.createElement('div');
        reasonsDiv.className = 'chart-container';
        reasonsDiv.innerHTML = `
            <h3>Common Feedback Reasons</h3>
            <div id="feedback-reasons-chart"></div>
        `;
        chartGrid.appendChild(reasonsDiv);
        
        // Add the chart grid to the main container
        container.appendChild(chartGrid);
    }
    
    /**
     * Show loading indicator
     */
    showLoading() {
        const statusEl = document.getElementById('feedback-status');
        if (statusEl) {
            statusEl.innerHTML = '<div class="loading">Loading feedback data...</div>';
        }
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const statusEl = document.getElementById('feedback-status');
        if (statusEl) {
            statusEl.innerHTML = `<div class="error">Error: ${message}</div>`;
        }
    }
    
    /**
     * Fetch feedback data from the server
     */
    async fetchData() {
        try {
            const response = await fetch(`${this.apiEndpoint}?timeRange=${this.timeRange}`);
            
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            this.data = await response.json();
            
            // Hide loading message
            const statusEl = document.getElementById('feedback-status');
            if (statusEl) {
                statusEl.innerHTML = '';
            }
            
            return this.data;
        } catch (error) {
            console.error('Error fetching feedback data:', error);
            throw error;
        }
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        const timeRangeSelect = document.getElementById('feedback-time-range');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', async (e) => {
                this.timeRange = e.target.value;
                await this.init();
            });
        }
    }
    
    /**
     * Render all charts
     */
    renderCharts() {
        if (!this.data) return;
        
        // Destroy any existing charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        // Event for data loaded - to notify parent components
        document.dispatchEvent(new CustomEvent('feedback-data-loaded', { 
            detail: this.data 
        }));
        
        // Render each chart
        this.renderOverallFeedbackChart();
        this.renderModelComparisonChart();
        this.renderTimeSeriesChart();
        this.renderQueryTypeChart();
        this.renderFeedbackReasonsChart();
        
        // If we have model adjustment recommendations, display them
        if (this.data.model_adjustments && Object.keys(this.data.model_adjustments).length > 0) {
            this.renderModelAdjustments();
        }
    }
    
    /**
     * Render overall feedback pie chart
     */
    renderOverallFeedbackChart() {
        const ctx = document.getElementById('overall-feedback-chart');
        if (!ctx) return;
        
        const { helpful, not_helpful } = this.data.overall;
        
        this.charts.overall = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Helpful', 'Not Helpful'],
                datasets: [{
                    data: [helpful, not_helpful],
                    backgroundColor: ['#4CAF50', '#F44336'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = helpful + not_helpful;
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${context.label}: ${context.raw} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Render model comparison chart
     */
    renderModelComparisonChart() {
        const ctx = document.getElementById('model-comparison-chart');
        if (!ctx) return;
        
        const models = this.data.by_model || {};
        const modelNames = Object.keys(models);
        const helpfulData = [];
        const notHelpfulData = [];
        
        modelNames.forEach(model => {
            helpfulData.push(models[model].helpful || 0);
            notHelpfulData.push(models[model].not_helpful || 0);
        });
        
        this.charts.modelComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [
                    {
                        label: 'Helpful',
                        data: helpfulData,
                        backgroundColor: '#4CAF50',
                        borderWidth: 1
                    },
                    {
                        label: 'Not Helpful',
                        data: notHelpfulData,
                        backgroundColor: '#F44336',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * Render time series chart
     */
    renderTimeSeriesChart() {
        const ctx = document.getElementById('feedback-time-series-chart');
        if (!ctx) return;
        
        const timeData = this.data.by_time || {};
        const dates = Object.keys(timeData).sort();
        const helpfulData = [];
        const notHelpfulData = [];
        
        dates.forEach(date => {
            helpfulData.push(timeData[date].helpful || 0);
            notHelpfulData.push(timeData[date].not_helpful || 0);
        });
        
        this.charts.timeSeries = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Helpful',
                        data: helpfulData,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        fill: true,
                        tension: 0.2
                    },
                    {
                        label: 'Not Helpful',
                        data: notHelpfulData,
                        borderColor: '#F44336',
                        backgroundColor: 'rgba(244, 67, 54, 0.1)',
                        fill: true,
                        tension: 0.2
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * Render query type chart
     */
    renderQueryTypeChart() {
        const ctx = document.getElementById('query-type-chart');
        if (!ctx) return;
        
        const queryTypes = this.data.by_query_type || {};
        const types = Object.keys(queryTypes);
        
        // Skip rendering if no data
        if (types.length === 0) return;
        
        // Format query type names for display
        const formatType = (type) => {
            return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
        };
        
        const helpfulData = [];
        const notHelpfulData = [];
        const successRates = [];
        
        types.forEach(type => {
            const helpful = queryTypes[type].helpful || 0;
            const notHelpful = queryTypes[type].not_helpful || 0;
            const total = helpful + notHelpful;
            
            helpfulData.push(helpful);
            notHelpfulData.push(notHelpful);
            
            // Calculate success rate
            const rate = total > 0 ? (helpful / total * 100) : 0;
            successRates.push(rate.toFixed(1));
        });
        
        // Create formatted labels with success rates
        const formattedLabels = types.map((type, index) => {
            return `${formatType(type)} (${successRates[index]}%)`;
        });
        
        this.charts.queryType = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: formattedLabels,
                datasets: [
                    {
                        label: 'Helpful',
                        data: helpfulData,
                        backgroundColor: 'rgba(76, 175, 80, 0.2)',
                        borderColor: '#4CAF50',
                        pointBackgroundColor: '#4CAF50'
                    },
                    {
                        label: 'Not Helpful',
                        data: notHelpfulData,
                        backgroundColor: 'rgba(244, 67, 54, 0.2)',
                        borderColor: '#F44336',
                        pointBackgroundColor: '#F44336'
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    r: {
                        min: 0,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const datasetLabel = context.dataset.label;
                                const value = context.raw;
                                const total = helpfulData[context.dataIndex] + notHelpfulData[context.dataIndex];
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${datasetLabel}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Render feedback reasons chart
     */
    renderFeedbackReasonsChart() {
        const container = document.getElementById('feedback-reasons-chart');
        if (!container) return;
        
        // Clear previous content and create container structure
        container.innerHTML = `
            <div class="feedback-reasons-container">
                <div class="row">
                    <div class="col-md-6">
                        <h4>Top Helpful Feedback Reasons</h4>
                        <canvas id="helpful-reasons-chart"></canvas>
                    </div>
                    <div class="col-md-6">
                        <h4>Top Not Helpful Feedback Reasons</h4>
                        <canvas id="not-helpful-reasons-chart"></canvas>
                    </div>
                </div>
                <div class="row mt-4">
                    <div class="col-md-12">
                        <h4>Categories of Not Helpful Feedback</h4>
                        <canvas id="feedback-categories-chart"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        // Check if we have the enhanced feedback reasons format
        if (this.data.feedback_reasons && 
            (this.data.feedback_reasons.helpful || this.data.feedback_reasons.not_helpful)) {
            
            this.renderEnhancedReasonCharts();
        } else {
            // Fall back to old format if needed
            this.renderLegacyReasonChart();
        }
    },
    
    /**
     * Render enhanced reason charts with separate helpful/not helpful and categories
     */
    renderEnhancedReasonCharts() {
        // Render helpful reasons chart
        const helpfulCtx = document.getElementById('helpful-reasons-chart');
        const notHelpfulCtx = document.getElementById('not-helpful-reasons-chart');
        const categoriesCtx = document.getElementById('feedback-categories-chart');
        
        const helpfulReasons = this.data.feedback_reasons.helpful || {};
        const notHelpfulReasons = this.data.feedback_reasons.not_helpful || {};
        const categories = this.data.feedback_reasons.categories || {};
        
        // Prepare helpful reasons data
        const helpfulData = Object.entries(helpfulReasons)
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 8);
            
        // Prepare not helpful reasons data
        const notHelpfulData = Object.entries(notHelpfulReasons)
            .sort((a, b) => b[1].count - a[1].count)
            .slice(0, 8);
            
        // Prepare categories data
        const categoriesData = Object.entries(categories)
            .sort((a, b) => b[1] - a[1]);
            
        // Helper function for label formatting
        const formatLabel = (text) => {
            if (text.length > 25) {
                return text.substring(0, 22) + '...';
            }
            return text;
        };
        
        // Create helpful reasons chart
        if (helpfulCtx && helpfulData.length > 0) {
            this.charts.helpfulReasons = new Chart(helpfulCtx, {
                type: 'bar',
                data: {
                    labels: helpfulData.map(item => formatLabel(item[0])),
                    datasets: [{
                        label: 'Count',
                        data: helpfulData.map(item => item[1].count),
                        backgroundColor: '#4CAF50',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                afterLabel: (context) => {
                                    const dataIndex = context.dataIndex;
                                    const examples = helpfulData[dataIndex][1].examples || [];
                                    if (examples.length === 0) return [];
                                    
                                    return ['Examples:', ...examples.map(ex => '• ' + ex)];
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create not helpful reasons chart
        if (notHelpfulCtx && notHelpfulData.length > 0) {
            this.charts.notHelpfulReasons = new Chart(notHelpfulCtx, {
                type: 'bar',
                data: {
                    labels: notHelpfulData.map(item => formatLabel(item[0])),
                    datasets: [{
                        label: 'Count',
                        data: notHelpfulData.map(item => item[1].count),
                        backgroundColor: '#F44336',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                afterLabel: (context) => {
                                    const dataIndex = context.dataIndex;
                                    const examples = notHelpfulData[dataIndex][1].examples || [];
                                    if (examples.length === 0) return [];
                                    
                                    return ['Examples:', ...examples.map(ex => '• ' + ex)];
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Create categories chart
        if (categoriesCtx && categoriesData.length > 0) {
            this.charts.feedbackCategories = new Chart(categoriesCtx, {
                type: 'polarArea',
                data: {
                    labels: categoriesData.map(item => item[0].charAt(0).toUpperCase() + item[0].slice(1)),
                    datasets: [{
                        data: categoriesData.map(item => item[1]),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        }
    },
    
    /**
     * Render legacy reason chart for backward compatibility
     */
    renderLegacyReasonChart() {
        const container = document.getElementById('helpful-reasons-chart');
        if (!container) return;
        
        const reasons = this.data.common_reasons || {};
        
        // Sort reasons by count
        const sortedReasons = Object.entries(reasons)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        this.charts.reasons = new Chart(container, {
            type: 'bar',
            data: {
                labels: sortedReasons.map(item => item[0]),
                datasets: [{
                    label: 'Count',
                    data: sortedReasons.map(item => item[1]),
                    backgroundColor: '#2196F3',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true
            }
        });
    }
}

// When the page is ready, initialize the feedback visualizer if we're on the admin page
/**
 * Render model adjustment recommendations
 */
FeedbackVisualizer.prototype.renderModelAdjustments = function() {
    const container = document.querySelector(this.containerSelector);
    if (!container) return;
    
    // Create recommendations section if it doesn't exist
    let recommendationsDiv = document.getElementById('model-adjustment-recommendations');
    if (!recommendationsDiv) {
        recommendationsDiv = document.createElement('div');
        recommendationsDiv.id = 'model-adjustment-recommendations';
        recommendationsDiv.className = 'chart-container wide';
        container.appendChild(recommendationsDiv);
    }
    
    // Clear previous content
    recommendationsDiv.innerHTML = '';
    
    // Create container for both sections - general and query-specific
    const adjustmentsHtml = `
        <div class="model-adjustments-container">
            <h3>Model Performance Insights & Recommendations</h3>
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4>General Model Performance</h4>
                        </div>
                        <div class="card-body" id="general-model-adjustments"></div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h4>Query Type Specialization</h4>
                        </div>
                        <div class="card-body" id="query-type-adjustments"></div>
                    </div>
                </div>
            </div>
            <div class="row mt-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h4>Recommended Actions</h4>
                        </div>
                        <div class="card-body" id="recommended-actions"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    recommendationsDiv.innerHTML = adjustmentsHtml;
    
    // Check if we have the enhanced data format
    if (this.data.model_adjustments && 
        (this.data.model_adjustments.general || this.data.model_adjustments.by_query_type)) {
        this.renderEnhancedModelAdjustments();
    } else {
        // Fallback to legacy format
        this.renderLegacyModelAdjustments();
    }
    
    // Add styling
    const style = document.createElement('style');
    style.textContent = `
        .model-adjustments-container {
            margin-bottom: 30px;
        }
        .model-adjustments-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .model-adjustments-table th, .model-adjustments-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .positive-adjustment {
            color: #4CAF50;
        }
        .negative-adjustment {
            color: #F44336;
        }
        .action-item {
            margin-bottom: 15px;
            padding: 10px;
            border-left: 4px solid #2196F3;
            background-color: #f8f9fa;
        }
        .action-type {
            font-weight: bold;
            margin-right: 5px;
        }
        .action-reason {
            font-style: italic;
            color: #666;
            margin-top: 5px;
        }
        .model-name {
            font-weight: bold;
        }
        .confidence-badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.8em;
            margin-left: 5px;
        }
        .high-confidence {
            background-color: #4CAF50;
            color: white;
        }
        .medium-confidence {
            background-color: #FFC107;
            color: black;
        }
        .low-confidence {
            background-color: #F44336;
            color: white;
        }
    `;
    document.head.appendChild(style);
};

/**
 * Render enhanced model adjustment recommendations
 */
FeedbackVisualizer.prototype.renderEnhancedModelAdjustments = function() {
    // Get the containers
    const generalContainer = document.getElementById('general-model-adjustments');
    const queryTypeContainer = document.getElementById('query-type-adjustments');
    const actionsContainer = document.getElementById('recommended-actions');
    
    if (!generalContainer || !queryTypeContainer || !actionsContainer) return;
    
    // Get the data
    const general = this.data.model_adjustments.general || {};
    const byQueryType = this.data.model_adjustments.by_query_type || {};
    const actions = this.data.model_adjustments.actions || [];
    
    // Render general model performance
    if (Object.keys(general).length > 0) {
        const topModels = general.top_models || [];
        const bottomModels = general.bottom_models || [];
        const recommendation = general.recommendation || 'No general recommendations available';
        
        let generalHtml = `
            <div class="general-recommendation">
                <p><strong>Recommendation:</strong> ${recommendation}</p>
            </div>
        `;
        
        if (topModels.length > 0) {
            generalHtml += `
                <div class="model-performance">
                    <h5>Top Performing Models</h5>
                    <ul class="top-models-list">
                        ${topModels.map(model => `<li class="model-name positive-adjustment">${model}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        if (bottomModels.length > 0) {
            generalHtml += `
                <div class="model-performance">
                    <h5>Models Needing Improvement</h5>
                    <ul class="bottom-models-list">
                        ${bottomModels.map(model => `<li class="model-name negative-adjustment">${model}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        generalContainer.innerHTML = generalHtml;
    } else {
        generalContainer.innerHTML = '<p>Insufficient data for general model recommendations.</p>';
    }
    
    // Render query type specialization
    if (Object.keys(byQueryType).length > 0) {
        const queryTypeEntries = Object.entries(byQueryType);
        
        if (queryTypeEntries.length > 0) {
            const queryTypeHtml = `
                <table class="model-adjustments-table">
                    <thead>
                        <tr>
                            <th>Query Type</th>
                            <th>Best Model</th>
                            <th>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${queryTypeEntries.map(([queryType, data]) => {
                            const displayQueryType = queryType.replace('_', ' ');
                            const confidenceClass = data.confidence >= 80 ? 'high-confidence' : 
                                                   data.confidence >= 60 ? 'medium-confidence' : 'low-confidence';
                            return `
                                <tr>
                                    <td><strong>${displayQueryType}</strong></td>
                                    <td>
                                        ${data.best_model}
                                        <span class="confidence-badge ${confidenceClass}">
                                            ${Math.round(data.confidence)}%
                                        </span>
                                    </td>
                                    <td>${data.recommendation}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
            
            queryTypeContainer.innerHTML = queryTypeHtml;
        } else {
            queryTypeContainer.innerHTML = '<p>No query type specialization data available.</p>';
        }
    } else {
        queryTypeContainer.innerHTML = '<p>Insufficient data for query type recommendations.</p>';
    }
    
    // Render recommended actions
    if (actions.length > 0) {
        const actionsHtml = `
            <div class="recommended-actions-list">
                ${actions.map(action => {
                    let actionIcon, actionClass;
                    
                    switch(action.action) {
                        case 'increase_weight':
                            actionIcon = '↑';
                            actionClass = 'positive-adjustment';
                            break;
                        case 'decrease_weight':
                            actionIcon = '↓';
                            actionClass = 'negative-adjustment';
                            break;
                        case 'specialize':
                            actionIcon = '🎯';
                            actionClass = 'info-adjustment';
                            break;
                        default:
                            actionIcon = '•';
                            actionClass = '';
                    }
                    
                    let actionText;
                    if (action.action === 'increase_weight') {
                        actionText = `Increase <span class="model-name">${action.model}</span> weight by ${action.amount}`;
                    } else if (action.action === 'decrease_weight') {
                        actionText = `Decrease <span class="model-name">${action.model}</span> weight by ${action.amount}`;
                    } else if (action.action === 'specialize') {
                        actionText = `Use <span class="model-name">${action.model}</span> for ${action.query_type.replace('_', ' ')} queries`;
                    } else {
                        actionText = `${action.action} for ${action.model}`;
                    }
                    
                    return `
                        <div class="action-item">
                            <div>
                                <span class="action-type ${actionClass}">${actionIcon}</span>
                                ${actionText}
                            </div>
                            <div class="action-reason">${action.reason}</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
        
        actionsContainer.innerHTML = actionsHtml;
    } else {
        actionsContainer.innerHTML = '<p>No specific actions recommended at this time.</p>';
    }
};

/**
 * Render legacy model adjustment recommendations for backward compatibility
 */
FeedbackVisualizer.prototype.renderLegacyModelAdjustments = function() {
    // Get the container
    const generalContainer = document.getElementById('general-model-adjustments');
    if (!generalContainer) return;
    
    // Check if we have legacy data
    if (!this.data.model_adjustments || typeof this.data.model_adjustments !== 'object') {
        generalContainer.innerHTML = '<p>No model adjustment data available.</p>';
        return;
    }
    
    // Create a table for adjustments
    const tableHtml = `
        <table class="model-adjustments-table">
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Adjustment</th>
                    <th>Recommendation</th>
                </tr>
            </thead>
            <tbody>
                ${Object.entries(this.data.model_adjustments).map(([model, adjustment]) => {
                    const direction = adjustment > 0 ? 'Increase' : 'Decrease';
                    const absAdjustment = Math.abs(adjustment).toFixed(2);
                    const colorClass = adjustment > 0 ? 'positive-adjustment' : 'negative-adjustment';
                    return `
                        <tr>
                            <td><strong>${model}</strong></td>
                            <td class="${colorClass}">${direction} by ${absAdjustment}</td>
                            <td>${this._getAdjustmentRecommendation(model, adjustment)}</td>
                        </tr>
                    `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    // Update the container
    generalContainer.innerHTML = tableHtml;
    
    // Hide other containers
    const queryTypeContainer = document.getElementById('query-type-adjustments');
    const actionsContainer = document.getElementById('recommended-actions');
    
    if (queryTypeContainer) {
        queryTypeContainer.parentElement.parentElement.style.display = 'none';
    }
    
    if (actionsContainer) {
        actionsContainer.parentElement.parentElement.style.display = 'none';
    }
};

/**
 * Generate a recommendation based on model adjustment
 */
FeedbackVisualizer.prototype._getAdjustmentRecommendation = function(model, adjustment) {
    if (Math.abs(adjustment) < 0.02) {
        return "Maintain current priority - performance is stable";
    }
    
    if (adjustment > 0.1) {
        return `Substantially increase ${model} priority - performing very well`;
    } else if (adjustment > 0.05) {
        return `Consider increasing ${model} priority for more queries`;
    } else if (adjustment > 0) {
        return `Slight performance improvement detected`;
    } else if (adjustment > -0.05) {
        return `Minor performance concerns detected`;
    } else if (adjustment > -0.1) {
        return `Consider decreasing ${model} priority for complex queries`;
    } else {
        return `Review model performance - consistently underperforming`;
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const feedbackContainer = document.getElementById('feedback-charts');
    if (feedbackContainer) {
        const visualizer = new FeedbackVisualizer();
        visualizer.init().catch(error => {
            console.error('Failed to initialize feedback visualizer:', error);
        });
    }
});
