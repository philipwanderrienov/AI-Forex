-- DBeaver: jalankan sebagai forex_app pada database "forex_intelligence".

DO $VERIFY$
DECLARE
    missing_items text[] := ARRAY[]::text[];
BEGIN
    IF to_regclass('public."__EFMigrationsHistory"') IS NULL THEN
        missing_items := array_append(missing_items, '__EFMigrationsHistory table');
    ELSE
        IF NOT EXISTS (
            SELECT 1 FROM "__EFMigrationsHistory"
            WHERE "MigrationId" = '20260818153547_InitialCreate') THEN
            missing_items := array_append(missing_items, 'InitialCreate migration record');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM "__EFMigrationsHistory"
            WHERE "MigrationId" = '20260819063605_AddRefreshTokens') THEN
            missing_items := array_append(missing_items, 'AddRefreshTokens migration record');
        END IF;
    END IF;

    IF to_regclass('public.candles') IS NULL THEN
        missing_items := array_append(missing_items, 'candles table');
    END IF;

    IF to_regclass('public.refresh_tokens') IS NULL THEN
        missing_items := array_append(missing_items, 'refresh_tokens table');
    END IF;

    IF to_regclass('public."IX_candles_Instrument_Timeframe_OpenTime"') IS NULL THEN
        missing_items := array_append(missing_items, 'candles unique index');
    END IF;

    IF to_regclass('public."IX_refresh_tokens_TokenHash"') IS NULL THEN
        missing_items := array_append(missing_items, 'refresh token unique index');
    END IF;

    IF to_regclass('public."IX_refresh_tokens_FamilyId_ExpiresAt"') IS NULL THEN
        missing_items := array_append(missing_items, 'refresh token family index');
    END IF;

    IF cardinality(missing_items) > 0 THEN
        RAISE EXCEPTION 'Schema belum lengkap. Missing: %', array_to_string(missing_items, ', ');
    END IF;
END $VERIFY$;

SELECT
    current_database() AS database_name,
    current_user AS connected_as,
    current_setting('server_version') AS postgres_version;

SELECT "MigrationId", "ProductVersion"
FROM "__EFMigrationsHistory"
ORDER BY "MigrationId";

SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('candles', 'refresh_tokens')
ORDER BY tablename;

SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('candles', 'refresh_tokens')
ORDER BY tablename, indexname;
