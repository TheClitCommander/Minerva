// Socket Initializer
console.log('Socket Initializer loaded');

// Initialize socket connection when available
window.initSocket = function() {
    if (typeof io !== 'undefined') {
        console.log('Initializing Socket.IO connection...');
        return io();
    } else {
        console.warn('Socket.IO not available');
        return null;
    }
}; 