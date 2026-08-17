# Fase 06 — API dan Dashboard

## Tujuan

Menyediakan Technical MVP yang dapat digunakan: pengguna melihat kondisi pasar, membandingkan pair, memahami alasan rekomendasi, dan memantau kesegaran data.

## Pekerjaan backend

### 1. API contracts

- Endpoint market overview, account telemetry, candle, currency strength forex, instrument ranking, instrument detail, opportunity, dan risk assessment.
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

### 4. Time synchronization

- Sediakan UTC server time pada bootstrap/health response beserta `generatedAt` agar frontend dapat menghitung offset terhadap clock perangkat.
- Jangan membuat endpoint yang dipanggil setiap detik; clock UI berjalan dengan monotonic timer dan melakukan resync saat startup, reconnect, visibility kembali aktif, serta interval yang dikonfigurasi.
- Response bisnis tetap menyertakan timestamp UTC/as-of masing-masing dan tidak bergantung pada clock header.

## Pekerjaan frontend Angular

- Application shell, routing, theme, loading, empty, dan error states.
- Header global menampilkan clock real-time London dan Jakarta dengan tanggal, detik, offset `GMT+00:00/GMT+01:00` untuk London dan `GMT+07:00` untuk Jakarta, serta status window London `ACTIVE/CLOSED`.
- Header/account widget menampilkan balance, equity, floating P/L, realized P/L hari ini, used/free margin, margin level, account currency, `asOf`, dan badge `GOOD/WARNING/STALE/UNAVAILABLE` dari MT5.
- Nilai finansial disamarkan saat privacy mode aktif dan tidak pernah dimasukkan ke URL, analytics pihak ketiga, atau client log.
- Dashboard market overview serta status terminal MT5, koneksi broker, Python bridge, dan freshness per pair.
- Instrument scanner dengan sort/filter berdasarkan type, score, regime, dan risk.
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
- Test terminal MT5/bridge disconnected serta pastikan UI memblokir rekomendasi baru tanpa kehilangan akses ke histori.
- Test clock pada boundary `07:59:59`, `08:00:00`, `12:59:59`, dan `13:00:00` waktu London; transisi GMT↔BST; pergantian tanggal yang berbeda antara London/Jakarta; tab sleep/resume; serta device clock drift.
- Test account telemetry berubah, terminal disconnect, snapshot stale, privacy mode, account currency, dan pastikan Risk Engine memakai snapshot ID/nilai yang sama dengan yang ditampilkan.
- Basic accessibility dan performance test.

## Kriteria selesai

- Pengguna dapat menyelesaikan alur utama tanpa membaca database/log.
- Nilai dan alasan di UI sama dengan snapshot backend.
- Stale/error/insufficient-data tidak pernah tampil sebagai rekomendasi normal.
- Technical MVP berhasil didemokan dari ingestion sampai dashboard.
- Header memperlihatkan waktu London/Jakarta yang benar dan status window konsisten dengan rule fase 00 tanpa melakukan polling setiap detik.
