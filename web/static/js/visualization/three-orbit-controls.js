/**
 * OrbitControls for Three.js
 * Simplified for Minerva's needs
 */

// This is the most important part - ensure we handle the dependency correctly
if (typeof THREE === "undefined") {
    console.error("THREE.js is not loaded before OrbitControls!");
} else {
    console.log("Initializing OrbitControls for THREE.js...");
    
    // Simple OrbitControls implementation
    THREE.OrbitControls = function(camera, domElement) {
        this.object = camera;
        this.domElement = domElement || document;
        
        // API
        this.enabled = true;
        this.target = new THREE.Vector3();
        this.enableZoom = true;
        this.zoomSpeed = 1.0;
        this.enableRotate = true;
        this.rotateSpeed = 1.0;
        this.autoRotate = true;
        this.autoRotateSpeed = 0.5;
        
        // Private properties
        const scope = this;
        const offset = new THREE.Vector3();
        
        // Main update function
        this.update = function() {
            const position = this.object.position;
            offset.copy(position).sub(this.target);
            
            // Auto-rotation
            if (this.autoRotate && this.enabled) {
                const angle = (2 * Math.PI / 60 / 60) * scope.autoRotateSpeed;
                const x = offset.x;
                const z = offset.z;
                offset.x = x * Math.cos(angle) - z * Math.sin(angle);
                offset.z = z * Math.cos(angle) + x * Math.sin(angle);
            }
            
            position.copy(this.target).add(offset);
            this.object.lookAt(this.target);
            
            return true;
        };
        
        this.dispose = function() { return this; };
        this.reset = function() {
            this.target.set(0, 0, 0);
            this.object.position.set(0, 0, 5);
            this.update();
            return this;
        };
        
        // Initialize
        this.update();
        return this;
    };
    
    // For compatibility with different import patterns
    window.OrbitControls = THREE.OrbitControls;
    
    console.log('✅ OrbitControls successfully attached to THREE namespace');
}

