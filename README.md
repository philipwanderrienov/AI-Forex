# Forex Intelligence

Aplikasi decision-support untuk lima instrumen MVP (`EURUSD`, `GBPUSD`, `EURGBP`, `EURCHF`, `XAUUSD`). Eksekusi transaksi tetap dilakukan manual oleh pengguna di MetaTrader 5.

## Arsitektur awal

```text
Controller → Service → repository spesifik → EF Core DbContext → PostgreSQL
                         ↑
                       Domain
```

- `ForexIntelligence.Api`: Controller, HTTP, OpenAPI, health endpoint.
- `ForexIntelligence.Application`: interface service/repository, DTO, dan use case.
- `ForexIntelligence.Domain`: entity, value object, enum, dan aturan bisnis.
- `ForexIntelligence.Infrastructure`: EF Core, PostgreSQL, dan implementasi repository.
- `ForexIntelligence.Worker`: pekerjaan background.
- `mt5-bridge`: receiver Python native Linux.
- `mt5-exporter`: EA MQL5 read-only.

Model HTTP ditempatkan terpisah di `ForexIntelligence.Api/Models/Requests` dan `Models/Responses`; Controller tidak mendeklarasikan DTO di dalam file yang sama.

## Prasyarat development

- .NET SDK `10.0.201` atau patch yang kompatibel menurut `global.json`.
- Python `3.12+` untuk bridge.
- PostgreSQL 18.x yang dipasang native pada mesin development/runtime.

## Build dan test .NET

```bash
dotnet restore ForexIntelligence.sln
dotnet build ForexIntelligence.sln --no-restore
dotnet test ForexIntelligence.sln --no-build --no-restore
```

Menjalankan API:

```bash
dotnet run --project src/ForexIntelligence.Api
```

Endpoint awal:

```text
GET /api/system-status
GET /health
GET /health/live
GET /health/ready
GET /openapi/v1.json   (development)
POST /api/market-data/candles
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/revoke
```

JWT pengguna memakai access token maksimal 15 menit dan refresh token maksimal 7 hari.
Konfigurasi sensitif wajib diberikan melalui environment atau secret store:

```text
Jwt__SigningKey=<minimal-32-byte-random-secret>
BootstrapUser__Username=<username>
BootstrapUser__PasswordHash=<pbkdf2-sha256-hash>
BootstrapUser__Role=ADMIN
```

Jangan masukkan nilai konfigurasi tersebut ke `appsettings*.json` atau source control.
Password bootstrap disimpan sebagai PBKDF2-SHA256 hash; API tidak menerima konfigurasi
password plaintext. Refresh token mentah hanya dikirim ke client, sedangkan PostgreSQL
menyimpan SHA-256 hash beserta token family untuk rotation, revocation, dan reuse detection.

Buat hash password secara interaktif tanpa menampilkan password di terminal:

```bash
dotnet run --project src/ForexIntelligence.Api -- --hash-password
```

Connection string production/development yang berisi password harus diberikan melalui environment atau secret store, misalnya `ConnectionStrings__PostgreSql`; jangan commit password.

## PostgreSQL lokal

Buka script bernomor pada folder `database/` di DBeaver dan jalankan sesuai urutan yang
dijelaskan pada [panduan database](database/README.md). Proyek tidak memakai Docker untuk
database.

`/health/live` hanya membuktikan proses API hidup. `/health/ready` juga memeriksa PostgreSQL.

## Python bridge

Lihat [panduan bridge](mt5-bridge/README.md). Jalur belajar pemula tersedia di [Panduan Belajar Python untuk MT5](Development-Phases/panduan-belajar-python-mt5.md).

## Spesifikasi

Mulai dari [roadmap development](Development-Phases/README.md), [discovery](Development-Phases/00-discovery-dan-spesifikasi.md), dan [data dictionary](Development-Phases/00-data-dictionary.md).
