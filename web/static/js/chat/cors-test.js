/**
 * Minerva CORS Test Script
 * This script attempts to diagnose CORS issues with the Think Tank API
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log("🔍 Running CORS Test for Minerva API");
    
    // Create test container - moved to top right with smaller footprint
    const testContainer = document.createElement('div');
    testContainer.id = 'cors-test-container';
    testContainer.style.position = 'fixed';
    testContainer.style.top = '20px';
    testContainer.style.right = '20px'; // Changed from left to right
    testContainer.style.width = '250px'; // Reduced width
    testContainer.style.padding = '10px';
    testContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    testContainer.style.color = 'white';
    testContainer.style.borderRadius = '8px';
    testContainer.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
    testContainer.style.zIndex = '1000'; // Lower z-index to not interfere with chat
    testContainer.style.fontFamily = 'Arial, sans-serif';
    testContainer.style.fontSize = '12px'; // Smaller font
    
    // Add minimize/close buttons
    testContainer.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <h4 style="margin: 0; color: #fff; font-size: 12px;">API CORS Test</h4>
            <div>
                <button id="cors-minimize-btn" style="background: none; border: none; color: white; cursor: pointer; font-size: 14px; padding: 0 5px;">−</button>
                <button id="cors-close-btn" style="background: none; border: none; color: white; cursor: pointer; font-size: 14px; padding: 0 5px;">×</button>
            </div>
        </div>
        <div id="cors-content">
            <div>API: <span id="cors-status">Checking...</span></div>
            <div style="margin-top: 5px;">
                <input type="text" id="port-input" placeholder="Port (7070)" value="7070"
                       style="padding: 3px; width: 80px; margin-right: 5px; font-size: 11px;">
                <button id="test-cors-btn" style="padding: 3px 6px; background: #4a4a9e; color: white; border: none; border-radius: 4px; font-size: 11px;">
                    Test
                </button>
            </div>
            <div id="test-results" style="margin-top: 5px; font-size: 10px; color: #ddd;"></div>
        </div>
    `;
    
    document.body.appendChild(testContainer);
    
    // Perform CORS test
    function testCORS(port = '8090') {
        const resultsEl = document.getElementById('test-results');
        const statusEl = document.getElementById('cors-status');
        
        statusEl.textContent = 'Testing...';
        statusEl.style.color = '#ffa500';
        
        resultsEl.innerHTML = `<div>Testing port ${port}...</div>`;
        
        // Try different request methods
        const apiUrl = `http://localhost:${port}/api/think-tank`;
        
        // Method 1: Simple HEAD with no-cors
        fetch(apiUrl, {
            method: 'HEAD',
            mode: 'no-cors'
        })
        .then(() => {
            resultsEl.innerHTML += `<div style="color:#8f8">✓ Server responds to no-cors HEAD</div>`;
            
            // Method 2: Try a simple POST with minimum payload
            return fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: 'ping' })
            });
        })
        .then(response => {
            if (response.ok) {
                statusEl.textContent = '✅ API Working';
                statusEl.style.color = '#4caf50';
                resultsEl.innerHTML += `<div style="color:#4f4">✓ API accepts POST request</div>`;
                
                // Save the working port to localStorage
                localStorage.setItem('minerva_api_port', port);
                localStorage.setItem('minerva_api_url', apiUrl);
                
                // Update main API URL if possible
                if (window.THINK_TANK_API_URL) {
                    window.THINK_TANK_API_URL = apiUrl;
                }
                
                return response.json();
            } else {
                throw new Error(`Status: ${response.status}`);
            }
        })
        .then(data => {
            resultsEl.innerHTML += `<div style="color:#4f4">✓ API returned valid JSON</div>`;
            console.log('API response:', data);
        })
        .catch(err => {
            // Method 3: Try with OPTIONS request to detect CORS support
            resultsEl.innerHTML += `<div style="color:#f88">✗ Standard POST failed: ${err.message}</div>`;
            resultsEl.innerHTML += `<div>Trying CORS preflight test...</div>`;
            
            // Create specialized CORS request
            let jsonBody = JSON.stringify({
                message: "CORS test",
                type: "system_check",
                conversation_id: localStorage.getItem('minerva_conversation_id') || 'test-session'
            });
            
            const xhr = new XMLHttpRequest();
            xhr.open('POST', apiUrl);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.withCredentials = false;
            
            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    statusEl.textContent = '✅ API Working via XHR';
                    statusEl.style.color = '#4caf50';
                    resultsEl.innerHTML += `<div style="color:#4f4">✓ XHR request succeeded</div>`;
                    
                    // Save the working port to localStorage
                    localStorage.setItem('minerva_api_port', port);
                    localStorage.setItem('minerva_api_url', apiUrl);
                    localStorage.setItem('minerva_api_method', 'xhr');
                    
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resultsEl.innerHTML += `<div style="color:#4f4">✓ API returned valid JSON via XHR</div>`;
                        console.log('XHR API response:', data);
                    } catch (e) {
                        resultsEl.innerHTML += `<div style="color:#f88">✗ XHR response not valid JSON: ${e.message}</div>`;
                    }
                } else {
                    resultsEl.innerHTML += `<div style="color:#f88">✗ XHR failed with status ${xhr.status}</div>`;
                    statusEl.textContent = '❌ All Tests Failed';
                    statusEl.style.color = '#f44336';
                }
            };
            
            xhr.onerror = function() {
                resultsEl.innerHTML += `<div style="color:#f88">✗ XHR network error</div>`;
                statusEl.textContent = '❌ Connection Error';
                statusEl.style.color = '#f44336';
                
                // Suggest possible solutions
                resultsEl.innerHTML += `
                    <div style="margin-top: 10px; border-top: 1px solid #555; padding-top: 8px;">
                        <strong>Possible solutions:</strong>
                        <ul style="margin-top: 5px; padding-left: 20px;">
                            <li>Ensure Think Tank server is running on port ${port}</li>
                            <li>Check if server has proper CORS headers enabled</li>
                            <li>Try adding 'Access-Control-Allow-Origin: *' to server</li>
                            <li>Verify your network connectivity</li>
                        </ul>
                    </div>
                `;
            };
            
            xhr.send(jsonBody);
        });
    }
    
    // Add click handlers for buttons
    document.getElementById('test-cors-btn').addEventListener('click', function() {
        const port = document.getElementById('port-input').value.trim() || '8090';
        testCORS(port);
    });
    
    // Minimize button handler
    document.getElementById('cors-minimize-btn').addEventListener('click', function() {
        const content = document.getElementById('cors-content');
        const minimizeBtn = document.getElementById('cors-minimize-btn');
        if (content.style.display === 'none') {
            content.style.display = 'block';
            minimizeBtn.textContent = '−';
        } else {
            content.style.display = 'none';
            minimizeBtn.textContent = '+';
        }
    });
    
    // Close button handler
    document.getElementById('cors-close-btn').addEventListener('click', function() {
        document.body.removeChild(testContainer);
    });
    
    // Run the test automatically with port 7070 after a delay to let chat initialize first
    setTimeout(() => testCORS('7070'), 2000);
});
