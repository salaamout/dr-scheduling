#!/bin/bash
# Build a standalone Mac application using PyInstaller
#
# Usage:
#   cd /Users/kyleeaton/dr_projects/vhp_projects
#   ./scripts/build_vhp_scheduling.sh
#
# Result:
#   dist/VHP Scheduling.app — copy to any Mac and double-click to run

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate the venv if it exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    echo "=== Activating virtual environment ==="
    source "$PROJECT_DIR/.venv/bin/activate"
fi

echo "=== Installing PyInstaller ==="
pip install pyinstaller

echo "=== Building VHP Scheduling.app ==="
pyinstaller --onedir --windowed \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "instance:instance" \
    --name "VHP Scheduling" \
    run.py

echo ""
echo "=== Build Complete ==="
echo "Application: dist/VHP Scheduling.app"
echo "Copy it to any Mac and double-click to run."
