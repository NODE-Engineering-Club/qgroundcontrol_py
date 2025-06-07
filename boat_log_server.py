import socket

def start_server(host='172.16.21.153', port=9999):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((host, port))
        server.listen()
        print(f"🟢 Waiting for connection on {host}:{port}")
        conn, addr = server.accept()
        print(f"🔵 Connected by {addr}")

        with conn:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(data.decode().strip())

if __name__ == "__main__":
    start_server()
