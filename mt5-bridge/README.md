# MT5 Python Bridge

Bridge ini berjalan native di Lubuntu dan hanya menerima data dari EA melalui `127.0.0.1`. Starter Fase 01 belum meneruskan data ke backend dan belum menyimpan payload.

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

Menjalankan test:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Jangan mengubah bind address ke LAN/internet. Authentication, spool, retry, dan publisher backend akan ditambahkan pada Fase 02.
