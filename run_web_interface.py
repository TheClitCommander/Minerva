#!/usr/bin/env python3
"""
Minerva Web Interface Launcher

This script launches the Minerva web interface with appropriate configuration.
"""

import os
import sys
import argparse
from pathlib import Path

def main():
    """Main function to run the web interface."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Launch the Minerva web interface')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on (default: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to run the web server on (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Set up environment variables
    os.environ['PORT'] = str(args.port)
    
    # Set up the Flask secret key (generate a secure one in production)
    if 'FLASK_SECRET_KEY' not in os.environ:
        os.environ['FLASK_SECRET_KEY'] = 'minerva-dev-key-for-testing-only'
    
    # Make sure we're in the right directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    try:
        # Add the current directory to the Python path
        sys.path.insert(0, str(script_dir))
        
        # Import and run the web app
        print(f"Starting Minerva Web Interface on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop the server")
        
        from web.app import app, socketio
        socketio.run(app, host=args.host, port=args.port, debug=args.debug)
        
    except ImportError as e:
        print(f"Error: {str(e)}")
        print("Make sure you've installed the required dependencies:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down Minerva Web Interface")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting Minerva Web Interface: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
