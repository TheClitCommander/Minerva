/**
 * Minerva Animation Utilities
 * Handles UI animations and transitions for a more polished user experience
 */

const MinervaAnimation = (function() {
    // Configuration
    const config = {
        messageAnimationDuration: 300, // ms
        systemMessageVisibilityDuration: 5000, // ms - how long system messages stay visible
        typingIndicatorAnimationSpeed: 1000, // ms - full animation cycle
        enableReducedMotion: false // Will be set based on user preference
    };
    
    // Initialization
    function initialize() {
        // Check for reduced motion preference
        checkReducedMotionPreference();
        
        // Initialize animation handling for existing elements
        setupExistingElements();
        
        // Set up observers to handle new elements
        setupObservers();
        
        console.log('Animation utilities initialized');
    }
    
    // Check user preference for reduced motion
    function checkReducedMotionPreference() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        config.enableReducedMotion = prefersReducedMotion;
        
        // Listen for changes to the preference
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
            config.enableReducedMotion = e.matches;
        });
    }
    
    // Set up animation handlers for existing elements
    function setupExistingElements() {
        // Enhance existing messages with animation classes
        document.querySelectorAll('.message').forEach(message => {
            enhanceMessageElement(message);
        });
        
        // Enhance typing indicator
        enhanceTypingIndicator();
    }
    
    // Set up observers to handle new elements being added to the DOM
    function setupObservers() {
        // Create a mutation observer to watch for new messages
        const messageObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if the added node is a message or contains messages
                        if (node.classList && node.classList.contains('message')) {
                            enhanceMessageElement(node);
                        } else {
                            node.querySelectorAll('.message').forEach(message => {
                                enhanceMessageElement(message);
                            });
                        }
                    }
                });
            });
        });
        
        // Observe chat history containers
        const chatHistories = document.querySelectorAll('#chat-history, #project-chat-history');
        chatHistories.forEach(container => {
            if (container) {
                messageObserver.observe(container, { childList: true, subtree: true });
            }
        });
    }
    
    // Enhance a message element with animations
    function enhanceMessageElement(messageElement) {
        if (!messageElement) return;
        
        // Different animation based on message type
        if (messageElement.classList.contains('user-message')) {
            // Mark as just sent for the scale animation feedback
            messageElement.classList.add('just-sent');
            
            // Remove the class after animation completes to avoid repeat animations
            setTimeout(() => {
                messageElement.classList.remove('just-sent');
            }, config.messageAnimationDuration);
        } 
        else if (messageElement.classList.contains('system-message')) {
            // Add fade-out class to system messages after a delay
            setTimeout(() => {
                messageElement.classList.add('fade-out');
                
                // Optionally remove after fade-out completes
                setTimeout(() => {
                    // Either remove or just hide based on preference
                    // messageElement.remove();
                    messageElement.style.display = 'none';
                }, config.messageAnimationDuration + 500);
            }, config.systemMessageVisibilityDuration);
        }
        
        // Ensure message is visible after animation
        setTimeout(() => {
            ensureElementInView(messageElement);
        }, config.messageAnimationDuration / 2);
    }
    
    // Enhance typing indicator with animation
    function enhanceTypingIndicator() {
        const typingIndicators = document.querySelectorAll('.typing-indicator');
        
        typingIndicators.forEach(indicator => {
            if (!indicator.querySelector('span')) {
                // If no spans exist, create them for the animation dots
                indicator.innerHTML = '<span>.</span><span>.</span><span>.</span>';
            }
        });
    }
    
    // Create a new typing indicator with animation
    function createTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span>.</span><span>.</span><span>.</span>';
        return indicator;
    }
    
    // Scroll an element into view smoothly
    function ensureElementInView(element) {
        if (!element || config.enableReducedMotion) return;
        
        const parent = element.closest('.chat-history') || element.parentElement;
        
        if (parent) {
            // Scroll parent to show the element if it's not fully visible
            const parentRect = parent.getBoundingClientRect();
            const elementRect = element.getBoundingClientRect();
            
            if (elementRect.bottom > parentRect.bottom || elementRect.top < parentRect.top) {
                element.scrollIntoView({ 
                    behavior: config.enableReducedMotion ? 'auto' : 'smooth', 
                    block: 'end' 
                });
            }
        }
    }
    
    // Add hover effects to interactive elements
    function enhanceInteractiveElements() {
        // Add hover effect classes to various interactive elements
        document.querySelectorAll('.project-card, .branch-node, button:not(.formatting-button)').forEach(element => {
            element.classList.add('interactive-element');
        });
    }
    
    // Public API
    return {
        initialize,
        enhanceMessageElement,
        createTypingIndicator,
        ensureElementInView,
        enhanceInteractiveElements
    };
})();

// Initialize animations when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // We'll initialize this from the main script
});
