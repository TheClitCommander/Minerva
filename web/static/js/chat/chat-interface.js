/**
 * Minerva Think Tank Chat Interface Controls
 * Adds draggable functionality and minimize/maximize controls to the chat interface
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Minerva Think Tank Chat Interface...');
    initChatControls();
    setupModelPanels();
});

// Initialize the chat interface controls
function initChatControls() {
    const chatInterface = document.getElementById('chat-interface');
    if (!chatInterface) {
        console.error('Chat interface element not found!');
        return;
    }
    
    // Get chat header
    const chatHeader = document.getElementById('chat-header');
    if (!chatHeader) {
        console.error('Chat header not found!');
        return;
    }
    
    // Make chat interface draggable using the header
    makeDraggable(chatInterface, chatHeader);
    
    // Set up minimize button functionality
    const minimizeBtn = document.getElementById('minimize-chat');
    if (minimizeBtn) {
        minimizeBtn.addEventListener('click', function() {
            chatInterface.classList.toggle('minimized');
            
            // Toggle icon between minus and expand
            const icon = this.querySelector('i');
            if (icon) {
                if (chatInterface.classList.contains('minimized')) {
                    icon.classList.remove('fa-minus');
                    icon.classList.add('fa-expand');
                    this.setAttribute('title', 'Expand chat');
                } else {
                    icon.classList.remove('fa-expand');
                    icon.classList.add('fa-minus');
                    this.setAttribute('title', 'Minimize chat');
                }
            }
        });
    }
    
    // Set up metrics toggle button functionality
    const metricsToggle = document.getElementById('toggle-metrics');
    if (metricsToggle) {
        const metricsPanel = document.getElementById('model-metrics-panel');
        if (metricsPanel) {
            metricsToggle.addEventListener('click', function() {
                metricsPanel.classList.toggle('hidden');
            });
        }
    }
    
    // Autofocus chat input when clicking anywhere in the chat interface
    chatInterface.addEventListener('click', function(e) {
        // Only focus if not clicking a button or input element
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'INPUT') {
            const chatInput = document.getElementById('chat-input');
            if (chatInput && !chatInterface.classList.contains('minimized')) {
                chatInput.focus();
            }
        }
    });
    
    console.log('Chat interface controls initialized');
}

// Make an element draggable 
function makeDraggable(element, handle) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    
    if (handle) {
        // If a handle is provided, use it
        handle.style.cursor = 'move';
        handle.onmousedown = dragMouseDown;
    } else {
        // Otherwise use the entire element as handle
        element.onmousedown = dragMouseDown;
    }
    
    function dragMouseDown(e) {
        e = e || window.event;
        
        // Don't start dragging if clicked on a button or input
        if (e.target.tagName === 'BUTTON' || e.target.tagName === 'TEXTAREA' || 
            e.target.tagName === 'INPUT' || e.target.tagName === 'I') {
            return;
        }
        
        e.preventDefault();
        
        // Get the mouse cursor position at startup
        pos3 = e.clientX;
        pos4 = e.clientY;
        
        // Store the element's current position
        const rect = element.getBoundingClientRect();
        const rightOffset = window.innerWidth - rect.right;
        const bottomOffset = window.innerHeight - rect.bottom;
        
        // Update CSS to use all positions so we can maintain the correct layout
        // during and after dragging
        element.style.right = `${rightOffset}px`;
        element.style.bottom = `${bottomOffset}px`;
        element.style.left = 'auto';
        element.style.top = 'auto';
        
        // Add dragging class
        element.classList.add('dragging');
        
        // Stop animations during drag
        element.style.transition = 'none';
        
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
        
        // Get current positions
        const rect = element.getBoundingClientRect();
        let rightOffset = parseInt(element.style.right) + pos1;
        let bottomOffset = parseInt(element.style.bottom) + pos2;
        
        // Ensure the element stays within the viewport
        if (rightOffset < 0) rightOffset = 0;
        if (bottomOffset < 0) bottomOffset = 0;
        if (rightOffset > window.innerWidth - 100) rightOffset = window.innerWidth - 100;
        if (bottomOffset > window.innerHeight - 100) bottomOffset = window.innerHeight - 100;
        
        // Set the element's new position
        element.style.right = `${rightOffset}px`;
        element.style.bottom = `${bottomOffset}px`;
    }
    
    function closeDragElement() {
        // Stop moving when mouse button is released
        document.onmouseup = null;
        document.onmousemove = null;
        
        // Remove dragging class
        element.classList.remove('dragging');
        
        // Restore animations
        element.style.transition = '';
    }
}

// Set up model panels for displaying AI metrics
function setupModelPanels() {
    // Set up the model metrics panel
    const metricsPanel = document.getElementById('model-metrics-panel');
    if (!metricsPanel) return;
    
    // Add close button functionality
    const closeBtn = document.getElementById('close-metrics');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            metricsPanel.classList.add('hidden');
        });
    }
    
    // Add visualization initialization here if needed
    console.log('Model panels initialized');
    
    // Update metrics values from memory function
    updateMetricsFromMemory();
}

// Update metrics based on Think Tank memory data 
function updateMetricsFromMemory() {
    // These values would normally come from the server
    // but we'll initialize with reasonable defaults for now
    const metrics = {
        blendingPercentage: 85.2,
        rankAccuracy: 92.5,
        routingEfficiency: 88.7
    };
    
    // Update DOM elements with metrics values
    document.getElementById('blending-percentage')?.textContent = metrics.blendingPercentage.toFixed(1) + '%';
    document.getElementById('rank-accuracy')?.textContent = metrics.rankAccuracy.toFixed(1) + '%';
    document.getElementById('routing-efficiency')?.textContent = metrics.routingEfficiency.toFixed(1) + '%';
    
    // These would be updated as real requests come in
    setupModelUsageChart();
}

// Setup model usage distribution chart
function setupModelUsageChart() {
    const chartElement = document.getElementById('model-usage-chart');
    if (!chartElement) return;
    
    // In a real implementation, this would use a charting library 
    // like Chart.js or D3.js to create visualizations
    chartElement.innerHTML = `
        <div class="simple-chart">
            <div class="chart-bar" style="width: 65%; background-color: #19c37d;" title="GPT-4: 65%">GPT-4</div>
            <div class="chart-bar" style="width: 48%; background-color: #9c5ddb;" title="Claude-3: 48%">Claude-3</div>
            <div class="chart-bar" style="width: 32%; background-color: #4285f4;" title="Gemini: 32%">Gemini</div>
            <div class="chart-bar" style="width: 25%; background-color: #00a3bf;" title="Mistral: 25%">Mistral</div>
        </div>
    `;
}
