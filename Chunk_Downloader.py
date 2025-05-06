import os
import json
import socket
import hashlib
from datetime import datetime
from colorama import Fore, init

init(autoreset=True)
BUFFER_SIZE = 4096

def combine_slices(file_name):
    with open('downloaded_files/' + file_name, 'wb') as outfile:
        for i in range(1, 6):
            chunkname = f"{file_name}_{i}_temp"
            with open('downloaded_files/' + chunkname, 'rb') as infile:
                outfile.write(infile.read())

os.makedirs('downloaded_files', exist_ok=True)
os.makedirs('logs', exist_ok=True)

peer_ip = input("Enter host: ").strip()
peer_port = int(input("Enter port: ").strip())

# Metadata request
try:
    s = socket.socket()
    s.connect((peer_ip, peer_port))
    s.send(json.dumps({'type': 'metadata'}).encode())
    metadata = json.loads(s.recv(BUFFER_SIZE).decode())
    file_name = metadata['fileName']
    chunk_list = metadata['chunks']
    print(Fore.GREEN + f"Metadata received for file: {file_name}")
    s.close()
except Exception as e:
    print(Fore.RED + f"Failed to retrieve metadata: {e}")
    exit(1)

# Hash file request
try:
    s = socket.socket()
    s.connect((peer_ip, peer_port))
    s.send(json.dumps({'type': 'hash', 'filename': file_name}).encode())
    hash_data = json.loads(s.recv(BUFFER_SIZE).decode())
    hash_file_path = f"json_files/{file_name}_hashes.json"
    os.makedirs('json_files', exist_ok=True)
    with open(hash_file_path, 'w') as f:
        json.dump(hash_data, f, indent=2)
    print(Fore.GREEN + f"Hash file received and saved: {file_name}_hashes.json")
    s.close()
except Exception as e:
    print(Fore.RED + f"Failed to fetch hash file for {file_name}")
    print("Error:", e)
    exit(1)

# Load hashes
with open(hash_file_path, 'r') as h:
    chunk_hashes = json.load(h)

all_ok = True
for chunk in chunk_list:
    try:
        s = socket.socket()
        s.connect((peer_ip, peer_port))
        s.send(json.dumps({'type': 'chunk', 'filename': chunk}).encode())

        data = b''
        while True:
            packet = s.recv(BUFFER_SIZE)
            if not packet:
                break
            data += packet
        s.close()

        with open('downloaded_files/' + chunk, 'wb') as f:
            f.write(data)

        h = hashlib.sha256(data).hexdigest()
        if h == chunk_hashes[chunk]:
            print(Fore.GREEN + f"Integrity check PASSED for {chunk}")
        else:
            print(Fore.RED + f"Integrity check FAILED for {chunk}")
            all_ok = False

        with open('logs/download_log.txt', 'a') as log:
            log.write(f"{datetime.now()} {chunk} from {peer_ip}\n")

    except Exception as e:
        print(Fore.RED + f"Failed to download {chunk}: {e}")
        all_ok = False
        break

if all_ok:
    print(Fore.CYAN + f"\nAll chunks downloaded. Reassembling {file_name}...")
    combine_slices(file_name)
else:
    print(Fore.RED + "\nDownload failed or integrity error.")