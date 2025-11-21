#!/bin/bash

# File Organization Execution Helper
# Executes approved mv commands from execution_log.md

set -e

EXECUTION_LOG="../logs/execution_log.md"
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n    Show what would be executed without doing it"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ ! -f "$EXECUTION_LOG" ]]; then
    echo "Error: $EXECUTION_LOG not found"
    exit 1
fi

echo "File Organization Executor"
echo "========================="
if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN MODE - No files will be moved"
fi
echo ""

# Extract pending mv commands (lines starting with [ ])
pending_commands=$(grep "^\[ \] mv" "$EXECUTION_LOG" | sed 's/^\[ \] //')

if [[ -z "$pending_commands" ]]; then
    echo "No pending commands found in $EXECUTION_LOG"
    exit 0
fi

echo "Found $(echo "$pending_commands" | wc -l) pending command(s):"
echo ""

# Process each command
while IFS= read -r cmd; do
    echo "Command: $cmd"
    
    # Extract source file from mv command
    source_file=$(echo "$cmd" | sed 's/mv "\([^"]*\)".*/\1/')
    
    if [[ ! -f "$source_file" ]]; then
        echo "  ❌ Source file not found: $source_file"
        # Mark as skipped in execution log
        if [[ "$DRY_RUN" != "true" ]]; then
            sed -i.bak "s|^\[ \] $cmd|[~] $cmd  # Skipped: $(date '+%Y-%m-%d %H:%M') - File not found|" "$EXECUTION_LOG"
        fi
        echo ""
        continue
    fi
    
    # Extract destination from mv command  
    dest_file=$(echo "$cmd" | sed 's/.*mv "[^"]*" "\([^"]*\)".*/\1/')
    dest_dir=$(dirname "$dest_file")
    
    # Create destination directory if needed
    if [[ ! -d "$dest_dir" ]]; then
        echo "  📁 Creating directory: $dest_dir"
        if [[ "$DRY_RUN" != "true" ]]; then
            mkdir -p "$dest_dir"
        fi
    fi
    
    # Execute the command
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  🔍 Would execute: $cmd"
    else
        echo "  ✅ Executing: $cmd"
        if eval "$cmd"; then
            # Mark as completed in execution log
            sed -i.bak "s|^\[ \] $cmd|[✓] $cmd  # Executed: $(date '+%Y-%m-%d %H:%M')|" "$EXECUTION_LOG"
            echo "  ✅ Success!"
        else
            # Mark as failed in execution log
            sed -i.bak "s|^\[ \] $cmd|[✗] $cmd  # Failed: $(date '+%Y-%m-%d %H:%M')|" "$EXECUTION_LOG"
            echo "  ❌ Failed!"
        fi
    fi
    
    echo ""
    
done <<< "$pending_commands"

echo "Execution complete!"
if [[ "$DRY_RUN" != "true" ]]; then
    echo "Check $EXECUTION_LOG for results."
fi