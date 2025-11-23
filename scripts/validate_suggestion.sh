#!/bin/bash

##############################################################################
# Validate File Organization Suggestion
#
# Helper script for Claude to validate file organization suggestions before
# adding them to the queue. Checks source file existence, destination validity,
# and potential issues.
#
# Usage:
#   ./validate_suggestion.sh <source_path> <dest_path>
#
# Exit codes:
#   0 - Validation passed
#   1 - Validation failed
##############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/../config.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse YAML config
parse_yaml() {
    local prefix=$1
    local file=$2
    local s='[[:space:]]*'
    local w='[a-zA-Z0-9_]*'
    local fs=$(echo @|tr @ '\034')

    sed -ne "s|^\($s\):|\1|" \
         -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
         -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p" "$file" |
    awk -F"$fs" '{
        indent = length($1)/2;
        vname[indent] = $2;
        for (i in vname) {if (i > indent) {delete vname[i]}}
        if (length($3) > 0) {
            vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
            printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
        }
    }'
}

# Load config
eval "$(parse_yaml "CONFIG_" "$CONFIG_FILE")"

# Expand destination roots
CONFIG_filing_root="${CONFIG_filing_root/#\~/$HOME}"
CONFIG_taxes_root="${CONFIG_taxes_root:-}"
if [[ -n "$CONFIG_taxes_root" ]]; then
    CONFIG_taxes_root="${CONFIG_taxes_root/#\~/$HOME}"
fi

