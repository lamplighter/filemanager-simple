#!/bin/bash

##############################################################################
# File Organization System - Main Script
#
# A unified script for organizing files with confidence-based routing.
#
# Usage:
#   ./organize.sh               Interactive mode
#   ./organize.sh --auto        Automatic mode (no prompts for medium confidence)
#   ./organize.sh --dry-run     Preview operations without executing
#   ./organize.sh --undo        Undo last batch of operations
#   ./organize.sh --status      Show current queue status
#   ./organize.sh --help        Show help
##############################################################################

set -euo pipefail

# Script directory resolution (works regardless of where script is called from)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# File paths
CONFIG_FILE="$SCRIPT_DIR/config.yaml"
QUEUE_FILE="$SCRIPT_DIR/state/file_queue.json"
HISTORY_FILE="$SCRIPT_DIR/state/history.json"

# Default options
DRY_RUN=false
AUTO_MODE=false
MODE="interactive"

# Color codes (only if terminal supports it)
if [[ -t 1 ]] && command -v tput &> /dev/null; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    BOLD=$(tput bold)
    RESET=$(tput sgr0)
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    BOLD=""
    RESET=""
fi

##############################################################################
# Helper Functions
##############################################################################

# Print error message and exit
error() {
    echo "${RED}Error: $1${RESET}" >&2
    exit 1
}

# Print warning message
warn() {
    echo "${YELLOW}Warning: $1${RESET}" >&2
}

# Print success message
success() {
    echo "${GREEN}✓ $1${RESET}"
}

# Print info message
info() {
    echo "${BLUE}ℹ $1${RESET}"
}

# Parse YAML config (simple key: value parser)
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

# Load configuration
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        error "Configuration file not found: $CONFIG_FILE"
    fi

    eval "$(parse_yaml "CONFIG_" "$CONFIG_FILE")"

    # Expand tildes in paths
    CONFIG_special_directories_installers="${CONFIG_special_directories_installers/#\~/$HOME}"
    CONFIG_special_directories_screenshots="${CONFIG_special_directories_screenshots/#\~/$HOME}"
    CONFIG_special_directories_unknown="${CONFIG_special_directories_unknown/#\~/$HOME}"
}

# Check if jq is available (required for JSON manipulation)
check_dependencies() {
    if ! command -v jq &> /dev/null; then
        error "jq is required but not installed. Install with: brew install jq"
    fi
}

# Validate source and destination paths
validate_paths() {
    local source_path="$1"
    local dest_path="$2"

    # Check source exists
    if [[ ! -f "$source_path" ]]; then
        return 1
    fi

    # Check destination directory exists or can be created
    local dest_dir=$(dirname "$dest_path")
    if [[ ! -d "$dest_dir" ]]; then
        if [[ "$DRY_RUN" == "false" ]]; then
            mkdir -p "$dest_dir" 2>/dev/null || return 1
        fi
    fi

    # Check write permissions
    if [[ ! -w "$dest_dir" ]] && [[ -d "$dest_dir" ]]; then
        return 1
    fi

    return 0
}

# Check if destination file exists and handle conflict
handle_conflict() {
    local dest_path="$1"

    if [[ ! -f "$dest_path" ]]; then
        echo "proceed"
        return 0
    fi

    # File exists - ask user what to do
    if [[ "$AUTO_MODE" == "true" ]]; then
        # In auto mode, rename
        echo "rename"
        return 0
    fi

    echo ""
    warn "Destination file already exists: $dest_path"
    echo "Options:"
    echo "  [O]verwrite - Replace existing file"
    echo "  [R]ename - Add number to new filename"
    echo "  [S]kip - Don't move this file"
    echo ""
    read -p "Choose action [O/R/S]: " -n 1 -r
    echo

    case $REPLY in
        [Oo])
            echo "overwrite"
            ;;
        [Rr])
            echo "rename"
            ;;
        *)
            echo "skip"
            ;;
    esac
}

