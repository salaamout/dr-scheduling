#!/usr/bin/env python3
"""
DEPRECATED — This launcher is deprecated. See scripts/build_app.sh
for the recommended PyInstaller method.

Launcher script for Patient Database Mac App
This script starts the Flask server and opens the browser
"""
import subprocess
import webbrowser
import time
import os
import sys
import signal
import socket
import shutil

def is_server_running(port):
    """Check if the server is running on the specified port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Use port 5001 instead of 5000 (5000 is often used by macOS Control Center)
    port = 5001
    
    # Check if server is already running
    if is_server_running(port):
        print(f"Server already running on port {port}")
        webbrowser.open(f'http://127.0.0.1:{port}')
        return
    
    # Start the Flask server
    print(f"Starting Patient Database server on port {port}...")
    
    # Use the same Python executable that's running this script
    python_cmd = sys.executable
    
    log_path = os.path.join(script_dir, 'server.log')
    log_file = None
    
    try:
        # Create a log file for the server output
        log_file = open(log_path, 'w')
        
        # Start the Flask server in the background
        server_process = subprocess.Popen(
            [python_cmd, 'patient_database.py'],
            env={**os.environ, 'FLASK_RUN_PORT': str(port)},
            stdout=log_file,
            stderr=log_file,
            start_new_session=True  # Detach from parent process
        )
        
        # Wait for server to start
        max_attempts = 30
        for i in range(max_attempts):
            if is_server_running(port):
                print("Server started successfully!")
                break
            time.sleep(0.5)
        else:
            print("Failed to start server")
            print(f"Check {log_path} for details")
            server_process.terminate()
            return
        
        # Open the browser
        print("Opening browser...")
        webbrowser.open(f'http://127.0.0.1:{port}')
        
        # Give the browser a moment to start opening
        time.sleep(1)
        
        print("\nPatient Database is running in the background!")
        print(f"Access it at: http://127.0.0.1:{port}")
        print(f"Server logs: {log_path}")
        print("\nYou can close this window - the server will keep running.")
    finally:
        if log_file is not None:
            log_file.close()
    
    # Exit cleanly - the server process will continue running in the background
    sys.exit(0)

if __name__ == '__main__':
    main()
