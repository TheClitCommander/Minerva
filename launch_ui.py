#!/usr/bin/env python3
"""
Minerva UI Launcher

Launches the Minerva server and automatically opens the beautiful cosmic UI.
"""

import os
import sys
import time
import webbrowser
import subprocess
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
os.chdir(PROJECT_ROOT)

def print_banner():
    """Print launch banner."""
    print("\n" + "="*60)
    print("🌟 LAUNCHING MINERVA COSMIC UI")
    print("="*60)
    print("Starting server and opening beautiful interface...")
    print()

def wait_for_server(host='localhost', port=5000, timeout=30):
    """Wait for server to be ready."""
    import socket
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return True
        except:
            pass
        
        time.sleep(0.5)
    
    return False

def open_browser():
    """Open the cosmic UI in browser."""
    print("⏳ Waiting for server to start...")
    
    if wait_for_server():
        print("✅ Server is ready!")
        print("🌟 Opening Cosmic UI...")
        
        # Open the cosmic portal
        webbrowser.open('http://localhost:5000/portal')
        
        print("\n" + "="*60)
        print("🎉 MINERVA COSMIC UI LAUNCHED!")
        print("="*60)
        print("🌟 Cosmic Portal: http://localhost:5000/portal")
        print("📱 Simple Interface: http://localhost:5000")
        print("📊 API Health: http://localhost:5000/api/health")
        print()
        print("🔧 Controls:")
        print("  • Drag the central orb around")
        print("  • Click the chat orb (bottom right) to chat")
        print("  • Press Ctrl+C in terminal to stop server")
        print("="*60)
    else:
        print("❌ Server failed to start within 30 seconds")
        print("Try running manually: python3 bin/launch_minerva.py server")

def main():
    """Main launcher function."""
    print_banner()
    
    # Check if Flask is available
    try:
        import flask
        import flask_socketio
        import flask_cors
    except ImportError as e:
        print("❌ Missing dependencies for web server!")
        print("Install with: pip install flask flask-socketio flask-cors")
        print(f"Error: {e}")
        return 1
    
    # Start browser opener in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        # Start the server
        subprocess.run([sys.executable, 'bin/launch_minerva.py', 'server'], cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        print("👋 Thanks for using Minerva!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 