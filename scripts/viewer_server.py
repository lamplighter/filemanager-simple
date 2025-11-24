#!/usr/bin/env python3
"""Simple HTTP server for file queue viewer with API to update statuses"""

import http.server
import socketserver
import json
import os
import shutil
import tempfile
from urllib.parse import parse_qs, urlparse
from datetime import datetime

PORT = 8765
HOST = '127.0.0.1'  # Bind to localhost only for security
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_FILE = os.path.join(PROJECT_ROOT, 'state', 'file_queue.json')
HISTORY_FILE = os.path.join(PROJECT_ROOT, 'state', 'move_history.json')


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
                    self.send_error(400, "Missing id or status")
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
                    self.send_error(404, "File not found")
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
                self.send_error(500, str(e))

        elif self.path == '/api/move-file':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                file_id = data.get('id')

                if not file_id:
                    self.send_error(400, "Missing file id")
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
                    self.send_error(404, "File not found in queue")
                    return

                source_path = os.path.expanduser(file_entry['source_path'])
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

                # Handle DELETE action (duplicates)
                if dest_path == "DELETE" or action == "delete":
                    try:
                        os.remove(source_path)
                        message = f"Deleted duplicate file: {os.path.basename(source_path)}"
                    except Exception as e:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'success': False,
                            'error': f'Failed to delete file: {str(e)}'
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
                self.send_error(500, str(e))

        elif self.path == '/api/update-queue':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                files = data.get('files')

                if files is None:
                    self.send_error(400, "Missing files array")
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
                self.send_error(500, str(e))

        else:
            self.send_error(404)

    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)

        if parsed_url.path == '/api/list-directory':
            # Extract directory path from query parameter
            query_params = parse_qs(parsed_url.query)
            dir_path = query_params.get('path', [None])[0]

            if not dir_path:
                self.send_error(400, "Missing path parameter")
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
                    self.send_error(400, "Path is not a directory")
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
                self.send_error(403, "Permission denied")
            except Exception as e:
                self.send_error(500, str(e))

        elif parsed_url.path == '/api/file-preview':
            # Serve a local file for preview (PDF, image, etc.)
            query_params = parse_qs(parsed_url.query)
            file_path = query_params.get('path', [None])[0]

            if not file_path:
                self.send_error(400, "Missing path parameter")
                return

            # Expand ~ to user home directory
            file_path = os.path.expanduser(file_path)

            # Security: Validate path exists and is a file
            if not os.path.exists(file_path):
                self.send_error(404, "File not found")
                return

            if not os.path.isfile(file_path):
                self.send_error(400, "Path is not a file")
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
                self.send_error(403, "Permission denied")
            except Exception as e:
                self.send_error(500, str(e))

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

if __name__ == '__main__':
    with socketserver.TCPServer((HOST, PORT), ViewerRequestHandler) as httpd:
        print(f"Server running at http://{HOST}:{PORT}/")
        print(f"Open http://localhost:{PORT}/viewer.html to view the queue")
        print("Press Ctrl+C to stop")
        print(f"(Bound to {HOST} only for security)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
