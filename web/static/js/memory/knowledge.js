/**
 * Minerva AI - Knowledge Management JavaScript
 * 
 * This file contains the JavaScript functionality for the knowledge management page.
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Knowledge Management interface initialized');
    
    // Initialize event listeners
    setupSearchForm();
    setupUploadForm();
    setupDocumentActions();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

/**
 * Set up knowledge search form
 */
function setupSearchForm() {
    const searchForm = document.getElementById('knowledge-search-form');
    const activeFilters = document.getElementById('active-filters');
    const addFilterBtn = document.getElementById('add-filter');
    
    // Current filters
    const filters = {};
    
    // Add filter button
    if (addFilterBtn) {
        addFilterBtn.addEventListener('click', function() {
            const keyInput = document.getElementById('filter-key');
            const valueInput = document.getElementById('filter-value');
            
            const key = keyInput.value.trim();
            const value = valueInput.value.trim();
            
            if (key && value) {
                addFilter(key, value);
                keyInput.value = '';
                valueInput.value = '';
                keyInput.focus();
            }
        });
    }
    
    // Add filter function
    function addFilter(key, value) {
        filters[key] = value;
        updateFiltersDisplay();
    }
    
    // Update filters display
    function updateFiltersDisplay() {
        activeFilters.innerHTML = '';
        
        for (const [key, value] of Object.entries(filters)) {
            const filterBadge = document.createElement('div');
            filterBadge.className = 'badge bg-secondary d-flex align-items-center';
            filterBadge.innerHTML = `
                <span>${key}: ${value}</span>
                <button class="btn-close btn-close-white ms-2" 
                        aria-label="Remove" data-key="${key}"></button>
            `;
            activeFilters.appendChild(filterBadge);
            
            // Add remove event listener
            const closeBtn = filterBadge.querySelector('.btn-close');
            closeBtn.addEventListener('click', function() {
                const key = this.getAttribute('data-key');
                delete filters[key];
                updateFiltersDisplay();
            });
        }
    }
    
    // Search form submission
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('search-query').value.trim();
            const limit = parseInt(document.getElementById('search-limit').value);
            
            if (query) {
                searchKnowledge(query, limit, filters);
            }
        });
    }
    
    // Search knowledge function
    function searchKnowledge(query, limit, filters) {
        const searchResultsContainer = document.getElementById('search-results');
        
        // Show loading indicator
        searchResultsContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Searching knowledge base...</p>
            </div>
        `;
        
        // Make API request
        fetch('/api/knowledge/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: limit,
                filters: Object.keys(filters).length > 0 ? filters : null
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                displaySearchResults(data.results);
            } else {
                searchResultsContainer.innerHTML = `
                    <div class="text-center text-muted py-5">
                        <i class="fas fa-search fa-3x mb-3"></i>
                        <p>No results found for "${query}".</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error searching knowledge:', error);
            searchResultsContainer.innerHTML = `
                <div class="text-center text-danger py-5">
                    <i class="fas fa-exclamation-circle fa-3x mb-3"></i>
                    <p>Error searching knowledge base. Please try again.</p>
                </div>
            `;
        });
    }
    
    // Display search results
    function displaySearchResults(results) {
        const searchResultsContainer = document.getElementById('search-results');
        
        // Create results HTML
        let resultsHtml = '<div class="list-group">';
        
        results.forEach((result, index) => {
            const metadata = result.metadata || {};
            let metadataHtml = '';
            
            for (const [key, value] of Object.entries(metadata)) {
                metadataHtml += `<span class="badge bg-secondary me-1">${key}: ${value}</span>`;
            }
            
            resultsHtml += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between mb-2">
                        <h5 class="mb-1">Result ${index + 1}</h5>
                        <small>Document ID: ${result.document_id}</small>
                    </div>
                    <div class="mb-2">
                        <div class="d-flex align-items-center mb-1">
                            <div class="me-2">Relevance:</div>
                            <div class="progress flex-grow-1" style="height: 8px;">
                                <div class="progress-bar" role="progressbar" 
                                     style="width: ${Math.round(result.similarity * 100)}%;" 
                                     aria-valuenow="${Math.round(result.similarity * 100)}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100"></div>
                            </div>
                            <div class="ms-2">${Math.round(result.similarity * 100)}%</div>
                        </div>
                        ${metadataHtml ? `<div class="mb-2">${metadataHtml}</div>` : ''}
                    </div>
                    <p class="mb-1">
                        <pre class="bg-light p-3 rounded">${escapeHtml(result.content)}</pre>
                    </p>
                </div>
            `;
        });
        
        resultsHtml += '</div>';
        searchResultsContainer.innerHTML = resultsHtml;
    }
}

/**
 * Set up document upload form
 */
function setupUploadForm() {
    const uploadForm = document.getElementById('document-upload-form');
    const addMetadataBtn = document.getElementById('add-metadata');
    const metadataContainer = document.getElementById('document-metadata');
    
    // Current metadata
    const metadata = {};
    
    // Add metadata button
    if (addMetadataBtn) {
        addMetadataBtn.addEventListener('click', function() {
            const keyInput = document.getElementById('metadata-key');
            const valueInput = document.getElementById('metadata-value');
            
            const key = keyInput.value.trim();
            const value = valueInput.value.trim();
            
            if (key && value) {
                addMetadata(key, value);
                keyInput.value = '';
                valueInput.value = '';
                keyInput.focus();
            }
        });
    }
    
    // Add metadata function
    function addMetadata(key, value) {
        metadata[key] = value;
        updateMetadataDisplay();
    }
    
    // Update metadata display
    function updateMetadataDisplay() {
        metadataContainer.innerHTML = '';
        
        for (const [key, value] of Object.entries(metadata)) {
            const metadataBadge = document.createElement('div');
            metadataBadge.className = 'badge bg-info d-flex align-items-center';
            metadataBadge.innerHTML = `
                <span>${key}: ${value}</span>
                <button class="btn-close btn-close-white ms-2" 
                        aria-label="Remove" data-key="${key}"></button>
            `;
            metadataContainer.appendChild(metadataBadge);
            
            // Add remove event listener
            const closeBtn = metadataBadge.querySelector('.btn-close');
            closeBtn.addEventListener('click', function() {
                const key = this.getAttribute('data-key');
                delete metadata[key];
                updateMetadataDisplay();
            });
        }
    }
    
    // Upload form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('document-file');
            
            if (fileInput.files.length === 0) {
                showNotification('Please select a file to upload', 'warning');
                return;
            }
            
            uploadDocument(fileInput.files[0], metadata);
        });
    }
    
    // Upload document function
    function uploadDocument(file, metadata) {
        // Create FormData
        const formData = new FormData();
        formData.append('document', file);
        
        // Add metadata
        if (Object.keys(metadata).length > 0) {
            formData.append('metadata', JSON.stringify(metadata));
        }
        
        // Show loading
        showNotification('Uploading document...', 'info');
        
        // Make API request
        fetch('/api/knowledge/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // Reset form
                uploadForm.reset();
                Object.keys(metadata).forEach(key => delete metadata[key]);
                updateMetadataDisplay();
                // Refresh documents list
                refreshDocumentsList();
            } else {
                showNotification(data.error || 'Upload failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error uploading document:', error);
            showNotification('Error uploading document. Please try again.', 'error');
        });
    }
}

/**
 * Set up document action buttons
 */
function setupDocumentActions() {
    const refreshBtn = document.getElementById('refresh-documents');
    const deleteModal = new bootstrap.Modal(document.getElementById('delete-document-modal'));
    let documentToDelete = null;
    
    // Refresh documents button
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshDocumentsList();
        });
    }
    
    // Setup delete buttons (need to be re-attached after refresh)
    setupDeleteButtons();
    
    function setupDeleteButtons() {
        document.querySelectorAll('.delete-document').forEach(button => {
            button.addEventListener('click', function() {
                documentToDelete = this.getAttribute('data-document-id');
                deleteModal.show();
            });
        });
    }
    
    // Confirm delete button
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function() {
            if (documentToDelete) {
                deleteDocument(documentToDelete);
                deleteModal.hide();
            }
        });
    }
    
    // Delete document function
    function deleteDocument(documentId) {
        fetch(`/api/knowledge/documents/${documentId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                // Remove from table
                const row = document.querySelector(`tr[data-document-id="${documentId}"]`);
                if (row) {
                    row.remove();
                }
            } else {
                showNotification(data.error || 'Deletion failed', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting document:', error);
            showNotification('Error deleting document. Please try again.', 'error');
        });
    }
    
    // Refresh documents list function
    window.refreshDocumentsList = function() {
        const tableBody = document.querySelector('#documents-table tbody');
        
        // Show loading
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-3">
                    <div class="spinner-border spinner-border-sm text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <span class="ms-2">Loading documents...</span>
                </td>
            </tr>
        `;
        
        // Make API request
        fetch('/api/knowledge/documents')
        .then(response => response.json())
        .then(data => {
            if (data.documents && Array.isArray(data.documents)) {
                if (data.documents.length === 0) {
                    tableBody.innerHTML = `
                        <tr>
                            <td colspan="4" class="text-center py-3 text-muted">
                                <i class="fas fa-info-circle me-2"></i>No documents found.
                            </td>
                        </tr>
                    `;
                } else {
                    tableBody.innerHTML = '';
                    data.documents.forEach(doc => {
                        let metadataHtml = '';
                        if (doc.metadata) {
                            for (const [key, value] of Object.entries(doc.metadata)) {
                                metadataHtml += `
                                    <span class="badge bg-secondary">${key}: ${value}</span> 
                                `;
                            }
                        }
                        
                        const row = document.createElement('tr');
                        row.setAttribute('data-document-id', doc.document_id);
                        row.innerHTML = `
                            <td>${doc.filename}</td>
                            <td>${formatDate(doc.added_at)}</td>
                            <td>${metadataHtml}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger delete-document" 
                                        data-document-id="${doc.document_id}">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </td>
                        `;
                        tableBody.appendChild(row);
                    });
                    
                    // Re-attach delete buttons
                    setupDeleteButtons();
                }
            } else {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-3 text-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>Error loading documents.
                        </td>
                    </tr>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading documents:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-3 text-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>Error loading documents.
                    </td>
                </tr>
            `;
        });
    };
}

/**
 * Format ISO date string to readable format
 */
function formatDate(isoString) {
    try {
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch (e) {
        return isoString;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
