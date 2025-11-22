#!/bin/bash

# File Queue Viewer Launcher
# Opens the HTML viewer in an isolated Chrome instance with file access enabled
# Also starts the API server in the background for approval functionality

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIEWER_PATH="$PROJECT_ROOT/viewer.html"
SERVER_SCRIPT="$SCRIPT_DIR/viewer_server.py"
SERVER_PORT=8765
TEMP_USER_DATA="/tmp/chrome-fileviewer-$(date +%s)"
PID_FILE="/tmp/viewer-server.pid"

if [ ! -f "$VIEWER_PATH" ]; then
    echo "Error: viewer.html not found at $VIEWER_PATH"
    exit 1
fi

# Check if server is already running
SERVER_RUNNING=false
if [ -f "$PID_FILE" ]; then
    SERVER_PID=$(cat "$PID_FILE")
    if ps -p "$SERVER_PID" > /dev/null 2>&1; then
        SERVER_RUNNING=true
        echo "✓ API server already running (PID: $SERVER_PID)"
    else
        # Stale PID file, remove it
        rm "$PID_FILE"
    fi
fi

# Start server if not running
if [ "$SERVER_RUNNING" = false ]; then
    echo "Starting API server on port $SERVER_PORT..."
    python3 "$SERVER_SCRIPT" > /dev/null 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$PID_FILE"

    # Wait for server to start
    sleep 1

    if ps -p "$SERVER_PID" > /dev/null 2>&1; then
        echo "✓ API server started (PID: $SERVER_PID)"
    else
        echo "Error: Failed to start API server"
        rm "$PID_FILE"
        exit 1
    fi
fi

echo "Opening file queue viewer in isolated Chrome instance..."
echo "Viewer: $VIEWER_PATH"

# Launch Chrome in app mode with a temporary profile
# App mode gives a cleaner interface without browser chrome
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --app="http://localhost:$SERVER_PORT/viewer.html" \
    --allow-file-access-from-files \
    --user-data-dir="$TEMP_USER_DATA" \
    --no-first-run \
    --no-default-browser-check &

echo "✓ Viewer opened in isolated Chrome instance"
echo ""
echo "Note: The viewer has full functionality:"
echo "  - File previews work (file:// access enabled)"
echo "  - Approve/Reject buttons work (API server running)"
echo "  - Just refresh the browser to see queue updates"
echo ""
echo "API server will keep running in the background."
echo "To stop it: kill \$(cat $PID_FILE)"
