# Fase 01 — Fondasi Solution

## Status implementasi

- Bootstrap dimulai pada 18 Agustus 2026 menggunakan .NET 10.
- Struktur modular monolith, project references, Controller, Service/Interface, repository spesifik, EF Core DbContext, Worker, dan tiga project test sudah tersedia.
- Python bridge serta EA read-only mempunyai starter heartbeat localhost; integrasi tick/candle tetap pekerjaan Fase 02.
- Initial migration, script SQL native PostgreSQL, dan database readiness health check sudah diverifikasi terhadap PostgreSQL 18 lokal.
- JWT dan pipeline CI masih perlu diselesaikan sebelum Fase 01 ditutup.

## Tujuan

Membangun kerangka aplikasi yang dapat dikembangkan, diuji, dan dijalankan secara konsisten. Fase awal menggunakan modular monolith; pemisahan service dilakukan kemudian jika terbukti perlu.

## Struktur awal

```text
src/
├── ForexIntelligence.Api
├── ForexIntelligence.Application
├── ForexIntelligence.Domain
├── ForexIntelligence.Infrastructure
└── ForexIntelligence.Worker
tests/
├── ForexIntelligence.Domain.Tests
├── ForexIntelligence.Application.Tests
└── ForexIntelligence.IntegrationTests
mt5-bridge/
├── src/
├── tests/
├── pyproject.toml
└── .env.example
mt5-exporter/
└── ForexIntelligenceDataExporter.mq5
```

## Pekerjaan

### 1. Bootstrap proyek

- Buat solution .NET dan project sesuai struktur.
- Terapkan dependency direction: Domain tidak bergantung pada Infrastructure atau API.
- Aktifkan nullable reference types, analyzers, formatting, dan warnings yang relevan.
- Buat konfigurasi per environment tanpa menyimpan secret di repository.
- Siapkan Python environment terisolasi untuk `mt5-bridge`; backend bisnis tetap .NET.
- Pin versi Python dan dependency, serta sediakan perintah setup yang dapat diikuti pemula.

### 2. Implementasikan domain foundation

- Buat value object `Currency`, `TradingInstrument`, `Timeframe`, `Money`, dan `Percentage`; `TradingInstrument` membedakan forex dari precious metal.
- Buat entity awal `Candle` beserta invariants OHLC.
- Tambahkan domain exception dan result/error model.
- Hindari dependensi EF Core pada model domain bila tidak diperlukan.

### 3. Siapkan persistence

- Jalankan PostgreSQL native pada mesin lokal/Lubuntu dan kelola schema melalui script SQL versioned yang sinkron dengan EF migration.
- Konfigurasikan EF Core, migration, naming convention, dan UTC handling.
- Buat repository hanya pada aggregate/query yang membutuhkannya; hindari generic repository tanpa tujuan.
- Siapkan seeding untuk data referensi, bukan data pasar palsu di produksi.

### 4. Cross-cutting concerns

- Structured logging dengan correlation ID.
- Global exception handling dan Problem Details.
- Health checks untuk aplikasi dan database.
- Validation pipeline dan configuration validation saat startup.
- OpenAPI untuk API awal.

### 5. Quality gate

- Unit test untuk value objects dan invariants.
- Integration test menggunakan database PostgreSQL nyata yang terisolasi.
- Script atau pipeline untuk restore, build, test, dan migration check.
- Dokumentasikan cara menjalankan proyek dari mesin baru.
- Dokumentasikan instalasi MT5/Wine pada Lubuntu, konfigurasi allowed URL localhost untuk EA exporter, Python bridge native Linux, serta batas bahwa exporter/bridge tidak boleh mengirim order.

## Deliverables

- Solution dapat dibuild dan dites dengan satu alur yang terdokumentasi.
- PostgreSQL dan migrasi awal.
- Skeleton API/worker beserta health endpoint.
- Konvensi coding, branching, configuration, dan error handling.

## Kriteria selesai

- Clean checkout dapat menjalankan build dan test.
- API dan worker dapat startup dengan konfigurasi lokal.
- Database dapat dibuat dari migration tanpa langkah manual tersembunyi.
- Dependency test atau review membuktikan Domain tetap independen.
- EA exporter dapat mengirim fixture dari terminal demo MT5 ke Python bridge localhost dan tidak membaca/menyimpan password akun.
