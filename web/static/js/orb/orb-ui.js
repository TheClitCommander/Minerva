console.log("🔄 Initializing Minerva Orb UI...");

document.addEventListener("DOMContentLoaded", () => {
  const orb = document.getElementById("orb-container");
  if (!orb) return showFallback("Missing #orb-container");

  const interface = document.getElementById("orb-interface");
  if (!interface) return showFallback("Missing #orb-interface");

  const sections = ["dashboard", "chat", "memory"];
  let foundAll = true;

  for (let sec of sections) {
    if (!document.getElementById(`orb-${sec}`)) {
      console.warn(`Missing orb-${sec}`);
      foundAll = false;
    }
  }

  if (!foundAll) return showFallback("Missing one or more orb sections.");

  initOrb();
  setupKeyboardShortcuts();
  makeOrbDraggable();
});

function initOrb() {
  const buttons = document.querySelectorAll(".orb-nav-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;
      switchSection(target);
    });
  });
  
  // Add back button functionality to close sections and show orb
  const backButtons = document.querySelectorAll(".back-button, .close-section");
  backButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      hideAllSections();
      showOrb();
    });
  });
  
  // Add floating instruction message
  addInstructionMessage();
  
  console.log("✅ Orb UI ready.");
}

function switchSection(target) {
  // Hide all sections first
  hideAllSections();
  
  // Then show the selected one
  const selected = document.getElementById(`orb-${target}`);
  if (selected) {
    selected.style.display = "block";
    selected.classList.add("active");
    
    // Minimize the orb rather than hiding it completely
    minimizeOrb();
    
    console.log(`🔀 Switched to ${target}`);
  } else {
    console.warn(`No section found for '${target}'`);
  }
}

function hideAllSections() {
  const all = document.querySelectorAll(".orb-section");
  all.forEach((sec) => {
    sec.style.display = "none";
    sec.classList.remove("active");
  });
}

function minimizeOrb() {
  const orb = document.getElementById("orb-container");
  if (orb) {
    orb.classList.add("minimized");
    orb.classList.add("section-active");
    
    // Show instruction message
    showInstructionMessage();
  }
}

function showOrb() {
  const orb = document.getElementById("orb-container");
  if (orb) {
    orb.classList.remove("minimized");
    orb.classList.remove("section-active");
    
    // Hide instruction message
    hideInstructionMessage();
  }
}

function makeOrbDraggable() {
  const orb = document.getElementById("orb-container");
  if (!orb) return;
  
  let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
  
  orb.onmousedown = dragMouseDown;
  
  function dragMouseDown(e) {
    e = e || window.event;
    e.preventDefault();
    
    // Get the mouse cursor position at startup
    pos3 = e.clientX;
    pos4 = e.clientY;
    
    // Add dragging class
    orb.classList.add("dragging");
    
    document.onmouseup = closeDragElement;
    document.onmousemove = elementDrag;
  }
  
  function elementDrag(e) {
    e = e || window.event;
    e.preventDefault();
    
    // Calculate the new cursor position
    pos1 = pos3 - e.clientX;
    pos2 = pos4 - e.clientY;
    pos3 = e.clientX;
    pos4 = e.clientY;
    
    // Set the element's new position, keeping it on screen
    const newTop = Math.max(0, Math.min(window.innerHeight - orb.offsetHeight, orb.offsetTop - pos2));
    const newLeft = Math.max(0, Math.min(window.innerWidth - orb.offsetWidth, orb.offsetLeft - pos1));
    
    orb.style.top = newTop + "px";
    orb.style.left = newLeft + "px";
    orb.style.bottom = "auto";
    orb.style.right = "auto";
  }
  
  function closeDragElement() {
    // Stop moving when mouse button is released
    document.onmouseup = null;
    document.onmousemove = null;
    orb.classList.remove("dragging");
  }
}

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Space bar to toggle orb visibility
    if (e.code === "Space" && !isInputFocused()) {
      e.preventDefault();
      toggleOrbVisibility();
    }
    
    // Escape key to close active section
    if (e.code === "Escape") {
      hideAllSections();
      showOrb();
    }
  });
  
  function isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement.tagName === "INPUT" || 
           activeElement.tagName === "TEXTAREA" || 
           activeElement.isContentEditable;
  }
}

function toggleOrbVisibility() {
  const orb = document.getElementById("orb-container");
  if (!orb) return;
  
  const hasActiveSection = document.querySelector(".orb-section.active");
  
  if (hasActiveSection) {
    hideAllSections();
    showOrb();
  } else {
    // Default to chat if no section is active
    switchSection("chat");
  }
}

function addInstructionMessage() {
  // Create or get the instruction message element
  let instructionMsg = document.getElementById("instruction-message");
  
  if (!instructionMsg) {
    instructionMsg = document.createElement("div");
    instructionMsg.id = "instruction-message";
    instructionMsg.className = "instruction-message";
    instructionMsg.innerHTML = "Press <span class='key'>SPACE</span> to toggle Minerva Assistant";
    instructionMsg.addEventListener("click", toggleOrbVisibility);
    document.body.appendChild(instructionMsg);
  }
}

function showInstructionMessage() {
  const instructionMsg = document.getElementById("instruction-message");
  if (instructionMsg) {
    instructionMsg.classList.add("visible");
  }
}

function hideInstructionMessage() {
  const instructionMsg = document.getElementById("instruction-message");
  if (instructionMsg) {
    instructionMsg.classList.remove("visible");
  }
}

function showFallback(msg) {
  const fallback = document.createElement("div");
  fallback.style = "padding:2rem;color:white;background:#111;font-family:monospace";
  fallback.innerHTML = `<h2>⚠️ UI Failed</h2><p>${msg}</p>`;
  document.body.prepend(fallback);
}