# Get unique filename if conflict
get_unique_filename() {
    local dest_path="$1"
    local dir=$(dirname "$dest_path")
    local filename=$(basename "$dest_path")
    local name="${filename%.*}"
    local ext="${filename##*.}"

    # If no extension, treat whole thing as name
    if [[ "$name" == "$ext" ]]; then
        ext=""
    fi

    local counter=2
    local new_path="$dest_path"

    while [[ -f "$new_path" ]]; do
        if [[ -n "$ext" ]]; then
            new_path="$dir/${name}_${counter}.${ext}"
        else
            new_path="$dir/${filename}_${counter}"
        fi
        ((counter++))
    done

    echo "$new_path"
}

# Execute file move (with atomic operation attempt)
execute_delete() {
    local source="$1"
    local file_id="$2"
    local duplicate_of="$3"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would delete duplicate: $source"
        return 0
    fi

    # Calculate hash before deletion (for undo capability)
    local hash_before=""
    if command -v shasum &> /dev/null; then
        hash_before=$(shasum -a 256 "$source" | awk '{print $1}')
    fi

    # Perform the deletion
    if rm "$source" 2>/dev/null; then
        # Add to history for undo capability (note: can't undo deletions)
        local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # Update history.json
        local history=$(jq --arg id "$file_id" \
                           --arg source "$source" \
                           --arg executed_at "$timestamp" \
                           --arg hash_before "$hash_before" \
                           --arg duplicate_of "$duplicate_of" \
                           '.operations += [{
                               id: $id,
                               action: "delete",
                               source_path: $source,
                               duplicate_of: $duplicate_of,
                               executed_at: $executed_at,
                               hash_before: $hash_before,
                               can_undo: false
                           }]' "$HISTORY_FILE")
        echo "$history" > "$HISTORY_FILE"

        return 0
    else
        return 1
    fi
}

execute_move() {
    local source="$1"
    local dest="$2"
    local file_id="$3"

    # Ensure destination directory exists
    local dest_dir=$(dirname "$dest")
    mkdir -p "$dest_dir"

    # Check if source and dest are on same filesystem
    local source_fs=$(df "$source" | tail -1 | awk '{print $1}')
    local dest_fs=$(df "$dest_dir" | tail -1 | awk '{print $1}')

    if [[ "$DRY_RUN" == "true" ]]; then
        info "Would move: $source → $dest"
        return 0
    fi

    # Calculate hash before move (for undo capability)
    local hash_before=""
    if command -v shasum &> /dev/null; then
        hash_before=$(shasum -a 256 "$source" | awk '{print $1}')
    fi

    # Perform the move
    if mv "$source" "$dest" 2>/dev/null; then
        # Calculate hash after move
        local hash_after=""
        if command -v shasum &> /dev/null; then
            hash_after=$(shasum -a 256 "$dest" | awk '{print $1}')
        fi

        # Add to history for undo capability
        local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        local can_undo="true"

        # Check if hashes match
        if [[ -n "$hash_before" ]] && [[ -n "$hash_after" ]] && [[ "$hash_before" != "$hash_after" ]]; then
            can_undo="false"
        fi

        # Update history.json
        local history=$(jq --arg id "$file_id" \
                           --arg source "$source" \
                           --arg dest "$dest" \
                           --arg executed_at "$timestamp" \
                           --arg hash_before "$hash_before" \
                           --arg hash_after "$hash_after" \
                           --arg can_undo "$can_undo" \
                           '.operations += [{
                               id: $id,
                               source_path: $source,
                               dest_path: $dest,
                               executed_at: $executed_at,
                               hash_before: $hash_before,
                               hash_after: $hash_after,
                               can_undo: ($can_undo == "true")
                           }]' "$HISTORY_FILE")
        echo "$history" > "$HISTORY_FILE"

        return 0
    else
        return 1
    fi
}

