import os
import shutil
import json
import pytest
import requests
import time
import subprocess
from pathlib import Path

# Configuration
PORT = 8766  # Use a different port for testing
HOST = "127.0.0.1"
BASE_URL = f"http://{HOST}:{PORT}"
TEST_DIR = Path(__file__).parent / "temp_delete_test"
STATE_DIR = TEST_DIR / "state"
QUEUE_FILE = STATE_DIR / "file_queue.json"
HISTORY_FILE = STATE_DIR / "move_history.json"

@pytest.fixture(scope="module")
def server():
    """Start the viewer server for testing."""
    # Create test directories
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True)
    STATE_DIR.mkdir()
    
    # Initialize state files
    with open(QUEUE_FILE, 'w') as f:
        json.dump({"schema_version": "1.0", "files": [], "last_updated": ""}, f)
    with open(HISTORY_FILE, 'w') as f:
        json.dump({"schema_version": "1.0", "files": [], "last_updated": ""}, f)

    # Start server
    env = os.environ.copy()
    env["FILEMANAGER_PORT"] = str(PORT)
    env["FILEMANAGER_STATE_DIR"] = str(STATE_DIR)
    
    server_script = Path(__file__).parent.parent / "scripts" / "viewer_server.py"
    process = subprocess.Popen(
        ["python3", str(server_script)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(2)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.wait()
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def test_delete_file(server):
    """Test deleting a regular file."""
    # Create a dummy file
    test_file = TEST_DIR / "test_file.txt"
    test_file.touch()
    
    # Add to queue
    file_id = "test-file-1"
    queue_data = {
        "schema_version": "1.0",
        "files": [{
            "id": file_id,
            "source_path": str(test_file),
            "dest_path": "DELETE",
            "action": "delete",
            "status": "pending"
        }]
    }
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue_data, f)
        
    # Call API
    response = requests.post(f"{BASE_URL}/api/move-file", json={"id": file_id})
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "Deleted file" in result["message"]
    
    # Verify file is gone
    assert not test_file.exists()

def test_delete_directory(server):
    """Test deleting a directory (empty or not)."""
    # Create a dummy directory with a file inside
    test_dir = TEST_DIR / "test_dir"
    test_dir.mkdir()
    (test_dir / "inner.txt").touch()
    
    # Add to queue
    file_id = "test-dir-1"
    queue_data = {
        "schema_version": "1.0",
        "files": [{
            "id": file_id,
            "source_path": str(test_dir),
            "dest_path": "DELETE",
            "action": "delete",
            "status": "pending"
        }]
    }
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue_data, f)
        
    # Call API
    response = requests.post(f"{BASE_URL}/api/move-file", json={"id": file_id})
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "Deleted directory" in result["message"]
    
    # Verify directory is gone
    assert not test_dir.exists()
