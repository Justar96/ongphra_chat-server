#!/usr/bin/env python
# run_chat_interface.py
import os
import sys
import subprocess
import argparse

def main():
    """Run the chat interface"""
    parser = argparse.ArgumentParser(description="Run the Fortune Telling Chat Interface")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the command
    cmd = [
        sys.executable,
        os.path.join(current_dir, "chat_interface.py"),
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    if args.debug:
        cmd.append("--debug")
    
    # Print startup message
    print(f"Starting Fortune Telling Chat Interface on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    # Run the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    main() 