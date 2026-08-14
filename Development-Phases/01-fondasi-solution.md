# Fase 01 — Fondasi Solution

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
```

## Pekerjaan

### 1. Bootstrap proyek

- Buat solution .NET dan project sesuai struktur.
- Terapkan dependency direction: Domain tidak bergantung pada Infrastructure atau API.
- Aktifkan nullable reference types, analyzers, formatting, dan warnings yang relevan.
- Buat konfigurasi per environment tanpa menyimpan secret di repository.

### 2. Implementasikan domain foundation

- Buat value object `Currency`, `CurrencyPair`, `Timeframe`, `Money`, dan `Percentage` bila diperlukan.
- Buat entity awal `Candle` beserta invariants OHLC.
- Tambahkan domain exception dan result/error model.
- Hindari dependensi EF Core pada model domain bila tidak diperlukan.

### 3. Siapkan persistence

- Jalankan PostgreSQL lokal melalui container.
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
- Integration test menggunakan database nyata/container.
- Script atau pipeline untuk restore, build, test, dan migration check.
- Dokumentasikan cara menjalankan proyek dari mesin baru.

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

