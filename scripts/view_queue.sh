#!/bin/bash

# File Queue Viewer Launcher
# Opens the HTML viewer with Chrome allowing local file access

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIEWER_PATH="$PROJECT_ROOT/viewer.html"

if [ ! -f "$VIEWER_PATH" ]; then
    echo "Error: viewer.html not found at $VIEWER_PATH"
    exit 1
fi

echo "Opening file queue viewer..."
echo "Viewer: $VIEWER_PATH"

# Open Chrome with file access enabled
# This allows the HTML to fetch the JSON file locally
open -a "Google Chrome" --args --allow-file-access-from-files "$VIEWER_PATH"

echo "✓ Viewer opened in Chrome"
echo ""
echo "Note: The viewer will auto-load state/file_queue.json"
echo "      Just refresh the browser to see updates to the queue."
