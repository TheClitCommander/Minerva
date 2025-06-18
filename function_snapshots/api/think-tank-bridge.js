/**
 * Think Tank Visualization Bridge
 * 
 * This file connects the Minerva Think Tank API data to the 3D UI visualization.
 * It ensures that model rankings, blending information, and metrics are properly
 * displayed in the orbital interface.
 */

(function() {
    // Initialize when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('Think Tank Bridge initialized');
        
        // Listen for chat responses to update the UI
        setupResponseListener();
        
        // Initialize the orbital UI with default data
        updateOrbitalUI(getDefaultModelData());
    });

    /**
     * Set up event listeners for new chat responses 
     */
    function setupResponseListener() {
        // Check for new chat responses
        // This would be connected to your existing chat system
        
        // Mock listener for demonstration
        document.addEventListener('minerva-response-received', function(event) {
            if (event.detail && event.detail.model_info) {
                console.log('Received model info:', event.detail.model_info);
                updateOrbitalUI(event.detail.model_info);
            }
        });
        
        // Also hook into the existing chat functionality if possible
        hookIntoExistingChat();
    }
    
    /**
     * Hook into existing chat functionality to capture model data
     */
    function hookIntoExistingChat() {
        // Check if we have the addBotMessage function from minerva-chat.js
        if (window.addBotMessage && typeof window.addBotMessage === 'function') {
            // Store the original function
            const originalAddBotMessage = window.addBotMessage;
            
            // Override with our version that also updates the 3D UI
            window.addBotMessage = function(message, modelInfo) {
                // Call the original function
                originalAddBotMessage(message, modelInfo);
                
                // Update 3D UI if model info is available
                if (modelInfo) {
                    console.log('Chat response includes model info:', modelInfo);
                    updateOrbitalUI(modelInfo);
                }
            };
            
            console.log('Successfully hooked into chat system');
        } else {
            console.log('Chat system not available yet, will try again soon');
            // Try again in a second
            setTimeout(hookIntoExistingChat, 1000);
        }
    }
    
    /**
     * Update the orbital UI with model data
     * @param {Object} modelInfo - Model info data from the API
     */
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
    
    /**
     * Format model data from API to UI format
     * @param {Object} modelInfo - Model info from API
     * @returns {Array} Formatted model data for UI
     */
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
                    technical: Math.round(ranking.technical_score * 100) || 75
                },
                capabilities: ranking.capabilities || ["General"],
                active: ranking.selected || false,
                reasoning: ranking.reasoning || "Model selected based on ranking"
            };
        });
    }
    
    /**
     * Get default model data for initialization
     * @returns {Array} Default model data
     */
    function getDefaultModelData() {
        return [
            { 
                name: "GPT-4 Turbo", 
                score: 9.2, 
                metrics: { quality: 92, relevance: 95, technical: 89 }, 
                capabilities: ["Reasoning", "Code", "Creative"],
                active: false,
                reasoning: "Strong performance across all metrics with excellent code understanding"
            },
            { 
                name: "Claude 3 Opus", 
                score: 9.4, 
                metrics: { quality: 94, relevance: 93, technical: 91 }, 
                capabilities: ["Research", "Analysis", "Creative"],
                active: false,
                reasoning: "Top model for analytical reasoning and detailed explanations"
            },
            { 
                name: "Gemini Pro", 
                score: 8.7, 
                metrics: { quality: 87, relevance: 89, technical: 85 }, 
                capabilities: ["Fast", "Research"],
                active: false,
                reasoning: "Good balance of speed and quality for general queries"
            }
        ];
    }
    
    /**
     * Animate the Think Tank to show processing state
     */
    function animateThinkTankProcessing() {
        // Find the Think Tank tab and add highlighting
        const thinkTankTab = document.querySelector('.control-ring-tab[data-tab="Think Tank"]');
        if (thinkTankTab) {
            thinkTankTab.classList.add('active-tab');
            
            // Remove highlight after animation completes
            setTimeout(() => {
                thinkTankTab.classList.remove('active-tab');
            }, 3000);
        }
    }
})();
