"""
Simple http server copied from Offensive Windows Dev Discord
"""

import http.server
import socketserver
import os

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Disposition', 'attachment; filename="payload.bin"')
        super().end_headers()

    def guess_type(self, path):
        return 'application/octet-stream'
                
    def do_GET(self):
        file_path = os.path.join(directory, 'payload.bin')
        with open(file_path, 'rb') as file:
            self.send_response(200)
            self.send_header('Content-Disposition', 'attachment; filename="payload.bin"')
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(file.read())
                                                                                                
# Set the directory where the file is located
directory = '%USERPROFILE%/payload.bin'

# Set the port for the web server
port = 4444

# Create the web server
Handler = FileHandler
httpd = socketserver.TCPServer(("", port), Handler)

# Change to the specified directory
os.chdir(directory)

# Start the web server
print(f"Server running on port {port}")
httpd.serve_forever()