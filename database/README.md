# Database PostgreSQL

Database dijalankan sebagai instalasi PostgreSQL native; proyek ini tidak memakai Docker.

## Instalasi awal

Jalankan script pertama sebagai administrator PostgreSQL. Ganti password contoh dan jangan menyimpannya di repository atau shell history bersama:

```bash
psql -U postgres -d postgres \
  -v forex_db_password='password-lokal-yang-kuat' \
  -f database/000-create-database.sql
```

Kemudian buat schema sebagai user aplikasi:

```bash
PGPASSWORD='password-lokal-yang-kuat' \
psql -h localhost -U forex_app -d forex_intelligence \
  -f database/001-initial-schema.sql
```

Konfigurasikan aplikasi melalui environment:

```bash
export ConnectionStrings__PostgreSql='Host=localhost;Port=5432;Database=forex_intelligence;Username=forex_app;Password=password-lokal-yang-kuat'
```

Script `001` idempotent dan mencatat versi EF migration yang sesuai. Setiap perubahan schema berikutnya mendapat nomor script baru; script lama tidak diedit setelah dipakai.
