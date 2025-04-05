/**
 * MINERVA IMMEDIATE FIXES
 * 
 * This script runs immediately to fix critical issues before any other scripts run.
 * It focuses on removing duplicate welcome messages and formatting error messages.
 */

// Execute immediately
(function() {
    console.log('🛠️ MINERVA IMMEDIATE FIXES: Running emergency fixes');
    
    // Function to clean up chat history when it becomes available
    function cleanupChatHistory() {
        const chatHistory = document.getElementById('chat-history');
        if (!chatHistory) {
            console.log('Chat history not found, will retry in 100ms');
            setTimeout(cleanupChatHistory, 100);
            return;
        }
        
        console.log('Found chat history, cleaning up duplicates');
        
        // SUPER AGGRESSIVE removal of duplicate welcome messages
        const welcomeMessages = chatHistory.querySelectorAll('.message.system.info, .system-message.info');
        if (welcomeMessages.length > 0) {
            console.log(`CRITICAL: Found ${welcomeMessages.length} welcome messages, removing all duplicates`);
            
            // Keep only the first one
            const firstWelcome = welcomeMessages[0];
            
            // Remove ALL welcome messages
            welcomeMessages.forEach(msg => msg.remove());
            
            // Add back just the first one
            chatHistory.prepend(firstWelcome);
        }
        
        // Clean up any raw error messages
        const errorMessages = chatHistory.querySelectorAll('.message.system.error');
        errorMessages.forEach(msg => {
            const text = msg.textContent || '';
            
            if (text.includes('Failed to fetch') || text.includes('Error connecting to Think Tank API')) {
                // Replace with a more user-friendly message
                msg.innerHTML = `<div class="message-content">
                    <div class="message-text">Think Tank API is currently offline. Your messages are being saved locally.</div>
                    <div class="message-note">Using fallback mode per Rule #4</div>
                    <div class="message-time">${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                </div>`;
                msg.className = 'message system warning';
            }
        });
    }
    
    // Run immediately
    cleanupChatHistory();
    
    // Also run when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', cleanupChatHistory);
    
    // And run again after a short delay to catch any late-loaded content
    setTimeout(cleanupChatHistory, 500);
    setTimeout(cleanupChatHistory, 1500);
    
    // Override console.error to never show empty objects
    const originalConsoleError = console.error;
    console.error = function(...args) {
        // Replace empty objects with descriptive message
        const processedArgs = args.map(arg => {
            if (arg && typeof arg === 'object' && Object.keys(arg).length === 0) {
                return "API connection error: Server may be offline or unreachable";
            }
            return arg;
        });
        
        originalConsoleError.apply(console, processedArgs);
    };
    
    console.log('🏁 MINERVA IMMEDIATE FIXES: Emergency fixes applied');
})();
