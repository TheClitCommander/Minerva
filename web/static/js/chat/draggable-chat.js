/**
 * Draggable Chat Module for Minerva
 * Allows users to move, minimize, and close the chat interface
 */

class DraggableChat {
  constructor(options = {}) {
    // Core elements
    this.chatContainer = options.container || document.getElementById('chat-container');
    this.chatHeader = options.header || document.querySelector('#chat-container .chat-header');
    this.chatBody = options.body || document.querySelector('#chat-container .chat-body');
    this.minimizeButton = options.minimizeButton || document.querySelector('#chat-container .btn-minimize');
    this.closeButton = options.closeButton || document.querySelector('#chat-container .btn-close');
    this.restoreButton = options.restoreButton || document.querySelector('#chat-container .btn-restore');
    
    // State
    this.isDragging = false;
    this.isMinimized = false;
    this.startX = 0;
    this.startY = 0;
    this.offsetX = 0;
    this.offsetY = 0;
    this.originalPos = { left: null, top: null, width: null, height: null };
    
    // Initialize if all required elements exist
    if (this.chatContainer && this.chatHeader) {
      this.init();
      console.log('✅ Draggable chat initialized');
    } else {
      console.error('Missing required chat elements', {
        container: !!this.chatContainer,
        header: !!this.chatHeader
      });
    }
  }
  
  /**
   * Initialize the draggable chat
   */
  init() {
    // Store original position
    const computedStyle = window.getComputedStyle(this.chatContainer);
    this.originalPos = {
      left: computedStyle.left,
      top: computedStyle.top,
      width: computedStyle.width,
      height: computedStyle.height
    };
    
    // Make sure the chat has the necessary styling
    this.chatContainer.style.position = 'absolute';
    
    // Create header controls if they don't exist
    this.ensureHeaderControls();
    
    // Add drag functionality
    this.chatHeader.addEventListener('mousedown', this.onDragStart.bind(this));
    document.addEventListener('mousemove', this.onDragMove.bind(this));
    document.addEventListener('mouseup', this.onDragEnd.bind(this));
    
    // Add minimize/close buttons if they exist
    if (this.minimizeButton) {
      this.minimizeButton.addEventListener('click', this.toggleMinimize.bind(this));
    }
    
    if (this.closeButton) {
      this.closeButton.addEventListener('click', this.closeChat.bind(this));
    }
    
    if (this.restoreButton) {
      this.restoreButton.addEventListener('click', this.restoreChat.bind(this));
    }
    
    // Load saved position from localStorage
    this.loadChatPosition();
  }
  
  /**
   * Create header controls if they don't exist
   */
  ensureHeaderControls() {
    // Only proceed if we have a header
    if (!this.chatHeader) return;
    
    // Create controls container if it doesn't exist
    let controlsContainer = this.chatHeader.querySelector('.chat-controls');
    
    if (!controlsContainer) {
      controlsContainer = document.createElement('div');
      controlsContainer.className = 'chat-controls';
      this.chatHeader.appendChild(controlsContainer);
    }
    
    // Create minimize button if it doesn't exist
    if (!this.minimizeButton) {
      this.minimizeButton = document.createElement('button');
      this.minimizeButton.className = 'btn-minimize';
      this.minimizeButton.innerHTML = '<i class="fas fa-minus"></i>';
      this.minimizeButton.title = 'Minimize Chat';
      controlsContainer.appendChild(this.minimizeButton);
      
      // Add event listener
      this.minimizeButton.addEventListener('click', this.toggleMinimize.bind(this));
    }
    
    // Create restore button if it doesn't exist
    if (!this.restoreButton) {
      this.restoreButton = document.createElement('button');
      this.restoreButton.className = 'btn-restore';
      this.restoreButton.innerHTML = '<i class="fas fa-expand"></i>';
      this.restoreButton.title = 'Restore Chat';
      this.restoreButton.style.display = 'none'; // Hidden by default
      controlsContainer.appendChild(this.restoreButton);
      
      // Add event listener
      this.restoreButton.addEventListener('click', this.toggleMinimize.bind(this));
    }
    
    // Create close button if it doesn't exist
    if (!this.closeButton) {
      this.closeButton = document.createElement('button');
      this.closeButton.className = 'btn-close';
      this.closeButton.innerHTML = '<i class="fas fa-times"></i>';
      this.closeButton.title = 'Close Chat';
      controlsContainer.appendChild(this.closeButton);
      
      // Add event listener
      this.closeButton.addEventListener('click', this.closeChat.bind(this));
    }
    
    // Add styles for controls
    const style = document.createElement('style');
    style.textContent = `
      .chat-controls {
        display: flex;
        align-items: center;
        margin-left: auto;
      }
      .chat-controls button {
        background: none;
        border: none;
        font-size: 14px;
        color: #ccc;
        cursor: pointer;
        padding: 4px 8px;
        margin-left: 5px;
        transition: color 0.2s ease;
      }
      .chat-controls button:hover {
        color: white;
      }
      #chat-container .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: grab;
        user-select: none;
      }
      #chat-container.minimized .chat-body {
        display: none;
      }
      #chat-container.minimized {
        height: auto !important;
        width: 250px !important;
      }
    `;
    document.head.appendChild(style);
    
    // Update chat header layout
    this.chatHeader.style.display = 'flex';
    this.chatHeader.style.justifyContent = 'space-between';
    this.chatHeader.style.alignItems = 'center';
    this.chatHeader.style.cursor = 'grab';
    this.chatHeader.style.userSelect = 'none';
  }
  
