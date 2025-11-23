# File Naming Conventions

Apply these naming patterns based on the destination category:

## Financial Documents
- **Bank Statements**: `YYYY-MM-DD_[account_identifier].pdf`
  - Example: `2024-04-30_x2705.pdf` (TD Chequing)
- **HoldCo Bank Statements**: `YYYY-MM-DD [Currency] [Account].pdf`
  - Use **start date only** (not date range)
  - Examples:
    - `2024-10-31 USD 1043-7309548.pdf`
    - `2024-01-31 CAD 1043-5236007.pdf`
- **Credit Card Statements**: `YYYY-MM-DD_[card_identifier].pdf`
- **Investment Documents**: `YYYY-MM-DD [Document_Type] - [Details].pdf`

## Utility Bills
- **Pattern**: `[Provider]-YYYY-MM-DD.pdf`
- **Examples**: 
  - `Rogers-2024-01-10.pdf`
  - `Bell-2024-02-15.pdf`
  - `Toronto Hydro-2024-03-20.pdf`

## Insurance Documents
- **Pattern**: `YYYY-MM-DD [Document_Type] - [Details].ext`
- **Examples**:
  - `2025-04-25 Scenarios Summary.xlsx`
  - `2025-04-11 Insurance as an Alternative Investment (April 2025).pdf`
  - `2024-11-18 Policy Application.pdf`

## General Business Documents
- **Pattern**: `YYYY-MM-DD [Descriptive_Name].ext`
- **Remove redundant entity names**: If file is going into "TD Chequing" folder, don't include "TD" in filename

## File Cleaning Rules
1. **Remove**: Leading underscores (`_Scenarios` → `Scenarios`)
2. **Remove**: Version numbers in parentheses (`(1)`, `(2)`, `copy`)
3. **Remove**: Temporary file indicators (`~$`, `.tmp`)
4. **Standardize**: Date format to `YYYY-MM-DD`
5. **Normalize**: Replace multiple spaces with single spaces
6. **Remove**: File path redundancy (don't repeat folder name in filename)

## Examples

### Before & After
```
_Scenarios Summary - 2025-04-25 (1).xlsx
→ 2025-04-25 Scenarios Summary v2.xlsx

Rogers_Bill_January_2025.pdf  
→ Rogers-2025-01-10.pdf

TD_Statement_Feb2025.pdf
→ 2025-02-28_x2705.pdf
```

### Common Transformations
- Remove leading `_`: `_filename.ext` → `filename.ext`
- Remove version: `file (1).ext` → `file.ext` or `file v2.ext`
- Standardize dates: `Feb2025` → `2025-02-28`
- Provider format: `Rogers_Bill_Jan` → `Rogers-2025-01-XX`