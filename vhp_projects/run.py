"""
VHP Patient Database — Application Entry Point
"""
import os
import subprocess
import sys
import threading

from app import create_app

app = create_app()

PORT = 8420
HOST = '127.0.0.1'


def open_browser():
    """Open the browser after a short delay to let the server start.

    On macOS, when running as a PyInstaller --windowed app there is no
    TTY, so the stdlib ``webbrowser`` module can silently fail.  We fall
    back to the macOS ``open`` command which works regardless.
    """
    import time
    time.sleep(1.5)

    url = f'http://{HOST}:{PORT}'

    if sys.platform == 'darwin':
        # 'open' is the most reliable way to launch a URL on macOS,
        # even from a no-console .app bundle.
        try:
            subprocess.Popen(['open', url])
            return
        except Exception:
            pass

    # Fallback for other platforms / if 'open' somehow fails
    import webbrowser
    webbrowser.open(url)


if __name__ == '__main__':
    # When running as a bundled .app (PyInstaller --windowed), there is no
    # console, so we must open the browser automatically.
    frozen = getattr(sys, 'frozen', False)

    # Always open the browser when launched as a packaged app;
    # also open it in normal runs so the experience is consistent.
    threading.Thread(target=open_browser, daemon=True).start()

    app.run(debug=not frozen, port=PORT, host=HOST)
