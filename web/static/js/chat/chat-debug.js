/**
 * Chat Debug Helper
 * This script helps diagnose issues with the Minerva chat interfaces
 */
(function() {
    // Wait for DOM to be fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔍 Running Minerva Chat Debug Helper');
        
        // Check for chat elements
        setTimeout(function() {
            const integratedChat = document.getElementById('integrated-chat');
            const projectChat = document.getElementById('project-chat');
            
            console.log('Chat containers found:');
            console.log('- Integrated Chat:', !!integratedChat);
            console.log('- Project Chat:', !!projectChat);
            
            if (integratedChat) {
                console.log('Integrated Chat position:', {
                    position: window.getComputedStyle(integratedChat).position,
                    top: window.getComputedStyle(integratedChat).top,
                    left: window.getComputedStyle(integratedChat).left,
                    bottom: window.getComputedStyle(integratedChat).bottom,
                    right: window.getComputedStyle(integratedChat).right,
                    zIndex: window.getComputedStyle(integratedChat).zIndex
                });
            }
            
            if (projectChat) {
                console.log('Project Chat position:', {
                    position: window.getComputedStyle(projectChat).position,
                    top: window.getComputedStyle(projectChat).top,
                    left: window.getComputedStyle(projectChat).left,
                    bottom: window.getComputedStyle(projectChat).bottom,
                    right: window.getComputedStyle(projectChat).right,
                    zIndex: window.getComputedStyle(projectChat).zIndex
                });
            }
            
            // Force chat windows to be visible and interactive
            if (integratedChat) {
                integratedChat.style.position = 'fixed';
                integratedChat.style.top = '100px';
                integratedChat.style.left = '50%';
                integratedChat.style.transform = 'translateX(-50%)';
                integratedChat.style.bottom = 'auto';
                integratedChat.style.right = 'auto';
                integratedChat.style.zIndex = '9999';
                integratedChat.style.display = 'flex';
                integratedChat.style.opacity = '1';
                integratedChat.style.pointerEvents = 'auto';
                
                console.log('Force-positioned integrated chat');
            }
            
            if (projectChat) {
                projectChat.style.position = 'fixed';
                projectChat.style.top = '400px';
                projectChat.style.left = '50%';
                projectChat.style.transform = 'translateX(-50%)';
                projectChat.style.bottom = 'auto';
                projectChat.style.right = 'auto';
                projectChat.style.zIndex = '9998';
                projectChat.style.display = 'flex';
                projectChat.style.opacity = '1';
                projectChat.style.pointerEvents = 'auto';
                
                console.log('Force-positioned project chat');
            }
            
            // Check for input fields and reinitialize handlers
            const mainChatInput = document.getElementById('chat-input');
            const projectChatInput = document.getElementById('project-chat-input');
            
            console.log('Chat inputs found:');
            console.log('- Main Chat Input:', !!mainChatInput);
            console.log('- Project Chat Input:', !!projectChatInput);
            
            // Reinitialize event handlers
            if (typeof window.initializeMinervaChats === 'function') {
                console.log('Reinitializing chat handlers...');
                window.initializeMinervaChats();
            } else {
                console.error('Could not find initializeMinervaChats function');
            }
            
            // Add emergency handlers if necessary
            if (projectChatInput) {
                projectChatInput.addEventListener('keydown', function(e) {
                    console.log('Emergency handler: Key pressed in project chat:', e.key);
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const projectSendButton = document.getElementById('project-send-button');
                        if (projectSendButton) {
                            console.log('Emergency handler: Clicking project send button');
                            projectSendButton.click();
                        }
                    }
                });
            }
            
            if (mainChatInput) {
                mainChatInput.addEventListener('keydown', function(e) {
                    console.log('Emergency handler: Key pressed in main chat:', e.key);
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const mainSendButton = document.getElementById('send-button');
                        if (mainSendButton) {
                            console.log('Emergency handler: Clicking main send button');
                            mainSendButton.click();
                        }
                    }
                });
            }
        }, 1000); // Wait 1 second for any async loading
    });
})();
