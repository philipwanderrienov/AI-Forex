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

- .NET SDK `10.0.400` atau patch `10.0.4xx` yang kompatibel menurut `global.json`.
- Python `3.12+` untuk bridge.
- PostgreSQL 18.x yang dipasang native pada mesin development/runtime.

## Build dan test .NET

```bash
dotnet restore ForexIntelligence.sln
dotnet build ForexIntelligence.sln --no-restore
dotnet test ForexIntelligence.sln --no-build --no-restore
```

GitHub Actions menjalankan quality gate yang sama pada Linux, memeriksa bahwa model EF Core
tidak tertinggal dari migration, dan menjalankan integration test persistence terhadap
PostgreSQL 18 yang terisolasi. Test PostgreSQL lokal dapat diaktifkan dengan environment
variable `FOREX_TEST_POSTGRESQL`; tanpa variable tersebut default test suite tidak memerlukan
database hidup.

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
POST /api/v1/bridge/candle-batches
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
BridgeAuthentication__ApiKey=<minimal-32-byte-random-secret>
```

Pada laptop development Windows baru, jalankan setup interaktif berikut dari root repository:

```powershell
.\scripts\setup-development.ps1
```

Pada macOS atau Linux, jalankan versi shell dari root repository:

```bash
./scripts/setup-development.sh
```

Kedua script meminta password database dan admin tanpa menampilkannya, membuat JWT/API key random,
menyimpan semuanya ke .NET User Secrets, lalu menampilkan bridge API key satu kali agar dapat
disimpan di password manager dan dipasang pada laptop server. Struktur konfigurasi tanpa nilai
rahasia tersedia di `src/ForexIntelligence.Api/appsettings.Development.example.json`. Versi
macOS/Linux menerima password database kosong untuk instalasi lokal yang memang memakai
autentikasi passwordless; password admin aplikasi tetap wajib.

Endpoint bridge hanya menerima header `X-Bridge-Api-Key`. Nilainya harus sama dengan
`MT5_BRIDGE_BACKEND_API_KEY` pada laptop server dan tidak boleh dipakai sebagai JWT pengguna.

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

## Verifikasi MT5 sampai PostgreSQL

1. Jalankan `database/001-complete-schema.sql` lalu `database/999-verify-schema.sql` melalui
   DBeaver pada database target.
2. Konfigurasikan `ConnectionStrings__PostgreSql`, seluruh secret JWT/bootstrap, dan
   `BridgeAuthentication__ApiKey` melalui environment atau .NET user-secrets.
3. Pada laptop server, set `MT5_BRIDGE_BACKEND_URL` ke
   `https://<backend-host>/api/v1/bridge/candle-batches` dan isi
   `MT5_BRIDGE_BACKEND_API_KEY` dengan nilai yang sama.
4. Jalankan API, lalu Python bridge dan EA MT5. Pastikan spool berkurang hanya setelah API
   memberikan ACK.
5. Di DBeaver, cocokkan `market_data_batches."RecordCount"` dengan candle terkait dan pastikan
   pengiriman ulang batch yang sama tidak menambah baris.

Jangan membuka Python receiver port `8001` ke jaringan. Hanya endpoint HTTPS .NET yang perlu
dapat dijangkau oleh publisher dari laptop server.

Untuk managed startup API dan bridge pada Lubuntu, gunakan
[`deployment/systemd/README.md`](deployment/systemd/README.md). Service mengambil secret dari
`/etc/forex-intelligence`, bukan dari repository, dan tidak diaktifkan otomatis oleh installer
sebelum operator memeriksa konfigurasi.

Audit quarantine secara read-only dapat dijalankan dari root repository:

```bash
python tools/audit_bridge_quarantine.py
```

## Spesifikasi

Mulai dari [roadmap development](Development-Phases/README.md), [discovery](Development-Phases/00-discovery-dan-spesifikasi.md), dan [data dictionary](Development-Phases/00-data-dictionary.md).
