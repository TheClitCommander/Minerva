# Minerva Server Fixes

This document summarizes the fixes applied to the Minerva server to resolve connectivity, import, and stability issues.

## Core Issues Fixed

### 1. MultiAICoordinator Import Issues

**Problem:** The coordinator instance defined in `multi_ai_coordinator.py` was not being properly recognized when imported in `server.py`.

**Fixes Applied:**
- Enhanced the coordinator export in `multi_ai_coordinator.py` with clearer logging
- Improved the import logic in `server.py` to try multiple import patterns
- Updated `web/__init__.py` to properly export the coordinator at the package level
- Added Python path modifications to ensure consistent imports

### 2. Socket.IO Protocol Mismatch

**Problem:** Socket.IO client and server were using incompatible versions or settings.

**Fixes Applied:**
- Updated Socket.IO client configuration in HTML with explicit compatibility settings
- Modified Socket.IO server initialization to ensure compatibility with client v4.7.4
- Added multiple event handlers for more robust message sending/receiving
- Enhanced error handling for Socket.IO connections

### 3. Server Stability Issues

**Problem:** The server would terminate unexpectedly without clear error messages.

**Fixes Applied:**
- Created a robust startup script with proper error handling and dependency checks
- Added better logging throughout the server
- Implemented graceful error handling for critical components
- Added a diagnostic script to verify server dependencies and configurations

## New Files Added

1. **start_minerva_server.sh** - A comprehensive server startup script with:
   - Dependency checks
   - Environment setup
   - Error handling
   - Logging configuration

2. **test_minerva_fixes.sh** - A diagnostic script to verify:
   - Python dependency installation
   - MultiAICoordinator import functionality
   - Socket.IO version compatibility
   - Server script integrity

## Modified Files

1. **web/multi_ai_coordinator.py** - Improved coordinator initialization and export
2. **web/__init__.py** - Enhanced package initialization for better imports
3. **server.py** - Improved import logic and Socket.IO configuration
4. **web/minerva-portal.html** - Updated Socket.IO client setup and event handling

## How to Use

1. **Run the diagnostic script to verify fixes:**
   ```bash
   ./test_minerva_fixes.sh
   ```

2. **Start the server with the new startup script:**
   ```bash
   ./start_minerva_server.sh
   ```

3. **Access the Minerva portal in your browser:**
   ```
   http://localhost:5505/portal
   ```

## Troubleshooting

If you encounter any issues:

1. Check the logs directory for detailed error messages
2. Run the diagnostic script to verify all dependencies
3. Ensure all API keys are properly set in your environment
4. Verify that the Socket.IO client version in the HTML matches the server 