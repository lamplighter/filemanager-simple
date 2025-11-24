# Filing Structure

## Directory Structure

### Source Directories (Unorganized)
- `~/Downloads/` - Downloaded files that need to be organized
- `~/Desktop/` - Desktop files that need to be organized

### Destination Directories (Organized)
- `~/Dropbox/Filing/` - **EXISTING** Main organized directory with extensive financial/personal structure:
  - **Financial**: Banking (TD, RBC, Tangerine), Credit Cards, Investments (Angel, Funds), Insurance
  - **Real Estate**: 40 Gibson Ave, Cottage, other properties with permits/docs
  - **Business**: HoldCo, Uken, Jam City, Priority Submetering
  - **Utilities**: Rogers (Wireless, Internet, Security), Bell, Hydro, etc.
  - **Legal**: Family Trust, Will, Legal matters
  - **Vehicles**: Mazda CX-5
  - **Personal**: Life Insurance, Executive Assistant, Housekeeper

  *Note: This directory is highly organized by entity/account rather than file type*

- `~/Dropbox/Taxes/` - **EXISTING** Tax returns, CRA correspondence, and tax-related documents:
  - **HoldCo**: Corporate tax returns (by year), CRA notices, audit documents
  - **Personal**: Personal tax returns (by year), tax slips, CRA correspondence
  - **Family Trust**: Trust tax returns and related documents
  - **Custo**: Custo-related tax documents
  - **W-8BEN**: Tax residency forms

  *Note: Organized by entity and year, contains CRA/IRS official documents*

### Special Directories
- `~/Files/` - **EXISTING** but empty base directory
- `~/Files/installers/` - **NEEDS CREATION** - DMG files and software installers
- `~/Files/screenshots/` - **NEEDS CREATION** - Screenshot images  
- `~/Files/unknown/` - **NEEDS CREATION** - Files that cannot be categorized

## Major Filing Categories

The `~/Dropbox/Filing/` directory contains the following main categories:

### Financial Services
- **Banking**: 
  - `TD Chequing/`, `TD Visa/`, `TD WebBroker/`, `TD Bank (US)/`, `TD Borderless/`, `TD Line of Credit/`
  - `RBC/`, `RBC US Visa/`
  - `Tangerine/`
  - **Naming pattern**: `YYYY-MM-DD_[account_identifier].pdf` (e.g., `2024-04-30_x2705.pdf`)

- **Investments**:
  - `Investments - Angel/` - Angel investments organized by company
  - `Investments - Funds/` - VC funds organized by fund name
  - `Investments - Advisors/` - Investment advisor documents
  - `TD Wealth/` - TD wealth management with advisor subfolders

- **Insurance**:
  - `Life Insurance/` - Life insurance policies, applications, scenarios
  - `TD Insurance/` - Property insurance organized by property address
  - **Naming pattern**: `YYYY-MM-DD [Document Type] - [Details].ext`

### Utilities & Services
- **Rogers**: `Rogers - Wireless/`, `Rogers - Internet/`, `Rogers - Home Security/`
- **Utilities**: `Bell/`, `Toronto Hydro/`, `Hydro One/`, `Enbridge/`, `Georgian Bay Propane/`
- **Naming pattern**: `[Provider]-YYYY-MM-DD.pdf` (e.g., `Rogers-2024-01-10.pdf`)

### Business Entities
- **HoldCo**: Corporate documents, bank statements, legal (incorporation, minute book, resolutions)
- **Uken**, **Jam City**: Business-related documents and contracts
- **Priority Submetering**: Business entity documents

### Real Estate
- **Properties**: `Real Estate - 40 Gibson Ave/`, `Real Estate - Cottage/`, `Real Estate - other/`
- **Organization**: By property address with subfolders for permits, insurance, legal, maintenance

### Legal & Personal
- **Legal**: `Family Trust/`, `Will/`, `Legal/` - Legal documents and estate planning
- **Personal Services**: `Executive Assistant/`, `Housekeeper/` - Service provider documents
- **Vehicles**: `Vehicles - Mazda CX-5/` - Vehicle-related documents

## Folder Naming Conventions

### Multi-Part Folder Names
When creating folders with multiple parts (entity-type, account names, related entities), use the **space-hyphen-space** separator:

**Standard**: ` - ` (space-hyphen-space)

**Examples**:
- `Rogers - Wireless` (entity-type)
- `Real Estate - 40 Gibson Ave` (category-location)
- `Investments - Funds` (category-subcategory)
- `TD Visa - CAD Mark x1381` (institution-details)
- `Uken - Jam City` (related entities)

**Do NOT use**:
- `:` (colon alone)
- ` : ` (space-colon-space)
- Mixed separators in the same path

### Archive and Legacy Folders
For archived, old, or legacy content, use the **z prefix** to push folders to the bottom of alphabetical listings:

**Standard**: `z [Descriptor]`

**Examples**:
- `z Old` (general legacy content)
- `z Old CAD Checking` (specific old account)
- `z Archived` (archived content)
- `z Passed` (closed/completed items)

**Benefits**:
- Visual clarity (all archived items grouped at bottom)
- Consistent sorting across all systems
- Easy to identify what's active vs archived

## File Organization Strategy

Given the existing `~/Dropbox/Filing/` structure is entity-based rather than file-type based:
- **Financial documents**: Place in appropriate entity folder in `~/Dropbox/Filing/`
- **Personal documents**: Place in appropriate entity folder or create new entity folder
- **DMG/installers**: `~/Files/installers/` (needs creation)
- **Screenshots**: `~/Files/screenshots/` (needs creation)
- **Unclear files**: `~/Files/unknown/` (needs creation)