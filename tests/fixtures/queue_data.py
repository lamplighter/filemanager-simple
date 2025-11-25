"""Factory functions for creating test queue data."""

import uuid
from datetime import datetime, timezone


def make_queue_entry(
    source_path: str,
    dest_path: str,
    confidence: int = 85,
    status: str = "pending",
    **kwargs
) -> dict:
    """Factory function for queue entries.

    Args:
        source_path: Full path to source file
        dest_path: Full path to destination
        confidence: Confidence score 0-100
        status: pending, approved, rejected, moved, failed
        **kwargs: Additional fields (reasoning, confidence_factors, etc.)

    Returns:
        Dict representing a queue entry
    """
    return {
        "id": kwargs.get("id", str(uuid.uuid4())),
        "source_path": source_path,
        "dest_path": dest_path,
        "confidence": confidence,
        "confidence_factors": kwargs.get("confidence_factors", {
            "similar_files_found": 30,
            "file_type_match": 20,
            "entity_keyword": 20,
            "content_match": 15,
        }),
        "status": status,
        "timestamp": kwargs.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "reasoning": kwargs.get("reasoning", "Test entry for automated testing."),
        **{k: v for k, v in kwargs.items()
           if k not in ["id", "confidence_factors", "timestamp", "reasoning"]},
    }


def make_duplicate_entry(
    source_path: str,
    duplicate_of: list[str],
    **kwargs
) -> dict:
    """Factory for duplicate file entries.

    Args:
        source_path: Path to the duplicate file
        duplicate_of: List of paths to existing files
        **kwargs: Additional fields

    Returns:
        Dict representing a duplicate entry
    """
    entry = make_queue_entry(
        source_path=source_path,
        dest_path="DELETE",
        confidence=100,
        **kwargs
    )
    entry.update({
        "duplicate_of": duplicate_of,
        "checksum": kwargs.get("checksum", "abc123def456fake789checksum"),
        "action": "delete",
    })
    return entry


def make_new_folder_entry(
    source_path: str,
    dest_path: str,
    **kwargs
) -> dict:
    """Factory for new folder proposal entries.

    Args:
        source_path: Path to source file
        dest_path: Path including the new folder
        **kwargs: Additional fields

    Returns:
        Dict representing a new folder entry
    """
    entry = make_queue_entry(source_path, dest_path, **kwargs)
    entry["new_folder"] = True
    return entry


def make_entry_with_alternatives(
    source_path: str,
    dest_path: str,
    alternatives: list[dict],
    **kwargs
) -> dict:
    """Factory for entries with alternative destinations.

    Args:
        source_path: Path to source file
        dest_path: Primary destination path
        alternatives: List of alternative destination dicts
        **kwargs: Additional fields

    Returns:
        Dict representing an entry with alternatives
    """
    entry = make_queue_entry(source_path, dest_path, **kwargs)
    entry["alternatives"] = alternatives
    return entry


def make_queue(files: list[dict]) -> dict:
    """Create a complete queue JSON structure.

    Args:
        files: List of queue entry dicts

    Returns:
        Complete queue dict with schema version and metadata
    """
    return {
        "schema_version": "1.0",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }


def make_empty_queue() -> dict:
    """Create an empty queue."""
    return make_queue([])


def make_sample_queue(source_dir: str, dest_dir: str) -> dict:
    """Create a sample queue with various file types.

    Args:
        source_dir: Base source directory path
        dest_dir: Base destination directory path

    Returns:
        Queue with sample entries
    """
    files = [
        make_queue_entry(
            source_path=f"{source_dir}/invoice.pdf",
            dest_path=f"{dest_dir}/Invoices/2024-01-15_invoice.pdf",
            confidence=95,
            reasoning="Found similar invoices in Invoices folder."
        ),
        make_queue_entry(
            source_path=f"{source_dir}/statement.pdf",
            dest_path=f"{dest_dir}/Bank/2024-01-20_statement.pdf",
            confidence=75,
            reasoning="Bank statement based on filename pattern."
        ),
        make_queue_entry(
            source_path=f"{source_dir}/unknown.pdf",
            dest_path=f"{dest_dir}/Unknown/unknown.pdf",
            confidence=35,
            reasoning="Unable to categorize this file."
        ),
    ]
    return make_queue(files)
