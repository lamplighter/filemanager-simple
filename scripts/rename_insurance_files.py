#!/usr/bin/env python3
"""
Rename Insurance Files Script

Scans TD Insurance folders for machine-generated filenames and suggests
descriptive renames based on PDF content analysis.

Usage:
    python scripts/rename_insurance_files.py [--dry-run] [--output FILE]

Options:
    --dry-run    Show rename suggestions without creating queue file
    --output     Specify output JSON file (default: state/rename_queue.json)
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Optional, Tuple
import PyPDF2


# Property address mappings (from naming-conventions.md)
PROPERTY_MAPPINGS = {
    "1035 FIRE ROUTE 20G": "Cottage",
    "1035 Fire Route 20G": "Cottage",
    "40 GIBSON AVE": "40 Gibson",
    "40 Gibson Ave": "40 Gibson",
    "319 CARLAW AVE UNIT 711": "Carlaw",
    "319 Carlaw Ave Unit 711": "Carlaw",
}

# Document type patterns to extract from PDF
DOCUMENT_TYPE_PATTERNS = {
    r"RENEWAL": "Renewal",
    r"POLICY\s*CHANGE": "Policy Change",  # Allow optional space
    r"COVERAGE\s*INCREASE": "Coverage Increase",
    r"PINK\s*CARD": "Pink Card",
    r"ISSUANCE": "Issuance",
    r"SERVICING\s*LETTER": "Servicing Letter",  # Allow optional space
    r"POLICY\s*APPLICATION": "Policy Application",
}

# Machine-generated filename patterns to identify files needing rename
MACHINE_GENERATED_PATTERNS = [
    r"^\d{11}_\d{4}-\d{2}-\d{2}_",  # 00134652057_2023-11-13_
    r"_\d{13,}\.pdf$",  # _0000252724963.pdf
    r"_[A-Z]\d{12}\.pdf$",  # _D000043200132.pdf
]


def is_machine_generated(filename: str) -> bool:
    """Check if filename matches machine-generated patterns."""
    for pattern in MACHINE_GENERATED_PATTERNS:
        if re.search(pattern, filename):
            return True
    return False


def extract_pdf_text(pdf_path: Path, max_pages: int = 3) -> str:
    """Extract text from first few pages of PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(min(max_pages, len(reader.pages))):
                text += reader.pages[page_num].extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""


def identify_document_type(text: str, filename: str = "") -> Optional[str]:
    """Identify document type from PDF text or filename."""
    # First try to extract from PDF text content
    text_upper = text.upper()
    for pattern, doc_type in DOCUMENT_TYPE_PATTERNS.items():
        if re.search(pattern, text_upper):
            return doc_type

    # Fallback: try to extract from filename (for machine-generated names)
    filename_upper = filename.upper()
    for pattern, doc_type in DOCUMENT_TYPE_PATTERNS.items():
        if re.search(pattern, filename_upper):
            return doc_type

    return None


def identify_properties(text: str) -> List[str]:
    """Identify properties mentioned in PDF text."""
    properties = []
    for address, short_name in PROPERTY_MAPPINGS.items():
        if address.upper() in text.upper():
            if short_name not in properties:
                properties.append(short_name)
    return properties


