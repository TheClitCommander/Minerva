/**
 * Minerva Chat Test Script
 * Tests API connectivity and chat element initialization
 */

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("🧪 Running Minerva Chat Test Script");
    
    // Create a test container
    const testContainer = document.createElement('div');
    testContainer.id = 'chat-test-container';
    testContainer.style.position = 'fixed';
    testContainer.style.top = '20px';
    testContainer.style.right = '20px';
    testContainer.style.width = '300px';
    testContainer.style.padding = '15px';
    testContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    testContainer.style.color = 'white';
    testContainer.style.borderRadius = '8px';
    testContainer.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
    testContainer.style.zIndex = '10000';
    testContainer.style.fontFamily = 'Arial, sans-serif';
    
    // Add status indicators
    testContainer.innerHTML = `
        <h3 style="margin: 0 0 10px; color: #fff;">Minerva Chat Test</h3>
        <div>API Status: <span id="api-status">Testing...</span></div>
        <div>Chat Elements: <span id="elements-status">Checking...</span></div>
        <button id="test-api-btn" style="margin-top: 10px; padding: 5px 10px; background: #4a4a9e; color: white; border: none; border-radius: 4px; cursor: pointer;">Test API</button>
        <button id="create-chat-btn" style="margin-top: 10px; padding: 5px 10px; background: #4a4a9e; color: white; border: none; border-radius: 4px; cursor: pointer;">Create Chat UI</button>
    `;
    
    document.body.appendChild(testContainer);
    
    // Test API connection
    function testAPI() {
        document.getElementById('api-status').textContent = 'Connecting...';
        document.getElementById('api-status').style.color = '#ffa500';
        
        // Try multiple port options, as the server might be running on different ports
        const portOptions = [7075, 8090, 7070, 5000, 8000, 8080, 3000];
        // Port explanations:
        // 7075 - CORS Proxy for Think Tank API
        // 8090 - Default Think Tank API port
        // 7070 - Test server
        const apiBase = "http://localhost:";
        let attemptedPorts = [];
        
        // Create a test container for additional info
        let testInfo = document.getElementById('api-test-info');
        if (!testInfo) {
            testInfo = document.createElement('div');
            testInfo.id = 'api-test-info';
            testInfo.style.marginTop = '10px';
            testInfo.style.fontSize = '12px';
            testInfo.style.color = '#aaa';
            document.getElementById('chat-test-container').appendChild(testInfo);
        }
        testInfo.innerHTML = 'Testing ports: ' + portOptions.join(', ');
        
        // Try each port sequentially
        function tryNextPort(index) {
            if (index >= portOptions.length) {
                document.getElementById('api-status').textContent = '❌ Failed: No server found';
                document.getElementById('api-status').style.color = '#f44336';
                testInfo.innerHTML += '<br>❌ No Think Tank API server found on any port';
                return;
            }
            
            const port = portOptions[index];
            const apiUrl = `${apiBase}${port}/api/think-tank`;
            attemptedPorts.push(port);
            testInfo.innerHTML = 'Testing ports: ' + attemptedPorts.join(', ');
            
            console.log(`Testing API on port ${port}...`);
            
            // Try using no-cors mode first to check if server exists
            fetch(apiUrl, {
                method: 'HEAD',
                mode: 'no-cors',
                cache: 'no-cache',
            })
            .then(() => {
                console.log(`Server may be available on port ${port}, trying full request...`);
                // If we get here, server may be reachable, try a real POST
                return fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Origin': window.location.origin
                    },
                    body: JSON.stringify({
                        message: 'Test from diagnostics',
                        type: 'system_check',
                        conversation_id: localStorage.getItem('minerva_conversation_id') || 'test-session'
                    })
                });
            })
            .then(response => {
                if (response.ok) {
                    document.getElementById('api-status').textContent = `✅ Connected on port ${port}`;
                    document.getElementById('api-status').style.color = '#4caf50';
                    testInfo.innerHTML += `<br>✅ API server found on port ${port}`;
                    
                    // Save the successful port for future use
                    localStorage.setItem('minerva_api_port', port.toString());
                    localStorage.setItem('minerva_api_url', apiUrl);
                    
                    // Update the main script's API URL
                    if (window.THINK_TANK_API_URL) {
                        window.THINK_TANK_API_URL = apiUrl;
                    }
                    
                    return response.json();
                } else {
                    throw new Error(`Status: ${response.status}`);
                }
            })
            .then(data => {
                console.log('API response:', data);
            })
            .catch(err => {
                console.log(`Port ${port} failed:`, err.message);
                // Try next port
                tryNextPort(index + 1);
            });
        }
        
        // Start with the first port
        tryNextPort(0);
    }
    
    // Check and create chat elements
    function checkChatElements() {
        // Check for chat elements
        const chatInput = document.getElementById('floating-chat-input') || document.getElementById('chat-input');
        const sendButton = document.getElementById('floating-chat-send-button') || document.getElementById('chat-send-button');
        const chatMessages = document.getElementById('floating-chat-messages') || document.getElementById('chat-messages');
        
        if (chatInput && sendButton && chatMessages) {
            document.getElementById('elements-status').textContent = '✅ Found';
            document.getElementById('elements-status').style.color = '#4caf50';
        } else {
            document.getElementById('elements-status').textContent = '❌ Missing';
            document.getElementById('elements-status').style.color = '#f44336';
        }
    }
    
    // Create minimal chat UI
    function createChatUI() {
        // Create floating chat container if it doesn't exist
        let container = document.getElementById('floating-chat-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'floating-chat-container';
            container.style.position = 'fixed';
            container.style.bottom = '20px';
            container.style.right = '20px';
            container.style.width = '350px';
            container.style.height = '450px';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.backgroundColor = 'white';
            container.style.borderRadius = '8px';
            container.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.2)';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        // Create chat header
        let header = container.querySelector('.chat-header');
        if (!header) {
            header = document.createElement('div');
            header.className = 'chat-header';
            header.style.padding = '10px';
            header.style.backgroundColor = '#4a4a9e';
            header.style.color = 'white';
            header.style.borderTopLeftRadius = '8px';
            header.style.borderTopRightRadius = '8px';
            header.textContent = 'Minerva Chat';
            container.appendChild(header);
        }
        
        // Create chat messages
        let messages = document.getElementById('floating-chat-messages');
        if (!messages) {
            messages = document.createElement('div');
            messages.id = 'floating-chat-messages';
            messages.className = 'chat-messages';
            messages.style.flex = '1';
            messages.style.padding = '10px';
            messages.style.overflowY = 'auto';
            container.appendChild(messages);
            
            // Add welcome message
            const welcome = document.createElement('div');
            welcome.className = 'message assistant';
            welcome.style.padding = '8px';
            welcome.style.marginBottom = '8px';
            welcome.style.backgroundColor = '#f1f1f1';
            welcome.style.borderRadius = '8px';
            welcome.textContent = 'Hello! How can I help you today?';
            messages.appendChild(welcome);
        }
        
        // Create input container
        let inputContainer = container.querySelector('.chat-input-container');
        if (!inputContainer) {
            inputContainer = document.createElement('div');
            inputContainer.className = 'chat-input-container';
            inputContainer.style.display = 'flex';
            inputContainer.style.padding = '10px';
            inputContainer.style.borderTop = '1px solid #eee';
            container.appendChild(inputContainer);
            
            // Create input
            const input = document.createElement('input');
            input.id = 'floating-chat-input';
            input.className = 'chat-input';
            input.style.flex = '1';
            input.style.padding = '8px';
            input.style.border = '1px solid #ddd';
            input.style.borderRadius = '4px';
            input.style.marginRight = '8px';
            input.placeholder = 'Ask Minerva...';
            inputContainer.appendChild(input);
            
            // Create send button
            const button = document.createElement('button');
            button.id = 'floating-chat-send-button';
            button.className = 'chat-send-button';
            button.style.padding = '8px 12px';
            button.style.backgroundColor = '#4a4a9e';
            button.style.color = 'white';
            button.style.border = 'none';
            button.style.borderRadius = '4px';
            button.style.cursor = 'pointer';
            button.textContent = 'Send';
            inputContainer.appendChild(button);
            
            // Add event listeners
            button.addEventListener('click', function() {
                if (input.value.trim()) {
                    const message = input.value;
                    input.value = '';
                    
                    // Add user message
                    const userMsg = document.createElement('div');
                    userMsg.className = 'message user';
                    userMsg.style.padding = '8px';
                    userMsg.style.marginBottom = '8px';
                    userMsg.style.backgroundColor = '#e3f2fd';
                    userMsg.style.borderRadius = '8px';
                    userMsg.style.marginLeft = '20%';
                    userMsg.textContent = message;
                    messages.appendChild(userMsg);
                    
                    // Send to API
                    testAPI();
                    
                    // Simulate response
                    setTimeout(() => {
                        const botMsg = document.createElement('div');
                        botMsg.className = 'message assistant';
                        botMsg.style.padding = '8px';
                        botMsg.style.marginBottom = '8px';
                        botMsg.style.backgroundColor = '#f1f1f1';
                        botMsg.style.borderRadius = '8px';
                        botMsg.textContent = 'I received your message: "' + message + '". The API connection status is shown in the test panel.';
                        messages.appendChild(botMsg);
                        messages.scrollTop = messages.scrollHeight;
                    }, 1000);
                    
                    messages.scrollTop = messages.scrollHeight;
                }
            });
            
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && input.value.trim()) {
                    button.click();
                }
            });
        }
        
        // Update status
        checkChatElements();
    }
    
    // Set up event listeners
    document.getElementById('test-api-btn').addEventListener('click', testAPI);
    document.getElementById('create-chat-btn').addEventListener('click', createChatUI);
    
    // Run initial tests
    setTimeout(() => {
        testAPI();
        checkChatElements();
    }, 1000);
});
