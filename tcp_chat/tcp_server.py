import socket
import threading
import hashlib
import os
import struct
import logging
import datetime

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
HOST        = "0.0.0.0"
PORT        = 9002
BUFFER_SIZE = 4096
LOG_FILE    = "tcp_server.log"
UPLOAD_DIR  = "server_uploads"

# ─── Setup logging ───────────────────────────────────────────────────────────
os.makedirs(UPLOAD_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("TCPServer")

# ─── Database pengguna sederhana (username -> hashed_password) ───────────────
# Hash dengan sha256; di produksi gunakan bcrypt
def _h(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

USERS: dict[str, str] = {
    "risna":  _h("risna1"),
    "dwi":    _h("dwi2"),
    "indriani": _h("indriani3"),
}

# ─── State server ─────────────────────────────────────────────────────────────
clients: dict[str, socket.socket] = {}   # username -> socket
lock = threading.Lock()


# ─── Helpers ──────────────────────────────────────────────────────────────────
def ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def send_msg(conn: socket.socket, msg: str):
    """Kirim string berakhiran newline ke satu client."""
    try:
        conn.sendall((msg + "\n").encode("utf-8"))
    except Exception:
        pass


def broadcast(msg: str, exclude: str = None):
    """Kirim pesan ke semua client yang sudah login."""
    with lock:
        targets = list(clients.items())
    for uname, conn in targets:
        if uname != exclude:
            send_msg(conn, msg)


def recv_line(conn: socket.socket) -> str | None:
    """Terima satu baris teks dari client (hingga '\\n')."""
    buf = b""
    while True:
        try:
            ch = conn.recv(1)
        except OSError:
            return None
        if not ch:
            return None
        if ch == b"\n":
            return buf.decode("utf-8", errors="replace").strip()
        buf += ch


# ─── Autentikasi ─────────────────────────────────────────────────────────────
def authenticate(conn: socket.socket, addr) -> str | None:
    """
    Lakukan proses login.
    Mengembalikan username jika berhasil, None jika gagal/disconnect.
    """
    MAX_TRIES = 3
    send_msg(conn, "=== Selamat datang di TCP Chat Server ===")
    send_msg(conn, "Akun tersedia: alice/alice123  bob/bob456  charlie/charlie789")

    for attempt in range(1, MAX_TRIES + 1):
        send_msg(conn, f"[Login {attempt}/{MAX_TRIES}] Username: ")
        username = recv_line(conn)
        if username is None:
            return None
        send_msg(conn, "Password: ")
        password = recv_line(conn)
        if password is None:
            return None

        hashed = _h(password)
        if USERS.get(username) == hashed:
            with lock:
                if username in clients:
                    send_msg(conn, "[!] Akun ini sudah login di tempat lain.")
                    continue
                clients[username] = conn
            logger.info(f"LOGIN  {username} dari {addr}")
            send_msg(conn, f"[✓] Login berhasil! Halo, {username}.")
            send_msg(conn, "Ketik /help untuk daftar perintah.\n")
            return username
        else:
            send_msg(conn, "[!] Username atau password salah.")

    send_msg(conn, "[!] Terlalu banyak percobaan. Koneksi ditutup.")
    return None


# ─── Penerimaan file ──────────────────────────────────────────────────────────
def receive_file(conn: socket.socket, sender: str):
    """
    Protokol transfer file:
      1. Client kirim: "FILE <namafile> <ukuran_bytes>"
      2. Server ACK  : "READY"
      3. Client kirim binary data
      4. Server simpan ke UPLOAD_DIR
    """
    try:
        header = recv_line(conn)
        if not header or not header.startswith("FILE "):
            send_msg(conn, "[!] Header file tidak valid.")
            return
        parts = header.split(" ", 2)
        if len(parts) != 3:
            send_msg(conn, "[!] Format: FILE <namafile> <bytes>")
            return
        _, filename, size_str = parts
        filesize = int(size_str)
        safe_name = os.path.basename(filename)  # cegah path traversal
        dest = os.path.join(UPLOAD_DIR, safe_name)

        send_msg(conn, "READY")
        received = 0
        with open(dest, "wb") as f:
            while received < filesize:
                chunk = conn.recv(min(BUFFER_SIZE, filesize - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)

        if received == filesize:
            logger.info(f"FILE  {sender} -> {safe_name} ({filesize} bytes)")
            send_msg(conn, f"[✓] File '{safe_name}' diterima ({filesize} bytes).")
            broadcast(
                f"[{ts()}] SERVER: {sender} mengunggah file '{safe_name}'",
                exclude=sender,
            )
        else:
            send_msg(conn, "[!] Transfer tidak lengkap, file dihapus.")
            os.remove(dest)
    except Exception as e:
        logger.error(f"FILE error dari {sender}: {e}")
        send_msg(conn, f"[!] Gagal menerima file: {e}")


# ─── Prosesor perintah ────────────────────────────────────────────────────────
HELP_TEXT = """
Perintah yang tersedia:
  /list          - Tampilkan semua user yang online
  /send          - Kirim file ke server
  /help          - Tampilkan bantuan ini
  /quit          - Keluar dari chat
  <pesan>        - Kirim pesan ke semua user
""".strip()


def handle_command(conn: socket.socket, username: str, line: str) -> bool:
    """
    Proses baris input dari client.
    Mengembalikan False jika client ingin keluar.
    """
    if line.startswith("/"):
        cmd = line.split()[0].lower()
        if cmd == "/list":
            with lock:
                online = list(clients.keys())
            send_msg(conn, f"[{ts()}] Online ({len(online)}): " + ", ".join(online))

        elif cmd == "/send":
            receive_file(conn, username)

        elif cmd == "/help":
            send_msg(conn, HELP_TEXT)

        elif cmd == "/quit":
            return False

        else:
            send_msg(conn, f"[!] Perintah tidak dikenal: {cmd}. Ketik /help.")
    else:
        # Pesan biasa → broadcast
        if not line:
            return True
        if len(line) > 500:
            send_msg(conn, "[!] Pesan terlalu panjang (maks 500 karakter).")
            return True
        formatted = f"[{ts()}] {username}: {line}"
        logger.info(formatted)
        broadcast(formatted)

    return True


# ─── Thread per-client ────────────────────────────────────────────────────────
def handle_client(conn: socket.socket, addr):
    """Entrypoint thread untuk setiap koneksi masuk."""
    logger.info(f"Koneksi baru dari {addr}")
    try:
        username = authenticate(conn, addr)
        if not username:
            return

        # Umumkan ke semua client
        broadcast(f"[{ts()}] SERVER: *** {username} bergabung ***", exclude=username)

        while True:
            line = recv_line(conn)
            if line is None:
                break
            if not handle_command(conn, username, line):
                break

    except Exception as e:
        logger.error(f"Error pada {addr}: {e}")
    finally:
        with lock:
            uname = next((u for u, c in clients.items() if c is conn), None)
            if uname:
                del clients[uname]
        broadcast(f"[{ts()}] SERVER: *** {uname or '?'} keluar ***")
        logger.info(f"LOGOUT {uname or '?'} ({addr})")
        conn.close()


# ─── Main ─────────────────────────────────────────────────────────────────────
def run_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(10)
    logger.info(f"TCP Server aktif di {HOST}:{PORT} | Log: {LOG_FILE}")
    print("=" * 55)
    print(f"  TCP CHAT SERVER  |  port {PORT}  |  Ctrl+C untuk stop")
    print("=" * 55)

    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        logger.info("Server dihentikan oleh pengguna.")
    finally:
        srv.close()


if __name__ == "__main__":
    run_server()