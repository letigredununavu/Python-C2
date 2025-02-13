import socket
import sys
import os

def get_system_info():
    """
    Retrieve the current system's hostname and username.
    """

    hostname = socket.gethostname()
    username = os.getenv("USERNAME") or os.getenv("USER") or "Unknown"

    # TODO : supporter linux??
    # Pour system info c'est facile avec les variable env USER et NAME


    return hostname, username


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
        if response == "ACK":
            print("[+] Server acknowledged connection.")

    except Exception as e:
        print(f"[-] Error : {e}")

    finally:
        client_socket.close()


if __name__ == '__main__':
    main()
    

