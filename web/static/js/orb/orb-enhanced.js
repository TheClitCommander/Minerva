/**
 * Enhanced Orb UI - Building on our stable foundation
 * 
 * Implements Minerva Master Ruleset principles while adding visual polish:
 * - Rule #1: Progressive Enhancement
 * - Rule #4: Graceful fallbacks
 * - Rule #5: UI visibility and responsiveness
 */

// More robust initialization that handles both DOMContentLoaded and window.onload
function initOrb() {
  try {
  console.log("🔄 Initializing Enhanced Minerva Orb UI...");
  
  // Initialize toast notification container
  createToastContainer();
  
  // Check for required DOM elements
  const orb = document.getElementById("orb-container");
  if (!orb) {
    return showFallback("Missing #orb-container element");
  }

  const interface = document.getElementById("orb-interface");
  if (!interface) {
    return showFallback("Missing #orb-interface element");
  }

  // Validate each required section
  const sections = ["dashboard", "chat", "memory"];
  let foundAll = true;

  for (let sec of sections) {
    if (!document.getElementById(`orb-${sec}`)) {
      console.warn(`Missing #orb-${sec} section`);
      foundAll = false;
    }
  }

  if (!foundAll) {
    return showFallback("Missing one or more orb sections");
  }

  // Initialize the UI components
  initNav();
  initOrbVisualization();
  initApiStatusCheck();
  initKeyboardShortcuts();
  
      console.log("✅ Enhanced Orb UI ready");
  } catch (error) {
    console.error("Error initializing Orb UI:", error);
    showFallback("Error initializing UI: " + error.message);
  }
}

// Initialize on DOM content loaded
document.addEventListener('DOMContentLoaded', initOrb);

// Backup initialization with window.onload (in case DOMContentLoaded already fired)
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  setTimeout(initOrb, 100);
}

// Initialize navigation between sections with icons
function initNav() {
  const buttons = document.querySelectorAll(".orb-nav-btn");
  
  // Add icons to navigation buttons if not present
  buttons.forEach(btn => {
    if (!btn.querySelector('i')) {
      const target = btn.dataset.target;
      let icon = '';
      
      switch(target) {
        case 'dashboard':
          icon = '📊';
          break;
        case 'chat':
          icon = '💬';
          break;
        case 'memory':
          icon = '🧠';
          break;
        default:
          icon = '📑';
      }
      
      // Insert icon before text
      btn.innerHTML = `<span>${icon}</span> ${btn.textContent}`;
    }
  });
  
  // Make dashboard active by default
  switchSection("dashboard");
  
  // Add click handlers to each nav button
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;
      switchSection(target);
    });
  });
}

// Switch between UI sections with animation
function switchSection(target) {
  // Hide all sections
  const all = document.querySelectorAll(".orb-section");
  all.forEach((sec) => {
    sec.style.display = "none";
    sec.style.opacity = "0";
  });

  // Show the selected section
  const selected = document.getElementById(`orb-${target}`);
  if (selected) {
    selected.style.display = "block";
    
    // Trigger animation
    setTimeout(() => {
      selected.style.opacity = "1";
      selected.style.transition = "opacity 0.3s ease";
    }, 10);
    
    console.log(`🔀 Switched to ${target}`);
    
    // Update active state on buttons
    document.querySelectorAll(".orb-nav-btn").forEach(btn => {
      if (btn.dataset.target === target) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
    
    // Remember last active section
    localStorage.setItem('minervaLastActiveSection', target);
  } else {
    console.warn(`No section found for '${target}'`);
  }
}

// Create interactive orb visualization with radial menu
function initOrbVisualization() {
  // Find a suitable container
  const dashboard = document.getElementById('orb-dashboard');
  
  if (!dashboard) {
    console.warn("Dashboard section not found for orb visualization");
    return;
  }
  
  // Create orb container if it doesn't exist
  let orbVis = document.getElementById('orb-visualization');
  if (!orbVis) {
    orbVis = document.createElement('div');
    orbVis.id = 'orb-visualization';
    dashboard.prepend(orbVis);
  }
  
  // Create orb elements with radial menu buttons
  const orbHTML = `
    <div class="orb-ring"></div>
    <div class="orb-ring"></div>
    <div class="orb-sphere" id="orb-button"></div>
    <div class="orb-label">M</div>
    <div class="orb-menu" id="orb-radial-menu">
      <button class="orb-menu-item" data-action="dashboard">
        <i class="fas fa-chart-network"></i>
        <span>Dashboard</span>
      </button>
      <button class="orb-menu-item" data-action="chat">
        <i class="fas fa-comments"></i>
        <span>Chat</span>
      </button>
      <button class="orb-menu-item" data-action="memory">
        <i class="fas fa-brain"></i>
        <span>Memory</span>
      </button>
      <button class="orb-menu-item" data-action="projects">
        <i class="fas fa-project-diagram"></i>
        <span>Projects</span>
      </button>
    </div>
  `;
  orbVis.innerHTML = orbHTML;
  
  // Make orb interactive
  const orbButton = document.getElementById('orb-button');
  const radialMenu = document.getElementById('orb-radial-menu');
  
  if (orbButton && radialMenu) {
    // Add click event to toggle radial menu
    orbButton.addEventListener('click', (e) => {
      e.preventDefault();
      toggleOrbMenu();
    });
    
    // Add click events to menu items
    const menuItems = radialMenu.querySelectorAll('.orb-menu-item');
    menuItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const action = item.getAttribute('data-action');
        handleOrbAction(action);
        toggleOrbMenu(false); // close menu after selection
      });
    });
  }
}

