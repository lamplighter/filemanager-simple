# State Directory

This directory contains JSON files that track the file organization system's state.

## Files

### file_queue.json
Tracks all files pending organization. Each entry has:
- `id`: Unique identifier (UUID)
- `source_path`: Full path to source file
- `dest_path`: Full path to destination (includes the new filename), or `"DELETE"` for duplicates
- `confidence`: Score 0-100
- `confidence_factors`: Object with individual scoring factors
- `status`: `"pending"`, `"approved"`, `"completed"`, or `"failed"`
- `timestamp`: ISO 8601 timestamp when added
- `reasoning`: Why this destination was chosen
- `action`: (optional) `"move"` (default) or `"delete"` (for duplicates)
- `duplicate_of`: (optional) Array of paths to existing duplicate files
- `checksum`: (optional) SHA256 hash of source file (for duplicates)
- `alternatives`: (optional) Array of alternative destination options
- `new_folder`: (optional) Boolean, true when proposing to create a new folder
- `content_analysis`: (optional) Object with content analysis results

### move_history.json
Tracks all executed file move operations for undo capability. Each entry has:
- `id`: Matches file_queue.json entry
- `source_path`: Original location
- `dest_path`: New location
- `status`: `"moved"` after successful move
- `timestamp`: ISO 8601 timestamp when added to queue
- `moved_at`: ISO 8601 timestamp when move was executed

### skip_history.json
Tracks all skipped file operations. Each entry has:
- `id`: Matches file_queue.json entry
- `source_path`: Original location
- `dest_path`: Suggested destination (or `"DELETE"`)
- `status`: `"skipped"`
- `skipped_at`: ISO 8601 timestamp when skipped
- `skipped_to`: (optional) Path where file was moved when skipped (e.g., `~/Downloads/Skipped/`)

## JSON Schema Examples

### file_queue.json

```json
{
  "schema_version": "1.0",
  "last_updated": "2025-01-21T10:30:00Z",
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_path": "/Users/marklampert/Downloads/statement.pdf",
      "dest_path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_statement.pdf",
      "confidence": 95,
      "confidence_factors": {
        "similar_files_found": 30,
        "file_type_match": 20,
        "entity_keyword": 20,
        "content_match": 15,
        "naming_pattern": 10
      },
      "content_analysis": {
        "summary": "TD Canada Trust Statement for January 2024",
        "detected_entities": ["TD"],
        "detected_dates": ["2024-01-15"]
      },
      "status": "pending",
      "timestamp": "2025-01-21T10:25:00Z",
      "reasoning": "Found 5 similar TD bank statements in destination folder. PDF format matches. Date pattern consistent with existing files."
    }
  ]
}
```

### move_history.json

```json
{
  "schema_version": "1.0",
  "last_updated": "2025-01-21T10:35:00Z",
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_path": "/Users/marklampert/Downloads/statement.pdf",
      "dest_path": "/Users/marklampert/Dropbox/Filing/TD Chequing/2024-01-15_statement.pdf",
      "confidence": 95,
      "status": "moved",
      "timestamp": "2025-01-21T10:25:00Z",
      "moved_at": "2025-01-21T10:35:00Z"
    }
  ]
}
```

### skip_history.json

```json
{
  "schema_version": "1.0",
  "last_updated": "2025-01-21T10:40:00Z",
  "files": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "source_path": "/Users/marklampert/Downloads/unknown_file.pdf",
      "dest_path": "/Users/marklampert/Downloads/unknown/unknown_file.pdf",
      "confidence": 30,
      "status": "skipped",
      "timestamp": "2025-01-21T10:30:00Z",
      "skipped_at": "2025-01-21T10:40:00Z",
      "skipped_to": "/Users/marklampert/Downloads/Skipped/unknown_file.pdf"
    }
  ]
}
```
