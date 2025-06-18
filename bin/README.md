# Minerva Unified Launcher

This directory contains the unified launcher system for Minerva AI Assistant.

## Quick Start

```bash
# Start the web server
python3 bin/launch_minerva.py server

# Start the AI assistant
python3 bin/launch_minerva.py ai

# Start CLI interface  
python3 bin/launch_minerva.py cli

# Check system status
python3 bin/launch_minerva.py status
```

## Files

- `launch_minerva.py` - Main Python launcher with all functionality
- `run.sh` - Simple shell wrapper for convenience
- `README.md` - This documentation

## Launch Modes

### AI Assistant Mode
```bash
python3 bin/launch_minerva.py ai [--verbose] [--discover PATH]
```
Starts the core Minerva AI Assistant for framework integration and AI processing.

### Web Server Mode  
```bash
python3 bin/launch_minerva.py server [--host HOST] [--port PORT] [--debug]
```
Starts the Flask web server with SocketIO support for the web interface.

### CLI Mode
```bash
python3 bin/launch_minerva.py cli [--cli-args ARGS...]
```
Starts an interactive command-line interface.

### Status Mode
```bash
python3 bin/launch_minerva.py status
```
Shows system status and available components.

## Options

### AI Assistant Options
- `--verbose, -v` - Enable verbose logging
- `--discover, -d PATH` - Discover frameworks in specified directory

### Web Server Options
- `--host HOST` - Server host (default: 0.0.0.0)
- `--port PORT` - Server port (default: 5000) 
- `--debug` - Enable Flask debug mode

### CLI Options
- `--cli-args ARGS` - Arguments to pass to CLI

## Environment Setup

The launcher automatically:
- Sets up the project root directory
- Creates required directories
- Configures Python path
- Initializes logging

## Migration from Old Scripts

This unified launcher replaces multiple run scripts:
- `run_minerva.sh` → `bin/launch_minerva.py ai`
- `run_server.sh` → `bin/launch_minerva.py server`
- `run_minimal.sh` → `bin/launch_minerva.py server --port 5505`
- Various other run scripts → Consolidated into single launcher

## Architecture

The launcher uses a modular design:
1. **Environment Setup** - Ensures proper directory structure
2. **Mode Routing** - Routes to appropriate launch function
3. **Error Handling** - Graceful error handling and reporting
4. **Path Management** - Automatic Python path configuration 