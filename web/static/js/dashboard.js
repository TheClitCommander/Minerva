// Define sections globally to share with orb-interface.js
window.sections = {};

document.addEventListener("DOMContentLoaded", function() {
    // Elements
    const contentDisplay = document.getElementById("content-display");
    
    // Define dashboard content sections
    window.sections = {
        dashboard: `
            <div class="dashboard-overview">
                <h1>📊 Minerva Dashboard Overview</h1>
                <p>Welcome to your system dashboard. Here you can see live stats, manage AI agents, and monitor Think Tank activities.</p>
                
                <div class="stats-grid">
                    <!-- System Status Card -->
                    <div class="stats-card">
                        <div class="card-header">
                            <h3>System Status</h3>
                        </div>
                        <div class="card-body">
                            <div class="status-indicator">
                                <div class="status-dot online"></div>
                                <div class="status-text">Minerva Core: <span class="highlight">Online</span></div>
                            </div>
                            
                            <div class="progress-item">
                                <div class="progress-label">
                                    <span>Memory Usage</span>
                                    <span id="memory-percent">68%</span>
                                </div>
                                <div class="progress-bar-container">
                                    <div class="progress-bar" id="memory-bar" style="width: 68%"></div>
                                </div>
                            </div>
                            
                            <div class="progress-item">
                                <div class="progress-label">
                                    <span>System Load</span>
                                    <span id="system-load-percent">42%</span>
                                </div>
                                <div class="progress-bar-container">
                                    <div class="progress-bar" id="system-load-bar" style="width: 42%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Active Processes Card -->
                    <div class="stats-card">
                        <div class="card-header">
                            <h3>Active Processes</h3>
                        </div>
                        <div class="card-body">
                            <ul class="process-list" id="active-processes-list">
                                <li>
                                    <span class="process-icon ai"></span>
                                    <span class="process-name">Think Tank</span>
                                    <span class="process-details">Processing query</span>
                                    <div class="process-progress">
                                        <div class="mini-progress">
                                            <div class="mini-progress-bar" style="width: 75%"></div>
                                        </div>
                                        <span>75%</span>
                                    </div>
                                </li>
                                <li>
                                    <span class="process-icon memory"></span>
                                    <span class="process-name">Memory Indexing</span>
                                    <span class="process-details">Optimizing search vectors</span>
                                    <div class="process-progress">
                                        <div class="mini-progress">
                                            <div class="mini-progress-bar" style="width: 45%"></div>
                                        </div>
                                        <span>45%</span>
                                    </div>
                                </li>
                                <li>
                                    <span class="process-icon data"></span>
                                    <span class="process-name">Conversation Memory</span>
                                    <span class="process-details">Storing context</span>
                                    <div class="process-progress">
                                        <div class="mini-progress">
                                            <div class="mini-progress-bar" style="width: 90%"></div>
                                        </div>
                                        <span>90%</span>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `,
        projects: `
            <div class="projects-section">
                <h1>📂 Projects</h1>
                <p>Organize your conversations into projects. View and manage active projects here.</p>
                
                <div class="projects-grid">
                    <div class="project-card">
                        <div class="project-header">
                            <h3>Research Analysis</h3>
                            <span class="project-badge">5 conversations</span>
                        </div>
                        <p>Analysis of research papers on quantum computing applications.</p>
                        <div class="project-footer">
                            <span class="last-updated">Updated: 2 hours ago</span>
                            <button class="view-project-btn">View Project</button>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-header">
                            <h3>Content Creation</h3>
                            <span class="project-badge">3 conversations</span>
                        </div>
                        <p>Content creation for technical blog posts on AI development.</p>
                        <div class="project-footer">
                            <span class="last-updated">Updated: Yesterday</span>
                            <button class="view-project-btn">View Project</button>
                        </div>
                    </div>
                    
                    <div class="project-card">
                        <div class="project-header">
                            <h3>Data Visualization</h3>
                            <span class="project-badge">2 conversations</span>
                        </div>
                        <p>Creating interactive data visualizations for annual report.</p>
                        <div class="project-footer">
                            <span class="last-updated">Updated: 3 days ago</span>
                            <button class="view-project-btn">View Project</button>
                        </div>
                    </div>
                </div>
                
                <button class="create-new-btn">+ Create New Project</button>
            </div>
        `,
        "ai-agents": `
            <div class="ai-agents-section">
                <h1>🤖 AI Agents</h1>
                <p>Deploy and monitor AI agents in real time.</p>
                
                <div class="agents-toolbar">
                    <button class="primary-btn">Deploy New Agent</button>
                    <div class="filter-options">
                        <span>Filter by:</span>
                        <select>
                            <option>All Agents</option>
                            <option>Active Agents</option>
                            <option>Idle Agents</option>
                        </select>
                    </div>
                </div>
                
                <div class="agents-grid">
                    <div class="agent-card active">
                        <div class="agent-status-indicator"></div>
                        <h3>Research Assistant</h3>
                        <p>Specialized in literature review and data analysis</p>
                        <div class="agent-metrics">
                            <div class="metric">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value">24h 12m</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Tasks</span>
                                <span class="metric-value">12/15</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Memory</span>
                                <span class="metric-value">62%</span>
                            </div>
                        </div>
                        <div class="agent-controls">
                            <button class="agent-btn">Configure</button>
                            <button class="agent-btn danger">Stop</button>
                        </div>
                    </div>
                    
                    <div class="agent-card">
                        <div class="agent-status-indicator idle"></div>
                        <h3>Content Writer</h3>
                        <p>Creates blog posts, articles and social media content</p>
                        <div class="agent-metrics">
                            <div class="metric">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value">0h 0m</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Tasks</span>
                                <span class="metric-value">0/0</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Memory</span>
                                <span class="metric-value">0%</span>
                            </div>
                        </div>
                        <div class="agent-controls">
                            <button class="agent-btn">Configure</button>
                            <button class="agent-btn primary">Start</button>
                        </div>
                    </div>
                    
                    <div class="agent-card active">
                        <div class="agent-status-indicator"></div>
                        <h3>Data Analyzer</h3>
                        <p>Processes large datasets and generates insights</p>
                        <div class="agent-metrics">
                            <div class="metric">
                                <span class="metric-label">Uptime</span>
                                <span class="metric-value">8h 45m</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Tasks</span>
                                <span class="metric-value">3/4</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">Memory</span>
                                <span class="metric-value">78%</span>
                            </div>
                        </div>
                        <div class="agent-controls">
                            <button class="agent-btn">Configure</button>
                            <button class="agent-btn danger">Stop</button>
                        </div>
                    </div>
                </div>
            </div>
        `,
        "think-tank": `
            <div class="think-tank-section">
                <h1>🧠 Think Tank</h1>
                <p>Run complex AI models and view recent analyses.</p>
                
                <!-- Think Tank Navigation Tabs -->
                <div class="think-tank-tabs">
                    <button class="tab-button active" data-tab="query">New Query</button>
                    <button class="tab-button" data-tab="conversations">Conversation History</button>
                    <button class="tab-button" data-tab="recent">Recent Queries</button>
                </div>
                
                <!-- New Query Tab Content -->
                <div class="tab-content active" id="query-tab">
                    <div class="think-tank-interface">
                        <div class="model-selection">
                            <h3>Select Models</h3>
                            <div class="model-checkboxes">
                                <label class="model-option">
                                    <input type="checkbox" checked> 
                                    <span class="model-name">GPT-4</span>
                                    <span class="model-tag">Large Language</span>
                                </label>
                                <label class="model-option">
                                    <input type="checkbox" checked> 
                                    <span class="model-name">Claude 3</span>
                                    <span class="model-tag">Reasoning</span>
                                </label>
                                <label class="model-option">
                                    <input type="checkbox"> 
                                    <span class="model-name">Gemini Pro</span>
                                    <span class="model-tag">Multimodal</span>
                                </label>
                                <label class="model-option">
                                    <input type="checkbox" checked> 
                                    <span class="model-name">Llama 3</span>
                                    <span class="model-tag">Open Source</span>
                                </label>
                                <label class="model-option">
                                    <input type="checkbox"> 
                                    <span class="model-name">DALL-E 3</span>
                                    <span class="model-tag">Image Generation</span>
                                </label>
                            </div>
                        </div>
                        
                        <div class="query-interface">
                            <h3>Enter Your Query</h3>
                            <textarea placeholder="Enter your question or task here..."></textarea>
                            <div class="query-options">
                                <label class="option">
                                    <input type="checkbox" checked> 
                                    <span>Store in memory</span>
                                </label>
                                <label class="option">
                                    <input type="checkbox" checked> 
                                    <span>Include previous context</span>
                                </label>
                                <label class="option">
                                    <input type="checkbox"> 
                                    <span>Prioritize processing</span>
                                </label>
                            </div>
                            <button class="run-query-btn">Run Think Tank Analysis</button>
                        </div>
                    </div>
                </div>
                
                <!-- Conversation History Tab Content -->
                <div class="tab-content" id="conversations-tab">
                    <div class="conversation-history">
                        <div class="conversation-actions">
                            <div class="action-buttons">
                                <button id="refresh-conversations" class="action-btn"><i class="fas fa-sync-alt"></i> Refresh</button>
                                <button id="organize-projects" class="action-btn"><i class="fas fa-folder"></i> Organize Projects</button>
                                <select id="project-filter" class="project-filter">
                                    <option value="all">All Conversations</option>
                                    <option value="general">General</option>
                                    <option value="research">Research</option>
                                    <option value="personal">Personal</option>
                                </select>
                                <input type="text" id="conversation-search" class="conversation-search" placeholder="Search conversations...">
                            </div>
                        </div>
                        <div class="conversations-container">
                            <table class="conversations-table">
                                <thead>
                                    <tr>
                                        <th>Title/First Message</th>
                                        <th>Project</th>
                                        <th>Date</th>
                                        <th>Models</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="conversation-history-tbody">
                                    <!-- Conversations will be loaded here dynamically -->
                                    <tr class="conversation-loading">
                                        <td colspan="5">Loading conversation history...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <!-- Recent Queries Tab Content -->
                <div class="tab-content" id="recent-tab">
                    <div class="recent-queries">
                        <h3>Recent Queries</h3>
                        <table class="queries-table">
                            <thead>
                                <tr>
                                    <th>Query</th>
                                    <th>Models</th>
                                    <th>Time</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Analysis of recent advancements in quantum computing</td>
                                    <td>GPT-4, Claude 3, Llama 3</td>
                                    <td>1 hour ago</td>
                                    <td><button class="view-btn">View Results</button></td>
                                </tr>
                                <tr>
                                    <td>Compare approaches to reinforcement learning</td>
                                    <td>GPT-4, Claude 3</td>
                                    <td>Yesterday</td>
                                    <td><button class="view-btn">View Results</button></td>
                                </tr>
                                <tr>
                                    <td>Generate visualizations for customer retention data</td>
                                    <td>GPT-4, DALL-E 3</td>
                                    <td>3 days ago</td>
                                    <td><button class="view-btn">View Results</button></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `,
        "logs": `
            <div class="logs-section">
                <h1>📜 Logs</h1>
                <p>View system logs, errors, and debugging reports.</p>
                
                <div class="logs-toolbar">
                    <div class="log-filters">
                        <select class="log-level-filter">
                            <option>All Levels</option>
                            <option>Info</option>
                            <option>Warning</option>
                            <option>Error</option>
                            <option>Debug</option>
                        </select>
                        <select class="log-source-filter">
                            <option>All Sources</option>
                            <option>System Core</option>
                            <option>Think Tank</option>
                            <option>Memory System</option>
                            <option>AI Agents</option>
                        </select>
                        <input type="text" placeholder="Search logs..." class="log-search">
                    </div>
                    <div class="log-actions">
                        <button class="refresh-logs-btn">Refresh</button>
                        <button class="export-logs-btn">Export</button>
                    </div>
                </div>
                
                <div class="logs-container">
                    <table class="logs-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Source</th>
                                <th>Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr class="log-entry">
                                <td class="timestamp">2025-03-15 23:30:12</td>
                                <td class="level info">INFO</td>
                                <td class="source">System Core</td>
                                <td class="message">System initialized successfully</td>
                            </tr>
                            <tr class="log-entry">
                                <td class="timestamp">2025-03-15 23:29:58</td>
                                <td class="level warning">WARNING</td>
                                <td class="source">Memory System</td>
                                <td class="message">Memory usage approaching threshold (78%)</td>
                            </tr>
                            <tr class="log-entry">
                                <td class="timestamp">2025-03-15 23:28:45</td>
                                <td class="level error">ERROR</td>
                                <td class="source">Think Tank</td>
                                <td class="message">Failed to connect to Claude 3 API: Timeout</td>
                            </tr>
                            <tr class="log-entry">
                                <td class="timestamp">2025-03-15 23:27:30</td>
                                <td class="level info">INFO</td>
                                <td class="source">AI Agents</td>
                                <td class="message">Research Assistant agent started successfully</td>
                            </tr>
                            <tr class="log-entry">
                                <td class="timestamp">2025-03-15 23:26:15</td>
                                <td class="level debug">DEBUG</td>
                                <td class="source">System Core</td>
                                <td class="message">Attempting to connect to external resources...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="pagination">
                    <button disabled>Previous</button>
                    <span>Page 1 of 5</span>
                    <button>Next</button>
                </div>
            </div>
        `,
        "settings": `
            <div class="settings-section">
                <h1>⚙️ Settings</h1>
                <p>Adjust system preferences and configurations.</p>
                
                <div class="settings-tabs">
                    <div class="tab active" data-tab="general">General</div>
                    <div class="tab" data-tab="models">AI Models</div>
                    <div class="tab" data-tab="memory">Memory & Storage</div>
                    <div class="tab" data-tab="appearance">Appearance</div>
                    <div class="tab" data-tab="advanced">Advanced</div>
                </div>
                
                <div class="settings-content active" id="general-settings">
                    <h3>General Settings</h3>
                    
                    <div class="setting-item">
                        <div class="setting-info">
                            <label>System Name</label>
                            <p class="setting-description">Name displayed throughout the interface</p>
                        </div>
                        <div class="setting-control">
                            <input type="text" value="Minerva" />
                        </div>
                    </div>
                    
                    <div class="setting-item">
                        <div class="setting-info">
                            <label>Default Project</label>
                            <p class="setting-description">Project to use when none is specified</p>
                        </div>
                        <div class="setting-control">
                            <select>
                                <option>General</option>
                                <option>Research</option>
                                <option>Personal</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="setting-item">
                        <div class="setting-info">
                            <label>Notifications</label>
                            <p class="setting-description">Enable system notifications</p>
                        </div>
                        <div class="setting-control">
                            <label class="toggle">
                                <input type="checkbox" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    
                    <div class="setting-item">
                        <div class="setting-info">
                            <label>Auto-save Interval</label>
                            <p class="setting-description">How often to automatically save conversations</p>
                        </div>
                        <div class="setting-control">
                            <select>
                                <option>30 seconds</option>
                                <option>1 minute</option>
                                <option selected>5 minutes</option>
                                <option>15 minutes</option>
                            </select>
                        </div>
                    </div>
                    
                    <button class="save-settings-btn">Save Changes</button>
                </div>
            </div>
        `
    };

    // Detect view mode changes from orb navigation
    const navOptions = document.querySelectorAll(".nav-option");
    if (navOptions.length > 0) {
        navOptions.forEach(option => {
            option.addEventListener("click", function() {
                const section = this.getAttribute("data-section");
                updateContentDisplay(section);
            });
        });
    }
    
    /**
     * Update content display based on section
     * @param {string} section - The section to display
     */
    function updateContentDisplay(section) {
        if (window.sections[section]) {
            contentDisplay.innerHTML = window.sections[section];
            
            // Special behavior for dashboard section (update stats)
            if (section === "dashboard") {
                window.updateSystemStats();
            }
        }
    }

    // Set up navigation
    menuItems.forEach(item => {
        item.addEventListener("click", function() {
            // Remove active class from all items
            menuItems.forEach(i => i.classList.remove("active"));
            // Add active class to clicked item
            this.classList.add("active");

            // Update the content area
            const section = this.getAttribute("data-section");
            contentDisplay.innerHTML = sections[section];
        });
    });

    // Auto-update stats - make globally accessible
    window.updateSystemStats = function() {
        // Update memory usage (random values for demo)
        const memoryUsage = 50 + Math.floor(Math.random() * 30);
        const systemLoad = 30 + Math.floor(Math.random() * 40);
        const lastQueryTime = Math.floor(Math.random() * 10) + 1; // 1-10 mins
        
        // Update memory usage
        const memoryBar = document.getElementById("memory-bar");
        const memoryValue = document.getElementById("memory-value");
        const memoryPercent = document.getElementById("memory-percent");
        
        if (memoryBar) memoryBar.style.width = `${memoryUsage}%`;
        if (memoryValue) memoryValue.textContent = `${memoryUsage}%`;
        if (memoryPercent) memoryPercent.textContent = `${memoryUsage}%`;
        
        // Update system load
        const loadBar = document.getElementById("load-bar");
        const loadValue = document.getElementById("load-value");
        const systemLoadPercent = document.getElementById("system-load-percent");
        const systemLoadBar = document.getElementById("system-load-bar");
        
        if (loadBar) loadBar.style.width = `${systemLoad}%`;
        if (loadValue) loadValue.textContent = `${systemLoad}%`;
        if (systemLoadPercent) systemLoadPercent.textContent = `${systemLoad}%`;
        if (systemLoadBar) systemLoadBar.style.width = `${systemLoad}%`;
        
        // Update last query time
        const lastQuery = document.getElementById("last-query-time");
        if (lastQuery) {
            lastQuery.textContent = `${lastQueryTime} mins ago`;
        }
        
        // Add some randomness to activity feed
        updateActivityFeed();
    }
    
    // Update stats initially and then every 5 seconds
    window.updateSystemStats();
    setInterval(window.updateSystemStats, 5000);
    
    /**
     * Randomly update one item in the activity feed to simulate live updates
     */
    function updateActivityFeed() {
        const activities = [
            { time: "12:45 PM", activity: "Think Tank Query: \"Quantum Computing Analysis\"", status: "Completed" },
            { time: "1:15 PM", activity: "Neural Network Training: Phase 2", status: "In Progress" },
            { time: "1:32 PM", activity: "New Project Created: \"Molecular Research\"", status: "Created" },
            { time: "1:54 PM", activity: "Data Synchronization with Cloud", status: "Completed" },
            { time: "2:10 PM", activity: "AI Agent Update: Version 1.3.4", status: "Deployed" }
        ];
        
        const statusClasses = {
            "Completed": "success",
            "Created": "success",
            "Deployed": "success",
            "In Progress": "warning",
            "Failed": "danger"
        };
        
        // Only update if we have an activity table
        const activityTable = document.querySelector(".activity-table tbody");
        if (activityTable && Math.random() > 0.7) {
            // Only occasionally update (30% chance)
            const randomRow = Math.floor(Math.random() * Math.min(activityTable.children.length, 4));
            const randomActivity = activities[Math.floor(Math.random() * activities.length)];
            
            if (activityTable.children[randomRow]) {
                const cells = activityTable.children[randomRow].children;
                if (cells.length >= 3) {
                    cells[0].textContent = randomActivity.time;
                    cells[1].textContent = randomActivity.activity;
                    cells[2].innerHTML = `<span class="badge ${statusClasses[randomActivity.status]}">${randomActivity.status}</span>`;
                }
            }
        }
    }
});

// Make the orb interface communicate with dashboard sections
document.addEventListener("DOMContentLoaded", function() {
    // Handle initial view
    if (window.orbInterface) {
        // Select default view on load
        setTimeout(() => {
            const defaultOption = document.querySelector(".nav-option[data-section='dashboard']");
            if (defaultOption && window.orbInterface.selectNavOption) {
                window.orbInterface.selectNavOption(defaultOption);
            }
        }, 500);
    }
});