  /**
   * Start dragging the chat window
   */
  onDragStart(e) {
    // Only allow dragging from the header
    if (e.target.closest('.chat-controls')) {
      return;
    }
    
    this.isDragging = true;
    this.startX = e.clientX;
    this.startY = e.clientY;
    
    // Get current position
    const rect = this.chatContainer.getBoundingClientRect();
    this.offsetX = this.startX - rect.left;
    this.offsetY = this.startY - rect.top;
    
    // Change cursor style
    this.chatHeader.style.cursor = 'grabbing';
    
    // Prevent text selection during drag
    e.preventDefault();
  }
  
  /**
   * Handle the chat window dragging
   */
  onDragMove(e) {
    if (!this.isDragging) return;
    
    const x = e.clientX - this.offsetX;
    const y = e.clientY - this.offsetY;
    
    // Keep within window bounds
    const maxX = window.innerWidth - this.chatContainer.offsetWidth;
    const maxY = window.innerHeight - this.chatContainer.offsetHeight;
    
    const boundedX = Math.max(0, Math.min(x, maxX));
    const boundedY = Math.max(0, Math.min(y, maxY));
    
    this.chatContainer.style.left = `${boundedX}px`;
    this.chatContainer.style.top = `${boundedY}px`;
    
    // Save position to localStorage (debounced)
    clearTimeout(this.saveTimeout);
    this.saveTimeout = setTimeout(() => {
      this.saveChatPosition();
    }, 200);
  }
  
  /**
   * End the dragging operation
   */
  onDragEnd(e) {
    if (!this.isDragging) return;
    
    this.isDragging = false;
    this.chatHeader.style.cursor = 'grab';
    
    // Save final position
    this.saveChatPosition();
  }
  
  /**
   * Toggle minimize state
   */
  toggleMinimize() {
    if (this.isMinimized) {
      // Restore
      this.chatContainer.classList.remove('minimized');
      this.chatBody.style.display = 'block';
      this.minimizeButton.style.display = 'block';
      this.restoreButton.style.display = 'none';
      
      // Restore previous dimensions
      if (this.preminimizedState) {
        this.chatContainer.style.width = this.preminimizedState.width;
        this.chatContainer.style.height = this.preminimizedState.height;
      }
    } else {
      // Minimize
      this.chatContainer.classList.add('minimized');
      this.chatBody.style.display = 'none';
      this.minimizeButton.style.display = 'none';
      this.restoreButton.style.display = 'block';
      
      // Save current dimensions
      this.preminimizedState = {
        width: this.chatContainer.style.width,
        height: this.chatContainer.style.height
      };
      
      // Adjust size to just show header
      this.chatContainer.style.width = '250px';
      this.chatContainer.style.height = 'auto';
    }
    
    this.isMinimized = !this.isMinimized;
    
    // Save state to localStorage
    localStorage.setItem('minerva_chat_minimized', this.isMinimized ? 'true' : 'false');
  }
  
  /**
   * Close the chat window
   */
  closeChat() {
    this.chatContainer.style.display = 'none';
    localStorage.setItem('minerva_chat_visible', 'false');
  }
  
  /**
   * Restore the chat window
   */
  restoreChat() {
    // Reset to original position
    for (const [key, value] of Object.entries(this.originalPos)) {
      if (value !== null) {
        this.chatContainer.style[key] = value;
      }
    }
    
    // Show chat
    this.chatContainer.style.display = 'block';
    
    // If minimized, restore full view
    if (this.isMinimized) {
      this.toggleMinimize();
    }
    
    localStorage.setItem('minerva_chat_visible', 'true');
  }
  
  /**
   * Save chat position to localStorage
   */
  saveChatPosition() {
    const position = {
      left: this.chatContainer.style.left,
      top: this.chatContainer.style.top,
      width: this.chatContainer.style.width,
      height: this.chatContainer.style.height
    };
    
    localStorage.setItem('minerva_chat_position', JSON.stringify(position));
  }
  
  /**
   * Load chat position from localStorage
   */
  loadChatPosition() {
    // Restore visibility state
    const visible = localStorage.getItem('minerva_chat_visible');
    if (visible === 'false') {
      this.chatContainer.style.display = 'none';
    }
    
    // Restore minimized state
    const minimized = localStorage.getItem('minerva_chat_minimized');
    if (minimized === 'true' && !this.isMinimized) {
      this.toggleMinimize();
    }
    
    // Restore position
    try {
      const savedPosition = JSON.parse(localStorage.getItem('minerva_chat_position'));
      if (savedPosition) {
        for (const [key, value] of Object.entries(savedPosition)) {
          if (value) {
            this.chatContainer.style[key] = value;
          }
        }
      }
    } catch (e) {
      console.error('Error loading chat position', e);
    }
  }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  window.draggableChat = new DraggableChat();
});
