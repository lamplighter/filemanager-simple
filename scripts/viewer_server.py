#!/usr/bin/env python3
"""Simple HTTP server for file queue viewer with API to update statuses"""

import http.server
import socketserver
import json
import os
from urllib.parse import parse_qs, urlparse
from datetime import datetime

PORT = 8765
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_FILE = os.path.join(PROJECT_ROOT, 'state', 'file_queue.json')

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

                # Write back to file
                with open(QUEUE_FILE, 'w') as f:
                    json.dump(queue_data, f, indent=2)

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
    with socketserver.TCPServer(("", PORT), ViewerRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/viewer.html to view the queue")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
