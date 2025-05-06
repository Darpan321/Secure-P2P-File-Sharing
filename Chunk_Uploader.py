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
=======
#Our imports
import ssl
import hashlib

#Color
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

# Define Constant Variables
SERVER_PORT = 5000
BUFFER_SIZE = 4096

def sliceFile(content_name:str) -> list:
    # Create the directory for sliced_files
    if not os.path.exists('sliced_files'):
        os.makedirs('sliced_files')

    # Function to slice the file into chunks
    fileURL = 'shared_files/' + content_name
    c = os.path.getsize(fileURL)
    CHUNK_SIZE = math.ceil(math.ceil(c) / 5)
    
    chunk_hashes = []

    index = 1
    with open(fileURL, 'rb') as infile:
        chunk = infile.read(int(CHUNK_SIZE))
        while chunk:
            chunkname = content_name + '_' + str(index) + '_' + 'temp'
            chunk_addr = 'sliced_files/' + chunkname
            with open(chunk_addr, 'wb+') as chunk_file:
                chunk_file.write(chunk)

            #Hash this chunk
            sha256 = hashlib.sha256()
            sha256.update(chunk)
            chunk_hashes.append(sha256.hexdigest())

            index += 1
            chunk = infile.read(int(CHUNK_SIZE))
    chunk_file.close()

    #Return the list of hashes
    return chunk_hashes 

# Get the server IP address
temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
temp_sock.connect(('8.8.8.8', 80))
SERVER_IP = temp_sock.getsockname()[0]
temp_sock.close()

#TSL STUFF
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')

# Create and configure the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((SERVER_IP, SERVER_PORT))
sock.listen(9)
print('Server is listening on' + Fore.GREEN + f' {SERVER_IP}:{SERVER_PORT}!')

# Get the list of shared files
shared_files = os.listdir('shared_files')

# Modify the file names in the list
for i in range(len(shared_files)):
    print(Fore.YELLOW + str(i) + ': ' + Fore.RESET + shared_files[i])
# Main


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
=======
# Slice the selected file into chunks
chunk_hashes = sliceFile(selectedFileName)

# Save chunk hashes to JSON
if not os.path.exists('json_files'):
    os.makedirs('json_files')

hash_dict = {}
for i, hash_value in enumerate(chunk_hashes, start=1):
    chunk_name = f"{selectedFileName}_{i}_temp"
    hash_dict[chunk_name] = hash_value

hash_file_path = f"json_files/{selectedFileName}_hashes.json"
with open(hash_file_path, 'w') as hash_file:
    json.dump(hash_dict, hash_file)

print(Fore.GREEN + 'Chunk hashes saved for integrity verification.')

#Main

print(Fore.GREEN + "contentDictionary and hash file ready.")
print(Fore.BLUE + "Waiting for download requests...")

while True:
    conn, addr = sock.accept()
    threading.Thread(target=handle_client, args=(conn, addr, file_name, chunk_list, chunk_hashes)).start()
