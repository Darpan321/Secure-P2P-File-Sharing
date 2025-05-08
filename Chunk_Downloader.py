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
=======
#Our imports
import ssl
import hashlib

#Color
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset=True)

# Define Constant Variables
PORT = 5000
BUFFER_SIZE = 4096  # 4KB of data


def delete_files_with_suffix(directory:str, suffix:str) -> None:
    # Get the list of files in the directory
    files = os.listdir(directory)

    # Iterate through the files
    for file in files:
        if file.endswith(suffix):
            file_path = os.path.join(directory, file)
            os.remove(file_path)
            # print(f"Deleted file: {file}")


def combineSlices(content_name: str) -> None:
    # Combine downloaded chunks into a single file
    chunknames = [content_name+'_1_temp', content_name+'_2_temp', content_name+'_3_temp', content_name+'_4_temp', content_name+'_5_temp']
    
    with open('downloaded_files/' + content_name, 'wb') as outfile:
        for chunk in chunknames:
            with open('sliced_files/' + chunk, 'rb') as infile:
                outfile.write(infile.read())
                
    delete_files_with_suffix('downloaded_files','temp')
    

# Open and load the content dictionary file
contentFile = open('json_files/contentDictionary.json', 'rt')
contentFile_data = json.load(contentFile)

while True:
    availableFiles = []
    # Iterate through contentDictionary to get available file names
    for fileChunk in contentFile_data:
        fileName = str(fileChunk)[:len(fileChunk)-7]  # get rid of the number part (_i)
        if fileName not in availableFiles:
            availableFiles.append(fileName)

    print('Enter the index of the file you want to download.')
    # Display available file options
    for index in range(len(availableFiles)):
        print(Fore.YELLOW + str(index) + ': '+ Fore.RESET + availableFiles[index])

    selectedFileIndex = int(input('> '))

    hash_file_path = f"json_files/{availableFiles[selectedFileIndex]}_hashes.json"
    with open(hash_file_path, 'r') as hash_file:
        chunk_hashes = json.load(hash_file)

    allChunksDownloaded = True
    # Iterate through chunks to download them
    for i in range(1, 6):
        chunkToDownload = availableFiles[selectedFileIndex] + '_' + str(i) + '_' + 'temp'
        requestJSON = json.dumps({'filename': chunkToDownload}).encode('utf8')
        file = json.loads(requestJSON)

        chunkIsDownloaded = False
        # Iterate through IPs associated with the chunk for downloading
        for ip in contentFile_data[chunkToDownload]:
            print(f'Requesting {ip} for ' + Fore.YELLOW + f'{chunkToDownload}' + Fore.RESET)
            context = ssl._create_unverified_context()  # for testing; skips cert verification
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            secure_sock = context.wrap_socket(sock, server_hostname=ip)
            secure_sock.settimeout(10)
            try:
                secure_sock.connect((ip, PORT))
                secure_sock.send(requestJSON)
                print(Fore.YELLOW + file['filename'] + ' was requested.')
                downloadedChunk = secure_sock.recv(BUFFER_SIZE)

                # Receive remaining data
                while True:
                    msg = secure_sock.recv(BUFFER_SIZE)
                    if not msg:
                        break
                    downloadedChunk += bytes(msg)

                chunkIsDownloaded = True

            except Exception as e:
                secure_sock.close()
                print('Could not download ' + chunkToDownload + ' from ' + ip)
                print('Error: ', e)
                # print(Back.CYAN + '=' * 70)
                continue

        if chunkIsDownloaded:
            # Log the downloaded chunk and save it to disk
            with open('logs/download_log.txt', 'a') as up_log:
                now = datetime.now()
                dt_string = now.strftime('%d/%m/%Y %H:%M:%S')
                up_log.write(dt_string + ' ' + chunkToDownload + ' from ' + str(ip) + '\n')

            # Create the directory for downloaded_files
            if not os.path.exists('downloaded_files'):
                os.makedirs('downloaded_files')

            with open('downloaded_files/' + chunkToDownload, 'wb') as downloadedFile:
                downloadedFile.write(downloadedChunk)

            # Verify hash
            sha256 = hashlib.sha256()
            sha256.update(downloadedChunk)
            downloaded_hash = sha256.hexdigest()
            expected_hash = chunk_hashes.get(chunkToDownload)

            if downloaded_hash == expected_hash:
                print(Fore.GREEN + f"Integrity check passed for {chunkToDownload}")
            else:
                print(Fore.RED + f"Integrity check FAILED for {chunkToDownload}")


            secure_sock.close()
            print(Fore.GREEN + 'Chunk downloaded successfully!\n')
            # print(Back.CYAN + '=' * 70)
# Main
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