# Check arguments
if [[ $# -lt 2 ]]; then
    echo -e "${RED}Error: Missing arguments${NC}"
    echo "Usage: $0 <source_path> <dest_path>"
    exit 1
fi

SOURCE_PATH="${1/#\~/$HOME}"
DEST_PATH="${2/#\~/$HOME}"

# Track validation results
ERRORS=0
WARNINGS=0

# Check if this is a DELETE action
IS_DELETE=false
if [[ "$DEST_PATH" == "DELETE" ]]; then
    IS_DELETE=true
fi

echo "Validating file organization suggestion..."
echo "  Source: $SOURCE_PATH"
if [[ "$IS_DELETE" == true ]]; then
    echo "  Action: DELETE (duplicate)"
else
    echo "  Dest:   $DEST_PATH"
fi
echo ""

##############################################################################
# Validation Checks
##############################################################################

# Check 1: Source file exists
if [[ ! -f "$SOURCE_PATH" ]]; then
    echo -e "${RED}✗ Source file does not exist${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Source file exists${NC}"

    # Get file info
    FILE_SIZE=$(stat -f%z "$SOURCE_PATH" 2>/dev/null || stat -c%s "$SOURCE_PATH" 2>/dev/null || echo "unknown")
    echo "  Size: $FILE_SIZE bytes"
fi

# Check 2: Source file is readable
if [[ -f "$SOURCE_PATH" ]] && [[ ! -r "$SOURCE_PATH" ]]; then
    echo -e "${RED}✗ Source file is not readable${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Source file is readable${NC}"
fi

# Check 3: Destination path structure (skip for DELETE actions)
if [[ "$IS_DELETE" == true ]]; then
    echo -e "${GREEN}✓ DELETE action - destination checks skipped${NC}"
else
    DEST_DIR=$(dirname "$DEST_PATH")

    if [[ ! "$DEST_PATH" =~ ^/ ]]; then
        echo -e "${YELLOW}⚠ Destination path is not absolute${NC}"
        ((WARNINGS++))
    fi
fi

# Skip remaining destination checks if DELETE action
if [[ "$IS_DELETE" == true ]]; then
    # All validations passed for DELETE action
    echo ""
    if [[ $ERRORS -eq 0 ]]; then
        echo -e "${GREEN}✓ Validation passed (DELETE action)${NC}"
        echo -e "${YELLOW}→ Source file will be deleted (duplicate)${NC}"
        exit 0
    else
        echo -e "${RED}✗ Validation failed with $ERRORS error(s)${NC}"
        exit 1
    fi
fi

DEST_DIR=$(dirname "$DEST_PATH")

# Check 4: Destination directory exists or can be created
if [[ -d "$DEST_DIR" ]]; then
    echo -e "${GREEN}✓ Destination directory exists${NC}"
elif [[ -e "$DEST_DIR" ]] && [[ ! -d "$DEST_DIR" ]]; then
    echo -e "${RED}✗ Destination parent path exists but is not a directory${NC}"
    ((ERRORS++))
else
    echo -e "${YELLOW}⚠ Destination directory does not exist (will be created)${NC}"
    ((WARNINGS++))

    # Check if we can create it
    PARENT_DIR=$(dirname "$DEST_DIR")
    if [[ ! -d "$PARENT_DIR" ]]; then
        echo -e "${YELLOW}  ⚠ Multiple levels of directories need to be created${NC}"
    fi
fi

# Check 5: Write permissions
if [[ -d "$DEST_DIR" ]] && [[ ! -w "$DEST_DIR" ]]; then
    echo -e "${RED}✗ No write permission on destination directory${NC}"
    ((ERRORS++))
else
    echo -e "${GREEN}✓ Destination directory is writable${NC}"
fi

# Check 6: Destination file already exists
if [[ -f "$DEST_PATH" ]]; then
    echo -e "${YELLOW}⚠ Destination file already exists (conflict will be handled during execution)${NC}"
    ((WARNINGS++))

    # Compare file sizes
    if [[ -f "$SOURCE_PATH" ]]; then
        DEST_SIZE=$(stat -f%z "$DEST_PATH" 2>/dev/null || stat -c%s "$DEST_PATH" 2>/dev/null || echo "unknown")
        if [[ "$FILE_SIZE" == "$DEST_SIZE" ]]; then
            echo -e "${YELLOW}  ⚠ Files have the same size (possible duplicate)${NC}"

            # Compare checksums to verify if it's a true duplicate
            if [[ -x "$SCRIPT_DIR/calculate_checksum.sh" ]]; then
                SOURCE_HASH=$("$SCRIPT_DIR/calculate_checksum.sh" "$SOURCE_PATH" 2>/dev/null || echo "")
                DEST_HASH=$("$SCRIPT_DIR/calculate_checksum.sh" "$DEST_PATH" 2>/dev/null || echo "")

                if [[ -n "$SOURCE_HASH" ]] && [[ -n "$DEST_HASH" ]] && [[ "$SOURCE_HASH" == "$DEST_HASH" ]]; then
                    echo -e "${RED}  ✗ FILES ARE IDENTICAL (same SHA256 checksum)${NC}"
                    echo -e "${YELLOW}  → Consider using dest_path=\"DELETE\" for duplicates${NC}"
                    ((ERRORS++))
                elif [[ -n "$SOURCE_HASH" ]] && [[ -n "$DEST_HASH" ]]; then
                    echo -e "${GREEN}  ✓ Files have different content (not duplicates)${NC}"
                fi
            fi
        fi
    fi
fi

# Check 7: File extension vs destination folder type
SOURCE_EXT="${SOURCE_PATH##*.}"
SOURCE_BASENAME=$(basename "$SOURCE_PATH")

# Warn if extension seems mismatched with destination
if [[ "$SOURCE_EXT" == "dmg" ]] && [[ ! "$DEST_PATH" =~ installer ]]; then
    echo -e "${YELLOW}⚠ DMG file not going to installers folder${NC}"
    ((WARNINGS++))
fi

if [[ "$SOURCE_EXT" =~ ^(png|jpg|jpeg|gif|bmp)$ ]] && [[ "$SOURCE_BASENAME" =~ Screenshot|Screen\ Shot ]]; then
    if [[ ! "$DEST_PATH" =~ screenshot ]]; then
        echo -e "${YELLOW}⚠ Screenshot not going to screenshots folder${NC}"
        ((WARNINGS++))
    fi
fi

# Check 8: Destination is under a known root
VALID_LOCATION=false

# Check against filing_root
if [[ -n "$CONFIG_filing_root" ]] && [[ "$DEST_PATH" =~ ^${CONFIG_filing_root} ]]; then
    VALID_LOCATION=true
fi

# Check against taxes_root
if [[ -n "$CONFIG_taxes_root" ]] && [[ "$DEST_PATH" =~ ^${CONFIG_taxes_root} ]]; then
    VALID_LOCATION=true
fi

# Check against special directories
if [[ "$DEST_PATH" =~ Files/installers ]] || \
   [[ "$DEST_PATH" =~ Files/screenshots ]] || \
   [[ "$DEST_PATH" =~ Files/unknown ]]; then
    VALID_LOCATION=true
fi

if [[ "$VALID_LOCATION" == "false" ]]; then
    echo -e "${YELLOW}⚠ Destination is not in a known filing location${NC}"
    expected_locations="$CONFIG_filing_root"
    if [[ -n "$CONFIG_taxes_root" ]]; then
        expected_locations="$expected_locations, $CONFIG_taxes_root"
    fi
    echo "  Expected under: $expected_locations or ~/Files/*"
    ((WARNINGS++))
fi

# Check 9: Filename contains problematic characters
if [[ "$DEST_PATH" =~ [\\\:\*\?\"\<\>\|] ]]; then
    echo -e "${RED}✗ Destination filename contains invalid characters${NC}"
    ((ERRORS++))
fi

# Check 10: Very long filename
DEST_FILENAME=$(basename "$DEST_PATH")
if [[ ${#DEST_FILENAME} -gt 200 ]]; then
    echo -e "${YELLOW}⚠ Destination filename is very long (${#DEST_FILENAME} chars)${NC}"
    ((WARNINGS++))
fi

# Check 11: Source and destination are the same
if [[ "$SOURCE_PATH" == "$DEST_PATH" ]]; then
    echo -e "${RED}✗ Source and destination are the same${NC}"
    ((ERRORS++))
fi

# Check 12: Destination filename contains problematic patterns
if [[ "$DEST_FILENAME" =~ \(1\)|\(2\) ]] || [[ "$DEST_FILENAME" =~ ^_ ]]; then
    echo -e "${YELLOW}⚠ Destination filename contains version numbers or leading underscores${NC}"
    echo "  Consider: $(echo "$DEST_FILENAME" | sed 's/ ([0-9]*)//g' | sed 's/^_//')"
    ((WARNINGS++))
fi

##############################################################################
# Summary
##############################################################################

echo ""
echo "Validation Summary:"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"
echo ""

if [[ $ERRORS -gt 0 ]]; then
    echo -e "${RED}✗ Validation FAILED - Please fix errors before adding to queue${NC}"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}✓ Validation PASSED with warnings - Review warnings before proceeding${NC}"
    exit 0
else
    echo -e "${GREEN}✓ Validation PASSED - Safe to add to queue${NC}"
    exit 0
fi
