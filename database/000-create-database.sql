\set ON_ERROR_STOP on

-- Jalankan melalui psql sebagai administrator PostgreSQL.
-- Contoh:
-- psql -U postgres -d postgres \
--   -v forex_db_password='ganti-dengan-password-kuat' \
--   -f database/000-create-database.sql

\if :{?forex_db_password}
\else
  \echo 'Variable forex_db_password wajib diberikan.'
  \quit
\endif

SELECT format(
    'CREATE ROLE forex_app LOGIN PASSWORD %L',
    :'forex_db_password')
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_roles
    WHERE rolname = 'forex_app')
\gexec

SELECT 'CREATE DATABASE forex_intelligence OWNER forex_app'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'forex_intelligence')
\gexec
