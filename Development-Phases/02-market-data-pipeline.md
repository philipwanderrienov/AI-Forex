# Fase 02 — Market Data Pipeline

## Tujuan

Mengambil, menormalisasi, memvalidasi, dan menyimpan market data yang dapat dipercaya. Semua analisis berikutnya bergantung pada kualitas fase ini.

## Pekerjaan

### 1. Adapter provider pertama

- Implementasikan client untuk satu provider, misalnya OANDA.
- Tangani authentication, timeout, rate limit, retry dengan backoff, dan cancellation.
- Pisahkan DTO provider dari model canonical aplikasi.
- Catat request ID provider tanpa mencatat credential.

### 2. Normalisasi

- Mapping simbol provider menjadi `CurrencyPair` canonical.
- Konversi timestamp ke UTC dan validasi batas candle.
- Tentukan apakah harga menggunakan bid, ask, atau mid.
- Normalisasi precision dan volume semantics.
- Tandai candle sebagai incomplete atau final.

### 3. Validasi kualitas data

- Validasi `Low <= Open/Close <= High` dan nilai harga positif.
- Deteksi duplikat, gap, data terlambat, urutan timestamp salah, dan candle stale.
- Simpan status kualitas serta alasan rejection.
- Buat rekonsiliasi untuk mengisi gap secara aman.

### 4. Persistence dan caching

- Buat unique key `(provider, pair, timeframe, timestamp)`.
- Gunakan upsert idempotent agar retry tidak menggandakan data.
- Buat indeks untuk query pair/timeframe/range.
- Tambahkan Redis hanya untuk latest price/candle jika pengukuran membuktikan kebutuhan real-time.

### 5. Worker ingestion

- Jadwalkan historical backfill dan incremental polling/streaming.
- Simpan watermark/checkpoint per pair dan timeframe.
- Hindari overlap job dan buat shutdown yang graceful.
- Publikasikan internal event `CandleFinalized` setelah transaksi penyimpanan berhasil.

### 6. Observability

- Metric: jumlah candle masuk, ditolak, duplikat, gap, latency, dan usia data terakhir.
- Alert bila data berhenti atau error provider melewati threshold.
- Dashboard operasional sederhana untuk kesehatan ingestion.

## Deliverables

- Historical backfill dan ingestion berkala untuk pair/timeframe MVP.
- Tabel candle canonical dan indeksnya.
- Laporan/metric kualitas data.
- Endpoint/query untuk mengambil candle historis dan latest candle.

## Pengujian

- Contract test adapter menggunakan contoh payload provider.
- Integration test idempotency dan unique constraint.
- Test DST/timezone, timeout, retry, rate limit, gap, dan malformed response.
- Bandingkan sampel candle tersimpan dengan data provider.

## Kriteria selesai

- Backfill dapat diulang tanpa duplikasi.
- Ingestion pulih setelah restart dari checkpoint terakhir.
- Gap dan stale data terdeteksi, bukan diproses diam-diam.
- Data MVP tersedia stabil selama periode burn-in yang disepakati.

