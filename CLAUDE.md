# File Organizer

This is a Claude Code driven file organization system. Claude analyzes files and suggests destinations with confidence scores. You review and approve each suggestion before files are moved.

## Quick Reference

- **Configuration**: See `config.yaml` for paths and thresholds
- **Filing Structure**: See `docs/filing-structure.md`
- **Naming Conventions**: See `docs/naming-conventions.md`
- **Examples**: See `docs/examples.md`
- **State Files**: `state/file_queue.json` (pending files), `state/move_history.json` (undo capability)

## How the System Works

### Your Role (Claude)
You analyze files and add suggestions to the queue. You **NEVER** move files directly.

### Viewer UI's Role
The viewer UI (`/view`) displays suggestions from `state/file_queue.json` and provides Move/Skip buttons. When the user clicks **Move**, the file is immediately moved to the destination. When the user clicks **Skip**, the file is removed from the queue without moving.

---

## File Organization Process

When asked to "organize next file" or similar:

### 1. Find Next File
Look in source directories (default: `~/Downloads/` and `~/Desktop/`) for unorganized files.

**IMPORTANT**: Always prioritize the most recently added files first.
- Use `ls -lt` to list files sorted by modification time (newest first)
- Analyze the most recent file that hasn't been processed yet
- This ensures new downloads are organized promptly
- **Skip subfolders**: Ignore files in `~/Downloads/Screenshots/`, `~/Downloads/installers/`, `~/Downloads/unknown/`, `~/Downloads/Skipped/`, `~/Downloads/TO_DELETE/`, and `~/Downloads/Uken/` - these are already organized or pending review

### 2. Analyze the File Content (MANDATORY)

**CRITICAL**: You MUST run content analysis before making any suggestions. Never guess from filenames alone.

```bash
./scripts/analyze_content.sh "<source_path>"
```

This script analyzes the actual file content and returns JSON with:
- `content_summary`: Human-readable description of what the file contains
- `detected_entities`: Known entities found (TD, Rogers, Uken, etc.)
- `detected_dates`: Dates extracted from the content
- `suggested_category`: Category hint based on content analysis
- `confidence_boost`: Additional confidence points from content match

**Use the output to:**
- Understand what the file actually contains (not just its filename)
- Extract entity names for accurate destination matching
- Find dates for proper filename generation
- Add `confidence_boost` to your confidence calculation
- Include `content_analysis` field in your queue entry

**Never suggest a destination without first running content analysis.**

**Special handling for Insurance PDFs**:
- Read PDF content to identify:
  - Document type (Renewal, Policy Change, Coverage Increase, Pink Card, Issuance, etc.)
  - Property addresses mentioned in the document
  - Policy numbers and account identifiers
  - Effective dates or transaction dates
- Map property addresses to standardized short names (see `docs/naming-conventions.md`):
  - "1035 Fire Route 20G" or "1035 FIRE ROUTE 20G" → "Cottage"
  - "40 Gibson Ave" or "40 GIBSON AVE" → "40 Gibson"
  - "319 Carlaw Ave Unit 711" or "319 CARLAW AVE UNIT 711" → "Carlaw"
  - Vehicle make/model → use short format (e.g., "Mazda CX-5")
- If multiple properties in one document → use combined format (e.g., "Cottage + Carlaw")
- Extract document date for filename (prefer effective date, statement date, or issue date)

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

**Creating New Folders**:
If NO existing folder is appropriate for the file, you can propose creating a new folder:
- Analyze the file's entity/category (e.g., new utility provider, new bank account, new business entity)
- Propose a new folder name following the naming conventions (use ` - ` separator for multi-part names)
- Set `new_folder: true` in the JSON entry
- Include justification in the reasoning field
- Typically set confidence to 70-85% (lower than exact matches, higher than unclear categorization)
- The viewer UI will highlight new folder proposals with a special badge
- The folder will be created automatically when the user clicks Move

**Examples of when to propose new folders**:
- New utility provider not in existing structure (e.g., "Enwave" for a new heating/cooling service)
- New bank account or financial institution (e.g., "Wealthsimple" for a new investment platform)
- New business entity or investment (e.g., new angel investment company)
- New real estate property (e.g., "Real Estate - 123 Main St")
- New service provider category (e.g., "Lawn Care" if not currently tracked)

### 4. Smart Categorization & Ranking
- Match against documented category patterns (Financial, Utilities, Business, etc.)
- Use similarity to existing files to refine placement
- When multiple options exist, score each independently using confidence factors
- Rank options by confidence score - highest becomes primary destination
- Save all alternatives with confidence >= 60% to `alternatives` array
- For each alternative, document key differences from primary choice
- For unclear categorization, examine 3-5 similar files for pattern confirmation