// Toggle the radial menu around the orb
function toggleOrbMenu(forcedState) {
  const menu = document.getElementById('orb-radial-menu');
  const orbButton = document.getElementById('orb-button');
  
  if (!menu || !orbButton) {
    console.warn("Orb menu elements not found");
    return;
  }
  
  const isVisible = menu.classList.contains('active');
  const newState = (forcedState !== undefined) ? forcedState : !isVisible;
  
  if (newState) {
    // Show menu
    menu.classList.add('active');
    orbButton.classList.add('active');
    showToast("🧠 Minerva Command Center", "info", { timeout: 1500 });
    
    // Trigger pulse effect
    orbButton.style.animation = 'none';
    setTimeout(() => {
      orbButton.style.animation = 'pulse 4s ease-in-out infinite';
    }, 10);
  } else {
    // Hide menu
    menu.classList.remove('active');
    orbButton.classList.remove('active');
  }
}

// Handle actions from the orb menu
function handleOrbAction(action) {
  console.log(`Orb action: ${action}`);
  
  switch(action) {
    case 'dashboard':
    case 'chat':
    case 'memory':
    case 'projects':
      switchSection(action);
      showToast(`📊 ${action} view activated`, "info", { timeout: 1500 });
      break;
      
    case 'think':
      showToast("🧠 Thinking...", "info");
      // Add think tank interaction here
      break;
      
    default:
      console.warn(`Unknown orb action: ${action}`);
  }
}

// Initialize API status check and create status indicator
function initApiStatusCheck() {
  // Create status indicator if it doesn't exist
  let statusIndicator = document.querySelector('.minerva-status');
  if (!statusIndicator) {
    statusIndicator = document.createElement('div');
    statusIndicator.className = 'minerva-status';
    statusIndicator.innerHTML = `
      <div class="status-indicator offline"></div>
      <span class="status-text">Checking connection...</span>
    `;
    
    const orbContainer = document.getElementById('orb-container');
    if (orbContainer) {
      orbContainer.appendChild(statusIndicator);
    }
  }
  
  // Remove old status indicator if exists
  const oldStatus = document.getElementById('think-tank-status');
  if (oldStatus) {
    oldStatus.remove();
  }
  
  // Check API status using our new API client
  checkApiStatus();
  
  // Listen for API status changes
  window.addEventListener('minerva-api-status', (event) => {
    updateMinervaStatus(event.detail.status, event.detail.status.charAt(0).toUpperCase() + event.detail.status.slice(1));
  });
}

// Check Think Tank API status
function checkApiStatus() {
  // First show a toast that we're checking
  showToast("🔌 Checking API connection...", "info", { id: 'api-check', timeout: false });
  
  // Use our robust API client if available
  if (window.minervaAPI) {
    window.minervaAPI.checkConnection()
      .then(status => {
        // Remove checking toast
        removeToast('api-check');
        
        // Show appropriate status toast
        if (status === 'online') {
          showToast("✅ Think Tank API connected", "success", { timeout: 3000 });
        } else if (status === 'limited') {
          showToast("⚠️ Limited API functionality", "warning", { timeout: 5000 });
        } else {
          showToast("🚫 API in offline mode", "error", { timeout: 5000 });
        }
      })
      .catch(error => {
        console.error("Error checking API status:", error);
        removeToast('api-check');
        showToast("🚫 API connection failed", "error", { timeout: 5000 });
        updateMinervaStatus('offline', 'Offline');
      });
  } else {
    // Fallback to basic fetch if API client isn't available
    fetch('/api/think-tank')
      .then(response => response.json())
      .then(data => {
        // Update toast
        removeToast('api-check');
        
        if (data.status === 'success') {
          showToast("✅ Think Tank API connected", "success", { timeout: 3000 });
          updateMinervaStatus('online', 'Online');
        } else {
          showToast("⚠️ Limited API functionality", "warning", { timeout: 5000 });
          updateMinervaStatus('limited', 'Limited');
        }
      })
      .catch(error => {
        // Update toast
        removeToast('api-check');
        showToast("🚫 API connection failed", "error", { timeout: 5000 });
        updateMinervaStatus('offline', 'Offline (fallback mode)');
        console.error("API check error:", error);
      });
  }
}

