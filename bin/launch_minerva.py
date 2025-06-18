#!/usr/bin/env python3
"""
Minerva Unified Launcher

This is the single entry point for all Minerva functionality.
It can launch the AI assistant, web server, or CLI interface.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional

# Ensure we're in the correct directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
os.chdir(PROJECT_ROOT)

# Add project root to Python path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def setup_environment():
    """Set up the environment for Minerva."""
    print(f"🔧 Setting up Minerva environment...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Ensure required directories exist
    required_dirs = [
        "minerva_logs",
        "data/chat_history",
        "data/memories",
        "data/memory_store",
        "web/static",
        "web/templates"
    ]
    
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ Environment setup complete")

def launch_ai_assistant(args):
    """Launch the Minerva AI Assistant."""
    print("🧠 Starting Minerva AI Assistant...")
    
    try:
        # Import and run the main AI assistant
        from minerva_main import main
        
        # Set up sys.argv for the AI assistant
        ai_args = ['minerva_main.py']
        if args.verbose:
            ai_args.append('--verbose')
        if args.discover:
            ai_args.extend(['--discover', args.discover])
        
        # Temporarily replace sys.argv
        original_argv = sys.argv
        sys.argv = ai_args
        
        try:
            main()
        finally:
            sys.argv = original_argv
            
    except ImportError as e:
        print(f"❌ Error importing AI assistant: {e}")
        print("Make sure all dependencies are installed.")
        return 1
    except Exception as e:
        print(f"❌ Error running AI assistant: {e}")
        return 1
    
    return 0

def launch_web_server(args):
    """Launch the Minerva Web Server."""
    print("🌐 Starting Minerva Web Server...")
    
    try:
        # Import the new server class
        from server import MinervaServer
        
        # Configure server settings
        host = args.host or '0.0.0.0'
        port = args.port or 5000
        debug = args.debug
        
        print(f"🚀 Starting server on {host}:{port}")
        print(f"🔧 Debug mode: {'enabled' if debug else 'disabled'}")
        
        # Create and run server
        server = MinervaServer(host=host, port=port, debug=debug)
        server.run()
        
    except ImportError as e:
        print(f"❌ Error importing web server: {e}")
        print("Make sure Flask and SocketIO dependencies are installed.")
        return 1
    except Exception as e:
        print(f"❌ Error running web server: {e}")
        return 1
    
    return 0

def launch_cli(args):
    """Launch the Minerva CLI."""
    print("💻 Starting Minerva CLI...")
    
    try:
        # Try to run the CLI
        cli_path = PROJECT_ROOT / "minerva_cli.py"
        if not cli_path.exists():
            print("❌ CLI not found. Creating basic CLI interface...")
            return create_basic_cli()
        
        # Run the existing CLI
        subprocess.run([sys.executable, str(cli_path)] + (args.cli_args or []))
        
    except Exception as e:
        print(f"❌ Error running CLI: {e}")
        return 1
    
    return 0

def create_basic_cli():
    """Create a basic CLI interface if none exists."""
    print("Creating basic CLI interface...")
    
    try:
        from minerva_main import MinervaAI
        
        # Initialize Minerva
        minerva = MinervaAI()
        
        print("\n" + "=" * 50)
        print(" Minerva AI Assistant - Basic CLI")
        print("=" * 50)
        print("Type 'exit' to quit, 'help' for commands")
        
        while True:
            try:
                user_input = input("\nMinerva> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                elif user_input.lower() in ['help', 'h']:
                    print("\nAvailable commands:")
                    print("  help - Show this help")
                    print("  exit - Exit the CLI")
                    print("  Any other text - Process as AI query")
                elif user_input:
                    # Start a conversation and get response
                    conversation = minerva.start_conversation()
                    conv_id = conversation['conversation_id']
                    
                    # Add user message
                    minerva.add_message(conv_id, "user", user_input)
                    
                    # Generate response
                    response = minerva.generate_response(conv_id)
                    print(f"\nMinerva: {response}")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except EOFError:
                print("\n\nGoodbye!")
                break
        
        minerva.shutdown()
        return 0
        
    except Exception as e:
        print(f"❌ Error creating basic CLI: {e}")
        return 1

def show_status():
    """Show Minerva system status."""
    print("\n" + "=" * 50)
    print(" Minerva System Status")
    print("=" * 50)
    
    # Check components
    components = {
        "AI Assistant": "core/minerva_main.py",
        "Web Server": "server/minerva_server.py", 
        "CLI": "minerva_cli.py",
        "Coordinator": "core/coordinator.py",
        "Memory Manager": "memory/unified_memory_manager.py"
    }
    
    for name, file_path in components.items():
        if (PROJECT_ROOT / file_path).exists():
            print(f"✅ {name}: Available")
        else:
            print(f"❌ {name}: Not found")
    
    # Check directories
    directories = [
        "bin", "core", "models", "memory", "frameworks",
        "server", "data", "web", "utils", "tests"
    ]
    
    print(f"\n📁 Directories:")
    for dir_name in directories:
        if (PROJECT_ROOT / dir_name).exists():
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (missing)")
    
    print(f"\n📍 Project root: {PROJECT_ROOT}")

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="Minerva AI Assistant - Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ai                     # Start AI assistant
  %(prog)s server                 # Start web server  
  %(prog)s server --port 8080     # Start server on port 8080
  %(prog)s cli                    # Start CLI interface
  %(prog)s status                 # Show system status
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['ai', 'server', 'cli', 'status'],
        help='Launch mode: ai=AI Assistant, server=Web Server, cli=CLI Interface, status=System Status'
    )
    
    # AI Assistant options
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='Enable verbose logging (AI mode)')
    parser.add_argument('--discover', '-d', 
                      help='Discover frameworks in directory (AI mode)')
    
    # Web Server options  
    parser.add_argument('--host', default='0.0.0.0',
                      help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000,
                      help='Server port (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug mode (server mode)')
    
    # CLI options
    parser.add_argument('--cli-args', nargs='*',
                      help='Arguments to pass to CLI')
    
    args = parser.parse_args()
    
    # Set up environment
    setup_environment()
    
    # Show banner
    print("\n" + "=" * 50)
    print(" 🌟 Minerva AI Assistant")
    print("=" * 50)
    
    # Route to appropriate launcher
    if args.mode == 'ai':
        return launch_ai_assistant(args)
    elif args.mode == 'server':
        return launch_web_server(args)
    elif args.mode == 'cli':
        return launch_cli(args)
    elif args.mode == 'status':
        show_status()
        return 0
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 