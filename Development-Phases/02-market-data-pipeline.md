# Fase 02 — MetaTrader 5 Market Data Pipeline

## Status implementasi

- Receiver Python localhost menerima heartbeat starter tervalidasi dan batch candle
  `mt5-envelope.v1`. Heartbeat memeriksa versi schema, instance ID terbatas, dan timestamp UTC.
- Bridge menyimpan heartbeat terakhir di memory dan melaporkan freshness terminal melalui
  `/health` sebagai `UNKNOWN`, `HEALTHY`, `WARNING`, atau `STALE` sesuai ambang canonical.
- Health bridge melaporkan depth, kapasitas item/byte, persentase pemakaian, ruang disk bebas,
  dan status ketersediaan durable spool untuk ditampilkan sebagai volume bar pada dashboard.
- Validasi contract-level tersedia untuk field wajib, versi schema, ULID batch, batas record,
  UTC, decimal string, enum canonical, konsistensi alias broker, checksum SHA-256, serta
  invariants OHLC.
- Batch valid disimpan atomik pada durable FIFO spool lokal yang berbatas dan tidak menghapus
  data lama ketika penuh.
- EA masih hanya mengirim heartbeat. Publisher backend, credential bridge, retry/backoff,
  checkpoint, tick/account telemetry, dan data MT5 nyata belum diimplementasikan.

## Tujuan

Mengambil market data real-time dari terminal MetaTrader 5 yang terhubung ke broker pengguna, lalu menormalisasi, memvalidasi, dan menyimpannya sebagai sumber analisis. Dengan demikian harga, spread, simbol, dan histori lebih dekat dengan kondisi eksekusi manual pengguna di broker yang sama.

## Batas arsitektur

```text
Broker → Terminal MetaTrader 5/Wine pada Lubuntu → EA MQL5 read-only
       → HTTP 127.0.0.1 → Python Data Bridge native Linux
       → ASP.NET Core ingestion endpoint → PostgreSQL/Redis
       → Analysis Engine → Dashboard/Notification
```

- Target collector memakai Lubuntu 24.04.4 LTS; MT5 berjalan melalui Wine sesuai panduan resmi MetaTrader. Windows VM/VPS tidak diperlukan.
- EA MQL5 dan Python bridge membentuk **read-only market-data collector**.
- Dilarang memanggil `OrderSend`, mengubah order, atau menutup posisi.
- Backend .NET adalah pemilik validasi canonical, persistence, scoring, dan aturan bisnis.
- Kredensial akun tidak dikirim ke backend. Login dilakukan oleh terminal MT5; bridge hanya membuka koneksi ke terminal yang telah dikonfigurasi.

## Pekerjaan

### 1. Fondasi Python yang ramah pemula

- Ikuti tahap 1–4 pada [Panduan Belajar Python untuk MT5](panduan-belajar-python-mt5.md).
- Gunakan virtual environment dan dependency yang dikunci di `pyproject.toml`.
- Terapkan type hints, formatter/linter, unit test, structured logging, dan configuration dari environment.
- Pisahkan modul koneksi MT5, mapping simbol, normalisasi DTO, HTTP publisher, checkpoint, dan health status.
- Jangan memasukkan token, password, nomor akun, atau alamat backend rahasia ke source code/log.

### 2. EA MQL5 exporter dan discovery broker

- Siapkan Lubuntu dan install MT5 melalui Wine mengikuti [checklist kesiapan runtime](00-lubuntu-mt5-readiness.md), lalu login ke akun demo broker.
- Buat EA `ForexIntelligenceDataExporter.mq5` tanpa fungsi trading.
- Catat versi terminal, broker/server, timezone semantics, dan status koneksi yang tidak sensitif.
- Discover nama simbol broker menggunakan fungsi simbol MQL5; jangan menganggap semua broker memakai `EURUSD` tanpa suffix/prefix.
- Buat mapping konfigurasi, misalnya `EURUSD.a → EURUSD`, tanpa menyebarkan nama provider ke domain.
- Pastikan lima instrumen MVP tersedia dan dapat dipilih melalui Market Watch/`SymbolSelect`.
- Ambil metadata `digits`, `point`, ukuran kontrak, volume min/max/step, mata uang base/profit/margin, dan trading status.
- Ambil account telemetry read-only melalui `AccountInfoDouble/String`; dilarang mengirim account number, nama, password, atau credential.
- Agregasikan realized P/L hari ini dari deal history secara read-only pada trade transaction dan rekonsiliasi periodik, terpisah dari `ACCOUNT_PROFIT`.

