# Minerva Codebase Cleanup

This document describes the cleanup process for the Minerva codebase and how the reorganization was performed.

## Cleanup Summary

The Minerva codebase was cleaned up to improve organization, remove redundancy, and make it easier to maintain going forward. This was accomplished by:

1. Moving redundant files to the `delete_me_later` directory
2. Reorganizing the remaining code into a cleaner structure
3. Creating improved versions of core files
4. Setting up shell scripts to run the reorganized code

## New Directory Structure

After cleanup, the codebase has the following structure:

```
Minerva/
├── data/                      # Data storage for chat history and cache
├── logs/                      # Server logs
├── static/                    # Static web assets
├── web/                       # Web-related code
│   ├── api/                   # API-related code
│   │   ├── multi_ai_coordinator.py   # AI model coordination
│   │   ├── minerva_extensions.py     # Minerva extensions (chat history, web research)
│   │   └── enhanced_fallback.py      # Fallback responses when API is unavailable
│   ├── chat/                  # Chat-related code
│   └── ui/                    # UI components
│       └── minerva-portal.html       # Main Minerva portal UI
├── reorganized_server.py      # Main server with clean organization
├── run_minerva.sh             # Shell script to run the reorganized server
├── cleanup_codebase.sh        # Shell script that performed the cleanup
└── delete_me_later/           # Directory for redundant/old files
    ├── redundant_ai/          # Redundant AI implementation files
    ├── unused_routes/         # Unused route handlers and shell scripts
    ├── legacy_sockets/        # Legacy Socket.IO implementations
    ├── dead_utils/            # Utilities that are no longer needed
    └── tests/                 # Test files that are not needed in production
```

## Files Moved During Cleanup

### Redundant Server Implementations (to delete_me_later/redundant_ai/)
- `forever_run_server.py` - Duplicates the functionality in simple_stable_server.py
- `forever_server.py` - Older version with less functionality
- `minerva_direct_server.py` - Redundant with server.py
- `minerva_chat_server.py` - Older standalone implementation
- `chat_directly.py` - Redundant implementation of chat
- `standalone_server.py` - Simplified version now replaced by simple_stable_server.py
- `direct_server.py` - Redundant implementation
- `simple_fixed_server.py` - Superseded by simple_stable_server.py
- `just_run_this.py` - Quick fix script no longer needed
- `fix_everything.py` - One-time fix script
- `quick_fix.py` - One-time fix script

### Legacy Shell Scripts (to delete_me_later/unused_routes/)
- Multiple shell scripts for various server implementations, including `no_kill_server.sh`, `run_minerva_direct.sh`, etc.

### Test HTML Files (to delete_me_later/tests/)
- `standalone_test.html` - Test file
- `direct_chat_test.html` - Test file
- `simple-test.html` - Test file

### Test and Debug Files (to delete_me_later/dead_utils/)
- Various test and debug files like `verify_coordinator_export.py`, `socket_io_test.py`, etc.

### Web Directory Cleanup (to delete_me_later/legacy_sockets/web/)
- Multiple redundant UI implementations and old server files

## New Files Created

1. `cleanup_codebase.sh` - Script for moving files to the delete_me_later directory
2. `reorganized_server.py` - Clean, reorganized version of server.py that imports from the new directory structure
3. `run_minerva.sh` - New script to run the reorganized server

## How to Run the Server

To run the server with the new organization:

```bash
./run_minerva.sh
```

This script will:
1. Activate the virtual environment if it exists
2. Install required packages
3. Run the cleanup script if needed
4. Start the reorganized server

## Notes About the Cleanup

- Core functionality is preserved, nothing essential was deleted
- The server maintains the same API and Socket.IO interfaces
- Previously scattered code is now organized into logical directories
- Redundant AI implementations have been consolidated
- Configuration is more centralized and easier to maintain

## Files Preserved During Cleanup

- Minerva Portal UI (`web/ui/minerva-portal.html`)
- AI Coordinator (`web/api/multi_ai_coordinator.py`)
- Minerva Extensions (`web/api/minerva_extensions.py`)
- Enhanced Fallback (`web/api/enhanced_fallback.py`)

## Recommendations for Further Improvement

1. Completely delete the `delete_me_later` directory after confirming the reorganization works well
2. Create proper documentation for the API endpoints
3. Implement better error handling and logging
4. Add automated tests
5. Standardize the code style and formatting 