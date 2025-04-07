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
    const sections = ["dashboard", "chat", "memory", "projects"];
    let foundAll = true;

    for (let sec of sections) {
      if (!document.getElementById(`orb-${sec}`)) {
        console.warn(`Missing #orb-${sec} section`);
        foundAll = false;
      }
    }

    if (!foundAll) {
      console.warn("Some orb sections are missing, but we'll continue");
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
  // Find the existing orb visualization or create it if needed
  let visualization = document.getElementById('orb-visualization');
  let orbButton = document.getElementById('orb-button');
  let orbMenu = document.getElementById('orb-menu');
  
  // If the essential elements don't exist, show a fallback
  if (!visualization) {
    return showFallback('Orb visualization container not found');  
  }
  
  // Make sure the orb button exists
  if (!orbButton) {
    orbButton = document.createElement('div');
    orbButton.id = 'orb-button';
    orbButton.className = 'orb-button';
    visualization.appendChild(orbButton);
  }
  
  // Make sure the menu exists
  if (!orbMenu) {
    orbMenu = document.createElement('div');
    orbMenu.id = 'orb-menu';
    orbMenu.className = 'orb-menu';
    visualization.appendChild(orbMenu);
    
    // Create menu items
    const menuItems = [
      { action: 'dashboard', icon: 'fa-home', text: 'Dashboard' },
      { action: 'chat', icon: 'fa-comment-alt', text: 'Chat' },
      { action: 'memory', icon: 'fa-brain', text: 'Memory' },
      { action: 'projects', icon: 'fa-project-diagram', text: 'Projects' }
    ];
    
    menuItems.forEach(item => {
      const menuItem = document.createElement('div');
      menuItem.className = 'orb-menu-item';
      menuItem.dataset.action = item.action;
      menuItem.innerHTML = `
        <i class="fas ${item.icon}"></i>
      orbMenu.appendChild(menuItem);
    });
  }
  
  // Apply pulse animation to orb button
  orbButton.classList.add('pulse');
  
  // Add inner ring for visual depth if not present
  let innerRing = visualization.querySelector('.orb-inner-ring');
  if (!innerRing) {
    innerRing = document.createElement('div');
    innerRing.className = 'orb-inner-ring';
    visualization.insertBefore(innerRing, orbMenu);
  }
  
  // Add the outer rings if missing
  const rings = visualization.querySelectorAll('.orb-ring');
  if (rings.length < 2) {
    // Clear existing and add two new rings
    rings.forEach(ring => ring.remove());
    
    for (let i = 0; i < 2; i++) {
      const ring = document.createElement('div');
      ring.className = 'orb-ring';
      if (i === 0) {
        ring.style.animationDelay = '0s';
      } else {
        ring.style.animationDelay = '1s';
      }
      visualization.insertBefore(ring, orbMenu);
    }
  }
  
  // Make orb clickable to toggle menu and interface
  orbButton.addEventListener('click', (e) => {
    toggleOrbMenu();
    handleOrbAction('toggle');
    e.stopPropagation();
  });
  
  // Add click handlers to the menu items
  document.querySelectorAll('.orb-menu-item').forEach(item => {
    item.addEventListener('click', (e) => {
      const action = item.getAttribute('data-action');
      if (action) {
        handleOrbAction(action);
      }
      e.stopPropagation(); // Prevent bubbling up to document
    });
  });
  
  console.log('✅ Orb visualization initialized');
    }
  });
  
  console.log('✨ Orb visualization initialized with click behavior');
}

// Toggle the radial menu around the orb
function toggleOrbMenu(forcedState) {
  const orbMenu = document.getElementById('orb-menu');
  const orbButton = document.getElementById('orb-button');
  
  if (!orbMenu || !orbButton) {
    console.error('Orb menu elements not found');
    return;
  }
  
  // If forcedState is provided, use it; otherwise toggle current state
  const newState = (forcedState !== undefined) 
    ? forcedState 
    : !orbMenu.classList.contains('active');
  
  if (newState) {
    orbMenu.classList.add('active');
    orbButton.classList.add('active');
    console.log('🔵 Orb menu opened');
  } else {
    orbMenu.classList.remove('active');
    orbButton.classList.remove('active');
    console.log('⚪ Orb menu closed');
  }
}

// Handle actions from the orb menu
function handleOrbAction(action) {
  console.log(`🔘 Orb action: ${action}`);
  
  // Get the orb interface element
  const orbInterface = document.getElementById('orb-interface');
  
  if (!orbInterface) {
    console.error('Orb interface not found');
    return showFallback('Missing orb interface element');
  }
  
  // Show the interface if it's not already visible
  if (!orbInterface.classList.contains('active')) {
    orbInterface.classList.add('active');
    orbInterface.style.display = 'block';
  }
  
  switch(action) {
    case 'dashboard':
    case 'chat':
    case 'memory':
    case 'projects':
      switchSection(action);
      break;
    
    // Special case for the orb button click (toggle interface)
    case 'toggle':
      if (orbInterface.classList.contains('active')) {
        orbInterface.classList.remove('active');
        setTimeout(() => {
          orbInterface.style.display = 'none';
        }, 300); // Match transition duration in CSS
      } else {
        orbInterface.classList.add('active');
        orbInterface.style.display = 'block';
        // Default to dashboard section if no last active section
        const lastSection = localStorage.getItem('minervaLastActiveSection') || 'dashboard';
        switchSection(lastSection);
      }
      break;
      
    default:
      console.warn(`Unknown orb action: ${action}`);
  }
  
  // Close the menu after an action
  toggleOrbMenu(false);
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
    // Only respond to keyboard shortcuts if not typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
      return;
    }
    
    // ALT + D: Dashboard
    if (e.altKey && e.key === 'd') {
      switchSection('dashboard');
    }
    
    // ALT + C: Chat
    if (e.altKey && e.key === 'c') {
      switchSection('chat');
    }
    
    // ALT + M: Memory
    if (e.altKey && e.key === 'm') {
      switchSection('memory');
    }
  });
}

// Toast notification system
let toastContainer = null;

function createToastContainer() {
  if (!toastContainer) {
    try {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toast-container';
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
    alert('Minerva UI Error: ' + msg);
  }
}
