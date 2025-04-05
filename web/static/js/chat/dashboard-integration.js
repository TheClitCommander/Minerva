/**
 * Minerva Chat Dashboard Integration
 * This script syncs the chat history with the dashboard display
 */

// Global dashboard update function
function updateDashboard() {
    console.log("Updating dashboard with conversation history...");
    
    // Try to get dashboard log element
    const dashboardLog = document.getElementById("dashboard-log");
    
    if (!dashboardLog) {
        console.warn("Dashboard log element not found - cannot update dashboard");
        return;
    }
    
    // Get conversation from localStorage
    const CONVO_STORAGE_KEY = "minerva_conversation";
    let conversation = JSON.parse(localStorage.getItem(CONVO_STORAGE_KEY)) || [];
    
    // Clear existing dashboard messages
    dashboardLog.innerHTML = "";
    
    if (conversation.length === 0) {
        // Show placeholder message if no conversations
        const placeholderEl = document.createElement("div");
        placeholderEl.className = "dashboard-placeholder";
        placeholderEl.textContent = "No conversations yet. Start chatting with Minerva to see your history here.";
        dashboardLog.appendChild(placeholderEl);
        return;
    }
    
    // Add header
    const headerEl = document.createElement("div");
    headerEl.className = "dashboard-header";
    headerEl.textContent = `Conversation History (${conversation.length} messages)`;
    dashboardLog.appendChild(headerEl);
    
    // Display each message in the conversation
    conversation.forEach((msg, index) => {
        const messageElement = document.createElement("div");
        messageElement.className = `dashboard-message ${msg.role}-message`;
        
        // Add avatar/icon
        const avatarEl = document.createElement("span");
        avatarEl.className = "message-avatar";
        avatarEl.textContent = msg.role === "user" ? "🧑" : "🤖";
        messageElement.appendChild(avatarEl);
        
        // Add message content
        const contentEl = document.createElement("span");
        contentEl.className = "message-content";
        contentEl.textContent = msg.message;
        messageElement.appendChild(contentEl);
        
        // Add timestamp if available
        if (msg.timestamp) {
            const timeEl = document.createElement("span");
            timeEl.className = "message-time";
            const msgDate = new Date(msg.timestamp);
            timeEl.textContent = msgDate.toLocaleTimeString();
            messageElement.appendChild(timeEl);
        }
        
        // Add to dashboard
        dashboardLog.appendChild(messageElement);
    });
    
    console.log("Dashboard updated successfully");
}

// Update dashboard when page loads
document.addEventListener("DOMContentLoaded", updateDashboard);

// Check for dashboard element every few seconds (in case it loads after this script)
let dashboardCheckInterval = setInterval(() => {
    const dashboardLog = document.getElementById("dashboard-log");
    if (dashboardLog) {
        updateDashboard();
        clearInterval(dashboardCheckInterval);
        console.log("Dashboard element found and updated");
    }
}, 2000);
