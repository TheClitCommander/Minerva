# Minerva Enhanced Analytics

This guide explains how to use the new Enhanced Analytics feature that properly separates real and simulated API calls.

## Features

- **Clear Separation**: Properly distinguishes between real API calls and simulated ones
- **Accurate Cost Tracking**: Shows actual API costs for real calls only
- **Interactive UI**: Toggle between real, simulated, and combined views
- **Detailed Metrics**: Response times, token usage, and call frequency

## Integration

The enhanced analytics system runs alongside the existing analytics and doesn't replace it, ensuring backward compatibility.

## How to Enable Enhanced Analytics

1. Import the integration module at the top of `minimal_chat_server.py`:

```python
# Near the top with other imports
from minimal_chat_server_integration import integrate_enhanced_analytics
```

2. Call the integration function after creating your Flask app:

```python
# After: app = Flask(__name__, static_folder='static')
integrate_enhanced_analytics(app)
```

3. Restart your Minerva server

## Using Enhanced Analytics

1. Access Enhanced Analytics from the navigation menu
2. Toggle between "Real API Calls", "Simulated Calls", and "Combined View" using the buttons
3. View detailed statistics and charts for each category

## Notes on Real API Tracking

- Real API calls will be tracked with their original model names (e.g., "gpt-4")
- Simulated calls are tracked with a "simulated-" prefix (e.g., "simulated-gpt-4")
- The enhanced analytics view automatically separates these and provides clear visualizations

## Troubleshooting

If you encounter any issues:

1. Check that `TRACK_API_USAGE` is set to `true` in your environment variables
2. Verify that the data directory exists and is writable
3. Make sure the integration code is correctly added to `minimal_chat_server.py`
