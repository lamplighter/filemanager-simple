# File Organization Log

This log tracks all file organization suggestions made by Claude Code.

## Format

Each entry includes:
- **Timestamp**: When the suggestion was made
- **Source File**: Path to the unorganized file
- **Confidence**: 0-100% score with confidence factors
- **Suggested Command**: The mv command to organize the file
- **Reasoning**: Why this location was chosen
- **Action**: Auto-approved (≥90%), Ask user (50-89%), Unknown folder (<50%)
- **Status**: Pending review, approved, rejected, etc.

---

## Suggestions

### 2025-01-09 21:45 - _Consolidated Model (Planned) - 05-30-2025.pdf

- **Source File**: `~/Downloads/_Consolidated Model (Planned) - 05-30-2025.pdf`
- **Confidence**: 85% (Medium-High)
- **Confidence Factors**:
  - +20%: "Consolidated Model" is strong insurance term
  - +20%: PDF matches typical Life Insurance document format
  - +15%: Contains insurance-specific terms (premium, CSV, death benefits, IRR)
  - +10%: Mentions specific people (Mark & Ashley Lampert)
  - +15%: Sun Life is known insurance company
  - +5%: File structure matches insurance planning documents
- **Suggested Command**: `mv ~/Downloads/_Consolidated\ Model\ \(Planned\)\ -\ 05-30-2025.pdf ~/Dropbox/Filing/Life\ Insurance/`
- **Reasoning**: Sun Life consolidated model showing premium schedules, CSV, death benefits, and IRR for multiple policies for Mark & Ashley Lampert. Fits with existing Life Insurance folder structure.
- **Action**: Ask user (50-89% confidence)
- **Status**: Pending review

---

### 2024-09-08 - backup_photos.zip

- **Source File**: `unorganized/backup_photos.zip`
- **Confidence**: 45% (Low-Medium)
- **Confidence Factors**:
  - +20%: Clear filename indicates "backup_photos"
  - +5%: .zip extension matches archive format
  - -30%: No similar files found in Filing directory
  - -20%: Generic destination path doesn't match current Filing structure
  - +20%: Filename is descriptive and unambiguous
- **Suggested Command**: `mv unorganized/backup_photos.zip organized/archives/backups/`
- **Reasoning**: File has .zip extension and filename contains "backup_photos", indicating it's a backup archive of photo files. Best placed in archives/backups/ subdirectory.
- **Action**: Unknown folder (<50% confidence)
- **Status**: Pending review

---

---

### 2025-09-09 - _Scenarios Summary - 2025-04-25 (1).xlsx

- **Source File**: `/Users/marklampert/Downloads/_Scenarios Summary - 2025-04-25 (1).xlsx`
- **Confidence**: 95% (High)
- **Confidence Factors**:
  - +30%: Found 4 similar "Scenarios Summary" files in exact destination folder
  - +20%: .xlsx extension matches typical Life Insurance planning files
  - +20%: "Scenarios" is strong insurance planning term
  - +15%: Content structure matches insurance planning documents
  - +10%: Date format (YYYY-MM-DD) matches existing naming pattern
- **Suggested Command**: `mv "/Users/marklampert/Downloads/_Scenarios Summary - 2025-04-25 (1).xlsx" "/Users/marklampert/Dropbox/Filing/Life Insurance/Continuum/planning/2025-04-25 Scenarios Summary v2.xlsx"`
- **Reasoning**: Found multiple similar "Scenarios Summary" files in Life Insurance/Continuum/planning/. Applied standard naming pattern YYYY-MM-DD [Document Type].xlsx. Removed leading underscore and version number (1). Added "v2" to differentiate from existing 2025-04-25 Scenarios Summary.xlsx. File size (69,759 bytes) matches similar file from 2025-04-27, suggesting updated version.
- **Action**: Auto-approved (confidence ≥ 90%)
- **Status**: Auto-approved → execution_log.md

---

### 2025-09-09 - REVERSAL-DELETION REQUEST.pdf

- **Source File**: `/Users/marklampert/Downloads/REVERSAL-DELETION REQUEST.pdf`
- **Confidence**: 25% (Low)
- **Confidence Factors**:
  - +20%: PDF format is clear document type
  - -30%: No similar files found in Filing directory
  - -20%: Generic administrative document type
  - +5%: Clear filename describing content
