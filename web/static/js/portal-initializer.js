/**
 * Minerva Portal Initializer
 * Ensures chat functionality and background effects work correctly
 */
(function() {
    console.log('🚀 Initializing Minerva Portal');
    
    // Create stars for background
    function createStars() {
        console.log('Creating star background');
        const container = document.querySelector('.portal-container');
        const starsContainer = document.createElement('div');
        starsContainer.className = 'stars';
        
        // Create 100 stars with random positions
        for (let i = 0; i < 100; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.animationDelay = `${Math.random() * 4}s`;
            starsContainer.appendChild(star);
        }
        
        if (container) {
            container.appendChild(starsContainer);
        }
    }
    
    // Force position chats in visible area
    function positionChats() {
        console.log('Positioning chat windows');
        
        // Main chat
        const integratedChat = document.getElementById('integrated-chat');
        if (integratedChat) {
            integratedChat.style.position = 'fixed';
            integratedChat.style.top = '100px';
            integratedChat.style.right = '30px';
            integratedChat.style.left = 'auto';
            integratedChat.style.bottom = 'auto';
            integratedChat.style.zIndex = '9999';
            integratedChat.style.boxShadow = '0 0 20px rgba(100, 149, 237, 0.6)';
            integratedChat.style.display = 'flex';
        }
        
        // Project chat
        const projectChat = document.getElementById('project-chat');
        if (projectChat) {
            projectChat.style.position = 'fixed';
            projectChat.style.top = '350px';
            projectChat.style.left = '30px';
            projectChat.style.right = 'auto';
            projectChat.style.bottom = 'auto';
            projectChat.style.zIndex = '9998';
            projectChat.style.boxShadow = '0 0 20px rgba(100, 149, 237, 0.6)';
            projectChat.style.display = 'flex';
        }
    }
    
    // Handle chat drag functionality directly
    function setupDragFunctionality() {
        console.log('Setting up drag functionality');
        
        const chatElements = [
            {
                container: document.getElementById('integrated-chat'),
                handle: document.querySelector('#integrated-chat .chat-header')
            },
            {
                container: document.getElementById('project-chat'),
                handle: document.querySelector('#project-chat .chat-header')
            }
        ];
        
        chatElements.forEach(({container, handle}) => {
            if (!container || !handle) return;
            
            // Make handle visibly draggable
            handle.style.cursor = 'move';
            handle.title = 'Drag to move chat';
            
            let isDragging = false;
            let offsetX, offsetY;
            
            handle.addEventListener('mousedown', (e) => {
                isDragging = true;
                offsetX = e.clientX - container.getBoundingClientRect().left;
                offsetY = e.clientY - container.getBoundingClientRect().top;
                container.classList.add('dragging');
                
                console.log(`Started dragging ${container.id}`);
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                // Keep within window bounds
                const maxX = window.innerWidth - container.offsetWidth;
                const maxY = window.innerHeight - container.offsetHeight;
                
                const boundedX = Math.max(0, Math.min(x, maxX));
                const boundedY = Math.max(0, Math.min(y, maxY));
                
                container.style.left = `${boundedX}px`;
                container.style.top = `${boundedY}px`;
                container.style.right = 'auto';
                container.style.bottom = 'auto';
            });
            
            document.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                    container.classList.remove('dragging');
                    console.log(`Stopped dragging ${container.id}`);
                }
            });
        });
    }
    
    // Fix chat input handling
    function fixChatInputs() {
        console.log('Fixing chat input handling');
        
        // Main chat
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        
        if (chatInput && sendButton) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendButton.click();
                }
            });
            
            sendButton.addEventListener('click', () => {
                const message = chatInput.value.trim();
                if (message) {
                    console.log('Sending message:', message);
                    // This will be handled by minerva-chat.js
                    chatInput.value = '';
                    chatInput.focus();
                }
            });
        }
        
        // Project chat
        const projectChatInput = document.getElementById('project-chat-input');
        const projectSendButton = document.getElementById('project-send-button');
        
        if (projectChatInput && projectSendButton) {
            projectChatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    projectSendButton.click();
                }
            });
            
            projectSendButton.addEventListener('click', () => {
                const message = projectChatInput.value.trim();
                if (message) {
                    console.log('Sending project message:', message);
                    // This will be handled by minerva-chat.js
                    projectChatInput.value = '';
                    projectChatInput.focus();
                }
            });
        }
    }
    
    // Run initialization when DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize immediately
        createStars();
        
        // Wait for a moment to ensure elements are fully rendered
        setTimeout(() => {
            positionChats();
            setupDragFunctionality();
            fixChatInputs();
        }, 500);
        
        console.log('✅ Minerva Portal initialization complete');
    });
    
    // If DOMContentLoaded already fired, run now
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        createStars();
        setTimeout(() => {
            positionChats();
            setupDragFunctionality();
            fixChatInputs();
        }, 500);
    }
})();
