# File Organization System

A Claude Code-driven file organization system that intelligently organizes files with confidence-based routing, comprehensive safety features, and undo capability.

## 🚀 Quick Start

```bash
# 1. Ask Claude to analyze files
"organize next file"

# 2. Process the queue
./organize.sh               # Interactive mode with confirmations
./organize.sh --auto        # Automatic (high-confidence only)
./organize.sh --dry-run     # Preview without executing

# 3. Check status or undo if needed
./organize.sh --status      # View queue status
./organize.sh --undo        # Revert last batch of operations
```

## 📁 Repository Structure

```
filemanager-simple/
├── organize.sh                 # ⭐ Main script - unified workflow
├── config.yaml                 # ⚙️  Configuration (paths & thresholds)
├── state/                      # 📊 State management
│   ├── file_queue.json        # Pending file operations
│   ├── history.json           # Undo capability
│   └── README.md              # State file documentation
├── scripts/                    # 🔧 Helper scripts
│   ├── validate_suggestion.sh # Validation tool for Claude
│   ├── auto_execute.sh.bak    # (archived)
│   └── execute.sh.bak         # (archived)
├── docs/                       # 📖 Documentation
│   ├── filing-structure.md    # Directory layout
│   ├── naming-conventions.md  # File naming patterns
│   └── examples.md            # Usage examples
├── logs/                       # 📝 Archived logs (old system)
│   ├── organize_log.md.bak
│   └── execution_log.md.bak
├── CLAUDE.md                   # 🧠 Instructions for Claude
└── README.md                   # 👋 This file
```

## 🎯 How It Works

### The Workflow

1. **Claude Analyzes** - When you say "organize next file", Claude:
   - Finds unorganized files in Downloads/Desktop
   - Analyzes content and finds similar files
   - Calculates confidence score (0-100%)
   - Adds suggestion to `state/file_queue.json` as JSON

2. **organize.sh Executes** - You run the script to process the queue:
   - **90-100% confidence**: Auto-approved, executed immediately
   - **50-89% confidence**: Asks for your confirmation
   - **0-49% confidence**: Moved to `~/Files/unknown/`

3. **Full Undo** - Every operation is tracked in `history.json`:
   - Run `./organize.sh --undo` to revert the last batch
   - File hashes ensure integrity

### Architecture

```
┌─────────────┐
│   Claude    │ Analyzes files, calculates confidence,
│  (Brain)    │ adds JSON entries to queue
└─────┬───────┘
      │
      ▼
┌──────────────────────┐
│ state/file_queue.json│ Stores pending operations as structured data
└─────┬────────────────┘
      │
      ▼
┌─────────────┐
│ organize.sh │ Executes based on confidence,
│  (Hands)    │ tracks history for undo
└──────────────┘
```

## 📊 Confidence Scoring

Files are scored 0-100% based on:

**Positive Factors:**
- +30%: Similar files found in destination
- +20%: File type matches folder content
- +20%: Strong entity keywords (TD, Rogers, etc.)
- +15%: Content matches category patterns
- +10%: Naming pattern matches existing files
- +5%: File size similar to others

**Negative Factors:**
- -20%: Ambiguous or generic filename
- -30%: No similar files in filing directory
- -20%: Multiple equally valid destinations

## 🏗️ File Categories

### Main Directory: `~/Dropbox/Filing/`
Entity-based organization:
- **Financial**: TD, RBC, Tangerine (by account)
- **Insurance**: Life Insurance, Property Insurance
- **Business**: HoldCo, Uken, Jam City
- **Utilities**: Rogers, Bell, Hydro
- **Real Estate**: By property address
- **Legal/Personal**: Family Trust, Wills, etc.

### Special Directories
- `~/Downloads/installers/` - DMG files and software
- `~/Downloads/Screenshots/` - Screenshot images
- `~/Downloads/unknown/` - Low-confidence files

## 🔧 Command Reference