def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract YYYY-MM-DD date from existing filename."""
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if match:
        return match.group(0)
    return None


def extract_date_from_pdf(text: str) -> Optional[str]:
    """Try to extract date from PDF content (fallback)."""
    # Look for date patterns in the text
    date_patterns = [
        r'Date:\s*(\w+ \d{1,2}, \d{4})',
        r'Effective Date:\s*(\w+ \d{1,2}, \d{4})',
        r'Statement Date:\s*(\w+ \d{1,2}, \d{4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            # Would need to parse the date string to convert to YYYY-MM-DD
            # For now, just return None and rely on filename date
            pass
    return None


def generate_new_filename(
    original_path: Path,
    doc_type: Optional[str],
    properties: List[str],
    date: str
) -> str:
    """Generate new filename following naming conventions."""
    parts = [date]

    if doc_type:
        parts.append(doc_type)
    else:
        # Fallback to generic name if can't determine type
        parts.append("Document")

    if properties:
        # Join multiple properties with +
        property_str = " + ".join(properties)
        parts.append(f"- {property_str}")

    filename = " ".join(parts) + ".pdf"
    return filename


def analyze_file(file_path: Path) -> Optional[Dict]:
    """Analyze a single insurance file and generate rename suggestion."""
    filename = file_path.name

    # Skip if not machine-generated
    if not is_machine_generated(filename):
        return None

    # Skip if file is empty
    if file_path.stat().st_size == 0:
        print(f"Skipping empty file: {filename}")
        return None

    # Extract date from filename
    date = extract_date_from_filename(filename)
    if not date:
        print(f"Warning: Could not extract date from {filename}")
        return None

    # Read PDF content
    text = extract_pdf_text(file_path)
    if not text:
        print(f"Warning: Could not extract text from {filename}")
        return None

    # Identify document type and properties
    doc_type = identify_document_type(text, filename)
    properties = identify_properties(text)

    if not doc_type and not properties:
        print(f"Warning: Could not identify doc type or properties for {filename}")
        # Still generate a basic rename

    # Generate new filename
    new_filename = generate_new_filename(file_path, doc_type, properties, date)
    new_path = file_path.parent / new_filename

    # Calculate confidence based on what we extracted
    confidence = 45  # Base confidence
    if doc_type:
        confidence += 25
    if properties:
        confidence += 20 if len(properties) == 1 else 15
    if text:
        confidence += 10  # Successfully read content

    # Cap confidence at 100%
    confidence = min(confidence, 100)

    # Build confidence factors
    confidence_factors = {}
    if doc_type:
        confidence_factors["document_type_identified"] = 25
    if properties:
        confidence_factors["property_identified"] = 20 if len(properties) == 1 else 15
    if text:
        confidence_factors["content_readable"] = 10

    # Build reasoning
    reasoning_parts = []
    if doc_type:
        reasoning_parts.append(f"Identified as {doc_type} document")
    if properties:
        reasoning_parts.append(f"Found property reference: {', '.join(properties)}")
    if not doc_type:
        reasoning_parts.append("Could not identify specific document type from content")

    reasoning = ". ".join(reasoning_parts) + "."

    return {
        "source_path": str(file_path.absolute()),
        "dest_path": str(new_path.absolute()),
        "confidence": confidence,
        "confidence_factors": confidence_factors,
        "reasoning": reasoning,
        "action": "rename",
        "status": "pending",
        "timestamp": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
    }


def scan_insurance_folders(base_path: Path) -> List[Dict]:
    """Scan TD Insurance folders for files needing rename."""
    suggestions = []

    insurance_base = base_path / "Dropbox" / "Filing"

    # Find all TD Insurance folders
    insurance_folders = []
    for item in insurance_base.iterdir():
        if item.is_dir() and "TD Insurance" in item.name:
            insurance_folders.append(item)

    print(f"Found {len(insurance_folders)} TD Insurance folders")

    # Scan each folder for PDF files (including subfolders)
    for folder in insurance_folders:
        print(f"\nScanning: {folder.name}")
        pdf_files = list(folder.rglob("*.pdf"))  # Recursive search
        print(f"  Found {len(pdf_files)} PDF files (including subfolders)")

        for pdf_file in pdf_files:
            suggestion = analyze_file(pdf_file)
            if suggestion:
                suggestions.append(suggestion)
                relative_path = pdf_file.relative_to(folder)
                print(f"  ✓ {relative_path} → {Path(suggestion['dest_path']).name}")

    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Rename insurance files with descriptive names")
    parser.add_argument("--dry-run", action="store_true", help="Show suggestions without saving")
    parser.add_argument("--output", default="state/rename_queue.json", help="Output JSON file")
    args = parser.parse_args()

    # Get base path - expand ~ to get home directory
    base_path = Path.home()  # /Users/marklampert/

    # Get project root (script is in project_root/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    print(f"Scanning insurance folders in {base_path / 'Dropbox' / 'Filing'}")

    suggestions = scan_insurance_folders(base_path)

    print(f"\n{'='*60}")
    print(f"Found {len(suggestions)} files to rename")

    if not suggestions:
        print("No files need renaming.")
        return

    # Create output structure
    output = {
        "schema_version": "1.0",
        "last_updated": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        "files": suggestions
    }

    if args.dry_run:
        print("\nDRY RUN - Suggestions:")
        print(json.dumps(output, indent=2))
    else:
        output_path = project_root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output, indent=2, fp=f)

        print(f"\nSaved {len(suggestions)} rename suggestions to {output_path}")
        print("\nNext steps:")
        print("1. Review suggestions in the rename queue file")
        print("2. Use /view or a custom viewer to approve/reject renames")


if __name__ == "__main__":
    main()
