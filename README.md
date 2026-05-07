# Tugas Socket Programming — UDP & TCP

## Deskripsi Program
Project ini merupakan implementasi pemrograman socket menggunakan bahasa Python dengan dua protokol komunikasi, yaitu UDP dan TCP.

Program terdiri dari:

1. **UDP Chat Application**
- Menggunakan protokol UDP
- Mendukung komunikasi client-server
- Server dapat menerima pesan dari lebih dari satu client
- Pesan dikirim dalam format `username: pesan`

2. **TCP Chat Application**
- Menggunakan protokol TCP
- Mendukung multiple client connection
- Memiliki sistem login sederhana menggunakan username dan password
- Mendukung pengiriman file dari client ke server

## Cara Menjalankan Program

1. Clone / download project
Masuk ke folder project:

```bash
cd socket_project
```

Jika menggunakan virtual environment:

```bash
source venv/bin/activate
```

2. Menjalankan Program UDP
Buka terminal pertama untuk server:

```bash
python3 udp_server.py
```

Buka terminal kedua atau lebih untuk client:

```bash
python3 udp_client.py
```

Masukkan username, lalu mulai chat.

Contoh:

```text
Masukkan username Anda: risna
> halo
[07:18:43] risna: halo
```

3. Menjalankan Program TCP
Buka terminal pertama untuk server:

```bash
python3 tcp_server.py
```

Buka terminal kedua atau lebih untuk client:

```bash
python3 tcp_client.py
```
Login menggunakan akun berikut:

```text
Username: risna
Password: risna1

Username: dwi
Password: dwi2

Username: indriani
Password: indriani
```

Setelah login berhasil, client dapat menggunakan command berikut:

```text
/list -> menampilkan user online
/send -> mengirim file ke server
/help -> bantuan command
/quit -> keluar dari chat
```

##	Fitur Program
### UDP
- Multi-client chat
- Logging pesan ke file
- Format pesan `username: pesan`
- Validasi input sederhana
- Broadcast pesan

### TCP
- Login autentikasi username/password
- Multiple client connection
- Real-time chat
- File transfer client ke server
- Command system:
- `/list` : melihat user online
- `/send` : mengirim file
- `/help` : menampilkan bantuan
- `/quit` : keluar dari chat

## Output Program
Program berjalan melalui Command Line Interface (CLI).

Output menampilkan:
- status server
Udp_server
 <img width="838" height="471" alt="image" src="https://github.com/user-attachments/assets/d1fd7aac-b01d-45f6-a092-572f1bd89081" />

tcp_server
 
<img width="871" height="284" alt="image" src="https://github.com/user-attachments/assets/f5602bdf-4f7c-42b2-9747-0a09b90aef2a" />

- koneksi client
<img width="940" height="374" alt="image" src="https://github.com/user-attachments/assets/ac4e5548-368a-47ba-98ed-5b0e7de68382" />

 - pesan chat
<img width="940" height="449" alt="image" src="https://github.com/user-attachments/assets/f803a03f-d899-467d-810b-19096c0e7229" />

- login
<img width="940" height="472" alt="image" src="https://github.com/user-attachments/assets/b620358b-85d0-4ba7-942f-3fe06eb08c6a" />
 
- file transfer
<img width="940" height="497" alt="image" src="https://github.com/user-attachments/assets/32f0911a-68af-4f5e-a54f-efbf0c5026ac" />

- logging aktivitas
Udp_chat.log
<img width="940" height="497" alt="image" src="https://github.com/user-attachments/assets/3919b623-9c17-4735-bf5e-e5f7ca6457fa" />

tcp_server.log
<img width="940" height="447" alt="image" src="https://github.com/user-attachments/assets/939cdbbc-778b-44b4-86ad-4f60aec00ba9" />

 
