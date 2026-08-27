# MT5 Read-only Exporter

`ForexIntelligenceDataExporter.mq5` adalah EA read-only untuk mengirim data terminal MT5 ke Python bridge lokal. Source tidak mempunyai fungsi membuka, mengubah, atau menutup order.

## Milestone saat ini

EA sekarang mengirim:

- heartbeat `mt5-heartbeat.v1` secara periodik;
- satu candle final `EURUSD H1` terbaru melalui envelope `mt5-envelope.v1`;
- harga menggunakan precision (`SYMBOL_DIGITS`) broker;
- `tickVolume`, waktu candle, broker symbol, canonical instrument, sequence, batch ID, dan checksum SHA-256 yang divalidasi Python bridge.

Candle indeks `0` tidak dikirim. Exporter mengambil shift `1` melalui `CopyRates`, sehingga milestone ini hanya mengirim candle H1 yang sudah selesai. Candle yang sama tidak dikirim ulang selama EA tetap hidup.

> Catatan timezone: milestone real-time ini mengonversi waktu bar server MT5 menggunakan offset server-ke-UTC saat ini. Mekanisme historical backfill yang DST-aware belum tersedia dan harus diselesaikan sebelum ingestion histori lama diaktifkan.

## Menjalankan milestone

1. Jalankan Python bridge.
2. Tambahkan `http://127.0.0.1:8001` ke daftar allowed WebRequest MT5.
3. Compile `ForexIntelligenceDataExporter.mq5` melalui MetaEditor.
4. Login ke akun **demo** broker dan pasang EA pada satu chart.
5. Bila broker memakai suffix/prefix, ubah input `BrokerSymbol`, misalnya `EURUSD.a`; `CanonicalInstrument` tetap `EURUSD`.
6. Periksa tab Experts. Setelah request diterima, EA menulis log `Published FINAL EURUSD H1 candle`.
7. Periksa `GET http://127.0.0.1:8001/health`; depth spool harus bertambah setelah batch candle baru diterima.

`RequestTimeoutMilliseconds` default ke 5000 ms agar durable spool write dan `fsync` pada
collector yang lambat tidak mudah dibaca sebagai timeout oleh WebRequest MT5/Wine. Respons
di luar HTTP 2xx dicatat bersama MQL5 error, response body, dan headers untuk diagnosis.

Endpoint yang digunakan:

```text
POST /v1/mt5/heartbeat
POST /v1/mt5/envelopes
GET  /health
```

## Batas milestone

Belum tersedia:

- discovery otomatis suffix/prefix broker;
- M15 dan H4;
- lima instrumen MVP sekaligus;
- tick dan account telemetry;
- sequence/checkpoint durable setelah restart EA;
- retry/backoff terjadwal;
- historical backfill DST-aware;
- publisher Python ke backend .NET.

Tahap berikutnya dilakukan setelah `EURUSD H1 → Python validation → durable spool` terbukti bekerja menggunakan data nyata dari akun demo MT5.
