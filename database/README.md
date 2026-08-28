# Database PostgreSQL melalui DBeaver

Database memakai PostgreSQL native. Seluruh script SQL pada folder ini dibuat untuk langsung
dijalankan melalui DBeaver tanpa perintah khusus terminal.

## Instalasi baru

1. Buka koneksi administrator DBeaver ke database bawaan `postgres`.
2. Buka `000-create-database.sql` dan ganti `CHANGE_ME_STRONG_PASSWORD`.
3. Jalankan blok pembuatan role. Jalankan `CREATE DATABASE` hanya jika database
   `forex_intelligence` belum tersedia.
4. Buat koneksi DBeaver ke `forex_intelligence` sebagai `forex_app`.
5. Jalankan seluruh `001-complete-schema.sql` dengan **Execute SQL Script** (`Alt+X`).
6. Jalankan `999-verify-schema.sql`. Verifikasi melempar exception jika schema belum lengkap.

Jangan simpan password nyata ke file SQL atau Git. Setelah setup, kembalikan placeholder
password sebelum menyimpan file.

## Schema terbaru

- `__EFMigrationsHistory`: histori migration EF Core;
- `candles`: candle market-data;
- `refresh_tokens`: hash refresh token, family, expiry, rotation, dan revocation;
- `market_data_batches`: ledger batch idempotent berdasarkan batch ID dan source sequence;
- unique index candle berdasarkan instrument, timeframe, dan open time;
- unique index refresh-token hash;
- index refresh-token family dan expiry.
- unique index source instance dan sequence batch market-data.

Tidak ada seed user atau password di database. Connection string, username/password hash
bootstrap, dan JWT signing key tetap disimpan melalui environment atau .NET user-secrets.
