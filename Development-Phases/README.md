# Roadmap Pengembangan Forex Intelligence

Dokumen ini menerjemahkan rancangan pada folder `Notes` menjadi fase pengembangan yang dapat dikerjakan dan diverifikasi. Urutan fase dibuat berdasarkan dependensi: data yang bersih dibangun sebelum analisis, analisis dibangun sebelum rekomendasi, dan rekomendasi dibuktikan melalui backtesting sebelum sistem diperkeras untuk produksi.

## Prinsip pelaksanaan

- Mulai sebagai **modular monolith** agar domain mudah diuji dan deployment tetap sederhana.
- Semua waktu disimpan dalam UTC dan semua pair memakai simbol canonical, misalnya `EURUSD`.
- Perhitungan teknikal, scoring, dan risiko harus deterministik serta dapat diuji tanpa AI.
- AI membantu klasifikasi dan penjelasan, bukan menjadi satu-satunya penentu keputusan.
- Setiap sinyal harus dapat ditelusuri ke data, aturan, konfigurasi, dan versi model yang menghasilkannya.
- Selesaikan acceptance criteria suatu fase sebelum menjadikan fase berikutnya sebagai fokus utama.

## Urutan fase

| Fase | Fokus | Hasil utama |
|---|---|---|
| [00](00-discovery-dan-spesifikasi.md) | Discovery dan spesifikasi | Scope, aturan bisnis, kontrak data, dan acceptance criteria |
| [01](01-fondasi-solution.md) | Fondasi solution | Solution .NET, modul, testing, database, dan standar proyek |
| [02](02-market-data-pipeline.md) | Market data pipeline | Candle tervalidasi dan tersimpan dari satu provider |
| [03](03-technical-analysis.md) | Technical analysis | Indikator, market structure, dan technical score |
| [04](04-market-brain-dan-pair-scanner.md) | Market Brain dan scanner | Currency strength, regime, ranking, dan opportunity |
| [05](05-risk-engine.md) | Risk engine | SL/TP, position sizing, kelayakan, dan risk warning |
| [06](06-api-dan-dashboard.md) | API dan dashboard | API, SignalR, dashboard, scanner, dan detail setup |
| [07](07-fundamental-dan-news-ai.md) | Fundamental, berita, dan AI | Economic intelligence dan klasifikasi berita terstruktur |
| [08](08-backtesting-dan-trade-journal.md) | Backtesting dan journal | Evaluasi historis, metrik strategi, dan pencatatan outcome |
| [09](09-production-hardening.md) | Production hardening | Security, observability, resilience, deployment, dan operasi |

## Milestone yang disarankan

### Milestone A — Technical MVP

Fase 00–06. Pengguna sudah dapat melihat data pasar, ranking pair, alasan teknikal, dan rekomendasi risiko melalui dashboard.

### Milestone B — Intelligence MVP

Fase 07. Analisis teknikal diperkaya data ekonomi dan berita, dengan AI yang menghasilkan structured output dan tetap memiliki guardrail.

### Milestone C — Validated Release

Fase 08–09. Strategi telah diuji historis, hasil trading dapat dipantau, dan aplikasi siap dioperasikan dengan kontrol produksi.

## Definition of Done umum

Sebuah pekerjaan dianggap selesai jika:

- implementasi dan migrasi database tersedia;
- unit/integration test relevan lulus;
- error path, retry, dan validasi input ditangani;
- logging tidak membocorkan secret atau data sensitif;
- kontrak API/data terdokumentasi;
- metric penting dapat diamati;
- dokumentasi operasional diperbarui;
- demo acceptance criteria berhasil dijalankan.

## Hal yang sengaja ditunda

- Multi-provider sebelum adapter provider pertama stabil.
- Microservices dan RabbitMQ sebelum beban atau independensi deployment membutuhkannya.
- Vector database sebelum kebutuhan semantic retrieval terbukti.
- Auto-execution order; roadmap awal hanya decision-support.
- Machine learning prediktif sebelum baseline rule-based mempunyai data evaluasi yang cukup.

