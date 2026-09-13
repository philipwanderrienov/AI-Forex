-- Scoped manual broker-history repair; execute the ENTIRE script in DBeaver.
-- DEFAULT IS A DRY RUN: the final ROLLBACK discards all inserted candles.
-- Only after reviewing the dry run, replace the final ROLLBACK with COMMIT.
-- Source: XAUUSD_H1_202609110100_202609111700.csv
-- CSV SHA256: d050e45d23a367a77f852e5e01cf7ba3ff44080a0f2b0b559852ece6d22856bf
-- Broker 2026-09-11 01:00..16:00 mapped using UTC+3 for this interval only.
-- All 16 OHLC match quarantine; 15 tick volumes match.
-- At broker 02:00 the CSV tick volume 3750 is selected over quarantine 3752.
-- This explicit manual repair does not create an ingestion batch, change the
-- existing batch ledger, advance exporter checkpoints or replay quarantine.
-- If any statement errors, execute ROLLBACK before retrying.

BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TEMP TABLE recovery_xauusd_h1 (
    open_time timestamptz PRIMARY KEY,
    o numeric(20,10), h numeric(20,10), l numeric(20,10),
    c numeric(20,10), ticks bigint
) ON COMMIT DROP;

INSERT INTO recovery_xauusd_h1 VALUES
    (TIMESTAMPTZ '2026-09-10T22:00:00+00:00', 4311.47, 4324.54, 4285.91, 4318.57, 3285),
    (TIMESTAMPTZ '2026-09-10T23:00:00+00:00', 4318.57, 4320.46, 4310.87, 4315.10, 3750),
    (TIMESTAMPTZ '2026-09-11T00:00:00+00:00', 4315.18, 4333.78, 4312.54, 4332.04, 19087),
    (TIMESTAMPTZ '2026-09-11T01:00:00+00:00', 4332.04, 4340.42, 4320.84, 4329.32, 20049),
    (TIMESTAMPTZ '2026-09-11T02:00:00+00:00', 4329.32, 4334.53, 4315.86, 4322.73, 15656),
    (TIMESTAMPTZ '2026-09-11T03:00:00+00:00', 4322.73, 4326.47, 4300.64, 4303.80, 15191),
    (TIMESTAMPTZ '2026-09-11T04:00:00+00:00', 4303.80, 4335.29, 4301.86, 4331.77, 14846),
    (TIMESTAMPTZ '2026-09-11T05:00:00+00:00', 4331.77, 4352.02, 4328.18, 4346.03, 15647),
    (TIMESTAMPTZ '2026-09-11T06:00:00+00:00', 4346.03, 4361.01, 4345.74, 4353.15, 18197),
    (TIMESTAMPTZ '2026-09-11T07:00:00+00:00', 4353.19, 4356.18, 4340.50, 4344.91, 13556),
    (TIMESTAMPTZ '2026-09-11T08:00:00+00:00', 4344.91, 4357.49, 4342.13, 4346.99, 18027),
    (TIMESTAMPTZ '2026-09-11T09:00:00+00:00', 4347.02, 4353.97, 4340.77, 4346.31, 14147),
    (TIMESTAMPTZ '2026-09-11T10:00:00+00:00', 4346.31, 4349.92, 4336.64, 4337.47, 14937),
    (TIMESTAMPTZ '2026-09-11T11:00:00+00:00', 4337.53, 4342.55, 4330.06, 4333.27, 17682),
    (TIMESTAMPTZ '2026-09-11T12:00:00+00:00', 4333.29, 4390.13, 4289.57, 4388.38, 37953),
    (TIMESTAMPTZ '2026-09-11T13:00:00+00:00', 4388.18, 4402.45, 4380.39, 4401.55, 37846);

-- Prevent a concurrent ingest changing a row between comparison and insertion.
LOCK TABLE public.candles IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM recovery_xauusd_h1 r
        JOIN public.candles c ON c."Instrument" = 'XAUUSD'
            AND c."Timeframe" = 'H1' AND c."OpenTime" = r.open_time
        WHERE ROW(c."Open", c."High", c."Low", c."Close", c."TickVolume",
                  c."CloseTime", c."Status")
            IS DISTINCT FROM ROW(r.o, r.h, r.l, r.c, r.ticks,
                                 r.open_time + INTERVAL '1 hour', 'Final'::varchar)
    ) THEN
        RAISE EXCEPTION 'Existing candle differs from CSV; no repair applied. ROLLBACK and inspect.';
    END IF;
END $$;

WITH inserted AS (
    INSERT INTO public.candles (
        "Id", "Instrument", "Timeframe", "OpenTime", "CloseTime",
        "Open", "High", "Low", "Close", "TickVolume", "Status"
    )
    SELECT gen_random_uuid(), 'XAUUSD', 'H1', r.open_time,
           r.open_time + INTERVAL '1 hour', r.o, r.h, r.l, r.c, r.ticks, 'Final'
    FROM recovery_xauusd_h1 r
    WHERE NOT EXISTS (
        SELECT 1 FROM public.candles c WHERE c."Instrument" = 'XAUUSD'
            AND c."Timeframe" = 'H1' AND c."OpenTime" = r.open_time
    )
    RETURNING "Id"
)
SELECT count(*) AS inserted_in_transaction FROM inserted;

SELECT c."OpenTime" AT TIME ZONE 'Asia/Jakarta' AS waktu_wib,
       c."Open", c."High", c."Low", c."Close", c."TickVolume", c."Status"
FROM public.candles c JOIN recovery_xauusd_h1 r ON c."OpenTime" = r.open_time
WHERE c."Instrument" = 'XAUUSD' AND c."Timeframe" = 'H1'
ORDER BY c."OpenTime";

ROLLBACK;
