import os
import sys
import json
import math
import socket
import hashlib
import threading
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)

BUFFER_SIZE = 4096
PORT = 5000


def slice_file(filename):
    file_path = os.path.join('shared_files', filename)
    file_size = os.path.getsize(file_path)
    chunk_size = math.ceil(file_size / 5)

    os.makedirs('sliced_files', exist_ok=True)
    chunk_hashes = {}
    with open(file_path, 'rb') as f:
        for i in range(1, 6):
            chunk = f.read(chunk_size)
            chunk_name = f"{filename}_{i}_temp"
            chunk_path = os.path.join('sliced_files', chunk_name)
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk)
            sha256 = hashlib.sha256(chunk).hexdigest()
            chunk_hashes[chunk_name] = sha256
    return chunk_hashes


def handle_client(conn, addr, file_name, chunk_list, hash_dict):
    try:
        data = conn.recv(BUFFER_SIZE)
        request = json.loads(data.decode())
        req_type = request.get('type')

        if req_type == 'metadata':
            print(Fore.YELLOW + f"Metadata requested by {addr[0]}")
            meta = {'fileName': file_name, 'chunks': chunk_list}
            conn.send(json.dumps(meta).encode())

        elif req_type == 'hash':
            print(Fore.YELLOW + f"Hash file requested by {addr[0]}")
            hash_json = json.dumps(hash_dict).encode()
            conn.send(hash_json)

        elif req_type == 'chunk':
            chunk_name = request['filename']
            chunk_path = os.path.join('sliced_files', chunk_name)
            if os.path.exists(chunk_path):
                with open(chunk_path, 'rb') as f:
                    data = f.read()
                    conn.sendall(data)
                print(Fore.GREEN + f"Sent {chunk_name} to {addr[0]}")
            else:
                print(Fore.RED + f"Requested chunk not found: {chunk_name}")
        else:
            print(Fore.RED + f"Unknown request type from {addr[0]}")

    except Exception as e:
        print(Fore.RED + f"Error handling client {addr}: {e}")
    finally:
        conn.close()

shared_files = os.listdir('shared_files')
for i, f in enumerate(shared_files):
    print(f"{i}: {f}")
selected = int(input("Select a file to host: "))
file_name = shared_files[selected]
print(Fore.GREEN + f"Hosting file: {file_name}")

chunk_hashes = slice_file(file_name)
chunk_list = list(chunk_hashes.keys())

sock = socket.socket()
sock.bind(('', PORT))
sock.listen(5)

print(Fore.GREEN + "contentDictionary and hash file ready.")
print(Fore.BLUE + "Waiting for download requests...")

while True:
    conn, addr = sock.accept()
    threading.Thread(target=handle_client, args=(conn, addr, file_name, chunk_list, chunk_hashes)).start()
