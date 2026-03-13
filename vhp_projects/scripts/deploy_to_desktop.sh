#!/bin/bash
# Build the VHP Scheduling app and deploy it to the Desktop.
#
# Usage:
#   cd /Users/kyleeaton/dr_projects/vhp_projects
#   ./scripts/deploy_to_desktop.sh
#
# This is the one command to run when you hear:
#   "rebuild the app and replace the one on the desktop"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="VHP Scheduling"
DESKTOP_APP="$HOME/Desktop/${APP_NAME}.app"

cd "$PROJECT_DIR"

# Activate venv
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    echo "=== Activating virtual environment ==="
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Install/upgrade PyInstaller
echo "=== Ensuring PyInstaller is installed ==="
pip install --quiet pyinstaller

# Build
echo "=== Building ${APP_NAME}.app ==="
pyinstaller --noconfirm "${APP_NAME}.spec"

# Deploy to Desktop
echo "=== Deploying to Desktop ==="
if [ -d "$DESKTOP_APP" ]; then
    echo "    Removing old ${APP_NAME}.app from Desktop..."
    rm -rf "$DESKTOP_APP"
fi

cp -R "dist/${APP_NAME}.app" "$DESKTOP_APP"

echo ""
echo "=== Done! ==="
echo "  ${APP_NAME}.app has been rebuilt and placed on your Desktop."
