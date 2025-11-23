# File Organizer

This is a Claude Code driven file organization system. Claude analyzes files and suggests destinations with confidence scores. You review and approve each suggestion before files are moved.

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
The `organize.sh` script reads your suggestions from `state/file_queue.json` and presents them for user review and approval. It executes only the moves that the user approves.

---

## File Organization Process

When asked to "organize next file" or similar:

### 1. Find Next File
Look in source directories (default: `~/Downloads/` and `~/Desktop/`) for unorganized files.

**IMPORTANT**: Always prioritize the most recently added files first.
- Use `ls -lt` to list files sorted by modification time (newest first)
- Analyze the most recent file that hasn't been processed yet
- This ensures new downloads are organized promptly

### 2. Analyze the File
- Check file extension, size, and basic metadata
- For text files: Use Read tool to examine content (first ~50 lines)
- For spreadsheets/PDFs: Examine content for entity names and domain-specific terms
- Identify potential category matches from filing structure

### 2.5. Check for Duplicates

**IMPORTANT**: Before exploring destinations, check if this file already exists elsewhere.

Use the duplicate detection script:
```bash
./scripts/find_duplicates.sh "<source_path>" "<destination_directory>"
```

The script will:
- Calculate SHA256 checksum of the source file
- Search the destination directory for files with matching checksums
- Search the pending queue for files with matching checksums
- Return JSON with duplicate information

**If duplicates are found:**
- Set `dest_path` to `"DELETE"`
- Add `duplicate_of` field with array of duplicate file paths
- Add `checksum` field with the SHA256 hash
- Add `action` field set to `"delete"`
- Set confidence to 100% (exact match)
- Skip remaining steps and go directly to step 8 (Add to Queue)

**If no duplicates found:**
- Continue to step 3 (Explore Destinations)

**Example duplicate detection:**
```bash
# Check for duplicates in the proposed destination folder
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/invoice.pdf" \
  "/Users/marklampert/Dropbox/Filing/TD Chequing/"

# Returns:
# {
#   "source_checksum": "abc123...",
#   "duplicates": [
#     {"path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15.pdf", "location": "destination"}
#   ]
# }
```

### 3. Explore Destinations

**IMPORTANT**: Search in BOTH primary locations:
- `~/Dropbox/Filing/` - Entity-based organization (business, financial, utilities, real estate)
- `~/Dropbox/Taxes/` - Tax documents by entity (HoldCo, Personal, Family Trust, etc.)

Exploration steps:
- **Search for similar files**: Use Glob/Grep to locate similar files in potential destinations
- **Analyze existing patterns**: Check naming conventions of files already in target folders
- **Explore subfolders**: Look at subfolder structure to find the most specific placement
- **Pattern matching**: Compare file content/name against existing files to find best match
- **Find multiple options**: When exploring, identify ALL valid destinations (not just the first match)

**Key distinction**:
- Tax returns, CRA/IRS notices, audit docs → `~/Dropbox/Taxes/`
- Bank statements, invoices, contracts, general business docs → `~/Dropbox/Filing/`

**Multiple Destinations**:
When you find multiple valid destinations, score each one independently and save ALL options with confidence >= 60% to the `alternatives` array. This gives the user transparency into your decision-making process.

### 4. Smart Categorization & Ranking
- Match against documented category patterns (Financial, Utilities, Business, etc.)
- Use similarity to existing files to refine placement
- When multiple options exist, score each independently using confidence factors
- Rank options by confidence score - highest becomes primary destination
- Save all alternatives with confidence >= 60% to `alternatives` array
- For each alternative, document key differences from primary choice
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

#### Duplicate File Example

