#!/bin/bash
# Build FileQueueViewer without needing sudo xcode-select
# Uses DEVELOPER_DIR environment variable to point to Xcode

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
XCODE_PATH="/Applications/Xcode.app/Contents/Developer"

if [ ! -d "$XCODE_PATH" ]; then
    echo "Error: Xcode not found at $XCODE_PATH"
    echo "Install Xcode from the App Store first."
    exit 1
fi

echo "Building FileQueueViewer..."

DEVELOPER_DIR="$XCODE_PATH" xcodebuild \
    -project "$PROJECT_DIR/FileQueueViewer.xcodeproj" \
    -scheme FileQueueViewer \
    -configuration Release \
    build \
    2>&1 | grep -E "(error:|warning:|BUILD|Compiling)" || true

# Find and copy the built app
BUILT_APP=$(find ~/Library/Developer/Xcode/DerivedData -name "FileQueueViewer.app" -path "*/Release/*" 2>/dev/null | head -1)

if [ -n "$BUILT_APP" ] && [ -d "$BUILT_APP" ]; then
    cp -r "$BUILT_APP" "$PROJECT_DIR/"
    echo ""
    echo "Build successful!"
    echo "App location: $PROJECT_DIR/FileQueueViewer.app"
    echo ""
    echo "To launch: open $PROJECT_DIR/FileQueueViewer.app"
else
    echo "Build may have failed - check output above"
    exit 1
fi
