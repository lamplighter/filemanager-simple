#!/usr/bin/env python3
"""Simple HTTP server for file queue viewer with API to update statuses"""

import http.server
import socketserver
import json
import os
import shutil
import tempfile
import unicodedata
from urllib.parse import parse_qs, urlparse
from datetime import datetime


def normalize_path(path: str) -> str:
    """Normalize Unicode in file path to handle macOS special characters.

    macOS can use different Unicode representations for the same character
    (e.g., narrow no-break space U+202F vs regular space). This normalizes
    paths to NFC form for consistent comparison.
    """
    return unicodedata.normalize('NFC', path)

PORT = int(os.environ.get('FILEMANAGER_PORT', 8765))
HOST = '127.0.0.1'  # Bind to localhost only for security
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# State directory can be overridden via environment variable (used by tests)

STATE_DIR = os.environ.get('FILEMANAGER_STATE_DIR', os.path.join(PROJECT_ROOT, 'state'))
QUEUE_FILE = os.path.join(STATE_DIR, 'file_queue.json')
HISTORY_FILE = os.path.join(STATE_DIR, 'move_history.json')
SKIP_HISTORY_FILE = os.path.join(STATE_DIR, 'skip_history.json')
SKIPPED_FOLDER = os.path.expanduser('~/Downloads/Skipped')


