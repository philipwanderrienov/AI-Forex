# Fase 00 — Discovery dan Spesifikasi

## Tujuan

Mengubah visi arsitektur menjadi definisi produk dan aturan bisnis yang tidak ambigu. Fase ini mencegah setiap modul menggunakan arti pair, waktu, skor, dan sinyal yang berbeda.

## Pekerjaan

### 1. Tetapkan scope produk

- Putuskan bahwa versi awal merupakan alat analisis/decision-support, bukan eksekutor order otomatis.
- Tentukan pengguna utama, kebutuhan dashboard, dan alur pengguna dari membuka scanner sampai menyimpan trade setup.
- Pilih pair dan timeframe MVP, misalnya major pairs pada `M15`, `H1`, dan `H4`.
- Tentukan jam operasi, kebutuhan real-time, dan batas keterlambatan data yang masih diterima.
- Tulis fitur yang masuk dan tidak masuk MVP.

### 2. Definisikan bahasa domain

- Definisikan `Candle`, `CurrencyPair`, `TechnicalSnapshot`, `EconomicEvent`, `NewsImpact`, `TradeSignal`, `TradeSetup`, `RiskAssessment`, dan `TradeOutcome`.
- Tetapkan enum canonical untuk timeframe, trend, market regime, signal direction, dan severity.
- Bedakan fakta pasar, hasil analisis, opportunity, rekomendasi, dan outcome.
- Tetapkan UTC untuk penyimpanan dan timezone pengguna hanya untuk tampilan.

### 3. Susun kontrak scoring

- Tentukan rentang setiap skor, misalnya `-10` sampai `+10`.
- Definisikan bobot indikator dan cara menghitung skor gabungan.
- Tentukan aturan konflik antar-timeframe dan antar-engine.
- Tetapkan threshold `BUY`, `SELL`, dan `WAIT`.
- Definisikan confidence secara matematis; jangan menyamakannya dengan probabilitas menang sebelum dikalibrasi.
- Tentukan perilaku ketika data hilang, stale, atau kualitasnya rendah.

### 4. Pilih provider dan batas operasional

- Pilih satu market-data provider utama untuk MVP dan dokumentasikan rate limit serta lisensinya.
- Tentukan mapping simbol provider ke simbol canonical.
- Catat interval candle, histori yang tersedia, spread, volume, dan timestamp semantics.
- Pilih sumber economic calendar dan berita untuk fase lanjutan.

### 5. Tetapkan non-functional requirements

- Target latency ingestion, scanner, dan API.
- Target availability, retention data, serta recovery point/recovery time.
- Aturan keamanan secret, autentikasi, authorization, dan audit.
- Target jumlah pair, timeframe, pengguna, dan event per hari.

## Deliverables

- Product Requirements Document ringkas.
- Glosarium domain dan diagram alur keputusan.
- Data dictionary dan contoh JSON setiap kontrak.
- Dokumen formula scoring versi 1.
- Daftar provider beserta batas, biaya, dan fallback.
- Backlog MVP yang terurut serta acceptance criteria.

## Pengujian/validasi

- Review contoh satu candle hingga menjadi trade setup secara manual.
- Uji formula pada contoh bullish, bearish, conflicting, dan insufficient-data.
- Pastikan stakeholder dapat menjelaskan arti setiap skor dengan interpretasi yang sama.

## Kriteria selesai

- Scope MVP dan non-goals disepakati.
- Tidak ada tipe inti atau formula skor yang masih memiliki dua interpretasi.
- Provider, pair, timeframe, dan target latency MVP sudah dipilih.
- Backlog fase 01–06 dapat dikerjakan tanpa keputusan produk besar yang tertunda.

