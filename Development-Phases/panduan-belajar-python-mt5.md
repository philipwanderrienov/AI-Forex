# Panduan Belajar Python untuk MT5 Data Bridge

## Tujuan

Panduan ini dirancang untuk pemilik proyek yang belum mengenal Python. Targetnya bukan menjadi ahli Python sebelum mulai, melainkan memahami bridge native macOS yang menerima market data dari EA MQL5 secara aman dan read-only.

Backend bisnis tetap menggunakan .NET. Python menerima HTTP/JSON dari EA, melakukan validasi, local spool, retry, dan meneruskan data ke backend. Desain ini menghindari package `MetaTrader5` khusus Windows dan kebutuhan VM berbayar.

## Aturan keselamatan

- Belajar dan development dimulai dengan akun demo.
- Bridge hanya membaca market data.
- EA tidak boleh memanggil `OrderSend` atau fungsi perubahan posisi/order.
- Password, nomor akun, token backend, dan secret tidak ditulis di source code atau commit Git.
- Setiap tahap harus dapat dijalankan dan dipahami sebelum lanjut ke tahap berikutnya.

## Tahap 0 — Persiapan

Pelajari dan siapkan:

- Terminal MetaTrader 5 menggunakan installer resmi macOS.
- Akun demo broker telah login dan lima instrumen MVP terlihat di Market Watch.
- Python versi yang dikunci proyek, editor, Terminal macOS, dan Git.
- Virtual environment agar library proyek tidak bercampur dengan instalasi Python sistem.

Hasil belajar: memahami perbedaan terminal MT5, broker, Python interpreter, package, script, dan backend .NET.

## Tahap 1 — Dasar Python

Materi:

- variabel dan tipe sederhana: `str`, `int`, `float`, `bool`, `None`;
- list, dictionary, tuple, dan loop;
- `if/elif/else`;
- function, parameter, return value, dan exception;
- module/import;
- type hints dan dataclass;
- membaca error/traceback.

Latihan proyek:

1. Normalisasi `EUR/USD`, `EUR_USD`, dan `EURUSD.a` menjadi `EURUSD`, serta suffix seperti `XAUUSDm` menjadi `XAUUSD` tanpa menyamakan jenis instrumennya.
2. Validasi bahwa `high >= open/close` dan `low <= open/close`.
3. Konversi timestamp UTC menjadi teks ISO-8601.

Kriteria lulus: dapat menjelaskan input, output, dan error dari setiap function latihan.

## Tahap 2 — Tooling dan test

Materi:

- membuat/mengaktifkan virtual environment;
- memasang dependency;
- konfigurasi environment variable;
- formatting, linting, type checking, dan `pytest`;
- logging yang aman.

Latihan proyek:

- Buat unit test untuk mapping lima instrumen, instrument type, dan validasi OHLC.
- Buat konfigurasi contoh tanpa secret.
- Pastikan test dapat dijalankan dengan satu perintah.

Kriteria lulus: dapat menjalankan test, membaca kegagalan, memperbaiki satu kasus, lalu melihat test lulus.

## Tahap 3 — Menerima data dari EA MT5

Materi:

- konsep EA MQL5 exporter dan `WebRequest` tanpa mempelajari algoritma trading MQL5;
- HTTP server lokal Python dan endpoint health/data;
- request method, header, body JSON, response code, dan timeout;
- validasi schema payload dari EA;
- UTC, timeframe, spread, tick volume, dan real volume.

Latihan proyek:

1. Jalankan Python receiver pada localhost.
2. Kirim fixture bid/ask `EURUSD` melalui HTTP dan tampilkan tanpa credential.
3. Terima sepuluh candle final `M15` dari EA dan simpan hanya di memori.
4. Bandingkan hasilnya secara manual dengan chart terminal.

Kriteria lulus: dapat menjelaskan alur EA → HTTP → Python, setiap field payload, dan alasan candle berjalan tidak boleh dianggap final.

## Tahap 4 — Bridge ke backend

Materi:

- JSON dan data contract;
- HTTP request, timeout, status code, dan authentication header;
- batch, idempotency key, retry dengan backoff, serta local spool;
- separation of concerns dan dependency injection sederhana.

Latihan proyek:

- Kirim payload dummy ke endpoint development.
- Kirim satu batch candle MT5 yang telah dinormalisasi.
- Simulasikan backend mati dan pastikan data masuk spool, lalu terkirim setelah backend pulih.

Kriteria lulus: dapat menelusuri satu candle dari terminal sampai diterima backend dan menjelaskan apa yang terjadi saat jaringan gagal.

## Tahap 5 — Operasional

Materi:

- menjalankan bridge sebagai background service;
- health check, metric, dan structured log;
- restart/reconnect dan checkpoint;
- sinkronisasi waktu serta diagnosis data stale;
- update dependency dan rollback.

Kriteria lulus: dapat mengikuti runbook untuk menyalakan, menghentikan, memeriksa kesehatan, dan memulihkan bridge tanpa mengubah kode.

## Cara belajar saat implementasi

Untuk setiap perubahan Python, gunakan urutan berikut:

1. Jelaskan tujuan dalam bahasa biasa.
2. Tulis contoh input dan expected output.
3. Tulis test kecil.
4. Implementasikan function paling kecil yang membuat test lulus.
5. Jalankan dan baca hasilnya.
6. Refactor hanya setelah perilakunya dipahami.
7. Catat istilah baru dan pertanyaan pada learning log.

Jangan langsung membuat service besar. Setiap sesi idealnya menghasilkan satu kemampuan kecil yang bisa didemokan.

## Batas pengetahuan yang perlu dicapai untuk MVP

Pengguna tidak harus menguasai machine learning, async tingkat lanjut, framework web Python, atau algoritma trading dalam Python. Untuk MVP cukup memahami:

- function dan struktur data;
- package/virtual environment;
- menerima dan memvalidasi HTTP/JSON dari EA MT5;
- validasi dan JSON;
- HTTP client;
- test, log, configuration, dan error handling.

## Referensi utama

- [Tutorial resmi Python](https://docs.python.org/3/tutorial/)
- [Virtual environments](https://docs.python.org/3/tutorial/venv.html)
- [Instalasi resmi MetaTrader 5 pada macOS](https://www.metatrader5.com/en/terminal/help/start_advanced/install_mac)
- [MQL5 `WebRequest`](https://www.mql5.com/en/docs/network/webrequest)

Dokumentasi resmi digunakan sebagai sumber utama; kode implementasi proyek akan dibuat bertahap pada fase 01–02.
