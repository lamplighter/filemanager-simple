#!/bin/bash

# File Queue Viewer Launcher
# Opens the HTML viewer in an isolated Chrome instance with file access enabled
# Also starts the API server in the background for approval functionality

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VIEWER_PATH="$PROJECT_ROOT/viewer.html"
SERVER_SCRIPT="$SCRIPT_DIR/viewer_server.py"
SERVER_PORT=8765
PID_FILE="/tmp/viewer-server.pid"

if [ ! -f "$VIEWER_PATH" ]; then
    echo "Error: viewer.html not found at $VIEWER_PATH"
    exit 1
fi

# Check if server is already running
SERVER_RUNNING=false

# First check if port is in use
if lsof -i :$SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    SERVER_PID=$(lsof -i :$SERVER_PORT -sTCP:LISTEN -t)
    SERVER_RUNNING=true
    echo "✓ API server already running on port $SERVER_PORT (PID: $SERVER_PID)"
    # Update PID file if it's missing or wrong
    echo $SERVER_PID > "$PID_FILE"
elif [ -f "$PID_FILE" ]; then
    # PID file exists but port not in use - clean up stale PID file
    rm "$PID_FILE"
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

echo "Opening file queue viewer with custom app..."
echo "Viewer URL: http://localhost:$SERVER_PORT/viewer.html"

# Launch the FileQueueViewer.app bundle (has custom icon)
open "$PROJECT_ROOT/FileQueueViewer.app"

echo "✓ Viewer opened with custom app icon"
echo ""
echo "Note: The viewer has full functionality:"
echo "  - Directory file listings work (API server running)"
echo "  - Approve/Reject buttons work (API server running)"
echo "  - Just refresh the browser to see queue updates"
echo ""
echo "API server will keep running in the background."
echo "To stop it: kill \$(cat $PID_FILE)"
