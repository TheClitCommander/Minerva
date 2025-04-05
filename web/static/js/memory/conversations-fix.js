/**
 * Minerva Conversations Page Fixes
 * Addresses issues with chat interface on the conversations page
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing conversations page fixes...');

    // Make chat container draggable
    makeChatDraggable();
    
    // Ensure Enter key functionality works
    setupMessageInput();
    
    // Set up background effects
    setupBackgroundEffects();
});

/**
 * Makes the chat container on the conversations page draggable
 */
function makeChatDraggable() {
    const chatContainer = document.querySelector('.card');
    
    if (!chatContainer) {
        console.error('Chat container not found!');
        return;
    }
    
    console.log('Making chat container draggable...');
    
    // Add draggable class and styling
    chatContainer.classList.add('draggable');
    
    // Create a drag handle at the top of the chat
    const cardHeader = chatContainer.querySelector('.card-header');
    if (cardHeader) {
        cardHeader.style.cursor = 'move';
        cardHeader.classList.add('drag-handle');
        
        // Set initial position if not already set
        if (!chatContainer.style.position) {
            chatContainer.style.position = 'relative';
        }
        
        // Initialize drag functionality
        let isDragging = false;
        let currentX, currentY, initialX, initialY;
        let xOffset = 0, yOffset = 0;

        cardHeader.addEventListener('mousedown', dragStart);
        document.addEventListener('mouseup', dragEnd);
        document.addEventListener('mousemove', drag);

        function dragStart(e) {
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;

            if (e.target === cardHeader) {
                isDragging = true;
                cardHeader.classList.add('active');
            }
        }

        function dragEnd() {
            initialX = currentX;
            initialY = currentY;

            isDragging = false;
            cardHeader.classList.remove('active');
        }

        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;

                xOffset = currentX;
                yOffset = currentY;

                setTranslate(currentX, currentY, chatContainer);
            }
        }

        function setTranslate(xPos, yPos, el) {
            el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
        }
    }
}

/**
 * Ensures message input handles Enter key properly
 */
function setupMessageInput() {
    const messageInput = document.getElementById('message-input');
    
    if (!messageInput) {
        console.error('Message input not found!');
        return;
    }
    
    console.log('Setting up message input with Enter key handling...');
    
    // Adjust input behavior
    messageInput.placeholder = "Type your message here...";
    
    // Ensure the chat form doesn't have unexpected submit behavior
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const messageInput = document.getElementById('message-input');
            if (messageInput && messageInput.value.trim()) {
                // The main chat.js script should handle the actual sending
                console.log('Form submitted, sending message:', messageInput.value);
            }
        });
    }
}

/**
 * Sets up subtle background effects for the chat page
 */
function setupBackgroundEffects() {
    const container = document.querySelector('.container-fluid');
    
    if (!container) return;
    
    // Add subtle background pattern
    container.style.backgroundImage = "url('data:image/svg+xml;utf8,<svg width=\"100\" height=\"100\" viewBox=\"0 0 100 100\" xmlns=\"http://www.w3.org/2000/svg\"><rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" fill=\"%23f8f9fa\"/><path d=\"M0 10L100 10M10 0L10 100\" stroke=\"%23eaeaea\" stroke-width=\"1\"/></svg>')";
    container.style.backgroundSize = "20px 20px";
    
    // Add subtle animation to the chat card
    const chatCard = document.querySelector('.card');
    if (chatCard) {
        chatCard.style.transition = "box-shadow 0.3s ease-in-out";
        chatCard.style.boxShadow = "0 4px 15px rgba(0, 0, 0, 0.1)";
        
        chatCard.addEventListener('mouseover', function() {
            this.style.boxShadow = "0 8px 25px rgba(0, 0, 0, 0.15)";
        });
        
        chatCard.addEventListener('mouseout', function() {
            this.style.boxShadow = "0 4px 15px rgba(0, 0, 0, 0.1)";
        });
    }
}
