-- DBeaver: jalankan sebagai forex_app pada database "forex_intelligence".

DO $VERIFY$
DECLARE
    missing_items text[] := ARRAY[]::text[];
BEGIN
    IF current_database() <> 'forex_intelligence' THEN
        RAISE EXCEPTION
            'Target database salah: terhubung ke %, seharusnya forex_intelligence. Verifikasi dibatalkan.',
            current_database();
    END IF;

    IF current_user <> 'forex_app' THEN
        RAISE EXCEPTION
            'Target user salah: terhubung sebagai %, seharusnya forex_app. Verifikasi dibatalkan.',
            current_user;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_database
        WHERE datname = current_database()
          AND pg_get_userbyid(datdba) = 'forex_app') THEN
        missing_items := array_append(missing_items, 'forex_intelligence database owner must be forex_app');
    END IF;

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

        IF NOT EXISTS (
            SELECT 1 FROM "__EFMigrationsHistory"
            WHERE "MigrationId" = '20260828044211_AddMarketDataBatches') THEN
            missing_items := array_append(missing_items, 'AddMarketDataBatches migration record');
        END IF;
    END IF;

    IF to_regclass('public.candles') IS NULL THEN
        missing_items := array_append(missing_items, 'candles table');
    END IF;

    IF to_regclass('public.refresh_tokens') IS NULL THEN
        missing_items := array_append(missing_items, 'refresh_tokens table');
    END IF;

    IF to_regclass('public.market_data_batches') IS NULL THEN
        missing_items := array_append(missing_items, 'market_data_batches table');
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

    IF to_regclass('public."IX_market_data_batches_SourceInstanceId_Sequence"') IS NULL THEN
        missing_items := array_append(missing_items, 'market data batch sequence index');
    END IF;

    IF to_regclass('public."PK_candles"') IS NULL THEN
        missing_items := array_append(missing_items, 'candles primary key index');
    END IF;

    IF to_regclass('public."PK_refresh_tokens"') IS NULL THEN
        missing_items := array_append(missing_items, 'refresh tokens primary key index');
    END IF;

    IF to_regclass('public."PK_market_data_batches"') IS NULL THEN
        missing_items := array_append(missing_items, 'market data batches primary key index');
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN ('candles', 'market_data_batches', 'refresh_tokens')
          AND tableowner <> 'forex_app') THEN
        missing_items := array_append(missing_items, 'all application tables must be owned by forex_app');
    END IF;

    IF cardinality(missing_items) > 0 THEN
        RAISE EXCEPTION 'Schema belum lengkap. Missing: %', array_to_string(missing_items, ', ');
    END IF;
END $VERIFY$;

SELECT
    current_database() AS database_name,
    current_user AS connected_as,
    pg_get_userbyid(datdba) AS database_owner,
    current_setting('server_version') AS postgres_version
FROM pg_database
WHERE datname = current_database();

SELECT "MigrationId", "ProductVersion"
FROM "__EFMigrationsHistory"
ORDER BY "MigrationId";

SELECT schemaname, tablename, tableowner
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('candles', 'market_data_batches', 'refresh_tokens')
ORDER BY tablename;

SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('candles', 'market_data_batches', 'refresh_tokens')
ORDER BY tablename, indexname;
