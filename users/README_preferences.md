# User Preference Manager

## Overview
The User Preference Manager enables personalized experiences in Minerva by storing and retrieving user-specific settings. The primary focus is on retrieval depth preferences, which control how much context is used when retrieving knowledge for responses.

## Features
- **Per-User Preferences**: Each user has their own preference profile
- **Persistent Storage**: Preferences are stored in JSON files for persistence
- **Retrieval Depth Settings**: Three levels of retrieval depth:
  - **Concise**: Brief responses with minimal context
  - **Standard**: Balanced approach (default)
  - **Deep Dive**: Detailed responses with extensive context
- **Response Tone Settings**: Three response tone styles:
  - **Formal**: Professional and structured language
  - **Casual**: Conversational and friendly tone
  - **Neutral**: Balanced tone (default)
- **Response Structure Settings**: Four structure formats:
  - **Paragraphs**: Traditional paragraph-based responses (default)
  - **Bullet Points**: Information organized in bullet points
  - **Numbered Lists**: Sequentially numbered information
  - **Summary**: Condensed summary of key points
- **Response Length Settings**: Three length options:
  - **Short**: Concise responses, focusing on essential information
  - **Medium**: Balanced length (default)
  - **Long**: Comprehensive responses with detailed explanations
- **Feedback Tracking**: Records user feedback on responses:
  - Tracks positive and negative feedback
  - Supports implicit feedback through expansion link usage
  - Automatically adjusts user preferences based on feedback patterns

## Usage

### Direct API Usage
```python
from users.user_preference_manager import user_preference_manager

# Get a user's current retrieval depth
depth = user_preference_manager.get_retrieval_depth("user_123")

# Set a user's retrieval depth
user_preference_manager.set_retrieval_depth("user_123", "deep_dive")

# Get retrieval parameters based on preference
params = user_preference_manager.get_retrieval_params("user_123")
# Returns: {'top_k': 8, 'max_tokens_per_chunk': 250, 'context_window': 1500}

# Response tone preferences
tone = user_preference_manager.get_response_tone("user_123")  # Returns: "neutral" (default)
user_preference_manager.set_response_tone("user_123", "formal")

# Response structure preferences
structure = user_preference_manager.get_response_structure("user_123")  # Returns: "paragraph" (default)
user_preference_manager.set_response_structure("user_123", "bullet_points")

# Response length preferences
length = user_preference_manager.get_response_length("user_123")  # Returns: "medium" (default)
user_preference_manager.set_response_length("user_123", "long")

# Record user feedback
user_preference_manager.record_feedback("user_123", "response_456", is_positive=True, feedback_type="general")

# Get formatting parameters for a response
formatting = user_preference_manager.get_formatting_params("user_123")
# Returns: {
#    'tone': 'formal', 
#    'structure': 'bullet_points',
#    'length': 'long',
#    'tone_markers': {'formal': ['professionally', 'precisely'], ...}
# }
```

### REST API Endpoints
The following endpoints are available for managing user preferences:

#### Get All User Preferences
```
GET /api/user/preferences?user_id={user_id}
```
Returns all preferences for the specified user.

#### Get Retrieval Depth
```
GET /api/user/preferences/retrieval_depth?user_id={user_id}
```
Returns the current retrieval depth setting for the specified user.

#### Set Retrieval Depth
```
POST /api/user/preferences/retrieval_depth
```
Body:
```json
{
  "user_id": "user_123",
  "retrieval_depth": "concise" 
}
```
Sets the retrieval depth preference for the specified user.

#### Set Response Tone
```
POST /api/user/preferences/response_tone
```
Body:
```json
{
  "user_id": "user_123",
  "response_tone": "formal" 
}
```
Sets the response tone preference for the specified user.

#### Set Response Structure
```
POST /api/user/preferences/response_structure
```
Body:
```json
{
  "user_id": "user_123",
  "response_structure": "bullet_points" 
}
```
Sets the response structure preference for the specified user.

#### Update Multiple Preferences
```
POST /api/user/preferences/update
```
Body:
```json
{
  "user_id": "user_123",
  "preferences": {
    "retrieval_depth": "concise",
    "response_tone": "formal",
    "response_structure": "bullet_points"
  }
}
```
Updates multiple preferences at once for the specified user.

### Chat Commands
Users can change their preferences directly within chat using the following commands:

#### Retrieval Depth Commands:
- **Concise Mode**: "concise mode", "/concise", or "be concise"
- **Standard Mode**: "standard mode", "/standard", or "be standard"
- **Deep Dive Mode**: "deep dive mode", "/deep", "be detailed", or "deep dive"

#### Response Tone Commands:
- **Formal Tone**: "/formal", "formal tone", or "be formal"
- **Casual Tone**: "/casual", "casual tone", or "be casual"
- **Neutral Tone**: "/neutral", "neutral tone", or "be neutral"

#### Response Structure Commands:
- **Paragraphs**: "/paragraph" or "use paragraphs" or "paragraph format"
- **Bullet Points**: "/bullets" or "use bullet points"
- **Numbered List**: "/numbered" or "use numbered list"
- **Summary**: "/summary" or "just summarize"

## Implementation Details

### Storage
User preferences are stored in JSON files in the `/users/preferences/` directory. Each user has their own file named with their user ID.

### Default Values
- Default retrieval depth: `standard`
- Default retrieval parameters:
  - Concise: `{'top_k': 3, 'max_tokens_per_chunk': 100, 'context_window': 500}`
  - Standard: `{'top_k': 5, 'max_tokens_per_chunk': 150, 'context_window': 1000}`
  - Deep Dive: `{'top_k': 8, 'max_tokens_per_chunk': 250, 'context_window': 1500}`
- Default response tone: `neutral`
- Default response structure: `paragraph`
- Tone markers:
  - Formal: `['professionally', 'precisely', 'formally']`
  - Casual: `['conversationally', 'casually', 'in a friendly way']`
  - Neutral: `[]` (no specific markers)

### Integration
The User Preference Manager is integrated with:
- Knowledge retrieval system
- GPT response processing
- Chat message handling
- REST API endpoints
- Response formatting system
- Web interface settings panel

## Testing
Comprehensive tests have been implemented to verify:
- Core preference functionality
- Integration with knowledge retrieval
- Command recognition
- Response formatter functionality
  - Tone application tests
  - Structure formatting tests
  - Edge case handling
- API endpoints for preference management
- UI components for preference settings

## Future Enhancements
- Additional tone styles (e.g., technical, educational, creative)
- More structure formats (e.g., Q&A format, hierarchical lists)
- Language preference settings
- AI voice tone adjustments
- Advanced personalization based on user behavior
- Interactive previews of different formatting styles
- Preference presets for common scenarios
- Analytics for preference usage patterns
