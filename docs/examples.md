# File Organization Examples

## Smart Exploration Algorithm

For each file to be organized:

```bash
# 1. Identify potential destinations based on initial analysis
potential_destinations=("Life Insurance" "TD Chequing" "Rogers - Wireless")

# 2. For each potential destination, explore existing files
for dest in potential_destinations; do
    find ~/Dropbox/Filing/"$dest" -name "*similar_keywords*" -type f
    ls ~/Dropbox/Filing/"$dest"/*.{pdf,xlsx} | head -10  # Check patterns
done

# 3. Find most similar existing file
grep -r "content_keywords" ~/Dropbox/Filing/"$best_match_dest"/

# 4. Apply naming pattern based on similar files found
# 5. Suggest final destination and renamed filename
```

## Enhanced Workflow Examples

### Example 1: Insurance Document

**Scenario**: `_Scenarios Summary - 2025-04-25 (1).xlsx` found in Downloads

```bash
# 1. Find Next File
Found: ~/Downloads/_Scenarios Summary - 2025-04-25 (1).xlsx

# 2. Initial Analysis
- Extension: .xlsx (Excel spreadsheet)
- Filename contains: "Scenarios", "Summary", date "2025-04-25"
- Keywords suggest: Life Insurance, Financial planning

# 3. Destination Exploration
# Search for similar files in potential destinations:
find ~/Dropbox/Filing/"Life Insurance" -name "*Scenarios*" -type f
# Results: 
# /Users/mark/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary.xlsx
# /Users/mark/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-22 Scenarios Summary.xlsx

# Check naming patterns in Life Insurance/Continuum/planning/:
ls ~/Dropbox/Filing/"Life Insurance/Continuum/planning"/*.xlsx
# Pattern observed: YYYY-MM-DD [Document Type].xlsx

# 4. Smart Categorization
- Best match: Life Insurance (scenarios = insurance planning term)
- Specific location: Continuum/planning/ (similar files found here)
- High confidence match based on existing "Scenarios Summary" files

# 5. File Renaming
- Remove leading underscore: "_Scenarios" → "Scenarios"
- Remove version number: "(1)" → ""
- Result: "2025-04-25 Scenarios Summary.xlsx"

# 6. Generate Suggestion
mv "~/Downloads/_Scenarios Summary - 2025-04-25 (1).xlsx" \
   "~/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary.xlsx"

# 7. Reasoning
Found 2 similar "Scenarios Summary" files in Life Insurance/Continuum/planning/
Applied standard naming pattern: YYYY-MM-DD [Document Type].xlsx
Removed leading underscore and version number for consistency
```

### Example 2: Utility Bill

```bash
# File: ~/Downloads/Rogers_Bill_January_2025.pdf  
# Exploration: Find similar in Rogers - Wireless/
# Pattern found: Rogers-YYYY-MM-DD.pdf
# Result: mv to ~/Dropbox/Filing/Rogers - Wireless/Rogers-2025-01-10.pdf
```

### Example 3: Bank Statement

```bash
# File: ~/Downloads/TD_Statement_Feb2025.pdf
# Exploration: Find similar in TD Chequing/
# Pattern found: YYYY-MM-DD_x2705.pdf  
# Result: mv to ~/Dropbox/Filing/TD Chequing/2025-02-28_x2705.pdf
```

### Example 4: DMG File

```bash
# File: ~/Downloads/Adobe_Installer_v2.dmg
# Analysis: Software installer
# Destination: ~/Files/installers/Adobe_Installer_v2.dmg
```

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
- **Destination**: `~/Dropbox/Filing/Personal/Life Insurance/`

#### Investment Documents  
- **Content indicators**: portfolio performance, asset allocation, fund holdings, market analysis
- **Company names**: TD Direct, RBC Direct, Questrade, Wealthsimple
- **Common filenames**: statement, holdings, performance report, portfolio summary
- **Destination**: `~/Dropbox/Filing/Financial/Investments/`

#### Banking Documents
- **Content indicators**: account balances, transactions, statements, credit card activity
- **Company names**: TD Bank, RBC, Tangerine, Scotia, BMO
- **Destination**: `~/Dropbox/Filing/Financial/Banking/[Bank Name]/`