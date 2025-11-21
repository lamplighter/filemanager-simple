# File Organization System

A Claude Code-driven file organization system that processes unorganized files with intelligent confidence-based routing.

## 🚀 Quick Start

```bash
# Auto-organize files with confidence-based routing
./scripts/auto_execute.sh --dry-run  # Preview what would happen
./scripts/auto_execute.sh            # Interactive mode
./scripts/auto_execute.sh --auto     # Fully automated
```

## 📁 Repository Structure

```
filemanager-simple/
├── docs/                      # 📖 Documentation
│   ├── filing-structure.md   # Directory structure & categories  
│   ├── naming-conventions.md # File naming patterns
│   └── examples.md           # Example workflows
├── scripts/                   # 🔧 Executable scripts
│   ├── auto_execute.sh       # ⭐ Intelligent auto-router
│   └── execute.sh            # Manual execution helper
├── logs/                      # 📝 Organization logs
│   ├── organize_log.md       # Suggestions with confidence scores
│   └── execution_log.md      # Approved commands ready to run
├── CLAUDE.md                  # 🧠 Core instructions for Claude
└── README.md                  # 👋 This file
```

## 🎯 How It Works

### 1. Organization Phase
- Ask Claude: `"organize next file"` or `"file _filename"`  
- Claude analyzes files and calculates confidence scores (0-100%)
- Suggestions logged in `logs/organize_log.md` with detailed reasoning

### 2. Auto-Routing Phase ⭐ 
- **90-100% confidence**: Auto-approve → `logs/execution_log.md`
- **50-89% confidence**: Ask for user confirmation  
- **0-49% confidence**: Auto-move to `~/Files/unknown/`

### 3. Execution Phase
- Run `./scripts/execute.sh` to execute approved moves
- All moves are logged with timestamps and status

## 📊 Confidence Scoring

Files are automatically scored based on:
- **+30%**: Similar files found in destination
- **+20%**: File type matches folder content
- **+20%**: Strong entity keywords (TD, Rogers, etc.)
- **+15%**: Content matches category patterns
- **+10%**: Naming pattern matches existing files
- **+5%**: File size similar to others in category
- **-20%**: Ambiguous or generic filename
- **-30%**: No similar files in Filing directory

## 🏗️ File Categories

The system organizes files into:

### Main Directory: `~/Dropbox/Filing/`
Entity-based structure with:
- **Financial** (Banking, Investments, Insurance)  
- **Business** (HoldCo, Uken, Jam City, etc.)
- **Real Estate** (by property address)
- **Utilities** (Rogers, Bell, Toronto Hydro, etc.)
- **Legal & Personal** documents

### Special Directories
- **`~/Files/installers/`** - DMG files and software installers
- **`~/Files/screenshots/`** - Screenshot images
- **`~/Files/unknown/`** - Files that cannot be categorized

## 🔧 Usage Examples

```bash
# Preview auto-routing decisions
./scripts/auto_execute.sh --dry-run

# Interactive mode (asks for medium confidence files)  
./scripts/auto_execute.sh

# Fully automated (only processes high confidence)
./scripts/auto_execute.sh --auto

# Manual execution of approved commands
./scripts/execute.sh --dry-run  # Preview
./scripts/execute.sh            # Execute

# Get help
./scripts/auto_execute.sh --help
./scripts/execute.sh --help
```

## 📚 Documentation

- **[Filing Structure](docs/filing-structure.md)** - Complete directory layout and categories
- **[Naming Conventions](docs/naming-conventions.md)** - File naming patterns and rules  
- **[Examples](docs/examples.md)** - Detailed workflow examples and patterns

## 🛡️ Safety Features

- **Dry-run mode** for testing
- **Source file verification** before moves
- **Automatic directory creation**
- **Conflict resolution** for duplicate filenames
- **Detailed logging** with timestamps
- **Backup creation** before modifications

## 🎨 Features

- ✅ **Intelligent confidence scoring** - Learn from existing file patterns
- ✅ **Auto-routing** - Reduce manual review burden  
- ✅ **Pattern recognition** - Find similar files automatically
- ✅ **Smart renaming** - Apply consistent naming conventions
- ✅ **Interactive confirmation** - Ask when uncertain
- ✅ **Comprehensive logging** - Track all decisions and reasoning