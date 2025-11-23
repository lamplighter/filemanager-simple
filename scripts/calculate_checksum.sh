#!/bin/bash

# calculate_checksum.sh
# Calculate SHA256 checksum of a file
# Usage: ./calculate_checksum.sh <file_path>

set -e

# Check if file path is provided
if [ $# -eq 0 ]; then
    echo "Error: No file path provided" >&2
    echo "Usage: $0 <file_path>" >&2
    exit 1
fi

FILE_PATH="$1"

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File not found: $FILE_PATH" >&2
    exit 1
fi

# Check if shasum is available
if ! command -v shasum &> /dev/null; then
    echo "Error: shasum command not found" >&2
    exit 1
fi

# Calculate and return checksum
shasum -a 256 "$FILE_PATH" | awk '{print $1}'
