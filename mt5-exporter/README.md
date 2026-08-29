# MT5 Read-only Exporter

`ForexIntelligenceDataExporter.mq5` adalah EA read-only untuk mengirim data terminal MT5 ke Python bridge lokal. Source tidak mempunyai fungsi membuka, mengubah, atau menutup order.

Versi 0.5 menyimpan nomor urut envelope dan checkpoint candle per instrumen/timeframe di
Terminal Global Variables MT5 berdasarkan
`SourceInstanceId`. Karena itu melepas/memasang ulang EA atau me-restart terminal tidak
mengulang sequence dan dapat melanjutkan candle yang tertinggal. Nomor yang terlewati akibat
kegagalan jaringan aman; state tersebut tidak boleh di-reset selama `SourceInstanceId` yang
sama masih digunakan.

## Milestone saat ini

EA sekarang mengirim:

- heartbeat `mt5-heartbeat.v1` secara periodik;
- candle final terbaru untuk EURUSD, GBPUSD, EURGBP, EURCHF, dan XAUUSD pada M15, H1,
  dan H4 melalui envelope `mt5-envelope.v1`;
- harga menggunakan precision (`SYMBOL_DIGITS`) broker;
- `tickVolume`, waktu candle, broker symbol, canonical instrument, sequence, batch ID, dan checksum SHA-256 yang divalidasi Python bridge.

Candle indeks `0` tidak dikirim. Pada pemakaian pertama, exporter mengirim candle FINAL terbaru
dan membentuk checkpoint. Setelah restart/reconnect, exporter mencari checkpoint tersebut dalam
histori broker dan mengirim candle sesudahnya secara kronologis, maksimal
`MaxBackfillBarsPerSeries` (default 32) per seri pada setiap siklus. Checkpoint baru disimpan
setelah bridge memberi HTTP 202, yaitu setelah envelope aman di durable spool.

> Catatan timezone: versi ini hanya melakukan backfill otomatis ketika offset UTC broker sama
> dengan offset yang tersimpan bersama checkpoint. Jika offset berubah—misalnya outage melewati
> pergantian DST—seri tersebut dihentikan dengan warning agar tidak menghasilkan timestamp yang
> keliru atau menyembunyikan gap. Normalisasi DST historis penuh tetap pekerjaan berikutnya.

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
- tick dan account telemetry;
- retry/backoff terjadwal;
- historical backfill DST-aware;
- discovery otomatis timezone/DST broker.

Seluruh matriks lima instrumen × tiga timeframe serta restart-safe sequence sudah terbukti pada
terminal demo nyata. Versi 0.5 berikutnya perlu diverifikasi dengan restart singkat dan beberapa
candle yang tertinggal sebelum pengembangan timezone/DST historis penuh.
