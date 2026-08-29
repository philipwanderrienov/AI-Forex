-- DBeaver: jalankan sebagai administrator PostgreSQL pada database "postgres".
-- Ganti CHANGE_ME_STRONG_PASSWORD sebelum menjalankan blok role.
-- Jangan simpan password nyata ke Git.

DO $TARGET$
BEGIN
    IF current_database() <> 'postgres' THEN
        RAISE EXCEPTION
            'Target database salah: terhubung ke %, seharusnya postgres untuk bootstrap database.',
            current_database();
    END IF;
END $TARGET$;

DO $ADMIN$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'forex_app') THEN
        CREATE ROLE forex_app
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            PASSWORD 'CHANGE_ME_STRONG_PASSWORD';
    ELSE
        RAISE NOTICE 'Role forex_app sudah tersedia; password tidak diubah.';
    END IF;
END $ADMIN$;

-- PostgreSQL tidak mendukung CREATE DATABASE IF NOT EXISTS.
-- Jalankan statement berikut hanya jika database forex_intelligence belum tersedia.
-- Pilih statement lalu jalankan Execute SQL Statement (Ctrl+Enter).

CREATE DATABASE forex_intelligence
    WITH
    OWNER = forex_app
    ENCODING = 'UTF8'
    TEMPLATE = template0;
