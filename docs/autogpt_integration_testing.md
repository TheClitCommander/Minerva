# AutoGPT Integration Testing Strategy

This document outlines the approach and tools for testing the AutoGPT integration with Minerva's chat functionality.

## Testing Objectives

1. Verify that the AutoGPT integration is properly initialized
2. Confirm that WebSocket communication works correctly with AutoGPT
3. Test that AutoGPT provides appropriate responses to different types of queries
4. Ensure error handling works correctly when AutoGPT is unavailable
5. Measure performance and response time of the integrated system

## Testing Tools

We have created several testing tools to verify the AutoGPT integration:

1. **Unit Tests** (`tests/test_autogpt_integration.py`) - Tests the core AutoGPT integration class
2. **WebSocket Client Tests** (`tests/test_websocket_with_autogpt.py`) - Tests the chat functionality with AutoGPT
3. **Simple SocketIO Test Server** (`simple_socketio_test.py`) - A minimal server for isolating WebSocket issues

## Running the Tests

### Unit Tests

```bash
cd ~/Desktop/Minerva
source fresh_venv/bin/activate
python -m unittest tests/test_autogpt_integration.py
```

### WebSocket Client Tests

First ensure Minerva is running:

```bash
cd ~/Desktop/Minerva
source fresh_venv/bin/activate
python run_minerva.py --debug
```

Then in another terminal:

```bash
cd ~/Desktop/Minerva
source fresh_venv/bin/activate
python tests/test_websocket_with_autogpt.py
```

### Simple SocketIO Test

For basic WebSocket testing without AutoGPT:

```bash
cd ~/Desktop/Minerva
source fresh_venv/bin/activate
python simple_socketio_test.py
```

Then open http://localhost:5001 in your browser.

## Test Cases

### Basic Connectivity Tests

- Verify WebSocket connection establishes correctly
- Test basic message sending and receiving
- Verify session handling works correctly

### AutoGPT Functionality Tests

- Check that AutoGPT initialization works correctly
- Verify that simple queries get appropriate responses
- Test complex queries that require deeper AI capabilities
- Ensure conversation history is maintained correctly

### Error Handling Tests

- Test behavior when AutoGPT is unavailable
- Verify graceful fallback to echo responses
- Check error reporting through WebSockets

### Performance Tests

- Measure response time for various query types
- Verify system stability under load
- Test long-running conversations

## Integration Success Criteria

The AutoGPT integration is considered successfully tested when:

1. Unit tests pass, confirming AutoGPT is correctly initialized
2. WebSocket communication with AutoGPT works without errors
3. Responses from AutoGPT are appropriate for the queries
4. The system gracefully handles failures
5. Performance meets acceptable response time targets

## Next Steps After Testing

Once testing is complete and issues are addressed:

1. Document any remaining limitations or known issues
2. Optimize performance based on test results
3. Enhance the UI to better support the AutoGPT integration
4. Expand functionality to include additional AI capabilities
