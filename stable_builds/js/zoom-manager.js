/**
 * Minerva Zoom Manager
 * Provides centralized control of zoom functionality across both 2D and 3D elements
 * Ensures consistent zoom behavior between 0.1 and 1.0 in 0.1 increments
 */

class ZoomManager {
  constructor(options = {}) {
    // Core zoom settings
    this.zoomLevel = options.initialZoom || 1.0;
    this.MIN_ZOOM = options.minZoom || 0.1;
    this.MAX_ZOOM = options.maxZoom || 1.0;
    this.ZOOM_STEP = options.zoomStep || 0.1;
    
    // Elements to control
    this.spaceBackground = options.spaceBackground || document.getElementById('space-background');
    this.zoomLevelIndicator = options.zoomLevelIndicator || document.getElementById('zoom-level-indicator');
    this.zoomInButton = options.zoomInButton || document.getElementById('zoom-in');
    this.zoomOutButton = options.zoomOutButton || document.getElementById('zoom-out');
    
    // 3D camera if available
    this.camera = options.camera || null;
    this.controls = options.controls || null;
    
    // Subscriber callbacks for zoom changes
    this.subscribers = [];
    
    // Event listeners
    this.setupEventListeners();
    
    // Initial update
    this.updateZoomDisplay();
    
    console.log(`ZoomManager initialized with zoom level: ${this.zoomLevel}`);
  }
  
  setupEventListeners() {
    // Set up zoom in button
    if (this.zoomInButton) {
      this.zoomInButton.addEventListener('click', () => {
        this.zoomIn();
        console.log(`Zoom in clicked: ${this.zoomLevel}`);
      });
    }
    
    // Set up zoom out button
    if (this.zoomOutButton) {
      this.zoomOutButton.addEventListener('click', () => {
        this.zoomOut();
        console.log(`Zoom out clicked: ${this.zoomLevel}`);
      });
    }
    
    // Add keyboard shortcuts for zoom
    document.addEventListener('keydown', (e) => {
      if (e.key === '+' || e.key === '=') {
        this.zoomIn();
      } else if (e.key === '-' || e.key === '_') {
        this.zoomOut();
      }
    });
  }
  
  // Zoom in - decrease zoom level (making objects appear larger)
  zoomIn() {
    if (this.zoomLevel < this.MAX_ZOOM) {
      // Increment by exactly the zoom step
      this.zoomLevel += this.ZOOM_STEP;
      // Round to one decimal place to avoid floating point issues
      this.zoomLevel = Math.round(this.zoomLevel * 10) / 10;
      
      // Make sure we don't exceed max zoom
      this.zoomLevel = Math.min(this.zoomLevel, this.MAX_ZOOM);
      
      this.updateZoom();
      return true;
    }
    return false;
  }
  
  // Zoom out - increase zoom level (making objects appear smaller)
  zoomOut() {
    if (this.zoomLevel > this.MIN_ZOOM) {
      // Decrement by exactly the zoom step
      this.zoomLevel -= this.ZOOM_STEP;
      // Round to one decimal place to avoid floating point issues
      this.zoomLevel = Math.round(this.zoomLevel * 10) / 10;
      
      // Make sure we don't go below min zoom
      this.zoomLevel = Math.max(this.zoomLevel, this.MIN_ZOOM);
      
      this.updateZoom();
      return true;
    }
    return false;
  }
  
  // Set zoom to a specific level
  setZoom(level) {
    if (level >= this.MIN_ZOOM && level <= this.MAX_ZOOM) {
      this.zoomLevel = Math.round(level * 10) / 10; // Ensure proper decimal precision
      this.updateZoom();
      return true;
    }
    return false;
  }
  
  // Update zoom visuals and notify subscribers
  updateZoom() {
    // Update 2D space background if available
    if (this.spaceBackground) {
      this.spaceBackground.style.transformOrigin = 'center';
      this.spaceBackground.style.transform = `scale(${this.zoomLevel})`;
      console.log(`Applied 2D zoom: scale(${this.zoomLevel})`);
    }
    
    // Update 3D camera if available
    if (this.camera) {
      // For perspective camera, update position.z based on zoom level
      // This assumes original z position was calibrated for zoom level 1.0
      const baseZ = 5; // Base Z position at zoom 1.0
      this.camera.position.z = baseZ / this.zoomLevel;
      
      if (this.controls) {
        // Update orbit controls if available
        this.controls.update();
      }
      
      console.log(`Applied 3D zoom: camera z=${this.camera.position.z}`);
    }
    
    // Update the zoom level indicator if available
    this.updateZoomDisplay();
    
    // Notify all zoom subscribers
    this.notifySubscribers();
  }
  
  // Update the zoom level text display
  updateZoomDisplay() {
    if (this.zoomLevelIndicator) {
      let zoomText = "Zoomed Out";
      
      if (this.zoomLevel === 1.0) {
        zoomText = "Normal View";
      } else if (this.zoomLevel > 0.7) {
        zoomText = "Zoomed In";
      } else if (this.zoomLevel > 0.4) {
        zoomText = "Distant View";
      } else {
        zoomText = "Far View";
      }
      
      this.zoomLevelIndicator.textContent = `${zoomText} (${this.zoomLevel.toFixed(1)}x)`;
      
      // Show zoom level indicator with fade out effect
      this.zoomLevelIndicator.style.opacity = '1';
      clearTimeout(this.fadeTimeout);
      this.fadeTimeout = setTimeout(() => {
        this.zoomLevelIndicator.style.opacity = '0';
      }, 2000);
    }
  }
  
  // Register a function to be called when zoom changes
  subscribe(callback) {
    if (typeof callback === 'function' && !this.subscribers.includes(callback)) {
      this.subscribers.push(callback);
      return true;
    }
    return false;
  }
  
  // Remove a subscriber
  unsubscribe(callback) {
    const index = this.subscribers.indexOf(callback);
    if (index !== -1) {
      this.subscribers.splice(index, 1);
      return true;
    }
    return false;
  }
  
  // Call all subscriber callbacks with current zoom level
  notifySubscribers() {
    this.subscribers.forEach(callback => {
      try {
        callback(this.zoomLevel);
      } catch (error) {
        console.error('Error in zoom subscriber:', error);
      }
    });
  }
  
  // Get current zoom level
  getZoomLevel() {
    return this.zoomLevel;
  }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { ZoomManager };
}
