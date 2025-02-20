from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
import threading
import logger
import requests
import socket
import os


log = logger.Logger(verbosity="debug")


class HTTPSession():
    def __init__(self, id, uid, client_address, client_username, secure=False):
        self.id = id
        self.uid = uid
        self.client_address = client_address
        self.client_username = client_username
        self.secure = secure


class HTTPClient():
    def __init__(self, id, client_address, commands_queue=[]):
        self.id = id
        self.client_address = client_address
        self.commands_queue = commands_queue
        self.session = HTTPSession(id, "12dfdqr2zf4tv90892", client_address, "tony")




class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)


    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data)
            response = self.handle_command(data)

        except json.JSONDecodeError:
            response = {"status": "error", "message": "Invalid JSON format"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    
    def handle_command(self, data):
        command = data.get("command")
        if command == "ping":
            return {"status":"ok", "message":"pong"}
        
        elif command == "info":
            return {"status":"ok", "message":"HTTP/HTTPS Listener Active"}

        else:
            return {"status": "error", "message": "Unknown command"}
        

class HTTPServerWrapper:
    def __init__(self, ip, port, use_https=False, certfile=None, keyfile=None):
        self.ip = ip
        self.port = port
        self.use_https = use_https
        self.certfile = certfile
        self.keyfile = keyfile
        self.running = False
        self.server = HTTPServer((ip, port), HTTPHandler)

        if use_https and certfile and keyfile:
            self.server.socket = ssl.SSLContext.wrap_socket(
                self.server.socket,
                keyfile=keyfile,
                certfile=certfile,
                server_side=True
            )

        log.info(f"HTTPS server created for {ip}:{port}")


    def start(self):
        self.server.serve_forever()
        #thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        #thread.daemon = True # Ensures threads exit when main program ends
        #thread.start()
        #return thread
    

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        log.info("HTTP Server stopped")

"""
class HTTPClient:
    def __init__(self, server_ip, server_port, use_https=False):
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol = "https" if use_https else "http"


    def send_command(self, command):
        url = f"{self.protocol}://{self.server_ip}:{self.server_port}"
        try:
            response = requests.post(url, json={"command": command})
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
"""  

if __name__ == "__main__":
    server = HTTPServerWrapper("0.0.0.0", 8888)
    server.start()

    