### 4.5. Validate Destination Path (MANDATORY)

**CRITICAL**: Before calculating confidence, validate the proposed destination:

```bash
./scripts/validate_destination.sh "<proposed_dest_path>"
```

**If validation fails:**
- DO NOT add to queue
- Re-analyze and choose an allowed destination
- Work files (including Uken corporate docs like Daybreak) → `~/Downloads/Uken/`
- Files to delete → `~/Downloads/TO_DELETE/`

**Allowed Destinations** (configured in `config.yaml`):
- `~/Dropbox/Filing/` - Personal filing (financial, utilities, real estate, etc.)
- `~/Dropbox/Taxes/` - Tax documents (HoldCo, Personal, Family Trust)
- `~/Downloads/Uken/` - Work files (including corporate entities like Daybreak)
- `~/Downloads/TO_DELETE/` - Temporary files for deletion
- `~/Downloads/Skipped/` - Files skipped for later review
- `~/Downloads/installers/` - Software installers
- `~/Downloads/Screenshots/` - Screenshots
- `~/Downloads/unknown/` - Unclear categorization

### 5. Calculate Confidence Score (0-100%)

**Positive Factors:**
- **+30%**: Found similar files in exact destination folder
- **+20%**: Content analysis detected entity name matching destination folder
- **+15%**: Content analysis confirms document type (invoice, statement, etc.)
- **+15%**: File extension matches folder's typical content
- **+10%**: Date pattern matches existing files in folder
- **+10%**: `confidence_boost` from content analysis script
- **+5%**: File size similar to existing files in category

**Negative Factors:**
- **-30%**: No content analysis performed (MUST run ./scripts/analyze_content.sh)
- **-20%**: Ambiguous or unreadable content
- **-20%**: No similar files found in Filing directory
- **-15%**: Multiple equally valid destinations exist

### 6. Apply Naming Conventions

**File Naming**:
- Follow category-specific naming patterns (see `docs/naming-conventions.md`)
- Remove version numbers like `(1)`, `(2)`, etc.
- Remove leading underscores and normalize spacing
- Ensure consistent date format: `YYYY-MM-DD`
- Remove duplicate entity names if they're in the folder path

**Insurance File Naming** (specific pattern):
- Format: `YYYY-MM-DD [Document Type] - [Property].pdf`
- Extract document type from PDF content (Renewal, Policy Change, Coverage Increase, etc.)
- Map property addresses to short identifiers (Cottage, 40 Gibson, Carlaw, etc.)
- Examples: `2024-11-13 Renewal - Cottage + Carlaw.pdf`, `2021-06-23 Pink Card - Mazda CX-5.pdf`
- Never use machine-generated policy numbers or document IDs in filename

**Folder Naming Standards** (when suggesting new folders):
- **Multi-part names**: Use ` - ` (space-hyphen-space) separator
  - ✅ Correct: `Rogers - Wireless`, `TD Visa - CAD Mark x1381`
  - ❌ Wrong: `Rogers : Wireless`, `TD Visa:USD`, mixed separators
- **Archive folders**: Use `z` prefix to push to bottom
  - ✅ Correct: `z Old`, `z Archived`, `z Old CAD Checking`
  - ❌ Wrong: `_old`, `old`, `archived` (without z prefix)

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
        "content_entity_match": 20,
        "content_type_match": 15,
        "file_type_match": 15,
        "naming_pattern": 10,
        "content_boost": 5
      },
      "content_analysis": {
        "summary": "3 page PDF. Content preview: TD Canada Trust Statement Period: January 1 - January 31, 2024 Account: x2705...",
        "detected_entities": ["TD"],
        "detected_dates": ["2024-01-01", "2024-01-31"]
      },
      "status": "pending",
      "timestamp": "2025-01-21T10:25:00Z",
      "reasoning": "Content analysis found TD bank statement for account x2705 with statement period Jan 2024. Found 8 similar TD statements in destination folder. High confidence based on entity match and content type."
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
- **content_analysis**: Object from analyze_content.sh output (REQUIRED for all files):
  - **summary**: Human-readable content description
  - **detected_entities**: Array of entities found (e.g., `["TD", "Rogers"]`)
  - **detected_dates**: Array of dates found (e.g., `["2024-01-15"]`)
