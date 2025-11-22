#!/bin/bash

# Stop the viewer API server

PID_FILE="/tmp/viewer-server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Server is not running (no PID file found)"
    exit 0
fi

SERVER_PID=$(cat "$PID_FILE")

if ps -p "$SERVER_PID" > /dev/null 2>&1; then
    echo "Stopping server (PID: $SERVER_PID)..."
    kill "$SERVER_PID"
    rm "$PID_FILE"
    echo "✓ Server stopped"
else
    echo "Server is not running (stale PID file)"
    rm "$PID_FILE"
fi
