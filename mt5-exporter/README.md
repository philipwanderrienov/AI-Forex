# MT5 Read-only Exporter

`ForexIntelligenceDataExporter.mq5` adalah EA read-only untuk mengirim data terminal MT5 ke Python bridge lokal. Source tidak mempunyai fungsi membuka, mengubah, atau menutup order.

Versi 0.4 menyimpan nomor urut envelope di Terminal Global Variables MT5 berdasarkan
`SourceInstanceId`. Karena itu melepas/memasang ulang EA atau me-restart terminal tidak
mengulang sequence yang sudah pernah dikirim ke ledger backend. Nomor yang terlewati akibat
kegagalan jaringan aman; sequence tidak boleh di-reset selama `SourceInstanceId` yang sama
masih digunakan.

## Milestone saat ini

EA sekarang mengirim:

- heartbeat `mt5-heartbeat.v1` secara periodik;
- candle final terbaru untuk EURUSD, GBPUSD, EURGBP, EURCHF, dan XAUUSD pada M15, H1,
  dan H4 melalui envelope `mt5-envelope.v1`;
- harga menggunakan precision (`SYMBOL_DIGITS`) broker;
- `tickVolume`, waktu candle, broker symbol, canonical instrument, sequence, batch ID, dan checksum SHA-256 yang divalidasi Python bridge.

Candle indeks `0` tidak dikirim. Exporter mengambil shift `1` melalui `CopyRates` dan
memastikan waktu penutupan sudah lewat. Candle yang sama tidak dikirim ulang selama EA
tetap hidup.

> Catatan timezone: milestone real-time ini mengonversi waktu bar server MT5 menggunakan offset server-ke-UTC saat ini. Mekanisme historical backfill yang DST-aware belum tersedia dan harus diselesaikan sebelum ingestion histori lama diaktifkan.

## Menjalankan milestone

1. Jalankan Python bridge.
2. Tambahkan `http://127.0.0.1:8001` ke daftar allowed WebRequest MT5.
3. Compile `ForexIntelligenceDataExporter.mq5` melalui MetaEditor.
4. Login ke akun **demo** broker dan pasang EA pada satu chart.
5. Bila broker memakai suffix/prefix, ubah kelima input `BrokerSymbol...`, misalnya
   `BrokerSymbolEURUSD=EURUSD.a`; nama instrumen canonical tetap tidak berubah.
6. Periksa tab Experts. Setelah request diterima, EA menulis log
   `Published FINAL <instrument> <timeframe> candle`.
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

Belum tersedia atau belum diverifikasi nyata:

- discovery otomatis suffix/prefix broker;
- ekspor terminal nyata untuk M15/H4 dan empat instrumen selain EURUSD (implementasinya
  sudah tersedia dan kontraknya sudah diuji melalui simulator);
- tick dan account telemetry;
- sequence/checkpoint durable setelah restart EA;
- retry/backoff terjadwal;
- historical backfill DST-aware;
- publisher Python ke backend .NET.

Milestone `EURUSD H1 -> Python validation -> durable spool` sudah terbukti menggunakan akun
demo MT5. Tahap berikutnya adalah memverifikasi seluruh matriks instrumen/timeframe pada
terminal nyata, termasuk disconnect, restart, dan recovery.
