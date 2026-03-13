#!/bin/bash
# ============================================================
# Setup custom "Laser Band 5.5x11" paper size on macOS
# 
# Usage:  bash scripts/setup_laserband_paper.sh
#
# This creates a custom paper size (5.5" x 11") that appears
# in any Print dialog's Paper Size dropdown on this Mac.
# Run once per machine — the setting persists across reboots.
# ============================================================

PAPER_NAME="Laser Band 5.5x11"
# macOS stores dimensions in points (1 inch = 72 points)
WIDTH_PT=396    # 5.5 * 72
HEIGHT_PT=792   # 11  * 72
MARGIN_PT=0     # zero margins (printer may enforce a minimum)

PLIST="$HOME/Library/Preferences/com.apple.print.custompapers.plist"

echo "🏷️  Setting up custom paper size: \"$PAPER_NAME\" (5.5\" × 11\")"

# Check if the entry already exists
if [ -f "$PLIST" ]; then
    EXISTING=$(/usr/libexec/PlistBuddy -c "Print" "$PLIST" 2>/dev/null | grep -c "$PAPER_NAME" || true)
    if [ "$EXISTING" -gt 0 ]; then
        echo "✅ \"$PAPER_NAME\" already exists. Nothing to do."
        exit 0
    fi
fi

# Find the next available index
if [ -f "$PLIST" ]; then
    INDEX=$(/usr/libexec/PlistBuddy -c "Print" "$PLIST" 2>/dev/null | grep -c "Dict" || echo "0")
else
    INDEX=0
fi

# Add the custom paper size
/usr/libexec/PlistBuddy -c "Add :$INDEX dict" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :$INDEX:name string '$PAPER_NAME'" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:width real $WIDTH_PT" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:height real $HEIGHT_PT" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:top real $MARGIN_PT" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:bottom real $MARGIN_PT" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:left real $MARGIN_PT" "$PLIST"
/usr/libexec/PlistBuddy -c "Add :$INDEX:right real $MARGIN_PT" "$PLIST"

echo "✅ Custom paper size \"$PAPER_NAME\" created successfully!"
echo ""
echo "📋 To use it:"
echo "   1. Open the laserband print page in the app"
echo "   2. Press ⌘P (or click 'Print Laserband')"
echo "   3. In the Print dialog → Paper Size → select \"$PAPER_NAME\""
echo "   4. Set Orientation to Landscape if needed"
echo ""
echo "💡 This only needs to be run once per Mac."
