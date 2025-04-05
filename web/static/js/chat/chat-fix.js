/**
 * Emergency chat fix for Minerva
 * This directly addresses visibility, dragging, and message sending issues
 */
(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🛠️ Applying emergency chat fixes');
        applyFixes();
    });
    
    // If DOM already loaded, run immediately
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        console.log('🛠️ DOM already loaded, applying emergency chat fixes now');
        setTimeout(applyFixes, 100);
    }
    
    function applyFixes() {
        // Force chat to be visible
        forceVisibility();
        
        // Add direct drag handlers
        addDirectDragHandlers();
        
        // Fix Enter key handling
        fixEnterKey();
        
        // CRITICAL FIX: Fix message sending functionality
        fixMessageSending();
        
        console.log('✅ Emergency fixes applied');
    }
    
    function forceVisibility() {
        console.log('Making chat visible');
        
        // Integrated Chat
        const integratedChat = document.getElementById('integrated-chat');
        if (integratedChat) {
            Object.assign(integratedChat.style, {
                display: 'flex',
                position: 'fixed',
                top: '80px',
                right: '30px',
                bottom: 'auto',
                left: 'auto',
                zIndex: '9999',
                opacity: '1',
                visibility: 'visible',
                pointerEvents: 'auto',
                boxShadow: '0 0 20px rgba(100, 149, 237, 0.8)'
            });
            console.log('✓ Integrated chat positioned');
        }
        
        // Project Chat
        const projectChat = document.getElementById('project-chat');
        if (projectChat) {
            Object.assign(projectChat.style, {
                display: 'flex',
                position: 'fixed',
                top: '350px',
                left: '30px',
                bottom: 'auto',
                right: 'auto',
                zIndex: '9998',
                opacity: '1',
                visibility: 'visible',
                pointerEvents: 'auto',
                boxShadow: '0 0 20px rgba(120, 149, 200, 0.8)'
            });
            console.log('✓ Project chat positioned');
        }
    }
    
    function addDirectDragHandlers() {
        // Add direct drag handlers to chat headers
        const chatElements = [
            {
                chat: document.getElementById('integrated-chat'),
                header: document.querySelector('#integrated-chat .chat-header')
            },
            {
                chat: document.getElementById('project-chat'),
                header: document.querySelector('#project-chat .chat-header')
            }
        ];
        
        chatElements.forEach(({chat, header}) => {
            if (!chat || !header) return;
            
            console.log(`Adding direct drag for ${chat.id}`);
            
            // Make sure header appears draggable
            Object.assign(header.style, {
                cursor: 'move',
                userSelect: 'none',
                backgroundColor: 'rgba(60, 80, 150, 0.7)'
            });
            
            // Override any existing handlers by cloning the element
            const newHeader = header.cloneNode(true);
            header.parentNode.replaceChild(newHeader, header);
            header = newHeader;
            
            let isDragging = false;
            let offsetX, offsetY;
            
            header.addEventListener('mousedown', startDrag);
            
            function startDrag(e) {
                console.log(`Started dragging ${chat.id}`);
                isDragging = true;
                
                // Get mouse position relative to chat
                const rect = chat.getBoundingClientRect();
                offsetX = e.clientX - rect.left;
                offsetY = e.clientY - rect.top;
                
                // Add visual indicator
                chat.classList.add('dragging');
                Object.assign(chat.style, {
                    transition: 'none',
                    opacity: '0.85'
                });
                
                // Add move and up handlers to document
                document.addEventListener('mousemove', doDrag);
                document.addEventListener('mouseup', stopDrag);
                
                // Prevent text selection
                e.preventDefault();
            }
            
            function doDrag(e) {
                if (!isDragging) return;
                
                // Calculate new position
                const x = e.clientX - offsetX;
                const y = e.clientY - offsetY;
                
                // Keep chat within viewport bounds
                const maxX = window.innerWidth - chat.offsetWidth;
                const maxY = window.innerHeight - chat.offsetHeight;
                const boundedX = Math.max(0, Math.min(x, maxX));
                const boundedY = Math.max(0, Math.min(y, maxY));
                
                // Apply new position
                Object.assign(chat.style, {
                    left: boundedX + 'px',
                    top: boundedY + 'px',
                    right: 'auto',
                    bottom: 'auto'
                });
            }
            
            function stopDrag() {
                if (isDragging) {
                    console.log(`Stopped dragging ${chat.id}`);
                    isDragging = false;
                    
                    // Remove visual indicator
                    chat.classList.remove('dragging');
                    Object.assign(chat.style, {
                        transition: 'opacity 0.3s',
                        opacity: '1'
                    });
                    
                    // Remove handlers
                    document.removeEventListener('mousemove', doDrag);
                    document.removeEventListener('mouseup', stopDrag);
                }
            }
        });
    }
    
    function fixEnterKey() {
        // Get chat inputs and buttons
        const inputs = [
            {
                input: document.getElementById('chat-input'),
                button: document.getElementById('send-button')
            },
            {
                input: document.getElementById('project-chat-input'),
                button: document.getElementById('project-send-button')
            }
        ];
        
        // Add direct enter key handlers
        inputs.forEach(({input, button}) => {
            if (!input || !button) return;
            
            console.log(`Adding Enter key handler for ${input.id}`);
            
            // Clone input to remove existing handlers
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            // Add fresh event listener
            newInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    console.log('Enter key pressed, sending message');
                    e.preventDefault();
                    button.click();
                }
            });
            
            // Make sure button looks clickable
            Object.assign(button.style, {
                cursor: 'pointer'
            });
        });
    }
    
    function fixMessageSending() {
        console.log('🔧 Applying critical fix for message sending');
        
        // Find all send buttons across different chat interfaces
        const sendButtons = [
            document.getElementById('send-message'),
            document.getElementById('send-button'),
            document.querySelector('button.send-button'),
            ...Array.from(document.querySelectorAll('button[id$="-send-button"]')),
            ...Array.from(document.querySelectorAll('button[id$="send-message"]'))
        ].filter(button => button); // Remove null/undefined
        
        console.log(`Found ${sendButtons.length} send buttons to fix`);
        
        // Apply fix to each button
        sendButtons.forEach((button, index) => {
            // Clone the button to remove all existing handlers
            const newButton = button.cloneNode(true);
            button.parentNode.replaceChild(newButton, button);
            
            // Add our direct message sending handler
            newButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log(`Direct send handler triggered for button ${index} (${newButton.id || 'unnamed'})`);
                
                // Find the corresponding input field
                let chatInput = null;
                let parent = this.parentNode;
                
                // Search up to 3 levels up for an input field
                for (let i = 0; i < 3; i++) {
                    if (!parent) break;
                    
                    chatInput = parent.querySelector('textarea') || 
                               parent.querySelector('input[type="text"]');
                    
                    if (chatInput) break;
                    parent = parent.parentNode;
                }
                
                if (!chatInput) {
                    console.log('Could not find input field, searching in entire document');
                    // Try searching in the wider document context
                    chatInput = document.getElementById('chat-input') || 
                               document.getElementById('integrated-chat-input') ||
                               document.getElementById('project-chat-input');
                }
                
                if (!chatInput) {
                    console.error('No chat input found!');
                    return;
                }
                
                // Get the message from the input
                const message = chatInput.value.trim();
                console.log(`Message to send: "${message}"`);
                
                if (!message) {
                    console.log('Message is empty, not sending');
                    return;
                }
                
                // Find the message container
                let messageContainer = document.getElementById('chat-messages') ||
                                       document.querySelector('.chat-messages') ||
                                       document.querySelector('.messages-container');
                
                if (!messageContainer) {
                    console.error('No message container found!');
                    return;
                }
                
                // Clear the input
                chatInput.value = '';
                
                // Add user message to the chat
                const userMessageElement = document.createElement('div');
                userMessageElement.className = 'message user-message';
                userMessageElement.innerHTML = `<p>${message}</p>`;
                messageContainer.appendChild(userMessageElement);
                
                // Scroll to bottom
                messageContainer.scrollTop = messageContainer.scrollHeight;
                
                // Try to use external send function if it exists
                if (typeof window.MinervaExternalSendMessage === 'function') {
                    console.log('Using external send function');
                    window.MinervaExternalSendMessage();
                    return;
                }
                
                // Try to find and use the sendMessage function from the parent document
                if (typeof window.sendMessage === 'function') {
                    console.log('Using window.sendMessage function');
                    window.sendMessage();
                    return;
                }
                
                // Try to find simulateThinkTankResponse function
                if (typeof window.simulateThinkTankResponse === 'function') {
                    console.log('Using window.simulateThinkTankResponse function');
                    window.simulateThinkTankResponse(message);
                    return;
                }
                
                // Fallback: Add a system message saying the message was sent
                const systemMessageElement = document.createElement('div');
                systemMessageElement.className = 'message system-message';
                systemMessageElement.innerHTML = '<p><em>Message sent. This is a backup handler - the chat functionality is working at a basic level but a server response may not be generated.</em></p>';
                messageContainer.appendChild(systemMessageElement);
                messageContainer.scrollTop = messageContainer.scrollHeight;
                
                console.log('✅ Direct message handler completed successfully');
            });
            
            console.log(`✅ Fixed send button ${index} (${newButton.id || 'unnamed'})`);
        });
    }
})();
