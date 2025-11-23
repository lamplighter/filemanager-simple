#!/bin/bash

# find_duplicates.sh
# Find duplicate files based on SHA256 checksum
# Usage: ./find_duplicates.sh <source_file> <destination_directory>
#
# Searches for duplicate files:
# 1. In the destination directory (and subdirectories)
# 2. In the pending file queue (state/file_queue.json)
#
# Returns JSON with duplicate information:
# {
#   "source_checksum": "abc123...",
#   "duplicates": [
#     {"path": "/path/to/duplicate1.pdf", "location": "destination"},
#     {"path": "/path/to/duplicate2.pdf", "location": "queue"}
#   ]
# }

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check arguments
if [ $# -lt 2 ]; then
    echo '{"error": "Usage: ./find_duplicates.sh <source_file> <destination_directory>"}' >&2
    exit 1
fi

SOURCE_FILE="$1"
DEST_DIR="$2"

# Expand ~ to full path
SOURCE_FILE="${SOURCE_FILE/#\~/$HOME}"
DEST_DIR="${DEST_DIR/#\~/$HOME}"

# Check if source file exists
if [ ! -f "$SOURCE_FILE" ]; then
    echo "{\"error\": \"Source file not found: $SOURCE_FILE\"}" >&2
    exit 1
fi

# Calculate source file checksum
SOURCE_CHECKSUM=$("$SCRIPT_DIR/calculate_checksum.sh" "$SOURCE_FILE" 2>/dev/null)
if [ $? -ne 0 ] || [ -z "$SOURCE_CHECKSUM" ]; then
    echo "{\"error\": \"Failed to calculate checksum for: $SOURCE_FILE\"}" >&2
    exit 1
fi

# Array to store duplicate paths
DUPLICATES=()

# Function to add duplicate to array
add_duplicate() {
    local path="$1"
    local location="$2"
    DUPLICATES+=("{\"path\": \"$path\", \"location\": \"$location\"}")
}

# 1. Search in destination directory for files with matching checksum
if [ -d "$DEST_DIR" ]; then
    while IFS= read -r -d '' file; do
        # Skip the source file itself
        if [ "$file" = "$SOURCE_FILE" ]; then
            continue
        fi

        FILE_CHECKSUM=$("$SCRIPT_DIR/calculate_checksum.sh" "$file" 2>/dev/null || echo "")
        if [ "$FILE_CHECKSUM" = "$SOURCE_CHECKSUM" ]; then
            add_duplicate "$file" "destination"
        fi
    done < <(find "$DEST_DIR" -type f -print0 2>/dev/null)
fi

# 2. Search in pending queue for files with matching checksum
QUEUE_FILE="$PROJECT_ROOT/state/file_queue.json"
if [ -f "$QUEUE_FILE" ]; then
    # Extract pending/approved source_paths from queue using Python
    QUEUE_SOURCES=$(python3 -c "
import json
import sys

try:
    with open('$QUEUE_FILE', 'r') as f:
        queue = json.load(f)

    for file_entry in queue.get('files', []):
        status = file_entry.get('status', '')
        if status in ['pending', 'approved']:
            source_path = file_entry.get('source_path', '')
            if source_path:
                print(source_path)
except Exception as e:
    print(f'Error reading queue: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)

    # Check each queued file's checksum
    while IFS= read -r queued_file; do
        if [ -n "$queued_file" ] && [ -f "$queued_file" ]; then
            QUEUED_CHECKSUM=$("$SCRIPT_DIR/calculate_checksum.sh" "$queued_file" 2>/dev/null || echo "")
            if [ "$QUEUED_CHECKSUM" = "$SOURCE_CHECKSUM" ]; then
                # Don't count the source file itself as a duplicate
                if [ "$queued_file" != "$SOURCE_FILE" ]; then
                    add_duplicate "$queued_file" "queue"
                fi
            fi
        fi
    done <<< "$QUEUE_SOURCES"
fi

# Build JSON output
DUPLICATES_JSON=$(IFS=,; echo "${DUPLICATES[*]}")
if [ -z "$DUPLICATES_JSON" ]; then
    DUPLICATES_JSON=""
fi

cat << EOF
{
  "source_checksum": "$SOURCE_CHECKSUM",
  "duplicates": [$DUPLICATES_JSON]
}
EOF
