#!/usr/bin/env python
"""
Utility script to check if a port is in use and optionally kill the process.
"""

import socket
import os
import subprocess
import sys
import argparse

def check_port(port):
    """Check if the given port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def get_process_using_port(port):
    """Get the PID of the process using the specified port."""
    try:
        # For macOS and Linux
        output = subprocess.check_output(['lsof', '-i', f':{port}'], text=True)
        lines = output.strip().split('\n')
        if len(lines) > 1:  # Header line plus at least one process
            # Format: COMMAND  PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
            # Extract PID (second column)
            process_line = lines[1].split()
            if len(process_line) >= 2:
                return int(process_line[1])
    except (subprocess.SubprocessError, IndexError, ValueError):
        pass
    return None

def kill_process(pid):
    """Kill a process by its PID."""
    try:
        # For macOS and Linux
        os.kill(pid, 9)  # SIGKILL
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Check if a port is in use and optionally kill the process.')
    parser.add_argument('port', type=int, help='Port number to check')
    parser.add_argument('--kill', action='store_true', help='Kill the process using the port')
    args = parser.parse_args()

    port = args.port
    port_in_use = check_port(port)
    
    if port_in_use:
        print(f"Port {port} is currently in use.")
        pid = get_process_using_port(port)
        if pid:
            print(f"Process using port {port}: PID {pid}")
            if args.kill:
                print(f"Attempting to kill process {pid}...")
                if kill_process(pid):
                    print(f"Successfully killed process {pid}")
                else:
                    print(f"Failed to kill process {pid}")
        else:
            print(f"Could not identify the process using port {port}")
    else:
        print(f"Port {port} is available (not in use)")

if __name__ == "__main__":
    main()
