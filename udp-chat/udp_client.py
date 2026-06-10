import socket
import json
import threading
import sys

# ─── Konfigurasi ─────────────────────────────────────────────────────────────
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9001
BUFFER_SIZE = 4096


def send_packet(sock: socket.socket, payload: dict):
    """Kirim dict sebagai JSON ke server."""
    data = json.dumps(payload).encode("utf-8")
    sock.sendto(data, (SERVER_HOST, SERVER_PORT))


def receive_loop(sock: socket.socket, stop_event: threading.Event):
    """Thread penerima – mencetak pesan masuk tanpa menghalangi input."""
    while not stop_event.is_set():
        try:
            sock.settimeout(1.0)
            data, _ = sock.recvfrom(BUFFER_SIZE)
            try:
                obj = json.loads(data.decode("utf-8"))
                if "error" in obj:
                    print(f"\n[!] Error: {obj['error']}")
                elif "ok" in obj:
                    print(f"\n[✓] {obj['ok']}")
                else:
                    print(f"\n{data.decode('utf-8')}")
            except json.JSONDecodeError:
                print(f"\n{data.decode('utf-8', errors='replace')}")
            print("> ", end="", flush=True)
        except socket.timeout:
            continue
        except OSError:
            break


def run_client():
    username = input("Masukkan username Anda: ").strip()
    if not username:
        print("[!] Username tidak boleh kosong.")
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    stop_event = threading.Event()
    recv_thread = threading.Thread(
        target=receive_loop, args=(sock, stop_event), daemon=True
    )
    recv_thread.start()

    # Kirim permintaan JOIN
    send_packet(sock, {"type": "join", "username": username})

    print("\nPerintah: ketik pesan lalu Enter | '/quit' untuk keluar")
    print("-" * 45)

    try:
        while True:
            print("> ", end="", flush=True)
            msg = input().strip()
            if not msg:
                continue
            if msg.lower() == "/quit":
                send_packet(sock, {"type": "leave"})
                print("[✓] Anda telah keluar dari chat.")
                break
            send_packet(sock, {"type": "msg", "message": msg})
    except (KeyboardInterrupt, EOFError):
        send_packet(sock, {"type": "leave"})
    finally:
        stop_event.set()
        sock.close()
        print("\nKoneksi ditutup.")


if __name__ == "__main__":
    run_client()