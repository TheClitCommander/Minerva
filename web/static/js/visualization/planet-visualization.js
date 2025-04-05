/**
 * Minerva Planet Visualization
 * Creates an interactive 3D planetary visualization for the Minerva Think Tank interface
 * This connects with the AI functionality while maintaining the immersive orbital UI
 */

// Initialize the planetary visualization
const initializeVisualization = function() {
    console.log('Initializing Minerva Planet Visualization...');
    
    // We rely on THREE and OrbitControls being loaded in the HTML head
    // through <script> tags with the correct order
    
    // Check if THREE is already available (loaded in the head)
    if (typeof THREE !== 'undefined') {
        console.log('THREE is available:', typeof THREE);
        console.log('OrbitControls available:', typeof THREE.OrbitControls);
        
        // A short delay to make sure everything is properly initialized
        setTimeout(() => {
            initPlanetVisualization();
        }, 100);
    } else {
        console.error('THREE is not defined! Check script loading order in HTML.');
        console.error('THREE status:', typeof THREE);
        console.error('window.THREE status:', typeof window.THREE);
    }
};

// Execute initialization when the document is ready
document.addEventListener('DOMContentLoaded', initializeVisualization);

// Initialize the planetary visualization with Three.js
function initPlanetVisualization() {
    console.log('Starting planet visualization initialization');
    
    // Make sure Three.js is available
    if (typeof THREE === 'undefined') {
        console.error('Three.js is not loaded, cannot initialize planet visualization');
        return;
    }
    
    const container = document.getElementById('orbital-planet-container');
    if (!container) {
        console.error('Planet visualization container not found');
        return;
    }
    
    console.log('Container found, creating scene');
    
    // Create scene, camera, and renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
        75, window.innerWidth / window.innerHeight, 0.1, 1000
    );
    
    // Create WebGL renderer with transparent background
    const renderer = new THREE.WebGLRenderer({ 
        antialias: true,
        alpha: true
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    
    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    scene.add(ambientLight);
    
    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 3, 5);
    scene.add(directionalLight);
    
    // Create a loader for textures
    const textureLoader = new THREE.TextureLoader();
    
    // Create planet
    const planetGeometry = new THREE.SphereGeometry(2, 64, 64);
    
    // Use a space/planet texture or a gradient
    const planetMaterial = new THREE.MeshPhongMaterial({
        color: 0x4a6bdf,
        emissive: 0x172554,
        shininess: 25,
        transparent: true,
        opacity: 0.9
    });
    
    const planet = new THREE.Mesh(planetGeometry, planetMaterial);
    scene.add(planet);
    
    // Create atmosphere
    const atmosphereGeometry = new THREE.SphereGeometry(2.15, 64, 64);
    const atmosphereMaterial = new THREE.MeshPhongMaterial({
        color: 0x6366f1,
        emissive: 0x818cf8,
        shininess: 10,
        transparent: true,
        opacity: 0.3,
        side: THREE.BackSide
    });
    
    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphere);
    
    // Create orbiting particles
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 1000;
    
    const posArray = new Float32Array(particlesCount * 3);
    const sizeArray = new Float32Array(particlesCount);
    
    for (let i = 0; i < particlesCount * 3; i += 3) {
        // Create a ring of particles
        const angle = Math.random() * Math.PI * 2;
        const radius = 2.5 + Math.random() * 0.5;
        
        posArray[i] = Math.cos(angle) * radius;
        posArray[i+1] = (Math.random() - 0.5) * 0.5; // slightly above/below center
        posArray[i+2] = Math.sin(angle) * radius;
        
        sizeArray[i/3] = Math.random() * 0.05 + 0.01;
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeometry.setAttribute('size', new THREE.BufferAttribute(sizeArray, 1));
    
    const particlesMaterial = new THREE.PointsMaterial({
        size: 0.05,
        color: 0xa5b4fc,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending
    });
    
    const particles = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particles);
    
    // Position camera
    camera.position.z = 6;
    
    // Set up orbit controls
    console.log('Initializing orbit controls...');
    console.log('THREE.OrbitControls check:', typeof THREE.OrbitControls);
    
    let controls;
    try {
        // Position camera
        camera.position.set(0, 0, 6);
        camera.lookAt(0, 0, 0);
        
        // Check if THREE.OrbitControls is available
        if (typeof THREE.OrbitControls === 'function') {
            console.log('✅ OrbitControls constructor available');
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            console.log('OrbitControls instance created successfully');
            
            // Configure controls for smooth automatic rotation
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.enableZoom = false;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.5;
        } else {
            throw new Error('THREE.OrbitControls is not a function');
        }
    } catch (err) {
        console.error('Error creating OrbitControls:', err.message);
        console.log('Falling back to manual camera animation');
        
        // Fallback to manual rotation if OrbitControls fails
        controls = {
            update: function() {
                const time = Date.now() * 0.0005;
                camera.position.x = Math.cos(time) * 7;
                camera.position.z = Math.sin(time) * 7;
                camera.lookAt(scene.position);
                return true;
            }
        };
    }
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Rotate planet slowly
        planet.rotation.y += 0.001;
        atmosphere.rotation.y += 0.0005;
        
        // Rotate particles
        particles.rotation.y += 0.0008;
        
        // Update controls if available
        if (controls) controls.update();
        
        renderer.render(scene, camera);
    }
    
    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    // Start animation
    animate();
    
    console.log('Planet visualization initialized successfully');
}

// Simple helper functions for debugging
window.checkThreeJsStatus = function() {
    console.log('Three.js status:', typeof THREE !== 'undefined' ? 'Loaded' : 'Not loaded');
    if (typeof THREE !== 'undefined') {
        console.log('Three.js version:', THREE.REVISION);
    }
    
    console.log('OrbitControls status:', typeof THREE !== 'undefined' && typeof THREE.OrbitControls !== 'undefined' ? 'Loaded' : 'Not loaded');
};

// Add a global error handler to catch script loading issues
window.addEventListener('error', function(event) {
    console.error('Global error caught:', event.message, event.filename, event.lineno);
});

// Utility function to load scripts dynamically
function loadScripts(urls) {
    console.log(`Loading ${urls.length} script(s) sequentially...`);
    return new Promise((resolve, reject) => {
        const loadedScripts = [];
        
        function loadNextScript(index) {
            if (index >= urls.length) {
                console.log('All scripts loaded successfully');
                resolve(loadedScripts);
                return;
            }
            
            const url = urls[index];
            console.log(`Loading script (${index+1}/${urls.length}): ${url}`);
            
            const script = document.createElement('script');
            script.src = url;
            script.async = false;
            
            script.onload = () => {
                console.log(`Script loaded successfully: ${url}`);
                loadedScripts.push(url);
                // Check if THREE.OrbitControls is available after each script
                if (typeof THREE !== 'undefined') {
                    console.log('THREE.OrbitControls status:', 
                        typeof THREE.OrbitControls !== 'undefined' ? 'Available' : 'Not available');
                }
                // Give a small delay to ensure script is fully processed
                setTimeout(() => loadNextScript(index + 1), 100);
            };
            
            script.onerror = (error) => {
                console.error(`Failed to load script: ${url}`, error);
                reject(new Error(`Failed to load script: ${url}`));
            };
            
            document.head.appendChild(script);
        }
        
        loadNextScript(0);
    });
}