# Update file status in queue
update_file_status() {
    local file_id="$1"
    local new_status="$2"

    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    local queue=$(jq --arg id "$file_id" \
                     --arg status "$new_status" \
                     '(.files[] | select(.id == $id) | .status) = $status' \
                     "$QUEUE_FILE")
    echo "$queue" > "$QUEUE_FILE"
}

##############################################################################
# Main Operations
##############################################################################

# Process file queue
process_queue() {
    # Read queue
    local total_files=$(jq '.files | length' "$QUEUE_FILE")

    if [[ "$total_files" -eq 0 ]]; then
        info "No files in queue. Run Claude to analyze files first."
        return 0
    fi

    echo "${BOLD}Processing $total_files file(s)...${RESET}"
    echo ""

    # Counters
    local processed=0
    local auto_approved=0
    local user_approved=0
    local skipped=0
    local failed=0

    # Get threshold values
    local auto_threshold=${CONFIG_thresholds_auto_approve:-90}
    local ask_threshold=${CONFIG_thresholds_ask_user:-50}

    # Process each file
    while IFS= read -r file_json; do
        local file_id=$(echo "$file_json" | jq -r '.id')
        local source_path=$(echo "$file_json" | jq -r '.source_path')
        local dest_path=$(echo "$file_json" | jq -r '.dest_path')
        local confidence=$(echo "$file_json" | jq -r '.confidence')
        local status=$(echo "$file_json" | jq -r '.status')
        local reasoning=$(echo "$file_json" | jq -r '.reasoning')
        local action_type=$(echo "$file_json" | jq -r '.action // "move"')
        local duplicate_of=$(echo "$file_json" | jq -r '.duplicate_of // [] | join(", ")')

        # Skip if not approved
        if [[ "$status" != "approved" ]]; then
            continue
        fi

        ((processed++))

        # Expand tildes
        source_path="${source_path/#\~/$HOME}"
        dest_path="${dest_path/#\~/$HOME}"

        # Check if this is a delete action
        local is_delete=false
        if [[ "$dest_path" == "DELETE" ]] || [[ "$action_type" == "delete" ]]; then
            is_delete=true
        fi

        echo "${BOLD}[$processed/$total_files]${RESET} $(basename "$source_path")"
        echo "  Confidence: ${confidence}%"
        if [[ "$is_delete" == true ]]; then
            echo "  Action: DELETE (duplicate)"
            if [[ -n "$duplicate_of" ]]; then
                echo "  Duplicate of: $duplicate_of"
            fi
        else
            echo "  Destination: $dest_path"
        fi

        # Validate source exists
        if [[ ! -f "$source_path" ]]; then
            warn "Source file not found, marking as failed"
            update_file_status "$file_id" "failed"
            ((failed++))
            echo ""
            continue
        fi

        # Determine action based on confidence
        local action="skip"

        if [[ $confidence -ge $auto_threshold ]]; then
            # High confidence - auto approve
            info "HIGH CONFIDENCE - Auto-approving"
            action="approve"
            ((auto_approved++))

        elif [[ $confidence -ge $ask_threshold ]]; then
            # Medium confidence - ask user (unless auto mode)
            if [[ "$AUTO_MODE" == "true" ]]; then
                info "MEDIUM CONFIDENCE - Skipping in auto mode"
                action="skip"
                ((skipped++))
            else
                warn "MEDIUM CONFIDENCE - Review needed"
                echo "  Reasoning: $reasoning"
                echo ""
                read -p "Approve this file organization? [Y/n]: " -n 1 -r
                echo

                if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
                    success "Approved by user"
                    action="approve"
                    ((user_approved++))
                else
                    warn "Rejected by user"
                    action="skip"
                    ((skipped++))
                fi
            fi

        else
            # Low confidence - move to unknown
            warn "LOW CONFIDENCE - Moving to unknown folder"
            local unknown_dir="${CONFIG_special_directories_unknown}"
            mkdir -p "$unknown_dir"
            dest_path="$unknown_dir/$(basename "$source_path")"
            action="approve"
        fi

        # Execute approved actions
        if [[ "$action" == "approve" ]]; then
            if [[ "$is_delete" == true ]]; then
                # Handle DELETE action for duplicates
                if execute_delete "$source_path" "$file_id" "$duplicate_of"; then
                    success "Deleted duplicate file"
                    update_file_status "$file_id" "deleted"
                else
                    error "Failed to delete file"
                    update_file_status "$file_id" "failed"
                    ((failed++))
                fi
            else
                # Handle normal MOVE action
                # Check for conflicts
                local conflict_action=$(handle_conflict "$dest_path")

                case $conflict_action in
                    "proceed"|"overwrite")
                        # Proceed with move
                        if execute_move "$source_path" "$dest_path" "$file_id"; then
                            success "Moved to $dest_path"
                            update_file_status "$file_id" "completed"
                        else
                            error "Failed to move file"
                            update_file_status "$file_id" "failed"
                            ((failed++))
                        fi
                        ;;
                    "rename")
                        # Get unique filename
                        local new_dest=$(get_unique_filename "$dest_path")
                        if execute_move "$source_path" "$new_dest" "$file_id"; then
                            success "Moved to $new_dest"
                            update_file_status "$file_id" "completed"
                        else
                            error "Failed to move file"
                            update_file_status "$file_id" "failed"
                            ((failed++))
                        fi
                        ;;
                    "skip")
                        warn "Skipped by user"
                        ((skipped++))
                        ;;
                esac
            fi
        fi

        echo ""

    done < <(jq -c '.files[]' "$QUEUE_FILE")

    # Print summary
    echo "${BOLD}Summary:${RESET}"
    echo "  Processed: $processed"
    echo "  Auto-approved: $auto_approved"
    echo "  User approved: $user_approved"
    echo "  Skipped: $skipped"
    echo "  Failed: $failed"

    if [[ $auto_approved -gt 0 ]] || [[ $user_approved -gt 0 ]]; then
        echo ""
        success "File organization complete!"
        echo "Run './organize.sh --undo' if you need to revert these changes."
    fi
}

