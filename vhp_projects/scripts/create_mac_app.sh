#!/bin/bash
# DEPRECATED — This approach is deprecated. See scripts/build_app.sh
# for the recommended PyInstaller method.
#
# Script to create a Mac .app bundle for the Patient Database

APP_NAME="Patient Database"
APP_DIR="$HOME/Desktop/${APP_NAME}.app"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Creating Mac app: ${APP_NAME}"

# Remove existing app if it exists
if [ -d "$APP_DIR" ]; then
    echo "Removing existing app..."
    rm -rf "$APP_DIR"
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Copy all project files to Resources
echo "Copying project files..."
cp -r "$CURRENT_DIR"/* "$RESOURCES_DIR/" 2>/dev/null || true
cp -r "$CURRENT_DIR"/.[^.]* "$RESOURCES_DIR/" 2>/dev/null || true

# Create the launcher script
echo "Creating launcher script..."
cat > "$MACOS_DIR/launch" << 'LAUNCHER_EOF'
#!/bin/bash

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RESOURCES_DIR="$DIR/../Resources"

# Change to the resources directory
cd "$RESOURCES_DIR"

# Launch the Python application
# First, try to find and use radioconda Python (where dependencies are installed)
if [ -f "$HOME/radioconda/bin/python" ]; then
    "$HOME/radioconda/bin/python" launch_app.py
elif [ -f "$HOME/miniforge3/bin/python" ]; then
    "$HOME/miniforge3/bin/python" launch_app.py
elif [ -f "$HOME/miniconda3/bin/python" ]; then
    "$HOME/miniconda3/bin/python" launch_app.py
elif [ -f "$HOME/anaconda3/bin/python" ]; then
    "$HOME/anaconda3/bin/python" launch_app.py
elif command -v python &> /dev/null; then
    python launch_app.py
else
    python3 launch_app.py
fi
LAUNCHER_EOF

# Make the launcher executable
chmod +x "$MACOS_DIR/launch"

# Create Info.plist
echo "Creating Info.plist..."
cat > "$CONTENTS_DIR/Info.plist" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Patient Database</string>
    <key>CFBundleDisplayName</key>
    <string>Patient Database</string>
    <key>CFBundleIdentifier</key>
    <string>com.vhp.patientdatabase</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST_EOF

# Create a simple icon (you can replace this with a custom icon later)
echo "Creating app icon..."
cat > "$RESOURCES_DIR/create_icon.py" << 'ICON_EOF'
#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple icon
size = 512
img = Image.new('RGB', (size, size), color='#4A90E2')
draw = ImageDraw.Draw(img)

# Draw a medical cross
cross_color = 'white'
thickness = 60
center = size // 2

# Vertical bar
draw.rectangle([center - thickness//2, 100, center + thickness//2, size - 100], fill=cross_color)
# Horizontal bar
draw.rectangle([100, center - thickness//2, size - 100, center + thickness//2], fill=cross_color)

# Save as icns (if sips is available) or png
icon_path = os.path.join(os.path.dirname(__file__), 'AppIcon.png')
img.save(icon_path)
print(f"Icon saved to {icon_path}")

# Try to convert to icns using sips
icns_path = os.path.join(os.path.dirname(__file__), 'AppIcon.icns')
os.system(f'sips -s format icns "{icon_path}" --out "{icns_path}" 2>/dev/null')
ICON_EOF

# Try to create the icon if PIL is available
python3 "$RESOURCES_DIR/create_icon.py" 2>/dev/null || {
    echo "Note: Could not create custom icon (PIL not installed). Using default icon."
}

# Clean up
rm -f "$RESOURCES_DIR/create_icon.py"

echo ""
echo "✓ Mac app created successfully!"
echo "Location: $APP_DIR"
echo ""
echo "You can now double-click the app on your Desktop to launch the Patient Database."
echo "The app will start a local server and open your default web browser."
echo ""
