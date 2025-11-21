#!/bin/bash

# Auto File Organization Executor
# Intelligently routes files based on confidence scores from organize_log.md

set -e

ORGANIZE_LOG="../logs/organize_log.md"
EXECUTION_LOG="../logs/execution_log.md"
DRY_RUN=false
INTERACTIVE=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --auto|-a)
            INTERACTIVE=false
            shift
            ;;
        --help|-h)
            echo "Auto File Organization Executor"
            echo "Usage: $0 [--dry-run] [--auto] [--help]"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n    Show what would be executed without doing it"
            echo "  --auto, -a       Run without interactive prompts for medium confidence"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "Confidence Thresholds:"
            echo "  90-100%: Auto-approve → execution_log.md"
            echo "  50-89%:  Ask user for confirmation (unless --auto)"
            echo "  0-49%:   Auto-move to ~/Files/unknown/"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ ! -f "$ORGANIZE_LOG" ]]; then
    echo "Error: $ORGANIZE_LOG not found"
    exit 1
fi

echo "Auto File Organization Executor"
echo "==============================="
if [[ "$DRY_RUN" == "true" ]]; then
    echo "DRY RUN MODE - No files will be moved"
fi
echo ""

# Create unknown directory if needed
unknown_dir="$HOME/Files/unknown"
if [[ ! -d "$unknown_dir" && "$DRY_RUN" != "true" ]]; then
    echo "📁 Creating unknown directory: $unknown_dir"
    mkdir -p "$unknown_dir"
fi

# Initialize counters
auto_approved=0
user_review=0
low_confidence=0
processed=0

# Extract confidence scores and associated data using simpler approach
confidence_entries=$(grep -n "^\- \*\*Confidence\*\*:" "$ORGANIZE_LOG" | while read -r line; do
    line_num=$(echo "$line" | cut -d: -f1)
    confidence=$(echo "$line" | sed 's/.*: \([0-9]*\)%.*/\1/')
    
    # Get the filename from a few lines above (find the ### header)
    filename=$(sed -n "$((line_num-10)),$((line_num))p" "$ORGANIZE_LOG" | grep "^###" | tail -1 | sed 's/^### [0-9-]* - //')
    
    # Get the command from a few lines below
    command=$(sed -n "$((line_num)),$((line_num+10))p" "$ORGANIZE_LOG" | grep "^\- \*\*Suggested Command\*\*:" | head -1 | sed 's/.*: `\(.*\)`.*/\1/')
    
    # Output in format: confidence|filename|command
    echo "$confidence|$filename|$command"
done)

# Process each entry (using process substitution to avoid subshell)
while IFS='|' read -r confidence filename command; do
    if [[ -z "$confidence" || -z "$filename" || -z "$command" ]]; then
        continue
    fi
    
    ((processed++))
    
    echo "Processing: $filename"
    echo "Confidence: $confidence%"
    
    if [[ $confidence -ge 90 ]]; then
        # High confidence - auto approve
        echo "  ✅ HIGH CONFIDENCE: Auto-approving"
        if [[ "$DRY_RUN" != "true" ]]; then
            # Add to execution log
            {
                echo ""
                echo "### $(date '+%Y-%m-%d') - Auto-approved (${confidence}%)"
                echo ""
                echo "\`\`\`bash"
                echo "# $filename - Auto-approved due to high confidence"
                echo "[ ] $command"
                echo "\`\`\`"
            } >> "$EXECUTION_LOG"
        fi
        ((auto_approved++))
        
    elif [[ $confidence -ge 50 ]]; then
        # Medium confidence - ask user (unless --auto)
        echo "  ⚠️  MEDIUM CONFIDENCE: Review needed"
        if [[ "$INTERACTIVE" == "true" && "$DRY_RUN" != "true" ]]; then
            echo ""
            echo "Command: $command"
            echo ""
            read -p "Approve this file organization? (y/n/s=skip): " -n 1 -r
            echo
            case $REPLY in
                [Yy])
                    echo "  ✅ User approved"
                    {
                        echo ""
                        echo "### $(date '+%Y-%m-%d') - User approved (${confidence}%)"
                        echo ""
                        echo "\`\`\`bash"
                        echo "# $filename - User approved"
                        echo "[ ] $command"
                        echo "\`\`\`"
                    } >> "$EXECUTION_LOG"
                    ;;
                [Ss])
                    echo "  ⏭️  Skipped by user"
                    ;;
                *)
                    echo "  ❌ User rejected"
                    ;;
            esac
        elif [[ "$INTERACTIVE" == "false" ]]; then
            echo "  ⏭️  AUTO MODE: Skipping medium confidence file"
        fi
        ((user_review++))
        
    else
        # Low confidence - move to unknown
        echo "  🤷 LOW CONFIDENCE: Moving to unknown folder"
        
        # Extract source file from command
        source_file=$(echo "$command" | sed 's/mv "\([^"]*\)".*/\1/')
        if [[ -f "$source_file" ]]; then
            base_filename=$(basename "$source_file")
            unknown_path="$unknown_dir/$base_filename"
            
            # Handle filename conflicts
            counter=1
            while [[ -f "$unknown_path" ]]; do
                name="${base_filename%.*}"
                ext="${base_filename##*.}"
                if [[ "$name" == "$ext" ]]; then
                    # No extension
                    unknown_path="$unknown_dir/${base_filename}_${counter}"
                else
                    unknown_path="$unknown_dir/${name}_${counter}.${ext}"
                fi
                ((counter++))
            done
            
            if [[ "$DRY_RUN" == "true" ]]; then
                echo "    🔍 Would move to: $unknown_path"
            else
                echo "    📁 Moving to: $unknown_path"
                if mv "$source_file" "$unknown_path"; then
                    echo "    ✅ Moved successfully"
                else
                    echo "    ❌ Move failed"
                fi
            fi
        else
            echo "    ❌ Source file not found: $source_file"
        fi
        ((low_confidence++))
    fi
    
    echo ""
done < <(echo "$confidence_entries")

echo "Processing Summary:"
echo "=================="
echo "Total processed: $processed"
echo "Auto-approved (≥90%): $auto_approved"  
echo "User review (50-89%): $user_review"
echo "Low confidence (<50%): $low_confidence"
echo ""

if [[ $auto_approved -gt 0 ]]; then
    echo "Next step: Run './execute.sh' to execute approved commands"
fi