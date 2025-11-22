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
