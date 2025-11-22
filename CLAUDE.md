# File Organizer

This is a Claude Code driven file organization system. It processes unorganized files with intelligent confidence-based routing.

## Quick Reference

- **Configuration**: See `config.yaml` for paths and thresholds
- **Filing Structure**: See `docs/filing-structure.md`
- **Naming Conventions**: See `docs/naming-conventions.md`
- **Examples**: See `docs/examples.md`
- **State Files**: `state/file_queue.json` (pending files), `state/history.json` (undo capability)

## How the System Works

### Your Role (Claude)
You analyze files and add suggestions to the queue. You **NEVER** move files directly.

### organize.sh's Role
The `organize.sh` script reads your suggestions from `state/file_queue.json` and executes them based on confidence scores.

---

## File Organization Process

When asked to "organize next file" or similar:

### 1. Find Next File
Look in source directories (default: `~/Downloads/` and `~/Desktop/`) for unorganized files.

### 2. Analyze the File
- Check file extension, size, and basic metadata
- For text files: Use Read tool to examine content (first ~50 lines)
- For spreadsheets/PDFs: Examine content for entity names and domain-specific terms
- Identify potential category matches from filing structure

### 3. Explore Destinations

**IMPORTANT**: Search in BOTH primary locations:
- `~/Dropbox/Filing/` - Entity-based organization (business, financial, utilities, real estate)
- `~/Dropbox/Taxes/` - Tax documents by entity (HoldCo, Personal, Family Trust, etc.)

Exploration steps:
- **Search for similar files**: Use Glob/Grep to locate similar files in potential destinations
- **Analyze existing patterns**: Check naming conventions of files already in target folders
- **Explore subfolders**: Look at subfolder structure to find the most specific placement
- **Pattern matching**: Compare file content/name against existing files to find best match

**Key distinction**:
- Tax returns, CRA/IRS notices, audit docs → `~/Dropbox/Taxes/`
- Bank statements, invoices, contracts, general business docs → `~/Dropbox/Filing/`

### 4. Smart Categorization
- Match against documented category patterns (Financial, Utilities, Business, etc.)
- Use similarity to existing files to refine placement
- When multiple options exist, prefer more specific entity folders
- For unclear categorization, examine 3-5 similar files for pattern confirmation

### 5. Calculate Confidence Score (0-100%)

**Positive Factors:**
- **+30%**: Found similar files in exact destination folder
- **+20%**: File extension matches folder's typical content
- **+20%**: Filename contains strong entity keywords (TD, Rogers, Insurance, etc.)
- **+15%**: Content analysis matches category patterns
- **+10%**: Date pattern matches existing files in folder
- **+5%**: File size similar to existing files in category

**Negative Factors:**
- **-20%**: Ambiguous filename or generic terms
- **-30%**: No similar files found in Filing directory
- **-20%**: Multiple equally valid destinations exist

### 6. Apply Naming Conventions
- Follow category-specific naming patterns (see `docs/naming-conventions.md`)
- Remove version numbers like `(1)`, `(2)`, etc.
- Remove leading underscores and normalize spacing
- Ensure consistent date format: `YYYY-MM-DD`
- Remove duplicate entity names if they're in the folder path

### 7. Validate the Suggestion (Optional but Recommended)
Before adding to queue, you can validate using:
```bash
./scripts/validate_suggestion.sh "<source_path>" "<dest_path>"
```
This checks for common issues and gives immediate feedback.

### 8. Add to Queue
Add the suggestion to `state/file_queue.json` using the Write tool.

**IMPORTANT**: Read the existing queue file first, then append your new entry.

#### JSON Format

```json
{
  "schema_version": "1.0",
  "last_updated": "2025-01-21T10:30:00Z",
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_path": "/Users/marklampert/Downloads/Statement_Jan2024.pdf",
      "dest_path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf",
      "confidence": 95,
      "confidence_factors": {
        "similar_files_found": 30,
        "file_type_match": 20,
        "entity_keyword": 20,
        "content_match": 15,
        "naming_pattern": 10
      },
      "status": "pending",
      "timestamp": "2025-01-21T10:25:00Z",
      "reasoning": "Found 8 similar TD bank statements in destination folder with account number x2705. PDF format matches typical bank statements. Date in filename (Jan2024) converted to standard YYYY-MM-DD format. Strong confidence based on clear account number match."
    }
  ]
}
```

#### Required Fields

- **id**: Generate a UUID (use `uuidgen` command or create a unique ID)
- **source_path**: Full absolute path to the source file (expand `~` to full path)
- **dest_path**: Full absolute path to destination including new filename
- **confidence**: Integer 0-100
- **confidence_factors**: Object with individual scoring factors and their values
- **status**: Always `"pending"` for new suggestions
- **timestamp**: ISO 8601 format `YYYY-MM-DDTHH:MM:SSZ` (use UTC)
- **reasoning**: Detailed explanation of why this destination was chosen (1-3 sentences)

