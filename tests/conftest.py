"""Shared fixtures for file organizer tests."""

import pytest
import subprocess
import time
import os
import json
import shutil
from pathlib import Path
from playwright.sync_api import Page, Browser

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
QUEUE_FILE = STATE_DIR / "file_queue.json"
HISTORY_FILE = STATE_DIR / "move_history.json"
SKIP_HISTORY_FILE = STATE_DIR / "skip_history.json"
SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "viewer_server.py"
SERVER_PORT = 8765
SERVER_URL = f"http://localhost:{SERVER_PORT}"


@pytest.fixture(scope="session")
def server():
    """Start the viewer server for the test session."""
    # Check if server is already running
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', SERVER_PORT))
    sock.close()

    if result == 0:
        # Server already running, just use it
        yield {"url": SERVER_URL, "port": SERVER_PORT, "process": None}
        return

    # Start the server
    proc = subprocess.Popen(
        ["python3", str(SERVER_SCRIPT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(PROJECT_ROOT),
    )
    time.sleep(2)  # Wait for server to start

    yield {"process": proc, "url": SERVER_URL, "port": SERVER_PORT}

    # Cleanup
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def backup_state():
    """Backup and restore state files around each test."""
    backups = {}

    # Backup existing state files
    for file in [QUEUE_FILE, HISTORY_FILE, SKIP_HISTORY_FILE]:
        if file.exists():
            backups[file] = file.read_text()

    yield

    # Restore originals
    for file, content in backups.items():
        file.write_text(content)

    # Remove files that didn't exist before
    for file in [QUEUE_FILE, HISTORY_FILE, SKIP_HISTORY_FILE]:
        if file not in backups and file.exists():
            file.unlink()


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory structure for file operations."""
    source_dir = tmp_path / "source"
    dest_dir = tmp_path / "dest"
    source_dir.mkdir()
    dest_dir.mkdir()

    return {"source": source_dir, "dest": dest_dir, "root": tmp_path}


@pytest.fixture
def sample_pdf(temp_test_dir):
    """Create a sample PDF file for testing."""
    # Minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
168
%%EOF"""
    pdf_path = temp_test_dir["source"] / "test_document.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_txt(temp_test_dir):
    """Create a sample text file for testing."""
    txt_path = temp_test_dir["source"] / "test_document.txt"
    txt_path.write_text("Sample test content for file operations.")
    return txt_path


@pytest.fixture
def queue_file():
    """Get the path to the queue file."""
    return QUEUE_FILE


@pytest.fixture
def history_file():
    """Get the path to the history file."""
    return HISTORY_FILE


@pytest.fixture
def skip_history_file():
    """Get the path to the skip history file."""
    return SKIP_HISTORY_FILE


@pytest.fixture
def write_queue(backup_state, queue_file, history_file, skip_history_file):
    """Factory fixture to write test queue data.

    Also clears history files since the viewer loads both queue AND history.
    """
    def _write_queue(queue_data: dict):
        # Write the queue file
        queue_file.write_text(json.dumps(queue_data, indent=2))
        # Clear history files so viewer only shows queue data
        history_file.write_text(json.dumps({"files": []}, indent=2))
        skip_history_file.write_text(json.dumps({"files": []}, indent=2))
    return _write_queue


@pytest.fixture
def read_queue(queue_file):
    """Factory fixture to read current queue data."""
    def _read_queue() -> dict:
        if queue_file.exists():
            return json.loads(queue_file.read_text())
        return {"schema_version": "1.0", "last_updated": "", "files": []}
    return _read_queue


@pytest.fixture
def read_history(history_file):
    """Factory fixture to read move history."""
    def _read_history() -> dict:
        if history_file.exists():
            return json.loads(history_file.read_text())
        return {"files": []}
    return _read_history


@pytest.fixture
def read_skip_history(skip_history_file):
    """Factory fixture to read skip history."""
    def _read_skip_history() -> dict:
        if skip_history_file.exists():
            return json.loads(skip_history_file.read_text())
        return {"files": []}
    return _read_skip_history


@pytest.fixture
def viewer_url(server):
    """Get the viewer URL."""
    return f"{server['url']}/viewer.html"
