import socket
import threading
import os
import sys

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9002
BUFFER_SIZE = 4096


# ─── Thread penerima ─────────────────────────────────────────────────────────
def receive_loop(sock: socket.socket, stop_event: threading.Event):
    """Terima dan cetak pesan dari server secara terus-menerus."""
    buf = ""
    while not stop_event.is_set():
        try:
            sock.settimeout(1.0)
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("\n[!] Koneksi ke server terputus.")
                stop_event.set()
                break
            buf += data.decode("utf-8", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if line.strip():
                    print(f"\r{line.strip()}")
                    print("> ", end="", flush=True)
        except socket.timeout:
            continue
        except OSError:
            break


# ─── Kirim file ──────────────────────────────────────────────────────────────
def send_file(sock: socket.socket, filepath: str):
    """
    Protokol:
      1. Kirim "FILE <namafile> <ukuran>"
      2. Tunggu "READY" dari server
      3. Kirim binary data
    """
    if not os.path.isfile(filepath):
        print(f"[!] File tidak ditemukan: {filepath}")
        return
    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filepath)

    sock.sendall(f"FILE {filename} {filesize}\n".encode())

    # Tunggu ACK dari server
    ack = b""
    while b"READY" not in ack and b"\n" not in ack:
        ack += sock.recv(BUFFER_SIZE)

    if b"READY" not in ack:
        print("[!] Server tidak siap menerima file.")
        return

    sent = 0
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            sock.sendall(chunk)
            sent += len(chunk)
            pct = int(sent / filesize * 100)
            print(f"\r  Mengirim... {pct}%", end="", flush=True)
    print(f"\r  File '{filename}' terkirim ({filesize} bytes).     ")


# ─── Input loop utama ─────────────────────────────────────────────────────────
def input_loop(sock: socket.socket, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            print("> ", end="", flush=True)
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            sock.sendall(b"/quit\n")
            break

        if not line:
            continue

        if line.lower().startswith("/send"):
            # Ambil path file dari input berikutnya jika tidak disertakan
            parts = line.split(maxsplit=1)
            if len(parts) < 2:
                print("Masukkan path file: ", end="", flush=True)
                filepath = input().strip()
            else:
                filepath = parts[1]
            sock.sendall(b"/send\n")   # beri tahu server
            send_file(sock, filepath)

        elif line.lower() == "/quit":
            sock.sendall(b"/quit\n")
            stop_event.set()
            break

        else:
            sock.sendall((line + "\n").encode("utf-8"))


# ─── Main ─────────────────────────────────────────────────────────────────────
def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
    except ConnectionRefusedError:
        print(f"[!] Tidak dapat terhubung ke {SERVER_HOST}:{SERVER_PORT}")
        sys.exit(1)

    print(f"[✓] Terhubung ke server {SERVER_HOST}:{SERVER_PORT}")
    print("─" * 45)

    stop_event = threading.Event()
    recv_thread = threading.Thread(
        target=receive_loop, args=(sock, stop_event), daemon=True
    )
    recv_thread.start()

    input_loop(sock, stop_event)

    sock.close()
    print("Koneksi ditutup.")


if __name__ == "__main__":
    run_client()