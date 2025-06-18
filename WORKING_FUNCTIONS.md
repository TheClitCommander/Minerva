# Minerva Working Functions Registry

This document serves as a registry of critical, working components that must be preserved during development. Any modifications to these functions should be done with extreme caution and thorough testing.

## Chat & Memory System

### Core Chat Functions (minerva-chat.js)
- `sendMessage()` - Handles sending user messages to the API while maintaining context
- `addUserMessage()` - Adds user messages to the chat interface
- `handleThinkTankResponse()` - Processes AI responses without duplication (recently fixed)
- `processAIResponse()` - Handles different response formats
- `renderMarkdown()` - Formats markdown responses

### Project-Specific Chat (minerva-ui-integration.js)
- `sendProjectMessage()` - Sends project-specific messages with project context
- `addProjectUserMessage()` - Adds user messages to the project chat interface
- `processProjectResponse()` - Handles project-specific AI responses

### Memory System
- Conversation persistence across sessions
- Project-specific memory context 
- Ability to recall previous conversations

## UI Components

### Orbital UI
- 3D space environment with central Minerva orb
- Project orbs in orbital arrangement
- Holographic UI elements
- Navigation buttons

### Think Tank
- Multi-model blending functionality
- Model selection and weighting
- Response metrics visualization

## Server Components

### API Endpoints
- `/api/chat` - General chat API endpoint
- `/api/project-chat` - Project-specific chat endpoint
- `/api/models` - Model information endpoint

### Data Persistence
- ChromaDB integration for vector storage
- Project state management

## Testing Protocols

When modifying any of the above components:
1. Always create a backup of working code
2. Test modifications in isolation
3. Verify that memory persistence still works
4. Ensure project context is maintained
5. Check that UI elements render correctly
6. Validate API responses

## Deployment Checklist

- [ ] Memory system works across sessions
- [ ] Project context switching preserves conversations
- [ ] Chat responses are not duplicated
- [ ] Orbital UI renders correctly
- [ ] Think Tank model blending functions properly
- [ ] All API endpoints return expected responses

---

**Last Updated**: March 13, 2025
**Created By**: Cascade AI