# Show queue status
show_status() {
    local total=$(jq '.files | length' "$QUEUE_FILE")
    local pending_approval=$(jq '[.files[] | select(.status == "pending_approval")] | length' "$QUEUE_FILE")
    local approved=$(jq '[.files[] | select(.status == "approved")] | length' "$QUEUE_FILE")
    local rejected=$(jq '[.files[] | select(.status == "rejected")] | length' "$QUEUE_FILE")
    local completed=$(jq '[.files[] | select(.status == "completed")] | length' "$QUEUE_FILE")
    local failed=$(jq '[.files[] | select(.status == "failed")] | length' "$QUEUE_FILE")

    echo "${BOLD}Queue Status:${RESET}"
    echo "  Total files: $total"
    echo "  Pending Approval: $pending_approval"
    echo "  Approved (ready to move): $approved"
    echo "  Rejected: $rejected"
    echo "  Completed: $completed"
    echo "  Failed: $failed"
    echo ""

    if [[ $pending_approval -gt 0 ]]; then
        echo "${BOLD}Files pending approval:${RESET}"
        jq -r '.files[] | select(.status == "pending_approval") | "  [\(.confidence)%] \(.source_path)"' "$QUEUE_FILE"
        echo ""
        info "Use the viewer to approve/reject files, then run './organize.sh'"
    fi

    if [[ $approved -gt 0 ]]; then
        echo "${BOLD}Approved files (ready to move):${RESET}"
        jq -r '.files[] | select(.status == "approved") | "  [\(.confidence)%] \(.source_path)"' "$QUEUE_FILE"
        echo ""
        info "Run './organize.sh' to process approved files"
    fi
}

