/**
 * Minerva 3D UI Loader
 * Simplified version that uses native Three.js instead of React components
 * This ensures better compatibility with the integrated chat system
 */

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing simplified Minerva 3D UI...');
    
    // Check if container exists
    const container = document.getElementById('minerva-orbital-ui');
    if (!container) {
        console.error('Minerva 3D UI container not found');
        return;
    }
    
    // Initialize with a simple spinning globe if THREE is available
    if (typeof THREE !== 'undefined') {
        console.log('THREE is available, initializing 3D scene');
        initializeSimpleScene(container);
    } else {
        console.error('THREE is not available, showing fallback UI');
        showFallbackUI(container);
    }
    
    // Helper Functions
    
    // Initialize a simple Three.js scene with a spinning globe
    function initializeSimpleScene(container) {
        try {
            // Create scene, camera, renderer
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setClearColor(0x000000, 0);
            container.appendChild(renderer.domElement);
            
            // Create a simple sphere for Minerva orb
            const geometry = new THREE.SphereGeometry(2, 32, 32);
            const material = new THREE.MeshBasicMaterial({
                color: 0x4a6bdf,
                wireframe: true,
                transparent: true,
                opacity: 0.7
            });
            
            const globe = new THREE.Mesh(geometry, material);
            scene.add(globe);
            
            // Add stars in background
            addStars(scene, 100);
            
            // Position camera
            camera.position.z = 5;
            
            // Simple controls without OrbitControls dependency
            let rotationSpeed = 0.001;
            
            // Add event listeners for interaction
            container.addEventListener('mousedown', () => {
                rotationSpeed = 0; // Stop rotation on click
            });
            
            container.addEventListener('mouseup', () => {
                rotationSpeed = 0.001; // Resume rotation
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                
                // Rotate the globe
                globe.rotation.y += rotationSpeed;
                
                renderer.render(scene, camera);
            }
            
            // Handle window resize
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });
            
            // Start animation
            animate();
            console.log('3D scene initialized successfully');
            
            // Connect to chat interface
            connectToChat(globe);
        } catch (error) {
            console.error('Error initializing 3D scene:', error);
            showFallbackUI(container);
        }
    }
    
    // Add stars to the scene
    function addStars(scene, count) {
        const starGeometry = new THREE.BufferGeometry();
        const starMaterial = new THREE.PointsMaterial({
            color: 0xFFFFFF,
            size: 0.1
        });
        
        const starVertices = [];
        for (let i = 0; i < count; i++) {
            const x = (Math.random() - 0.5) * 50;
            const y = (Math.random() - 0.5) * 50;
            const z = (Math.random() - 0.5) * 50;
            starVertices.push(x, y, z);
        }
        
        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
        const stars = new THREE.Points(starGeometry, starMaterial);
        scene.add(stars);
    }
    
    // Connect globe visuals to chat interface
    function connectToChat(globe) {
        // Pulse effect when new messages come in
        document.addEventListener('minerva-new-message', function() {
            pulseEffect(globe);
        });
    }
    
    // Visual pulse effect
    function pulseEffect(object) {
        let scale = 1.0;
        let growing = true;
        let pulseCount = 0;
        
        const pulse = setInterval(() => {
            if (growing) {
                scale += 0.01;
                if (scale >= 1.2) growing = false;
            } else {
                scale -= 0.01;
                if (scale <= 1.0) {
                    growing = true;
                    pulseCount++;
                }
            }
            
            object.scale.set(scale, scale, scale);
            
            if (pulseCount >= 3) {
                clearInterval(pulse);
                object.scale.set(1, 1, 1);
            }
        }, 20);
    }
    
    // Fallback UI if 3D fails
    function showFallbackUI(container) {
        container.innerHTML = `
            <div style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.8); border-radius: 50%; padding: 20px; box-sizing: border-box;">
                <div style="font-size: 24px; color: #4a6bdf; margin-bottom: 10px;">Minerva Think Tank</div>
                <div style="font-size: 14px; color: #ffffff; text-align: center;">3D visualization unavailable.<br>Chat functionality works normally.</div>
            </div>
        `;
    }
});