// Update Minerva status indicator
function updateMinervaStatus(status, text) {
  const indicator = document.querySelector('.minerva-status .status-indicator');
  const statusText = document.querySelector('.minerva-status .status-text');
  
  if (indicator) {
    indicator.className = `status-indicator ${status}`;
  }
  
  if (statusText) {
    statusText.textContent = text;
  }
  
  // Update orb appearance based on status
  const orbButton = document.getElementById('orb-button');
  if (orbButton) {
    // Remove previous status classes
    orbButton.classList.remove('status-online', 'status-limited', 'status-offline');
    // Add new status class
    orbButton.classList.add(`status-${status}`);
  }
}

// Add keyboard shortcuts
function initKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    // Check if Ctrl key is pressed
    if (e.ctrlKey) {
      const sectionKeys = {
        '1': 'dashboard',
        '2': 'chat',
        '3': 'memory'
      };
      
      const key = e.key;
      if (sectionKeys[key]) {
        e.preventDefault();
        switchSection(sectionKeys[key]);
        
        // Show shortcut toast
        showToast(`⌨️ Shortcut: ${sectionKeys[key]}`, "info", { timeout: 1000 });
      }
    }
  });
}

// Toast notification system
let toastContainer = null;

function createToastContainer() {
  // If we already have a reference, verify it's still in the DOM
  if (toastContainer) {
    if (!document.body.contains(toastContainer)) {
      toastContainer = null; // Reference is invalid, container was removed
    }
  }
  
  // Create new container if needed
  if (!toastContainer) {
    try {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container';
      document.body.appendChild(toastContainer);
    } catch (error) {
      console.error("Could not create toast container:", error);
      return null;
    }
  }
  return toastContainer;
}

function showToast(message, type = 'info', options = {}) {
  const container = createToastContainer();
  const id = options.id || 'toast-' + Date.now();
  
  // Check if toast with this ID already exists
  const existingToast = document.getElementById(id);
  if (existingToast) {
    existingToast.querySelector('.message').textContent = message;
    return;
  }
  
  // Create icons based on type
  let icon = '💬';
  switch(type) {
    case 'success': icon = '✅'; break;
    case 'error': icon = '❌'; break;
    case 'warning': icon = '⚠️'; break;
    case 'info': icon = '💬'; break;
  }
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast-notification ${type}`;
  toast.id = id;
  toast.innerHTML = `
    <div class="icon">${icon}</div>
    <div class="message">${message}</div>
    <div class="close">✕</div>
  `;
  
  // Add to container
  container.appendChild(toast);
  
  // Handle close button
  toast.querySelector('.close').addEventListener('click', () => {
    removeToast(id);
  });
  
  // Auto-remove after timeout (if specified)
  if (options.timeout !== false) {
    setTimeout(() => {
      removeToast(id);
    }, options.timeout || 3000);
  }
  
  return id;
}

function removeToast(id) {
  const toast = document.getElementById(id);
  if (toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }
}

// Show fallback UI when critical elements are missing
function showFallback(msg) {
  console.error(`Orb UI Error: ${msg}`);
  
  try {
    // Try to show toast, but don't fail if it can't be shown
    showToast(`🚨 ${msg}`, "error", { timeout: false });
  } catch (e) {
    console.warn('Could not show toast notification:', e);
  }
  
  try {
    // Create a standalone error message element that doesn't rely on existing DOM
    const fallback = document.createElement("div");
    fallback.id = 'minerva-fallback-message';
    fallback.style = "position:fixed;top:20px;left:20px;right:20px;z-index:9999;padding:2rem;color:white;background:rgba(15, 23, 42, 0.9);font-family:sans-serif;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3);backdrop-filter:blur(10px);border:1px solid rgba(239, 68, 68, 0.3);";
    fallback.innerHTML = `
      <h2 style="margin-top:0;margin-bottom:10px;color:#ef4444;">⚠️ Minerva UI Error</h2>
      <p style="margin:0 0 15px 0;">${msg}</p>
      <p style="margin:0;font-size:14px;opacity:0.7;">Please check the browser console for details</p>
      <div style="margin-top:15px;">
        <button id="minerva-error-dismiss" style="background:#ef4444;border:none;color:white;padding:8px 16px;border-radius:4px;cursor:pointer;">Dismiss</button>
        <button id="minerva-error-retry" style="background:#3b82f6;border:none;color:white;padding:8px 16px;border-radius:4px;cursor:pointer;margin-left:10px;">Retry</button>
      </div>
    `;
    
    // Avoid duplicate error messages
    const existingFallback = document.getElementById('minerva-fallback-message');
    if (existingFallback) {
      existingFallback.remove();
    }
    
    // Append to body
    document.body.appendChild(fallback);
    
    // Add event listeners to buttons
    document.getElementById('minerva-error-dismiss')?.addEventListener('click', () => {
      fallback.style.display = 'none';
    });
    
    document.getElementById('minerva-error-retry')?.addEventListener('click', () => {
      fallback.style.display = 'none';
      location.reload();
    });
  } catch (e) {
    // Last resort: alert
    console.error('Failed to show fallback UI:', e);
    try {
      alert('Minerva UI Error: ' + msg);
    } catch (e2) {
      // Nothing more we can do
    }
  }
}