- **status**: Always `"pending"` for new suggestions
- **timestamp**: ISO 8601 format `YYYY-MM-DDTHH:MM:SSZ` (use UTC)
- **reasoning**: Detailed explanation referencing actual file content (not just filename)

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

**For New Folder Proposals:**
- **new_folder**: `true` when proposing to create a new folder (dest_path parent doesn't exist yet)
  - Set to `true` when the destination folder needs to be created
  - The viewer UI will highlight this with a "NEW FOLDER" badge
  - The folder will be created automatically when the user clicks Move
  - Include clear justification in reasoning field for why new folder is needed

### 9. Inform the User

After adding to queue, tell the user:
- What file was analyzed
- Confidence score
- Destination path
- Next step: Run `./scripts/view_queue.sh` to review and click Move or Skip

---

## Complete Workflow Example

```bash
# User says: "organize next file"

# 1. You find the next file
ls -lt ~/Downloads/  # Find next file (sorted by newest first)
# Found: "Rogers-Invoice-Jan-2024.pdf" (most recent file)

# 2. MANDATORY: Run content analysis FIRST
./scripts/analyze_content.sh "/Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf"
# Returns JSON:
# {
#   "file_type": "pdf",
#   "content_summary": "3 page PDF. Content preview: Rogers Communications Invoice Date: January 15, 2024 Account: 12345...",
#   "detected_entities": ["Rogers"],
#   "detected_dates": ["2024-01-15"],
#   "suggested_category": "Utilities - Rogers",
#   "confidence_boost": 15
# }

# 2.5. Check for duplicates BEFORE exploring destinations
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf" \
  "/Users/marklampert/Dropbox/Filing/Rogers - Wireless/"
# Returns: {"source_checksum": "abc123...", "duplicates": []}
# No duplicates found - continue to exploration

# 3. You explore and categorize (using detected entities to guide search)
glob "**/*Rogers*" ~/Dropbox/Filing/  # Find similar files
# Found: ~/Dropbox/Filing/Rogers - Wireless/ with similar invoices

# 4. You calculate confidence using content analysis + similar files

# 5. You generate UUID and add to queue with content_analysis
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "source_path": "/Users/marklampert/Downloads/Rogers-Invoice-Jan-2024.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Rogers - Wireless/Rogers-2024-01-15.pdf",
  "confidence": 95,
  "confidence_factors": {
    "similar_files_found": 30,
    "content_entity_match": 20,
    "content_type_match": 15,
    "file_type_match": 15,
    "naming_pattern": 10,
    "content_boost": 5
  },
  "content_analysis": {
    "summary": "3 page PDF. Rogers Communications invoice for January 2024",
    "detected_entities": ["Rogers"],
    "detected_dates": ["2024-01-15"]
  },
  "status": "pending",
  "timestamp": "2025-01-21T14:30:00Z",
  "reasoning": "Content analysis confirmed Rogers invoice dated Jan 15, 2024. Found 12 similar Rogers invoices in destination folder. Entity and date extracted from PDF content, not filename."
}

# 6. You inform the user
"Added Rogers invoice to queue with 95% confidence.
Content: Rogers Communications invoice dated January 15, 2024
Destination: ~/Dropbox/Filing/Rogers - Wireless/Rogers-2024-01-15.pdf

Run ./scripts/view_queue.sh to review and click Move or Skip."
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

Run ./scripts/view_queue.sh to review and click Delete or Keep."
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

Run ./scripts/view_queue.sh to see all options and choose."
```

### Workflow Example: Proposing a New Folder

```bash
# User says: "organize next file"

# 1. You find and analyze the file
ls -lt ~/Downloads/  # Find next file (sorted by newest first)
# Found: "Wealthsimple-Statement-2024-01.pdf" (most recent file)

# 2. Analyze the file content
read /Users/marklampert/Downloads/Wealthsimple-Statement-2024-01.pdf
# Identified: Investment statement from Wealthsimple (new platform not in filing system)

# 2.5. Check for duplicates
./scripts/find_duplicates.sh \
  "/Users/marklampert/Downloads/Wealthsimple-Statement-2024-01.pdf" \
  "/Users/marklampert/Dropbox/Filing/"
# Returns: {"source_checksum": "def456...", "duplicates": []}
# No duplicates found - continue

# 3. Explore existing destinations
glob "**/*Wealthsimple*" ~/Dropbox/Filing/
# Returns: No matches found

glob "**/*Investment*" ~/Dropbox/Filing/
# Found: ~/Dropbox/Filing/Investments - Angel/, Investments - Funds/, Investments - Advisors/
# None match Wealthsimple (online brokerage platform)

glob "**/TD WebBroker*" ~/Dropbox/Filing/
# Found: ~/Dropbox/Filing/TD WebBroker/ (similar brokerage platform)
# Pattern suggests creating dedicated folder for each brokerage

# 4. Decision: Propose new folder "Wealthsimple"
# Rationale: Similar platforms (TD WebBroker) have dedicated folders
# Confidence: 75% (clear category, following existing pattern, but new folder)

# 5. Generate UUID and add to queue with new_folder flag
{
  "id": "a1b2c3d4-e5f6-47de-b88f-f20fc4f93cf0",
  "source_path": "/Users/marklampert/Downloads/Wealthsimple-Statement-2024-01.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Wealthsimple/Wealthsimple-2024-01-31.pdf",
  "new_folder": true,
  "confidence": 75,
  "confidence_factors": {
    "similar_platform_pattern": 25,
    "file_type_match": 20,
    "entity_keyword": 20,
    "content_match": 10
  },
  "status": "pending",
  "timestamp": "2025-01-21T16:00:00Z",
  "reasoning": "New investment platform (Wealthsimple) not currently in filing system. Proposing new folder following pattern of existing brokerage folders (TD WebBroker). Investment statement matches PDF format typical of brokerage platforms."
}

# 6. Inform the user
"New folder proposal! Wealthsimple investment statement to be filed in new folder:
/Users/marklampert/Dropbox/Filing/Wealthsimple/

Confidence: 75% (following existing pattern for brokerage platforms)
Will create new folder if approved.

Run ./scripts/view_queue.sh to review and approve.""
```

---

## User Review and Approval via Viewer UI

The **viewer UI** is the primary way to review and execute file organization. Open it with `./scripts/view_queue.sh` (launches the custom FileQueueViewer.app).

**All files require explicit user action** - clicking the Move or Skip button in the UI.

### In the Viewer UI:
- **Move button** - Immediately moves the file to the suggested destination
- **Skip button** - Removes from queue without moving (file stays in original location)
- **Confidence scores** help you prioritize which suggestions to trust
- **Directory listings** show what's already in the destination folder
- **Success notifications** confirm when files are moved

### Confidence Scores Guide Your Decision:
- **90-100%**: High confidence - Claude found strong matching patterns and similar files
- **70-89%**: Good confidence - Clear categorization with some supporting evidence
- **50-69%**: Moderate confidence - Reasonable guess but limited supporting evidence
- **Below 50%**: Low confidence - Unclear categorization, review carefully

### Optional: Batch Processing
For power users, `organize.sh` can still be used for batch operations:
- `./organize.sh --dry-run` - Preview all suggestions without executing
- `./organize.sh --status` - Check queue status from command line

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
- Set destination to unknown folder: `~/Downloads/unknown/`
- Include reasoning about why categorization is unclear

### Multiple Valid Destinations
- Score each option independently using confidence factors
- Choose the highest confidence as primary destination
- Save all alternatives with confidence >= 60% to `alternatives` array
- For each alternative, explain key differences from primary
- DO NOT reduce primary confidence - each option is scored independently

### Special File Types
- **DMG files**: `~/Downloads/installers/`
- **Screenshots**: `~/Downloads/Screenshots/`
- **Unknown/unclear**: `~/Downloads/unknown/`

---

## Quick Command Reference

```bash
# MANDATORY: Analyze file content before suggesting destination
./scripts/analyze_content.sh <file_path>      # Returns JSON with content analysis

# Open viewer UI (primary method)
./scripts/view_queue.sh          # Launches FileQueueViewer.app with custom icon

# Optional batch operations
./organize.sh --dry-run          # Preview all suggestions
./organize.sh --status           # Check pending file count

# Validate before adding
./scripts/validate_suggestion.sh <source> <dest>

# Check for duplicates
./scripts/find_duplicates.sh <source> <dest_dir>

# Generate UUID for file ID
uuidgen | tr '[:upper:]' '[:lower:]'
```

---

## Summary

1. **You analyze** files and add JSON entries to `state/file_queue.json`
2. **User reviews** suggestions in the viewer UI (`./scripts/view_queue.sh`)
3. **User clicks Move** → file is immediately moved to destination
4. **User clicks Skip** → file is moved to `~/Downloads/Skipped/` for later review
5. **System tracks** operations in JSON for transparency

Your job is to be the "brain" - analyze files intelligently and create accurate suggestions. The user is the decision-maker. The viewer UI is the "hands" - it handles all actual file operations immediately when the user clicks Move or Skip.
