# Minerva Codebase Organization Guide

## Introduction

This document outlines the organization structure of the Minerva codebase following the Minerva Master Ruleset. It aims to provide clarity on where different types of files belong and how the codebase is structured for maintainability and navigation.

## Core Directory Structure

### `/minerva/`
The core application package containing the main business logic:
- `/minerva/ai/` - AI reasoning systems (task_reasoner.py)
- `/minerva/chat/` - Chat handling logic 
- `/minerva/core/` - Core system functions
- `/minerva/runtime/` - Runtime environment components

### `/web/`
Web interface and API layer:
- `/web/api/` - API endpoints
- `/web/static/` - Frontend assets (JS, CSS, images)
- `/web/templates/` - HTML templates
- `/web/static/js/projects/` - Project management functionality 
- `/web/static/js/chat/` - Chat interface components

## File Organization Rules

1. **Module Structure**
   - Keep related functionality together in modules
   - Use `__init__.py` files for proper Python package structure
   - Follow clear naming conventions for files

2. **Chat System (Per Minerva Ruleset #7)**
   - `unified-chat-handler.js` is the primary chat handler
   - Legacy chat files (`direct-chat.js`, `floating-chat.js`, `chat.js`, `chat-core.js`) have been archived

3. **Test Files**
   - All test files should be in `/test/` or `/tests/` directories
   - Name test files with pattern `test_*.py` or `*_test.py`

4. **Backup and Generated Files**
   - Backup files are stored in `/archive/backup_files/`
   - Files with extensions `.bak`, `.backup`, `_backup`, `.fixed`, etc. are considered backups

## Archive Structure

The `/archive/` directory contains files that are no longer in active use but are preserved for reference:

- `/archive/test_files/` - Archived test files
- `/archive/backup_files/` - Backup and fixed versions of files
- `/archive/demo_files/` - Example and demo files
- `/archive/old_scripts/` - Legacy scripts and outdated components

## File Categories

1. **Core Files**
   - Essential files needed for the main functionality
   - Located in the main package directories
   - Examples: `task_reasoner.py`, `project_api.py`, `multi_ai_coordinator.py`

2. **Framework Files**
   - Support the core functionality but aren't core themselves
   - Examples: `logging_config.py`, `api_request_handler.py`

3. **Test Files**
   - Used for testing but not needed in production
   - Should be in dedicated test directories

4. **Backup Files**
   - Temporary versions, backups, or fixed versions
   - Should be in the archive or excluded via .gitignore

## Organization Tools

The `scripts/organize_codebase.py` script helps organize files according to this structure:

```bash
# Run the organization script
python scripts/organize_codebase.py
```

This script identifies and moves files to appropriate archive directories based on their types.

## Future Maintenance

When adding new files to the codebase:

1. Consider where the file belongs in the structure
2. Use consistent naming conventions
3. Add appropriate tests in the test directories
4. Document the purpose and usage of the file

## Complying with Minerva Master Ruleset

This organization follows the Minerva Master Ruleset, particularly rule #7 regarding File & Module Structure:

1. Use unified-chat-handler.js as the only chat handler
2. Archive legacy chat files
3. Split logic across appropriate modules (memory storage, chat display, API bridge, UI rendering)

By maintaining this structure, the codebase becomes more maintainable, easier to navigate, and better organized for future development.