# Undo last batch
undo_operations() {
    local total=$(jq '.operations | length' "$HISTORY_FILE")

    if [[ $total -eq 0 ]]; then
        info "No operations to undo"
        return 0
    fi

    echo "${BOLD}Found $total operation(s) in history${RESET}"
    echo ""

    if [[ "$DRY_RUN" == "false" ]] && [[ "$AUTO_MODE" == "false" ]]; then
        read -p "Undo all operations? [y/N]: " -r
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Undo cancelled"
            return 0
        fi
    fi

    local undone=0
    local failed=0

    # Process in reverse order
    while IFS= read -r op_json; do
        local source=$(echo "$op_json" | jq -r '.source_path')
        local dest=$(echo "$op_json" | jq -r '.dest_path')
        local can_undo=$(echo "$op_json" | jq -r '.can_undo')

        if [[ "$can_undo" != "true" ]]; then
            warn "Cannot undo: $dest (file was modified)"
            ((failed++))
            continue
        fi

        if [[ ! -f "$dest" ]]; then
            warn "Cannot undo: $dest (file no longer exists)"
            ((failed++))
            continue
        fi

        if [[ "$DRY_RUN" == "true" ]]; then
            info "Would undo: $dest → $source"
            ((undone++))
        else
            # Ensure source directory exists
            mkdir -p "$(dirname "$source")"

            if mv "$dest" "$source" 2>/dev/null; then
                success "Undone: $dest → $source"
                ((undone++))
            else
                error "Failed to undo: $dest"
                ((failed++))
            fi
        fi

    done < <(jq -c '.operations | reverse | .[]' "$HISTORY_FILE")

    echo ""
    echo "${BOLD}Undo Summary:${RESET}"
    echo "  Undone: $undone"
    echo "  Failed: $failed"

    if [[ "$DRY_RUN" == "false" ]] && [[ $undone -gt 0 ]]; then
        # Clear history
        echo '{"schema_version": "1.0", "operations": []}' > "$HISTORY_FILE"
        success "History cleared"
    fi
}

# Show help
show_help() {
    cat << EOF
${BOLD}File Organization System${RESET}

Usage: ./organize.sh [OPTIONS]

Options:
  (none)          Interactive mode - process files with user confirmation
  --auto, -a      Automatic mode - only process high confidence files
  --dry-run, -n   Preview mode - show what would happen without executing
  --undo, -u      Undo last batch of file operations
  --status, -s    Show current queue status
  --help, -h      Show this help message

Confidence Thresholds:
  ≥90%: Auto-approved and executed
  50-89%: Requires user confirmation (skipped in --auto mode)
  <50%: Moved to unknown folder

Examples:
  ./organize.sh              Process files interactively
  ./organize.sh --dry-run    Preview what would happen
  ./organize.sh --auto       Process only high-confidence files
  ./organize.sh --status     Check queue status
  ./organize.sh --undo       Revert last batch of moves

Configuration:
  Edit config.yaml to customize paths and thresholds

EOF
}

##############################################################################
# Main Script
##############################################################################

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --auto|-a)
            AUTO_MODE=true
            MODE="auto"
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --undo|-u)
            MODE="undo"
            shift
            ;;
        --status|-s)
            MODE="status"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1\nUse --help for usage information"
            ;;
    esac
done

# Check dependencies
check_dependencies

# Load configuration
load_config

# Execute based on mode
case $MODE in
    "interactive"|"auto")
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "${YELLOW}${BOLD}DRY RUN MODE - No files will be moved${RESET}"
            echo ""
        fi
        process_queue
        ;;
    "status")
        show_status
        ;;
    "undo")
        if [[ "$DRY_RUN" == "true" ]]; then
            echo "${YELLOW}${BOLD}DRY RUN MODE - Showing what would be undone${RESET}"
            echo ""
        fi
        undo_operations
        ;;
esac

exit 0
