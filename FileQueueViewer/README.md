# FileQueueViewer - SwiftUI Native App

A native macOS app for reviewing and executing file organization suggestions from the Hoot file organizer.

## Quick Start

1. Open the project in Xcode:
   ```bash
   open FileQueueViewer.xcodeproj
   ```

2. Build and run (⌘R)

3. The app reads from `../state/file_queue.json` and displays pending files

## Features

- **Native SwiftUI table** with sorting and filtering
- **Confidence badges** (high/medium/low)
- **Detail sheet** with tabs:
  - Details: paths, reasoning, confidence breakdown
  - Preview: PDF, images, text files
  - Directory: existing files in destination
- **Bulk actions**: move or skip multiple files
- **Auto-refresh**: watches queue file for changes
- **Keyboard shortcuts**:
  - ⌘M: Move selected
  - ⌘S: Skip selected
  - ⌘R: Refresh queue

## No Server Required

Unlike the old HTML-based viewer, this app:
- Reads JSON files directly (no HTTP server)
- Performs file operations natively (no Python)
- Is a single self-contained .app

## Project Structure

```
FileQueueViewer/
├── FileQueueViewerApp.swift  # App entry point
├── ContentView.swift         # Main table view
├── Models/
│   ├── FileEntry.swift       # Queue data model
│   └── QueueManager.swift    # Load/save/watch queue
├── Views/
│   ├── ConfidenceBadge.swift
│   ├── PreviewView.swift
│   ├── DirectoryListView.swift
│   └── FileDetailSheet.swift
└── Services/
    └── FileOperations.swift  # Move, skip, delete
```

## Building

### In Xcode
1. Open `FileQueueViewer.xcodeproj`
2. Select "My Mac" as destination
3. ⌘R to build and run

### From Command Line (requires Xcode)
```bash
xcodebuild -project FileQueueViewer.xcodeproj -scheme FileQueueViewer -configuration Release build
```

The built app will be in `build/Release/FileQueueViewer.app`

## Deployment

After building, copy the app to a convenient location:
```bash
cp -r build/Release/FileQueueViewer.app ~/Applications/
```

Then update the Hoot `/view` command to open this app.
