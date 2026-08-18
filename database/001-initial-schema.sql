CREATE TABLE IF NOT EXISTS "__EFMigrationsHistory" (
    "MigrationId" character varying(150) NOT NULL,
    "ProductVersion" character varying(32) NOT NULL,
    CONSTRAINT "PK___EFMigrationsHistory" PRIMARY KEY ("MigrationId")
);

START TRANSACTION;

DO $EF$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM "__EFMigrationsHistory"
        WHERE "MigrationId" = '20260818153547_InitialCreate') THEN
        CREATE TABLE candles (
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

        CREATE UNIQUE INDEX "IX_candles_Instrument_Timeframe_OpenTime"
            ON candles ("Instrument", "Timeframe", "OpenTime");

        INSERT INTO "__EFMigrationsHistory" ("MigrationId", "ProductVersion")
        VALUES ('20260818153547_InitialCreate', '10.0.4');
    END IF;
END $EF$;

COMMIT;