When a duplicate is detected, the entry looks like this:

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "source_path": "/Users/marklampert/Downloads/Invoice_duplicate.pdf",
  "dest_path": "DELETE",
  "duplicate_of": [
    "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf",
    "/Users/marklampert/Dropbox/Filing/TD Chequing/Archive/2024-01-15_x2705_old.pdf"
  ],
  "checksum": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "action": "delete",
  "confidence": 100,
  "confidence_factors": {
    "exact_checksum_match": 100
  },
  "status": "pending",
  "timestamp": "2025-01-21T10:30:00Z",
  "reasoning": "Exact duplicate detected. File has identical SHA256 checksum as 2 existing files in destination directory. Source file can be safely deleted to avoid duplication."
}
```

#### Required Fields

- **id**: Generate a UUID (use `uuidgen` command or create a unique ID)
- **source_path**: Full absolute path to the source file (expand `~` to full path)
- **dest_path**: Full absolute path to destination including new filename (or `"DELETE"` for duplicates)
- **confidence**: Integer 0-100
- **confidence_factors**: Object with individual scoring factors and their values
- **status**: Always `"pending"` for new suggestions
- **timestamp**: ISO 8601 format `YYYY-MM-DDTHH:MM:SSZ` (use UTC)
- **reasoning**: Detailed explanation of why this destination was chosen (1-3 sentences)

#### Optional Fields

**For Duplicates:**
- **duplicate_of**: Array of paths to existing duplicate files (only when duplicates detected)
- **checksum**: SHA256 hash of the source file (only when duplicates detected)
- **action**: `"move"` (default) or `"delete"` (for duplicates)

**For Multiple Destination Options:**
- **alternatives**: Array of alternative destination options (only when multiple valid options exist with confidence >= 60%)
  - Each alternative object contains:
    - **dest_path**: Full absolute path to alternative destination
    - **confidence**: Confidence score for this alternative (0-100)
    - **confidence_factors**: Breakdown of confidence scoring for this option
    - **reasoning**: Why this option ranked lower than primary (1-2 sentences)
    - **differences**: Key differences from primary destination (1 sentence)

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
ls -lt ~/Downloads/  # Find next file (sorted by newest first)
# Found: "Rogers-Invoice-Jan-2024.pdf" (most recent file)

# 2. Analyze the file content
read /Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf

# 2.5. Check for duplicates BEFORE exploring destinations
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf" \
  "/Users/marklampert/Dropbox/Filing/Rogers - Wireless/"
# Returns: {"source_checksum": "abc123...", "duplicates": []}
# No duplicates found - continue to exploration

# 3. You explore and categorize
glob "**/*Rogers*" ~/Dropbox/Filing/  # Find similar files
# Found: ~/Dropbox/Filing/Rogers - Wireless/ with similar invoices

# 4. You calculate confidence (95%) and create suggestion

# 5. You generate UUID and add to queue
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

# 6. You inform the user
"Added Rogers invoice to queue with 95% confidence.
Destination: ~/Dropbox/Filing/Rogers - Wireless/Rogers-2024-01-15.pdf

Run ./organize.sh to process the queue."
```

### Workflow Example: Duplicate Detected

```bash
# User says: "organize next file"

# 1. You find and analyze the file
ls -lt ~/Downloads/  # Find next file (sorted by newest first)
# Found: "Statement-Jan-2024.pdf" (most recent file)

# 2. Analyze the file content
read /Users/marklampert/Downloads/Statement-Jan-2024.pdf
# Identified: TD Bank statement for account x2705

# 2.5. Check for duplicates BEFORE exploring
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/Statement-Jan-2024.pdf" \
  "/Users/marklampert/Dropbox/Filing/TD Chequing/"
# Returns: {
#   "source_checksum": "a1b2c3d4...",
#   "duplicates": [
#     {"path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf", "location": "destination"}
#   ]
# }
# DUPLICATE FOUND! Skip to adding DELETE entry to queue

# 3. Generate UUID and add DELETE entry to queue
{
  "id": "8d7e6679-8536-41de-955c-e08fc2f91ae8",
  "source_path": "/Users/marklampert/Downloads/Statement-Jan-2024.pdf",
  "dest_path": "DELETE",
  "duplicate_of": [
    "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf"
  ],
  "checksum": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "action": "delete",
  "confidence": 100,
  "confidence_factors": {
    "exact_checksum_match": 100
  },
  "status": "pending",
  "timestamp": "2025-01-21T14:35:00Z",
  "reasoning": "Exact duplicate detected. File has identical SHA256 checksum as existing file at /Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf. Source file can be safely deleted."
}

# 4. Inform the user
"Duplicate file detected! Statement-Jan-2024.pdf is identical to existing file:
/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_x2705.pdf

Added to queue with DELETE action (100% confidence - exact checksum match).

Run ./organize.sh to review and approve deletion."
```

### Workflow Example: Multiple Valid Destinations

