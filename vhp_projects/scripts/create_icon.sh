#!/bin/bash
# DEPRECATED — This approach is deprecated. See scripts/build_app.sh
# for the recommended PyInstaller method.
#
# Create a simple custom icon for the Patient Database app

ICON_DIR="/tmp/icon.iconset"
APP_ICON_PATH="$HOME/Desktop/Patient Database.app/Contents/Resources/AppIcon.icns"

# Remove old iconset if it exists
rm -rf "$ICON_DIR"
mkdir -p "$ICON_DIR"

# Create a simple SVG icon
cat > /tmp/icon.svg << 'SVG_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="512" height="512" fill="#4A90E2" rx="90"/>
  
  <!-- Medical Cross -->
  <rect x="206" y="100" width="100" height="312" fill="white" rx="10"/>
  <rect x="100" y="206" width="312" height="100" fill="white" rx="10"/>
  
  <!-- Accent circles at cross ends -->
  <circle cx="256" cy="100" r="30" fill="#2E5C8A"/>
  <circle cx="256" cy="412" r="30" fill="#2E5C8A"/>
  <circle cx="100" cy="256" r="30" fill="#2E5C8A"/>
  <circle cx="412" cy="256" r="30" fill="#2E5C8A"/>
</svg>
SVG_EOF

# Convert SVG to different sizes using sips and qlmanage
for size in 16 32 64 128 256 512; do
    size2x=$((size * 2))
    
    # Convert SVG to PNG at required size
    qlmanage -t -s $size -o "$ICON_DIR" /tmp/icon.svg 2>/dev/null
    if [ -f "$ICON_DIR/icon.svg.png" ]; then
        mv "$ICON_DIR/icon.svg.png" "$ICON_DIR/icon_${size}x${size}.png"
    fi
    
    # Create @2x version
    qlmanage -t -s $size2x -o "$ICON_DIR" /tmp/icon.svg 2>/dev/null
    if [ -f "$ICON_DIR/icon.svg.png" ]; then
        mv "$ICON_DIR/icon.svg.png" "$ICON_DIR/icon_${size}x${size}@2x.png"
    fi
done

# Convert iconset to icns
if [ -d "$ICON_DIR" ] && [ "$(ls -A $ICON_DIR)" ]; then
    iconutil -c icns "$ICON_DIR" -o "$APP_ICON_PATH" 2>/dev/null && {
        echo "✓ Custom icon created successfully!"
    } || {
        echo "Note: Could not create .icns file. Using default icon."
    }
else
    echo "Note: Could not create icon files. Using default icon."
fi

# Clean up
rm -rf "$ICON_DIR"
rm -f /tmp/icon.svg

# Refresh Desktop to show new icon
killall Finder 2>/dev/null || true

echo "Icon installation complete!"
