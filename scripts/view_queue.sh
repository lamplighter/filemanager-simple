#!/bin/bash

# File Queue Viewer Launcher
# Opens the HTML viewer in an isolated Chrome instance with file access enabled

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIEWER_PATH="$PROJECT_ROOT/viewer.html"
TEMP_USER_DATA="/tmp/chrome-fileviewer-$(date +%s)"

if [ ! -f "$VIEWER_PATH" ]; then
    echo "Error: viewer.html not found at $VIEWER_PATH"
    exit 1
fi

echo "Opening file queue viewer in isolated Chrome instance..."
echo "Viewer: $VIEWER_PATH"

# Launch Chrome directly with a temporary profile
# This creates an isolated instance that won't interfere with your main Chrome
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --allow-file-access-from-files \
    --user-data-dir="$TEMP_USER_DATA" \
    --no-first-run \
    --no-default-browser-check \
    "$VIEWER_PATH" &

echo "✓ Viewer opened in isolated Chrome instance"
echo ""
echo "Note: The viewer will auto-load state/file_queue.json"
echo "      Just refresh the browser to see updates to the queue."
echo "      This is a separate Chrome window with a temporary profile."
