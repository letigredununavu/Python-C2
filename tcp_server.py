import threading
import socket
import logger

log = logger.Logger(verbosity="debug")


class TCPServer:

    def __init__(self, IP:str, PORT:int, threads:int = 5):
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
        self.running = True # Flag to control server shutdown
        self.counter = 0 # Keep track of clients

        log.debug(f"TCPServer initialized for {IP}:{PORT} with capacity {threads}")


    def listen(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows reusing the same port quickly
        self.server.bind((self.IP, self.PORT))
        self.server.listen(self.threads)
        
        log.info(f"TCPServer started listening for {self.IP}:{self.PORT} with capacity {self.threads}")

        try:

            while True:
                client, address = self.server.accept()
                self.counter+=1
                log.info(f"Accepted connection from {address[0]}:{address[1]}")

                client_handler = threading.Thread(target=self.handle_client, args=(client,address))
                client_handler.daemin = True # Ensures threads exit when main program ends
                client_handler.start()

        except KeyboardInterrupt:
            log.warning("Server shutting down due to keyboard interrupt.")
        finally:
            self.stop()


    def handle_client(self, client_socket, address):
        """
        Handles a single client connection.

        :param client_socket: The client's socket object
        :param address: The client's (IP, Port) tuple
        """
        log.debug(f"Handling client {address[0]}:{address[1]}")        
        
        try:
            while True:
                request = client_socket.recv(1024)
                log.info(f"Received data from client {address[0]}:{address[1]}")
                client_data = request.decode('UTF-8')
                if client_data == "exit\n":
                    log.warning(f"Received 'exit' command, closing connection")
                    break
                else:
                    print(f"Data : {request.decode('UTF-8')}")
                    client_socket.send(b'ACK')
        
        except Exception as e:
            log.error(f"Error handling client {address[0]}:{address[1]} : {e}")
        
        finally:
            self.counter-=1
            log.info(f"Closing connection with {address[0]}:{address[1]}")
            client_socket.close()

    
    def stop(self):
        """
        Stops the server gracefully.
        """
        log.warning("Stopping TCP server...")
        