### 3. Akuisisi tick dan candle

- Ambil latest tick melalui `SymbolInfoTick` untuk bid, ask, last, dan waktu.
- Ambil tick historis dengan `CopyTicks/CopyTicksRange` bila tersedia.
- Ambil candle `M15`, `H1`, dan `H4` menggunakan `CopyRates`.
- Perlakukan `tick_volume` sebagai aktivitas tick broker, bukan volume transaksi forex global.
- `real_volume` bersifat opsional dan tidak boleh diasumsikan tersedia.
- Atur `Max. bars in chart` terminal agar histori yang dibutuhkan dapat diambil; kedalaman histori tetap bergantung pada broker.
- Semua waktu dikonversi dan dikirim sebagai UTC ISO-8601.
- Candle indeks `0` umumnya masih berjalan; hanya candle yang batas waktunya telah lewat dan lolos finality check yang diberi status `FINAL`.

### 4. Kontrak EA → Python bridge → backend

- EA mengirim DTO versioned ke Python bridge localhost melalui `WebRequest`; alamat harus ditambahkan manual ke allowed URLs terminal.
- Karena `WebRequest` synchronous, EA mengirim batch terbatas melalui `OnTimer`, bukan melakukan request pada setiap tick.
- Batch heartbeat memuat latest account telemetry dengan cadence fase 00; payload membedakan `ACCOUNT_SNAPSHOT` dari tick/candle.
- Python memvalidasi envelope, menyediakan local spool/retry, lalu mengirim DTO yang sama melalui HTTPS ke ingestion endpoint internal.
- Satu batch memuat `source`, `brokerServer`, simbol broker, instrument canonical/type, timeframe, OHLC, tick/real volume, spread, event time, received time, dan sequence/checkpoint.
- Gunakan idempotency key agar retry tidak membuat duplikat.
- Autentikasi machine-to-machine menggunakan credential bridge terpisah dari JWT pengguna dashboard.
- Terapkan timeout, retry eksponensial dengan jitter, batch size terbatas, dan local spool ketika backend sementara tidak tersedia.
- Local spool tidak boleh tumbuh tanpa batas dan harus dapat direplay berurutan setelah koneksi pulih.

### 5. Normalisasi

- Mapping simbol broker menjadi `TradingInstrument` canonical: `EURUSD`, `GBPUSD`, `EURGBP`, `EURCHF`, `XAUUSD`.
- Normalisasi timeframe, precision, pip/point, bid/ask/mid, dan spread.
- Simpan `source=MT5`, identitas broker/server yang aman, serta simbol aslinya untuk audit.
- Bedakan `eventTime` dari MT5, `receivedAt` di bridge, dan `ingestedAt` di backend.
- Gunakan decimal untuk harga pada backend; jangan mengandalkan perbandingan float mentah untuk invariants harga.

### 6. Validasi kualitas data

- Tolak candle dengan `high < max(open, close)` atau `low > min(open, close)`.
- Tolak timestamp mundur, timeframe salah, harga non-positive, dan spread negatif.
- Deteksi duplikat, gap candle, tick terlambat, market closed, dan lonjakan spread.
- Bedakan `NO_TICK`, `TERMINAL_DISCONNECTED`, `SYMBOL_DISABLED`, `MARKET_CLOSED`, dan `BACKEND_UNAVAILABLE`.
- Jangan membuat candle sintetis diam-diam untuk menutup gap.
- Saat reconnect, backfill dari checkpoint terakhir sebelum real-time publishing dilanjutkan.

### 7. Persistence dan caching

