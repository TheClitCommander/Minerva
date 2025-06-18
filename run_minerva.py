#!/usr/bin/env python3
"""
Minerva Runner Script
Starts the Minerva AI assistant with the specified configuration.
"""

# Import and configure eventlet before anything else
import os
import sys
import logging
import argparse
from pathlib import Path

# Set up logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

print("[STARTUP] Beginning server initialization...")

# Add parent directory to sys.path to allow importing modules
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

print("[STARTUP] Core modules imported")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Start the Minerva AI assistant')
    
    parser.add_argument('--port', type=int, default=5505, 
                        help='Port to run the server on')
    
    parser.add_argument('--host', type=str, default='0.0.0.0', 
                        help='Host to bind the server to')
    
    parser.add_argument('--debug', action='store_true', 
                        help='Run in debug mode')
    
    parser.add_argument('--no-reload', action='store_true',
                        help='Disable auto-reload')
    
    parser.add_argument('--config', type=str, 
                        help='Path to configuration file')
    
    return parser.parse_args()

def main():
    """Main function to start Minerva."""
    # Make sure eventlet is properly patched BEFORE any other imports
    try:
        import eventlet
        logger.info("[STARTUP] Checking eventlet monkey patching...")
        if not eventlet.patcher.is_monkey_patched('socket'):
            logger.info("[STARTUP] Applying eventlet monkey patching...")
            eventlet.monkey_patch()
            logger.info("[STARTUP] Eventlet monkey patching completed")
        else:
            logger.info("[STARTUP] Eventlet already monkey patched")
    except ImportError:
        logger.error("[STARTUP] Eventlet not installed. Socket.IO will not work correctly!")
        sys.exit(1)
    
    args = parse_args()
    
    # Set up environment
    os.environ['FLASK_APP'] = 'web.app'
    
    if args.debug:
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("[STARTUP] Debug mode enabled")
    
    logger.info("[STARTUP] Starting Minerva server...")
    
    # Generate a random secret key
    import secrets
    secret_key = secrets.token_hex(16)
    os.environ['SECRET_KEY'] = secret_key
    logger.info(f"[STARTUP] Generated random secret key: {secret_key}")
    
    try:
        # Import the Flask app
        logger.info("[STARTUP] Importing web.app module...")
        from web.app import app, socketio
        
        logger.info(f"[STARTUP] Starting Minerva server on {args.host}:{args.port}")
        logger.info(f"[STARTUP] Debug mode: {args.debug}")
        logger.info(f"[STARTUP] Auto-reload: {not args.no_reload}")
        
        # Enable Socket.IO logging
        if args.debug:
            logging.getLogger('engineio').setLevel(logging.DEBUG)
            logging.getLogger('socketio').setLevel(logging.DEBUG)
            logging.getLogger('werkzeug').setLevel(logging.DEBUG)
            logger.info("[STARTUP] Socket.IO and werkzeug logging enabled")
        
        # Start the server
        logger.info("[STARTUP] Starting SocketIO server...")
        websocket_url = "ws://{host}:{port}/socket.io/".format(
            host=args.host if args.host != '0.0.0.0' else 'localhost',
            port=args.port
        )
        logger.info(f"[STARTUP] WebSocket endpoint will be available at {websocket_url}")
        
        try:
            # Try with the specified port first
            # Remove allow_unsafe_werkzeug which isn't supported in this eventlet version
            socketio.run(
                app, 
                host=args.host, 
                port=args.port, 
                debug=args.debug,
                use_reloader=not args.no_reload,
                log_output=True
            )
        except OSError as e:
            if "Address already in use" in str(e):
                # Port is already in use, try to be smarter about resolution
                logger.warning(f"[STARTUP] Port {args.port} is already in use. Attempting intelligent recovery...")
                
                # First, try to identify and kill the process using the port
                import subprocess
                import platform
                import time
                
                def find_process_on_port(port):
                    """Find the process ID using the specified port."""
                    system = platform.system()
                    try:
                        if system == "Darwin" or system == "Linux":  # macOS or Linux
                            cmd = f"lsof -i :{port} -t"
                            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                            if result:
                                return [int(pid) for pid in result.split('\n')]
                        elif system == "Windows":
                            cmd = f"netstat -ano | findstr :{port}"
                            result = subprocess.check_output(cmd, shell=True).decode('utf-8')
                            if result:
                                pids = set()
                                for line in result.splitlines():
                                    if f":{port}" in line:
                                        parts = line.strip().split()
                                        if len(parts) >= 5:
                                            pids.add(int(parts[-1]))
                                return list(pids)
                        return []
                    except subprocess.SubprocessError:
                        logger.warning(f"[STARTUP] Failed to identify process using port {port}")
                        return []
                
                def is_minerva_process(pid):
                    """Check if the process is likely a Minerva process."""
                    try:
                        system = platform.system()
                        if system == "Darwin" or system == "Linux":
                            cmd = f"ps -p {pid} -o command="
                            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().lower()
                            return "python" in result and ("minerva" in result or "run_minerva.py" in result)
                        elif system == "Windows":
                            cmd = f"wmic process where processid={pid} get commandline"
                            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip().lower()
                            return "python" in result and ("minerva" in result or "run_minerva.py" in result)
                        return False
                    except subprocess.SubprocessError:
                        return False
                
                def kill_process(pid):
                    """Kill a process by its PID."""
                    system = platform.system()
                    try:
                        if system == "Darwin" or system == "Linux":
                            subprocess.check_call(f"kill -9 {pid}", shell=True)
                            return True
                        elif system == "Windows":
                            subprocess.check_call(f"taskkill /F /PID {pid}", shell=True)
                            return True
                        return False
                    except subprocess.SubprocessError:
                        return False
                
                # Find processes using our port
                pids = find_process_on_port(args.port)
                if pids:
                    logger.info(f"[STARTUP] Found {len(pids)} process(es) using port {args.port}: {pids}")
                    
                    # Check if any of these are likely old Minerva processes
                    minerva_pids = [pid for pid in pids if is_minerva_process(pid)]
                    
                    if minerva_pids:
                        logger.info(f"[STARTUP] Identified {len(minerva_pids)} previous Minerva process(es): {minerva_pids}")
                        success_count = 0
                        
                        for pid in minerva_pids:
                            logger.info(f"[STARTUP] Attempting to terminate previous Minerva process (PID: {pid})")
                            if kill_process(pid):
                                logger.info(f"[STARTUP] Successfully terminated process {pid}")
                                success_count += 1
                            else:
                                logger.warning(f"[STARTUP] Failed to terminate process {pid}")
                        
                        if success_count > 0:
                            logger.info(f"[STARTUP] Terminated {success_count} processes. Waiting for port to be released...")
                            # Wait a moment for the port to be released
                            time.sleep(2)
                            
                            # Try to start on the original port again
                            try:
                                logger.info(f"[STARTUP] Retrying with original port {args.port}...")
                                socketio.run(
                                    app, 
                                    host=args.host, 
                                    port=args.port, 
                                    debug=args.debug,
                                    use_reloader=not args.no_reload,
                                    allow_unsafe_werkzeug=True,
                                    log_output=True
                                )
                                # If we reach here, we succeeded
                                return
                            except OSError:
                                logger.warning(f"[STARTUP] Port {args.port} is still in use after cleanup attempt")
                    else:
                        logger.warning(f"[STARTUP] The processes using port {args.port} are not Minerva processes")
                else:
                    logger.warning(f"[STARTUP] Could not identify processes using port {args.port}")
                
                # Try a few alternative ports
                alt_ports = [8000, 8080, 3000, 3001, 0]  # 0 means any available port
                
                for alt_port in alt_ports:
                    try:
                        if alt_port == 0:
                            logger.info("[STARTUP] Trying with any available port...")
                        else:
                            logger.info(f"[STARTUP] Trying alternative port: {alt_port}...")
                        
                        # Update the WebSocket URL for the new port
                        websocket_url = "ws://{host}:{port}/socket.io/".format(
                            host=args.host if args.host != '0.0.0.0' else 'localhost',
                            port=alt_port
                        )
                        logger.info(f"[STARTUP] WebSocket endpoint will be available at {websocket_url}")
                        
                        socketio.run(
                            app, 
                            host=args.host, 
                            port=alt_port, 
                            debug=args.debug,
                            use_reloader=not args.no_reload,
                            allow_unsafe_werkzeug=True,
                            log_output=True
                        )
                        
                        # If we get here, the server started successfully
                        break
                    except OSError as e2:
                        if "Address already in use" in str(e2) and alt_port != 0:
                            logger.warning(f"[STARTUP] Port {alt_port} is also in use, trying next...")
                        else:
                            # Re-raise if it's not a port conflict or we're out of alternatives
                            raise
            else:
                # Re-raise if it's not a port conflict
                raise
        
    except Exception as e:
        logger.error(f"[STARTUP] Error starting Minerva server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
