/**
 * Clean Orb UI - Stable Implementation
 * 
 * This is a complete rewrite that follows the Minerva Master Ruleset:
 * - Rule #1: Progressive Enhancement
 * - Rule #4: Fallback Interfaces
 */

// Wait for DOM to be fully loaded before initializing
document.addEventListener('DOMContentLoaded', () => {
  console.log("🔄 Initializing Minerva Orb UI (clean version)...");
  
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

  // Only proceed if all required sections exist
  if (!foundAll) {
    return showFallback("Missing one or more orb sections");
  }

  // Initialize the UI components
  initNav();
  console.log("✅ Orb UI ready");
});

// Initialize navigation between sections
function initNav() {
  const buttons = document.querySelectorAll(".orb-nav-btn");
  
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

// Switch between UI sections
function switchSection(target) {
  // Hide all sections
  const all = document.querySelectorAll(".orb-section");
  all.forEach((sec) => (sec.style.display = "none"));

  // Show the selected section
  const selected = document.getElementById(`orb-${target}`);
  if (selected) {
    selected.style.display = "block";
    console.log(`🔀 Switched to ${target}`);
    
    // Update active state on buttons
    document.querySelectorAll(".orb-nav-btn").forEach(btn => {
      if (btn.dataset.target === target) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
  } else {
    console.warn(`No section found for '${target}'`);
  }
}

// Show fallback UI when critical elements are missing
function showFallback(msg) {
  console.error(`Orb UI Error: ${msg}`);
  
  const fallback = document.createElement("div");
  fallback.style = "padding:2rem;color:white;background:#111;font-family:monospace;border-radius:8px;margin:20px;";
  fallback.innerHTML = `
    <h2>⚠️ UI Error</h2>
    <p>${msg}</p>
    <p>Please check the browser console for more information.</p>
  `;
  document.body.prepend(fallback);
}
