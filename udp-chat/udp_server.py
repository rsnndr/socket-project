import socket
import logging
import datetime
import re
import os
import json
import threading

# ─── Konfigurasi ────────────────────────────────────────────────────────────
HOST        = "0.0.0.0"
PORT        = 9001
BUFFER_SIZE = 4096
LOG_FILE    = "udp_chat.log"
MAX_MSG_LEN = 300

# ─── Setup logging ke file + console ────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("UDPServer")

# ─── State server ────────────────────────────────────────────────────────────
clients: dict[tuple, str] = {}   # addr -> username
lock = threading.Lock()


# ─── Validasi input ──────────────────────────────────────────────────────────
def validate_username(name: str) -> tuple[bool, str]:
    """Username harus 3-20 karakter alfanumerik/underscore."""
    name = name.strip()
    if len(name) < 3 or len(name) > 20:
        return False, "Username harus 3-20 karakter."
    if not re.match(r"^\w+$", name):
        return False, "Username hanya boleh huruf, angka, dan underscore."
    return True, ""


def validate_message(msg: str) -> tuple[bool, str]:
    """Pesan tidak boleh kosong dan tidak melebihi MAX_MSG_LEN."""
    msg = msg.strip()
    if not msg:
        return False, "Pesan tidak boleh kosong."
    if len(msg) > MAX_MSG_LEN:
        return False, f"Pesan terlalu panjang (maks {MAX_MSG_LEN} karakter)."
    return True, ""


# ─── Format pesan ────────────────────────────────────────────────────────────
def format_message(username: str, message: str) -> str:
    """Format: [HH:MM:SS] username: pesan"""
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    return f"[{ts}] {username}: {message}"


# ─── Broadcast ke semua client terdaftar ────────────────────────────────────
def broadcast(sock: socket.socket, formatted: str, exclude: tuple = None):
    with lock:
        targets = list(clients.items())
    msg_bytes = formatted.encode("utf-8")
    for addr, _ in targets:
        if addr != exclude:
            try:
                sock.sendto(msg_bytes, addr)
            except Exception as e:
                logger.warning(f"Gagal kirim ke {addr}: {e}")


# ─── Proses paket masuk ──────────────────────────────────────────────────────
def handle_packet(sock: socket.socket, data: bytes, addr: tuple):
    """Parse paket JSON dan proses berdasarkan tipe."""
    try:
        payload = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        sock.sendto(b'{"error":"Format paket tidak valid."}', addr)
        return

    ptype = payload.get("type", "")

    # --- Registrasi username ---
    if ptype == "join":
        username = payload.get("username", "")
        ok, err = validate_username(username)
        if not ok:
            sock.sendto(json.dumps({"error": err}).encode(), addr)
            return
        with lock:
            if username in clients.values():
                sock.sendto(
                    json.dumps({"error": "Username sudah dipakai."}).encode(), addr
                )
                return
            clients[addr] = username

        logger.info(f"JOIN  {username} dari {addr}")
        sock.sendto(json.dumps({"ok": f"Selamat datang, {username}!"}).encode(), addr)
        notice = format_message("SERVER", f"*** {username} bergabung ***")
        broadcast(sock, notice, exclude=addr)
        logger.info(notice)

    # --- Pesan chat ---
    elif ptype == "msg":
        with lock:
            username = clients.get(addr)
        if not username:
            sock.sendto(
                json.dumps({"error": "Belum terdaftar. Kirim JOIN dahulu."}).encode(),
                addr,
            )
            return
        message = payload.get("message", "")
        ok, err = validate_message(message)
        if not ok:
            sock.sendto(json.dumps({"error": err}).encode(), addr)
            return
        formatted = format_message(username, message)
        logger.info(formatted)
        broadcast(sock, formatted)   # kirim ke semua termasuk pengirim

    # --- Keluar ---
    elif ptype == "leave":
        with lock:
            username = clients.pop(addr, "Unknown")
        notice = format_message("SERVER", f"*** {username} keluar ***")
        logger.info(notice)
        broadcast(sock, notice)

    else:
        sock.sendto(json.dumps({"error": "Tipe paket tidak dikenal."}).encode(), addr)


# ─── Main loop ───────────────────────────────────────────────────────────────
def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    logger.info(f"UDP Server aktif di {HOST}:{PORT} | Log: {LOG_FILE}")
    print("=" * 55)
    print(f"  UDP CHAT SERVER  |  port {PORT}  |  Ctrl+C untuk stop")
    print("=" * 55)

    try:
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            # Setiap paket diproses di thread terpisah agar non-blocking
            t = threading.Thread(
                target=handle_packet, args=(sock, data, addr), daemon=True
            )
            t.start()
    except KeyboardInterrupt:
        logger.info("Server dihentikan oleh pengguna.")
    finally:
        sock.close()


if __name__ == "__main__":
    run_server()