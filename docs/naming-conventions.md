# Naming Conventions

This document covers both **folder naming** and **file naming** conventions for the filing system.

---

## Folder Naming Conventions

### Multi-Part Folder Names
When creating folders with multiple components, use the **space-hyphen-space** separator consistently:

**Standard**: ` - ` (space-hyphen-space)

**Examples**:
- `Rogers - Wireless` (entity and service type)
- `Real Estate - 40 Gibson Ave` (category and specific property)
- `TD Visa - CAD Mark x1381` (institution and account details)
- `Investments - Angel` (category and investment type)
- `Uken - Jam City` (related business entities)

**NOT Allowed**:
- `:` (colon) - e.g., ~~`Uken : Jam City`~~
- ` : ` (space-colon-space) - e.g., ~~`TD Visa : USD`~~
- Mixed separators - e.g., ~~`Mark x1381:x3752 : Ashley`~~

### Archive and Legacy Folders
For old, archived, or legacy content, use the **z prefix**:

**Standard**: `z [Descriptor]`

**Examples**:
- `z Old` - general legacy files
- `z Old CAD Checking` - specific legacy account
- `z Archived` - archived content
- `z Passed` - closed investments or completed items

**Benefits**:
- Alphabetically sorted to bottom of directory listings
- Instantly recognizable as non-current content
- Consistent across all folders

---

## File Naming Conventions

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
- **Pattern**: `YYYY-MM-DD [Document_Type] - [Property].ext`
- **Document Types**: Renewal, Policy Change, Coverage Increase, Pink Card, Issuance, Servicing Letter
- **Property Identifiers** (use short, consistent names):
  - `Cottage` - 1035 Fire Route 20G, Gravenhurst
  - `40 Gibson` - 40 Gibson Ave (house)
  - `Carlaw` - 319 Carlaw Ave Unit 711 (rental condo)
  - `[Vehicle Make Model]` - for auto insurance (e.g., "Mazda CX-5")
  - `Cottage + Carlaw` - for multi-property documents
  - `All Properties` - for portfolio-wide documents
- **Examples**:
  - `2024-11-13 Renewal - Cottage + Carlaw.pdf` (multi-property renewal)
  - `2024-09-30 Coverage Increase - Cottage.pdf` (single property change)
  - `2021-06-23 Pink Card - Mazda CX-5.pdf` (auto insurance card)
  - `2024-11-18 Policy Application - 40 Gibson.pdf` (new policy application)
  - `2025-04-25 Scenarios Summary.xlsx` (general analysis, no property)
  - `2025-04-11 Insurance as an Alternative Investment (April 2025).pdf` (general article)
- **Machine-Generated Names to Avoid**:
  - ❌ `00134652057_2023-11-13_Renewal_0000252724963.pdf` (policy numbers, document IDs)
  - ❌ `Renewal_0000252724963 (1).pdf` (version numbers without context)

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