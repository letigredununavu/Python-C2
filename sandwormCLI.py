import cmd
import logger
from tcp_server import TCPServer

class SandwormCLI(cmd.cmd):
    """
    Interactive CLI for managing the Python C2 Server
    """

    intro = "Welcome to Arakis🐍. Type help or ? to list commands."
    prompt = "(Sandworm)> "

    def __init__(self, verbosity="info"):
        super().__init__()
        self.log = logger.Logger(verbosity=verbosity)
        
        # Storing TCP servers
        self.tcp_servers = {}
        self.tcp_servers_ids = 0

        # Storing HTTP servers
        self.http_servers = {}
        self.http_servers_ids = 0


        self.log.info(f"Verbosity level set to: {verbosity}")

    def do_setup_tcp_server(self, arg):
        """
        setup_tcp_server <interface> <port> - Setup a listening TCP server
        Example: setup_tcp_server 0.0.0.0 8888
        """
        args = arg.split()
        if len(args) != 2:
            self.log.error("Usage : setup_tcp_server <interface> <port>")
            return
        
        try:
            interface, port = args[0], int(args[1])
            server = TCPServer(interface, port)
            self.tcp_servers[self.tcp_servers_count] = server
            self.tcp_servers_ids+=1
            self.log.info(f"Starting listener on {interface}:{port}")

        except ValueError:
            self.log.error("Invalid tcp server arguments (interface or port)")


    def do_remove_tcp_server(self, arg):
        """
        remove_tcp_server <id> - Remove TCP listener by id
        Example: remove_tcp_server 0
        """
        args = arg.split
        if len(args) != 1:
            self.log.error("Usage : remove_tcp_server <id>")
            return
        
        try:
            id = args[0]
            self.tcp_servers[id].stop()
            self.log.warning(f"Stopped TCP Server indexed {id}..")
            del self.tcp_servers[id]
            self.log.warning(f"Removed TCP Server indexed {id}..")

        except ValueError:
            self.log.error("Invalid tcp server id (list your active server with list_tcp_servers)")
            
            
""" TODO
Faire une option pour lister les serveurs
    - TCP
    - HTTP


Faire des options pour interagir avec le système distant
    - upload_file
    - download file
    - execute cmd
    - execute powershell


Faire une option pour exécuter des commandes locales
    - cat
    - ls
    - id
    - cd
    - etc.

"""
