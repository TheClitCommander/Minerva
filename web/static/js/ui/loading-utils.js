/**
 * Minerva Loading Utilities
 * Manages loading states, skeleton loaders, and visual feedback during operations
 */

const MinervaLoading = (function() {
    // Configuration
    const config = {
        skeletonMessageCount: 3, // Number of skeleton messages to show when loading chat history
        typingDelayMin: 500,     // Minimum typing delay in ms
        typingDelayMax: 2000,    // Maximum typing delay in ms
        enableReducedMotion: false // Will be set based on user preference
    };
    
    // Initialize the loading utilities
    function initialize() {
        // Check for reduced motion preference
        checkReducedMotionPreference();
        
        // Set up any existing loading states
        setupExistingLoadingStates();
        
        console.log('Loading utilities initialized');
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
    
    // Set up any existing loading states on the page
    function setupExistingLoadingStates() {
        // Find and enhance any existing loading indicators
        document.querySelectorAll('.loading-indicator, .processing-spinner').forEach(loader => {
            // Apply any needed enhancements or animations
            enhanceLoadingIndicator(loader);
        });
    }
    
    // Create a skeleton loader for chat messages
    function createMessageSkeleton(type = 'bot-message', lines = 3) {
        const skeleton = document.createElement('div');
        skeleton.className = `message-skeleton ${type}`;
        
        // Add different line lengths for a more natural look
        const lineTypes = ['short', 'medium', 'long'];
        
        for (let i = 0; i < lines; i++) {
            const lineType = lineTypes[Math.floor(Math.random() * lineTypes.length)];
            const line = document.createElement('div');
            line.className = `skeleton-loader line ${lineType}`;
            skeleton.appendChild(line);
        }
        
        return skeleton;
    }
    
    // Create a conversation history skeleton with alternating messages
    function createConversationSkeleton(container) {
        const skeleton = document.createElement('div');
        skeleton.className = 'conversation-skeleton';
        
        // Create alternating user and bot message skeletons
        for (let i = 0; i < config.skeletonMessageCount; i++) {
            const type = i % 2 === 0 ? 'user-message' : 'bot-message';
            const lines = type === 'user-message' ? 1 : Math.floor(Math.random() * 3) + 2;
            const messageSkeleton = createMessageSkeleton(type, lines);
            skeleton.appendChild(messageSkeleton);
        }
        
        // Add to the container if provided
        if (container) {
            container.innerHTML = '';
            container.appendChild(skeleton);
        }
        
        return skeleton;
    }
    
    // Create the AI response loading skeleton
    function createAIResponseLoading() {
        const loading = document.createElement('div');
        loading.className = 'ai-response-loading';
        
        // Avatar skeleton
        const avatar = document.createElement('div');
        avatar.className = 'skeleton-loader avatar';
        
        // Content skeleton with thinking animation
        const content = document.createElement('div');
        content.className = 'content';
        
        const thinking = document.createElement('div');
        thinking.className = 'thinking-animation';
        thinking.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        
        content.appendChild(thinking);
        
        loading.appendChild(avatar);
        loading.appendChild(content);
        
        return loading;
    }
    
    // Show AI response loading indicator
    function showAIResponseLoading(container) {
        // Remove any existing loading indicators
        hideAIResponseLoading(container);
        
        // Create and add the loading indicator
        const loading = createAIResponseLoading();
        loading.id = 'ai-response-loading';
        container.appendChild(loading);
        
        // Make sure it's visible by scrolling to it
        if (window.MinervaAnimation) {
            MinervaAnimation.ensureElementInView(loading);
        } else {
            container.scrollTop = container.scrollHeight;
        }
        
        return loading;
    }
    
    // Hide AI response loading indicator
    function hideAIResponseLoading(container) {
        const loading = container.querySelector('#ai-response-loading');
        if (loading) {
            loading.remove();
        }
    }
    
    // Create a loading overlay for a container
    function createLoadingOverlay(title = 'Loading...', subtitle = 'Please wait') {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        
        const content = document.createElement('div');
        content.className = 'loading-content';
        
        const spinner = document.createElement('div');
        spinner.className = 'processing-spinner';
        
        const titleEl = document.createElement('div');
        titleEl.className = 'title';
        titleEl.textContent = title;
        
        const subtitleEl = document.createElement('div');
        subtitleEl.className = 'subtitle';
        subtitleEl.textContent = subtitle;
        
        content.appendChild(spinner);
        content.appendChild(titleEl);
        content.appendChild(subtitleEl);
        overlay.appendChild(content);
        
        return overlay;
    }
    
    // Show a loading overlay on a container
    function showLoadingOverlay(container, title, subtitle) {
        // Remove any existing overlay
        hideLoadingOverlay(container);
        
        // Create and add the overlay
        const overlay = createLoadingOverlay(title, subtitle);
        overlay.id = `loading-overlay-${Date.now()}`;
        
        // Make sure the container has position relative or absolute
        const currentPosition = window.getComputedStyle(container).position;
        if (currentPosition === 'static') {
            container.style.position = 'relative';
        }
        
        container.appendChild(overlay);
        return overlay;
    }
    
    // Hide a loading overlay from a container
    function hideLoadingOverlay(container) {
        const overlay = container.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
            
            // Reset position if we changed it
            if (container.style.position === 'relative') {
                container.style.position = '';
            }
        }
    }
    
    // Create a progress bar
    function createProgressBar() {
        const bar = document.createElement('div');
        bar.className = 'progress-bar';
        return bar;
    }
    
    // Enhance an existing loading indicator with animations
    function enhanceLoadingIndicator(indicator) {
        if (!indicator) return;
        
        // Custom animations based on the type of indicator
        if (indicator.classList.contains('spinner') || indicator.classList.contains('processing-spinner')) {
            // Already styled by our CSS, nothing additional needed
        } else if (indicator.classList.contains('dots') || indicator.classList.contains('thinking-animation')) {
            // Ensure it has dots if it's a thinking animation
            if (indicator.children.length === 0) {
                indicator.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
            }
        }
    }
    
    // Apply skeleton loaders to elements within a container
    function applySkeletonLoaders(container, selector, type) {
        if (!container) return;
        
        container.querySelectorAll(selector).forEach(element => {
            // Hide the original element
            element.style.visibility = 'hidden';
            
            // Create a skeleton loader
            const skeleton = document.createElement('div');
            skeleton.className = `skeleton-loader ${type}`;
            
            // Insert the skeleton before the element
            element.parentNode.insertBefore(skeleton, element);
        });
    }
    
    // Remove skeleton loaders from a container
    function removeSkeletonLoaders(container) {
        if (!container) return;
        
        // Remove all skeleton loaders
        container.querySelectorAll('.skeleton-loader, .message-skeleton, .conversation-skeleton').forEach(skeleton => {
            skeleton.remove();
        });
        
        // Show all hidden elements
        container.querySelectorAll('[style*="visibility: hidden"]').forEach(element => {
            element.style.visibility = '';
        });
    }
    
    // Public API
    return {
        initialize,
        createMessageSkeleton,
        createConversationSkeleton,
        createAIResponseLoading,
        showAIResponseLoading,
        hideAIResponseLoading,
        createLoadingOverlay,
        showLoadingOverlay,
        hideLoadingOverlay,
        createProgressBar,
        enhanceLoadingIndicator,
        applySkeletonLoaders,
        removeSkeletonLoaders
    };
})();

// Initialize loading utilities when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // We'll initialize this from the main script
});
