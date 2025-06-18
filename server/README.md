# Minerva Server

Clean, organized server implementation for Minerva AI Assistant.

## 🏗️ Structure

```
server/
├── minerva_server.py      # Main production server
├── main_server.py         # Legacy main server (kept for reference)
├── websocket/             # WebSocket-specific implementations
│   ├── enhanced_standalone_websocket.py
│   ├── pure_minimal.py
│   ├── pure_threading_server.py
│   └── threading_server.py
├── test_servers/          # Development and testing servers
│   ├── *.py               # Various test server implementations
│   └── *.html             # Test HTML files
├── legacy/                # Historical implementations
│   └── *.py               # Fix/solution attempts
├── backups/               # Server backups
│   └── server.py.*        # Backup files
└── scripts/               # Server management scripts
    └── *.sh               # Run and maintenance scripts
```

## 🚀 Quick Start

### Production Server
```bash
# Using the launcher (recommended)
python3 bin/launch_minerva.py server

# Direct execution
python3 server/minerva_server.py --port 5000
```

### Development Server
```bash
python3 server/minerva_server.py --debug --port 5001
```

## 📋 API Endpoints

### Health Check
- `GET /api/health` - Server health status
- `GET /api/models` - Available AI models
- `GET /api/config` - Server configuration

### WebSocket Events
- `connect` - Client connection
- `chat_message` - Send chat messages
- `join_session` - Join a session

## 🔧 Configuration

The server uses the centralized configuration from `core/config.py`:

```python
from core.config import config

# Server settings
host = config.server_config.get('host', '0.0.0.0')
port = config.server_config.get('port', 5000)
```

## 📝 Legacy Files

The following files have been preserved for reference but are no longer actively used:

### Main Legacy Server
- `main_server.py` - Original large server implementation

### WebSocket Implementations
- Various experimental WebSocket implementations in `websocket/`

### Test Servers
- Multiple test and debug server implementations in `test_servers/`

### Fix Attempts
- Historical fix and solution attempts in `legacy/`

## 🧪 Testing

Test servers are available in `test_servers/` for development:

```bash
# Run a minimal test server
python3 server/test_servers/minimal_test_server.py

# Run debug server
python3 server/test_servers/debug_socketio.py
```

## 📜 Scripts

Server management scripts in `scripts/`:

- `run_*.sh` - Various server startup scripts
- `fix_*.sh` - Maintenance and fix scripts
- `cleanup_*.sh` - Cleanup utilities

## 🔄 Migration

### From Old Structure
If you were using the old scattered server files:

1. **Replace `server.py`** → Use `server/minerva_server.py`
2. **Replace custom run scripts** → Use `bin/launch_minerva.py server`
3. **Update imports** → `from server import MinervaServer`

### Breaking Changes
- Server is now class-based (`MinervaServer`)
- Configuration is centralized in `core/config.py`
- WebSocket handling is improved and standardized

## 🛠️ Development

To extend the server:

1. **Add routes** in `MinervaServer._setup_routes()`
2. **Add WebSocket handlers** in `MinervaServer._setup_websocket_handlers()`
3. **Use core components** from `core/` package
4. **Follow the established patterns** for consistency

## 📚 Dependencies

Core dependencies managed by the main launcher:
- Flask & Flask-SocketIO
- Flask-CORS
- Core Minerva components

## 🐛 Troubleshooting

Common issues and solutions:

### Port Already in Use
```bash
# Find and kill existing server
lsof -ti:5000 | xargs kill -9
```

### Import Errors
```bash
# Ensure you're running from project root
cd /path/to/Minerva
python3 server/minerva_server.py
```

### WebSocket Connection Issues
- Check CORS settings
- Verify SocketIO version compatibility
- Use threading mode for Python 3.13+

## 🎯 Future Improvements

- [ ] Add rate limiting
- [ ] Implement server clustering
- [ ] Add metrics collection
- [ ] WebSocket room management
- [ ] SSL/TLS support 