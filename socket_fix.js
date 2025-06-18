/**
 * Socket.IO Compatibility Fix for Minerva Chat
 * 
 * This script fixes compatibility issues with older Socket.IO clients
 * by replacing them with a CDN-hosted version that works with the server.
 * 
 * Add to your HTML: <script src="/socket_fix.js"></script>
 */

(function() {
    console.log("Checking for Socket.IO compatibility...");

    // Check if an incompatible Socket.IO is loaded
    if (typeof io === 'undefined' || !io.version || io.version.startsWith('2.')) {
        console.log("Incompatible Socket.IO detected. Loading v4.7.2 from CDN...");
        
        // Remove existing Socket.IO script if present
        const existingScripts = document.querySelectorAll('script[src*="socket.io"]');
        existingScripts.forEach(script => script.remove());
        
        // Create and inject the compatible version
        const script = document.createElement('script');
        script.src = "https://cdn.socket.io/4.7.2/socket.io.min.js";
        script.integrity = "sha384-mZLF4UVrpi/QTWPA7BjNPEnkIfRFn4ZEO42xFXOCQrFuFJHBuKAsEME7Z8xeXVbV";
        script.crossOrigin = "anonymous";
        script.onload = function() {
            console.log("Socket.IO v4.7.2 loaded successfully.");
            
            // Dispatch a custom event to notify the application
            document.dispatchEvent(new CustomEvent('socketio-compatible-loaded'));
        };
        
        script.onerror = function() {
            console.error("Failed to load Socket.IO from CDN. Chat functionality may be limited.");
        };
        
        document.head.appendChild(script);
    } else if (io.version) {
        console.log(`Using Socket.IO v${io.version} - compatibility check passed`);
    }
    
    // Helper function to connect to Minerva chat server
    window.createMinervaSocket = function(url) {
        // Wait for Socket.IO to be properly loaded
        if (typeof io === 'undefined') {
            console.log("Socket.IO not available yet, waiting...");
            setTimeout(() => window.createMinervaSocket(url), 100);
            return null;
        }
        
        console.log(`Creating compatible Socket.IO connection to ${url || window.location.origin}`);
        const socket = io(url || window.location.origin, {
            transports: ['websocket', 'polling'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            timeout: 20000
        });
        
        // Add compatibility layer for various event names
        const originalEmit = socket.emit;
        socket.emit = function(event, data) {
            console.log(`Emitting ${event}:`, data);
            return originalEmit.apply(this, arguments);
        };
        
        // Setup basic handlers
        socket.on('connect', () => console.log('Connected to Minerva server'));
        socket.on('connect_error', (err) => console.error('Connection error:', err));
        socket.on('disconnect', (reason) => console.log('Disconnected:', reason));
        
        return socket;
    };
})(); 