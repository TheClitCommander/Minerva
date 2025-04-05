/**
 * Minerva Markdown Formatter
 * Provides real-time Markdown formatting and preview functionality for chat messages
 */

const MarkdownFormatter = (function() {
    // DOM references - will be populated on initialization
    let chatInput = null;
    let previewContainer = null;
    let formattingToolbar = null;
    let previewToggleButton = null;
    
    // State management
    let isPreviewEnabled = false;
    let isToolbarVisible = false;
    let typingTimer = null;
    const typingDelay = 300; // ms to wait after typing stops before updating preview

    /**
     * Initialize the markdown formatter
     * @param {Object} options Configuration options
     */
    function initialize(options = {}) {
        // Set default options
        const config = {
            inputSelector: '#chat-input',
            previewContainerId: 'markdown-preview-container',
            toolbarContainerId: 'formatting-toolbar',
            previewDelay: 300,
            ...options
        };
        
        // Find or create required elements
        setupElements(config);
        
        // Initialize the Marked.js library with our preferred settings
        initializeMarkedLibrary();
        
        // Set up event listeners
        setupEventListeners();
        
        console.log('Markdown formatter initialized');
    }
    
    /**
     * Setup required DOM elements for markdown functionality
     */
    function setupElements(config) {
        // Get the chat input element
        chatInput = document.querySelector(config.inputSelector);
        if (!chatInput) {
            console.error('Chat input element not found!');
            return;
        }
        
        // Create preview container if it doesn't exist
        if (!document.getElementById(config.previewContainerId)) {
            previewContainer = document.createElement('div');
            previewContainer.id = config.previewContainerId;
            previewContainer.className = 'markdown-preview-container hidden';
            
            // Insert preview container after the chat input
            chatInput.parentNode.insertBefore(previewContainer, chatInput.nextSibling);
        } else {
            previewContainer = document.getElementById(config.previewContainerId);
        }
        
        // Create formatting toolbar if it doesn't exist
        if (!document.getElementById(config.toolbarContainerId)) {
            formattingToolbar = document.createElement('div');
            formattingToolbar.id = config.toolbarContainerId;
            formattingToolbar.className = 'formatting-toolbar hidden';
            
            // Create toolbar buttons
            const buttons = [
                { icon: 'bold', title: 'Bold', markdownSyntax: '**', example: 'text' },
                { icon: 'italic', title: 'Italic', markdownSyntax: '*', example: 'text' },
                { icon: 'code', title: 'Code', markdownSyntax: '`', example: 'code' },
                { icon: 'list-ul', title: 'Bulleted List', markdownSyntax: '- ', isBlock: true },
                { icon: 'list-ol', title: 'Numbered List', markdownSyntax: '1. ', isBlock: true },
                { icon: 'link', title: 'Link', markdownSyntax: '[', example: 'link text](https://example.com)' }
            ];
            
            buttons.forEach(button => {
                const buttonElement = document.createElement('button');
                buttonElement.type = 'button';
                buttonElement.className = 'formatting-button';
                buttonElement.title = button.title;
                buttonElement.innerHTML = `<i class="fas fa-${button.icon}"></i>`;
                buttonElement.dataset.syntax = button.markdownSyntax;
                buttonElement.dataset.example = button.example || '';
                buttonElement.dataset.isBlock = button.isBlock || false;
                
                buttonElement.addEventListener('click', () => {
                    insertMarkdownSyntax(button.markdownSyntax, button.example, button.isBlock);
                });
                
                formattingToolbar.appendChild(buttonElement);
            });
            
            // Add preview toggle button
            previewToggleButton = document.createElement('button');
            previewToggleButton.type = 'button';
            previewToggleButton.className = 'formatting-button preview-toggle';
            previewToggleButton.title = 'Toggle Preview';
            previewToggleButton.innerHTML = '<i class="fas fa-eye"></i>';
            previewToggleButton.addEventListener('click', togglePreview);
            formattingToolbar.appendChild(previewToggleButton);
            
            // Insert toolbar before the chat input
            chatInput.parentNode.insertBefore(formattingToolbar, chatInput);
        } else {
            formattingToolbar = document.getElementById(config.toolbarContainerId);
        }
    }
    
    /**
     * Initialize the Marked.js library with secure and customized settings
     */
    function initializeMarkedLibrary() {
        if (typeof marked !== 'undefined') {
            // Configure marked with secure defaults and our preferred settings
            marked.setOptions({
                gfm: true, // GitHub Flavored Markdown
                breaks: true, // Add <br> on single line breaks
                sanitize: false, // We'll use DOMPurify for sanitization
                smartLists: true,
                smartypants: true,
                highlight: function(code, lang) {
                    // Simple syntax highlighting
                    return code.replace(/([a-z]+)(\s*=)/g, '<span class="syntax-key">$1</span>$2')
                        .replace(/(".*?")/g, '<span class="syntax-string">$1</span>');
                }
            });
        } else {
            console.warn('Marked.js library not found. Markdown preview will be disabled.');
        }
    }
    
    /**
     * Set up event listeners for markdown functionality
     */
    function setupEventListeners() {
        if (!chatInput) return;
        
        // Input event for live preview
        chatInput.addEventListener('input', debounceUpdatePreview);
        
        // Focus/blur events to show/hide toolbar
        chatInput.addEventListener('focus', () => {
            if (formattingToolbar) {
                formattingToolbar.classList.remove('hidden');
                isToolbarVisible = true;
            }
        });
        
        // Don't hide toolbar immediately when clicking on its buttons
        if (formattingToolbar) {
            formattingToolbar.addEventListener('mousedown', (e) => {
                e.preventDefault(); // Prevent focus loss on chatInput
            });
        }
        
        // Hide toolbar when clicking outside
        document.addEventListener('click', (e) => {
            if (isToolbarVisible && 
                e.target !== chatInput && 
                e.target !== formattingToolbar && 
                !formattingToolbar.contains(e.target)) {
                formattingToolbar.classList.add('hidden');
                isToolbarVisible = false;
                
                // Also hide preview if clicking elsewhere
                if (isPreviewEnabled && previewContainer) {
                    previewContainer.classList.add('hidden');
                    isPreviewEnabled = false;
                    if (previewToggleButton) {
                        previewToggleButton.innerHTML = '<i class="fas fa-eye"></i>';
                    }
                }
            }
        });
    }
    
    /**
     * Debounce the preview update to avoid performance issues during typing
     */
    function debounceUpdatePreview() {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(updatePreview, typingDelay);
    }
    
    /**
     * Update the markdown preview
     */
    function updatePreview() {
        if (!isPreviewEnabled || !previewContainer || !chatInput) return;
        
        const text = chatInput.value.trim();
        
        if (text) {
            let html = '';
            
            // Use marked.js if available
            if (typeof marked === 'function') {
                html = marked(text);
                
                // Use DOMPurify if available
                if (typeof DOMPurify === 'function') {
                    html = DOMPurify.sanitize(html);
                }
            } else {
                // Simple fallback formatting
                html = text
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/`(.*?)`/g, '<code>$1</code>')
                    .replace(/\n/g, '<br>');
            }
            
            previewContainer.innerHTML = html;
            previewContainer.classList.remove('hidden');
        } else {
            previewContainer.classList.add('hidden');
        }
    }
    
    /**
     * Toggle the markdown preview visibility
     */
    function togglePreview() {
        if (!previewContainer || !previewToggleButton) return;
        
        isPreviewEnabled = !isPreviewEnabled;
        
        if (isPreviewEnabled) {
            updatePreview();
            previewToggleButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
        } else {
            previewContainer.classList.add('hidden');
            previewToggleButton.innerHTML = '<i class="fas fa-eye"></i>';
        }
    }
    
    /**
     * Insert markdown syntax into the chat input at the current cursor position
     * @param {string} syntax The markdown syntax to insert
     * @param {string} example Example text to insert between syntax markers
     * @param {boolean} isBlock Whether this is a block-level element (e.g., list item)
     */
    function insertMarkdownSyntax(syntax, example = '', isBlock = false) {
        if (!chatInput) return;
        
        const startPos = chatInput.selectionStart;
        const endPos = chatInput.selectionEnd;
        const text = chatInput.value;
        let selectedText = text.substring(startPos, endPos);
        let newText = '';
        
        if (selectedText) {
            // User has selected text, apply formatting to it
            if (isBlock) {
                // For block elements like lists, apply to each line
                const lines = selectedText.split('\n');
                selectedText = lines.map(line => syntax + line).join('\n');
                newText = text.substring(0, startPos) + selectedText + text.substring(endPos);
            } else if (syntax === '[') {
                // Special case for links
                newText = text.substring(0, startPos) + '[' + selectedText + '](url)' + text.substring(endPos);
            } else {
                // Inline formatting
                newText = text.substring(0, startPos) + syntax + selectedText + syntax + text.substring(endPos);
            }
        } else {
            // No selection, insert example syntax
            if (isBlock) {
                newText = text.substring(0, startPos) + syntax + text.substring(endPos);
            } else if (syntax === '[') {
                newText = text.substring(0, startPos) + '[' + example + text.substring(endPos);
            } else {
                newText = text.substring(0, startPos) + syntax + example + syntax + text.substring(endPos);
            }
        }
        
        // Update input value and reposition cursor
        chatInput.value = newText;
        
        // Set cursor position
        if (selectedText) {
            // If there was a selection, place cursor at the end of the formatted text
            chatInput.setSelectionRange(startPos + newText.length - text.length + selectedText.length, 
                                        startPos + newText.length - text.length + selectedText.length);
        } else {
            // If no selection, place cursor between syntax markers or after prefix for blocks
            if (isBlock) {
                chatInput.setSelectionRange(startPos + syntax.length, startPos + syntax.length);
            } else if (syntax === '[') {
                // For links, place cursor in the URL position
                chatInput.setSelectionRange(startPos + example.length + 2, startPos + example.length + 5);
            } else {
                chatInput.setSelectionRange(startPos + syntax.length, startPos + syntax.length + example.length);
            }
        }
        
        // Focus the input and trigger preview update
        chatInput.focus();
        debounceUpdatePreview();
    }
    
    /**
     * Format a message with markdown
     * @param {string} message The message to format
     * @returns {string} The formatted HTML
     */
    function formatMessage(message) {
        if (!message) return '';
        
        // Use marked.js if available
        if (typeof marked === 'function') {
            let html = marked(message);
            
            // Use DOMPurify if available
            if (typeof DOMPurify === 'function') {
                html = DOMPurify.sanitize(html);
            }
            
            return html;
        }
        
        // Simple fallback formatting if marked.js is not available
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }
    
    // Public API
    return {
        initialize,
        formatMessage,
        togglePreview,
        insertMarkdownSyntax
    };
})();

// Initialize the formatter when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // We'll initialize this in minerva-chat.js
});
