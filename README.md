# Secure Peer-to-Peer File Sharing

A Python-based P2P file sharing system that enables secure, encrypted, and decentralized file exchange using TLS and chunk-based transfer.

## 📦 Features
- Secure file sharing using TLS
- Chunked file upload and download with SHA-256 integrity checking
- Peer discovery and announcement system
- Works across NAT using Ngrok
- Multithreaded uploader and downloader

## 📁 Project Structure
- `Uploader.py` – Hosts and serves file chunks
- `Downloader.py` – Downloads and assembles chunks
- `Announcer.py` – Broadcasts available chunks
- `Discovery.py` – Discovers available chunks from other peers

## 🚀 Usage
Start the uploader:
```bash
python uploader/Uploader.py