```bash
# User says: "organize next file"

# 1. You find and analyze the file
ls -lt ~/Downloads/  # Find next file (sorted by newest first)
# Found: "Bell-Internet-Invoice-2024-01.pdf" (most recent file)

# 2. Analyze the file content
read /Users/marklampert/Downloads/Bell-Internet-Invoice-2024-01.pdf
# Identified: Bell internet invoice (business expense, could be tax deductible)

# 2.5. Check for duplicates
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/Bell-Internet-Invoice-2024-01.pdf" \
  "/Users/marklampert/Dropbox/Filing/"
# Returns: {"source_checksum": "xyz789...", "duplicates": []}
# No duplicates found - continue

# 3. Explore multiple potential destinations
glob "**/*Bell*" ~/Dropbox/Filing/
# Found: ~/Dropbox/Filing/Bell - Internet/ (12 similar invoices)
#        ~/Dropbox/Filing/Utilities/Internet/ (3 mixed provider invoices)

glob "**/*Bell*" ~/Dropbox/Taxes/
# Found: ~/Dropbox/Taxes/HoldCo/Expenses/Utilities/ (tax-deductible expenses)

# 4. Score each destination independently
# Option 1 (Primary): ~/Dropbox/Filing/Bell - Internet/
#   - Similar files found: +30
#   - File type match: +20
#   - Entity keyword: +20
#   - Content match: +15
#   - Naming pattern: +10
#   Total: 95%

# Option 2: ~/Dropbox/Filing/Utilities/Internet/
#   - Similar files found: +15 (fewer Bell files, mixed providers)
#   - File type match: +20
#   - Content match: +15
#   - Naming pattern: +10
#   Total: 60% (less specific than Bell folder)

# Option 3: ~/Dropbox/Taxes/HoldCo/Expenses/Utilities/
#   - Similar files found: +10 (some utility expenses)
#   - File type match: +20
#   - Content match: +15
#   - Tax context: +10
#   Total: 55% (below 60% threshold - not included)

# 5. Generate UUID and add to queue with alternatives
{
  "id": "9e8f7766-9647-42de-a66d-f19fc3f92be9",
  "source_path": "/Users/marklampert/Downloads/Bell-Internet-Invoice-2024-01.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Bell - Internet/Bell-2024-01-15.pdf",
  "confidence": 95,
  "confidence_factors": {
    "similar_files_found": 30,
    "file_type_match": 20,
    "entity_keyword": 20,
    "content_match": 15,
    "naming_pattern": 10
  },
  "alternatives": [
    {
      "dest_path": "/Users/marklampert/Dropbox/Filing/Utilities/Internet/Bell-2024-01-15.pdf",
      "confidence": 60,
      "confidence_factors": {
        "similar_files_found": 15,
        "file_type_match": 20,
        "content_match": 15,
        "naming_pattern": 10
      },
      "reasoning": "Less specific folder with mixed internet providers rather than Bell-specific organization",
      "differences": "General utilities/internet folder vs dedicated Bell folder with 12 existing invoices"
    }
  ],
  "status": "pending",
  "timestamp": "2025-01-21T15:00:00Z",
  "reasoning": "Bell-specific folder has 12 similar invoices with consistent naming pattern. Highest confidence due to entity-specific organization and strong pattern match. Alternative general utilities folder also valid but less specific."
}

# 6. Inform the user
"Added Bell internet invoice to queue with 95% confidence (+1 alternative option).
Primary: ~/Dropbox/Filing/Bell - Internet/Bell-2024-01-15.pdf
Alternative: ~/Dropbox/Filing/Utilities/Internet/ (60% confidence)

Run ./organize.sh or open viewer to see all options."
```

---

## User Review and Approval via organize.sh

The `organize.sh` script is the execution layer - it reads suggestions from the queue and lets the user review and approve them.

**All files require explicit user approval** - there is no automatic execution. Confidence scores help you prioritize which suggestions to trust, but you always have the final say.

### Confidence Scores Guide User Review:
- **90-100%**: High confidence - Claude found strong matching patterns and similar files
- **70-89%**: Good confidence - Clear categorization with some supporting evidence
- **50-69%**: Moderate confidence - Reasonable guess but limited supporting evidence
- **Below 50%**: Low confidence - Unclear categorization, may need manual review

User can run:
- `./organize.sh` - Interactive review mode (review and approve/reject each suggestion)
- `./organize.sh --dry-run` - Preview suggestions without executing
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
- Score each option independently using confidence factors
- Choose the highest confidence as primary destination
- Save all alternatives with confidence >= 60% to `alternatives` array
- For each alternative, explain key differences from primary
- DO NOT reduce primary confidence - each option is scored independently

### Special File Types
- **DMG files**: `~/Files/installers/`
- **Screenshots**: `~/Files/screenshots/`
- **Unknown/unclear**: `~/Files/unknown/`

---

## Quick Command Reference

```bash
# Process the queue
./organize.sh                    # Interactive review and approval
./organize.sh --dry-run          # Preview suggestions only

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
2. **User reviews** suggestions via `./organize.sh` and approves/rejects each one
3. **organize.sh executes** approved moves only
4. **System tracks** everything in JSON for undo capability

Your job is to be the "brain" - analyze files intelligently and create accurate suggestions. The user is the decision-maker. The organize.sh script is the "hands" - it handles all actual file operations safely after user approval.
