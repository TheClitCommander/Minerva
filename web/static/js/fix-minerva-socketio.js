// Socket.IO Connection Fixer
(function() {
    console.log('🔌 Minerva Socket.IO Fixer loaded');
    
    // Wait for the DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const statusDiv = document.createElement('div');
        statusDiv.id = 'socketio-status';
        statusDiv.style.position = 'fixed';
        statusDiv.style.top = '10px';
        statusDiv.style.right = '10px';
        statusDiv.style.padding = '5px 10px';
        statusDiv.style.borderRadius = '5px';
        statusDiv.style.background = 'rgba(0,0,0,0.7)';
        statusDiv.style.color = 'white';
        statusDiv.style.fontSize = '12px';
        statusDiv.style.zIndex = '9999';
        statusDiv.innerHTML = '<span style="color:orange">●</span> Connecting...';
        document.body.appendChild(statusDiv);
        
        // Initialize Socket.IO with compatibility options
        try {
            console.log('🔌 Initializing Socket.IO connection with compatibility');
            window.minervaSocket = io({
                path: '/socket.io',
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000,
                timeout: 20000
            });
            
            // Set up event handlers
            window.minervaSocket.on('connect', function() {
                console.log('✅ Socket.IO connected successfully');
                statusDiv.innerHTML = '<span style="color:green">●</span> Socket.IO Connected';
                statusDiv.style.opacity = '1';
                
                // Fade out after 5 seconds
                setTimeout(function() {
                    statusDiv.style.transition = 'opacity 1s';
                    statusDiv.style.opacity = '0.2';
                }, 5000);
                
                // Add hover effect to show/hide
                statusDiv.addEventListener('mouseenter', function() {
                    statusDiv.style.opacity = '1';
                });
                statusDiv.addEventListener('mouseleave', function() {
                    statusDiv.style.opacity = '0.2';
                });
            });
            
            window.minervaSocket.on('connect_error', function(error) {
                console.error('❌ Socket.IO connection error:', error);
                statusDiv.innerHTML = '<span style="color:red">●</span> Socket.IO Error';
            });
            
            // Add debug hooks
            window.minervaSocket.on('debug', function(data) {
                console.log('🔍 Socket.IO Debug:', data);
                
                // Display temporary message
                const msgDiv = document.createElement('div');
                msgDiv.style.position = 'fixed';
                msgDiv.style.top = '50px';
                msgDiv.style.left = '50%';
                msgDiv.style.transform = 'translateX(-50%)';
                msgDiv.style.padding = '10px 20px';
                msgDiv.style.borderRadius = '5px';
                msgDiv.style.background = 'rgba(0,0,0,0.8)';
                msgDiv.style.color = 'white';
                msgDiv.style.zIndex = '9998';
                msgDiv.style.maxWidth = '80%';
                msgDiv.innerHTML = `<em>System: ${data.message || data}</em>`;
                document.body.appendChild(msgDiv);
                
                // Remove after 5 seconds
                setTimeout(function() {
                    document.body.removeChild(msgDiv);
                }, 5000);
            });
        } catch (e) {
            console.error('❌ Error initializing Socket.IO:', e);
            statusDiv.innerHTML = '<span style="color:red">●</span> Socket.IO Not Found';
            
            // Try again after a short delay
            setTimeout(function() {
                if (!window.io) {
                    console.warn('⚠️ Socket.IO library not found, attempting to load fallback');
                    
                    // Try to load fallback version
                    const script = document.createElement('script');
                    script.src = '/compatible-socket.io.js';
                    script.onload = function() {
                        console.log('✅ Fallback Socket.IO loaded successfully');
                        location.reload();
                    };
                    script.onerror = function() {
                        console.error('❌ Failed to load fallback Socket.IO');
                        statusDiv.innerHTML = '<span style="color:red">●</span> Socket.IO Failed';
                    };
                    document.head.appendChild(script);
                }
            }, 2000);
        }
    });
})(); 