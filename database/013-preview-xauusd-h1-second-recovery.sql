-- Scoped second XAUUSD H1 manual repair. Execute the ENTIRE script in DBeaver.
-- Default dry run ends in ROLLBACK. Review 15 rows before changing it to COMMIT.
-- Source: XAUUSD_H1_202609092200_202609110200.csv
-- CSV SHA256: 47e37cd6bafb12a199211825d4bc9613eaffcb1e8c7486acb307da7ea24ea06b
-- CSV contains 25 bars; only broker September 10 08:00..22:00 are candidates.
-- UTC+3 mapping is scoped to this incident: UTC September 10 05:00..19:00,
-- displayed as WIB September 10 12:00..September 11 02:00.
-- Export has no broker 23:00 or 00:00 bars on either intervening night.
-- Do not synthesize those four slots or infer a universal broker session rule.
-- The first CSV recovery (012) is separate; its two overlapping CSV bars agree.
-- No batch ledger, exporter state or quarantine changes. On error: ROLLBACK.

BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TEMP TABLE recovery_xauusd_h1 (
    open_time timestamptz PRIMARY KEY,
    o numeric(20,10), h numeric(20,10), l numeric(20,10),
    c numeric(20,10), ticks bigint
) ON COMMIT DROP;

INSERT INTO recovery_xauusd_h1 VALUES
    (TIMESTAMPTZ '2026-09-10T05:00:00+00:00', 4408.35, 4431.26, 4408.05, 4431.06, 13262),
    (TIMESTAMPTZ '2026-09-10T06:00:00+00:00', 4430.97, 4434.62, 4410.85, 4425.19, 15950),
    (TIMESTAMPTZ '2026-09-10T07:00:00+00:00', 4425.19, 4425.35, 4404.00, 4411.78, 14399),
    (TIMESTAMPTZ '2026-09-10T08:00:00+00:00', 4411.79, 4412.83, 4392.43, 4394.83, 16885),
    (TIMESTAMPTZ '2026-09-10T09:00:00+00:00', 4394.83, 4396.89, 4388.35, 4394.01, 14127),
    (TIMESTAMPTZ '2026-09-10T10:00:00+00:00', 4394.01, 4400.20, 4374.93, 4378.87, 19609),
    (TIMESTAMPTZ '2026-09-10T11:00:00+00:00', 4378.82, 4390.69, 4373.40, 4374.52, 19674),
    (TIMESTAMPTZ '2026-09-10T12:00:00+00:00', 4374.52, 4377.75, 4323.99, 4340.21, 28576),
    (TIMESTAMPTZ '2026-09-10T13:00:00+00:00', 4340.07, 4375.82, 4339.42, 4365.58, 36631),
    (TIMESTAMPTZ '2026-09-10T14:00:00+00:00', 4365.63, 4376.27, 4353.85, 4358.08, 34096),
    (TIMESTAMPTZ '2026-09-10T15:00:00+00:00', 4358.09, 4372.13, 4352.58, 4365.82, 27199),
    (TIMESTAMPTZ '2026-09-10T16:00:00+00:00', 4365.95, 4369.92, 4353.99, 4363.99, 24498),
    (TIMESTAMPTZ '2026-09-10T17:00:00+00:00', 4363.99, 4368.06, 4351.10, 4352.63, 23893),
    (TIMESTAMPTZ '2026-09-10T18:00:00+00:00', 4352.75, 4356.16, 4329.73, 4332.90, 27391),
    (TIMESTAMPTZ '2026-09-10T19:00:00+00:00', 4332.76, 4332.88, 4313.68, 4324.32, 23724);

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
