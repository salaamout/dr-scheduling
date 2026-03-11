"""
Launcher for Medical Mission Logs.
Starts the Flask server and opens the browser automatically.
"""

import subprocess
import sys
import threading
import time
import webbrowser

URL = "http://localhost:9874"


def open_browser():
    """Wait for the server to start, then open the browser."""
    time.sleep(1.5)
    print(f"  Opening browser to {URL} ...")
    webbrowser.open(URL)


def main():
    # Make sure dependencies are installed
    try:
        import flask  # noqa: F401
        import fpdf   # noqa: F401
    except ImportError:
        print("\n  Installing required packages...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=sys.path[0] or ".",
        )
        print("  Packages installed!\n")

    # Open the browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run the app (this blocks until you quit)
    from app import app, init_db, start_backup_scheduler  # noqa: E402

    init_db()
    start_backup_scheduler()

    print("\n  ✅ Medical Mission Logs is running!")
    print(f"  Open your browser to: {URL}")
    print("  Press Ctrl+C to stop.\n")

    app.run(port=9874)


if __name__ == "__main__":
    main()