### Main Commands

```bash
./organize.sh               # Interactive - asks for medium confidence
./organize.sh --auto        # Auto mode - high confidence only
./organize.sh --dry-run     # Preview what would happen
./organize.sh --status      # Show queue status
./organize.sh --undo        # Revert last batch
./organize.sh --help        # Show help
```

### Helper Commands

```bash
# Validate a suggestion before adding to queue
./scripts/validate_suggestion.sh "<source>" "<dest>"

# Check queue manually
cat state/file_queue.json | jq '.files[] | select(.status == "pending")'

# View history
cat state/history.json | jq '.operations[-5:]'  # Last 5 operations
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Source directories to scan
source_directories:
  - ~/Downloads
  - ~/Desktop

# Main filing directory
filing_root: ~/Dropbox/Filing

# Confidence thresholds (0-100)
thresholds:
  auto_approve: 90    # Execute immediately
  ask_user: 50        # Require confirmation
  # Below ask_user → unknown folder
```

## 🛡️ Safety Features

- ✅ **Undo Capability** - Revert operations with `--undo`
- ✅ **Dry-Run Mode** - Preview before executing
- ✅ **File Validation** - Check existence, permissions, conflicts
- ✅ **Conflict Resolution** - Prompt to overwrite/rename/skip
- ✅ **Atomic Operations** - File hashes verify integrity
- ✅ **Detailed Logging** - All operations tracked with timestamps
- ✅ **State Management** - JSON tracking of all file operations

## 🎨 Features

### What's New in 2.0

- ✨ **Single Unified Script** - No more confusion about which script to run
- ✨ **JSON State Management** - Structured data instead of markdown parsing
- ✨ **Full Undo** - Revert any batch of operations
- ✨ **Validation Helper** - Claude can test suggestions before adding
- ✨ **Better Error Handling** - Comprehensive checks and clear messages
- ✨ **Configuration File** - Customize paths and thresholds
- ✨ **Color Output** - Clear visual feedback
- ✨ **Progress Indicators** - Know what's happening
- ✨ **Status Command** - Check queue at any time

### Platform Support

- ✅ **macOS** - Fully supported (BSD tools)
- ✅ **Linux** - Fully supported (GNU tools)
- ⚠️ **Windows** - Requires WSL

## 📚 Documentation

- **[CLAUDE.md](CLAUDE.md)** - Complete instructions for Claude
- **[Filing Structure](docs/filing-structure.md)** - Directory organization
- **[Naming Conventions](docs/naming-conventions.md)** - File naming rules
- **[Examples](docs/examples.md)** - Detailed workflow examples
- **[State Files](state/README.md)** - JSON schema documentation

## 🔍 Troubleshooting

### Queue not processing?
```bash
./organize.sh --status  # Check if files are in queue
cat state/file_queue.json | jq  # View raw JSON
```

### Need to start fresh?
```bash
# Clear queue (keep history for undo)
echo '{"schema_version": "1.0", "files": []}' > state/file_queue.json

# Clear everything
echo '{"schema_version": "1.0", "operations": []}' > state/history.json
```

### Validation failing?
```bash
# Test a specific path
./scripts/validate_suggestion.sh "/path/to/source" "/path/to/dest"
```

## 🤝 Contributing

This is a personal tool, but improvements welcome! Key areas:

- Better confidence scoring algorithms
- Duplicate detection
- File type-specific handlers
- Analytics and reporting
- Additional platform support

## 📝 License

Personal use. No license.

---

## Changelog

### Version 2.0 (2025-01-21)
- Complete redesign with unified organize.sh script
- JSON-based state management
- Full undo capability
- Validation helper for Claude
- Configuration file support
- Platform-independent (macOS & Linux)
- Comprehensive error handling

### Version 1.0 (2025-01-09)
- Initial release with markdown-based logging
- Separate auto_execute.sh and execute.sh scripts