- **Suggested Command**: `mv "/Users/marklampert/Downloads/REVERSAL-DELETION REQUEST.pdf" "/Users/marklampert/Files/unknown/2023-09-06 REVERSAL-DELETION REQUEST.pdf"`
- **Reasoning**: Administrative document with no clear category match. Generic nature suggests placement in unknown folder.
- **Action**: Unknown folder (<50% confidence)
- **Status**: Auto-move to unknown

---

### 2025-09-09 - Staff List - Uken Inc 2021 -CY (1).xlsx

- **Source File**: `/Users/marklampert/Downloads/Staff List - Uken Inc 2021 -CY (1).xlsx`
- **Confidence**: 85% (Medium-High)
- **Confidence Factors**:
  - +30%: Found multiple Uken files in Filing directory
  - +20%: .xlsx matches business document format
  - +20%: "Uken Inc" is strong entity keyword
  - +15%: Content matches business entity patterns
  - +10%: Year format (2021) matches existing naming
  - -10%: Version number (1) needs cleaning
- **Suggested Command**: `mv "/Users/marklampert/Downloads/Staff List - Uken Inc 2021 -CY (1).xlsx" "/Users/marklampert/Dropbox/Filing/Uken/2021 Staff List.xlsx"`
- **Reasoning**: Found existing Uken folder with incorporation documents. Staff list is business document for established entity.
- **Action**: Ask user (50-89% confidence)
- **Status**: Pending review

---

### 2025-09-09 - earnings_earnings_202209_5381357678263438-152.zip

- **Source File**: `/Users/marklampert/Downloads/earnings_earnings_202209_5381357678263438-152.zip`
- **Confidence**: 20% (Low)
- **Confidence Factors**:
  - -30%: No similar files found in Filing directory
  - -20%: Cryptic filename with random numbers
  - -20%: Generic "earnings" term without entity
  - +10%: Date pattern (202209) identifiable
  - +20%: Clear file type (.zip)
- **Suggested Command**: `mv "/Users/marklampert/Downloads/earnings_earnings_202209_5381357678263438-152.zip" "/Users/marklampert/Files/unknown/2022-09 earnings_5381357678263438-152.zip"`
- **Reasoning**: Generic earnings file with cryptic naming. No clear entity or category match found.
- **Action**: Unknown folder (<50% confidence)
- **Status**: Auto-move to unknown

---

### 2025-09-09 - Statement_71H775_Dec-2020.pdf

- **Source File**: `/Users/marklampert/Downloads/Statement_71H775_Dec-2020.pdf`
- **Confidence**: 75% (Medium-High)
- **Confidence Factors**:
  - +20%: PDF matches bank statement format
  - +15%: "Statement" indicates financial document
  - +15%: Account number pattern (71H775) matches banking
  - +10%: Date format (Dec-2020) matches existing patterns
  - +20%: Found similar HoldCo bank statements from 2020
  - -5%: No exact account match found
- **Suggested Command**: `mv "/Users/marklampert/Downloads/Statement_71H775_Dec-2020.pdf" "/Users/marklampert/Dropbox/Filing/HoldCo/bank statements/2020-12-31_71H775.pdf"`
- **Reasoning**: Bank statement with account identifier. Found HoldCo bank statements folder with similar 2020 files.
- **Action**: Ask user (50-89% confidence)
- **Status**: Pending review

---

### 2025-09-09 - LOE - 2021 Personal Tax Return Engagement Letter (1).pdf

- **Source File**: `/Users/marklampert/Downloads/LOE - 2021 Personal Tax Return Engagement Letter (1).pdf`
- **Confidence**: 65% (Medium)
- **Confidence Factors**:
  - +20%: PDF matches professional document format
  - +15%: "Personal Tax" indicates clear category
  - +10%: Year (2021) provides date context
  - +15%: Found tax-related files in Filing directory
  - -20%: No specific personal tax folder found
  - +10%: "Engagement Letter" indicates professional service
  - -5%: Version number (1) needs cleaning
- **Suggested Command**: `mv "/Users/marklampert/Downloads/LOE - 2021 Personal Tax Return Engagement Letter (1).pdf" "/Users/marklampert/Dropbox/Filing/Legal/2021 Personal Tax Engagement Letter.pdf"`
- **Reasoning**: Personal tax engagement letter, professional legal document. Placed in Legal folder as tax preparation is legal/professional service.
- **Action**: Ask user (50-89% confidence)
- **Status**: Pending review

---
