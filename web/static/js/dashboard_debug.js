// Dashboard Debugging Tool
console.log("Dashboard Debug Script Loaded");

// Store original fetch function to monitor API calls
const originalFetch = window.fetch;

// Override fetch to monitor all API calls
window.fetch = async function(url, options) {
    console.log(`🔍 API Call detected: ${url}`);
    
    try {
        const response = await originalFetch(url, options);
        
        // Clone the response to avoid consuming it
        const clonedResponse = response.clone();
        
        // Only log analytics API calls
        if (url.includes('/analytics')) {
            try {
                const data = await clonedResponse.json();
                console.log("📊 Analytics API Response:", data);
                
                // Check specifically for Think Tank metrics
                if (data.think_tank_metrics) {
                    console.log("✅ Think Tank metrics found in API response:", data.think_tank_metrics);
                } else {
                    console.error("❌ Think Tank metrics missing from API response!");
                }
            } catch (err) {
                console.error("Error parsing API response:", err);
            }
        }
        
        return response;
    } catch (error) {
        console.error(`❌ API Call failed for ${url}:`, error);
        throw error;
    }
};

// Add a function to verify DOM elements
function verifyDashboardElements() {
    console.log("🔍 Checking dashboard elements...");
    
    // Check Think Tank metric cards
    const thinkTankElements = [
        { id: 'blending-percentage', name: 'Blending Accuracy' },
        { id: 'rank-accuracy', name: 'Ranking Precision' },
        { id: 'routing-efficiency', name: 'Routing Efficiency' },
        { id: 'validation-rate', name: 'Validation Success' },
        { id: 'capability-match', name: 'Capability Match' }
    ];
    
    thinkTankElements.forEach(element => {
        const el = document.getElementById(element.id);
        if (el) {
            console.log(`✅ Found ${element.name} element (${element.id}): ${el.innerText}`);
        } else {
            console.error(`❌ Missing ${element.name} element (${element.id})`);
        }
    });
    
    // Check chart canvases
    const chartCanvases = [
        { id: 'queryTagsChart', name: 'Query Tags Chart' },
        { id: 'blendingStrategyChart', name: 'Blending Strategy Chart' }
    ];
    
    chartCanvases.forEach(canvas => {
        const el = document.getElementById(canvas.id);
        if (el) {
            console.log(`✅ Found ${canvas.name} canvas (${canvas.id})`);
        } else {
            console.error(`❌ Missing ${canvas.name} canvas (${canvas.id})`);
        }
    });
    
    // Check that Chart.js is loaded
    if (typeof Chart !== 'undefined') {
        console.log("✅ Chart.js is loaded");
    } else {
        console.error("❌ Chart.js is not loaded!");
    }
}

// Add a function to manually update dashboard from API data
async function manuallyUpdateDashboard() {
    console.log("🔄 Manually updating dashboard...");
    
    try {
        const response = await fetch('/analytics');
        const data = await response.json();
        console.log("📊 Fetched analytics data:", data);
        
        if (!data.think_tank_metrics) {
            console.error("❌ Think Tank metrics missing!");
            return;
        }
        
        // Update Think Tank metrics
        updateThinkTankMetrics(data.think_tank_metrics);
        
        // Update charts
        if (typeof updateQueryTagsChart === 'function') {
            console.log("🔄 Updating Query Tags Chart...");
            updateQueryTagsChart(data.think_tank_metrics.query_tags);
        } else {
            console.error("❌ updateQueryTagsChart function not found!");
        }
        
        if (typeof updateBlendingStrategyChart === 'function') {
            console.log("🔄 Updating Blending Strategy Chart...");
            updateBlendingStrategyChart(data.think_tank_metrics.blending_strategies);
        } else {
            console.error("❌ updateBlendingStrategyChart function not found!");
        }
        
        console.log("✅ Manual dashboard update complete");
    } catch (error) {
        console.error("❌ Error manually updating dashboard:", error);
    }
}

// Helper function to update Think Tank metrics
function updateThinkTankMetrics(metrics) {
    try {
        if (document.getElementById('blending-percentage')) {
            document.getElementById('blending-percentage').innerText = 
                metrics.blending_accuracy.toFixed(1) + '%';
        }
        
        if (document.getElementById('rank-accuracy')) {
            document.getElementById('rank-accuracy').innerText = 
                metrics.ranking_precision.toFixed(1) + '%';
        }
        
        if (document.getElementById('routing-efficiency')) {
            document.getElementById('routing-efficiency').innerText = 
                metrics.routing_efficiency.toFixed(1) + '%';
        }
        
        if (document.getElementById('validation-rate')) {
            document.getElementById('validation-rate').innerText = 
                metrics.validation_success.toFixed(1) + '%';
        }
        
        if (document.getElementById('capability-match')) {
            document.getElementById('capability-match').innerText = 
                metrics.capability_match.toFixed(1) + '%';
        }
        
        console.log("✅ Think Tank metrics updated successfully");
    } catch (error) {
        console.error("❌ Error updating Think Tank metrics:", error);
    }
}

// Run verification when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Dashboard debug script ready");
    
    // Check if we're on the correct page
    const currentPath = window.location.pathname;
    console.log(`📍 Current page: ${currentPath}`);
    
    if (currentPath === '/analytics-dashboard') {
        console.log("✅ Correct dashboard URL detected");
    } else {
        console.warn(`⚠️ Incorrect URL detected. You are on ${currentPath} instead of /analytics-dashboard`);
    }
    
    // Verify dashboard elements
    setTimeout(verifyDashboardElements, 1000);
    
    // Add debug button to page
    const debugButton = document.createElement('button');
    debugButton.innerText = 'Debug Dashboard';
    debugButton.style.position = 'fixed';
    debugButton.style.bottom = '20px';
    debugButton.style.right = '20px';
    debugButton.style.zIndex = '9999';
    debugButton.style.padding = '10px';
    debugButton.style.backgroundColor = '#ff5722';
    debugButton.style.color = 'white';
    debugButton.style.border = 'none';
    debugButton.style.borderRadius = '4px';
    debugButton.style.cursor = 'pointer';
    
    debugButton.addEventListener('click', function() {
        console.clear();
        console.log("🛠️ Running dashboard debug...");
        verifyDashboardElements();
        manuallyUpdateDashboard();
    });
    
    document.body.appendChild(debugButton);
});

// Expose debug functions globally
window.dashboardDebug = {
    verifyElements: verifyDashboardElements,
    manualUpdate: manuallyUpdateDashboard
};

console.log("Dashboard Debug Script Fully Loaded");
