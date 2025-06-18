// Minerva Orb Fix
console.log('Minerva Orb Fix loaded');

// Basic orb functionality
window.minervaOrb = {
    initialized: false,
    
    init: function() {
        if (this.initialized) return;
        console.log('Initializing Minerva Orb...');
        this.initialized = true;
    }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.minervaOrb.init());
} else {
    window.minervaOrb.init();
} 