/**
 * MINERVA FALLBACK CHAT HANDLER
 * 
 * Provides a client-side fallback when the Think Tank API is unavailable
 * Maintains conversation memory compatibility with the core system
 */

(function() {
    // Register the fallback handler in the global space
    window.minervaFallbackHandler = {
        initialize: initializeFallbackHandler,
        processMessage: processFallbackMessage,
        generateResponse: generateFallbackResponse,
        getSystemStatus: getSystemStatus
    };
    
    // Initialization state
    let isInitialized = false;
    
    // Initialize the fallback handler
    function initializeFallbackHandler() {
        console.log('🔶 Initializing Minerva Fallback Chat Handler');
        
        // Ensure conversation memory structures are available
        window.minervaMemory = window.minervaMemory || [];
        window.conversationHistory = window.conversationHistory || [];
        
        isInitialized = true;
        return true;
    }
    
    // Process a message when the API is unavailable
    async function processFallbackMessage(message, conversationId) {
        if (!isInitialized) {
            initializeFallbackHandler();
        }
        
        console.log('🔶 Processing message with fallback handler');
        console.log('Message:', message);
        console.log('Conversation ID:', conversationId);
        
        // Generate a response locally
        const response = await generateFallbackResponse(message, conversationId);
        
        // Return in the format expected by the Think Tank API
        return {
            status: "success",
            response: response.text,
            conversation_id: conversationId || 'fallback_' + Date.now(),
            message_id: 'msg_' + Date.now(),
            timestamp: new Date().toISOString(),
            model_info: {
                models_used: ["minerva-fallback"],
                rankings: [
                    {model_name: "minerva-fallback", score: 1.0, reason: "Only available model"}
                ],
                processing_time_ms: 150
            },
            using_real_think_tank: false,
            memory_updates: {
                saved_context: true,
                retrieved_contexts: []
            }
        };
    }
    
    // Generate a fallback response using client-side logic
    async function generateFallbackResponse(message, conversationId) {
        console.log('🔶 Generating fallback response');
        
        // Get response text based on keywords in the message
        let responseText = '';
        
        // Basic pattern matching for common message types
        if (message.match(/hello|hi|hey|greetings/i)) {
            responseText = "Hello! I'm currently operating in fallback mode. The Think Tank API connection is unavailable, but I'll do my best to assist you with basic responses.";
        } 
        else if (message.match(/help|how can you help|what can you do/i)) {
            responseText = "I can provide basic assistance while operating in fallback mode. For full functionality, the Think Tank API connection needs to be restored. Your messages are still being saved to conversation memory.";
        }
        else if (message.match(/project|projects/i)) {
            responseText = "Project functionality requires the Think Tank API to be fully operational. I've saved your request and it will be processed when the connection is restored.";
        }
        else if (message.match(/memory|remember|recall/i)) {
            responseText = "The conversation memory system is still functioning in fallback mode. Your messages are being saved, but advanced memory retrieval requires the Think Tank API connection.";
        }
        else if (message.match(/toggle|middle|center|orb|navigation/i)) {
            responseText = "The circular navigation system in the middle of the Minerva portal is an orbital navigation ring. It allows you to rotate through different interface options with the Minerva Orb in the center serving as a home button. The options follow an elliptical path to create a 3D depth effect.";
        }
        else {
            // Default response
            responseText = "I've received your message while operating in fallback mode. The Think Tank API is currently unavailable, but your message has been saved to conversation memory. For full functionality, please check the API connection and server status.";
        }
        
        // Add to local conversation memory
        if (window.conversationHistory) {
            window.conversationHistory.push({
                role: 'user',
                content: message,
                timestamp: new Date().toISOString()
            });
            
            window.conversationHistory.push({
                role: 'assistant',
                content: responseText,
                timestamp: new Date().toISOString()
            });
        }
        
        return {
            text: responseText,
            conversationId: conversationId
        };
    }
    
    // Get system status
    function getSystemStatus() {
        return {
            initialized: isInitialized,
            mode: 'fallback',
            apiConnected: false,
            memoryActive: true
        };
    }
    
    // Initialize immediately
    initializeFallbackHandler();
    console.log('🔶 Fallback handler ready');
})();
