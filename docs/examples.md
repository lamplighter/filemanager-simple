# File Organization Examples

## Overview

This document shows real-world examples of the file organization workflow using the new JSON-based system.

## Complete Workflow

For each file to be organized:

1. **Analyze** the file (content, metadata, filename)
2. **Explore** similar files in potential destinations
3. **Calculate** confidence score based on findings
4. **Generate** UUID and create JSON entry
5. **Add** to `state/file_queue.json`
6. **User reviews** in viewer UI (run `./scripts/view_queue.sh`) and clicks Move or Skip

## Enhanced Workflow Examples

### Example 1: Insurance Document (High Confidence)

**Scenario**: `_Scenarios Summary - 2025-04-25 (1).xlsx` found in Downloads

#### Step 1: Find and Analyze

```bash
# Find file in Downloads
ls ~/Downloads/
# Found: _Scenarios Summary - 2025-04-25 (1).xlsx

# Initial Analysis:
- Extension: .xlsx (Excel spreadsheet)
- Filename contains: "Scenarios", "Summary", date "2025-04-25"
- Keywords suggest: Life Insurance, Financial planning
```

#### Step 2: Explore Destinations

```bash
# Search for similar files:
find ~/Dropbox/Filing/Life\ Insurance -name "*Scenarios*" -type f

# Results found:
# ~/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary.xlsx
# ~/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-22 Scenarios Summary.xlsx

# Check naming pattern:
ls ~/Dropbox/Filing/Life\ Insurance/Continuum/planning/*.xlsx
# Pattern: YYYY-MM-DD [Document Type].xlsx
```

#### Step 3: Calculate Confidence

- **+30%**: Found 2 similar files in exact destination
- **+20%**: .xlsx matches folder content
- **+20%**: "Scenarios" is insurance planning term
- **+15%**: Pattern matches existing files
- **+10%**: Date format consistent
- **Total: 95%** (High confidence - will auto-execute)

#### Step 4: Generate UUID

```bash
uuidgen | tr '[:upper:]' '[:lower:]'
# Result: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

#### Step 5: Create JSON Entry

```json
{
  "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "source_path": "/Users/marklampert/Downloads/_Scenarios Summary - 2025-04-25 (1).xlsx",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary v2.xlsx",
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
  "reasoning": "Found 2 similar 'Scenarios Summary' files in Life Insurance/Continuum/planning/ folder. Applied standard naming pattern YYYY-MM-DD [Document Type].xlsx. Removed leading underscore and version number (1). Added 'v2' since 2025-04-25 Scenarios Summary.xlsx already exists."
}
```

#### Step 6: Add to Queue

```bash
# Read existing queue
Read state/file_queue.json

# Append new entry to files array
Write state/file_queue.json
```

#### Step 7: Execute

```bash
./organize.sh
# Output:
# Processing 1 file(s)...
#
# [1/1] _Scenarios Summary - 2025-04-25 (1).xlsx
#   Confidence: 95%
#   Destination: .../Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary v2.xlsx
#   ℹ HIGH CONFIDENCE - Auto-approving
#   ✓ Moved to .../2025-04-25 Scenarios Summary v2.xlsx
#
# Summary:
#   Processed: 1
#   Auto-approved: 1
#   ✓ File organization complete!
```

### Example 2: Utility Bill (Medium Confidence)

```json
{
  "id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "source_path": "/Users/marklampert/Downloads/Rogers_Bill_January_2025.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/Rogers - Wireless/Rogers-2025-01-10.pdf",
  "confidence": 75,
  "confidence_factors": {
    "similar_files_found": 30,
    "file_type_match": 20,
    "entity_keyword": 20,
    "naming_pattern": 5
  },
  "status": "pending",
  "timestamp": "2025-01-21T15:00:00Z",
  "reasoning": "Found Rogers invoices in Rogers - Wireless folder. Applied naming pattern Rogers-YYYY-MM-DD.pdf. Confidence reduced due to unclear date (using first of month)."
}
```

**Execution**: Will ask for confirmation (75% = medium confidence)

### Example 3: Bank Statement (High Confidence)

```json
{
  "id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
  "source_path": "/Users/marklampert/Downloads/TD_Statement_Feb2025.pdf",
  "dest_path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2025-02-28_x2705.pdf",
  "confidence": 92,
  "confidence_factors": {
    "similar_files_found": 30,
    "file_type_match": 20,
    "entity_keyword": 20,
    "content_match": 12,
    "naming_pattern": 10
  },
  "status": "pending",
  "timestamp": "2025-01-21T15:15:00Z",
  "reasoning": "Found many TD statements in TD Chequing folder with account x2705. Applied pattern YYYY-MM-DD_x2705.pdf matching existing files."
}
```

**Execution**: Auto-approved (92% ≥ 90%)

### Example 4: DMG File (Special Directory)

```json
{
  "id": "12345678-90ab-cdef-1234-567890abcdef",
  "source_path": "/Users/marklampert/Downloads/Adobe_Installer_v2.dmg",
  "dest_path": "/Users/marklampert/Downloads/installers/Adobe_Installer_v2.dmg",
  "confidence": 100,
  "confidence_factors": {
    "file_type_match": 40,
    "special_directory": 40,
    "clear_purpose": 20
  },
  "status": "pending",
  "timestamp": "2025-01-21T15:30:00Z",
  "reasoning": "DMG file goes to installers folder per documented filing structure. High confidence based on file type and clear purpose."
}
```

**Execution**: Auto-approved (100% confidence)

## File Analysis Guidelines

### Content-Based Pattern Matching
- **For Excel/PDF files**: Look for key indicators in content, not just filename
- **Insurance companies** (Sun Life, Manulife, Equitable, Canada Life, etc.) → Life Insurance
- **Insurance terms** ("Death Benefit", "CSV", "Premium", "Policy", "Illustration") → Life Insurance  
- **Bank names** (TD, RBC, Tangerine, Scotia, BMO) → appropriate Banking subfolder
- **Investment terms** (portfolio, returns, holdings, fund performance) → Investments

### Common File Patterns

#### Life Insurance Documents
- **Content indicators**: premium schedules, death benefits, cash surrender values (CSV), policy illustrations
- **Company names**: Sun Life, Manulife, Equitable, Canada Life, Industrial Alliance
- **Common filenames**: scenarios, consolidated model, illustration, policy, premium schedule
- **Destination**: `~/Dropbox/Filing/Life Insurance/`

#### Investment Documents
- **Content indicators**: portfolio performance, asset allocation, fund holdings, market analysis
- **Company names**: TD Direct, RBC Direct, Questrade, Wealthsimple
- **Common filenames**: statement, holdings, performance report, portfolio summary
- **Destination**: `~/Dropbox/Filing/` (under entity-specific folders like `TD WebBroker/`, `Wealthsimple/`, etc.)

#### Banking Documents
- **Content indicators**: account balances, transactions, statements, credit card activity
- **Company names**: TD Bank, RBC, Tangerine, Scotia, BMO
- **Destination**: `~/Dropbox/Filing/` (under entity-specific folders like `TD Chequing/`, `RBC/`, `Tangerine/`)