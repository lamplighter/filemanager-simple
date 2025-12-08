#!/bin/bash
# Validates destination path against allowed whitelist
# Usage: ./scripts/validate_destination.sh <dest_path>
# Returns: 0 if valid, 1 if invalid (with error message)

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

DEST_PATH="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

if [[ -z "$DEST_PATH" ]]; then
    echo -e "${RED}ERROR: No destination path provided${NC}"
    echo "Usage: $0 <dest_path>"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}ERROR: Config file not found: $CONFIG_FILE${NC}"
    exit 1
fi

# Expand ~ to full path for the input
DEST_PATH="${DEST_PATH/#\~/$HOME}"

# Special case: "DELETE" is always allowed (for duplicate detection)
if [[ "$DEST_PATH" == "DELETE" ]]; then
    echo -e "${GREEN}OK: DELETE is a valid action${NC}"
    exit 0
fi

# Parse allowed_destinations from config
parse_allowed() {
    local in_section=false
    while IFS= read -r line; do
        if [[ "$line" =~ ^allowed_destinations: ]]; then
            in_section=true
            continue
        fi
        if [[ "$in_section" == true ]]; then
            # Stop at forbidden_destinations section or other top-level key
            if [[ "$line" =~ ^[a-zA-Z] && ! "$line" =~ ^[[:space:]] ]]; then
                break
            fi
            # Skip comment lines
            if [[ "$line" =~ ^[[:space:]]*# ]]; then
                continue
            fi
            # Extract path from "  - ~/path"
            if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*(.*) ]]; then
                local path="${BASH_REMATCH[1]}"
                # Expand ~ and remove trailing spaces/comments
                path="${path/#\~/$HOME}"
                path="${path%% #*}"
                path="${path%% *}"
                echo "$path"
            fi
        fi
    done < "$CONFIG_FILE"
}

# Check against allowed paths (whitelist)
while IFS= read -r allowed_path; do
    if [[ -n "$allowed_path" && "$DEST_PATH" == "$allowed_path"* ]]; then
        echo -e "${GREEN}OK: Destination allowed under $allowed_path${NC}"
        exit 0
    fi
done < <(parse_allowed)

# If we get here, path is not in allowed list
echo -e "${RED}ERROR: Destination not in allowed list: $DEST_PATH${NC}"
echo ""
echo "Allowed destination prefixes:"
parse_allowed | while read -r path; do
    echo "  - ${path/$HOME/~}"
done
exit 1
