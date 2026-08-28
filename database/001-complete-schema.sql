-- DBeaver: jalankan sebagai forex_app pada database "forex_intelligence".
-- Gunakan Execute SQL Script (Alt+X).

BEGIN;

CREATE TABLE IF NOT EXISTS "__EFMigrationsHistory" (
    "MigrationId" character varying(150) NOT NULL,
    "ProductVersion" character varying(32) NOT NULL,
    CONSTRAINT "PK___EFMigrationsHistory" PRIMARY KEY ("MigrationId")
);

CREATE TABLE IF NOT EXISTS candles (
    "Id" uuid NOT NULL,
    "Instrument" character varying(12) NOT NULL,
    "Timeframe" character varying(4) NOT NULL,
    "OpenTime" timestamp with time zone NOT NULL,
    "CloseTime" timestamp with time zone NOT NULL,
    "Open" numeric(20,10) NOT NULL,
    "High" numeric(20,10) NOT NULL,
    "Low" numeric(20,10) NOT NULL,
    "Close" numeric(20,10) NOT NULL,
    "TickVolume" bigint NOT NULL,
    "Status" character varying(12) NOT NULL,
    CONSTRAINT "PK_candles" PRIMARY KEY ("Id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "IX_candles_Instrument_Timeframe_OpenTime"
    ON candles ("Instrument", "Timeframe", "OpenTime");

CREATE TABLE IF NOT EXISTS market_data_batches (
    "BatchId" character varying(26) NOT NULL,
    "SourceInstanceId" character varying(64) NOT NULL,
    "Sequence" bigint NOT NULL,
    "Checksum" character varying(71) NOT NULL,
    "RecordCount" integer NOT NULL,
    "StoredAt" timestamp with time zone NOT NULL,
    CONSTRAINT "PK_market_data_batches" PRIMARY KEY ("BatchId")
);

CREATE UNIQUE INDEX IF NOT EXISTS "IX_market_data_batches_SourceInstanceId_Sequence"
    ON market_data_batches ("SourceInstanceId", "Sequence");

CREATE TABLE IF NOT EXISTS refresh_tokens (
    "Id" uuid NOT NULL,
    "TokenHash" character varying(64) NOT NULL,
    "FamilyId" uuid NOT NULL,
    "Username" character varying(128) NOT NULL,
    "Role" character varying(16) NOT NULL,
    "CreatedAt" timestamp with time zone NOT NULL,
    "ExpiresAt" timestamp with time zone NOT NULL,
    "ConsumedAt" timestamp with time zone,
    "RevokedAt" timestamp with time zone,
    "ReplacedByTokenHash" character varying(64),
    CONSTRAINT "PK_refresh_tokens" PRIMARY KEY ("Id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "IX_refresh_tokens_TokenHash"
    ON refresh_tokens ("TokenHash");

CREATE INDEX IF NOT EXISTS "IX_refresh_tokens_FamilyId_ExpiresAt"
    ON refresh_tokens ("FamilyId", "ExpiresAt");

INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
VALUES ('20260818153547_InitialCreate', '10.0.4')
ON CONFLICT ("MigrationId") DO NOTHING;

INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
VALUES ('20260819063605_AddRefreshTokens', '10.0.4')
ON CONFLICT ("MigrationId") DO NOTHING;

INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
VALUES ('20260828044211_AddMarketDataBatches', '10.0.4')
ON CONFLICT ("MigrationId") DO NOTHING;

COMMIT;
