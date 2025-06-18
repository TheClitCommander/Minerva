# Minerva Memory System Documentation

## Overview
The Minerva Memory System manages conversation persistence across sessions and projects. This is a critical component that allows the AI to maintain context and remember previous interactions with users across different parts of the Minerva ecosystem.

## Core Components

### 1. Conversation Storage System
- **Location**: `minimal_server.py`, `minerva-chat.js`
- **How it Works**: Conversations are stored using a combination of:
  - Browser localStorage for client-side persistence
  - ChromaDB for server-side vector storage
  - Session management to track conversation context

### 2. Project Context Management
- **Location**: `minerva-ui-integration.js`
- **How it Works**: 
  - Projects have unique identifiers stored in `sessionStorage`
  - Conversations within a project maintain a separate context
  - `updateProjectMemoryContext()` manages updating the project-specific memories

### 3. Memory Retrieval System
- **Location**: `minimal_server.py` (API endpoints)
- **How it Works**:
  - Memory retrieval happens when loading a project
  - Previous conversations are fetched from storage
  - Context is maintained between chat sessions

## Critical Functions

### Client-Side Memory Functions (JavaScript)
- `storeSessionContext()`: Persists session information to localStorage
- `getSessionContext()`: Retrieves session context from localStorage
- `updateProjectMemoryContext()`: Updates project-specific memory
- `getProjectMemoryContext()`: Retrieves project-specific memory

### Server-Side Memory Functions (Python)
- `store_conversation()`: Adds messages to the vector database
- `retrieve_conversation_history()`: Gets previous conversations
- `get_project_context()`: Retrieves context for a specific project
- `update_project_memory()`: Updates the project's memory vectors

## Integration Points

### Chat System Integration
- Chat messages are stored with session identifiers
- Messages include project context when sent from project view
- Response handlers maintain the context chain

### Project System Integration
- Projects store their conversation history separately
- Project switching loads the appropriate context
- New projects can be created from existing conversations

### Think Tank Integration
- Think Tank receives context from the memory system
- Multi-model responses are tracked in memory with metadata
- Memory system preserves model selection and weighting

## Implementation Details

### Memory Format
```javascript
// Example memory storage format in localStorage
{
  "role": "user" | "assistant",
  "content": "Message text",
  "timestamp": "ISO timestamp",
  "project_id": "project-identifier" | null,
  "metadata": {
    // Additional context
  }
}
```

### ChromaDB Integration
- Conversations are embedded as vectors
- Similar previous conversations can be retrieved
- Semantic searching allows for context-aware responses

## Known Limitations
- Memory has a size limit in localStorage
- Long conversations may be truncated for API calls
- Project switching may occasionally cause context loss

## Testing Methodology
- Test persistence across page refreshes
- Verify project context switching maintains memory
- Confirm long-term storage works properly

---

## DO NOT MODIFY WITHOUT TESTING
Any changes to the memory system should be thoroughly tested to ensure:
1. Conversations persist across sessions
2. Project context is maintained
3. The appropriate conversation history is retrieved
4. No duplicate messages are created
