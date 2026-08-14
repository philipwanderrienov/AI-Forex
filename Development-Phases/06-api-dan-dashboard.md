# Fase 06 — API dan Dashboard

## Tujuan

Menyediakan Technical MVP yang dapat digunakan: pengguna melihat kondisi pasar, membandingkan pair, memahami alasan rekomendasi, dan memantau kesegaran data.

## Pekerjaan backend

### 1. API contracts

- Endpoint market overview, candle, currency strength, pair ranking, pair detail, opportunity, dan risk assessment.
- Pagination/filtering untuk data historis dan berita.
- Gunakan DTO khusus API; jangan mengekspos entity persistence langsung.
- Dokumentasikan OpenAPI, error code, timezone, dan units.

### 2. Application queries

- Optimalkan read model agar dashboard tidak melakukan banyak request kecil.
- Terapkan caching hanya pada query yang aman dan memiliki invalidation jelas.
- Sertakan `asOf`, `dataFreshness`, dan version pada response.
- Tambahkan rate limiting dan request correlation.

### 3. Real-time update

- Gunakan SignalR untuk latest price, ranking update, dan data-health warning.
- Definisikan event contract dan versioning.
- Tangani reconnect, duplicate event, dan fallback polling.
- Jangan mengirim seluruh dataset pada setiap perubahan kecil.

## Pekerjaan frontend Angular

- Application shell, routing, theme, loading, empty, dan error states.
- Dashboard market overview dan status provider.
- Pair scanner dengan sort/filter berdasarkan score, regime, dan risk.
- Currency strength visualization.
- Halaman detail pair: candle chart, indikator, score breakdown, evidence, serta setup.
- Tampilkan `WAIT` dan alasan penolakan dengan bobot visual yang sama jelasnya dengan BUY/SELL.
- Format waktu sesuai timezone pengguna sambil mempertahankan UTC di API.
- Responsive layout dan dasar accessibility.

## Security

- Tambahkan authentication jika aplikasi multi-user atau dapat diakses publik.
- Authorization untuk konfigurasi/admin.
- CORS, secure headers, input validation, dan secret management.
- Disclaimer bahwa output adalah alat analisis, sesuai konteks penggunaan aplikasi.

## Pengujian

- API integration dan contract test.
- Component test untuk state penting UI.
- End-to-end test: membuka scanner → memilih pair → membaca setup/risk.
- Test reconnect SignalR dan stale-data warning.
- Basic accessibility dan performance test.

## Kriteria selesai

- Pengguna dapat menyelesaikan alur utama tanpa membaca database/log.
- Nilai dan alasan di UI sama dengan snapshot backend.
- Stale/error/insufficient-data tidak pernah tampil sebagai rekomendasi normal.
- Technical MVP berhasil didemokan dari ingestion sampai dashboard.

