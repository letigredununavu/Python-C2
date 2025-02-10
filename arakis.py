import cmd
import logger
import threading
from tcp_server import TCPServer
from colorama import Fore, Style

class ArakisCLI(cmd.Cmd):
    """
    Interactive CLI for managing the Python C2 Server
    """

    intro = "Welcome to Arakis🐍. Type help or ? to list commands."
    prompt = "(Arakis)> "

    def __init__(self, verbosity="error"):
        super().__init__()
        self.log = logger.Logger(verbosity=verbosity)
        
        self.tcp_servers = {} # Indexed by ID, values are TCPServer instances
        self.tcp_servers_count = 0

        self.http_servers = {} # Indexed by ID, values are HTTPServer instances
        self.http_servers_count = 0

        self.sandworms = {} # Connected clients
        self.current_sandworm = None # Active client session


        self.log.info(f"Verbosity level set to: {verbosity}")


    def default(self, line):
        """
        Overrides default cmd behavior to parse hierarchical commands
        """
        args = line.split()
        if not args:
            return
        
        main_cmd = args[0]
        sub_cmd = args[1] if len(args) > 1 else None
        sub_args = args[2:]

        if main_cmd == "tcp":
            self.handle_tcp_commands(sub_cmd, sub_args)
        
        elif main_cmd == "sandworm":
            self.handle_sandworm_commands(sub_cmd, sub_args)
        #elif main_cmd == "http":
        #    self.handle_http_commands(sub_cmd, sub_args)
        else:
            self.log.error(f"Unkown command: {line}. Type 'help' for usage.")
            print(Fore.YELLOW + f"[-] Unkown command: {line}." + Style.RESET_ALL + "Type 'help' for usage")


    ### TCP COMMANDS ###
    def handle_tcp_commands(self, sub_cmd, args):
        """
        wrapper for all tcp related commands. Options : list, create, start, remove, stop.
        Example: tcp list
        """
        if sub_cmd == "list":
            self.list_tcp_servers()
        
        elif sub_cmd == "create" and len(args) == 2:
            self.create_tcp_server(args[0], args[1])
        
        elif sub_cmd == "remove" and len(args) == 1:
            self.remove_tcp_server(args[0])
        
        elif sub_cmd == "start" and len(args) == 1:
            self.start_tcp_server(args[0])
        
        elif sub_cmd == "help":
            self.tcp_help()

        else:
            self.log.error(f"Invalid TCP command. Use: 'tcp help' if needed.")
            print(Fore.YELLOW + f"[-] Invalid TCP command. " + Style.RESET_ALL + "")
            print("Use: 'tcp help' if needed.")


    def create_tcp_server(self, ip, port):
        """
        setup_tcp_server <interface> <port> - Setup a listening TCP server
        Example: setup_tcp_server 0.0.0.0 8888
        """
        try:
            interface, port = ip, int(port)
            server = TCPServer(interface, port, self.on_new_sandworm)

            index = self.tcp_servers_count
            self.tcp_servers[index] = (server,index)
            self.tcp_servers_count+=1
            
            self.log.info(f"Setting up TCPServer on {interface}:{port} with index {index}. Use start_tcp_server to start it")
            print(Fore.GREEN + f"[+] Setting up TCPServer on {interface}:{port} with index {index}." + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalid tcp create arguments (interface or port)")
            print(Fore.YELLOW + "[-] Invalid tcp create arguments (interface or port)" + Style.RESET_ALL)


    def start_tcp_server(self, index):
        """
        start_tcp_server <index> - Start the tcp server indexed <index>
        Example: start_tcp_server 1
        """
        try:
            index = int(index)
            server,_ = self.tcp_servers.get(index)
            
            if not server:
                self.log.error(f"No TCP server found at index {index}. Use 'list_tcp_servers")
                return
            
            self.log.info(f"Starting TCP server {index}...")
            print(Fore.GREEN + f"[+] Starting TCP server {index}..." + Style.RESET_ALL)
            thread = threading.Thread(target=server.listen, daemon=True)
            thread.start()

        except ValueError:
            self.log.error("Invalid index. Ensure you provide a valid integer.")
            print(Fore.YELLOW + "[-] Invalid index. Ensure you provide a valid integer." + Style.RESET_ALL)


    def remove_tcp_server(self, index):
        """
        remove_tcp_server <id> - Remove TCP listener by id
        Example : remove_tcp_server 0
        """
        try:
            index = int(index)
            server,_ = self.tcp_servers[index]

            if not server:
                self.log.error(f"No TCP server found at index {index}. Use 'list_tcp_servers.")
                print(Fore.YELLOW + f"[-] No TCP server found at index {index}. Use 'list_tcp_servers." + Style.RESET_ALL)
                return
            
            if server.running:
                server.stop()

            del self.tcp_servers[index]
            self.log.warning(f"Removed TCP server {index}")
            print(Fore.GREEN + f"[+] Removed TCP server {index}" + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalid index. Ensure you provide a valid integer.")

    
    def list_tcp_servers(self):
        """
        list_tcp_servers - List all currently configured TCP Servers
        Example : list_tcp_servers
        """
        if not self.tcp_servers:
            self.log.info("No active TCP servers")
            print(Fore.YELLOW + f"[-] No active TCP servers" + Style.RESET_ALL)
            return
        
        print(Fore.GREEN + f"[+] TCP Servers actives :" + Style.RESET_ALL)
        for index, server_tuple in self.tcp_servers.items():
            server = server_tuple[0]
            self.log.info(f"[{index}] TCP Server on {server.IP}:{server.PORT}")
            print(Fore.GREEN + f"[{index}] {server.IP}:{server.PORT} ({"running" if server.running else "idle"})" + Style.RESET_ALL)


    def tcp_help(self):
        """
        help [command] - Show detailed help for a command.
        Example: help setup_tcp_server
        """
        print("\nAvailable Commands:")
        print("  tcp help                - This help message")
        print("  tcp start <index>       - Start an existing TCP server")
        print("  tcp remove <id>         - Remove a TCP server")
        print("  tcp list                - List all TCP servers")
        print("  tcp create <ip> <port>  - Create a new TCP server")
        print("  exit                    - Exit the CLI\n")

    ### SANDWORM COMMANDS ###
    def handle_sandworm_commands(self, sub_cmd, args):
        if sub_cmd == "list":
            self.list_sandworms()
        
        elif sub_cmd == "interact" and len(args) == 1:
            self.interact_with_sandworm(args[0])

        else:
            self.log.error("Invalid Sandworm command.")


    def list_sandworms(self):
        """
        List all connected sandworms
        """

        if not self.sandworms:
            print(Fore.YELLOW + "[-] No active sandworm" + Style.RESET_ALL)
            return
        
        print(Fore.GREEN + "[+] Connected Sandworms :" + Style.RESET_ALL)
        for index, client in self.sandworms.items():
            print(Fore.GREEN + f"- Sandworm [{index}] : {client['username']}@{client['hostname']}" + Style.RESET_ALL)
            

    def interact_with_sandworm(self, index):
        """
        Switch to interacting with a specific Sandworm
        """
        try:
            index = int(index)
            if index not in self.sandworms:
                self.log.error(f"Sandowmr [{index}] not found.")
                return
            
            self.current_sandworm = index
            self.prompt = f"(Sandworm [{index}:{self.sandworms[index]['username']}]> "

        except ValueError:
            self.log.error("Invalid index")

    ### CALLBACK FUNCTION FOR NEW SANDWORM ###
    def on_new_sandworm(self, index, hostname, username, client_socket):
        """
        This function is called when a new Sandworm connects.
        """
        self.sandworms[index] = {
            "socket": client_socket,
            "hostname": hostname,
            "username": username
        }

    
    ### CALLBACK FUNCTION WHEN CLIENT DISCONNECT
    def del_sandworm(self, index):
        # TODO, peut-être que ca sera pas ca non plus, jsuis pas sur de celle-là
        pass


    def do_help(self, arg):
        """
        Custom help command to list hierarchical commands.
        """
        if arg:
            cmd.Cmd.do_help(self, arg)
        else:
            print("\nAvailable Commands:")
            print("  tcp list                - List all TCP servers")
            print("  tcp start <ip> <port>   - Start a new TCP server")
            print("  tcp remove <id>         - Remove a TCP server")
            print("  http list               - List all HTTP servers")
            print("  http remove <id>        - Remove an HTTP server")
            print("  exit                    - Exit the CLI\n")



    def do_exit(self, arg):
        """
        exit - Exit the CLI
        """
        self.log.info("Exiting Arakis CLI. May Thy Knife Chip & Shatter!")
        return True
            
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
if __name__ == '__main__':
    ArakisCLI().cmdloop()