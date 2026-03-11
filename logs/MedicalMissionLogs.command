#!/bin/bash
# ───────────────────────────────────────────
#  Medical Mission Logs — macOS Launcher
#  Double-click this file to start the app.
# ───────────────────────────────────────────

# Move to the folder where this script lives
cd "$(dirname "$0")"

echo ""
echo "  ================================================"
echo "   Medical Mission Logs"
echo "  ================================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "  ❌ Python 3 is not installed."
    echo "  Please install it from https://www.python.org/downloads/"
    echo ""
    echo "  Press any key to close..."
    read -n 1
    exit 1
fi

# Install dependencies if needed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  📦 Installing required packages..."
    python3 -m pip install -r requirements.txt
    echo ""
fi

# Start the app (opens browser automatically)
python3 start.py
