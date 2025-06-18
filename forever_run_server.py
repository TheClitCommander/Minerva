#!/usr/bin/env python3
"""
Forever Run Server

This Python script runs the Minerva server and prevents it from being killed by SIGTERM.
It's a standalone script that doesn't rely on any shell scripts.
"""

import os
import sys
import signal
import subprocess
import time
import socket
import atexit
import shutil

# Define colors for terminal output
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color

def check_port(port):
    """Check if a port is in use."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def kill_process_on_port(port):
    """Kill the process using the specified port."""
    try:
        # macOS or Linux
        if sys.platform.startswith(('darwin', 'linux')):
            output = subprocess.check_output(['lsof', '-i', f':{port}', '-t']).decode().strip()
            if output:
                pids = output.split('\n')
                for pid in pids:
                    print(f"{YELLOW}Killing process {pid} on port {port}{NC}")
                    os.kill(int(pid), 9)  # SIGKILL
                return True
        # Windows
        elif sys.platform.startswith('win'):
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            if output:
                for line in output.split('\n'):
                    if 'LISTENING' in line:
                        pid = line.strip().split()[-1]
                        print(f"{YELLOW}Killing process {pid} on port {port}{NC}")
                        subprocess.check_call(f'taskkill /F /PID {pid}', shell=True)
                return True
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError):
        pass
    return False

def clear_python_cache():
    """Clear Python cache to ensure fresh imports."""
    print(f"{BLUE}Clearing Python cache...{NC}")
    cache_dirs = []
    
    # Find __pycache__ directories
    for root, dirs, files in os.walk('.'):
        for dir in dirs:
            if dir == '__pycache__':
                cache_dirs.append(os.path.join(root, dir))
    
    # Delete cache directories and .pyc files
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"Removed {cache_dir}")
        except Exception as e:
            print(f"Failed to remove {cache_dir}: {e}")
    
    # Also delete .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                except Exception:
                    pass

def ensure_sigterm_handling_in_server():
    """Ensure server.py has SIGTERM handling code."""
    if not os.path.exists('server.py'):
        print(f"{RED}server.py not found!{NC}")
        return False
    
    with open('server.py', 'r') as f:
        content = f.read()
    
    # Check if SIGTERM handling is already present
    if 'signal.signal(signal.SIGTERM, signal.SIG_IGN)' in content:
        print(f"{GREEN}SIGTERM handling already present in server.py{NC}")
        return True
    
    # Add SIGTERM handling
    print(f"{YELLOW}Adding SIGTERM handling to server.py...{NC}")
    
    # Make sure signal is imported
    if 'import signal' not in content:
        # Add signal import after the first import
        lines = content.split('\n')
        import_index = next((i for i, line in enumerate(lines) if line.startswith('import ') or line.startswith('from ')), 0)
        lines.insert(import_index + 1, 'import signal')
        content = '\n'.join(lines)
    
    # Add SIGTERM handling code
    lines = content.split('\n')
    import_indices = [i for i, line in enumerate(lines) if line.startswith('import ') or line.startswith('from ')]
    if import_indices:
        last_import_index = max(import_indices)
        sigterm_code = [
            "",
            "# Protect against SIGTERM",
            "print(\"Setting up signal handlers to prevent termination...\")",
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)",
            "print(\"✅ SIGTERM handler installed - server won't be killed by SIGTERM\")",
            ""
        ]
        for i, line in enumerate(sigterm_code):
            lines.insert(last_import_index + 1 + i, line)
        
        # Write back to file
        with open('server.py', 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"{GREEN}SIGTERM handling added to server.py{NC}")
        return True
    
    print(f"{RED}Could not add SIGTERM handling to server.py{NC}")
    return False

def setup_environment():
    """Set up the environment variables."""
    # Set dummy API keys if not already set
    if not os.environ.get('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = "sk-dummy-key-12345678901234567890123456789012"
        print(f"{YELLOW}Using dummy OpenAI API key{NC}")
    
    if not os.environ.get('ANTHROPIC_API_KEY'):
        os.environ['ANTHROPIC_API_KEY'] = "sk-ant-dummy-key-123456789012345678901234"
        print(f"{YELLOW}Using dummy Anthropic API key{NC}")
    
    if not os.environ.get('MISTRAL_API_KEY'):
        os.environ['MISTRAL_API_KEY'] = "dummy-key-12345678901234567890"
        print(f"{YELLOW}Using dummy Mistral API key{NC}")
    
    # Set other environment variables
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

def run_server():
    """Run the server as a subprocess and monitor it."""
    print(f"{GREEN}Starting Minerva server...{NC}")
    
    # Use subprocess to run server.py
    try:
        # Create server process
        server_process = subprocess.Popen(
            [sys.executable, 'server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Register cleanup function
        def cleanup():
            if server_process.poll() is None:
                print(f"{YELLOW}Terminating server process...{NC}")
                try:
                    # Try to terminate gracefully first
                    server_process.terminate()
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # If it doesn't terminate, kill it
                    print(f"{RED}Server not responding to terminate, killing...{NC}")
                    server_process.kill()
        
        atexit.register(cleanup)
        
        # Monitor the server output
        print(f"{GREEN}Server is running. Press Ctrl+C to stop.{NC}")
        print(f"{BLUE}Access the portal at http://localhost:5505/portal{NC}")
        print("=" * 50)
        
        # Read and print server output
        try:
            for line in server_process.stdout:
                print(line, end='')
        except KeyboardInterrupt:
            print(f"{YELLOW}Keyboard interrupt detected. Shutting down gracefully...{NC}")
        finally:
            cleanup()
            atexit.unregister(cleanup)
    
    except Exception as e:
        print(f"{RED}Error running server: {e}{NC}")
        return False
    
    return True

def main():
    """Main function."""
    print(f"{GREEN}=" * 50)
    print("FOREVER MINERVA SERVER LAUNCHER")
    print("=" * 50 + f"{NC}")
    
    # Override SIGTERM handling for this script
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    print(f"{GREEN}✅ SIGTERM protection enabled for launcher{NC}")
    
    # Check if port 5505 is already in use
    if check_port(5505):
        print(f"{YELLOW}Port 5505 is already in use.{NC}")
        response = input("Do you want to kill the process using this port? (y/n): ").strip().lower()
        if response == 'y':
            kill_process_on_port(5505)
            # Wait for port to be released
            for _ in range(5):  # Try 5 times
                time.sleep(1)
                if not check_port(5505):
                    print(f"{GREEN}Port 5505 is now available.{NC}")
                    break
            else:
                print(f"{RED}Failed to free port 5505. Exiting.{NC}")
                return False
        else:
            print(f"{RED}Exiting without killing the process.{NC}")
            return False
    
    # Clear Python cache
    clear_python_cache()
    
    # Ensure server.py has SIGTERM handling
    if not ensure_sigterm_handling_in_server():
        return False
    
    # Set up environment variables
    setup_environment()
    
    # Run the server
    return run_server()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"{YELLOW}Exiting due to keyboard interrupt.{NC}")
        sys.exit(0) 