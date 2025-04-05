/**
 * Response Ranking System - Client-side JavaScript
 * 
 * Handles the client-side functionality for the response ranking system
 * including integration with the chat interface, ranking submissions,
 * and analytics display.
 */

class ResponseRankingManager {
    constructor() {
        this.currentConversationId = null;
        this.currentModelName = null;
        this.employeeId = this.getEmployeeId();
        this.lastRankedMessageId = null;
        
        this.initEventListeners();
    }
    
    /**
     * Initialize all event listeners for the ranking system
     */
    initEventListeners() {
        // Add ranking buttons to each AI message
        document.addEventListener('DOMContentLoaded', () => {
            this.addRankingButtonsToMessages();
            
            // Watch for new messages and add ranking buttons
            const chatContainer = document.getElementById('chat-messages');
            if (chatContainer) {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                            this.addRankingButtonsToMessages();
                        }
                    });
                });
                
                observer.observe(chatContainer, { childList: true, subtree: true });
            }
            
            // Initialize any other UI components
            this.initAnalyticsDisplay();
        });
    }
    
    /**
     * Add ranking buttons to all AI messages in the chat
     */
    addRankingButtonsToMessages() {
        const aiMessages = document.querySelectorAll('.ai-message');
        
        aiMessages.forEach(message => {
            // Check if this message already has a ranking button
            if (!message.querySelector('.rank-response-button')) {
                const messageId = message.getAttribute('data-message-id');
                const messageContent = message.querySelector('.message-content').textContent;
                
                // Create ranking button
                const rankButton = document.createElement('button');
                rankButton.className = 'rank-response-button';
                rankButton.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg> Rank Response';
                rankButton.onclick = () => this.openRankingModal(messageId, messageContent);
                
                // Find the message tools container or create one
                let toolsContainer = message.querySelector('.message-tools');
                if (!toolsContainer) {
                    toolsContainer = document.createElement('div');
                    toolsContainer.className = 'message-tools';
                    message.appendChild(toolsContainer);
                }
                
                toolsContainer.appendChild(rankButton);
            }
        });
    }
    
    /**
     * Open the ranking modal for a specific message
     * 
     * @param {string} messageId - The ID of the message to rank
     * @param {string} messageContent - The content of the message
     */
    openRankingModal(messageId, messageContent) {
        // Find the query that led to this response
        const messageElement = document.querySelector(`[data-message-id="${messageId}"]`);
        let queryContent = "Unknown query";
        let modelName = "unknown";
        
        if (messageElement) {
            // Find the previous user message
            let prevElement = messageElement.previousElementSibling;
            while (prevElement) {
                if (prevElement.classList.contains('user-message')) {
                    queryContent = prevElement.querySelector('.message-content').textContent;
                    break;
                }
                prevElement = prevElement.previousElementSibling;
            }
            
            // Try to extract model name from message metadata if available
            const modelBadge = messageElement.querySelector('.model-badge');
            if (modelBadge) {
                modelName = modelBadge.textContent;
            }
        }
        
        // Save current message context
        this.lastRankedMessageId = messageId;
        this.currentModelName = modelName;
        
        // Open the ranking page in a new tab/window
        const rankingUrl = `/rank_response?message_id=${encodeURIComponent(messageId)}&model=${encodeURIComponent(modelName)}&employee_id=${encodeURIComponent(this.employeeId)}`;
        window.open(rankingUrl, '_blank');
    }
    
    /**
     * Initialize analytics display if on the analytics page
     */
    initAnalyticsDisplay() {
        const analyticsContainer = document.getElementById('ranking-analytics');
        if (!analyticsContainer) return;
        
        // Load analytics data
        fetch('/api/ranking_analytics')
            .then(response => response.json())
            .then(data => {
                this.renderAnalyticsCharts(data);
            })
            .catch(error => {
                console.error('Error loading analytics data:', error);
                analyticsContainer.innerHTML = '<div class="error-message">Error loading analytics data.</div>';
            });
    }
    
    /**
     * Render analytics charts with the provided data
     * 
     * @param {Object} data - The analytics data
     */
    renderAnalyticsCharts(data) {
        const analyticsContainer = document.getElementById('ranking-analytics');
        if (!analyticsContainer) return;
        
        // Clear container
        analyticsContainer.innerHTML = '';
        
        // Model performance comparison chart
        if (data.model_performance) {
            this.createModelPerformanceChart(data.model_performance);
        }
        
        // Criteria breakdown chart
        if (data.criteria_averages) {
            this.createCriteriaChart(data.criteria_averages);
        }
        
        // Score distribution chart
        if (data.score_distribution) {
            this.createScoreDistributionChart(data.score_distribution);
        }
    }
    
    /**
     * Create a model performance comparison chart
     * 
     * @param {Object} performanceData - Model performance data
     */
    createModelPerformanceChart(performanceData) {
        // Implementation depends on your preferred charting library
        // This is a placeholder that would be replaced with actual chart rendering
        const container = document.createElement('div');
        container.className = 'analytics-chart';
        container.innerHTML = `<h3>Model Performance Comparison</h3>
                              <div class="chart-placeholder">
                                <p>Chart would render here using the performance data.</p>
                                <pre>${JSON.stringify(performanceData, null, 2)}</pre>
                              </div>`;
        
        document.getElementById('ranking-analytics').appendChild(container);
    }
    
    /**
     * Create a criteria breakdown chart
     * 
     * @param {Object} criteriaData - Criteria average scores data
     */
    createCriteriaChart(criteriaData) {
        // Implementation depends on your preferred charting library
        const container = document.createElement('div');
        container.className = 'analytics-chart';
        container.innerHTML = `<h3>Criteria Score Breakdown</h3>
                              <div class="chart-placeholder">
                                <p>Chart would render here using the criteria data.</p>
                                <pre>${JSON.stringify(criteriaData, null, 2)}</pre>
                              </div>`;
        
        document.getElementById('ranking-analytics').appendChild(container);
    }
    
    /**
     * Create a score distribution chart
     * 
     * @param {Object} distributionData - Score distribution data
     */
    createScoreDistributionChart(distributionData) {
        // Implementation depends on your preferred charting library
        const container = document.createElement('div');
        container.className = 'analytics-chart';
        container.innerHTML = `<h3>Score Distribution</h3>
                              <div class="chart-placeholder">
                                <p>Chart would render here using the distribution data.</p>
                                <pre>${JSON.stringify(distributionData, null, 2)}</pre>
                              </div>`;
        
        document.getElementById('ranking-analytics').appendChild(container);
    }
    
    /**
     * Get the employee ID, either from storage or prompt the user
     * 
     * @returns {string} The employee ID
     */
    getEmployeeId() {
        let employeeId = localStorage.getItem('minerva_employee_id');
        
        if (!employeeId) {
            employeeId = this.promptForEmployeeId();
            if (employeeId) {
                localStorage.setItem('minerva_employee_id', employeeId);
            }
        }
        
        return employeeId || 'anonymous';
    }
    
    /**
     * Prompt the user for their employee ID
     * 
     * @returns {string} The employee ID
     */
    promptForEmployeeId() {
        return prompt('Please enter your employee ID for ranking submissions:', '');
    }
}

// Initialize the ranking manager
const responseRankingManager = new ResponseRankingManager();

// Export for potential use in other modules
window.ResponseRankingManager = ResponseRankingManager;
