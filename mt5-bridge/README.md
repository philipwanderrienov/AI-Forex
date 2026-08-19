# MT5 Python Bridge

Lihat [Alur MT5 Bridge](FLOW.md) untuk diagram dan penjelasan perjalanan data dari EA sampai
durable spool, termasuk status bagian yang belum diimplementasikan.

![Flowchart MT5 Bridge](docs/mt5-bridge-flowchart.png)

Untuk memahami urutan kerja source Python tanpa membaca kode terlebih dahulu, lihat
[flowchart program Python](docs/python-program-flowchart.png).

![Flowchart program Python MT5 Bridge](docs/python-program-flowchart.png)

Bridge ini berjalan native di Lubuntu dan hanya menerima data dari EA melalui `127.0.0.1`.
Bridge menerima heartbeat starter dan envelope candle `mt5-envelope.v1`, lalu memvalidasi
kontrak canonical dan menyimpan batch secara atomik ke durable FIFO spool sebelum memberikan
respons `202 Accepted`. Bridge belum meneruskan data ke backend.

```bash
cd mt5-bridge
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m forex_intelligence_bridge.server
```

Pada terminal kedua:

```bash
curl http://127.0.0.1:8001/health
```

EA mengirim heartbeat ke `POST /v1/mt5/heartbeat` dan batch candle versioned ke
`POST /v1/mt5/envelopes`. Batch candle dibatasi maksimal 100 record. Timestamp harus UTC,
harga dikirim sebagai decimal string, dan checksum memakai format `sha256:<64 hex>`.
Checksum dihitung dari array `records` sebagai JSON UTF-8 compact dengan key yang diurutkan.

Konfigurasi spool bersifat opsional:

```text
MT5_BRIDGE_SPOOL_PATH=spool
MT5_BRIDGE_SPOOL_MAX_ITEMS=10000
```

Saat kapasitas penuh, bridge menolak batch baru dengan HTTP `507` dan tidak menghapus batch
lama secara diam-diam. File spool diberi permission `0600` dan direplay menurut sequence.

Menjalankan test:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Jangan mengubah bind address ke LAN/internet. Authentication, retry/backoff, dan publisher
backend akan ditambahkan pada Fase 02.