### 9. Inform the User

After adding to queue, tell the user:
- What file was analyzed
- Confidence score
- Destination path
- Next step: Run `./organize.sh` to process

---

## Complete Workflow Example

```bash
# User says: "organize next file"

# 1. You find and analyze the file
ls ~/Downloads/  # Find next file
# Found: "Rogers-Invoice-Jan-2024.pdf"

# 2. You explore and categorize
glob "**/*Rogers*" ~/Dropbox/Filing/  # Find similar files
# Found: ~/Dropbox/Filing/Rogers - Wireless/ with similar invoices

# 3. You calculate confidence (95%) and create suggestion

# 4. You generate UUID and add to queue
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "source_path": "/Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Rogers - Wireless/Rogers-2024-01-15.pdf",
  "confidence": 95,
  "confidence_factors": {
    "similar_files_found": 30,
    "file_type_match": 20,
    "entity_keyword": 20,
    "content_match": 15,
    "naming_pattern": 10
  },
  "status": "pending",
  "timestamp": "2025-01-21T14:30:00Z",
  "reasoning": "Found 12 similar Rogers wireless invoices in destination folder. PDF format matches typical invoice format. Applied standard naming pattern Rogers-YYYY-MM-DD.pdf used by existing files."
}

# 5. You inform the user
"Added Rogers invoice to queue with 95% confidence.
Destination: ~/Dropbox/Filing/Rogers - Wireless/Rogers-2024-01-15.pdf

Run ./organize.sh to process the queue."
```

---

## Auto-Routing by organize.sh

When user runs `./organize.sh`, it will:

- **90-100% confidence**: Auto-approve and execute immediately
- **50-89% confidence**: Ask user for confirmation
- **0-49% confidence**: Move to `~/Files/unknown/` folder

User can run:
- `./organize.sh` - Interactive mode (asks for medium confidence)
- `./organize.sh --auto` - Only process high confidence automatically
- `./organize.sh --dry-run` - Preview what would happen
- `./organize.sh --status` - Check queue status
- `./organize.sh --undo` - Revert last batch of moves

---

## Important Guidelines

### DO:
✅ Always use absolute paths (expand `~` to `/Users/marklampert`)
✅ Generate unique UUIDs for each file (use `uuidgen` bash command)
✅ Read existing queue before appending new entries
✅ Include detailed reasoning for human review
✅ Search for similar files to inform destination choice
✅ Apply naming conventions from docs/naming-conventions.md
✅ Calculate confidence scores honestly based on actual findings

### DON'T:
❌ Never actually move files yourself - only add to queue
❌ Don't guess paths - always verify destination structure exists
❌ Don't skip content analysis - filename alone is insufficient
❌ Don't use relative paths - always use full absolute paths
❌ Don't reuse IDs - each file needs a unique UUID
❌ Don't add entries with missing required fields

---

## Testing Your Suggestions

You can test a suggestion before adding to queue:

```bash
./scripts/validate_suggestion.sh "/Users/marklampert/Downloads/file.pdf" "/Users/marklampert/Dropbox/Filing/Category/file.pdf"
```

This will check for:
- Source file existence
- Destination path validity
- Permission issues
- File type mismatches
- Common naming problems

---

## Handling Edge Cases

### File Already Exists at Destination
- Still add to queue with full reasoning
- organize.sh will handle conflicts during execution (ask user to overwrite/rename/skip)

### Very Low Confidence (<30%)
- Set destination to unknown folder: `~/Files/unknown/`
- Include reasoning about why categorization is unclear

### Multiple Valid Destinations
- Choose the most specific folder
- Reduce confidence by -20%
- Explain alternatives in reasoning

### Special File Types
- **DMG files**: `~/Files/installers/`
- **Screenshots**: `~/Files/screenshots/`
- **Unknown/unclear**: `~/Files/unknown/`

---

## Quick Command Reference

```bash
# Process the queue
./organize.sh                    # Interactive
./organize.sh --auto             # Auto mode
./organize.sh --dry-run          # Preview

# Check status
./organize.sh --status           # See pending files

# Undo operations
./organize.sh --undo             # Revert last batch

# Validate before adding
./scripts/validate_suggestion.sh <source> <dest>

# Generate UUID for file ID
uuidgen | tr '[:upper:]' '[:lower:]'
```

---

## Summary

1. **You analyze** files and add JSON entries to `state/file_queue.json`
2. **organize.sh executes** based on confidence scores
3. **User controls** via command-line options
4. **System tracks** everything in JSON for undo capability

Your job is to be the "brain" - analyze files intelligently and create accurate suggestions. The organize.sh script is the "hands" - it handles all actual file operations safely.
