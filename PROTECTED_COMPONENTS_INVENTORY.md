# Minerva Protected Components Inventory

## Purpose
This document provides a complete inventory of all preserved and protected components in the Minerva system. Use this as a reference when developing to ensure you don't lose working functionality.

## Memory System
- **Critical Files**: 
  - `/web/static/js/minerva-chat.js`
  - `/web/static/js/minerva-ui-integration.js`
  - `/web/minimal_server.py`
- **Protected Functions**:
  - `handleThinkTankResponse()` - Fixed to prevent duplicate responses
  - `sendProjectMessage()` - Manages project context and messages
  - `storeSessionContext()` - Preserves conversation across sessions
  - `getProjectMemoryContext()` - Retrieves project-specific memories
- **Documentation**: `/function_snapshots/memory/MEMORY_SYSTEM_DOCUMENTATION.md`

## Orbital UI System
- **Critical Files**:
  - `/web/static/js/orb-ui/orb-ui-init.js`
  - `/web/static/js/orb-ui/react-three/*`
  - `/web/static/css/orbital-enhanced.css`
  - `/web/templates/orbital_home.html`
- **Protected Functions**:
  - React Three.js components for 3D visualization
  - Orbital ring animations and positioning
  - Holographic UI elements and styling
  - Space background and star field effects
- **Documentation**: `/function_snapshots/orb_system/ORBITAL_UI_DOCUMENTATION.md`

## Think Tank System
- **Critical Files**:
  - `/web/static/js/think-tank-bridge.js`
  - `/web/static/js/think-tank-metrics.js`
  - `/web/static/js/model-metrics.js`
  - `/web/static/js/model-visualization.js`
- **Protected Functions**:
  - Multi-model blending algorithm
  - Response quality evaluation
  - Model performance tracking
  - Visualization of model metrics
- **Documentation**: `/function_snapshots/api/THINK_TANK_DOCUMENTATION.md`

## Chat Interface
- **Critical Files**:
  - `/web/static/js/chat-interface.js`
  - `/web/static/js/minerva-chat.js`
  - `/web/static/css/chat-interface.css`
- **Protected Functions**:
  - Message handling and display
  - Markdown rendering
  - User input processing
  - Floating chat panel integration
- **Documentation**: `/function_snapshots/chat/CRITICAL_MEMORY_FUNCTIONS.js`

## Project Management
- **Critical Files**:
  - `/web/static/js/orb-ui/orb-ui-project.js`
  - `/web/static/js/minerva-ui-integration.js`
- **Protected Functions**:
  - Project creation and management
  - Conversation assignment to projects
  - Project context switching
  - Project visualization in orbital UI
- **Documentation**: From UI and Memory documentation

## API Integration
- **Critical Files**:
  - `/web/minimal_server.py`
  - `/web/static/js/think-tank-bridge.js`
- **Protected Functions**:
  - Chat API endpoints
  - Project management endpoints
  - ChromaDB integration
  - Session management
- **Documentation**: `/function_snapshots/api/THINK_TANK_DOCUMENTATION.md`

## Visualization System
- **Critical Files**:
  - `/web/static/js/model-visualization.js`
  - `/web/static/js/planet-visualization.js`
- **Protected Functions**:
  - Model performance charts
  - Project visualization
  - Think Tank metrics display
- **Documentation**: Included in Think Tank and UI documentation

## Protection Methodology
- **Code Comments**: Added `/* PROTECTED FUNCTION */` comments to critical functions
- **File Backups**: Created snapshots in `/function_snapshots/` directory
- **Documentation**: Detailed documentation for each system component
- **Development Guidelines**: See `/FUNCTION_PRESERVATION_SYSTEM.md`

## How To Use This Inventory
1. Before modifying any component, check if it's in this inventory
2. If it is protected, review the relevant documentation first
3. Always test changes to protected components thoroughly
4. Update this inventory if you successfully enhance a protected component

---

Remember that the integration of conversation memory with project context and the 3D orbital UI are your current priorities, as outlined in your development plan. All modifications should preserve these core functionalities while progressively enhancing the system.
