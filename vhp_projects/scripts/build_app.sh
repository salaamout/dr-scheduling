#!/bin/bash
# Build a standalone Mac application using PyInstaller
#
# Usage:
#   cd /Users/kyleeaton/dr_projects/vhp_projects
#   ./scripts/build_app.sh
#
# Result:
#   dist/PatientDatabase.app — copy to any Mac and double-click to run

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Installing PyInstaller ==="
pip install pyinstaller

echo "=== Building PatientDatabase.app ==="
pyinstaller --onedir --windowed \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --add-data "instance:instance" \
    --name "PatientDatabase" \
    run.py

echo ""
echo "=== Build Complete ==="
echo "Application: dist/PatientDatabase.app"
echo "Copy it to any Mac and double-click to run."
