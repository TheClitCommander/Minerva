# 🚀 Minerva Quick Start Guide

Welcome to the refactored Minerva AI Assistant! This guide will help you quickly test the system.

## ⚡ Quick Launch

### Option 1: Simple Test Launcher (Recommended)
```bash
# Run the interactive test launcher
python3 test_minerva.py

# Or use the shell wrapper
./test_minerva.sh
```

### Option 2: Direct Component Testing
```bash
# Test the system status
python3 bin/launch_minerva.py status

# Start AI chat (simulation mode)
python3 bin/launch_minerva.py ai

# Start web server (requires Flask)
python3 bin/launch_minerva.py server
```

## 🧪 Test Menu Options

The test launcher provides these options:

1. **🔍 Check dependencies** - See what's installed and what's needed
2. **🧪 Test components** - Quick test of all refactored components
3. **🔬 Run comprehensive tests** - Full test suite (20+ tests)
4. **💬 Start AI chat** - Interactive AI assistant
5. **🌐 Start web server** - Web interface (needs Flask)
6. **📊 Show system status** - Component availability
7. **🚪 Exit** - Close the launcher

## 📋 System Requirements

### Required (Built-in Python)
- `pathlib`, `json`, `sqlite3`, `logging` ✅

### Optional (Install if needed)
```bash
pip install flask flask-socketio flask-cors python-dotenv openai anthropic
```

## 🏗️ New Architecture

After refactoring, Minerva now has a clean structure:

```
📁 bin/         - Launch scripts (unified entry point)
🧠 core/        - Core orchestration & config
🤖 models/      - AI model clients (OpenAI, Anthropic, etc.)
🧩 memory/      - Advanced memory system with priority
🔧 frameworks/  - Framework integration registry
🌐 server/      - Organized web/socket servers
🧪 tests/       - Comprehensive test suite
```

## 🎯 Quick Test Workflow

1. **First time**: Run `python3 test_minerva.py` and choose option 1 to check dependencies
2. **Test components**: Choose option 2 to verify all imports work
3. **Run full tests**: Choose option 3 to run the complete test suite
4. **Try AI chat**: Choose option 4 for simulation mode (works without API keys)
5. **Install Flask** (optional): For web interface functionality

## ⚙️ Configuration

- **API Keys**: Add to `.env` file or environment variables
- **Settings**: Configured via `core/config.py`
- **No API keys?** No problem! System runs in simulation mode

## 🆘 Troubleshooting

### Import Errors
- Run the dependency checker (option 1)
- Make sure you're in the project directory

### Server Won't Start
- Install Flask: `pip install flask flask-socketio flask-cors`
- Check port 5000 isn't in use: `lsof -ti:5000`

### AI Not Working
- Check API keys in `.env` file
- Simulation mode works without any keys

## 🎉 Success Indicators

✅ **All 18+ tests pass** (with 2 optional Flask tests skipped if no Flask)  
✅ **Components import cleanly**  
✅ **Launcher shows all systems available**  
✅ **Memory system initializes**  
✅ **Framework registry loads**

Enjoy testing the refactored Minerva system! 🌟 