- Buat unique key `(source, broker_server, pair, timeframe, timestamp)`.
- Simpan candle final secara durable di PostgreSQL.
- Simpan latest tick/freshness di Redis hanya sebagai cache; data keputusan pengguna tidak boleh bergantung pada Redis.
- Buat indeks untuk instrument/timeframe/range dan kebijakan retention sesuai fase 00.
- Simpan watermark/checkpoint per broker, pair, dan timeframe.

### 8. Worker dan scheduling

- Poll latest tick sesuai target freshness tanpa busy loop.
- Periksa final candle segera setelah boundary M15/H1/H4 dengan grace period yang ditetapkan.
- Hindari overlap job dan buat pemrosesan idempotent.
- Sinkronkan waktu Lubuntu dengan NTP dan ukur clock drift.
- Hentikan publikasi signal baru ketika terminal/bridge tidak sehat, tetapi pertahankan dashboard status dan histori.

### 9. Observability

- Log terstruktur: connection state, symbol, timeframe, batch ID, jumlah record, checkpoint, latency, dan error code; tanpa credential.
- Metric: tick age, candle finalization delay, gap, duplicate, rejected record, bridge/backend latency, spool depth, reconnect count, dan clock drift.
- Metric account telemetry: snapshot age, publish latency, material-change count, dan stale duration; nilai balance/equity aktual tidak ditulis ke metric label atau log.
- Health status terpisah untuk terminal, broker connection, bridge, backend ingestion, database, dan freshness setiap pair.
- Alert bila hard freshness threshold fase 00 terlewati saat pasar seharusnya buka.

## Deliverables

- EA MQL5 exporter read-only pada MT5/Wine dan Python Data Bridge native Linux yang kecil, terdokumentasi, dan dapat dijalankan dari satu perintah.
- Mapping simbol nyata dari broker pengguna ke lima instrumen canonical.
- Historical backfill dan ingestion real-time untuk `M15`, `H1`, dan `H4`.
- Endpoint ingestion .NET, persistence, checkpoint, serta dashboard health.
- Runbook menjalankan terminal, bridge, reconnect, backfill, dan rotasi credential.
- Catatan belajar per tahap dan glossary Python sederhana untuk pemilik proyek.

## Pengujian

- Unit test normalisasi payload tanpa terminal MT5.
- Adapter test terhadap EA pada terminal MT5 demo/Wine di Lubuntu yang berjalan.
- Bandingkan tick, candle, spread, dan timestamp sampel dengan chart broker pada terminal.
- Bandingkan balance, equity, floating P/L, margin, dan account currency dengan nilai terminal tanpa mengekspos identitas akun.
- Uji suffix/prefix simbol, perbedaan digits, market closed, no tick, reconnect, backend down, replay spool, duplicate, dan gap.
- Pastikan source scan atau policy test gagal jika exporter mengandung `OrderSend` atau fungsi perubahan posisi/order.
- Soak test minimum lima hari trading pada Lubuntu, termasuk restart/reconnect dan window `08:00–12:59 Europe/London`.

## Kriteria selesai

- Untuk sampel yang disepakati, data tersimpan sama dengan data terminal setelah normalisasi precision/timezone.
- Candle partial tidak pernah dipakai sebagai candle final dalam scoring.
- Restart terminal, bridge, dan backend tidak membuat duplikat atau kehilangan gap tanpa deteksi.
- Kondisi stale/disconnected memaksa `WAIT` dan terlihat jelas di dashboard.
- Pengguna dapat menjelaskan dan menjalankan script bridge dasar dengan panduan proyek.
- Tidak ada jalur kode bridge yang dapat mengeksekusi order.

## Referensi resmi

- [Instalasi MetaTrader 5 pada Linux](https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux)
- [MQL5 `WebRequest`](https://www.mql5.com/en/docs/network/webrequest)
- [MQL5 `CopyRates`](https://www.mql5.com/en/docs/series/copyrates)
- [MQL5 `CopyTicksRange`](https://www.mql5.com/en/docs/series/copyticksrange)
