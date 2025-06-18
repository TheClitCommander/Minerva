/**
 * Minerva UI Test Helper
 * Provides tools to test and debug UI components and API connectivity
 * Implements Master Ruleset principles for testing and validation
 */

(function() {
    'use strict';
    
    // Configuration
    const config = {
        apiEndpoints: [
            { name: 'Think Tank API', url: '/api/think-tank', method: 'GET' },
            { name: 'Memory API', url: '/api/memory', method: 'GET' },
            { name: 'Projects API', url: '/api/projects', method: 'GET' }
        ],
        uiElements: [
            { name: 'Orbital UI Container', selector: '#minerva-orbital-ui' },
            { name: 'Orb Container', selector: '#orb-container' },
            { name: '3D Container', selector: '#minerva-3d-container' },
            { name: 'Orbital Container', selector: '#orbital-container' },
            { name: 'Navigation Ring', selector: '#nav-ring' },
            { name: 'Orb Interface', selector: '#orb-interface' }
        ],
        webSocketEndpoint: (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
                           window.location.host + '/socket.io/'
    };
    
    // Create test panel
    function createTestPanel() {
        // Check if panel already exists
        if (document.getElementById('minerva-test-panel')) {
            return;
        }
        
        // Create panel container
        const panel = document.createElement('div');
        panel.id = 'minerva-test-panel';
        panel.style.cssText = `
            position: fixed;
            bottom: 50px;
            right: 50px;
            width: 350px;
            max-height: 500px;
            overflow-y: auto;
            background: rgba(15, 25, 40, 0.9);
            border: 1px solid #9c5ddb;
            border-radius: 8px;
            color: white;
            font-family: monospace;
            font-size: 12px;
            padding: 15px;
            z-index: 9999;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
            display: none;
        `;
        
        // Create header
        const header = document.createElement('div');
        header.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #9c5ddb;">Minerva UI Test Panel</h3>
                <button id="close-test-panel" style="background: none; border: none; color: white; cursor: pointer;">×</button>
            </div>
            <p>Test UI components and API connections</p>
            <button id="run-all-tests" style="background: #9c5ddb; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-bottom: 10px;">Run All Tests</button>
        `;
        panel.appendChild(header);
        
        // Create sections
        const uiTestSection = createSection('UI Elements', runUITests);
        const apiTestSection = createSection('API Endpoints', runAPITests);
        const wsTestSection = createSection('WebSocket Connection', runWebSocketTest);
        
        panel.appendChild(uiTestSection);
        panel.appendChild(apiTestSection);
        panel.appendChild(wsTestSection);
        
        // Add to body
        document.body.appendChild(panel);
        
        // Add event listeners
        document.getElementById('close-test-panel').addEventListener('click', () => {
            panel.style.display = 'none';
        });
        
        document.getElementById('run-all-tests').addEventListener('click', runAllTests);
        
        // Show panel
        panel.style.display = 'block';
        
        console.log('Minerva Test Panel initialized');
    }
    
    // Create a test section
    function createSection(title, testFunction) {
        const section = document.createElement('div');
        section.className = 'test-section';
        section.style.cssText = `
            margin-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 10px;
        `;
        
        const titleEl = document.createElement('h4');
        titleEl.textContent = title;
        titleEl.style.cssText = `
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
        `;
        
        const button = document.createElement('button');
        button.textContent = 'Test';
        button.style.cssText = `
            background: #334155;
            border: none;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
        `;
        button.addEventListener('click', testFunction);
        
        titleEl.appendChild(button);
        section.appendChild(titleEl);
        
        const resultsList = document.createElement('ul');
        resultsList.className = `${title.toLowerCase().replace(/\s+/g, '-')}-results`;
        resultsList.style.cssText = `
            list-style: none;
            padding: 0;
            margin: 0;
        `;
        section.appendChild(resultsList);
        
        return section;
    }
    
    // Run all tests
    function runAllTests() {
        runUITests();
        runAPITests();
        runWebSocketTest();
    }
    
    // Run UI element tests
    function runUITests() {
        const resultsList = document.querySelector('.ui-elements-results');
        resultsList.innerHTML = '';
        
        config.uiElements.forEach(element => {
            const el = document.querySelector(element.selector);
            const result = document.createElement('li');
            result.style.cssText = `
                margin-bottom: 5px;
                padding: 5px;
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
            `;
            
            const status = el ? 'PASS' : 'FAIL';
            result.className = status === 'PASS' ? 'test-pass' : 'test-fail';
            result.style.backgroundColor = status === 'PASS' ? 'rgba(0, 128, 0, 0.2)' : 'rgba(128, 0, 0, 0.2)';
            
            result.innerHTML = `
                <span>${element.name}</span>
                <span style="color: ${status === 'PASS' ? '#4ade80' : '#f87171'}">${status}</span>
            `;
            
            resultsList.appendChild(result);
        });
    }
    
    // Run API endpoint tests
    function runAPITests() {
        const resultsList = document.querySelector('.api-endpoints-results');
        resultsList.innerHTML = '';
        
        config.apiEndpoints.forEach(endpoint => {
            // Create result item with loading state
            const result = document.createElement('li');
            result.style.cssText = `
                margin-bottom: 5px;
                padding: 5px;
                border-radius: 4px;
                display: flex;
                justify-content: space-between;
                background-color: rgba(128, 128, 0, 0.2);
            `;
            result.innerHTML = `
                <span>${endpoint.name}</span>
                <span style="color: #facc15">TESTING...</span>
            `;
            resultsList.appendChild(result);
            
            // Test endpoint
            fetch(endpoint.url, { method: endpoint.method })
                .then(response => {
                    const status = response.ok ? 'PASS' : 'FAIL';
                    updateTestResult(result, status, response.status);
                })
                .catch(error => {
                    updateTestResult(result, 'FAIL', error.message);
                });
        });
    }
    
    // Run WebSocket test
    function runWebSocketTest() {
        const resultsList = document.querySelector('.websocket-connection-results');
        resultsList.innerHTML = '';
        
        // Create result item with loading state
        const result = document.createElement('li');
        result.style.cssText = `
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            background-color: rgba(128, 128, 0, 0.2);
        `;
        result.innerHTML = `
            <span>WebSocket Connection</span>
            <span style="color: #facc15">CONNECTING...</span>
        `;
        resultsList.appendChild(result);
        
        // Test WebSocket connection
        let wsSupported = true;
        
        try {
            // Check if WebSocket is supported
            if (typeof WebSocket === 'undefined') {
                wsSupported = false;
                throw new Error('WebSocket not supported');
            }
            
            // Connect to WebSocket endpoint
            const socket = new WebSocket(config.webSocketEndpoint);
            
            // Set timeout for connection attempt
            const timeout = setTimeout(() => {
                updateTestResult(result, 'FAIL', 'Connection timeout');
                socket.close();
            }, 5000);
            
            // Handle connection open
            socket.onopen = () => {
                clearTimeout(timeout);
                updateTestResult(result, 'PASS', 'Connected');
                socket.close();
            };
            
            // Handle connection error
            socket.onerror = (error) => {
                clearTimeout(timeout);
                updateTestResult(result, 'FAIL', 'Connection error');
            };
        } catch (error) {
            if (!wsSupported) {
                updateTestResult(result, 'FAIL', 'WebSocket not supported');
            } else {
                updateTestResult(result, 'FAIL', error.message);
            }
        }
    }
    
    // Update test result
    function updateTestResult(resultElement, status, message) {
        resultElement.className = status === 'PASS' ? 'test-pass' : 'test-fail';
        resultElement.style.backgroundColor = status === 'PASS' ? 'rgba(0, 128, 0, 0.2)' : 'rgba(128, 0, 0, 0.2)';
        
        resultElement.innerHTML = `
            <span>${resultElement.querySelector('span').textContent}</span>
            <span style="color: ${status === 'PASS' ? '#4ade80' : '#f87171'}">
                ${status} ${message ? `(${message})` : ''}
            </span>
        `;
    }
    
    // Initialize test helper
    function init() {
        // Create global function to show test panel
        window.showMinervaTestPanel = createTestPanel;
        
        // Add keyboard shortcut (Alt+T)
        document.addEventListener('keydown', (event) => {
            if (event.altKey && event.key === 't') {
                const panel = document.getElementById('minerva-test-panel');
                
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
                } else {
                    createTestPanel();
                }
            }
        });
        
        console.log('Minerva UI Test Helper initialized. Press Alt+T to show test panel.');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
