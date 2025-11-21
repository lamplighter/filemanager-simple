# File Organizer

This is a Claude Code driven file organization system. It processes unorganized files one at a time with intelligent confidence-based routing.

## Quick Reference

- **Filing Structure**: See `docs/filing-structure.md`
- **Naming Conventions**: See `docs/naming-conventions.md` 
- **Examples**: See `docs/examples.md`
- **Scripts**: Located in `scripts/` folder
- **Logs**: Located in `logs/` folder

## File Organization Process

When asked to "organize next file" or similar:

1. **Find Next File**: Look in `~/Downloads/` and `~/Desktop/` directories for the next file to process

2. **Initial Analysis**: 
   - Check file extension, size, and basic metadata
   - For text files: Use Read tool to examine content (first ~50 lines)
   - For spreadsheets/PDFs: Examine content for entity names and domain-specific terms
   - Identify potential category matches from filing structure

3. **Destination Exploration**:
   - **Search for similar files**: Use find/grep to locate similar files in potential destinations
   - **Analyze existing patterns**: Check naming conventions of files already in target folders
   - **Explore subfolders**: Look at subfolder structure to find the most specific placement
   - **Pattern matching**: Compare file content/name against existing files to find best match

4. **Smart Categorization**:
   - Match against documented category patterns (Financial, Utilities, Business, etc.)
   - Use similarity to existing files to refine placement
   - When multiple options exist, prefer more specific entity folders
   - For unclear categorization, examine 3-5 similar files for pattern confirmation

5. **Calculate Confidence Score** (0-100%):
   - **+30%**: Found similar files in exact destination folder
   - **+20%**: File extension matches folder's typical content
   - **+20%**: Filename contains strong entity keywords (TD, Rogers, Insurance, etc.)
   - **+15%**: Content analysis matches category patterns
   - **+10%**: Date pattern matches existing files in folder
   - **+5%**: File size similar to existing files in category
   - **-20%**: Ambiguous filename or generic terms
   - **-30%**: No similar files found in Filing directory
   - **-20%**: Multiple equally valid destinations exist

6. **File Renaming**:
   - Apply category-specific naming conventions (see `docs/naming-conventions.md`)
   - Remove version numbers `(1)`, `(2)`, etc.
   - Remove leading underscores and normalize spacing
   - Ensure consistent date format: `YYYY-MM-DD`
   - Remove duplicate company names if they're already in the folder path

7. **Auto-Route Based on Confidence**:
   - **90-100%**: Auto-approve → logs/execution_log.md (high confidence)
   - **50-89%**: Generate suggestion for user review (medium confidence)
   - **0-49%**: Auto-move to `~/Files/unknown/` folder (low confidence)

8. **Generate Suggestion**:
   - Create `mv` command that both moves AND renames the file appropriately
   - Include confidence score and detailed confidence factors
   - Provide reasoning including: similar files found, naming pattern applied, destination logic

9. **Log Suggestion**: 
   - Append the suggestion to `logs/organize_log.md`
   - Include confidence score, confidence factors, action taken, and detailed reasoning

## Execution Workflow

### Auto-Processing (Recommended)
```bash
# Run intelligent auto-router
./scripts/auto_execute.sh --dry-run    # Preview
./scripts/auto_execute.sh              # Interactive mode  
./scripts/auto_execute.sh --auto       # Fully automated
```

### Manual Processing
```bash  
# Execute approved commands
./scripts/execute.sh --dry-run         # Preview
./scripts/execute.sh                   # Execute
```

## Important Notes

- **DRY RUN ONLY**: Never actually move files, only suggest mv commands
- **One File at a Time**: Process files individually for careful review
- **Content over Filename**: Don't rely on filename alone - analyze actual content
- **Detailed Logging**: Always log reasoning for human review
- **Safe Suggestions**: If unsure, suggest a general category rather than specific subfolder