def atomic_write_json(data: dict, filepath: str) -> None:
    """Write JSON data atomically to prevent race conditions.

    Uses a temporary file and atomic rename to ensure the file is either
    fully written or not written at all, preventing data corruption when
    organize.sh and viewer_server.py write concurrently.
    """
    dir_path = os.path.dirname(filepath)
    fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2)
        os.rename(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

class ViewerRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def send_json_error(self, status_code: int, message: str):
        """Send a JSON error response instead of HTML error page."""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'success': False, 'error': message}).encode())

    def _send_bulk_error(self, error: str, processed_count: int, action: str = "move"):
        """Send error response for bulk operations that stopped on first error."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        count_key = 'moved_count' if action == 'move' else 'skipped_count'
        self.wfile.write(json.dumps({
            'success': False,
            'error': error,
            count_key: processed_count
        }).encode())

    def do_POST(self):
        """Handle POST requests to update file status"""
        if self.path == '/api/update-status':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_id = data.get('id')
                new_status = data.get('status')

                if not file_id or not new_status:
                    self.send_json_error(400, "Missing id or status")
                    return

                # Read current queue
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Find and update the file
                file_found = False
                for file in queue_data['files']:
                    if file['id'] == file_id:
                        file['status'] = new_status
                        file_found = True
                        break

                if not file_found:
                    self.send_json_error(404, "File not found")
                    return

                # Update last_updated timestamp
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write back to file atomically
                atomic_write_json(queue_data, QUEUE_FILE)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        elif self.path == '/api/move-file':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_id = data.get('id')

                if not file_id:
                    self.send_json_error(400, "Missing file id")
                    return

                # Read current queue
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Find the file in queue
                file_entry = None
                file_index = None
                for i, file in enumerate(queue_data['files']):
                    if file['id'] == file_id:
                        file_entry = file
                        file_index = i
                        break

                if not file_entry:
                    self.send_json_error(404, "File not found in queue")
                    return

                source_path = normalize_path(os.path.expanduser(file_entry['source_path']))
                dest_path = os.path.expanduser(file_entry['dest_path'])
                action = file_entry.get('action', 'move')

                # Check if source file exists
                if not os.path.exists(source_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': f'Source file not found: {source_path}'
                    }).encode())
                    return

                # Handle DELETE action (duplicates or empty folders)
                if dest_path == "DELETE" or action == "delete":
                    try:
                        if os.path.isdir(source_path):
                            shutil.rmtree(source_path)
                            message = f"Deleted directory: {os.path.basename(source_path)}"
                        else:
                            os.remove(source_path)
                            message = f"Deleted file: {os.path.basename(source_path)}"
                    except Exception as e:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': False,
                            'error': f'Failed to delete: {str(e)}'
                        }).encode())
                        return
                else:
                    # Normal move operation
                    # Create destination directory if it doesn't exist
                    dest_dir = os.path.dirname(dest_path)
                    os.makedirs(dest_dir, exist_ok=True)

                    # Check if destination file already exists
                    if os.path.exists(dest_path):
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': False,
                            'error': f'Destination file already exists: {dest_path}'
                        }).encode())
                        return

                    # Move the file
                    try:
                        shutil.move(source_path, dest_path)
                        message = f"Moved {os.path.basename(source_path)} to {dest_path}"
                    except Exception as e:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': False,
                            'error': f'Failed to move file: {str(e)}'
                        }).encode())
                        return

                # Update file entry with moved status and timestamp
                file_entry['status'] = 'moved'
                file_entry['moved_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Add to move history
                try:
                    with open(HISTORY_FILE, 'r') as f:
                        history_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    history_data = {
                        'schema_version': '1.0',
                        'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'files': []
                    }

                history_data['files'].append(file_entry)
                history_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write history file atomically
                atomic_write_json(history_data, HISTORY_FILE)

                # Remove file from queue
                queue_data['files'].pop(file_index)
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write back to queue file atomically
                atomic_write_json(queue_data, QUEUE_FILE)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': message
                }).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        elif self.path == '/api/update-queue':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                files = data.get('files')

                if files is None:
                    self.send_json_error(400, "Missing files array")
                    return

                # Read current queue to preserve schema
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Update files array
                queue_data['files'] = files
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write back to file atomically
                atomic_write_json(queue_data, QUEUE_FILE)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        elif self.path == '/api/skip-file':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_id = data.get('id')

                if not file_id:
                    self.send_json_error(400, "Missing file id")
                    return

                # Read current queue
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Find the file in queue
                file_entry = None
                file_index = None
                for i, file in enumerate(queue_data['files']):
                    if file['id'] == file_id:
                        file_entry = file
                        file_index = i
                        break

                if not file_entry:
                    self.send_json_error(404, "File not found in queue")
                    return

                # Move file to Skipped folder
                source_path = normalize_path(os.path.expanduser(file_entry['source_path']))
                os.makedirs(SKIPPED_FOLDER, exist_ok=True)
                skipped_path = os.path.join(SKIPPED_FOLDER, os.path.basename(source_path))
                if os.path.exists(source_path):
                    shutil.move(source_path, skipped_path)
                    file_entry['skipped_to'] = skipped_path
                else:
                    file_entry['skipped_to'] = None  # File was already gone

                # Update file entry with skipped status and timestamp
                file_entry['status'] = 'skipped'
                file_entry['skipped_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Add to skip history
                try:
                    with open(SKIP_HISTORY_FILE, 'r') as f:
                        skip_history_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    skip_history_data = {
                        'schema_version': '1.0',
                        'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'files': []
                    }

                skip_history_data['files'].append(file_entry)
                skip_history_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write skip history file atomically
                atomic_write_json(skip_history_data, SKIP_HISTORY_FILE)

                # Remove file from queue
                queue_data['files'].pop(file_index)
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                # Write back to queue file atomically
                atomic_write_json(queue_data, QUEUE_FILE)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': f"Skipped {os.path.basename(file_entry['source_path'])}"
                }).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        elif self.path == '/api/bulk-move':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_ids = data.get('ids', [])

                if not file_ids:
                    self.send_json_error(400, "Missing file ids")
                    return

                # Read current queue
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Read/initialize history
                try:
                    with open(HISTORY_FILE, 'r') as f:
                        history_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    history_data = {
                        'schema_version': '1.0',
                        'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'files': []
                    }

                moved_count = 0
                processed_ids = []

                for file_id in file_ids:
                    # Find file in queue
                    file_entry = None
                    for f in queue_data['files']:
                        if f['id'] == file_id:
                            file_entry = f
                            break

                    if not file_entry:
                        # Stop on first error
                        self._send_bulk_error(f"File not found in queue: {file_id[:8]}...", moved_count)
                        return

                    source_path = normalize_path(os.path.expanduser(file_entry['source_path']))
                    dest_path = os.path.expanduser(file_entry['dest_path'])
                    action = file_entry.get('action', 'move')

                    if not os.path.exists(source_path):
                        self._send_bulk_error(
                            f"Source file not found: {os.path.basename(source_path)}",
                            moved_count
                        )
                        return

                    try:
                        if dest_path == "DELETE" or action == "delete":
                            os.remove(source_path)
                        else:
                            dest_dir = os.path.dirname(dest_path)
                            os.makedirs(dest_dir, exist_ok=True)
                            if os.path.exists(dest_path):
                                self._send_bulk_error(
                                    f"Destination already exists: {os.path.basename(dest_path)}",
                                    moved_count
                                )
                                return
                            shutil.move(source_path, dest_path)

                        # Mark as moved
                        file_entry['status'] = 'moved'
                        file_entry['moved_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                        history_data['files'].append(file_entry.copy())
                        processed_ids.append(file_id)
                        moved_count += 1

                    except Exception as e:
                        self._send_bulk_error(
                            f"Failed to move {os.path.basename(source_path)}: {str(e)}",
                            moved_count
                        )
                        return

                # Remove processed files from queue
                queue_data['files'] = [f for f in queue_data['files'] if f['id'] not in processed_ids]
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                history_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                atomic_write_json(queue_data, QUEUE_FILE)
                atomic_write_json(history_data, HISTORY_FILE)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': f"Successfully moved {moved_count} file{'s' if moved_count != 1 else ''}",
                    'moved_count': moved_count
                }).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        elif self.path == '/api/bulk-skip':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_ids = data.get('ids', [])

                if not file_ids:
                    self.send_json_error(400, "Missing file ids")
                    return

                # Read current queue
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)

                # Read/initialize skip history
                try:
                    with open(SKIP_HISTORY_FILE, 'r') as f:
                        skip_history_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    skip_history_data = {
                        'schema_version': '1.0',
                        'last_updated': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'files': []
                    }

                skipped_count = 0
                processed_ids = []

                for file_id in file_ids:
                    # Find file in queue
                    file_entry = None
                    for f in queue_data['files']:
                        if f['id'] == file_id:
                            file_entry = f
                            break

                    if not file_entry:
                        # Stop on first error
                        self._send_bulk_error(f"File not found in queue: {file_id[:8]}...", skipped_count, action="skip")
                        return

                    # Move file to Skipped folder
                    source_path = normalize_path(os.path.expanduser(file_entry['source_path']))
                    os.makedirs(SKIPPED_FOLDER, exist_ok=True)
                    skipped_path = os.path.join(SKIPPED_FOLDER, os.path.basename(source_path))
                    if os.path.exists(source_path):
                        shutil.move(source_path, skipped_path)
                        file_entry['skipped_to'] = skipped_path
                    else:
                        file_entry['skipped_to'] = None  # File was already gone

                    # Mark as skipped
                    file_entry['status'] = 'skipped'
                    file_entry['skipped_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    skip_history_data['files'].append(file_entry.copy())
                    processed_ids.append(file_id)
                    skipped_count += 1

                # Remove processed files from queue
                queue_data['files'] = [f for f in queue_data['files'] if f['id'] not in processed_ids]
                queue_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                skip_history_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

                atomic_write_json(queue_data, QUEUE_FILE)
                atomic_write_json(skip_history_data, SKIP_HISTORY_FILE)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': f"Successfully skipped {skipped_count} file{'s' if skipped_count != 1 else ''}",
                    'skipped_count': skipped_count
                }).encode())

            except Exception as e:
                self.send_json_error(500, str(e))

        else:
            self.send_json_error(404, "Unknown API endpoint")

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)

        # Serve state files from STATE_DIR (supports test isolation)
        if parsed_url.path.startswith('/state/') and parsed_url.path.endswith('.json'):
            filename = os.path.basename(parsed_url.path)
            file_path = os.path.join(STATE_DIR, filename)

            if not os.path.exists(file_path):
                self.send_json_error(404, f"State file not found: {filename}")
                return

            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode())

            except Exception as e:
                self.send_json_error(500, str(e))
            return

        elif parsed_url.path == '/api/list-directory':
            # Extract directory path from query parameter
            query_params = parse_qs(parsed_url.query)
            dir_path = query_params.get('path', [None])[0]

            if not dir_path:
                self.send_json_error(400, "Missing path parameter")
                return

            # Expand ~ to user home directory
            dir_path = os.path.expanduser(dir_path)

            try:
                # Check if directory exists
                if not os.path.exists(dir_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': 'Directory does not exist',
                        'directory': dir_path,
                        'files': []
                    }).encode())
                    return

                if not os.path.isdir(dir_path):
                    self.send_json_error(400, "Path is not a directory")
                    return

                # List all files in directory
                files = []
                for entry in os.scandir(dir_path):
                    if entry.is_file():
                        stat = entry.stat()
                        files.append({
                            'name': entry.name,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })

                # Sort by modified date (newest first)
                files.sort(key=lambda x: x['modified'], reverse=True)

                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'directory': dir_path,
                    'files': files,
                    'total_count': len(files)
                }).encode())

            except PermissionError:
                self.send_json_error(403, "Permission denied")
            except Exception as e:
                self.send_json_error(500, str(e))

        elif parsed_url.path == '/api/file-info':
            # Get file metadata (size, etc.)
            query_params = parse_qs(parsed_url.query)
            file_path = query_params.get('path', [None])[0]

            if not file_path:
                self.send_json_error(400, "Missing path parameter")
                return

            file_path = os.path.expanduser(file_path)

            if not os.path.exists(file_path):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'File not found',
                    'size': None
                }).encode())
                return

            try:
                stat = os.stat(file_path)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                }).encode())
            except Exception as e:
                self.send_json_error(500, str(e))

        elif parsed_url.path == '/api/file-preview':
            # Serve a local file for preview (PDF, image, etc.)
            query_params = parse_qs(parsed_url.query)
            file_path = query_params.get('path', [None])[0]

            if not file_path:
                self.send_json_error(400, "Missing path parameter")
                return

            # Expand ~ to user home directory
            file_path = os.path.expanduser(file_path)

            # Security: Validate path exists and is a file
            if not os.path.exists(file_path):
                self.send_json_error(404, "File not found")
                return

            if not os.path.isfile(file_path):
                self.send_json_error(400, "Path is not a file")
                return

            try:
                # Determine content type based on file extension
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'

                # Read and serve the file
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-Length', len(file_content))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(file_content)

            except PermissionError:
                self.send_json_error(403, "Permission denied")
            except Exception as e:
                self.send_json_error(500, str(e))

        else:
            # Delegate to parent class for serving static files
            super().do_GET()

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

class ReusableTCPServer(socketserver.TCPServer):
    """TCPServer with SO_REUSEADDR for quick restarts during testing."""
    allow_reuse_address = True


if __name__ == '__main__':
    with ReusableTCPServer((HOST, PORT), ViewerRequestHandler) as httpd:
        print(f"Server running at http://{HOST}:{PORT}/")
        print(f"Open http://localhost:{PORT}/viewer.html to view the queue")
        print("Press Ctrl+C to stop")
        print(f"(Bound to {HOST} only for security)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
