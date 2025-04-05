#!/usr/bin/env python3
"""
Simple script to open the Minerva Orbital UI in the default browser
"""
import http.server
import socketserver
import threading
import time
import webbrowser
import os
import sys

# Set the port for the web server
PORT = 8090

# Get the directory containing this script
directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(directory)

# Create a handler for the SimpleHTTPServer
Handler = http.server.SimpleHTTPRequestHandler

# Create the server with the handler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(1)
    
    # Open the browser to the fixed UI page
    url = f"http://localhost:{PORT}/minerva_orbital_fixed.html"
    print(f"Opening {url} in your default browser...")
    webbrowser.open(url)
    
    # Keep the server running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown()
        sys.exit(0)
