# State Directory

This directory contains JSON files that track the file organization system's state.

## Files

### file_queue.json
Tracks all files pending organization. Each entry has:
- `id`: Unique identifier (UUID)
- `source_path`: Full path to source file
- `dest_path`: Full path to destination
- `new_filename`: New filename to apply
- `confidence`: Score 0-100
- `confidence_factors`: Object with individual scoring factors
- `status`: "pending", "approved", "executed", or "rejected"
- `timestamp`: ISO 8601 timestamp when added
- `reasoning`: Why this destination was chosen

### history.json
Tracks all executed file operations for undo capability. Each operation has:
- `id`: Matches file_queue.json entry
- `source_path`: Original location
- `dest_path`: New location
- `executed_at`: ISO 8601 timestamp
- `hash_before`: SHA256 hash before move
- `hash_after`: SHA256 hash after move
- `can_undo`: Boolean (false if source file was modified/deleted)

## JSON Schema Example

```json
{
  "schema_version": "1.0",
  "last_updated": "2025-01-21T10:30:00Z",
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source_path": "/Users/mark/Downloads/statement.pdf",
      "dest_path": "/Users/mark/Dropbox/Filing/TD Chequing/2024-01-15_statement.pdf",
      "confidence": 95,
      "confidence_factors": {
        "similar_files_found": 30,
        "file_type_match": 20,
        "entity_keyword": 20,
        "content_match": 15,
        "naming_pattern": 10
      },
      "status": "approved",
      "timestamp": "2025-01-21T10:25:00Z",
      "reasoning": "Found 5 similar TD bank statements in destination folder. PDF format matches. Date pattern consistent with existing files."
    }
  ]
}
```
