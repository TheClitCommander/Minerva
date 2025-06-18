/**
 * Minerva Orbital UI Initialization
 * This file handles the initialization and mounting of the 3D React components for Minerva's orbital interface
 */

// Initialize the 3D UI when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if the container exists
    const orbitalContainer = document.getElementById('minerva-orbital-ui');
    if (!orbitalContainer) {
        console.error('Minerva Orbital UI container not found in the DOM');
        return;
    }

    // Log that we're attempting to mount the UI
    console.log('Initializing Minerva Orbital UI...');
    
    try {
        // Create sample project data for the orbital UI
        const sampleProjects = [
            {
                id: 'project-1',
                name: 'General Chat',
                color: '#4a6bdf',
                position: [0, 0, -3],
                agents: [
                    { id: 'agent-1', name: 'GPT-4', color: '#19c37d', score: 0.92 },
                    { id: 'agent-2', name: 'Claude-3', color: '#9c5ddb', score: 0.89 },
                    { id: 'agent-3', name: 'Gemini', color: '#4285f4', score: 0.85 }
                ]
            },
            {
                id: 'project-2',
                name: 'Code Project',
                color: '#ff7b5a',
                position: [-4, 0, 0],
                agents: [
                    { id: 'agent-4', name: 'GPT-4', color: '#19c37d', score: 0.95 },
                    { id: 'agent-5', name: 'Claude-3', color: '#9c5ddb', score: 0.83 },
                    { id: 'agent-6', name: 'Llama-3', color: '#e37400', score: 0.79 }
                ]
            },
            {
                id: 'project-3',
                name: 'Research',
                color: '#20c997',
                position: [4, 0, 0],
                agents: [
                    { id: 'agent-7', name: 'Claude-3', color: '#9c5ddb', score: 0.94 },
                    { id: 'agent-8', name: 'GPT-4', color: '#19c37d', score: 0.91 },
                    { id: 'agent-9', name: 'Gemini', color: '#4285f4', score: 0.88 }
                ]
            }
        ];

        // Initialize React and mount the component
        // We're creating a script element to load React and ReactDOM
        // This is necessary because we're initializing React in a vanilla JS environment
        const loadScript = (src) => {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = src;
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        };

        // Load React, ReactDOM, and other required libraries if not already loaded
        const loadDependencies = async () => {
            // Check if React is already loaded
            if (typeof React === 'undefined') {
                await loadScript('https://unpkg.com/react@18/umd/react.production.min.js');
            }
            
            // Check if ReactDOM is already loaded
            if (typeof ReactDOM === 'undefined') {
                await loadScript('https://unpkg.com/react-dom@18/umd/react-dom.production.min.js');
            }
            
            // Load React Three Fiber and Three.js if needed
            if (typeof THREE === 'undefined') {
                await loadScript('https://unpkg.com/three@0.149.0/build/three.min.js');
            }
            
            // Load Babel for JSX support
            if (typeof Babel === 'undefined') {
                await loadScript('https://unpkg.com/@babel/standalone/babel.min.js');
            }
            
            // Load React Three Fiber
            await loadScript('https://unpkg.com/@react-three/fiber@8.11.5/dist/react-three-fiber.min.js');
            
            // Load React Three Drei
            await loadScript('https://unpkg.com/@react-three/drei@9.56.28/index.min.js');
        };

        // Function to load our custom components
        const loadMinervaComponents = async () => {
            // Load our MinervaUI component
            const minervaUIModule = await import('/static/js/orb-ui/react-three/MinervaUI.jsx');
            const MinervaUI = minervaUIModule.default;
            
            // Create a root element for React
            const rootElement = document.createElement('div');
            rootElement.style.width = '100%';
            rootElement.style.height = '100%';
            orbitalContainer.appendChild(rootElement);
            
            // Render the MinervaUI component
            const root = ReactDOM.createRoot(rootElement);
            root.render(
                React.createElement(MinervaUI, { projectOrbs: sampleProjects })
            );
            
            console.log('Minerva Orbital UI mounted successfully');
        };

        // Execute loading sequence
        loadDependencies()
            .then(() => {
                console.log('Dependencies loaded successfully');
                return loadMinervaComponents();
            })
            .catch(error => {
                console.error('Error initializing Minerva Orbital UI:', error);
                orbitalContainer.innerHTML = `
                    <div class="alert alert-danger m-3">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading 3D interface: ${error.message}
                    </div>
                `;
            });

        // Handle the toggle button for expanding/collapsing the 3D view
        const toggleButton = document.getElementById('toggle-orbital-view-btn');
        if (toggleButton) {
            toggleButton.addEventListener('click', function() {
                if (orbitalContainer.style.height === '400px') {
                    orbitalContainer.style.height = '600px';
                    this.innerHTML = '<i class="fas fa-compress-alt"></i> Compact View';
                } else {
                    orbitalContainer.style.height = '400px';
                    this.innerHTML = '<i class="fas fa-expand-alt"></i> Toggle Full View';
                }
            });
        }

    } catch (error) {
        console.error('Critical error initializing Minerva Orbital UI:', error);
        orbitalContainer.innerHTML = `
            <div class="alert alert-danger m-3">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to initialize 3D interface: ${error.message}
            </div>
        `;
    }
});
