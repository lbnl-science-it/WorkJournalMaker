#!/bin/bash
# ABOUTME: Creates a macOS .dmg installer from the PyInstaller .app bundle
# ABOUTME: Wraps create-dmg with project-specific settings

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="WorkJournalMaker"
APP_PATH="$PROJECT_ROOT/dist/${APP_NAME}.app"
DMG_OUTPUT="$PROJECT_ROOT/dist/${APP_NAME}.dmg"
VOLUME_NAME="Work Journal Maker"

# Verify .app exists
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: $APP_PATH not found. Run PyInstaller build first."
    exit 1
fi

# Remove old DMG if it exists
rm -f "$DMG_OUTPUT"

echo "Creating DMG installer..."

create-dmg \
    --volname "$VOLUME_NAME" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 150 190 \
    --app-drop-link 450 190 \
    --no-internet-enable \
    "$DMG_OUTPUT" \
    "$APP_PATH"

echo "DMG created: $DMG_OUTPUT"
echo "Size: $(du -h "$DMG_OUTPUT" | cut -f1)"
