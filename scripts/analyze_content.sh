#!/bin/bash
# Content Analysis Wrapper Script
#
# Analyzes file content and outputs structured JSON with:
# - Content summary
# - Detected entities (TD, Rogers, etc.)
# - Detected dates
# - Suggested category
# - Confidence boost
#
# Usage:
#   ./scripts/analyze_content.sh <file_path>
#   ./scripts/analyze_content.sh <file_path> --pretty
#
# Example:
#   ./scripts/analyze_content.sh "/Users/marklampert/Downloads/Statement.pdf"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if file path provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file_path> [--pretty]" >&2
    echo "" >&2
    echo "Analyzes file content for organization decisions." >&2
    echo "" >&2
    echo "Arguments:" >&2
    echo "  file_path    Path to the file to analyze" >&2
    echo "  --pretty     Pretty-print JSON output" >&2
    exit 1
fi

# Run the Python script with uv
cd "$PROJECT_ROOT" && uv run python scripts/analyze_content.py "$@"
