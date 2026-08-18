# Roadmap Pengembangan Forex Intelligence

Dokumen ini menerjemahkan rancangan pada folder `Notes` menjadi fase pengembangan yang dapat dikerjakan dan diverifikasi. Urutan fase dibuat berdasarkan dependensi: data yang bersih dibangun sebelum analisis, analisis dibangun sebelum rekomendasi, dan rekomendasi dibuktikan melalui backtesting sebelum sistem diperkeras untuk produksi.

## Prinsip pelaksanaan

- Mulai sebagai **modular monolith** agar domain mudah diuji dan deployment tetap sederhana.
- Sumber market data real-time MVP adalah terminal **MetaTrader 5** yang terhubung ke broker pengguna.
- Development memakai kebijakan **free-first**: pilih software open-source/free-tier dan hindari lisensi atau layanan berbayar selama kebutuhan MVP masih dapat dipenuhi secara aman.
- Coding dilakukan pada macOS. Seluruh runtime MVP memakai laptop fisik Lubuntu 24.04.4 LTS terpisah: MT5/Wine, EA read-only, Python bridge, backend .NET, database/cache, dan Angular.
- Layanan gratis tidak boleh dianggap mempunyai SLA. Semua integrasi eksternal dibungkus adapter agar dapat dipindahkan bila kuota atau ketentuannya berubah.
- Semua waktu disimpan dalam UTC dan semua instrumen memakai simbol canonical, misalnya `EURUSD` dan `XAUUSD`.
- Perhitungan teknikal, scoring, dan risiko harus deterministik serta dapat diuji tanpa AI.
- AI membantu klasifikasi dan penjelasan, bukan menjadi satu-satunya penentu keputusan.
- Setiap sinyal harus dapat ditelusuri ke data, aturan, konfigurasi, dan versi model yang menghasilkannya.
- Selesaikan acceptance criteria suatu fase sebelum menjadikan fase berikutnya sebagai fokus utama.

## Urutan fase

| Fase | Fokus | Hasil utama |
|---|---|---|
| [00](00-discovery-dan-spesifikasi.md) | Discovery dan spesifikasi | Scope, aturan bisnis, kontrak data, dan acceptance criteria |
| [00A](00-data-dictionary.md) | Data dictionary dan kontrak JSON | Field canonical, enum, invariants, payload antarkomponen, dan contract testing |
| [00B](00-scoring-rules-v1.md) | Tabel aturan scoring v1 | Kondisi indikator, skor numerik, konflik timeframe, confidence, dan fixture |
| [00C](00-risk-rules-v1.md) | Tabel aturan Risk Engine v1 | Stop-loss, target, sizing MT5, margin, exposure, circuit breaker, dan fixture |
| [00D](00-lubuntu-mt5-readiness.md) | Kesiapan MT5 pada Lubuntu | Instalasi aman, topologi runtime, spike, soak test, dan operasi collector |
| [01](01-fondasi-solution.md) | Fondasi solution | Solution .NET, modul, testing, database, dan standar proyek |
| [02](02-market-data-pipeline.md) | MT5 market data pipeline | Tick/candle broker tervalidasi dan tersimpan melalui Python bridge |
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
- Pengiriman, modifikasi, atau penutupan order melalui Python/MQL5; bridge MVP hanya boleh membaca market data.
- Windows VM/VPS berbayar; hanya dipertimbangkan jika soak test membuktikan MT5/Wine pada Lubuntu tidak memenuhi target stabilitas.

## Jalur belajar Python

Implementasi bridge dikerjakan bersama jalur belajar bertahap pada [Panduan Belajar Python untuk MT5](panduan-belajar-python-mt5.md). Setiap tahap menghasilkan program kecil yang dapat dijalankan dan diuji sebelum masuk ke pipeline produksi.

## Kebijakan free-first

Baseline development tidak memerlukan pembelian software atau server:

| Kebutuhan | Pilihan awal gratis |
|---|---|
| Editor dan source control | VS Code, Git |
| Backend | .NET SDK/ASP.NET Core |
| MT5 data export | Terminal MT5/Wine pada Lubuntu + EA MQL5 read-only |
| Data bridge dan pembelajaran | Python native Linux; coding dapat dilakukan dari macOS |
| Frontend | Angular |
| Database/cache | PostgreSQL dan Redis/Valkey lokal |
| API documentation/testing | OpenAPI dan tool open-source |
| Hosting percobaan | Lubuntu lokal terlebih dahulu; layanan free-tier hanya setelah diperlukan |
| Economic calendar | Free API yang lolos spike dan syarat lisensinya |
| AI/LLM | OpenAI API berbayar milik pengguna; penggunaannya dibatasi, diaudit, dan tidak menjadi dependency Technical MVP |

Aturan biaya:

- Tidak boleh mengaktifkan subscription, resource berbayar, atau API yang dapat menagih otomatis tanpa persetujuan pemilik produk.
- Pengecualian yang telah disetujui: pemakaian OpenAI API dari project key khusus aplikasi, dengan budget/usage cap dan observability biaya.
- Semua free tier harus mempunyai usage cap, alert, dan fallback `UNAVAILABLE/DEGRADED`.
- Kartu pembayaran, bila diwajibkan penyedia free tier, bukan izin untuk menghasilkan biaya.
- “Gratis” tidak menghapus biaya listrik, koneksi internet, domain opsional, backup eksternal, maupun keterbatasan availability.
- Saat kebutuhan produksi tidak dapat dipenuhi secara aman oleh opsi gratis, buat keputusan biaya eksplisit beserta alternatif; jangan menurunkan keamanan atau integritas data secara diam-diam.
