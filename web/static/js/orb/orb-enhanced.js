/**
 * Enhanced Orb UI - Building on our stable foundation
 * 
 * Implements Minerva Master Ruleset principles while adding visual polish:
 * - Rule #1: Progressive Enhancement
 * - Rule #4: Graceful fallbacks
 * - Rule #5: UI visibility and responsiveness
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
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
});

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

// Create interactive orb visualization
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
  
  // Create orb elements
  const orbHTML = `
    <div class="orb-ring"></div>
    <div class="orb-ring"></div>
    <div class="orb-sphere"></div>
    <div class="orb-label">M</div>
  `;
  orbVis.innerHTML = orbHTML;
  
  // Make orb interactive
  const orbSphere = orbVis.querySelector('.orb-sphere');
  if (orbSphere) {
    orbSphere.addEventListener('click', () => {
      showToast("🧠 Minerva Orb activated", "info");
      
      // Trigger pulse effect
      orbSphere.style.animation = 'none';
      setTimeout(() => {
        orbSphere.style.animation = 'pulse 4s ease-in-out infinite';
      }, 10);
    });
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
  
  // Check API status
  checkApiStatus();
}

// Check Think Tank API status
function checkApiStatus() {
  showToast("🔌 Checking API connection...", "info", { id: 'api-check', timeout: false });
  
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
      updateMinervaStatus('offline', 'Offline');
      console.error("API check error:", error);
    });
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
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
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
  showToast(`🚨 ${msg}`, "error", { timeout: false });
  
  const fallback = document.createElement("div");
  fallback.style = "padding:2rem;color:white;background:rgba(15, 23, 42, 0.9);font-family:monospace;border-radius:8px;margin:20px;backdrop-filter:blur(10px);border:1px solid rgba(239, 68, 68, 0.3);";
  fallback.innerHTML = `
    <h2>⚠️ UI Error</h2>
    <p>${msg}</p>
    <p>Please check the browser console for more information.</p>
  `;
  document.body.prepend(fallback);
}
